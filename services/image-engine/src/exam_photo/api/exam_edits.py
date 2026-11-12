"""The owner's edits to examination records, made in the console (DEC-136).

The catalogue's records are files in the repository, and a change used to mean
a commit and a redeploy. An edit made in the console is saved here instead, on
the engine's data volume, as the whole edited record, and laid over the
catalogue at start and the moment it is saved. Processing uses it at once; the
site's pages pick it up within minutes (they refresh from the engine).

An edit is refused unless it passes both the canonical JSON Schema and the
engine's own model, and it may not change the examination's id: the id is the
page's address and every kit, order and deadline is keyed by it.

Reverting deletes the edit and the repository's record is served again. Each
save keeps the previous edit beside it (``.previous.json``), so one mistake can
be undone by hand.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from exam_photo.models.exam_rule import ExamRule
from exam_photo.orchestration.rule_catalogue import Catalogue, CatalogueEntry
from exam_photo.rule_validation import validate_exam_rule

_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,159}$")


@dataclass(frozen=True)
class Edit:
    exam_id: str
    record: Dict[str, Any]
    edited_at: str
    edited_by: str
    path: Path


class EditRefusedError(Exception):
    """The edited record cannot be served; ``problems`` says why, field by field."""

    def __init__(self, problems: List[Dict[str, str]]):
        super().__init__("; ".join(p["message"] for p in problems[:3]))
        self.problems = problems


class ExamEdits:
    def __init__(self, artifact_root: Path):
        self.root = artifact_root / "_exams"

    def _path(self, exam_id: str) -> Path:
        if not _ID.match(exam_id):
            raise ValueError("Invalid exam id")
        return self.root / f"{exam_id}.json"

    def all(self) -> Dict[str, Edit]:
        edits: Dict[str, Edit] = {}
        if not self.root.is_dir():
            return edits
        for path in sorted(self.root.glob("*.json")):
            if path.name.endswith(".previous.json"):
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                record = payload["record"]
                exam_id = str(record["exam"]["exam_id"])
            except (OSError, ValueError, KeyError, TypeError):
                continue
            edits[exam_id] = Edit(
                exam_id=exam_id,
                record=record,
                edited_at=str(payload.get("edited_at") or ""),
                edited_by=str(payload.get("edited_by") or ""),
                path=path,
            )
        return edits

    def get(self, exam_id: str) -> Optional[Edit]:
        return self.all().get(exam_id)

    @staticmethod
    def check(exam_id: str, record: Dict[str, Any]) -> ExamRule:
        """The record as the engine will serve it, or ``EditRefusedError``."""
        problems: List[Dict[str, str]] = []
        exam = record.get("exam") if isinstance(record, dict) else None
        if not isinstance(exam, dict) or exam.get("exam_id") != exam_id:
            problems.append(
                {
                    "field": "exam.exam_id",
                    "message": "The examination's id cannot be changed here.",
                }
            )
        if isinstance(record, dict) and record.get("fictional_example") is not False:
            problems.append(
                {"field": "fictional_example", "message": "Must stay false."}
            )
        if problems:
            raise EditRefusedError(problems)
        for error in validate_exam_rule(record):
            if str(getattr(error, "severity", "")).lower().endswith("error"):
                problems.append(
                    {"field": error.field_path or "", "message": error.message}
                )
        try:
            rule = ExamRule.model_validate(record)
        except ValidationError as error:
            for item in error.errors()[:20]:
                problems.append(
                    {
                        "field": ".".join(str(p) for p in item["loc"]),
                        "message": item["msg"],
                    }
                )
            raise EditRefusedError(problems) from None
        if problems:
            raise EditRefusedError(problems)
        return rule

    def save(self, exam_id: str, record: Dict[str, Any], actor: str) -> Edit:
        self.check(exam_id, record)
        path = self._path(exam_id)
        self.root.mkdir(parents=True, exist_ok=True)
        if path.is_file():
            path.replace(path.with_suffix(".previous.json"))
        edited_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        payload = {"record": record, "edited_at": edited_at, "edited_by": actor}
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8"
        )
        temporary.replace(path)
        return Edit(exam_id, record, edited_at, actor, path)

    def remove(self, exam_id: str) -> bool:
        path = self._path(exam_id)
        if not path.is_file():
            return False
        path.replace(path.with_suffix(".previous.json"))
        return True


def overlay(base: Catalogue, edits: Dict[str, Edit]) -> Catalogue:
    """The catalogue with every valid edit laid over its record.

    An edit that no longer validates (a schema change since it was saved) is
    skipped and reported in ``unreadable`` rather than served or crashing the
    engine; the repository's record is served for that examination.
    """
    entries = dict(base.entries)
    unreadable = dict(base.unreadable)
    for exam_id, edit in edits.items():
        if exam_id not in entries:
            continue
        try:
            rule = ExamEdits.check(exam_id, edit.record)
        except EditRefusedError as refused:
            unreadable[edit.path.name] = f"edit not applied: {refused}"
            continue
        entries[exam_id] = CatalogueEntry(
            exam_id=exam_id, rule=rule, source_path=edit.path
        )
    return replace(base, entries=entries, unreadable=unreadable)
