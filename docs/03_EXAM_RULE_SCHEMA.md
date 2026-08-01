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
* **filename**:
  - `mode`: `exact`, `pattern`, or `unspecified`.
  - `exact_filename` or `pattern` (strings). Path separation and traversal patterns (`..`) are strictly rejected.

---

## 3. Contradiction Rules

The schema validator enforces:
1. Exact mode requires both width and height. Range fields must be omitted.
2. In range mode, minimum boundaries must not exceed maximum boundaries.
3. Minimum file bytes must not exceed maximum file bytes. Safety margins must not exceed maximum size limits.
4. Preferred format must be included in allowed format lists.
5. Fictional examples cannot have an officially verified status.
