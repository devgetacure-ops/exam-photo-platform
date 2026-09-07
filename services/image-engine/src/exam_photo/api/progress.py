"""Real progress for a preparation that is still running.

DEC-075. Preparation blocks for about ten seconds and returns the finished
job, so the interface had nothing to show but a spinner. A progress ring
driven by a timer would be inventing the number, and the first time the
network was slow it would sit at 90% while nothing happened -- which is the
detail that makes a premium interface feel fake.

**Why a token the caller supplies.** The job id is only known once the
preparation finishes, so it cannot be used to poll a preparation in progress.
The client mints a token, sends it with the upload, and polls it alongside.
That keeps `prepare` synchronous and its contract unchanged; the alternative
-- 202 plus polling (DEC-055) -- is the better long-term shape and a breaking
change, and is still open.

**Why disk and not memory.** A deployment runs several uvicorn workers, and
the poll will not reliably land on the worker doing the work. An in-memory
dictionary would report "unknown" at random, which is worse than no progress
bar. The files are tiny and short-lived.

**What the weights are, and are not.** They are measured shares of a real
run, so the bar moves at roughly the rate the work happens. They are not a
promise: a slow machine takes longer at every stage, and the bar is honest
about *what* is happening even when it is wrong about when it will end.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

#: Minted by the browser and used as a filename, so its shape is pinned here
#: and checked before it is ever joined to a path.
PROGRESS_TOKEN_REGEX = re.compile(r"^prg_[A-Za-z0-9_-]{1,64}$")

#: Roughly what share of a photograph's wall clock each stage takes, measured
#: on the ten `perfect` photographs at 413x531 (DEC-054's set). The two
#: BiRefNet inferences dominate: segmentation and the crop-region re-matte
#: inside refinement are about eight of the ten seconds.
#:
#: A stage missing from this map contributes nothing, which is correct for the
#: cheap ones -- the bar should not lurch forward on a step that takes 3 ms.
STAGE_WEIGHTS: Dict[str, float] = {
    "rule_validation": 0.01,
    "input_normalization": 0.02,
    "suitability_evaluation": 0.03,
    "face_detection": 0.04,
    "head_estimation": 0.02,
    "subject_segmentation": 0.34,
    "mask_refinement": 0.30,
    "crop_selection": 0.02,
    "crop_planning": 0.02,
    "foreground_decontamination": 0.04,
    "background_composition": 0.04,
    "portrait_composition": 0.02,
    "composition_quality_validation": 0.01,
    "matte_quality_validation": 0.01,
    "output_preparation": 0.03,
    "output_compression": 0.03,
    "final_decode_validation": 0.01,
    "final_rule_validation": 0.01,
    "filename_generation": 0.00,
}

#: What a candidate is told each stage is. Deliberately not the internal name:
#: "foreground decontamination" is precise and means nothing to anybody.
STAGE_LABELS: Dict[str, str] = {
    "rule_validation": "Reading the examination's rules",
    "input_normalization": "Opening your photograph",
    "suitability_evaluation": "Checking it can be used",
    "face_detection": "Finding your face",
    "head_estimation": "Measuring head and shoulders",
    "subject_segmentation": "Separating you from the background",
    "mask_refinement": "Refining the edges",
    "crop_selection": "Choosing the frame",
    "crop_planning": "Positioning you in it",
    "foreground_decontamination": "Cleaning the edges",
    "background_composition": "Laying the required background",
    "portrait_composition": "Composing the portrait",
    "composition_quality_validation": "Checking the composition",
    "matte_quality_validation": "Checking the edges",
    "output_preparation": "Resizing to the exact specification",
    "output_compression": "Compressing under the size limit",
    "final_decode_validation": "Re-opening it to be certain",
    "final_rule_validation": "Checking every rule again",
    "filename_generation": "Naming it as the portal expects",
}

#: Progress files older than this are swept. Generous against a preparation
#: that overran; short enough that the directory does not accumulate.
STALE_AFTER_SECONDS = 900


class ProgressState(BaseModel):
    """What a preparation is doing right now."""

    token: str
    #: 0.0-1.0. Monotonic: it never goes backwards, because a bar that
    #: retreats reads as a fault even when the work is fine.
    fraction: float = 0.0
    stage: Optional[str] = None
    label: Optional[str] = None
    completed_stages: List[str] = Field(default_factory=list)
    started_at: str
    updated_at: str
    finished: bool = False
    failed: bool = False


class ProgressRegistry:
    """Per-preparation progress, on disk, readable by any worker."""

    def __init__(self, artifact_root: Path):
        self.root = artifact_root / "_progress"

    def _path(self, token: str) -> Path:
        return self.root / f"{token}.json"

    def start(self, token: str) -> Optional[ProgressState]:
        if not PROGRESS_TOKEN_REGEX.match(token):
            return None
        now = datetime.now(timezone.utc).isoformat()
        state = ProgressState(token=token, started_at=now, updated_at=now)
        self._write(state)
        return state

    def advance(self, token: str, stage: str) -> None:
        """Record that `stage` has completed.

        Failure to write is swallowed on purpose. Progress is a courtesy to
        the interface; a full disk or a racing sweep must never be the reason
        a candidate's photograph does not get made.
        """
        if not PROGRESS_TOKEN_REGEX.match(token):
            return
        state = self.get(token)
        if state is None or state.finished:
            return
        if stage in state.completed_stages:
            return
        state.completed_stages.append(stage)
        earned = sum(STAGE_WEIGHTS.get(name, 0.0) for name in state.completed_stages)
        # Never reaches 1.0 here: only `finish` does that, so the bar cannot
        # sit full while the candidate is still waiting.
        state.fraction = max(state.fraction, min(0.99, round(earned, 4)))
        state.stage = stage
        state.label = STAGE_LABELS.get(stage)
        state.updated_at = datetime.now(timezone.utc).isoformat()
        self._write(state)

    def finish(self, token: str, failed: bool = False) -> None:
        if not PROGRESS_TOKEN_REGEX.match(token):
            return
        state = self.get(token)
        if state is None:
            return
        state.fraction = 1.0
        state.finished = True
        state.failed = failed
        state.label = "Finished" if not failed else "Could not finish"
        state.updated_at = datetime.now(timezone.utc).isoformat()
        self._write(state)

    def get(self, token: str) -> Optional[ProgressState]:
        if not PROGRESS_TOKEN_REGEX.match(token):
            return None
        path = self._path(token)
        if not path.is_file():
            return None
        try:
            return ProgressState.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _write(self, state: ProgressState) -> None:
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            self._path(state.token).write_text(
                state.model_dump_json(), encoding="utf-8"
            )
        except OSError:
            pass

    def sweep(self) -> int:
        """Delete progress files older than `STALE_AFTER_SECONDS`.

        Runs on the existing artifact sweeper's timer (DEC-064), so this
        directory -- unlike `_orders/` and `_usage/` -- does not accumulate.
        Progress is genuinely ephemeral and needs no retention decision.
        """
        if not self.root.is_dir():
            return 0
        cutoff = time.time() - STALE_AFTER_SECONDS
        removed = 0
        for path in self.root.glob("prg_*.json"):
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink()
                    removed += 1
            except OSError:
                continue
        return removed


def json_safe(state: ProgressState) -> Dict[str, object]:
    payload: Dict[str, object] = json.loads(state.model_dump_json())
    return payload
