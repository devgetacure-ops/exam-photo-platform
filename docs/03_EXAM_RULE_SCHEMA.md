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
* **image_requirements** (object, required): Physical image criteria (dimensions, sizes, etc.) for the examination's candidate photograph.
* **requirements** (array, optional): The complete inventory of what the examination asks for at this stage. See *Requirements* below. Absence means the deliverable research has not been done for that examination — never that the photograph is the only requirement.
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

### Requirements

One entry per item the examination asks for during application (DEC-047).

* `requirement_id` (string, required): Unique within the rule, `^[a-z0-9_]+$`. Orders and packages reference it, so it must not be regenerated from a display name.
* `requirement_name` (string, required).
* `requirement_type` (string, required): `photograph`, `signature`, `thumb_impression`, `handwritten_declaration`, `certificate_scan`, `identity_document`, `portal_declaration`, `other`.
* `submission_method` (string, required): `file_upload`, `handwritten_then_uploaded`, `document_scan_upload`, `official_live_capture`, `external_identity_verification`, `typed_or_selected_declaration`, `physical_stage_requirement`.
* `requirement_status` (string, required): `mandatory`, `conditional`, `optional`, `portal_dependent`.
* `platform_support` (string, required): `supported`, `partially_supported`, `guidance_only`, `physical_stage`, `not_yet_supported`.
* `file_spec` (object, optional): `dimensions`, `file_size`, `formats`, `filename`, each reusing the `$defs` the photograph rule uses.
* `applicability`, `content_instructions`, `rejection_conditions`, `evidence_status`, `notes` (optional).

Type and method are independent: a live portal photograph is a `photograph`
submitted by `official_live_capture`, not a type of its own.

`platform_support` is a separate vocabulary from
`image_requirements.exceptional_instructions.processing_support_status`. They
answer different questions — what the platform does for one item, versus how
completely the photograph pipeline satisfies a photograph rule.

**The inventory includes items the platform cannot produce.** An omitted
requirement reads as "this examination does not ask for it", which for a
live-capture or physical-stage item is false.

### provenance types

`official`, `inferred`, `platform_default`, and `interim_default`.

`interim_default` (DEC-048) marks a value the platform chose because no source
published one — a placeholder standing in until the real figure is supplied. It
is deliberately distinct from `platform_default`, which is a settled policy
choice the platform stands behind. An interim value is known to be
wrong-until-replaced, and collapsing the two would make every placeholder
unfindable the moment the real figures arrive.

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
8. A `photograph` requirement must not carry a `file_spec`. Its specification is `image_requirements`, so there is exactly one place a photograph rule can live.
9. A submission method the platform cannot execute — `official_live_capture`, `external_identity_verification`, `typed_or_selected_declaration`, `physical_stage_requirement` — cannot be marked `supported` or `partially_supported`.
10. `platform_support: physical_stage` and `submission_method: physical_stage_requirement` imply each other.
11. `platform_support: supported` on a non-photograph requirement requires a `file_spec` carrying at least a `file_size` or a `formats` block. "Supported" is a promise to produce the file; dimensions alone leave nothing to encode or compress to.
12. A `conditional` requirement must state its `applicability`, on the same reasoning as constraint 6.
13. `requirement_id` is unique within a rule, and at most one photograph requirement may use a file-producing submission method — a rule carries one `image_requirements` block, so it can specify one uploaded photograph.
14. A rule containing any `interim_default` provenance entry cannot hold `verified` or `verified_with_ambiguity` status. Interim entries additionally require `reasoning`, carry `confidence: 1`, and cannot be `approved`.

Constraints 6 and 7 are expressed in the JSON Schema itself via `if`/`then`,
not only in the Pydantic mirror. The schema is canonical and the web admin
console validates against it directly, so a constraint living only in Python
would let a TypeScript consumer accept an invalid record.

Constraints 8 to 14 are cross-field and currently live in the Pydantic mirror
only; the JSON Schema carries the shapes and enums. Every current writer —
the encoder, the admin console and `POST /v1/rules/validate` — goes through
`validate_exam_rule`, which runs both, so nothing writes a record that skips
them. A future direct-to-JSON-Schema consumer would be the gap.
