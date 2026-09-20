"""API configuration settings module."""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class ApiSettings(BaseModel):
    """Configuration settings for the local API service."""

    artifact_root: Path = Field(default_factory=lambda: Path(".tmp/artifacts"))
    max_upload_bytes: int = Field(default=5 * 1024 * 1024)  # 5 MB
    # DEC-066: thirty minutes, and it is a published promise rather than a
    # convenience default. A candidate who pays and does not download inside
    # the window must prepare the file again; that cost was accepted against
    # holding a face photograph and a signature for twice as long. Access ends
    # at exactly this deadline -- `ProcessingJobRecord.is_expired` is checked
    # on the read path -- and the sweeper erases the bytes behind it.
    job_ttl_seconds: int = Field(default=1800)  # 30 minutes

    # DEC-067: the ceiling a candidate's own extensions cannot pass. Set to
    # 3600 deliberately -- the longest a file can now live, and only because
    # someone asked for it, is exactly what every file used to get
    # unconditionally before DEC-066. So the extension option cannot make the
    # product hold anything longer than it already did, and the default case
    # is half of it.
    job_max_lifetime_seconds: int = Field(default=3600)  # 1 hour

    # Where the encoded examination catalogue is read from (DEC-055).  Relative
    # paths resolve against the repository root, the same way the model paths
    # do.  The directory is still named `examples/rules` while holding the real
    # generated catalogue; renaming it touches the encoder, the gap register
    # and every documented path, so the name is carried rather than changed.
    catalogue_root: Optional[Path] = None

    # Model configuration overrides
    face_model_path: Optional[Path] = None
    segmenter_model_path: Optional[Path] = None
    face_expected_sha256: Optional[str] = None
    segmenter_expected_sha256: Optional[str] = None

    # Subject segmentation backend (DEC-031; faster-matting Step 1). "auto"
    # prefers the ONNX BiRefNet export when it is present (same weights and
    # maths as the PyTorch backend, ~2x faster on CPU, no torch dependency),
    # then the PyTorch backend, and otherwise **raises** rather than falling
    # back to MediaPipe: a paid output never comes from the coarse backend
    # (DEC-060). MediaPipe stays selectable explicitly for diagnostics.
    matting_backend: str = "auto"

    # The purchase gate (DEC-063). On by default, for the reason DEC-060
    # records about `model-assets/`: a fresh clone and a fresh deployment host
    # start in exactly the state an insecure default would ship, and a gate
    # that has to be switched on is a gate that will be off in production.
    # Switch it off for engine quality work -- judging a matte on a
    # watermarked half-resolution copy is judging it on the wrong thing.
    purchase_gate_enabled: bool = True

    # Pipeline output and local CORS toggles
    allow_invalid_output_save: bool = False
    local_cors_enabled: bool = False

    # --- Deployment hardening (DEC-064) -----------------------------------

    #: Browser origins allowed to call the API.  Empty means the two localhost
    #: development origins, which is what `local_cors_enabled` has always
    #: meant.  A real deployment either lists its domain here or -- better --
    #: serves the app and the engine from one origin behind a reverse proxy,
    #: where CORS never enters into it.
    allowed_origins: List[str] = Field(default_factory=list)

    #: Run one real inference at boot so a candidate does not pay the
    #: first-inference cost.  Measured on this codebase: 48.8 s for the first
    #: segmentation in a process against 7.7 s for the second.
    warmup_on_boot: bool = True

    #: How often the expired-artifact sweeper runs.  Nothing swept before
    #: this: `POST /v1/cleanup-expired` existed and no caller invoked it, so
    #: `expires_at` was an assertion the service never acted on.
    cleanup_interval_seconds: int = 300

    #: Shared secret for the operator surface (`/v1/process`,
    #: `/v1/rules/validate`, `/v1/cleanup-expired`, `/test`).  Empty leaves
    #: them open, which is right for local development and wrong in public;
    #: `GET /ready` reports which of the two a running process is in.
    #: It deliberately does not gate the candidate surface -- a browser would
    #: have to carry the token and would hand it to anyone opening the network
    #: tab.
    operator_token: str = ""

    # DEC-069. The Razorpay webhook's shared secret. Empty means the webhook
    # route refuses every request rather than accepting unsigned ones: the
    # whole reason DEC-063 declined to write a release route is that an
    # unauthenticated one reads as protection and is none, and a secret that
    # defaults to "accept anything" would reintroduce exactly that.
    razorpay_webhook_secret: str = ""

    # DEC-070. The API credentials used to create orders server-side, at a
    # price the service computes. `key_id` is publishable and reaches the
    # browser; `key_secret` never leaves the process. Both empty means order
    # creation refuses rather than pretending, so a host without them cannot
    # accidentally fall back to a browser-supplied amount.
    # DEC-072. SMTP for delivering a paid file by email, so it survives the
    # thirty-minute window. Empty host or sender means email delivery refuses
    # rather than reporting a success it did not achieve.
    # DEC-073. Free preparations a kit may make before it must buy something.
    # 0 disables the check, which is the default: the counters are there to
    # say what a real candidate does, and a limit set before that is a guess
    # that costs sales when it is set too low.
    free_preparation_allowance: int = 0

    # Cloudflare Turnstile. Empty means no challenge, and unlike the payment
    # secrets this fails *open* -- an unchallenged preparation costs some CPU,
    # while refusing every candidate over a misconfiguration costs the product.
    turnstile_secret: str = ""

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_address: str = ""
    smtp_use_tls: bool = True
    #: The name an inbox shows beside the sender address (DEC-102).
    smtp_from_name: str = "ExamUploadKit"
    #: Where a candidate's reply goes, and the support address the email
    #: names. Empty sends no Reply-To and names no address.
    smtp_reply_to: str = ""
    #: The public site, linked from the email's header and footer. Empty links
    #: nothing.
    site_url: str = ""

    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""

    #: DEC-089. A stand-in for Razorpay, for walking the whole checkout on a
    #: machine with no payment account. Off by default. It refuses to create or
    #: settle anything beside real Razorpay credentials, and `GET /ready`
    #: reports `payments: simulated`, so it can never pass for a working
    #: payment setup.
    payment_simulator_enabled: bool = False

    #: How many files one document request may carry.  `max_upload_bytes`
    #: bounds each file and nothing bounded the count, so a single request
    #: could hand the service an unlimited number of 5 MB uploads to hold in
    #: memory and write to disk.  A certificate with its annexures is rarely
    #: more than a handful of pages.
    max_document_files: int = 20

    #: Bound paid-kit email delivery as an external side effect. Failed and
    #: successful sends both count so a broken or adversarial recipient cannot
    #: consume an SMTP provider indefinitely during the retention window.
    max_email_delivery_attempts_per_job: int = 3

    #: How many preparations may run at once.  The pipeline is ~10 s of CPU
    #: per photograph, so this is what actually protects the box.  There is no
    #: per-IP limit by design: carrier-grade NAT puts thousands of candidates
    #: behind one address, so a per-IP quota punishes a shared carrier or is
    #: set so high it protects nothing.  Default 2 is sized for a small VPS;
    #: set it to about the core count of the deployment box, measured.
    max_concurrent_preparations: int = 2

    @field_validator("artifact_root")
    @classmethod
    def validate_artifact_root(cls, v: Path) -> Path:
        """Ensure artifact_root is not a filesystem root drive."""
        resolved = v.resolve()
        # A root drive/directory resolves to a path where it equals its own parent
        # or has an empty name (like WindowsPath('C:\\') or PosixPath('/'))
        if resolved == resolved.parent or not resolved.name:
            raise ValueError(
                "artifact_root cannot be a filesystem root drive/directory"
            )
        return resolved

    @field_validator("max_upload_bytes")
    @classmethod
    def validate_max_upload(cls, v: int) -> int:
        """Ensure max upload bytes is strictly positive."""
        if v <= 0:
            raise ValueError("max_upload_bytes must be greater than 0")
        return v

    @field_validator("cleanup_interval_seconds")
    @classmethod
    def validate_cleanup_interval(cls, v: int) -> int:
        """Ensure the sweeper interval is strictly positive."""
        if v <= 0:
            raise ValueError("cleanup_interval_seconds must be greater than 0")
        return v

    @field_validator("max_document_files", "max_email_delivery_attempts_per_job")
    @classmethod
    def validate_max_document_files(cls, v: int) -> int:
        """Ensure resource budgets cannot be disabled with zero."""
        if v < 1:
            raise ValueError("resource limits must be at least 1")
        return v

    @field_validator("max_concurrent_preparations")
    @classmethod
    def validate_concurrency(cls, v: int) -> int:
        """Ensure at least one preparation can run."""
        if v < 1:
            raise ValueError("max_concurrent_preparations must be at least 1")
        return v

    @field_validator("job_ttl_seconds")
    @classmethod
    def validate_job_ttl(cls, v: int) -> int:
        """Ensure job TTL seconds is strictly positive."""
        if v <= 0:
            raise ValueError("job_ttl_seconds must be greater than 0")
        return v

    @model_validator(mode="after")
    def validate_lifetime_ceiling(self) -> "ApiSettings":
        """The ceiling cannot be shorter than the window it bounds.

        A ceiling below the TTL would mean every job was born already past
        its maximum lifetime, and the extension route would refuse a job that
        had never been extended -- a configuration that reads as working and
        is not.
        """
        if self.job_max_lifetime_seconds < self.job_ttl_seconds:
            raise ValueError(
                "job_max_lifetime_seconds must be at least job_ttl_seconds"
            )
        return self


def get_settings() -> ApiSettings:
    """Load settings from environment variables with defaults."""
    from typing import Any

    kwargs: dict[str, Any] = {}
    if "EXAM_PHOTO_ARTIFACT_ROOT" in os.environ:
        kwargs["artifact_root"] = Path(os.environ["EXAM_PHOTO_ARTIFACT_ROOT"])
    if "EXAM_PHOTO_MAX_UPLOAD_BYTES" in os.environ:
        kwargs["max_upload_bytes"] = int(os.environ["EXAM_PHOTO_MAX_UPLOAD_BYTES"])
    if "EXAM_PHOTO_JOB_TTL_SECONDS" in os.environ:
        kwargs["job_ttl_seconds"] = int(os.environ["EXAM_PHOTO_JOB_TTL_SECONDS"])
    if "EXAM_PHOTO_JOB_MAX_LIFETIME_SECONDS" in os.environ:
        kwargs["job_max_lifetime_seconds"] = int(
            os.environ["EXAM_PHOTO_JOB_MAX_LIFETIME_SECONDS"]
        )
    if "EXAM_PHOTO_CATALOGUE_ROOT" in os.environ:
        kwargs["catalogue_root"] = Path(os.environ["EXAM_PHOTO_CATALOGUE_ROOT"])

    # Load model configuration paths and hashes from environment
    if "EXAM_PHOTO_FACE_MODEL_PATH" in os.environ:
        kwargs["face_model_path"] = Path(os.environ["EXAM_PHOTO_FACE_MODEL_PATH"])
    if "EXAM_PHOTO_SEGMENTER_MODEL_PATH" in os.environ:
        kwargs["segmenter_model_path"] = Path(
            os.environ["EXAM_PHOTO_SEGMENTER_MODEL_PATH"]
        )
    if "EXAM_PHOTO_FACE_MODEL_SHA256" in os.environ:
        kwargs["face_expected_sha256"] = os.environ["EXAM_PHOTO_FACE_MODEL_SHA256"]
    if "EXAM_PHOTO_SEGMENTER_MODEL_SHA256" in os.environ:
        kwargs["segmenter_expected_sha256"] = os.environ[
            "EXAM_PHOTO_SEGMENTER_MODEL_SHA256"
        ]

    if "EXAM_PHOTO_MATTING_BACKEND" in os.environ:
        kwargs["matting_backend"] = os.environ["EXAM_PHOTO_MATTING_BACKEND"].lower()

    # Load boolean flags
    if "EXAM_PHOTO_ALLOW_INVALID_OUTPUT_SAVE" in os.environ:
        val = os.environ["EXAM_PHOTO_ALLOW_INVALID_OUTPUT_SAVE"].lower()
        kwargs["allow_invalid_output_save"] = val in ("1", "true", "yes")
    if "EXAM_PHOTO_LOCAL_CORS_ENABLED" in os.environ:
        val = os.environ["EXAM_PHOTO_LOCAL_CORS_ENABLED"].lower()
        kwargs["local_cors_enabled"] = val in ("1", "true", "yes")
    if "EXAM_PHOTO_PURCHASE_GATE_ENABLED" in os.environ:
        val = os.environ["EXAM_PHOTO_PURCHASE_GATE_ENABLED"].lower()
        kwargs["purchase_gate_enabled"] = val in ("1", "true", "yes")
    if "EXAM_PHOTO_PAYMENT_SIMULATOR" in os.environ:
        val = os.environ["EXAM_PHOTO_PAYMENT_SIMULATOR"].lower()
        kwargs["payment_simulator_enabled"] = val in ("1", "true", "yes")
    if "EXAM_PHOTO_WARMUP_ON_BOOT" in os.environ:
        val = os.environ["EXAM_PHOTO_WARMUP_ON_BOOT"].lower()
        kwargs["warmup_on_boot"] = val in ("1", "true", "yes")

    # Deployment hardening (DEC-064)
    if "EXAM_PHOTO_ALLOWED_ORIGINS" in os.environ:
        kwargs["allowed_origins"] = [
            origin.strip()
            for origin in os.environ["EXAM_PHOTO_ALLOWED_ORIGINS"].split(",")
            if origin.strip()
        ]
    if "EXAM_PHOTO_CLEANUP_INTERVAL_SECONDS" in os.environ:
        kwargs["cleanup_interval_seconds"] = int(
            os.environ["EXAM_PHOTO_CLEANUP_INTERVAL_SECONDS"]
        )
    if "EXAM_PHOTO_OPERATOR_TOKEN" in os.environ:
        kwargs["operator_token"] = os.environ["EXAM_PHOTO_OPERATOR_TOKEN"]
    if "EXAM_PHOTO_FREE_PREPARATION_ALLOWANCE" in os.environ:
        kwargs["free_preparation_allowance"] = int(
            os.environ["EXAM_PHOTO_FREE_PREPARATION_ALLOWANCE"]
        )
    if "EXAM_PHOTO_TURNSTILE_SECRET" in os.environ:
        kwargs["turnstile_secret"] = os.environ["EXAM_PHOTO_TURNSTILE_SECRET"]
    for var, field in (
        ("EXAM_PHOTO_SMTP_HOST", "smtp_host"),
        ("EXAM_PHOTO_SMTP_USERNAME", "smtp_username"),
        ("EXAM_PHOTO_SMTP_PASSWORD", "smtp_password"),
        ("EXAM_PHOTO_SMTP_FROM", "smtp_from_address"),
        ("EXAM_PHOTO_SMTP_FROM_NAME", "smtp_from_name"),
        ("EXAM_PHOTO_SMTP_REPLY_TO", "smtp_reply_to"),
        ("EXAM_PHOTO_SITE_URL", "site_url"),
    ):
        if var in os.environ:
            kwargs[field] = os.environ[var]
    if "EXAM_PHOTO_SMTP_PORT" in os.environ:
        kwargs["smtp_port"] = int(os.environ["EXAM_PHOTO_SMTP_PORT"])
    if "EXAM_PHOTO_SMTP_USE_TLS" in os.environ:
        val = os.environ["EXAM_PHOTO_SMTP_USE_TLS"].strip().lower()
        kwargs["smtp_use_tls"] = val in ("1", "true", "yes")
    if "EXAM_PHOTO_RAZORPAY_KEY_ID" in os.environ:
        kwargs["razorpay_key_id"] = os.environ["EXAM_PHOTO_RAZORPAY_KEY_ID"]
    if "EXAM_PHOTO_RAZORPAY_KEY_SECRET" in os.environ:
        kwargs["razorpay_key_secret"] = os.environ["EXAM_PHOTO_RAZORPAY_KEY_SECRET"]
    if "EXAM_PHOTO_RAZORPAY_WEBHOOK_SECRET" in os.environ:
        kwargs["razorpay_webhook_secret"] = os.environ[
            "EXAM_PHOTO_RAZORPAY_WEBHOOK_SECRET"
        ]
    if "EXAM_PHOTO_MAX_DOCUMENT_FILES" in os.environ:
        kwargs["max_document_files"] = int(os.environ["EXAM_PHOTO_MAX_DOCUMENT_FILES"])
    if "EXAM_PHOTO_MAX_EMAIL_DELIVERY_ATTEMPTS_PER_JOB" in os.environ:
        kwargs["max_email_delivery_attempts_per_job"] = int(
            os.environ["EXAM_PHOTO_MAX_EMAIL_DELIVERY_ATTEMPTS_PER_JOB"]
        )
    if "EXAM_PHOTO_MAX_CONCURRENT_PREPARATIONS" in os.environ:
        kwargs["max_concurrent_preparations"] = int(
            os.environ["EXAM_PHOTO_MAX_CONCURRENT_PREPARATIONS"]
        )

    return ApiSettings(**kwargs)
