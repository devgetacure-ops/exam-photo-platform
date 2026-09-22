#!/usr/bin/env python3
"""Tell the owner when the site stops working (DEC-106).

Nothing watched this: the engine could be unhealthy, the disk full or payments
refusing, and the first anyone would know is a candidate who paid and got
nothing. This runs every five minutes and sends one email when something
breaks and one when it recovers -- never a stream, because an alarm nobody can
bear to read is an alarm nobody reads.

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


def notify(subject: str, body: str, config: dict[str, str]) -> None:
    host = config.get("EXAM_PHOTO_SMTP_HOST", "")
    sender = config.get("EXAM_PHOTO_SMTP_FROM", "")
    to = config.get("EXAM_PHOTO_SMTP_REPLY_TO") or sender
    if not host or not sender or not to:
        return
    message = EmailMessage()
    message["From"] = f"ExamUploadKit watch <{sender}>"
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP(host, int(config.get("EXAM_PHOTO_SMTP_PORT", "587")), timeout=30) as server:
        server.starttls()
        if config.get("EXAM_PHOTO_SMTP_USERNAME"):
            server.login(config["EXAM_PHOTO_SMTP_USERNAME"], config.get("EXAM_PHOTO_SMTP_PASSWORD", ""))
        server.send_message(message)


def main() -> int:
    config = settings()
    found = failures()
    was_broken = False
    if STATE.is_file():
        try:
            was_broken = bool(json.loads(STATE.read_text(encoding="utf-8")).get("broken"))
        except Exception:
            was_broken = False

    if found and not was_broken:
        notify(
            "ExamUploadKit: something is wrong",
            "\n".join(found) + f"\n\n{SITE}\nssh root@65.20.73.233\n",
            config,
        )
    elif not found and was_broken:
        notify("ExamUploadKit: back to normal", f"Everything answers again.\n\n{SITE}\n", config)

    STATE.write_text(json.dumps({"broken": bool(found), "detail": found}), encoding="utf-8")
    print("broken:" if found else "well:", "; ".join(found) or "site, engine and disk all answer")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
