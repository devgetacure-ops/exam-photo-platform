#!/usr/bin/env python3
"""Tell the owner when the site stops working (DEC-106).

Nothing watched this: the engine could be unhealthy, the disk full or payments
refusing, and the first anyone would know is a candidate who paid and got
nothing. This runs every five minutes and sends one email when something
breaks and one when it recovers -- never a stream, because an alarm nobody can
bear to read is an alarm nobody reads.

It also emails the operator page's alerts (DEC-109): a paid order not delivered
within 15 minutes, a run of failed preparations, a complaint unanswered for
48 hours, and a digest of yesterday at 08:00 IST.

Checks, in the order that matters:
  * the public site answers through Cloudflare
  * the engine is ready, with payments and email configured
  * the disk has room for the models and a day's artifacts

Credentials come from the same `deploy/.env` the service uses; nothing new is
stored. The state file remembers what was already reported.
"""

from __future__ import annotations

import json
import smtplib
import subprocess
import urllib.request
from email.message import EmailMessage
from pathlib import Path

ENV = Path("/opt/exam-photo-platform/deploy/.env")
STATE = Path("/var/lib/euk-watch.json")
SITE = "https://examuploadkit.com"
COMPOSE = [
    "docker", "compose", "-f", "/opt/exam-photo-platform/deploy/docker-compose.yml",
]
DISK_FLOOR_GB = 10
#: The web app's request queue (DEC-108): forwarded to support@ once each, with
#: the candidate's own address so the owner can reply.
REQUESTS_VOLUME = "exam-upload_requests"


def settings() -> dict[str, str]:
    values: dict[str, str] = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def failures() -> list[str]:
    found: list[str] = []

    # Through Caddy, with the real hostname, from the machine itself: this is
    # the whole stack except Cloudflare. Cloudflare refuses a request that does
    # not look like a browser, so asking the public address would alarm every
    # five minutes about a site that is perfectly well.
    try:
        page = subprocess.run(
            ["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "25",
             "-k", "--resolve", "examuploadkit.com:443:127.0.0.1", SITE],
            capture_output=True, text=True, timeout=40,
        )
        code = page.stdout.strip()
        if code != "200":
            found.append(f"The site answered {code or page.stderr.strip()[:80]}.")
    except Exception as error:
        found.append(f"The site did not answer: {error}.")

    # And that Cloudflare still reaches us: anything it answers, including a
    # challenge, means the edge and the origin are talking.
    try:
        edge = subprocess.run(
            ["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "25", SITE],
            capture_output=True, text=True, timeout=40,
        )
        if not edge.stdout.strip().startswith(("2", "3", "4")):
            found.append(f"Cloudflare answered {edge.stdout.strip() or nothing}.")
    except Exception as error:
        found.append(f"Cloudflare could not be reached: {error}.")

    try:
        ready = subprocess.run(
            COMPOSE + [
                "exec", "-T", "engine", "python", "-c",
                "import urllib.request;print(urllib.request.urlopen("
                "'http://127.0.0.1:8000/ready', timeout=20).read().decode())",
            ],
            capture_output=True, text=True, timeout=90,
        )
        if ready.returncode != 0:
            found.append("The engine did not answer its readiness check.")
        else:
            report = json.loads(ready.stdout.strip().splitlines()[-1])
            if report.get("status") != "ready":
                found.append(f"The engine is {report.get('status')}.")
            for field in ("payments", "email"):
                if report.get(field) != "configured":
                    found.append(f"The engine reports {field}: {report.get(field)}.")
    except Exception as error:
        found.append(f"The engine could not be reached: {error}.")

    try:
        disk = subprocess.run(
            ["df", "-B1", "--output=avail", "/"], capture_output=True, text=True, timeout=20
        )
        free_gb = int(disk.stdout.split()[1]) / 1_000_000_000
        if free_gb < DISK_FLOOR_GB:
            found.append(f"The disk has {free_gb:.1f} GB free.")
    except Exception as error:
        found.append(f"The disk could not be measured: {error}.")

    return found


def new_requests(seen: set[str]) -> list[dict[str, str]]:
    """Requests in the web app's volume that have not been forwarded yet."""
    try:
        where = subprocess.run(
            ["docker", "volume", "inspect", "-f", "{{.Mountpoint}}", REQUESTS_VOLUME],
            capture_output=True, text=True, timeout=20,
        )
    except Exception:
        return []
    directory = Path(where.stdout.strip())
    if where.returncode != 0 or not directory.is_dir():
        return []
    found = []
    for path in directory.glob("*.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        reference = str(record.get("reference") or path.stem)
        if reference not in seen:
            item = {key: str(record.get(key) or "") for key in (
                "kind", "exam", "email", "message", "created_at")}
            item["reference"] = reference
            found.append(item)
    return sorted(found, key=lambda item: item["created_at"])


def engine_call(config: dict[str, str], path: str, body: object = None) -> object:
    """Ask the engine's operator surface, from inside its own container.

    The token is read from the container's own environment, so it never
    appears on a command line where `ps` would show it.
    """
    del config
    script = (
        "import os,sys,urllib.request;"
        "body=sys.stdin.read();"
        f"req=urllib.request.Request('http://127.0.0.1:8000{path}',"
        "data=body.encode() if body else None,"
        "headers={'X-Operator-Token':os.environ['EXAM_PHOTO_OPERATOR_TOKEN'],'Content-Type':'application/json'});"
        "print(urllib.request.urlopen(req,timeout=60).read().decode())"
    )
    result = subprocess.run(
        COMPOSE + ["exec", "-T", "engine", "python", "-c", script],
        input=json.dumps(body) if body is not None else "",
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip()[-300:] or "engine call failed")
    return json.loads(result.stdout.strip().splitlines()[-1])


def send_alerts(config: dict[str, str]) -> int:
    """Refund-due orders, failure runs, late replies and the 08:00 digest (DEC-109)."""
    try:
        alerts = engine_call(config, "/v1/operator/alerts").get("alerts", [])  # type: ignore[union-attr]
    except Exception as error:
        print(f"alerts unavailable: {error}")
        return 0
    sent = []
    for alert in alerts:
        try:
            notify(f"ExamUploadKit: {alert['subject']}", alert["body"], config)
            sent.append(alert["key"])
        except Exception as error:
            print(f"could not send alert {alert.get('key')}: {error}")
    if sent:
        try:
            engine_call(config, "/v1/operator/alerts/sent", sent)
        except Exception as error:
            print(f"could not mark alerts sent: {error}")
    return len(sent)


def request_email(requests: list[dict[str, str]]) -> tuple[str, str]:
    """One email for everything that arrived since the last run."""
    parts = []
    for item in requests:
        heading = item["exam"] if item["kind"] == "exam" else "Support"
        parts.append(
            f"{heading}  ({item['reference']}, {item['created_at']})\n"
            f"From: {item['email']}\n\n"
            f"{item['message'] or '(no message)'}\n"
        )
    if len(requests) == 1:
        subject = f"New request: {requests[0]['exam'] or 'support'}"
    else:
        subject = f"{len(requests)} new requests on ExamUploadKit"
    divider = "\n" + "-" * 40 + "\n\n"
    return subject, divider.join(parts) + f"\nAll of them: {SITE}/admin#requests\n"


def notify(
    subject: str, body: str, config: dict[str, str], reply_to: str = ""
) -> None:
    host = config.get("EXAM_PHOTO_SMTP_HOST", "")
    sender = config.get("EXAM_PHOTO_SMTP_FROM", "")
    to = config.get("EXAM_PHOTO_SMTP_REPLY_TO") or sender
    if not host or not sender or not to:
        return
    message = EmailMessage()
    message["From"] = f"ExamUploadKit watch <{sender}>"
    message["To"] = to
    message["Subject"] = subject
    if reply_to:
        message["Reply-To"] = reply_to
    message.set_content(body)
    with smtplib.SMTP(host, int(config.get("EXAM_PHOTO_SMTP_PORT", "587")), timeout=30) as server:
        server.starttls()
        if config.get("EXAM_PHOTO_SMTP_USERNAME"):
            server.login(config["EXAM_PHOTO_SMTP_USERNAME"], config.get("EXAM_PHOTO_SMTP_PASSWORD", ""))
        server.send_message(message)


def main() -> int:
    config = settings()
    found = failures()
    state: dict = {}
    if STATE.is_file():
        try:
            state = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            state = {}
    was_broken = bool(state.get("broken"))

    if found and not was_broken:
        notify(
            "ExamUploadKit: something is wrong",
            "\n".join(found) + f"\n\n{SITE}\nssh root@65.20.73.233\n",
            config,
        )
    elif not found and was_broken:
        notify("ExamUploadKit: back to normal", f"Everything answers again.\n\n{SITE}\n", config)

    seen = set(state.get("requests_seen") or [])
    arrived = new_requests(seen)
    if arrived:
        subject, body = request_email(arrived)
        # One sender, so a reply goes straight back to them.
        single = arrived[0]["email"] if len(arrived) == 1 else ""
        try:
            notify(subject, body, config, reply_to=single)
            seen.update(item["reference"] for item in arrived)
        except Exception as error:
            print(f"could not forward {len(arrived)} request(s): {error}")

    if not found:
        alerted = send_alerts(config)
        if alerted:
            print(f"alerts: {alerted} sent")

    STATE.write_text(
        json.dumps({"broken": bool(found), "detail": found, "requests_seen": sorted(seen)}),
        encoding="utf-8",
    )
    print("broken:" if found else "well:", "; ".join(found) or "site, engine and disk all answer")
    if arrived:
        print(f"requests: {len(arrived)} new")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
