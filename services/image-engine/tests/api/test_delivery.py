"""Getting the file to the candidate, and proving we did (DEC-072).

Two things are pinned here. That a paid file can leave by email, so it
outlives the thirty-minute window DEC-066 enforces. And that what left is
recorded, because the product owner's refund rule is *paid, and not
delivered*, and deciding that needs evidence rather than a conversation.

The privacy property is pinned as hard as the delivery one: **the address is
used and not stored.**
"""

import pytest
from fastapi.testclient import TestClient

from exam_photo.api.app import app
from exam_photo.api.contracts import ApiJobStatus, JobEntitlement
from exam_photo.api.delivery import (
    EmailRejectedError,
    UnconfiguredEmailSender,
    mask_address,
    sender_for,
    validate_address,
)
from exam_photo.api.jobs import JobRegistry
from exam_photo.api.settings import ApiSettings
from exam_photo.api.storage import LocalArtifactStore

client = TestClient(app, raise_server_exceptions=False)

KIT = "kit_delivery"
OPERATOR = "operator-token"


class FakeSender:
    """Records what it was asked to send. Never opens a socket."""

    def __init__(self, fail: bool = False):
        self.sent: list[dict] = []
        self.fail = fail

    def send(self, to_address, subject, body, attachments, html=None):
        if self.fail:
            raise EmailRejectedError("SMTP send failed: connection refused")
        self.sent.append(
            {
                "to": to_address,
                "subject": subject,
                "body": body,
                "html": html,
                "filenames": [item.filename for item in attachments],
                "bytes": sum(len(item.content) for item in attachments),
            }
        )


@pytest.fixture
def api(tmp_path):
    from exam_photo.api.app import service

    original = (
        service.settings,
        service.store,
        service.registry,
        service.orders,
        service._email_sender,
    )
    service.settings = ApiSettings(
        artifact_root=tmp_path / "artifacts", operator_token=OPERATOR
    )
    service.store = LocalArtifactStore(tmp_path / "artifacts")
    service.registry = JobRegistry(tmp_path / "artifacts")
    from exam_photo.api.orders import OrderRegistry

    service.orders = OrderRegistry(tmp_path / "artifacts")
    service.email_sender = FakeSender()
    try:
        yield service
    finally:
        (
            service.settings,
            service.store,
            service.registry,
            service.orders,
            service._email_sender,
        ) = original


def _job(api, job_id, released=True, kind="photograph"):
    record = api.registry.create_job(job_id, 1800)
    record.status = ApiJobStatus.SUCCEEDED
    record.kit_id = KIT
    record.exam_id = "ctet-september-2026"
    record.requirement_type = kind
    record.output_filename = f"{job_id}.jpg"
    record.output_media_type = "image/jpeg"
    if released:
        record.entitlement = JobEntitlement.RELEASED
    api.store.write_file(job_id, f"{job_id}.jpg", b"\xff\xd8\xff\xdb-prepared-bytes")
    api.registry.update_job(record)
    return record


# ----------------------------------------------------------------------
# The address is used and not stored
# ----------------------------------------------------------------------


def test_the_address_is_never_written_to_the_manifest(api):
    """DPDP: personal data with no use after the send is not retained."""
    _job(api, "job_a")

    client.post(f"/v1/kits/{KIT}/email", json={"address": "candidate@example.com"})

    manifest = (api.settings.artifact_root / "job_a" / "job.json").read_text(
        encoding="utf-8"
    )
    assert "candidate@example.com" not in manifest
    assert "c***@example.com" in manifest


def test_masking_keeps_only_what_settles_a_dispute():
    assert mask_address("dmbonwork@gmail.com") == "d***@gmail.com"
    assert mask_address("a@b.co") == "a***@b.co"
    assert mask_address("not-an-address") == "***"


def test_a_malformed_address_is_refused_before_any_send(api):
    _job(api, "job_a")

    response = client.post(f"/v1/kits/{KIT}/email", json={"address": "not-an-email"})

    assert response.status_code == 422
    assert api.email_sender.sent == []


def test_address_validation_rejects_the_obvious_cases():
    for bad in ("", "  ", "no-at-sign", "a@b", "a@@b.com", "x" * 250 + "@b.com"):
        with pytest.raises(EmailRejectedError):
            validate_address(bad)
    assert validate_address("  ok@example.com  ") == "ok@example.com"


# ----------------------------------------------------------------------
# Only paid files leave
# ----------------------------------------------------------------------


def test_a_paid_file_is_sent(api):
    _job(api, "job_a")

    body = client.post(
        f"/v1/kits/{KIT}/email", json={"address": "candidate@example.com"}
    ).json()

    assert body["sent"] is True
    assert body["masked_address"] == "c***@example.com"
    assert api.email_sender.sent[0]["filenames"] == ["job_a.jpg"]


def test_an_unpaid_file_is_never_emailed(api):
    """Emailing the clean file before payment is the purchase gate with a hole."""
    _job(api, "job_unpaid", released=False)

    response = client.post(
        f"/v1/kits/{KIT}/email", json={"address": "candidate@example.com"}
    )

    assert response.status_code == 422
    assert api.email_sender.sent == []


def test_only_the_paid_files_in_a_mixed_kit_are_sent(api):
    _job(api, "job_paid")
    _job(api, "job_unpaid", released=False)

    body = client.post(
        f"/v1/kits/{KIT}/email", json={"address": "candidate@example.com"}
    ).json()

    assert body["job_ids"] == ["job_paid"]


def test_an_expired_file_is_not_emailed(api):
    from datetime import datetime, timedelta, timezone

    record = _job(api, "job_gone")
    record.expires_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    api.registry.update_job(record)

    assert (
        client.post(
            f"/v1/kits/{KIT}/email", json={"address": "candidate@example.com"}
        ).status_code
        == 422
    )


def test_the_message_names_the_deadline_so_the_candidate_keeps_the_email(api):
    _job(api, "job_a")

    client.post(f"/v1/kits/{KIT}/email", json={"address": "candidate@example.com"})

    body = api.email_sender.sent[0]["body"]
    assert "Save this email" in body
    assert "is deleted" in body
    assert "IST" in body


# ----------------------------------------------------------------------
# How the message reads (DEC-102)
# ----------------------------------------------------------------------


def test_the_deadline_is_written_for_a_person_in_indian_time():
    from exam_photo.api.delivery import human_deadline

    assert (
        human_deadline("2026-09-16T12:29:37.616392+00:00")
        == "16 September 2026, 5:59 pm IST"
    )
    assert (
        human_deadline("2026-09-16T00:05:00+00:00") == "16 September 2026, 5:35 am IST"
    )
    assert human_deadline("2026-09-16T06:30:00Z") == "16 September 2026, 12:00 pm IST"
    # Never the raw value: unreadable is left out, not printed.
    assert human_deadline("not a time") is None


def test_the_message_uses_the_examination_name_and_describes_each_file():
    from exam_photo.api.delivery import DeliveredFile, Delivery, compose

    email = compose(
        Delivery(
            exam_names=["NEET (UG) 2026"],
            files=[
                DeliveredFile(
                    label="Candidate photograph",
                    filename="neet-ug_photo.jpg",
                    size_bytes=124_600,
                    media_type="image/jpeg",
                    width=413,
                    height=531,
                )
            ],
            expires_at="2026-09-16T12:29:37+00:00",
            order_id="order_TchUYmPbD9Irz2",
            amount_paise=300,
            payment_reference="pay_TchUfQ2g3gW6gY",
            site_url="https://examuploadkit.com",
            support_address="support@examuploadkit.com",
        )
    )

    assert email.subject == "Your NEET (UG) 2026 file is ready"
    for part in (email.text, email.html):
        assert "neet-ug-2026" not in part
        assert "+00:00" not in part
        assert "Candidate photograph" in part
        assert "neet-ug_photo.jpg" in part
        assert "413 × 531 px · 125 KB · JPEG" in part
        assert "16 September 2026, 5:59 pm IST" in part
        assert "order_TchUYmPbD9Irz2" in part
        assert "₹3" in part
        assert "support@examuploadkit.com" in part
        assert "did not store it" in part
    assert email.html.startswith("<!doctype html>")
    assert "http://" not in email.html and "<img" not in email.html


def test_what_a_candidate_typed_is_never_markup_in_the_message():
    from exam_photo.api.delivery import DeliveredFile, Delivery, compose

    email = compose(
        Delivery(
            exam_names=["<script>alert(1)</script>"],
            files=[
                DeliveredFile(
                    label="Photo",
                    filename='x"><b>.jpg',
                    size_bytes=1,
                    media_type="image/jpeg",
                )
            ],
        )
    )
    assert "<script>" not in email.html
    assert '"><b>' not in email.html


def test_a_kit_that_was_not_paid_for_carries_no_receipt():
    from exam_photo.api.delivery import DeliveredFile, Delivery, compose

    email = compose(
        Delivery(
            exam_names=["CTET"],
            files=[
                DeliveredFile(
                    label="Signature",
                    filename="s.jpg",
                    size_bytes=9000,
                    media_type="image/jpeg",
                ),
                DeliveredFile(
                    label="Photograph",
                    filename="p.jpg",
                    size_bytes=90000,
                    media_type="image/jpeg",
                ),
            ],
        )
    )
    assert email.subject == "Your CTET files are ready"
    assert "Receipt" not in email.html and "RECEIPT" not in email.text
    assert "9.0 KB" in email.text and "90 KB" in email.text


def test_the_wire_message_has_a_named_sender_a_reply_address_and_both_bodies():
    from exam_photo.api.delivery import Attachment, build_message

    message = build_message(
        from_address="files@examuploadkit.com",
        from_name="ExamUploadKit",
        reply_to="support@examuploadkit.com",
        to_address="candidate@example.com",
        subject="Your CTET file is ready",
        body="text version",
        html="<!doctype html><p>html version</p>",
        attachments=[Attachment("p.jpg", b"\xff\xd8\xff", "image/jpeg")],
    )
    assert message["From"] == "ExamUploadKit <files@examuploadkit.com>"
    assert message["Reply-To"] == "support@examuploadkit.com"
    assert message["Message-ID"].endswith("@examuploadkit.com>")
    assert message["Date"]
    assert message.get_content_type() == "multipart/mixed"
    kinds = [part.get_content_type() for part in message.walk()]
    assert kinds.index("text/plain") < kinds.index("text/html")
    assert "image/jpeg" in kinds
    assert [part.get_filename() for part in message.iter_attachments()] == ["p.jpg"]


def test_a_configured_display_name_is_kept_as_it_is():
    from exam_photo.api.delivery import build_message

    message = build_message(
        from_address="Exam Files <files@examuploadkit.com>",
        from_name="ExamUploadKit",
        reply_to="",
        to_address="c@example.com",
        subject="s",
        body="b",
        attachments=[],
    )
    assert message["From"] == "Exam Files <files@examuploadkit.com>"
    assert message["Reply-To"] is None


def test_the_email_names_the_examination_and_the_order_that_paid_for_it(api):
    from exam_photo.api.orders import OrderRegistry

    record = _job(api, "job_named")
    record.requirement_id = "candidate_photograph"
    record.output_width, record.output_height = 413, 531
    api.registry.update_job(record)
    orders: OrderRegistry = api.orders
    orders.create(
        order_id="order_named1",
        kit_id=KIT,
        job_ids=["job_named"],
        amount_paise=300,
        currency="INR",
    )
    orders.mark_paid("order_named1", "pay_named1")

    client.post(f"/v1/kits/{KIT}/email", json={"address": "candidate@example.com"})

    sent = api.email_sender.sent[0]
    assert sent["subject"] == "Your CTET September 2026 file is ready"
    assert "Candidate photograph" in sent["body"]
    assert "order_named1" in sent["body"] and "pay_named1" in sent["html"]
    assert "413 × 531 px" in sent["body"]


# ----------------------------------------------------------------------
# Evidence: what actually reached the candidate
# ----------------------------------------------------------------------


def test_a_download_is_recorded(api):
    _job(api, "job_a")

    assert client.get("/v1/jobs/job_a/output").status_code == 200

    record = api.registry.get_job("job_a")
    assert record.download_count == 1
    assert record.first_downloaded_at


def test_repeat_downloads_count_but_the_first_time_is_kept(api):
    _job(api, "job_a")

    client.get("/v1/jobs/job_a/output")
    first = api.registry.get_job("job_a").first_downloaded_at
    client.get("/v1/jobs/job_a/output")

    record = api.registry.get_job("job_a")
    assert record.download_count == 2
    assert record.first_downloaded_at == first


def test_a_failed_send_is_recorded_as_a_failure(api):
    """A refund claim after a bounced send must find the bounce."""
    _job(api, "job_a")
    api.email_sender = FakeSender(fail=True)

    response = client.post(
        f"/v1/kits/{KIT}/email", json={"address": "candidate@example.com"}
    )

    assert response.status_code == 422
    attempts = api.registry.get_job("job_a").email_attempts
    assert len(attempts) == 1
    assert attempts[0].succeeded is False
    assert "connection refused" in attempts[0].error


def test_the_order_records_that_something_reached_the_candidate(api):
    api.orders.create("order_ABC", KIT, ["job_a"], 300, "INR")
    _job(api, "job_a")

    client.get("/v1/jobs/job_a/output")

    order = api.orders.get("order_ABC")
    assert order.delivered_at and order.delivery_method == "download"


def test_the_first_delivery_is_the_one_recorded(api):
    api.orders.create("order_ABC", KIT, ["job_a"], 300, "INR")
    _job(api, "job_a")

    client.get("/v1/jobs/job_a/output")
    first = api.orders.get("order_ABC").delivered_at
    client.post(f"/v1/kits/{KIT}/email", json={"address": "candidate@example.com"})

    order = api.orders.get("order_ABC")
    assert order.delivered_at == first
    assert order.delivery_method == "download"


def test_delivery_evidence_survives_the_file_it_describes(api):
    """A claim arrives after thirty minutes. The evidence must still be there."""
    from datetime import datetime, timedelta, timezone

    api.orders.create("order_ABC", KIT, ["job_a"], 300, "INR")
    _job(api, "job_a")
    client.get("/v1/jobs/job_a/output")

    record = api.registry.get_job("job_a")
    record.expires_at = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    api.registry.update_job(record)
    assert client.get("/v1/jobs/job_a/output").status_code == 404

    order = api.orders.get("order_ABC")
    assert order.delivered_at is not None


# ----------------------------------------------------------------------
# The operator's view
# ----------------------------------------------------------------------


def test_the_evidence_endpoint_is_operator_only(api):
    api.orders.create("order_ABC", KIT, ["job_a"], 300, "INR")

    assert client.get("/v1/orders/order_ABC/evidence").status_code == 401


def test_the_evidence_endpoint_answers_the_refund_question(api):
    api.orders.create("order_ABC", KIT, ["job_a"], 300, "INR")
    api.orders.mark_paid("order_ABC", "pay_123")
    _job(api, "job_a")
    client.get("/v1/jobs/job_a/output")

    body = client.get(
        "/v1/orders/order_ABC/evidence",
        headers={"X-Operator-Token": OPERATOR},
    ).json()

    assert body["paid_at"] and body["payment_reference"] == "pay_123"
    assert body["delivered_at"] and body["delivery_method"] == "download"
    assert body["jobs"][0]["download_count"] == 1


def test_evidence_for_an_unknown_order_is_404(api):
    assert (
        client.get(
            "/v1/orders/order_nope/evidence",
            headers={"X-Operator-Token": OPERATOR},
        ).status_code
        == 404
    )


# ----------------------------------------------------------------------
# The sender a host's configuration entitles it to
# ----------------------------------------------------------------------


def test_a_host_without_smtp_refuses_rather_than_pretending():
    """DEC-060: telling a candidate their file is on the way, and sending
    nothing, is worse than being plainly switched off."""
    sender = sender_for("", 587, "", "", "")

    assert isinstance(sender, UnconfiguredEmailSender)
    with pytest.raises(EmailRejectedError, match="not configured"):
        sender.send("a@b.com", "s", "b", [])


def test_smtp_settings_produce_a_real_sender():
    from exam_photo.api.delivery import SmtpEmailSender

    sender = sender_for("smtp.example.com", 587, "u", "p", "from@example.com")
    assert isinstance(sender, SmtpEmailSender)
