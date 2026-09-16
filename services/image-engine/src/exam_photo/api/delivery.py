"""Getting the file to the candidate, and remembering that we did.

DEC-072. Two jobs that look separate and are not.

**Delivery**: a candidate who has paid must be able to leave with the file --
downloaded now, or emailed so it survives the thirty-minute window that
DEC-066 enforces. A `wa.me` link is the interface's to build and needs nothing
from here: WhatsApp carries the text, the candidate carries the file.

**Evidence**: the product owner's refund rule is *paid, and not delivered*.
Deciding that needs a record of what actually reached the candidate, and the
record has to outlive the file it describes -- the photograph is erased at
thirty minutes and a claim will arrive after that.

**On what is stored.** A candidate's email address is personal data under the
DPDP Act and we have no use for it once the message is sent, so it is **not
retained**. What is kept is a masked form -- `d***@gmail.com` -- which is
enough to settle "you sent it to the wrong address" and useless for anything
else. The unmasked address exists only in the arguments of the send call.

**On how the message reads** (DEC-102). It is the receipt for something a
candidate paid for, and it arrived looking like a log line: a slug for the
examination, a sender called "files", a UTC timestamp to the microsecond. It is
now a proper transactional email -- a named sender and a reply address, the
examination's own name, each file described, the deletion time in Indian
Standard Time, the order it was paid under -- sent as HTML with a plain-text
twin. The HTML uses tables and inline styles only, with no remote images or web
fonts, so Gmail, Outlook and a phone's mail app draw it the same and none of
them hides anything behind "show images".
"""

from __future__ import annotations

import re
import smtplib
import ssl
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid, parseaddr
from html import escape
from typing import List, Optional, Protocol, Sequence

#: Deliberately permissive. This is a sanity check before handing a string to
#: an SMTP server, not an attempt to decide which addresses exist -- that
#: question has no correct regular expression and the send itself answers it.
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MAX_ATTACHMENT_BYTES = 15 * 1024 * 1024

#: India keeps one offset all year, so a fixed zone is exact and needs no tz
#: database in the container.
IST = timezone(timedelta(hours=5, minutes=30), "IST")

BRAND = "ExamUploadKit"

#: Used when the catalogue has no name for a requirement.
TYPE_LABELS = {
    "photograph": "Photograph",
    "signature": "Signature",
    "thumb_impression": "Thumb impression",
    "handwritten_declaration": "Handwritten declaration",
}


class EmailRejectedError(Exception):
    """The message could not be sent, with a reason for the operator's log."""


@dataclass(frozen=True)
class Attachment:
    filename: str
    content: bytes
    media_type: str


@dataclass(frozen=True)
class DeliveredFile:
    """One attached file, as the message describes it."""

    label: str
    filename: str
    size_bytes: int
    media_type: str
    width: Optional[int] = None
    height: Optional[int] = None


@dataclass(frozen=True)
class Delivery:
    """Everything the message says. Built by the service, rendered here."""

    exam_names: List[str]
    files: List[DeliveredFile]
    expires_at: Optional[str] = None
    order_id: Optional[str] = None
    amount_paise: Optional[int] = None
    payment_reference: Optional[str] = None
    paid_at: Optional[str] = None
    site_url: str = ""
    support_address: str = ""


@dataclass(frozen=True)
class ComposedEmail:
    subject: str
    text: str
    html: str
    preheader: str = ""


def mask_address(address: str) -> str:
    """`dmbonwork@gmail.com` becomes `d***@gmail.com`.

    Kept instead of the address itself: enough to resolve a dispute about
    where a file was sent, and not enough to contact anyone or to be worth
    stealing.
    """
    address = address.strip()
    if "@" not in address:
        return "***"
    local, _, domain = address.partition("@")
    head = local[:1] if local else ""
    return f"{head}***@{domain}"


class EmailSender(Protocol):
    def send(
        self,
        to_address: str,
        subject: str,
        body: str,
        attachments: Sequence[Attachment],
        html: Optional[str] = None,
    ) -> None: ...


class UnconfiguredEmailSender:
    """What a host without SMTP settings gets.

    Refuses rather than silently succeeding, following DEC-060. A delivery
    path that reports success while sending nothing is worse than one that is
    plainly switched off, because the candidate is told their file is on the
    way.
    """

    def send(
        self,
        to_address: str,
        subject: str,
        body: str,
        attachments: Sequence[Attachment],
        html: Optional[str] = None,
    ) -> None:
        raise EmailRejectedError("email delivery is not configured on this host")


def build_message(
    *,
    from_address: str,
    from_name: str,
    reply_to: str,
    to_address: str,
    subject: str,
    body: str,
    attachments: Sequence[Attachment],
    html: Optional[str] = None,
) -> EmailMessage:
    """The message as it goes on the wire. Pure, so its headers can be tested.

    `multipart/mixed` holding `multipart/alternative` (text, then HTML, so a
    client that can draw HTML prefers it) and then the files.
    """
    message = EmailMessage()
    _, bare_from = parseaddr(from_address)
    bare_from = bare_from or from_address
    # A configured "Name <address>" is kept as it is; a bare address gets the
    # brand as its name, so the inbox shows "ExamUploadKit" and not "files".
    if "<" in from_address or not from_name:
        message["From"] = from_address
    else:
        message["From"] = formataddr((from_name, bare_from))
    message["To"] = to_address
    if reply_to:
        message["Reply-To"] = reply_to
    message["Subject"] = subject
    message["Date"] = formatdate(usegmt=True)
    domain = bare_from.rpartition("@")[2] or None
    message["Message-ID"] = make_msgid(domain=domain)
    # Transactional, sent because the candidate asked: an out-of-office
    # should not answer it.
    message["Auto-Submitted"] = "auto-generated"
    message.set_content(body)
    if html:
        message.add_alternative(html, subtype="html")
    for attachment in attachments:
        maintype, _, subtype = attachment.media_type.partition("/")
        message.add_attachment(
            attachment.content,
            maintype=maintype or "application",
            subtype=subtype or "octet-stream",
            filename=attachment.filename,
        )
    return message


class SmtpEmailSender:
    """Sends over SMTP, using the standard library and no new dependency."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_address: str,
        use_tls: bool = True,
        timeout_seconds: float = 20.0,
        from_name: str = BRAND,
        reply_to: str = "",
    ):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from = from_address
        self._use_tls = use_tls
        self._timeout = timeout_seconds
        self._from_name = from_name
        self._reply_to = reply_to

    def send(
        self,
        to_address: str,
        subject: str,
        body: str,
        attachments: Sequence[Attachment],
        html: Optional[str] = None,
    ) -> None:
        message = build_message(
            from_address=self._from,
            from_name=self._from_name,
            reply_to=self._reply_to,
            to_address=to_address,
            subject=subject,
            body=body,
            attachments=attachments,
            html=html,
        )

        try:
            if self._use_tls:
                with smtplib.SMTP(
                    self._host, self._port, timeout=self._timeout
                ) as server:
                    server.starttls(context=ssl.create_default_context())
                    if self._username:
                        server.login(self._username, self._password)
                    server.send_message(message)
            else:
                with smtplib.SMTP(
                    self._host, self._port, timeout=self._timeout
                ) as server:
                    if self._username:
                        server.login(self._username, self._password)
                    server.send_message(message)
        except Exception as err:
            raise EmailRejectedError(f"SMTP send failed: {err}") from err


def sender_for(
    host: str,
    port: int,
    username: str,
    password: str,
    from_address: str,
    use_tls: bool = True,
    from_name: str = BRAND,
    reply_to: str = "",
) -> EmailSender:
    if host and from_address:
        return SmtpEmailSender(
            host,
            port,
            username,
            password,
            from_address,
            use_tls,
            from_name=from_name,
            reply_to=reply_to,
        )
    return UnconfiguredEmailSender()


def validate_address(address: str) -> str:
    address = (address or "").strip()
    if not EMAIL_REGEX.match(address) or len(address) > 254:
        raise EmailRejectedError("that does not look like an email address")
    return address


def check_attachment_budget(attachments: Sequence[Attachment]) -> None:
    total = sum(len(item.content) for item in attachments)
    if total > MAX_ATTACHMENT_BYTES:
        raise EmailRejectedError("the files are too large to send by email")


# ----------------------------------------------------------------------
# Words
# ----------------------------------------------------------------------


def human_deadline(expires_at: Optional[str]) -> Optional[str]:
    """`2026-09-16T12:29:37.616392+00:00` becomes `16 September 2026, 5:59 pm IST`.

    `None` for a value that cannot be read, rather than printing it raw: a
    machine timestamp in a candidate's inbox is exactly what this replaced.
    """
    if not expires_at:
        return None
    try:
        moment = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    local = moment.astimezone(IST)
    hour = local.hour % 12 or 12
    meridiem = "am" if local.hour < 12 else "pm"
    return f"{local.day} {local:%B %Y}, {hour}:{local:%M} {meridiem} IST"


def human_size(size_bytes: int) -> str:
    """Kilobytes as the site counts them: 1 KB is 1000 bytes (DEC-096)."""
    kb = size_bytes / 1000
    if kb < 10:
        return f"{kb:.1f} KB"
    if kb < 1000:
        return f"{round(kb)} KB"
    return f"{kb / 1000:.1f} MB"


def human_format(media_type: str, filename: str) -> str:
    if media_type == "application/pdf":
        return "PDF"
    if media_type == "image/png":
        return "PNG"
    if media_type in ("image/jpeg", "image/jpg"):
        return "JPEG"
    extension = filename.rpartition(".")[2].upper()
    return "JPEG" if extension == "JPG" else (extension or "File")


def file_facts(item: DeliveredFile) -> str:
    parts = []
    if item.width and item.height:
        parts.append(f"{item.width} × {item.height} px")
    parts.append(human_size(item.size_bytes))
    parts.append(human_format(item.media_type, item.filename))
    return " · ".join(parts)


def rupees(paise: int) -> str:
    whole, part = divmod(paise, 100)
    return f"₹{whole}" if part == 0 else f"₹{whole}.{part:02d}"


def _exam_phrase(exam_names: List[str]) -> str:
    if not exam_names:
        return ""
    if len(exam_names) == 1:
        return exam_names[0]
    return f"{exam_names[0]} and {len(exam_names) - 1} more"


def compose(delivery: Delivery) -> ComposedEmail:
    """The subject, plain text and HTML of the delivery message."""
    exam = _exam_phrase(delivery.exam_names)
    count = len(delivery.files)
    noun = "file" if count == 1 else "files"
    verb = "is" if count == 1 else "are"
    subject = (
        f"Your {exam} {noun} {verb} ready"
        if exam
        else f"Your prepared {noun} {verb} ready"
    )
    deadline = human_deadline(delivery.expires_at)
    paid = delivery.amount_paise is not None and delivery.amount_paise > 0
    preheader = f"{count} {noun} attached, ready to upload." + (
        f" Save this email: our copy is deleted on {deadline}." if deadline else ""
    )

    # --- plain text --------------------------------------------------------
    lines: List[str] = [
        BRAND.upper(),
        "",
        f"Your {exam} {noun} {'is' if count == 1 else 'are'} attached."
        if exam
        else f"Your {noun} {'is' if count == 1 else 'are'} attached.",
        "",
        "Prepared to the examination's published rules and ready to upload.",
        "",
        f"ATTACHED ({count})",
    ]
    for item in delivery.files:
        lines += [f"- {item.label}: {item.filename}", f"  {file_facts(item)}"]
    lines += [
        "",
        "Upload them exactly as they are. Renaming, editing or re-saving a file",
        "can change its size or format and make it non-compliant.",
    ]
    if deadline:
        lines += [
            "",
            f"Save this email. Our copy of these files is deleted on {deadline}.",
            "The attachments here stay with you.",
        ]
    if delivery.order_id:
        lines += ["", "RECEIPT", f"Order: {delivery.order_id}"]
        if paid:
            lines.append(f"Paid: {rupees(int(delivery.amount_paise or 0))}")
        if delivery.payment_reference:
            lines.append(f"Payment: {delivery.payment_reference}")
    lines += [
        "",
        f"All the best for {exam}." if exam else "All the best for your examination.",
    ]
    lines += ["", "--"]
    if delivery.support_address:
        lines.append(
            f"Questions? Reply to this email or write to {delivery.support_address}."
        )
    lines.append(
        "You asked for these files to be emailed to you. We used your address "
        "to send this message and did not store it."
    )
    if delivery.site_url:
        lines.append(delivery.site_url.rstrip("/"))
    text = "\n".join(lines)

    html = _html(delivery, exam, count, noun, deadline, paid, preheader)
    return ComposedEmail(subject=subject, text=text, html=html, preheader=preheader)


# ----------------------------------------------------------------------
# HTML
# ----------------------------------------------------------------------

INK = "#111110"
MUTED = "#55524b"
PAPER = "#faf9f6"
GROUND = "#efece4"
RULE = "#dedacf"
SIGNAL = "#f04e23"
SIGNAL_DEEP = "#c1370e"
FONT = (
    "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',"
    "Arial,sans-serif"
)
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"


def _html(
    delivery: Delivery,
    exam: str,
    count: int,
    noun: str,
    deadline: Optional[str],
    paid: bool,
    preheader: str,
) -> str:
    e = escape
    site = delivery.site_url.rstrip("/")
    heading = (
        f"Your {e(exam)} {noun} {'is' if count == 1 else 'are'} ready"
        if exam
        else f"Your {noun} {'is' if count == 1 else 'are'} ready"
    )

    rows = []
    for index, item in enumerate(delivery.files):
        top = f"border-top:1px solid {RULE};" if index else ""
        rows.append(
            f"""<tr><td style="{top}padding:14px 0;">
<div style="font:600 15px/1.35 {FONT};color:{INK};">{e(item.label)}</div>
<div style="font:13px/1.5 {MONO};color:{INK};padding-top:3px;word-break:break-all;">{e(item.filename)}</div>
<div style="font:13px/1.5 {FONT};color:{MUTED};padding-top:1px;">{e(file_facts(item))}</div>
</td></tr>"""
        )

    deadline_block = ""
    if deadline:
        deadline_block = f"""<tr><td style="padding:0 32px 8px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">
<tr><td style="border-left:4px solid {SIGNAL};background:{GROUND};padding:14px 16px;">
<div style="font:700 14px/1.4 {FONT};color:{INK};">Save this email</div>
<div style="font:14px/1.55 {FONT};color:{INK};padding-top:4px;">Our copy of these files is deleted on <strong>{e(deadline)}</strong>. The attachments in this email stay with you.</div>
</td></tr></table></td></tr>"""

    receipt_block = ""
    if delivery.order_id:
        receipt_rows = [("Order", delivery.order_id)]
        if paid:
            receipt_rows.append(("Paid", rupees(int(delivery.amount_paise or 0))))
        if delivery.payment_reference:
            receipt_rows.append(("Payment", delivery.payment_reference))
        cells = "".join(
            f"""<tr><td style="font:13px/1.6 {FONT};color:{MUTED};padding:2px 16px 2px 0;white-space:nowrap;">{e(k)}</td><td style="font:13px/1.6 {MONO};color:{INK};padding:2px 0;word-break:break-all;">{e(v)}</td></tr>"""
            for k, v in receipt_rows
        )
        receipt_block = f"""<tr><td style="padding:20px 32px 0;">
<div style="font:700 11px/1 {FONT};letter-spacing:.12em;text-transform:uppercase;color:{MUTED};padding-bottom:8px;">Receipt</div>
<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">{cells}</table>
</td></tr>"""

    support = ""
    if delivery.support_address:
        address = e(delivery.support_address)
        support = f"""Questions? Reply to this email or write to <a href="mailto:{address}" style="color:{INK};text-decoration:underline;">{address}</a>.<br>"""
    brand = (
        f'<a href="{e(site)}" style="color:{INK};text-decoration:none;">{BRAND.upper()}</a>'
        if site
        else BRAND.upper()
    )
    site_link = (
        f'<br><a href="{e(site)}" style="color:{MUTED};text-decoration:underline;">{e(site.split("://", 1)[-1])}</a>'
        if site
        else ""
    )
    wish = (
        f"All the best for {e(exam)}." if exam else "All the best for your examination."
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<title>{heading}</title>
</head>
<body style="margin:0;padding:0;background:{GROUND};-webkit-text-size-adjust:100%;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:{GROUND};">{e(preheader)}&#8199;&#65279;&#847;&#8199;&#65279;&#847;&#8199;&#65279;&#847;</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{GROUND};border-collapse:collapse;">
<tr><td align="center" style="padding:28px 12px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;background:{PAPER};border:2px solid {INK};border-collapse:collapse;">
<tr><td style="padding:22px 32px 18px;border-bottom:2px solid {INK};">
<div style="font:800 15px/1 {FONT};letter-spacing:.24em;color:{INK};">{brand}</div>
</td></tr>
<tr><td style="height:5px;line-height:5px;font-size:0;background:{SIGNAL};">&nbsp;</td></tr>
<tr><td style="padding:30px 32px 6px;">
<div style="font:700 11px/1 {FONT};letter-spacing:.12em;text-transform:uppercase;color:{SIGNAL_DEEP};">Files delivered</div>
<h1 style="margin:10px 0 0;font:800 26px/1.2 {FONT};color:{INK};">{heading}</h1>
<p style="margin:12px 0 0;font:15px/1.6 {FONT};color:{INK};">{"It is" if count == 1 else "They are"} attached to this email, prepared to the examination&rsquo;s published rules and ready to upload as {"it is" if count == 1 else "they are"}.</p>
</td></tr>
<tr><td style="padding:22px 32px 4px;">
<div style="font:700 11px/1 {FONT};letter-spacing:.12em;text-transform:uppercase;color:{MUTED};padding-bottom:4px;">Attached ({count})</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;border-top:2px solid {INK};border-bottom:2px solid {INK};">
{"".join(rows)}
</table>
</td></tr>
<tr><td style="padding:14px 32px 18px;">
<p style="margin:0;font:14px/1.55 {FONT};color:{MUTED};">Upload {"it" if count == 1 else "them"} exactly as {"it is" if count == 1 else "they are"}. Renaming, editing or re-saving a file can change its size or format and make it non-compliant.</p>
</td></tr>
{deadline_block}
{receipt_block}
<tr><td style="padding:26px 32px 30px;">
<p style="margin:0;font:700 16px/1.4 {FONT};color:{INK};">{wish}</p>
</td></tr>
<tr><td style="padding:18px 32px 22px;border-top:2px solid {INK};background:{GROUND};">
<p style="margin:0;font:12px/1.65 {FONT};color:{MUTED};">{support}You asked for these files to be emailed to you. We used your address to send this message and did not store it.{site_link}</p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""
