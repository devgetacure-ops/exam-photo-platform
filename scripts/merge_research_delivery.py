"""Merge a research delivery into the versioned research files, additively.

A delivery is two JSON files in the same shape as
``packages/exam-rules/research/exam_photo_specs_2026.json`` and
``exam_deliverables_2026.json``. This script folds one into the other
**without ever losing what the repository already holds**, which a plain
replacement does not manage: the 2026-09-07 completion pass carried 117
records but zero rejection conditions against the catalogue's 204, and half
the deliverable detail, so adopting it wholesale would have deleted both
(DEC-068).

The merge rules, in the order they are applied:

1. **A record the delivery adds is added.** No question.
2. **A field is overwritten only when the delivery's value is better.**
   Better means: the delivery has ``verified`` and the repository does not;
   or both are ``verified`` but only the delivery's is from an official
   source. A verified official value is never replaced by ``not_found``,
   because "we did not find it this time" is not evidence that a previously
   sourced value is wrong.
3. **Rejection conditions are unioned**, never replaced.
4. **Deliverables are unioned by name**, and where both sides carry the same
   deliverable the entry with more parsed detail wins.
5. **An overlay is applied last and unconditionally.** It carries values read
   directly from an authority document, so it outranks a delivery that
   recorded the same field as ``not_found``.

Everything the merge changes is reported. Nothing is changed silently.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

Record = Dict[str, Any]


def _by_name(records: List[Record]) -> Dict[str, Record]:
    return {str(r.get("exam_name")): r for r in records}


def _is_verified(field: Optional[Dict[str, Any]]) -> bool:
    return bool(field) and field.get("status") == "verified"


def _is_official(field: Optional[Dict[str, Any]]) -> bool:
    return bool(field) and bool(field.get("official_source"))


def _field_is_better(new: Optional[Dict[str, Any]], old: Optional[Dict[str, Any]]) -> bool:
    """Whether the delivery's field should replace the repository's."""
    if not _is_verified(new):
        # Rule 2: a `not_found` never displaces something already established.
        return False
    if not _is_verified(old):
        return True
    # Both verified. Only an upgrade in source authority justifies a change.
    return _is_official(new) and not _is_official(old)


#: Source types a delivery has used that the canonical schema does not define.
#: Mapped rather than dropped, because the evidence is real and the name is the
#: only thing wrong with it. CAT's registration guide genuinely sits on the
#: examination vendor's application portal, so that is what it is called here.
SOURCE_TYPE_ALIASES = {"official_vendor_portal": "official_application_portal"}


def _normalise_source_types(record: Record, log: List[str], name: str) -> None:
    for path, field in (record.get("fields") or {}).items():
        alias = SOURCE_TYPE_ALIASES.get(str(field.get("source_type")))
        if alias:
            log.append(
                f"SRCTYPE {name} :: {path} :: {field['source_type']} -> {alias}"
            )
            field["source_type"] = alias


def _key(name: str) -> str:
    """A deliverable's identity for de-duplication.

    Punctuation and spacing are stripped, so "Handwritten declaration" and
    "Hand written declaration" are recognised as one deliverable rather than
    accumulated as two. They arrived spelled both ways from two deliveries.
    """
    return "".join(ch for ch in str(name).lower() if ch.isalnum())


def _is_uploaded_photograph(deliverable: Dict[str, Any]) -> bool:
    """Whether this is a photograph the candidate uploads as a file.

    The rule model permits exactly one, because a rule carries a single
    ``image_requirements`` block to specify it with. Two deliveries naming the
    same photograph differently -- "Recent passport-size photograph" and
    "Candidate photograph" -- would otherwise union into two and the whole
    examination would be rejected at validation.
    """
    from encode_exam_rules import _requirement_type  # single source of truth

    method = str(deliverable.get("submission_method") or "")
    if method not in ("file_upload", "document_scan_upload"):
        return False
    return _requirement_type(str(deliverable.get("name") or ""), method) == "photograph"


def _collapse_uploaded_photographs(
    deliverables: List[Dict[str, Any]], log: List[str], name: str
) -> List[Dict[str, Any]]:
    photos = [d for d in deliverables if _is_uploaded_photograph(d)]
    if len(photos) <= 1:
        return deliverables
    keep = max(photos, key=_parsed_depth)
    dropped = [d for d in photos if d is not keep]
    for d in dropped:
        log.append(
            f"PHOTO-  {name} :: dropped duplicate uploaded photograph "
            f"{d.get('name')!r}, kept {keep.get('name')!r}"
        )
    return [d for d in deliverables if d is keep or not _is_uploaded_photograph(d)]


def _parsed_depth(deliverable: Dict[str, Any]) -> int:
    parsed = deliverable.get("parsed") or {}
    size = parsed.get("file_size_kb") or {}
    formats = parsed.get("formats") or {}
    return (
        bool(size.get("maximum"))
        + bool(size.get("minimum"))
        + bool(formats.get("values"))
        + bool(deliverable.get("specification"))
        + bool(deliverable.get("source_url"))
    )


def merge_specs(
    repo: List[Record], delivery: List[Record], overlay: Dict[str, Any]
) -> Tuple[List[Record], List[str]]:
    log: List[str] = []
    out = _by_name(repo)

    for name, incoming in _by_name(delivery).items():
        _normalise_source_types(incoming, log, name)
        existing = out.get(name)
        if existing is None:
            out[name] = incoming
            log.append(f"ADDED   record {name}")
            continue
        fields = existing.setdefault("fields", {})
        for path, new_field in (incoming.get("fields") or {}).items():
            if _field_is_better(new_field, fields.get(path)):
                before = (fields.get(path) or {}).get("value")
                fields[path] = new_field
                log.append(
                    f"FIELD   {name} :: {path} :: {before!r} -> {new_field.get('value')!r}"
                )

    for name, overrides in (overlay.get("specs") or {}).items():
        target = out.get(name)
        if target is None:
            log.append(f"SKIP    overlay for unknown record {name}")
            continue
        fields = target.setdefault("fields", {})
        for path, field in overrides.items():
            before = (fields.get(path) or {}).get("value")
            fields[path] = field
            log.append(
                f"OVERLAY {name} :: {path} :: {before!r} -> {field.get('value')!r}"
            )

    return list(out.values()), log


def merge_deliverables(
    repo: List[Record], delivery: List[Record], overlay: Dict[str, Any]
) -> Tuple[List[Record], List[str]]:
    log: List[str] = []
    out = _by_name(repo)
    next_number = max((int(r.get("record_number") or 0) for r in repo), default=0)

    for name, incoming in _by_name(delivery).items():
        existing = out.get(name)
        if existing is None:
            next_number += 1
            incoming["record_number"] = next_number
            out[name] = incoming
            log.append(f"ADDED   deliverable record {name}")
            continue

        # Rule 3: conditions are unioned.
        merged_conditions = list(existing.get("rejection_conditions") or [])
        for condition in incoming.get("rejection_conditions") or []:
            if condition not in merged_conditions:
                merged_conditions.append(condition)
                log.append(f"REJECT+ {name} :: {condition[:70]}")
        existing["rejection_conditions"] = merged_conditions

        # Rule 4: deliverables unioned by name, deeper entry wins.
        by_key = {_key(d.get("name", "")): d
                  for d in existing.get("deliverables") or []}
        for deliverable in incoming.get("deliverables") or []:
            key = _key(deliverable.get("name", ""))
            current = by_key.get(key)
            if current is None:
                by_key[key] = deliverable
                log.append(f"DELIV+  {name} :: {deliverable.get('name')}")
            elif _parsed_depth(deliverable) > _parsed_depth(current):
                by_key[key] = deliverable
                log.append(f"DELIV~  {name} :: {deliverable.get('name')} (deeper)")
        existing["deliverables"] = _collapse_uploaded_photographs(
            list(by_key.values()), log, name)

    for name, entries in (overlay.get("deliverables") or {}).items():
        target = out.get(name)
        if target is None:
            log.append(f"SKIP    overlay deliverables for unknown record {name}")
            continue
        by_key = {_key(d.get("name", "")): d
                  for d in target.get("deliverables") or []}
        for deliverable in entries:
            by_key[_key(deliverable.get("name", ""))] = deliverable
            log.append(f"OVERLAY {name} :: deliverable {deliverable.get('name')}")
        target["deliverables"] = _collapse_uploaded_photographs(
            list(by_key.values()), log, name)

    for name, conditions in (overlay.get("rejection_conditions") or {}).items():
        target = out.get(name)
        if target is None:
            continue
        merged = list(target.get("rejection_conditions") or [])
        for condition in conditions:
            if condition not in merged:
                merged.append(condition)
                log.append(f"OVERLAY {name} :: rejection condition")
        target["rejection_conditions"] = merged

    return list(out.values()), log


def _load(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _dump(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research-dir", type=Path,
                        default=Path("packages/exam-rules/research"))
    parser.add_argument("--delivery", type=Path, required=True,
                        help="Directory holding the delivery's two JSON files.")
    parser.add_argument("--overlay", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    specs_path = args.research_dir / "exam_photo_specs_2026.json"
    deliv_path = args.research_dir / "exam_deliverables_2026.json"
    overlay = _load(args.overlay) if args.overlay else {}

    specs, specs_log = merge_specs(
        _load(specs_path),
        _load(args.delivery / "exam_photo_specs_2026.json"),
        overlay,
    )
    deliverables, deliv_log = merge_deliverables(
        _load(deliv_path),
        _load(args.delivery / "exam_deliverables_2026.json"),
        overlay,
    )

    for line in specs_log + deliv_log:
        print(line)
    print(f"\nspecs records      : {len(specs)}")
    print(f"deliverable records: {len(deliverables)}")
    print(f"changes            : {len(specs_log) + len(deliv_log)}")

    if args.dry_run:
        print("\n(dry run -- nothing written)")
        return 0

    _dump(specs_path, specs)
    _dump(deliv_path, deliverables)
    print(f"\nwritten {specs_path}\nwritten {deliv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
