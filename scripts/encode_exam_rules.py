"""Encode researched examination photograph specifications into rule records.

Input is the machine-readable sidecar from the 48-examination evidence research:
one record per exam-stage, each field carrying its own status, value, verbatim
source wording, citation and confidence.

The conversion is deliberately mechanical and total. Every value written to a
rule record traces to a field in the sidecar or to a derivation stated here, and
anything that cannot be encoded is *rejected and reported* rather than patched
by hand. That is what makes the step repeatable when the research is refreshed:
re-running this script must reproduce the catalogue exactly, so the rule files
are an output of the evidence rather than a parallel copy of it that drifts.

Nothing is invented. A field the research recorded as ``not_found`` is omitted
from the rule, never defaulted -- an absent rule and a permissive rule are
different statements, and only the first one is true (AGENTS.md, "no silent
assumptions").

Usage::

    python scripts/encode_exam_rules.py \
        --specs exam_photo_specs_2026.json \
        --out examples/rules \
        --report docs/EXAM_RULE_GAP_REGISTER.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_SRC = REPO_ROOT / "services" / "image-engine" / "src"
if str(ENGINE_SRC) not in sys.path:
    sys.path.insert(0, str(ENGINE_SRC))

from exam_photo.rule_validation import validate_exam_rule  # noqa: E402

# --- Decisions, each recorded with the reason it was taken -------------------

# Published file sizes are ambiguous: no body in the researched set defines
# whether "50 KB" means 50,000 or 51,200 bytes, and the sidecar carries both
# interpretations with ``unit_ambiguous: true`` on every record. The decimal
# reading is chosen because it is the *smaller* of the two, so a file that
# satisfies it satisfies the binary reading as well. The cost is ~2% of the
# available headroom against a product requirement to land just under the
# ceiling; the alternative risks landing just over a portal's actual limit,
# which rejects the candidate outright.
_BYTES_PER_KB = 1000
_BYTES_PER_MB = 1000 * 1000

# Every examination gets the tight composition. See the reasoning on
# ``EXAM_COMPOSITION_DEFAULTS`` in rule_resolver.py: no researched body
# publishes a coverage maximum a tight crop would breach, all of them publish
# minima that it clears, and where an exam's own dimensions make it unreachable
# the relaxation ladder returns the tightest crop the geometry allows.
_CROP_PROFILE = "tight_exam_portrait"

# Colour names as published, mapped to what the engine can composite.
#
# A mandate and a preference are encoded differently on purpose. "White" is a
# requirement, so it becomes ``exact_colour`` and the engine must hit it.
# "Preferably white" and "white or light colour" are permissions, so they become
# ``plain_light`` with white as the fallback -- the same delivered photograph,
# but a rule record that does not claim the body demanded something it merely
# preferred.
_COLOUR_MAP: dict[str, tuple[str, Optional[str], Optional[str]]] = {
    "white": ("exact_colour", "#FFFFFF", None),
    "preferably white": ("plain_light", None, "#FFFFFF"),
    "white or light colour": ("plain_light", None, "#FFFFFF"),
    "light or white": ("plain_light", None, "#FFFFFF"),
    # MPSC is the one body in the set that prefers a non-white background
    # (blue, green or red). It is a preference rather than a requirement, so a
    # white background remains acceptable and is what the engine produces; the
    # published wording is preserved in ``instructions`` so the divergence is
    # visible rather than silently normalised. Recorded in the gap register.
    "preferably blue, green or red": ("plain_background", None, "#FFFFFF"),
}

# Requirements the engine cannot satisfy today. A rule carrying one of these is
# still encoded -- the photograph it produces is correct in every other respect
# -- but it is marked as partially supported so no caller can read a complete
# success into it (AGENTS.md, "no fictional successes").
_IMPRINT_UNSUPPORTED = (
    "The body requires the candidate's name and/or the photograph date printed "
    "on the image. The engine has no text-rendering capability, so the "
    "photograph is produced correctly sized and composed but without the "
    "imprint, which the candidate must add before uploading."
)


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)[:80]


class Field:
    """One researched field: its value, status and citation."""

    def __init__(self, raw: Any) -> None:
        self.raw: dict[str, Any] = raw if isinstance(raw, dict) else {}

    @property
    def status(self) -> str:
        return str(self.raw.get("status", "not_found"))

    @property
    def present(self) -> bool:
        return self.status == "verified" and self.raw.get("value") is not None

    @property
    def value(self) -> Any:
        return self.raw.get("value") if self.present else None

    @property
    def official(self) -> bool:
        return self.raw.get("official_source") is True

    @property
    def confidence(self) -> int:
        try:
            return max(1, min(5, int(self.raw.get("confidence") or 1)))
        except (TypeError, ValueError):
            return 1


class Record:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data
        self.fields = {k: Field(v) for k, v in (data.get("fields") or {}).items()}

    def f(self, path: str) -> Field:
        return self.fields.get(path, Field(None))

    def v(self, path: str) -> Any:
        return self.f(path).value

    @property
    def name(self) -> str:
        return str(self.data.get("exam_name", "unknown"))

    @property
    def live_capture_only(self) -> bool:
        """No upload specification of any kind, and live capture is required.

        SSC's portal photographs the candidate through the browser; there is no
        file to prepare, so the platform has nothing to deliver. Distinguished
        from bodies that require live capture *in addition to* an upload (UPSC,
        NTA, IBPS), which do have an upload specification and are served.
        """
        return (
            self.v("appearance.live_capture_required") is True
            and not self.f("file_size.published_maximum").present
            and not self.f("formats.allowed_formats").present
        )

    @property
    def has_dimensions(self) -> bool:
        return any(
            self.f(p).present
            for p in (
                "dimensions.width_px",
                "dimensions.minimum_width_px",
                "dimensions.preferred_width_px",
            )
        )

    def tier(self) -> str:
        if self.live_capture_only:
            return "live_capture_only"
        if not (
            self.f("file_size.published_maximum").present
            and self.f("formats.allowed_formats").present
        ):
            return "incomplete"
        dim_official = any(
            self.f(p).official
            for p in (
                "dimensions.width_px",
                "dimensions.minimum_width_px",
                "dimensions.preferred_width_px",
            )
        )
        size_official = self.f("file_size.published_maximum").official
        if self.has_dimensions and dim_official and size_official:
            return "full"
        if not self.has_dimensions and size_official:
            return "size_only"
        return "secondary"


def _bytes_from(value: Any, unit: Any) -> Optional[int]:
    if value is None:
        return None
    unit_text = str(unit or "KB").strip().lower()
    factor = _BYTES_PER_MB if unit_text.startswith("mb") else _BYTES_PER_KB
    try:
        return int(round(float(value) * factor))
    except (TypeError, ValueError):
        return None


def _orient_portrait(
    width: Optional[int], height: Optional[int]
) -> tuple[Optional[int], Optional[int], bool]:
    """Return the pair oriented as a portrait, and whether it was transposed.

    An examination photograph is a head-and-shoulders portrait; none is
    landscape. Two records in the research nonetheless encode one, and both say
    so in a sentence that contradicts itself: RRB publishes "35mmX45mm or
    320 x 240 pixels", where 35x45 mm is portrait at 0.778 and 320x240 is
    landscape at 1.333. The magnitudes agree -- 240/320 is 0.750, a close match
    to 0.778 -- so the figure is transposed at source rather than wrong.

    Transposing is a judgement, not a transcription, so it is applied by a rule
    that states its own scope rather than by editing two records: pixels that
    come out landscape are turned upright. Nothing else in the set is affected
    -- the three square records (250x250, 1200x1200, 240x240) are untouched
    because square is not landscape, and every other record is already
    portrait.

    Orientation is deliberately the only signal used. Comparing against the
    published physical size would misfire: IBPS writes "4.5 cm x 3.5 cm" --
    height first -- alongside a correct portrait 200x230, so an aspect
    comparison would 'correct' a figure that is already right.
    """
    if width and height and width > height:
        return height, width, True
    return width, height, False


def _aspect_ratio(width: Optional[int], height: Optional[int]) -> Optional[str]:
    """Derive a reduced W:H string. Never guessed -- only computed from pixels."""
    if not width or not height:
        return None
    from math import gcd

    g = gcd(int(width), int(height))
    return f"{int(width) // g}:{int(height) // g}"


def _source_evidence(record: Record) -> list[dict[str, Any]]:
    """One entry per distinct cited document, carrying its verbatim wording.

    Deduplicated by URL plus section: the research cites per field, and a single
    bulletin page routinely supplies a dozen fields, so a naive one-per-field
    transcription would produce an unreadable record that says the same thing
    twelve times.
    """
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    for field in record.fields.values():
        if field.status == "not_found":
            continue
        raw = field.raw
        url = str(raw.get("source_url") or "")
        section = str(raw.get("section_name") or "")
        wording = str(raw.get("captured_wording") or "").strip()
        if not wording:
            continue
        key = (url, section)
        entry = seen.get(key)
        if entry is None:
            source_type = str(raw.get("source_type") or "secondary_reference")
            entry = {
                "source_type": source_type,
                "official_source": bool(raw.get("official_source")),
                "captured_wording": wording,
            }
            if url.startswith(("http://", "https://", "file://")):
                entry["source_url"] = url
            if raw.get("document_title"):
                entry["document_title"] = str(raw["document_title"])
            if raw.get("document_identifier"):
                entry["document_identifier"] = str(raw["document_identifier"])
            if isinstance(raw.get("page_number"), int) and raw["page_number"] >= 1:
                entry["page_number"] = raw["page_number"]
            if section:
                entry["section_name"] = section
            seen[key] = entry
        elif wording not in entry["captured_wording"]:
            merged = f"{entry['captured_wording']}; {wording}"
            entry["captured_wording"] = merged[:1800]
    return list(seen.values())


def _dimensions(record: Record) -> dict[str, Any]:
    # The researched ``dimensions.mode`` is deliberately not trusted as the
    # mode. It records what the body's wording implied, and the wording is
    # routinely looser than the numbers: twelve bank records say "unspecified"
    # while supplying preferred pixels. The mode is therefore derived from which
    # numbers are actually present, so it can never disagree with them.
    block: dict[str, Any] = {}
    exact_w = record.v("dimensions.width_px")
    exact_h = record.v("dimensions.height_px")
    min_w = record.v("dimensions.minimum_width_px")
    max_w = record.v("dimensions.maximum_width_px")
    min_h = record.v("dimensions.minimum_height_px")
    max_h = record.v("dimensions.maximum_height_px")
    pref_w = record.v("dimensions.preferred_width_px")
    pref_h = record.v("dimensions.preferred_height_px")

    transposed = False
    if exact_w and exact_h:
        exact_w, exact_h, transposed = _orient_portrait(int(exact_w), int(exact_h))
        block["mode"] = "exact"
        block["width_px"] = int(exact_w)
        block["height_px"] = int(exact_h)
        ratio = _aspect_ratio(int(exact_w), int(exact_h))
        if ratio:
            block["aspect_ratio"] = ratio
        if transposed:
            block["fallback_reason"] = (
                "The published pixel figure is landscape, which contradicts the "
                "portrait physical size given in the same sentence. Recorded "
                "upright; see provenance."
            )
    elif min_w and max_w and min_h and max_h:
        block["mode"] = "range"
        block["minimum_width_px"] = int(min_w)
        block["maximum_width_px"] = int(max_w)
        block["minimum_height_px"] = int(min_h)
        block["maximum_height_px"] = int(max_h)
        if pref_w and min_w <= pref_w <= max_w:
            block["preferred_width_px"] = int(pref_w)
        if pref_h and min_h <= pref_h <= max_h:
            block["preferred_height_px"] = int(pref_h)
    else:
        block["mode"] = "unspecified"
        if pref_w and pref_h:
            pref_w, pref_h, transposed = _orient_portrait(int(pref_w), int(pref_h))
            block["preferred_width_px"] = int(pref_w)
            block["preferred_height_px"] = int(pref_h)
            block["fallback_reason"] = (
                "The body publishes a preferred pixel size without mandating it, "
                "so the size is honoured while the mode stays unspecified."
            )
        else:
            block["fallback_reason"] = (
                "No pixel dimensions are published by the conducting body. The "
                "output size is chosen per photograph from the crop geometry "
                "rather than from a fixed default."
            )
    dpi = record.v("dpi")
    if dpi:
        block["dpi"] = int(dpi)
    permitted = record.v("permitted_pixel_range")
    if permitted:
        block["permitted_pixel_range"] = str(permitted)
    block["_transposed"] = transposed
    return block


def _file_size(record: Record) -> Optional[dict[str, Any]]:
    published_max = record.v("file_size.published_maximum")
    unit = record.v("file_size.size_unit_as_published")
    maximum = _bytes_from(published_max, unit)
    if maximum is None or maximum <= 0:
        return None
    block: dict[str, Any] = {"maximum_bytes": maximum}
    minimum = _bytes_from(record.v("file_size.published_minimum"), unit)
    if minimum is not None and 0 < minimum < maximum:
        block["minimum_bytes"] = minimum
    if unit:
        block["size_unit_as_published"] = str(unit)
    if published_max is not None:
        block["published_maximum"] = float(published_max)
    published_min = record.v("file_size.published_minimum")
    if published_min is not None:
        block["published_minimum"] = float(published_min)
    return block


# Formats the engine can emit. A body may accept more -- ICSI's portal takes
# GIF, BMP and PDF -- but ``allowed_formats`` on a rule record states what the
# engine may produce for that exam, not the full set the portal will swallow.
# The published list is preserved verbatim in the provenance note so the
# narrowing is visible rather than looking like a transcription error.
_ENGINE_FORMATS = frozenset({"jpg", "jpeg", "png", "webp"})


def _formats(record: Record) -> Optional[tuple[dict[str, Any], list[str]]]:
    allowed_raw = record.v("formats.allowed_formats")
    if not allowed_raw:
        return None
    published = [str(f).lower().strip() for f in allowed_raw]
    allowed = [f for f in published if f in _ENGINE_FORMATS]
    dropped = [f for f in published if f not in _ENGINE_FORMATS]
    if not allowed:
        return None
    # ``preferred_format`` is required by the schema but is rarely published,
    # because JPG and JPEG name one format and a body listing both has stated a
    # single preference. Choosing jpeg where it is permitted is a derivation
    # rather than a finding, and is recorded as ``inferred`` provenance below.
    published = record.v("formats.preferred_format")
    if published and str(published).lower().strip() in allowed:
        preferred = str(published).lower().strip()
    elif "jpeg" in allowed:
        preferred = "jpeg"
    elif "jpg" in allowed:
        preferred = "jpg"
    else:
        return None
    block: dict[str, Any] = {
        "allowed_formats": allowed,
        "preferred_format": preferred,
        "preserve_transparency": False,
        "strip_metadata": True,
        "colour_space": "sRGB",
    }
    return block, dropped


def _background(record: Record) -> dict[str, Any]:
    published = record.v("background.required_colour")
    mode = record.v("background.mode")
    block: dict[str, Any] = {"mode": "unspecified"}
    if published:
        key = str(published).strip().lower()
        mapped = _COLOUR_MAP.get(key)
        if mapped:
            resolved_mode, required, fallback = mapped
            block["mode"] = resolved_mode
            if required:
                block["required_colour"] = required
                block["tolerance"] = 3.0
            if fallback:
                block["fallback_colour"] = fallback
        else:
            # An unmapped colour name is not guessed at. The engine composites
            # white and the published wording is preserved for a human.
            block["mode"] = "plain_background"
            block["fallback_colour"] = "#FFFFFF"
    elif mode in ("plain_light", "plain_background", "exact_colour"):
        block["mode"] = "plain_light" if mode == "exact_colour" else str(mode)
        block["fallback_colour"] = "#FFFFFF"
    shadows = record.v("background.shadows_allowed")
    if shadows is not None:
        block["shadows_allowed"] = bool(shadows)
    gradient = record.v("background.gradient_allowed")
    if gradient is not None:
        block["gradient_allowed"] = bool(gradient)
    instructions = record.v("background.instructions") or (
        str(published)
        if published and str(published).strip().lower() not in _COLOUR_MAP
        else None
    )
    if instructions:
        block["instructions"] = str(instructions)
    return block


def _composition(record: Record) -> dict[str, Any]:
    block: dict[str, Any] = {
        "crop_profile": _CROP_PROFILE,
        # Subject protection is not an exam-by-exam preference: the crop may
        # never cut hair or the chin/beard boundary whatever the body says, so
        # these are set on every record rather than read from the research.
        "complete_hair_required": True,
        "complete_chin_required": True,
    }
    ears = record.v("composition.ears_visible")
    block["ears_policy"] = "required_visible" if ears is True else "unspecified"
    for src, dest in (
        ("composition.face_coverage_target", "face_coverage_target"),
        ("composition.face_coverage_minimum", "face_coverage_minimum"),
        ("composition.face_coverage_maximum", "face_coverage_maximum"),
    ):
        value = record.v(src)
        if value is not None:
            block[dest] = float(value)
    for src, dest in (
        ("composition.complete_hair_visible", "complete_hair_visible"),
        ("composition.ears_visible", "ears_visible"),
        ("composition.chin_visible", "chin_visible"),
        ("composition.face_centred", "face_centred"),
        ("composition.frontal_pose", "frontal_pose"),
        ("composition.eye_visibility", "eye_visibility"),
    ):
        value = record.v(src)
        if value is not None:
            block[dest] = bool(value)
    return block


def _appearance(record: Record) -> dict[str, Any]:
    block: dict[str, Any] = {}
    for key in ("spectacles", "headwear", "smile", "facial_hair", "face_mask"):
        policy = record.v(f"appearance.{key}")
        if isinstance(policy, dict) and policy.get("policy"):
            entry = {"policy": policy["policy"]}
            if policy.get("condition"):
                entry["condition"] = str(policy["condition"])
            if policy.get("source_wording"):
                entry["source_wording"] = str(policy["source_wording"])
            # The schema requires a condition whenever the policy is
            # conditional, because a conditional rule with no stated condition
            # carries no more information than an omitted one.
            if entry["policy"] == "conditional" and "condition" not in entry:
                continue
            block[key] = entry
    monochrome = record.v("appearance.monochrome_accepted")
    if monochrome is not None:
        block["monochrome_accepted"] = bool(monochrome)
    basis = record.v("appearance.face_coverage_basis")
    if basis:
        block["face_coverage_basis"] = str(basis)
    live = record.v("appearance.live_capture_required")
    if live is not None:
        block["live_capture_required"] = bool(live)
    recency = record.v("appearance.recency_maximum_days")
    if recency is not None:
        block["recency_maximum_days"] = int(recency)
    attestation = record.v("appearance.attestation_required")
    if attestation is not None:
        block["attestation_required"] = bool(attestation)
    imprint_policy = record.v("appearance.imprint.policy")
    if imprint_policy:
        imprint: dict[str, Any] = {"policy": str(imprint_policy)}
        fields = record.v("appearance.imprint.fields")
        if fields:
            imprint["fields"] = [str(f) for f in fields]
        position = record.v("appearance.imprint.position")
        if position:
            imprint["position"] = str(position)
        if imprint_policy == "required" and not imprint.get("fields"):
            imprint = {}
        if imprint:
            block["imprint"] = imprint
    return block


def _filename(record: Record) -> dict[str, Any]:
    mode = record.v("filename.mode")
    block: dict[str, Any] = {"mode": "unspecified", "extension_required": True}
    if mode == "exact" and record.v("filename.exact_filename"):
        block["mode"] = "exact"
        block["exact_filename"] = str(record.v("filename.exact_filename"))
    elif mode == "pattern" and record.v("filename.pattern"):
        block["mode"] = "pattern"
        block["pattern"] = str(record.v("filename.pattern"))
    case_sensitive = record.v("filename.case_sensitive")
    block["case_sensitive"] = (
        bool(case_sensitive) if case_sensitive is not None else False
    )
    instructions = record.v("filename.instructions")
    if instructions:
        block["instructions"] = str(instructions)
    return block


def _exceptional(record: Record, appearance: dict[str, Any]) -> dict[str, Any]:
    block: dict[str, Any] = {}
    imprint = appearance.get("imprint") or {}
    unsupported: list[str] = []
    if imprint.get("policy") == "required":
        block["printed_name"] = "candidate_name" in (imprint.get("fields") or [])
        block["printed_date"] = "photograph_date" in (imprint.get("fields") or [])
        unsupported.append(_IMPRINT_UNSUPPORTED)
    elif imprint.get("policy") == "prohibited":
        block["printed_name"] = False
        block["printed_date"] = False
    if "spectacles" in appearance:
        block["spectacles_restriction"] = (
            appearance["spectacles"]["policy"] != "permitted"
        )
    if "headwear" in appearance:
        block["headwear_restriction"] = appearance["headwear"]["policy"] != "permitted"
    if appearance.get("monochrome_accepted") is False:
        block["black_and_white_restriction"] = True
    if appearance.get("recency_maximum_days") is not None:
        block["recent_photo_requirement"] = True
    block["processing_support_status"] = (
        "partially_supported" if unsupported else "supported"
    )
    if unsupported:
        block["unsupported_requirement_reasons"] = unsupported
    return block


def _evidence_ref(field: Field) -> Optional[str]:
    """Cite the document a value came from, in the form the schema expects.

    An ``official`` provenance entry without one is rejected by the model, and
    correctly so: "this came from the body" is a claim, and a claim with no
    pointer to the document is unverifiable.
    """
    raw = field.raw
    title = str(raw.get("document_title") or "").strip()
    section = str(raw.get("section_name") or "").strip()
    url = str(raw.get("source_url") or "").strip()
    parts = [p for p in (title, section) if p]
    label = " - ".join(parts) if parts else url
    if not label:
        return None
    return f"{label} ({url})" if url else label


def _provenance(
    record: Record,
    tier: str,
    formats_derived: bool,
    dropped_formats: list[str],
    transposed: bool,
) -> dict[str, Any]:
    block: dict[str, Any] = {}
    size_field = record.f("file_size.published_maximum")
    size_ref = _evidence_ref(size_field)
    size_official = size_field.official and bool(size_ref)
    block["image_requirements.file_size"] = {
        "type": "official" if size_official else "inferred",
        **({"evidence_reference": size_ref} if size_ref else {}),
        "reasoning": (
            "Byte ceiling converted from the published figure using 1 KB = 1000 "
            "bytes. No body in the researched set defines the unit, and the "
            "decimal reading is the smaller of the two, so a file satisfying it "
            "also satisfies a 1024-byte reading."
        ),
        "confidence": size_field.confidence,
        "approved": size_official,
    }
    dim_field = next(
        (
            record.f(p)
            for p in (
                "dimensions.width_px",
                "dimensions.minimum_width_px",
                "dimensions.preferred_width_px",
            )
            if record.f(p).present
        ),
        None,
    )
    if dim_field is not None:
        dim_ref = _evidence_ref(dim_field)
        dim_official = dim_field.official and bool(dim_ref)
        block["image_requirements.dimensions"] = {
            "type": "official" if dim_official else "inferred",
            **({"evidence_reference": dim_ref} if dim_ref else {}),
            "reasoning": "Pixel dimensions transcribed from the cited source.",
            "confidence": dim_field.confidence,
            "approved": dim_official,
        }
    else:
        block["image_requirements.dimensions"] = {
            "type": "inferred",
            "reasoning": (
                "The conducting body publishes no pixel dimensions. The output "
                "size is chosen per photograph from the crop geometry, so no "
                "dimension is asserted on the body's behalf."
            ),
            "confidence": 1,
            "approved": False,
        }
    if dropped_formats:
        block["image_requirements.formats.allowed_formats"] = {
            "type": "inferred",
            "reasoning": (
                "The body also permits "
                + ", ".join(sorted(dropped_formats)).upper()
                + ", which this engine cannot produce. The list here is the "
                "intersection of what the body accepts and what the engine "
                "emits; the narrowing loses nothing for the candidate, since "
                "the delivered format is permitted."
            ),
            "confidence": 4,
            "approved": True,
        }
    if formats_derived:
        block["image_requirements.formats.preferred_format"] = {
            "type": "inferred",
            "reasoning": (
                "The body lists permitted formats without naming a preference. "
                "JPEG is selected from the permitted list; JPG and JPEG name the "
                "same format, so this chooses a spelling rather than a format."
            ),
            "confidence": 4,
            "approved": True,
        }
    if transposed:
        block["image_requirements.dimensions.width_px"] = {
            "type": "inferred",
            "reasoning": (
                "The body publishes the pixel figure landscape while giving a "
                "portrait physical size in the same sentence, and the two agree "
                "in magnitude but not orientation. Recorded upright, because an "
                "examination photograph is a head-and-shoulders portrait and no "
                "body in the researched set requires a landscape one. The "
                "published figure is preserved verbatim in "
                "permitted_pixel_range so the transposition is visible."
            ),
            "confidence": 3,
            "approved": True,
        }
    block["image_requirements.composition.crop_profile"] = {
        "type": "platform_default",
        "reasoning": (
            "One composition is used for every examination: the tightest crop "
            "that keeps hair, ears and the chin/beard boundary intact. No "
            "researched body publishes a coverage maximum this would breach, "
            "and all published minima are cleared by it."
        ),
        "confidence": 5,
        "approved": True,
    }
    if tier == "secondary":
        block["image_requirements"] = {
            "type": "inferred",
            "reasoning": (
                "Values for this examination were located only on secondary "
                "sources, not on the conducting body's own material. Recorded "
                "so the examination is servable, and held at provisional status "
                "so the dependence stays visible until an official source is "
                "found."
            ),
            "confidence": 2,
            "approved": False,
        }
    return block


# --- The deliverable inventory ----------------------------------------------

#: Submission methods that produce a file the platform could prepare. The rest
#: are completed by the candidate inside the official portal or at a physical
#: stage, and the model refuses to let them be marked supported.
_DELIVERABLE_METHODS = frozenset(
    {"file_upload", "handwritten_then_uploaded", "document_scan_upload"}
)

_KNOWN_SUBMISSION_METHODS = _DELIVERABLE_METHODS | frozenset(
    {
        "official_live_capture",
        "external_identity_verification",
        "typed_or_selected_declaration",
        "physical_stage_requirement",
    }
)

#: Interim file sizes for deliverables no body published one for (DEC-048).
#:
#: These are placeholders, not readings, and every value written from this table
#: is stamped ``interim_default`` so it can be found and replaced in one query.
#:
#: The signature figure is the *modal* published specification, not the mean.
#: The mean across the 25 published signature records is 10.6-45.2 KB, and a
#: 45 KB signature exceeds the ceiling at SSC, banking, JEE Main, UGC-NET and
#: CTET -- five of the six distinct published specifications. Overshooting a
#: maximum is a hard portal rejection; undershooting is usually harmless. The
#: modal 10-20 KB falls inside five of those six ranges, missing only UPSC's
#: 20 KB floor.
#:
#: The thumb figure is not an average at all: all 13 records that publish one
#: publish 20-50 KB. Handwritten declarations need no entry -- all 13 publish
#: 50-100 KB, so there is no gap to fill, and a constant nothing reads is worse
#: than no constant.
#:
#: The certificate ceiling is a product-owner ruling rather than a reading of a
#: distribution: not one of the 45 certificate deliverables in the research
#: publishes a file size, so there is nothing to average. 400 KB is set as a
#: working ceiling until real figures arrive. It carries no minimum, because a
#: floor invented on top of an invented ceiling would compound the guess, and a
#: scanned certificate that compresses small is not thereby wrong.
_INTERIM_FILE_SIZE_KB: dict[str, tuple[Optional[int], int, str]] = {
    "signature": (
        10,
        20,
        "No published signature file size for this body. Standing in with the "
        "modal published specification across the researched set (10-20 KB), "
        "which falls inside five of the six distinct published ranges. The "
        "arithmetic mean (10.6-45.2 KB) was rejected: its ceiling exceeds five "
        "of those six, and overshooting a maximum is a hard portal rejection.",
    ),
    "thumb_impression": (
        20,
        50,
        "No published thumb-impression file size for this body. Standing in "
        "with 20-50 KB, which is not an average but the only specification in "
        "the researched set -- all 13 records that publish one agree on it.",
    ),
    "certificate_scan": (
        None,
        400,
        "No published file size for this certificate, and none for any of the "
        "45 certificate deliverables in the research, so no distribution exists "
        "to stand in for. 400 KB is a product-owner working ceiling pending the "
        "published figures. No minimum is set: a floor on top of an invented "
        "ceiling would compound the guess.",
    ),
}

#: Deliverable types whose format is stood in for when none is published. The
#: certificate types are excluded: portals variously accept PDF and JPEG for a
#: certificate scan, and the engine cannot encode PDF, so a JPG placeholder
#: would assert a format the body may not take.
_INTERIM_FORMAT_TYPES = frozenset({"signature", "thumb_impression"})

#: Interim format for an ink-on-paper deliverable whose body published none.
#: Every published format across the signature, thumb and declaration records in
#: the research is JPG or JPEG, so this is the set's only value rather than a
#: choice between competing ones.
_INTERIM_FORMAT_REASONING = (
    "No published file format for this deliverable. Standing in with JPG, "
    "which is the only format any body in the researched set publishes for a "
    "signature, thumb impression or handwritten declaration."
)

#: Deliverable types that get an interim specification when the body published
#: none. Certificates are deliberately excluded: not one of the 45 certificate
#: deliverables in the research carries a published file size, so there is no
#: distribution to stand in for -- inventing one would be a guess about a guess.
_INTERIM_TYPES = frozenset(_INTERIM_FILE_SIZE_KB)


def _requirement_type(name: str, method: str) -> str:
    """Classify a deliverable by what it is, from its published name.

    Order matters and is not alphabetical. "Left thumb impression" contains no
    "sign", but "Valid photo identity document" contains both "photo" and
    "identity" and is an identity document; a declaration confirmed on screen is
    a portal declaration while one written on paper is a handwritten one.
    """
    lowered = name.lower()
    if any(word in lowered for word in ("thumb", "finger", "impression")):
        return "thumb_impression"
    if "declaration" in lowered:
        if method == "typed_or_selected_declaration":
            return "portal_declaration"
        return "handwritten_declaration"
    if "sign" in lowered:
        return "signature"
    if any(word in lowered for word in ("identity", "aadhaar")):
        return "identity_document"
    if any(
        word in lowered
        for word in (
            "certificate",
            "marksheet",
            "mark sheet",
            "proof",
            "testimonial",
            "noc",
            "forms",
            "particulars",
        )
    ):
        return "certificate_scan"
    if "photo" in lowered:
        return "photograph"
    return "other"


def _requirement_status(published: Optional[str]) -> str:
    """Map the report's status wording onto the schema's four states.

    The report states status in prose and uses twelve distinct phrasings. The
    ones that hedge -- "or portal-dependent", "upload status not fully
    established" -- become ``portal_dependent`` rather than ``mandatory``,
    because asserting a requirement the evidence did not establish is the same
    class of error as asserting a specification it did not establish.
    """
    text = (published or "").strip().lower()
    if not text:
        return "portal_dependent"
    if "portal-dependent" in text or "not fully established" in text:
        return "portal_dependent"
    if "later-stage" in text:
        return "conditional"
    if text.startswith("conditional"):
        return "conditional"
    if "conditional" in text or "alternative" in text or "if not already" in text:
        return "conditional"
    if "physical-stage" in text:
        return "mandatory"
    if text.startswith("mandatory"):
        return "mandatory"
    if text.startswith("optional"):
        return "optional"
    return "portal_dependent"


def _platform_support(
    requirement_type: str, method: str, photograph_status: str
) -> str:
    """What the platform does for one deliverable.

    Non-photograph deliverables are ``not_yet_supported`` even where a full
    specification exists, because the engine that would prepare them is not
    built. Marking them supported on the strength of having a specification
    would be a fictional success: the record would promise an output nothing
    can produce.
    """
    if method == "physical_stage_requirement":
        return "physical_stage"
    if method not in _DELIVERABLE_METHODS:
        return "guidance_only"
    if requirement_type == "photograph":
        return photograph_status
    return "not_yet_supported"


def _deliverable_file_spec(
    parsed: dict[str, Any], requirement_type: str
) -> tuple[dict[str, Any], list[str]]:
    """Build one deliverable's file specification.

    Returns the block and the list of field paths within it that carry an
    interim placeholder rather than a published value.
    """
    spec: dict[str, Any] = {}
    interim: list[str] = []

    size = parsed.get("file_size_kb") or {}
    maximum = size.get("maximum")
    minimum = size.get("minimum")
    if maximum is not None:
        block: dict[str, Any] = {"maximum_bytes": int(maximum * _BYTES_PER_KB)}
        if minimum is not None:
            block["minimum_bytes"] = int(minimum * _BYTES_PER_KB)
            block["published_minimum"] = minimum
        block["published_maximum"] = maximum
        block["size_unit_as_published"] = "KB"
        spec["file_size"] = block
    elif requirement_type in _INTERIM_TYPES:
        low, high, _ = _INTERIM_FILE_SIZE_KB[requirement_type]
        block = {"maximum_bytes": high * _BYTES_PER_KB}
        interim.append("file_size.maximum_bytes")
        if low is not None:
            block["minimum_bytes"] = low * _BYTES_PER_KB
            interim.append("file_size.minimum_bytes")
        spec["file_size"] = block

    formats = parsed.get("formats") or {}
    values = [f for f in (formats.get("values") or []) if f in _ENGINE_FORMATS]
    if values:
        spec["formats"] = {
            "allowed_formats": values,
            "preferred_format": values[0],
        }
    elif requirement_type in _INTERIM_FORMAT_TYPES:
        spec["formats"] = {"allowed_formats": ["jpg"], "preferred_format": "jpg"}
        interim.append("formats.allowed_formats")

    # Dimensions are deliberately never stood in for. The two published
    # signature dimensions are 140x60 and 580x180 -- different aspect ratios --
    # so an average would invent a shape no body publishes. A deliverable with
    # no published dimension is sized from its own source, exactly as the
    # size-only photograph records already are.
    dimensions = parsed.get("dimensions_px") or {}
    if dimensions.get("mode") == "exact":
        spec["dimensions"] = {
            "mode": "exact",
            "width_px": dimensions["width"],
            "height_px": dimensions["height"],
        }
    elif dimensions.get("mode") == "range":
        spec["dimensions"] = {
            "mode": "range",
            "minimum_width_px": dimensions["minimum_width"],
            "maximum_width_px": dimensions["maximum_width"],
            "minimum_height_px": dimensions["minimum_height"],
            "maximum_height_px": dimensions["maximum_height"],
        }

    filename = parsed.get("filename") or {}
    if filename.get("value"):
        stem = str(filename["value"]).rsplit(".", 1)[0]
        spec["filename"] = {"mode": "exact", "exact_filename": stem}

    return spec, interim


def _requirements(
    deliverables: list[dict[str, Any]], photograph_status: str
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    """Convert one exam's deliverables into the rule's inventory.

    Returns the inventory, the provenance entries for any interim value it
    contains, and the names of deliverables that could not be encoded.
    """
    inventory: list[dict[str, Any]] = []
    provenance: dict[str, Any] = {}
    unencodable: list[str] = []
    used_ids: set[str] = set()

    for deliverable in deliverables:
        method = str(deliverable.get("submission_method") or "")
        if method not in _KNOWN_SUBMISSION_METHODS:
            # The report could not establish how the item is provided. A guess
            # here would put a submission method into the record that no source
            # supports, so the item is reported instead.
            unencodable.append(str(deliverable.get("name") or "unknown"))
            continue

        name = str(deliverable.get("name") or "").strip()
        requirement_type = _requirement_type(name, method)
        requirement_id = _slug(name).replace("-", "_")[:48] or "requirement"
        suffix = 2
        while requirement_id in used_ids:
            requirement_id = f"{_slug(name).replace('-', '_')[:44]}_{suffix}"
            suffix += 1
        used_ids.add(requirement_id)

        entry: dict[str, Any] = {
            "requirement_id": requirement_id,
            "requirement_name": name,
            "requirement_type": requirement_type,
            "submission_method": method,
            "requirement_status": _requirement_status(
                deliverable.get("requirement_status")
            ),
            "platform_support": _platform_support(
                requirement_type, method, photograph_status
            ),
        }
        applicability = deliverable.get("applicability")
        if applicability:
            entry["applicability"] = str(applicability)
        specification = deliverable.get("specification")
        if specification:
            entry["content_instructions"] = str(specification)
        evidence_status = deliverable.get("evidence_status")
        if evidence_status:
            entry["evidence_status"] = str(evidence_status)
        note = deliverable.get("important_note")
        if note:
            entry["notes"] = str(note)

        # The photograph's specification is image_requirements; a second copy
        # here is rejected by the model and would be a second truth if it were
        # not.
        if requirement_type != "photograph" and method in _DELIVERABLE_METHODS:
            spec, interim_paths = _deliverable_file_spec(
                deliverable.get("parsed") or {}, requirement_type
            )
            if spec:
                entry["file_spec"] = spec
            index = len(inventory)
            for path in interim_paths:
                key = f"requirements[{index}].file_spec.{path}"
                reasoning = (
                    _INTERIM_FILE_SIZE_KB[requirement_type][2]
                    if path.startswith("file_size")
                    else _INTERIM_FORMAT_REASONING
                )
                provenance[key] = {
                    "type": "interim_default",
                    "reasoning": reasoning,
                    "confidence": 1,
                    "approved": False,
                }

        inventory.append(entry)

    return inventory, provenance, unencodable


_STATUS_BY_TIER = {
    "full": "verified",
    "size_only": "verified_with_ambiguity",
    "secondary": "provisional",
}


def build_rule(
    record: Record,
    tier: str,
    deliverables: Optional[list[dict[str, Any]]] = None,
) -> tuple[Optional[dict[str, Any]], list[str]]:
    file_size = _file_size(record)
    formats_result = _formats(record)
    if file_size is None or formats_result is None:
        return None, []
    formats, dropped_formats = formats_result
    appearance = _appearance(record)
    year = record.data.get("examination_year")
    stage = str(record.data.get("application_stage") or "application")
    role = str(record.data.get("photo_role") or "")
    identity = record.name if stage == "application" else f"{record.name} {stage}"
    if role and role not in ("candidate_photograph",):
        identity = f"{identity} {role}"
    rule_id = _slug(identity)
    exam: dict[str, Any] = {
        "exam_id": rule_id,
        "exam_name": record.name,
        "conducting_body": str(record.data.get("conducting_body") or "unknown"),
        "examination_year": int(year) if isinstance(year, int) else 2026,
        "application_cycle": str(record.data.get("application_cycle") or "current"),
    }
    aliases = record.data.get("aliases")
    if aliases:
        exam["aliases"] = [str(a) for a in aliases]
    if stage:
        exam["application_stage"] = stage
    if record.data.get("jurisdiction"):
        exam["jurisdiction"] = str(record.data["jurisdiction"])
    if record.data.get("category"):
        exam["category"] = str(record.data["category"])

    published_pref = record.v("formats.preferred_format")
    formats_derived = not (
        published_pref
        and str(published_pref).lower().strip() in formats["allowed_formats"]
    )
    composition = _composition(record)
    dimensions = _dimensions(record)
    transposed = bool(dimensions.pop("_transposed", False))
    exceptional = _exceptional(record, appearance)
    inventory, interim_provenance, unencodable = _requirements(
        deliverables or [], str(exceptional["processing_support_status"])
    )
    rule = {
        "schema_version": "1.1",
        "rule_id": rule_id,
        "rule_version": "1.0.0",
        "status": _STATUS_BY_TIER[tier],
        "exam": exam,
        "source_evidence": _source_evidence(record),
        "image_requirements": {
            "dimensions": dimensions,
            "file_size": file_size,
            "formats": formats,
            "background": _background(record),
            "composition": composition,
            "appearance": appearance,
            "filename": _filename(record),
            "exceptional_instructions": exceptional,
        },
        "provenance": {
            **_provenance(record, tier, formats_derived, dropped_formats, transposed),
            **interim_provenance,
        },
        "verification": {"verification_status": _STATUS_BY_TIER[tier]},
        "fictional_example": False,
    }
    if inventory:
        # Placed directly after the photograph specification so the record reads
        # in the order the product does: the exam, its evidence, its photograph
        # rule, then everything else the exam asks for.
        ordered: dict[str, Any] = {}
        for key, value in rule.items():
            ordered[key] = value
            if key == "image_requirements":
                ordered["requirements"] = inventory
        rule = ordered
    if not rule["source_evidence"]:
        return None, unencodable
    return rule, unencodable


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--specs", type=Path, required=True)
    parser.add_argument(
        "--deliverables",
        type=Path,
        default=None,
        help=(
            "Deliverable-inventory sidecar from extract_deliverables.py. "
            "Omitted, every rule is written with a photograph specification and "
            "no inventory -- which is the pre-inventory catalogue, not a claim "
            "that these exams require only a photograph."
        ),
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument(
        "--prefix",
        default="exam_",
        help="Filename prefix for generated rule records.",
    )
    args = parser.parse_args()

    records = [Record(r) for r in json.loads(args.specs.read_text(encoding="utf-8"))]
    args.out.mkdir(parents=True, exist_ok=True)

    # The two research sidecars cover the same 50 examination-stage records and
    # are joined on the examination name plus stage. A record present in one and
    # absent from the other is reported rather than dropped silently, because a
    # silent miss looks exactly like an exam that requires only a photograph.
    deliverables_by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    if args.deliverables:
        for entry in json.loads(args.deliverables.read_text(encoding="utf-8")):
            key = (
                str(entry.get("exam_name") or "").strip(),
                str(entry.get("application_stage") or "application").strip(),
            )
            deliverables_by_key[key] = entry.get("deliverables") or []
    unmatched_specs: list[str] = []
    matched_keys: set[tuple[str, str]] = set()

    # The script owns every record carrying its prefix, so a re-run replaces the
    # catalogue rather than adding to it. Without this an examination that was
    # renamed, retired, or dropped from the research on a later pass would leave
    # a stale rule file behind that no evidence supports and nothing removes --
    # and a stale rule is worse than a missing one, because the pipeline will
    # happily serve it.
    for stale in sorted(args.out.glob(f"{args.prefix}*.json")):
        stale.unlink()

    written: list[tuple[str, str, Path]] = []
    skipped: list[tuple[str, str, str]] = []
    rejected: list[tuple[str, list[str]]] = []
    unencodable_items: list[tuple[str, str]] = []
    unserved_deliverables: list[tuple[str, int]] = []

    for record in records:
        tier = record.tier()
        stage_key = (
            record.name,
            str(record.data.get("application_stage") or "application"),
        )
        # Matched before the skips, so "unmatched" means the two research
        # sidecars genuinely disagree about which examinations exist -- not that
        # an examination was skipped for a photograph reason. Those are
        # different findings and were briefly reported as the same one.
        if args.deliverables:
            if stage_key in deliverables_by_key:
                matched_keys.add(stage_key)
            else:
                unmatched_specs.append(f"{stage_key[0]} ({stage_key[1]})")
            if tier in ("live_capture_only", "incomplete"):
                count = len(
                    [
                        item
                        for item in deliverables_by_key.get(stage_key, [])
                        if item.get("submission_method") in _DELIVERABLE_METHODS
                        and _requirement_type(
                            str(item.get("name") or ""),
                            str(item.get("submission_method") or ""),
                        )
                        != "photograph"
                    ]
                )
                if count:
                    unserved_deliverables.append((record.name, count))

        if tier == "live_capture_only":
            skipped.append(
                (
                    record.name,
                    "live capture only",
                    "The portal photographs the candidate directly; there is no "
                    "upload specification and nothing for the platform to deliver.",
                )
            )
            continue
        if tier == "incomplete":
            missing = []
            if not record.f("file_size.published_maximum").present:
                missing.append("file size")
            if not record.f("formats.allowed_formats").present:
                missing.append("format")
            conflicting = [
                path
                for path, field in record.fields.items()
                if field.status == "conflicting"
            ]
            detail = "no " + " and no ".join(missing) if missing else "incomplete"
            if conflicting:
                detail += f"; conflicting: {', '.join(sorted(conflicting))}"
            skipped.append((record.name, "incomplete evidence", detail))
            continue

        rule, unencodable = build_rule(
            record, tier, deliverables_by_key.get(stage_key, [])
        )
        for item in unencodable:
            unencodable_items.append((record.name, item))
        if rule is None:
            skipped.append(
                (
                    record.name,
                    "incomplete evidence",
                    "required block could not be built",
                )
            )
            continue

        errors = validate_exam_rule(rule)
        blocking = [e for e in errors if e.severity.value == "error"]
        if blocking:
            rejected.append(
                (record.name, [f"{e.field_path}: {e.message}" for e in blocking[:6]])
            )
            continue

        path = args.out / f"{args.prefix}{rule['rule_id'].replace('-', '_')}.json"
        path.write_text(json.dumps(rule, indent=2) + "\n", encoding="utf-8")
        written.append((record.name, tier, path))

    unmatched_deliverables = sorted(
        f"{key[0]} ({key[1]})" for key in deliverables_by_key if key not in matched_keys
    )
    _write_report(
        args.report,
        written,
        skipped,
        rejected,
        unencodable_items,
        unmatched_specs,
        unmatched_deliverables,
        unserved_deliverables,
    )

    print(f"written  : {len(written)}")
    print(f"skipped  : {len(skipped)}")
    print(f"rejected : {len(rejected)}")
    if args.deliverables:
        print(
            f"inventory unmatched : {len(unmatched_specs) + len(unmatched_deliverables)}"
        )
        print(f"items not encodable : {len(unencodable_items)}")
    for name, messages in rejected:
        print(f"  REJECTED {name}")
        for message in messages:
            print(f"     {message}")
    return 1 if rejected else 0


def _write_report(
    path: Path,
    written: list[tuple[str, str, Path]],
    skipped: list[tuple[str, str, str]],
    rejected: list[tuple[str, list[str]]],
    unencodable_items: list[tuple[str, str]],
    unmatched_specs: list[str],
    unmatched_deliverables: list[str],
    unserved_deliverables: list[tuple[str, int]],
) -> None:
    tier_label = {
        "full": "Full specification (official dimensions, size and format)",
        "size_only": "Size and format only -- no pixel dimensions published",
        "secondary": "Secondary sources only -- provisional",
    }
    lines = [
        "# Exam Rule Catalogue -- Coverage and Gap Register",
        "",
        "Generated by `scripts/encode_exam_rules.py` from the 48-examination",
        "evidence research. Do not edit by hand: re-running the script rebuilds",
        "both the rule records and this register, so a manual edit here is lost",
        "and a manual edit to a rule record silently diverges from its evidence.",
        "",
        f"**Encoded: {len(written)}. Not encoded: {len(skipped)}. "
        f"Rejected by validation: {len(rejected)}.**",
        "",
        "## Encoded",
        "",
        "| Examination | Tier | Record |",
        "|---|---|---|",
    ]
    for name, tier, file_path in sorted(written, key=lambda row: (row[1], row[0])):
        lines.append(f"| {name} | {tier_label.get(tier, tier)} | `{file_path.name}` |")
    lines += [
        "",
        "## Not encoded",
        "",
        "These are recorded rather than dropped, so the gap stays visible and a",
        "later research pass knows exactly what is missing.",
        "",
        "| Examination | Reason | Detail |",
        "|---|---|---|",
    ]
    for name, reason, detail in sorted(skipped):
        lines.append(f"| {name} | {reason} | {detail} |")
    if rejected:
        lines += ["", "## Rejected by validation", ""]
        for name, messages in rejected:
            lines.append(f"- **{name}**")
            for message in messages:
                lines.append(f"  - {message}")

    if unencodable_items:
        lines += [
            "",
            "## Deliverables recorded in the research but not encoded",
            "",
            "The research could not establish how the candidate provides these,",
            "so no submission method could be written without guessing one.",
            "",
            "| Examination | Deliverable |",
            "|---|---|",
        ]
        for exam_name, item in sorted(unencodable_items):
            lines.append(f"| {exam_name} | {item} |")

    if unserved_deliverables:
        lines += [
            "",
            "## Examinations not encoded that still have deliverables",
            "",
            "These were skipped for a *photograph* reason -- the portal captures",
            "the candidate live, or the photograph evidence is incomplete -- but",
            "the examination still requires files the platform could prepare.",
            "Dropping the examination drops those too, which is a coverage gap",
            "rather than a correct exclusion. A rule record currently requires a",
            "photograph specification, which is what blocks them.",
            "",
            "| Examination | Non-photograph deliverables |",
            "|---|---:|",
        ]
        for exam_name, count in sorted(unserved_deliverables):
            lines.append(f"| {exam_name} | {count} |")

    if unmatched_specs or unmatched_deliverables:
        lines += [
            "",
            "## Research records present in one sidecar only",
            "",
            "The photograph and deliverable research are joined on examination",
            "name plus stage. A record here is missing its counterpart, so its",
            "rule carries no inventory -- which is not the same statement as the",
            "examination requiring only a photograph.",
            "",
        ]
        for entry in unmatched_specs:
            lines.append(f"- Photograph record with no deliverable record: {entry}")
        for entry in unmatched_deliverables:
            lines.append(f"- Deliverable record with no photograph record: {entry}")

    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
