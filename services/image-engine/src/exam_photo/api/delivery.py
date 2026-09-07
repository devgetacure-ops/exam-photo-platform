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
"""

from __future__ import annotations

import re
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from typing import List, Optional, Protocol, Sequence, Tuple

#: Deliberately permissive. This is a sanity check before handing a string to
#: an SMTP server, not an attempt to decide which addresses exist -- that
#: question has no correct regular expression and the send itself answers it.
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MAX_ATTACHMENT_BYTES = 15 * 1024 * 1024


class EmailRejectedError(Exception):
    """The message could not be sent, with a reason for the operator's log."""


@dataclass(frozen=True)
class Attachment:
    filename: str
    content: bytes
    media_type: str


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
    ) -> None:
        raise EmailRejectedError("email delivery is not configured on this host")


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
    ):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from = from_address
        self._use_tls = use_tls
        self._timeout = timeout_seconds

    def send(
        self,
        to_address: str,
        subject: str,
        body: str,
        attachments: Sequence[Attachment],
    ) -> None:
        message = EmailMessage()
        message["From"] = self._from
        message["To"] = to_address
        message["Subject"] = subject
        message.set_content(body)
        for attachment in attachments:
            maintype, _, subtype = attachment.media_type.partition("/")
            message.add_attachment(
                attachment.content,
                maintype=maintype or "application",
                subtype=subtype or "octet-stream",
                filename=attachment.filename,
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
) -> EmailSender:
    if host and from_address:
        return SmtpEmailSender(host, port, username, password, from_address, use_tls)
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


def compose(
    exam_names: List[str], filenames: List[str], expires_at: Optional[str]
) -> Tuple[str, str]:
    """The subject and body of the delivery message.

    Plain text on purpose. A candidate opening this on a slow phone on the
    morning of a deadline needs the files and the deadline, not a layout.
    """
    subject = "Your prepared files"
    if exam_names:
        subject = f"Your prepared files for {exam_names[0]}"
        if len(exam_names) > 1:
            subject += f" and {len(exam_names) - 1} more"

    lines = [
        "Your files are attached and ready to upload.",
        "",
        "Attached:",
    ]
    lines += [f"  - {name}" for name in filenames]
    lines += [
        "",
        "Upload them exactly as they are. They have been named, sized and",
        "compressed to the examination's own published rules, so renaming or",
        "re-saving them can make them non-compliant.",
        "",
    ]
    if expires_at:
        lines += [
            f"The copies on our servers are deleted at {expires_at}.",
            "This email keeps its attachments after that, so save it.",
            "",
        ]
    lines += ["Good luck with your examination."]
    return subject, "\n".join(lines)
