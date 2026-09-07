"""Protecting the pipeline's capacity, and measuring what it is used for.

DEC-073. Preparation is the expensive thing this service does -- roughly ten
seconds of CPU and 2.4 GB resident per photograph -- and it is free until the
candidate decides to buy. Somebody running hundreds of images through it
without ever paying costs very little money (the compute is a VPS already
paid for) and can cost a great deal of *availability*, which on a deadline day
is the same as costing sales.

Three things live here, and they are deliberately in one module because they
answer one question:

**Turnstile** keeps automated abuse out, which is the only kind with the volume
to matter. It is a Cloudflare challenge verified server-side.

**A per-kit allowance** adds friction to a human idly re-uploading. It is
trivially bypassed by clearing browser storage and that is fine -- it is a
speed bump for casual use, never a security control, and pretending otherwise
would be the mistake.

**Counters**, which the allowance needs anyway and which answer the question
that should decide the allowance: how many preparations does a real candidate
make, and how many kits convert? Setting a limit without that is guessing, and
guessing low costs real sales.

None of it is per-IP. Carrier-grade NAT puts thousands of Indian mobile
candidates behind one address (DEC-064), so a per-IP quota punishes a shared
address while barely inconveniencing anyone determined.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel

from exam_photo.api.jobs import KIT_ID_REGEX

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


class ChallengeFailedError(Exception):
    """The Turnstile token was missing, malformed, or rejected upstream."""


class AllowanceExceededError(Exception):
    """This kit has used its free preparations without buying anything."""

    def __init__(self, used: int, allowance: int) -> None:
        super().__init__(
            f"{used} preparations used against an allowance of {allowance}"
        )
        self.used = used
        self.allowance = allowance


class KitUsage(BaseModel):
    """What one kit has asked of the service.

    Kept outside the job directories, like orders (DEC-071), because it has to
    survive retention: the jobs are erased after thirty minutes and a counter
    that went with them would reset the allowance every half hour, which is
    the same as having no allowance.
    """

    kit_id: str
    preparations: int = 0
    #: Preparations since the last purchase. Buying resets it, so a paying
    #: candidate is never stopped -- the allowance exists to bound free use,
    #: not to ration a customer.
    preparations_since_purchase: int = 0
    purchases: int = 0
    first_seen: str
    last_seen: str


class UsageRegistry:
    """Per-kit counters, on disk, surviving the artifacts they describe."""

    def __init__(self, artifact_root: Path):
        self.root = artifact_root / "_usage"

    def _path(self, kit_id: str) -> Path:
        return self.root / f"{kit_id}.json"

    def get(self, kit_id: str) -> Optional[KitUsage]:
        if not KIT_ID_REGEX.match(kit_id):
            return None
        path = self._path(kit_id)
        if not path.is_file():
            return None
        try:
            return KitUsage.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _save(self, usage: KitUsage) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self._path(usage.kit_id).write_text(
            usage.model_dump_json(indent=2), encoding="utf-8"
        )

    def record_preparation(self, kit_id: str) -> KitUsage:
        now = datetime.now(timezone.utc).isoformat()
        usage = self.get(kit_id) or KitUsage(
            kit_id=kit_id, first_seen=now, last_seen=now
        )
        usage.preparations += 1
        usage.preparations_since_purchase += 1
        usage.last_seen = now
        self._save(usage)
        return usage

    def record_purchase(self, kit_id: str) -> None:
        """A purchase clears the allowance, so a customer keeps working."""
        usage = self.get(kit_id)
        if usage is None:
            return
        usage.purchases += 1
        usage.preparations_since_purchase = 0
        usage.last_seen = datetime.now(timezone.utc).isoformat()
        self._save(usage)

    def check_allowance(self, kit_id: str, allowance: int) -> None:
        """Raise if this kit has spent its free preparations.

        `allowance <= 0` disables the check, which is the default: DEC-073
        turns it on only once the counters say what a normal candidate does.
        """
        if allowance <= 0:
            return
        usage = self.get(kit_id)
        if usage is None:
            return
        if usage.preparations_since_purchase >= allowance:
            raise AllowanceExceededError(usage.preparations_since_purchase, allowance)

    def summary(self) -> Dict[str, object]:
        """Aggregate counters, for setting the allowance on evidence.

        Reports distribution rather than only a mean: the mean of a population
        containing one script and a thousand candidates describes neither.
        """
        kits: List[KitUsage] = []
        if self.root.is_dir():
            for path in self.root.glob("kit_*.json"):
                try:
                    kits.append(
                        KitUsage.model_validate_json(path.read_text(encoding="utf-8"))
                    )
                except Exception:
                    continue

        if not kits:
            return {
                "kits": 0,
                "preparations": 0,
                "kits_that_purchased": 0,
                "conversion_rate": None,
                "preparations_per_kit": {},
                "heaviest_kits": [],
            }

        counts = sorted(kit.preparations for kit in kits)
        purchased = [kit for kit in kits if kit.purchases > 0]

        def percentile(fraction: float) -> int:
            index = min(int(len(counts) * fraction), len(counts) - 1)
            return counts[index]

        return {
            "kits": len(kits),
            "preparations": sum(counts),
            "kits_that_purchased": len(purchased),
            "conversion_rate": round(len(purchased) / len(kits), 4),
            "preparations_per_kit": {
                "median": percentile(0.5),
                "p90": percentile(0.9),
                "p99": percentile(0.99),
                "max": counts[-1],
            },
            "heaviest_kits": [
                {
                    "kit_id": kit.kit_id,
                    "preparations": kit.preparations,
                    "purchases": kit.purchases,
                }
                for kit in sorted(kits, key=lambda k: -k.preparations)[:10]
            ],
        }


def verify_turnstile(
    token: str, secret: str, remote_ip: Optional[str] = None, timeout: float = 8.0
) -> None:
    """Verify a Cloudflare Turnstile token, or raise.

    An empty secret means the host has not configured a challenge, and the
    check is skipped -- unlike the payment secrets, which fail shut. The
    difference is what each protects: an unverified webhook releases files that
    were not paid for, while an unchallenged preparation costs some CPU. Making
    this fail shut would take the whole product down on a misconfiguration, for
    a threat that is measured in rupees.
    """
    if not secret:
        return
    if not token:
        raise ChallengeFailedError("no challenge token was supplied")

    import httpx

    payload = {"secret": secret, "response": token}
    if remote_ip:
        payload["remoteip"] = remote_ip

    try:
        response = httpx.post(TURNSTILE_VERIFY_URL, data=payload, timeout=timeout)
        body = response.json()
    except Exception as err:
        # Cloudflare unreachable. Allowing the request through is the right
        # trade: the alternative is refusing every candidate because a third
        # party is down, to stop something that costs a fraction of a rupee.
        print(f"turnstile verification unavailable, allowing request: {err}")
        return

    if not body.get("success"):
        raise ChallengeFailedError(f"challenge rejected: {body.get('error-codes')}")
