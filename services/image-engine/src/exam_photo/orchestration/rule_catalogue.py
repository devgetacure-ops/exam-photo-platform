"""Reading the encoded examination catalogue.

The rule records in ``examples/rules/`` are generated from versioned research
and have, until now, been reachable only by a caller that already held a path.
Nothing in the service read the directory at all, so the 39 encoded
examinations and their requirements were invisible to the API and therefore to
the application (DEC-054).

This module is the read side of that catalogue and nothing more. It does not
resolve a rule into a processing plan -- ``rule_resolver`` does that -- and it
does not decide what the platform will prepare, which is the API's gate to
apply (DEC-055).

Two properties are worth stating because they are load-bearing.

**A bad record costs its own examination and no others.** A file that will not
parse, or that fails the model's cross-field rules, is recorded against its
name and skipped. The alternative -- raising on the first bad record -- means
one malformed regeneration takes down the entire picker, which is a much worse
outcome than one examination going missing while the rest of the catalogue
serves. This mirrors ``plan_document``'s treatment of an unreadable upload for
the same reason.

**A duplicate ``exam_id`` is a conflict, not a last-one-wins.** Today all 39
identifiers are unique, but that is a property of the current catalogue rather
than a guarantee: DEC-047 exists partly because one examination can require
several stage-specific records, and the RBI Assistant cycle already needed two.
If a regeneration ever produces two records under one identifier, silently
serving whichever was read last would make the wrong rule reachable at a stable
URL. Both are refused and the collision is reported.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from exam_photo.models.exam_rule import ExamRule, PlatformSupport

#: Written by `scripts/encode_exam_rules.py` beside the rule records. Skipped
#: when scanning for records, and read separately below.
UNAVAILABLE_FILENAME = "unavailable_examinations.json"


@dataclass(frozen=True)
class CatalogueEntry:
    """One encoded examination, and the file it was read from."""

    exam_id: str
    rule: ExamRule
    #: Kept for diagnostics and for the admin console. Never returned to a
    #: candidate-facing caller: a filesystem path is not theirs to know.
    source_path: Path


@dataclass(frozen=True)
class UnavailableExamination:
    """An examination the research covers that the catalogue does not encode.

    Carried so the picker can show it rather than omit it. A candidate
    searching for SSC CGL and finding nothing concludes the platform does not
    cover the examination; an absence discovered at the portal is worse than
    one admitted here (DEC-055).
    """

    exam_name: str
    reason: str
    detail: str
    #: What the candidate loses by the absence: deliverables the platform
    #: could prepare if a rule record did not require a photograph
    #: specification. Ten of the eleven carry at least one.
    non_photograph_deliverables: int = 0


@dataclass(frozen=True)
class Catalogue:
    """Every examination that could be read, and every one that could not."""

    entries: dict[str, CatalogueEntry] = field(default_factory=dict)
    #: File name to the reason it was not served. Surfaced by diagnostics
    #: rather than swallowed, because an examination missing from the picker
    #: with no trace is indistinguishable from one that was never researched.
    unreadable: dict[str, str] = field(default_factory=dict)
    #: Examinations the research covers that no rule record encodes.
    unavailable: list[UnavailableExamination] = field(default_factory=list)

    def get(self, exam_id: str) -> Optional[CatalogueEntry]:
        return self.entries.get(exam_id)

    def listed(self) -> list[CatalogueEntry]:
        """Every entry, ordered by examination name.

        Ordered here rather than by the caller so that the list endpoint, the
        CLI and any test see the same sequence. Name order is the only one a
        candidate scanning a picker can predict; file order is an accident of
        the encoder and identifier order is an accident of slugification.
        """
        return sorted(self.entries.values(), key=lambda e: e.rule.exam.exam_name)


def support_counts(rule: ExamRule) -> dict[PlatformSupport, int]:
    """How many of an examination's requirements sit in each support state.

    Returned as the full five-key mapping with explicit zeros rather than as a
    sparse count, so a caller cannot read a missing key as "none of these" in
    one place and "not computed" in another. DEC-055 forbids collapsing these
    five values into a boolean anywhere downstream; keeping all five present
    here is the same rule applied one layer earlier.
    """
    counts = {support: 0 for support in PlatformSupport}
    for requirement in rule.requirements or []:
        counts[requirement.platform_support] += 1
    return counts


def load_catalogue(root: Path) -> Catalogue:
    """Read every real examination record under ``root``.

    Fictional records are excluded by their own ``fictional_example`` flag
    rather than by a filename convention. Both would work today -- the 39 real
    records are exactly the ``exam_*.json`` files, and the 13 sample and
    benchmark records are exactly the others -- but the flag is the field that
    means it, and a benchmark fixture renamed for any reason must not become an
    examination a candidate can select.
    """
    entries: dict[str, CatalogueEntry] = {}
    unreadable: dict[str, str] = {}
    #: Every identifier seen, including ones already withdrawn for a collision.
    #: Tracked separately from ``entries`` so that a third record claiming a
    #: contested identifier is refused too, rather than being installed into
    #: the gap the first two left behind.
    claimed: dict[str, Path] = {}

    if not root.is_dir():
        return Catalogue(entries=entries, unreadable=unreadable)

    for path in sorted(root.glob("*.json")):
        if path.name == UNAVAILABLE_FILENAME:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            unreadable[path.name] = f"could not be read: {error}"
            continue

        if not isinstance(payload, dict):
            unreadable[path.name] = "is not a JSON object"
            continue

        if payload.get("fictional_example") is not False:
            continue

        try:
            rule = ExamRule.model_validate(payload)
        except ValidationError as error:
            unreadable[path.name] = (
                f"failed rule validation with {error.error_count()} error(s)"
            )
            continue

        exam_id = rule.exam.exam_id
        first_claim = claimed.get(exam_id)
        if first_claim is not None:
            unreadable[path.name] = (
                f"declares exam_id '{exam_id}', which {first_claim.name} also "
                "declares. Neither is served: serving whichever was read last "
                "would put the wrong rule behind a stable identifier."
            )
            unreadable.setdefault(
                first_claim.name,
                f"declares exam_id '{exam_id}', which {path.name} also "
                "declares. Neither is served.",
            )
            entries.pop(exam_id, None)
            continue

        claimed[exam_id] = path
        entries[exam_id] = CatalogueEntry(exam_id=exam_id, rule=rule, source_path=path)

    return Catalogue(
        entries=entries,
        unreadable=unreadable,
        unavailable=_load_unavailable(root / UNAVAILABLE_FILENAME, unreadable),
    )


def _load_unavailable(
    path: Path, unreadable: dict[str, str]
) -> list[UnavailableExamination]:
    """Read the encoder's list of examinations it could not encode.

    Absent is not an error: a catalogue directory assembled by hand, or one
    generated before this file existed, still serves its records. A file that
    is present and broken *is* recorded, because at that point something is
    wrong and silence would hide it.
    """
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        unreadable[path.name] = f"could not be read: {error}"
        return []

    if not isinstance(payload, dict):
        unreadable[path.name] = "is not a JSON object"
        return []

    listed = payload.get("examinations")
    if not isinstance(listed, list):
        unreadable[path.name] = "carries no 'examinations' list"
        return []

    unavailable: list[UnavailableExamination] = []
    for item in listed:
        if not isinstance(item, dict) or not item.get("exam_name"):
            continue
        unavailable.append(
            UnavailableExamination(
                exam_name=str(item["exam_name"]),
                reason=str(item.get("reason") or ""),
                detail=str(item.get("detail") or ""),
                non_photograph_deliverables=int(
                    item.get("non_photograph_deliverables") or 0
                ),
            )
        )
    return sorted(unavailable, key=lambda item: item.exam_name)
