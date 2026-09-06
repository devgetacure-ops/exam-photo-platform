# Deep research brief — Indian examination upload specifications

Copy everything below the line into the research tool, and attach the four
research zips plus `OUTSTANDING_UPLOAD_RULES.md`.

---

## Your task

Find and record the **published file-upload specifications** that Indian
examination authorities impose on the documents a candidate uploads with their
application — photograph, signature, thumb impression, handwritten declaration,
and certificate scans.

The output is consumed by a program, not read by a person. **An answer in the
wrong format is unusable even when the facts are right**, so the output contract
in section 5 is the most important part of this brief.

## 1. What you are being given

| Attachment | What it is | How to use it |
|---|---|---|
| `exam-research-FINAL-nationwide-high-volume-closed.zip` | 97 examinations, market discovery, v3.0.0 | **The exam list for workstream A.** Read `research/research-package.json`. |
| `exam-research-batch-02-...zip` | 57 examinations, v2.1.0 | **Superseded** — all 57 are inside the FINAL package. Reference only. |
| `exam-research-2.zip` | 3 records in the target output format | **A worked example of the format you must produce.** |
| `exam-research-1.zip` | 2 records | **Superseded** by `exam-research-2`. Ignore. |
| `OUTSTANDING_UPLOAD_RULES.md` | The worklist, ranked by candidate volume | **Your task list.** Every row is a job. |

Two facts about the FINAL package that shape the work:

- It proved **market volume**, not upload rules. It says so itself: *"Market-volume
  evidence does not silently become a technical upload rule."* It is phase one;
  you are phase two.
- **Only 9 of its 89 unresolved examinations have an official government source
  recorded.** For the other 80, the authority's own notification or portal
  instruction page **has not been located**. Locating it is the first half of the
  job, and often the harder half.

## 2. The two fields that decide everything

An examination is unusable to us unless **both** of these are found:

| Field | Example published wording |
|---|---|
| Maximum file size | "photograph must not exceed 50 KB" |
| Allowed formats | "JPEG only" / "JPG, JPEG or PNG" |

**Pixel dimensions are welcome but optional.** An examination that publishes only
"JPEG, under 50 KB" is fully usable. An examination missing either of the two
above is unusable no matter how much else you find. **Prioritise these two.**

## 3. The four workstreams

Work them in this order. Within workstream A, work in the worklist's order — it
is sorted by candidate volume, so row 1 is worth ~4.8 million candidates and row
89 is worth ~100,000.

**A. 89 newly discovered examinations** (Section 1 of the worklist).
For each: locate the authority's current notification or portal upload-instruction
page, then extract every field in section 5. Where a row already lists something
under "Already known", **do not re-fetch it** — but do record it in your output
with its source, so each record stands alone.

**B. 7 examinations already in our catalogue but blocked** (Section 2).
Five need a missing value. **Two need a conflict resolved, not a value found** —
RPSC and Indian Army Agniveer (online upload) each have two contradictory
published figures on record. For those the deliverable is a decision: which
figure is current and authoritative, with the evidence for preferring it. Say
plainly if both are live on different official pages, because that is itself the
answer.

**C. 86 interim placeholder values across 24 examinations we already publish.**
These are real examinations we serve today, where we invented a plausible number
because none was found. They are **not photograph values** — they are:

| Deliverable | Placeholder values |
|---|---:|
| Certificate / ID scan | 31 |
| Signature | 18 |
| Thumb impression | 2 |

**This workstream has the highest value per hour of any here** — these are
examinations candidates already reach, today, answered with a number we made up.
For each, find the authority's published signature / certificate /
thumb-impression size and format. If the authority genuinely publishes nothing
for a deliverable, **say so explicitly** — that is a real and useful finding.

The 24 examinations, exactly:

| | |
|---|---|
| BPSC Current Recruitment Photograph Specification | Management Aptitude Test 2026 |
| Common Admission Test 2025 | MPSC General Online Application Photograph Instruction |
| CUET (PG) 2026 | NEET (UG) 2026 |
| CUET (UG) 2026 | RRB Level-1 Posts - CEN 08/2024 |
| GATE 2026 | RRB NTPC Graduate - CEN 05/2024 |
| IBPS CRP Customer Service Associates-XV | TNPSC Combined Technical Services Examination 2025 |
| IBPS CRP PO/MT-XVI | UGC-NET June 2026 |
| IBPS CRP Regional Rural Banks-XIV | WBJEE 2026 |
| IBPS CRP Specialist Officers-XVI | WBPSC / WBCS Current Online Application Photograph |
| ICAI Examination Portal Photograph (current portal scope) | Karnataka Common Entrance Test 2026 |
| ICSI Student Registration / Examination Account Photograph | Karnataka PSC Current Recruitment Portal Photograph |
| JEE (Main) 2026 | Kerala PSC One Time Registration Photograph |

**D. 7 examinations resting on secondary sources only.** BPSC, CAT 2025, GIC
Assistant Manager 2024-25, Karnataka CET 2026, Karnataka PSC, WBJEE 2026,
WBPSC/WBCS. Their values came from coaching sites and news coverage rather than
the authority. Confirm or correct each against an official source.

**Six of these seven are also in workstream C** — everything except GIC. Do both
jobs in one visit to the authority's page: confirm the photograph values you
already hold, and pick up the missing signature and certificate values while you
are there. Treated separately this is thirteen visits; treated together it is
seven.

## 4. Evidence rules — non-negotiable

1. **Absent is not permissive.** If an authority publishes no format, record
   `not_found`. **Never** default to JPEG because it is usual. A guessed value is
   worse than a gap, because a gap is visible and a guess is not.
2. **Official sources only for the values.** The conducting body's own domain,
   notification PDF, information bulletin, or portal instruction page. Coaching
   sites, news articles and aggregators may be used to *locate* the official
   document, never to source a value. Mark the source type honestly.
3. **Capture the wording verbatim.** Every value carries the exact published
   phrase it came from ("between 20 kb and 50 kb"), plus the URL, document title,
   page number and section heading.
4. **Flag conflicts rather than choosing silently.** If two official pages
   disagree, record `conflicting` and give both values with both sources.
5. **Never convert or normalise.** Record "50 KB" as published. Do not turn it
   into bytes — the unit is ambiguous and we handle that ourselves.
6. **Per deliverable, not per examination.** A signature limit is not a
   photograph limit. Keep them separate even where the authority states both in
   one sentence.
7. **Date every access.**

## 5. Output contract

Produce **two JSON files** in exactly the shape of the ones inside
`exam-research-2.zip`. Match them field for field — that archive is the
specification, and this section explains it.

### File 1 — `exam_photo_specs_2026.json`

A JSON array. One object per examination:

```json
{
  "exam_name": "CTET September 2026",
  "aliases": ["CTET"],
  "conducting_body": "Central Board of Secondary Education",
  "examination_year": 2026,
  "application_cycle": "September 2026",
  "application_stage": "application",
  "photo_role": "candidate_photograph",
  "jurisdiction": "national",
  "category": "teaching_eligibility",
  "primary_source_id": "SRC-CTET-2026",
  "fields": { "one entry per field path listed below": {} }
}
```

Every field object takes this shape:

```json
"file_size.published_maximum": {
  "status": "verified",
  "value": 100,
  "captured_wording": "100 KB",
  "confidence": 5,
  "source_type": "official_pdf",
  "official_source": true,
  "source_url": "https://example.gov.in/bulletin.pdf",
  "document_title": "Information Bulletin - CTET September 2026",
  "document_identifier": null,
  "page_number": "2, 26",
  "section_name": "Online Uploading of Scanned Images",
  "access_date": "2026-09-10"
}
```

`status` is exactly one of **`verified`**, **`not_found`**, or **`conflicting`**.
A `not_found` field still appears, with `value: null` and a note on where you
looked. For `conflicting`, give both readings and both sources.

**The field paths.** Emit all of them for every examination, using `not_found`
where nothing is published:

- **Size** — `file_size.published_maximum`, `file_size.published_minimum`,
  `file_size.size_unit_as_published`
- **Format** — `formats.allowed_formats`, `formats.preferred_format`,
  `formats.extension_policy`, `formats.colour_space`
- **Dimensions** — `dimensions.mode` (`exact` / `range` / `unspecified`),
  `dimensions.width_px`, `dimensions.height_px`,
  `dimensions.minimum_width_px`, `dimensions.minimum_height_px`,
  `dimensions.maximum_width_px`, `dimensions.maximum_height_px`,
  `dimensions.preferred_width_px`, `dimensions.preferred_height_px`,
  `aspect_ratio`, `permitted_pixel_range`, `dpi`
- **Appearance** — `appearance.spectacles`, `appearance.headwear`,
  `appearance.facial_hair`, `appearance.face_mask`, `appearance.smile`,
  `appearance.monochrome_accepted`, `appearance.recency_maximum_days`,
  `appearance.live_capture_required`, `appearance.attestation_required`,
  `appearance.face_coverage_basis`, `appearance.imprint.policy`,
  `appearance.imprint.fields`, `appearance.imprint.position`
- **Background** — `background.mode`, `background.required_colour`,
  `background.gradient_allowed`, `background.shadows_allowed`,
  `background.instructions`
- **Composition** — `composition.face_coverage_minimum`,
  `composition.face_coverage_target`, `composition.face_coverage_maximum`,
  `composition.frontal_pose`, `composition.face_centred`,
  `composition.eye_visibility`, `composition.ears_visible`,
  `composition.chin_visible`, `composition.complete_hair_visible`
- **Filename** — `filename.mode`, `filename.pattern`,
  `filename.exact_filename`, `filename.extension_required`,
  `filename.allowed_characters`, `filename.case_sensitive`,
  `filename.instructions`

### File 2 — `exam_deliverables_2026.json`

A JSON array, one object per examination, listing **every** file the application
asks for — not only the photograph:

```json
{
  "record_number": 31,
  "exam_name": "CTET September 2026",
  "conducting_body": "Central Board of Secondary Education",
  "application_cycle": "September 2026",
  "application_stage": "application",
  "photo_role": "candidate_photograph",
  "evidence_source_url": "https://example.gov.in/bulletin.pdf",
  "rejection_conditions": ["Applications bearing a photograph older than three months are rejected"],
  "deliverables": [
    {
      "name": "Candidate signature",
      "requirement_status": "Mandatory",
      "submission_method": "file_upload",
      "applicability": "All applicants",
      "specification": "JPG/JPEG, 3-30 KB, signed in black ink on white paper",
      "evidence_status": "Current official CTET bulletin",
      "source_url": "https://example.gov.in/bulletin.pdf",
      "important_note": null,
      "parsed": {
        "file_size_kb": {"minimum": 3, "maximum": 30, "source_wording": "3-30 KB"},
        "formats": {"values": ["jpg", "jpeg"], "source_wording": "JPG/JPEG"}
      }
    }
  ]
}
```

`submission_method` is one of `file_upload`, `live_capture`, `physical_submission`,
`portal_declaration`, or `not_established`. **This one field decides whether we
can serve a deliverable at all**, so do not guess it — `not_established` is a
valid and useful answer.

`rejection_conditions` are the authority's own published statements about what
gets an application rejected, quoted. Attribute each to the deliverable(s) it
names. **Do not record a null-statement** — where no condition is published, give
an empty list rather than a sentence saying none was found.

## 6. Also record, wherever the authority states it

Not blocking, but each one prevents a specific failure on our side:

1. **Whether the authority forbids editing or enhancing the image.** Some
   prohibit it outright. We need to know before we process anything.
2. **Whether a name or date must be printed on the photograph**, and where —
   `appearance.imprint.*`. Some authorities require this and we cannot do it, so
   knowing which lets us say so honestly rather than deliver a rejectable file.
3. **Whether the photograph is captured live through the portal**, in which case
   there is no upload at all. Flag it early; it stops the rest of the work for
   that examination.
4. **Whether the authority defines KB as 1000 or 1024 bytes.** Almost none do —
   capture the wording if any does, since it decides whether a 50 KB ceiling is
   50,000 or 51,200 bytes.
5. **Whether one uploaded image must combine several things** — some ask for a
   single image holding three signatures, or a photograph with a declaration
   written beneath it.
6. **The application window**, so we know how current the rules are.

## 7. Do not

- **Do not research the four SSC examinations** — CGL 2026, CHSL 2025, MTS 2025,
  Constable GD 2025. They photograph the candidate live through the portal, so no
  upload specification exists and none can be found. Section 3 of the worklist.
- **Do not fill a gap with a plausible value**, ever. See rule 1.
- **Do not convert units, normalise formats, or tidy wording.** Verbatim.
- **Do not merge two examinations** that share an authority. RRB NTPC
  Undergraduate and RRB NTPC Graduate are separate records with separate rules.
- **Do not use `exam-research-1.zip` or the batch-02 zip.** Both are superseded.

## 8. What to hand back

1. `exam_photo_specs_2026.json` — one record per examination researched.
2. `exam_deliverables_2026.json` — matching records, same `exam_name` spelling.
3. `coverage.md` — what you resolved, what you could not, and **for each failure,
   where you looked**. A well-documented failure is worth real money to us: it
   stops us paying to look for the same thing twice.
4. A short list of any examination where you concluded **the authority publishes
   no specification at all**. That is a finding, not a gap, and we record it as
   one.

`exam_name` must match between the two files exactly, and must match the
worklist's spelling for anything in workstreams B, C and D, or the records will
not join.
