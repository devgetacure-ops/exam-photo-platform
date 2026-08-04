# Canonical Exam Rule Schema Specification (03_EXAM_RULE_SCHEMA.md)

This specification defines the canonical, language-neutral schema for examination rule configuration files. All language-specific model implementations (e.g., Python Pydantic models) must conform to this schema.

---

## 1. Top-Level Structure

Every rule file is a JSON object containing:

* **schema_version** (string, required): Schema version reference (e.g., `"1.0"`).
* **rule_id** (string, required): Unique machine-safe rule identifier.
* **rule_version** (string, required): Semantic version of this rule.
* **status** (string, required): Enum of: `draft`, `provisional`, `verified`, `verified_with_ambiguity`, `expired`, `superseded`.
* **exam** (object, required): Identifies the target exam cycle.
* **source_evidence** (array, required): Source documentation evidence.
* **image_requirements** (object, required): Physical image criteria (dimensions, sizes, etc.).
* **provenance** (object, required): Field-level metadata origin tracking.
* **verification** (object, required): Quality check status.
* **effective_period** (object, optional): Cycle applicability period.
* **supersession** (object, optional): Version history links.
* **notes** (string, optional): General comments.
* **fictional_example** (boolean, required): True if the record is a mock example.

---

## 2. Component Structures

### Exam Identity
* `exam_id` (string, required): Machine-safe lowercase slug (e.g., `jee-main-2026`). Matches `^[a-z0-9\-]+$`.
* `exam_name` (string, required): Full official exam name.
* `aliases` (array of strings, optional): Alternative name listings. Must not duplicate primary name.
* `conducting_body` (string, required): Organizing authority.
* `examination_year` (integer, required): Target year.
* `application_cycle` (string, required): Stage identifier (e.g., `Cycle 1`).

### Source Evidence
* `source_type`: `official_webpage`, `official_notification`, `official_information_bulletin`, `official_application_portal`, `official_pdf`, `secondary_reference`, or `internal_research_note`.
* `official_source` (boolean, required).
* `source_url` (string, optional): HTTP/HTTPS/File scheme web links.
* `captured_wording` (string, required): Exact copy-pasted wording.

### Image Requirements
* **dimensions**:
  - `mode`: `exact`, `range`, or `unspecified`.
  - `width_px`, `height_px` (integers, Mode `exact`).
  - `dpi` (integer, optional): Target square output DPI/JFIF density when an exam specifies it.
  - `minimum_width_px`, `maximum_width_px`, `minimum_height_px`, `maximum_height_px` (integers, Mode `range`).
  - `platform_default_profile`, `fallback_reason` (strings, Mode `unspecified`).
* **file_size**:
  - `maximum_bytes` (integer, required).
  - `minimum_bytes` (integer, optional).
  - `safety_margin_bytes` (integer, optional).
* **formats**:
  - `allowed_formats` (array, required): Normalized format extensions (e.g. `["jpg", "jpeg"]`).
  - `preferred_format` (string, required).
* **background**:
  - `mode`: `exact_colour`, `plain_light`, `plain_background`, or `unspecified`.
  - `required_colour` (hex color string e.g., `#FFFFFF`).
* **composition**:
  - `face_coverage_target` (float, e.g. `75.0`).
  - `coverage_is_strict` (boolean, defaults safely to `false`).
  - `crop_profile`, `ears_policy`, and the head-height / top-margin / eye-line / centring / torso ratio bounds that drive the adaptive crop search.
* **appearance** (optional, added by DEC-042): candidate-appearance rules carried per exam.
  - `spectacles`, `headwear`, `smile`, `facial_hair`, `face_mask`: each an `appearancePolicy` (see below).
  - `monochrome_accepted` (boolean): most bodies require colour; CUET-PG and UGC-NET accept either.
  - `face_coverage_basis`: `face_box_area`, `face_height`, `head_height`, or `unspecified`. Carried because the published percentages (50, 60-70, ~75, 80) are **not comparable across bodies** -- they do not agree on what is being measured.
  - `live_capture_required` (boolean), `recency_maximum_days` (integer), `prohibited_provenance` (array): recorded for guidance only. None is checkable from a submitted image, so none may produce a warning or a block.
  - `imprint`: `policy` of `required` / `prohibited` / `unspecified`, plus `fields` and `position`. TNPSC, Kerala PSC and CBSE require a printed name and date; Railways prohibits any name, date or mark on the photograph.
  - `attestation_required` (boolean): NEET and UGC-NET state attestation is unnecessary; several state commissions require it.
* **filename**:
  - `mode`: `exact`, `pattern`, or `unspecified`.
  - `exact_filename` or `pattern` (strings). Path separation and traversal patterns (`..`) are strictly rejected.

### appearancePolicy (`$defs`)

A three-state rule: `policy` is `permitted`, `prohibited`, or `conditional`,
with an optional `condition` string and a `source_wording` verbatim anchor.

`conditional` exists because conducting bodies publish rules a boolean cannot
express -- "prohibited except for religious reasons", "permitted only if
regularly worn". Recording those as either permitted or prohibited would assert
something the body did not say, and they are exactly the cases with the highest
cost of error, covering religious head coverings and prescription eyewear.

**An omitted appearance field means the body did not specify that rule.** It is
never read as permission and never as prohibition.

---

## 3. Contradiction Rules

The schema validator enforces:
1. Exact mode requires both width and height. Range fields must be omitted.
2. In range mode, minimum boundaries must not exceed maximum boundaries.
3. Minimum file bytes must not exceed maximum file bytes. Safety margins must not exceed maximum size limits.
4. Preferred format must be included in allowed format lists.
5. Fictional examples cannot have an officially verified status.
6. A `conditional` appearance policy must state its `condition`. Without one it carries no more information than an omitted rule.
7. A `required` imprint must name its `fields`. The engine cannot infer whether a body wants the name, the date, or both.

Constraints 6 and 7 are expressed in the JSON Schema itself via `if`/`then`,
not only in the Pydantic mirror. The schema is canonical and the web admin
console validates against it directly, so a constraint living only in Python
would let a TypeScript consumer accept an invalid record.
