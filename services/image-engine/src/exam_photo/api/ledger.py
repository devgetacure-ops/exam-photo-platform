"""The business's own history, kept after the files are gone (DEC-109).

Uploads are erased after thirty minutes (DEC-066); orders outlive them as JSON
(DEC-071). Neither answers "how long did preparing take last week", "who is
this customer", or "which complaint is about which order". This is the one
place those live: a SQLite file on the artifacts volume, beside `_orders/`.

It holds **no image and no image-derived data** -- only what happened, when,
to which examination, and who asked. Every write is best effort from the
candidate's side: a ledger failure is logged and never fails a preparation, a
payment or a delivery.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

TICKET_KINDS = ("exam", "support", "question", "complaint", "grievance")
TICKET_STATES = ("open", "answered", "resolved")
#: The grievance page promises acknowledgement within 48 hours and resolution
#: within a month; the page shows anything past either in red.
ACK_WITHIN = timedelta(hours=48)
RESOLVE_WITHIN = timedelta(days=30)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS uploads (
    job_id TEXT PRIMARY KEY,
    kit_id TEXT,
    exam_id TEXT,
    exam_name TEXT,
    requirement_id TEXT,
    requirement_name TEXT,
    requirement_type TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    outcome TEXT,
    findings TEXT,
    issue_codes TEXT,
    input_bytes INTEGER,
    output_width INTEGER,
    output_height INTEGER,
    output_bytes INTEGER,
    processing_seconds REAL,
    stage_ms TEXT,
    error TEXT
);
CREATE INDEX IF NOT EXISTS uploads_started ON uploads(started_at);
CREATE INDEX IF NOT EXISTS uploads_kit ON uploads(kit_id);

CREATE TABLE IF NOT EXISTS contacts (
    email TEXT PRIMARY KEY,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    sources TEXT NOT NULL,
    phone TEXT
);

CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    reference TEXT,
    kind TEXT NOT NULL,
    exam TEXT,
    email TEXT,
    message TEXT,
    payment_reference TEXT,
    order_id TEXT,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    acknowledged_at TEXT,
    resolved_at TEXT,
    added_at TEXT
);
CREATE INDEX IF NOT EXISTS tickets_created ON tickets(created_at);
CREATE INDEX IF NOT EXISTS tickets_email ON tickets(email);
CREATE INDEX IF NOT EXISTS tickets_order ON tickets(order_id);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target TEXT NOT NULL,
    at TEXT NOT NULL,
    actor TEXT NOT NULL,
    text TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS notes_target ON notes(target);

CREATE TABLE IF NOT EXISTS refunds (
    order_id TEXT PRIMARY KEY,
    at TEXT NOT NULL,
    actor TEXT NOT NULL,
    reference TEXT,
    amount_paise INTEGER
);

CREATE TABLE IF NOT EXISTS activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    at TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT
);
CREATE INDEX IF NOT EXISTS activity_at ON activity(at);

CREATE TABLE IF NOT EXISTS health (
    at TEXT PRIMARY KEY,
    status TEXT,
    disk_free_bytes INTEGER,
    busy_refusals INTEGER
);

CREATE TABLE IF NOT EXISTS alerts_sent (
    key TEXT PRIMARY KEY,
    at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kv (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS visits (
    session_id TEXT PRIMARY KEY,
    first_at TEXT NOT NULL,
    last_at TEXT NOT NULL,
    active_seconds INTEGER NOT NULL DEFAULT 0,
    pages INTEGER NOT NULL DEFAULT 0,
    landing TEXT,
    referrer_host TEXT,
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    device TEXT,
    browser TEXT,
    connection TEXT,
    kit_ids TEXT NOT NULL DEFAULT '[]',
    exam_pages INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS visits_first ON visits(first_at);

CREATE TABLE IF NOT EXISTS pageviews (
    session_id TEXT NOT NULL,
    at TEXT NOT NULL,
    path TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS pageviews_at ON pageviews(at);

CREATE TABLE IF NOT EXISTS searches (
    at TEXT NOT NULL,
    query TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS searches_at ON searches(at);

CREATE TABLE IF NOT EXISTS deadlines (
    exam_id TEXT PRIMARY KEY,
    closes_on TEXT NOT NULL,
    note TEXT,
    auto_remind INTEGER NOT NULL DEFAULT 0,
    set_by TEXT,
    set_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS coupons (
    code TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    value INTEGER NOT NULL,
    partner TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    max_uses INTEGER,
    uses INTEGER NOT NULL DEFAULT 0,
    expires_on TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS suppressions (
    email TEXT PRIMARY KEY,
    at TEXT NOT NULL,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS campaigns (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    actor TEXT NOT NULL,
    segment TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    status TEXT NOT NULL,
    total INTEGER NOT NULL DEFAULT 0,
    sent INTEGER NOT NULL DEFAULT 0,
    failed INTEGER NOT NULL DEFAULT 0,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS campaign_recipients (
    campaign_id TEXT NOT NULL,
    email TEXT NOT NULL,
    status TEXT NOT NULL,
    at TEXT,
    error TEXT,
    PRIMARY KEY (campaign_id, email)
);

CREATE TABLE IF NOT EXISTS feedback (
    order_id TEXT PRIMARY KEY,
    at TEXT NOT NULL,
    worked INTEGER NOT NULL,
    comment TEXT,
    may_publish INTEGER NOT NULL DEFAULT 0,
    published INTEGER NOT NULL DEFAULT 0
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse(stamp: Optional[str]) -> Optional[datetime]:
    if not stamp:
        return None
    try:
        value = datetime.fromisoformat(stamp)
    except ValueError:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def normalise_email(address: Optional[str]) -> Optional[str]:
    if not address:
        return None
    value = address.strip().lower()
    return value if "@" in value and len(value) <= 254 else None


def stage_timings(report: Any) -> Dict[str, float]:
    """Every `{stage, duration_ms}` pair anywhere in a pipeline report."""
    found: Dict[str, float] = {}

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            stage, duration = node.get("stage"), node.get("duration_ms")
            if isinstance(stage, str) and isinstance(duration, (int, float)):
                found[stage] = found.get(stage, 0.0) + float(duration)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(report)
    return {stage: round(ms, 1) for stage, ms in found.items()}


class Ledger:
    """One SQLite file; one connection per call; one writer lock per process."""

    def __init__(self, artifact_root: Path):
        self.path = artifact_root / "_ledger" / "ledger.sqlite3"
        self._lock = threading.Lock()
        self._ready = False

    @contextmanager
    def _db(self) -> Iterator[sqlite3.Connection]:
        if not self._ready:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            if not self._ready:
                connection.execute("PRAGMA journal_mode=WAL")
                connection.executescript(_SCHEMA)
                self._ready = True
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _write(self, sql: str, args: tuple[Any, ...] = ()) -> None:
        with self._lock, self._db() as db:
            db.execute(sql, args)

    def _rows(self, sql: str, args: tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
        with self._db() as db:
            return [dict(row) for row in db.execute(sql, args).fetchall()]

    # --- uploads ---------------------------------------------------------

    def upload_started(self, job_id: str, **fields: Any) -> None:
        self._write(
            "INSERT OR REPLACE INTO uploads (job_id, kit_id, exam_id, exam_name, "
            "requirement_id, requirement_name, requirement_type, started_at, "
            "status, input_bytes) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                job_id,
                fields.get("kit_id"),
                fields.get("exam_id"),
                fields.get("exam_name"),
                fields.get("requirement_id"),
                fields.get("requirement_name"),
                fields.get("requirement_type"),
                fields.get("started_at") or now_iso(),
                "processing",
                fields.get("input_bytes"),
            ),
        )

    def upload_finished(
        self,
        job_id: str,
        *,
        status: str,
        processing_seconds: float,
        outcome: Optional[str] = None,
        findings: Optional[List[str]] = None,
        issue_codes: Optional[List[str]] = None,
        output_width: Optional[int] = None,
        output_height: Optional[int] = None,
        output_bytes: Optional[int] = None,
        stage_ms: Optional[Dict[str, float]] = None,
        error: Optional[str] = None,
    ) -> None:
        self._write(
            "UPDATE uploads SET finished_at=?, status=?, processing_seconds=?, "
            "outcome=?, findings=?, issue_codes=?, output_width=?, output_height=?, "
            "output_bytes=?, stage_ms=?, error=? WHERE job_id=?",
            (
                now_iso(),
                status,
                round(processing_seconds, 2),
                outcome,
                json.dumps(findings or []),
                json.dumps(issue_codes or []),
                output_width,
                output_height,
                output_bytes,
                json.dumps(stage_ms or {}),
                (error or "")[:300] or None,
                job_id,
            ),
        )

    def uploads(
        self,
        *,
        query: str = "",
        since: Optional[str] = None,
        kit_ids: Optional[List[str]] = None,
        limit: int = 500,
    ) -> List[Dict[str, Any]]:
        clauses, args = [], []
        if query:
            like = f"%{query}%"
            clauses.append(
                "(job_id LIKE ? OR kit_id LIKE ? OR exam_name LIKE ? OR exam_id LIKE ?)"
            )
            args += [like, like, like, like]
        if since:
            clauses.append("started_at >= ?")
            args.append(since)
        if kit_ids is not None:
            if not kit_ids:
                return []
            clauses.append(f"kit_id IN ({','.join('?' * len(kit_ids))})")
            args += kit_ids
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._rows(
            f"SELECT * FROM uploads {where} ORDER BY started_at DESC LIMIT ?",
            (*args, limit),
        )
        for row in rows:
            for key in ("findings", "issue_codes", "stage_ms"):
                row[key] = json.loads(row[key]) if row.get(key) else None
        return rows

    def upload(self, job_id: str) -> Optional[Dict[str, Any]]:
        found = self._rows("SELECT * FROM uploads WHERE job_id=?", (job_id,))
        if not found:
            return None
        row = found[0]
        for key in ("findings", "issue_codes", "stage_ms"):
            row[key] = json.loads(row[key]) if row.get(key) else None
        return row

    # --- contacts --------------------------------------------------------

    def contact_seen(
        self, email: Optional[str], source: str, phone: Optional[str] = None
    ) -> None:
        address = normalise_email(email)
        if not address:
            return
        with self._lock, self._db() as db:
            row = db.execute(
                "SELECT sources, phone FROM contacts WHERE email=?", (address,)
            ).fetchone()
            stamp = now_iso()
            if row is None:
                db.execute(
                    "INSERT INTO contacts (email, first_seen, last_seen, sources, phone) "
                    "VALUES (?,?,?,?,?)",
                    (address, stamp, stamp, json.dumps([source]), phone),
                )
                return
            sources = json.loads(row["sources"])
            if source not in sources:
                sources.append(source)
            db.execute(
                "UPDATE contacts SET last_seen=?, sources=?, phone=COALESCE(?, phone) "
                "WHERE email=?",
                (stamp, json.dumps(sources), phone, address),
            )

    def contacts(self, query: str = "", limit: int = 1000) -> List[Dict[str, Any]]:
        like = f"%{query.lower()}%"
        rows = self._rows(
            "SELECT * FROM contacts WHERE email LIKE ? OR IFNULL(phone,'') LIKE ? "
            "ORDER BY last_seen DESC LIMIT ?",
            (like, like, limit),
        )
        for row in rows:
            row["sources"] = json.loads(row["sources"])
        return rows

    def contact(self, email: str) -> Optional[Dict[str, Any]]:
        address = normalise_email(email)
        if not address:
            return None
        rows = self._rows("SELECT * FROM contacts WHERE email=?", (address,))
        if not rows:
            return None
        rows[0]["sources"] = json.loads(rows[0]["sources"])
        return rows[0]

    # --- tickets ---------------------------------------------------------

    def add_ticket(
        self,
        *,
        kind: str,
        email: Optional[str],
        message: str,
        exam: str = "",
        reference: Optional[str] = None,
        payment_reference: Optional[str] = None,
        order_id: Optional[str] = None,
        created_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        if kind not in TICKET_KINDS:
            raise ValueError(f"unknown ticket kind {kind!r}")
        ticket_id = f"t_{uuid.uuid4().hex[:12]}"
        address = normalise_email(email)
        with self._lock, self._db() as db:
            if reference:
                existing = db.execute(
                    "SELECT id FROM tickets WHERE reference=?", (reference,)
                ).fetchone()
                if existing is not None:
                    return self.ticket(str(existing["id"])) or {}
            db.execute(
                "INSERT INTO tickets (id, reference, kind, exam, email, message, "
                "payment_reference, order_id, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    ticket_id,
                    reference,
                    kind,
                    exam[:200],
                    address,
                    message[:3000],
                    (payment_reference or "")[:80] or None,
                    order_id,
                    created_at or now_iso(),
                ),
            )
        self.contact_seen(address, f"form:{kind}")
        return self.ticket(ticket_id) or {}

    def ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        rows = self._rows("SELECT * FROM tickets WHERE id=?", (ticket_id,))
        return _with_clock(rows[0]) if rows else None

    def tickets(
        self,
        *,
        kinds: Optional[List[str]] = None,
        status: Optional[str] = None,
        email: Optional[str] = None,
        order_id: Optional[str] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        clauses: List[str] = []
        args: List[Any] = []
        if kinds:
            clauses.append(f"kind IN ({','.join('?' * len(kinds))})")
            args += kinds
        if status:
            clauses.append("status=?")
            args.append(status)
        if email:
            clauses.append("email=?")
            args.append(normalise_email(email))
        if order_id:
            clauses.append("order_id=?")
            args.append(order_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._rows(
            f"SELECT * FROM tickets {where} ORDER BY created_at DESC LIMIT ?",
            (*args, limit),
        )
        return [_with_clock(row) for row in rows]

    def set_ticket(
        self,
        ticket_id: str,
        *,
        status: Optional[str] = None,
        order_id: Optional[str] = None,
        added: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        current = self.ticket(ticket_id)
        if current is None:
            return None
        stamp = now_iso()
        if status is not None:
            if status not in TICKET_STATES:
                raise ValueError(f"unknown status {status!r}")
            ack = current["acknowledged_at"] or (stamp if status != "open" else None)
            resolved = stamp if status == "resolved" else None
            self._write(
                "UPDATE tickets SET status=?, acknowledged_at=?, resolved_at=? WHERE id=?",
                (status, ack, resolved, ticket_id),
            )
        if order_id is not None:
            self._write(
                "UPDATE tickets SET order_id=? WHERE id=?",
                (order_id or None, ticket_id),
            )
        if added is not None:
            self._write(
                "UPDATE tickets SET added_at=? WHERE id=?",
                (stamp if added else None, ticket_id),
            )
        return self.ticket(ticket_id)

    # --- notes, refunds, activity ---------------------------------------

    def add_note(self, target: str, actor: str, text: str) -> None:
        self._write(
            "INSERT INTO notes (target, at, actor, text) VALUES (?,?,?,?)",
            (target, now_iso(), actor[:200], text[:4000]),
        )

    def notes(self, target: str) -> List[Dict[str, Any]]:
        return self._rows(
            "SELECT at, actor, text FROM notes WHERE target=? ORDER BY at", (target,)
        )

    def mark_refunded(
        self,
        order_id: str,
        actor: str,
        reference: Optional[str],
        amount_paise: Optional[int],
    ) -> None:
        self._write(
            "INSERT OR REPLACE INTO refunds (order_id, at, actor, reference, "
            "amount_paise) VALUES (?,?,?,?,?)",
            (
                order_id,
                now_iso(),
                actor[:200],
                (reference or "")[:80] or None,
                amount_paise,
            ),
        )

    def unmark_refunded(self, order_id: str) -> None:
        self._write("DELETE FROM refunds WHERE order_id=?", (order_id,))

    def refunds(self) -> Dict[str, Dict[str, Any]]:
        return {row["order_id"]: row for row in self._rows("SELECT * FROM refunds")}

    def log(self, actor: str, action: str, target: Optional[str] = None) -> None:
        self._write(
            "INSERT INTO activity (at, actor, action, target) VALUES (?,?,?,?)",
            (now_iso(), actor[:200], action[:200], (target or "")[:300] or None),
        )

    def activity(self, limit: int = 500) -> List[Dict[str, Any]]:
        return self._rows(
            "SELECT at, actor, action, target FROM activity ORDER BY id DESC LIMIT ?",
            (limit,),
        )

    # --- health and alerts ----------------------------------------------

    def sample_health(
        self, status: str, disk_free_bytes: Optional[int], busy_refusals: int
    ) -> None:
        self._write(
            "INSERT OR REPLACE INTO health (at, status, disk_free_bytes, "
            "busy_refusals) VALUES (?,?,?,?)",
            (now_iso(), status, disk_free_bytes, busy_refusals),
        )
        cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
        self._write("DELETE FROM health WHERE at < ?", (cutoff,))

    def health(self, since: str) -> List[Dict[str, Any]]:
        return self._rows("SELECT * FROM health WHERE at >= ? ORDER BY at", (since,))

    def alert_sent(self, key: str) -> bool:
        return bool(self._rows("SELECT 1 FROM alerts_sent WHERE key=?", (key,)))

    def mark_alert_sent(self, key: str) -> None:
        self._write(
            "INSERT OR REPLACE INTO alerts_sent (key, at) VALUES (?,?)",
            (key, now_iso()),
        )

    # --- key/value -------------------------------------------------------

    def get_value(self, key: str) -> Optional[str]:
        rows = self._rows("SELECT value FROM kv WHERE key=?", (key,))
        return str(rows[0]["value"]) if rows else None

    def set_value(self, key: str, value: str) -> None:
        self._write("INSERT OR REPLACE INTO kv (key, value) VALUES (?,?)", (key, value))

    # --- visits (Release 2) ---------------------------------------------

    def record_visit_event(self, event: Dict[str, Any]) -> None:
        """One page view or heartbeat from the site's own beacon (DEC-110)."""
        session = str(event["session_id"])
        stamp = now_iso()
        kind = event.get("type")
        with self._lock, self._db() as db:
            row = db.execute(
                "SELECT kit_ids FROM visits WHERE session_id=?", (session,)
            ).fetchone()
            if row is None:
                db.execute(
                    "INSERT INTO visits (session_id, first_at, last_at, landing, "
                    "referrer_host, utm_source, utm_medium, utm_campaign, device, "
                    "browser, connection) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        session,
                        stamp,
                        stamp,
                        event.get("path"),
                        event.get("referrer_host"),
                        event.get("utm_source"),
                        event.get("utm_medium"),
                        event.get("utm_campaign"),
                        event.get("device"),
                        event.get("browser"),
                        event.get("connection"),
                    ),
                )
                kits: List[str] = []
            else:
                kits = json.loads(row["kit_ids"])
            kit = event.get("kit_id")
            if kit and kit not in kits:
                kits.append(kit)
            seconds = int(event.get("seconds") or 0) if kind == "ping" else 0
            is_view = kind == "view"
            is_exam = bool(
                is_view and str(event.get("path") or "").startswith("/exam/")
            )
            db.execute(
                "UPDATE visits SET last_at=?, active_seconds=active_seconds+?, "
                "pages=pages+?, exam_pages=exam_pages+?, kit_ids=?, "
                "connection=COALESCE(?, connection) WHERE session_id=?",
                (
                    stamp,
                    max(0, min(seconds, 120)),
                    1 if is_view else 0,
                    1 if is_exam else 0,
                    json.dumps(kits[:20]),
                    event.get("connection"),
                    session,
                ),
            )
            if is_view:
                db.execute(
                    "INSERT INTO pageviews (session_id, at, path) VALUES (?,?,?)",
                    (session, stamp, str(event.get("path") or "/")[:300]),
                )

    def record_empty_search(self, query: str) -> None:
        text = " ".join(query.split())[:120]
        if len(text) >= 2:
            self._write(
                "INSERT INTO searches (at, query) VALUES (?,?)", (now_iso(), text)
            )

    def visits(self, since: str) -> List[Dict[str, Any]]:
        rows = self._rows("SELECT * FROM visits WHERE first_at >= ?", (since,))
        for row in rows:
            row["kit_ids"] = json.loads(row["kit_ids"])
        return rows

    def empty_searches(self, since: str) -> List[Dict[str, Any]]:
        return self._rows(
            "SELECT lower(query) AS query, COUNT(*) AS count, MAX(at) AS last_at "
            "FROM searches WHERE at >= ? GROUP BY lower(query) ORDER BY count DESC LIMIT 200",
            (since,),
        )

    def prune_visits(self, keep_days: int = 400) -> None:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=keep_days)).isoformat()
        self._write("DELETE FROM pageviews WHERE at < ?", (cutoff,))

    # --- deadlines -------------------------------------------------------

    def set_deadline(
        self,
        exam_id: str,
        closes_on: Optional[str],
        note: str,
        auto_remind: bool,
        actor: str,
    ) -> None:
        if not closes_on:
            self._write("DELETE FROM deadlines WHERE exam_id=?", (exam_id,))
            return
        self._write(
            "INSERT OR REPLACE INTO deadlines (exam_id, closes_on, note, auto_remind, "
            "set_by, set_at) VALUES (?,?,?,?,?,?)",
            (exam_id, closes_on, note[:300], 1 if auto_remind else 0, actor, now_iso()),
        )

    def deadlines(self) -> Dict[str, Dict[str, Any]]:
        return {row["exam_id"]: row for row in self._rows("SELECT * FROM deadlines")}

    # --- coupons (Release 3) --------------------------------------------

    def save_coupon(
        self,
        code: str,
        kind: str,
        value: int,
        partner: str = "",
        max_uses: Optional[int] = None,
        expires_on: Optional[str] = None,
    ) -> None:
        self._write(
            "INSERT INTO coupons (code, kind, value, partner, max_uses, expires_on, "
            "created_at) VALUES (?,?,?,?,?,?,?) ON CONFLICT(code) DO UPDATE SET "
            "kind=excluded.kind, value=excluded.value, partner=excluded.partner, "
            "max_uses=excluded.max_uses, expires_on=excluded.expires_on, active=1",
            (code, kind, value, partner[:120], max_uses, expires_on, now_iso()),
        )

    def set_coupon_active(self, code: str, active: bool) -> None:
        self._write(
            "UPDATE coupons SET active=? WHERE code=?", (1 if active else 0, code)
        )

    def coupon(self, code: str) -> Optional[Dict[str, Any]]:
        rows = self._rows("SELECT * FROM coupons WHERE code=?", (code,))
        return rows[0] if rows else None

    def coupons(self) -> List[Dict[str, Any]]:
        return self._rows("SELECT * FROM coupons ORDER BY created_at DESC")

    def coupon_used(self, code: str) -> None:
        self._write("UPDATE coupons SET uses=uses+1 WHERE code=?", (code,))

    # --- marketing (Release 3) ------------------------------------------

    def suppress(self, email: str, reason: str) -> None:
        address = normalise_email(email)
        if address:
            self._write(
                "INSERT OR REPLACE INTO suppressions (email, at, reason) VALUES (?,?,?)",
                (address, now_iso(), reason[:120]),
            )

    def suppressed(self) -> set[str]:
        return {row["email"] for row in self._rows("SELECT email FROM suppressions")}

    def create_campaign(
        self, actor: str, segment: str, subject: str, body: str, recipients: List[str]
    ) -> str:
        campaign_id = f"c_{uuid.uuid4().hex[:12]}"
        with self._lock, self._db() as db:
            db.execute(
                "INSERT INTO campaigns (id, created_at, actor, segment, subject, body, "
                "status, total) VALUES (?,?,?,?,?,?,?,?)",
                (
                    campaign_id,
                    now_iso(),
                    actor,
                    segment,
                    subject,
                    body,
                    "sending",
                    len(recipients),
                ),
            )
            db.executemany(
                "INSERT OR IGNORE INTO campaign_recipients (campaign_id, email, status) "
                "VALUES (?,?,?)",
                [(campaign_id, email, "queued") for email in recipients],
            )
        return campaign_id

    def campaign_result(
        self, campaign_id: str, email: str, ok: bool, error: Optional[str] = None
    ) -> None:
        with self._lock, self._db() as db:
            db.execute(
                "UPDATE campaign_recipients SET status=?, at=?, error=? "
                "WHERE campaign_id=? AND email=?",
                (
                    "sent" if ok else "failed",
                    now_iso(),
                    (error or "")[:200] or None,
                    campaign_id,
                    email,
                ),
            )
            column = "sent" if ok else "failed"
            db.execute(
                f"UPDATE campaigns SET {column}={column}+1 WHERE id=?", (campaign_id,)
            )

    def finish_campaign(self, campaign_id: str, status: str = "finished") -> None:
        self._write(
            "UPDATE campaigns SET status=?, finished_at=? WHERE id=?",
            (status, now_iso(), campaign_id),
        )

    def campaigns(self) -> List[Dict[str, Any]]:
        return self._rows("SELECT * FROM campaigns ORDER BY created_at DESC LIMIT 200")

    def campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        rows = self._rows("SELECT * FROM campaigns WHERE id=?", (campaign_id,))
        if not rows:
            return None
        campaign = rows[0]
        campaign["recipients"] = self._rows(
            "SELECT email, status, at, error FROM campaign_recipients WHERE campaign_id=? "
            "ORDER BY email",
            (campaign_id,),
        )
        return campaign

    def queued_recipients(self, campaign_id: str) -> List[str]:
        return [
            row["email"]
            for row in self._rows(
                "SELECT email FROM campaign_recipients WHERE campaign_id=? AND status='queued'",
                (campaign_id,),
            )
        ]

    # --- feedback (Release 3) -------------------------------------------

    def record_feedback(
        self, order_id: str, worked: bool, comment: str = "", may_publish: bool = False
    ) -> None:
        self._write(
            "INSERT INTO feedback (order_id, at, worked, comment, may_publish) "
            "VALUES (?,?,?,?,?) ON CONFLICT(order_id) DO UPDATE SET at=excluded.at, "
            "worked=excluded.worked, "
            "comment=CASE WHEN excluded.comment != '' THEN excluded.comment ELSE comment END, "
            "may_publish=MAX(may_publish, excluded.may_publish)",
            (
                order_id,
                now_iso(),
                1 if worked else 0,
                comment[:1000],
                1 if may_publish else 0,
            ),
        )

    def set_feedback_published(self, order_id: str, published: bool) -> None:
        self._write(
            "UPDATE feedback SET published=? WHERE order_id=? AND may_publish=1",
            (1 if published else 0, order_id),
        )

    def feedback(self, published_only: bool = False) -> List[Dict[str, Any]]:
        where = "WHERE published=1" if published_only else ""
        return self._rows(f"SELECT * FROM feedback {where} ORDER BY at DESC LIMIT 500")


def _with_clock(row: Dict[str, Any]) -> Dict[str, Any]:
    """Whether a ticket is past what the grievance page promises."""
    created = parse(row.get("created_at"))
    now = datetime.now(timezone.utc)
    row["ack_overdue"] = bool(
        created
        and row.get("kind") != "exam"
        and not row.get("acknowledged_at")
        and now - created > ACK_WITHIN
    )
    row["resolve_overdue"] = bool(
        created
        and row.get("kind") != "exam"
        and row.get("status") != "resolved"
        and now - created > RESOLVE_WITHIN
    )
    return row
