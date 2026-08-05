# Indian Examination Photograph Specifications - Evidence Report

**Evidence cut-off:** 4 August 2026  
**Scope:** 48 distinct examinations/recruitment streams; 50 records because differing photo roles/stages are separated where material.  
**Primary purpose:** candidate-upload and live-capture photograph output specifications, with provenance and explicit gaps.

> **Do not treat this report as a substitute for the live application portal.** A portal can change after publication. Before submitting, candidates should compare the relevant record with the active portal. This report never upgrades a secondary value into an official rule.

## 1. Method and truthfulness controls

- Every listed field exists in the machine-readable sidecar. A field not located is explicitly `not_found`; it is never silently omitted.
- `official_source: true` means the conducting body’s own site, bulletin, notification, or application portal. `official_source: false` means a secondary or vendor-hosted lead.
- Preferred pixel dimensions are not converted into mandatory exact dimensions. Physical sizes are not converted to pixels unless both the physical size and DPI make a defensible conversion possible; this report makes no such hidden conversions.
- Published unit spelling/capitalization is preserved (`KB`, `kb`, `kB`, `Kb`, `MB`). Both decimal and binary byte interpretations are included in the JSON sidecar, and `unit_ambiguous` remains true unless a source defines the unit.
- Month-based recency limits are represented as 30 days per month only because the supplied research specification explicitly requested conversion. The conversion is labelled as a derivation, not as source wording.
- Secondary values are used only when official material was inaccessible or silent, and are labelled `secondary_only` or `mixed_official_secondary`. Conflicting secondary values remain `conflicting`.

### Evidence tiers

| Tier | Meaning | Operational use |
|---|---|---|
| Current/recent official | Current or most recent official source states the value | Strongest available evidence |
| Prior-cycle official | Official source from an older cycle only | Lead only; recheck the current portal |
| Mixed official/secondary | Some fields official, others secondary | Use official fields; recheck secondary fields |
| Secondary only | No usable official value located | Lead only, not a conducting-body rule |
| Not found | Checked source did not yield the field | Do not invent a default |

## 2. Coverage table - output specification first

| # | Exam / record | Cycle | Stage / photo role | Evidence tier | Dimensions | DPI | File size | Format | Filename |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | UPSC Civil Services Examination 2026 | 2026 | application / candidate_photograph | current_or_recent_official | verified | not_found | verified | verified | verified |
| 2 | UPSC NDA & NA Examination (II) 2026 | 2026 | application / candidate_photograph | current_or_recent_official | verified | not_found | verified | verified | verified |
| 3 | UPSC Combined Defence Services Examination (II) 2026 | 2026 | application / candidate_photograph | current_or_recent_official | verified | not_found | verified | verified | verified |
| 4 | UPSC CAPF (Assistant Commandants) Examination 2026 | 2026 | application / candidate_photograph | current_or_recent_official | verified | not_found | verified | verified | verified |
| 5 | SSC Combined Graduate Level Examination 2026 | 2026 | application / live_capture | current_or_recent_official | verified | not_found | not_found | not_found | not_found |
| 6 | SSC Combined Higher Secondary (10+2) Level Examination 2025 | 2025 | application / live_capture | current_or_recent_official | verified | not_found | not_found | not_found | not_found |
| 7 | SSC Multi-Tasking Staff and Havaldar Examination 2025 | 2025 | application / live_capture | current_or_recent_official | verified | not_found | not_found | not_found | not_found |
| 8 | SSC Constable (GD) Examination 2025 | 2025 | application / live_capture | current_or_recent_official | verified | not_found | not_found | not_found | not_found |
| 9 | IBPS CRP PO/MT-XVI | 2026-27 | application / candidate_photograph | current_or_recent_official | verified | verified | verified | verified | not_found |
| 10 | IBPS CRP Customer Service Associates-XV | 2025-26 | application / candidate_photograph | current_or_recent_official | verified | verified | verified | verified | not_found |
| 11 | IBPS CRP Specialist Officers-XVI | 2026-27 | application / candidate_photograph | current_or_recent_official | verified | verified | verified | verified | not_found |
| 12 | IBPS CRP Regional Rural Banks-XIV | 2025-26 | application / candidate_photograph | current_or_recent_official | verified | verified | verified | verified | not_found |
| 13 | SBI Probationary Officers 2025 | 2025 | application / candidate_photograph | current_or_recent_official | verified | verified | verified | verified | not_found |
| 14 | SBI Junior Associates 2025 | 2025 | application / candidate_photograph | current_or_recent_official | verified | verified | verified | verified | not_found |
| 15 | LIC Assistant Administrative Officers (Generalist) 2025 | 2025 | application / candidate_photograph | current_or_recent_official | verified | verified | verified | verified | not_found |
| 16 | RBI Assistant - Panel Year 2025 | 2025 | application / candidate_photograph | current_or_recent_official | verified | verified | verified | verified | not_found |
| 17 | RBI Officers in Grade B 2026 - prior-cycle official fallback | 2026 | application / candidate_photograph | prior_cycle_official | verified | verified | verified | verified | not_found |
| 18 | NABARD Grade A 2025 | 2025 | application / candidate_photograph | current_or_recent_official | verified | verified | verified | verified | not_found |
| 19 | NIACL Administrative Officers 2025 | 2025 | application / candidate_photograph | current_or_recent_official | verified | verified | verified | verified | not_found |
| 20 | GIC Assistant Manager 2024-25 | 2024-25 | application / candidate_photograph | secondary_only | verified | not_found | verified | verified | not_found |
| 21 | RBI Assistant - Panel Year 2025 (live photograph) | 2025 | application / live_capture | current_or_recent_official | verified | verified | verified | verified | not_found |
| 22 | JEE (Main) 2026 | 2026 | application / candidate_photograph | current_or_recent_official | verified | not_found | verified | verified | not_found |
| 23 | NEET (UG) 2026 | 2026 | application / candidate_photograph | current_or_recent_official | verified | not_found | verified | verified | not_found |
| 24 | CUET (UG) 2026 | 2026 | application / candidate_photograph | current_or_recent_official | verified | not_found | verified | verified | not_found |
| 25 | CUET (PG) 2026 | 2026 | application / candidate_photograph | current_or_recent_official | verified | not_found | verified | verified | not_found |
| 26 | UGC-NET June 2026 | June 2026 | application / candidate_photograph | current_or_recent_official | verified | not_found | verified | verified | not_found |
| 27 | JEE (Advanced) 2026 | 2026 | application / candidate_photograph | current_or_recent_official | verified | not_found | not_found | not_found | not_found |
| 28 | GATE 2026 | 2026 | application / candidate_photograph | current_or_recent_official | verified | not_found | verified | verified | not_found |
| 29 | RRB Level-1 Posts - CEN 08/2024 | CEN 08/2024 | application / candidate_photograph | current_or_recent_official | verified | verified | verified | verified | not_found |
| 30 | RRB NTPC Graduate - CEN 05/2024 | CEN 05/2024 | application / candidate_photograph | current_or_recent_official | verified | verified | verified | verified | not_found |
| 31 | CTET September 2026 | September 2026 | application / candidate_photograph | current_or_recent_official | verified | not_found | verified | verified | not_found |
| 32 | TNPSC Combined Technical Services Examination 2025 | 2025 | application / candidate_photograph | current_or_recent_official | verified | verified | verified | verified | verified |
| 33 | CBSE Classes IX/XI Registration 2025-26 | 2025-26 | application / candidate_photograph | current_or_recent_official | verified | not_found | verified | verified | verified |
| 34 | MPSC General Online Application Photograph Instruction | current portal guide | application / candidate_photograph | current_or_recent_official | verified | not_found | verified | verified | not_found |
| 35 | UPPSC One Time Registration Photograph | current OTR | application / candidate_photograph | current_or_recent_official | verified | not_found | verified | not_found | not_found |
| 36 | BPSC Current Recruitment Photograph Specification | current | application / candidate_photograph | secondary_only | verified | not_found | verified | verified | not_found |
| 37 | RPSC Current Online Application Photograph | current | application / candidate_photograph | mixed_official_secondary | conflicting | not_found | conflicting | verified | not_found |
| 38 | Karnataka PSC Current Recruitment Portal Photograph | current | application / candidate_photograph | secondary_only | verified | not_found | verified | verified | not_found |
| 39 | WBPSC / WBCS Current Online Application Photograph | current | application / candidate_photograph | secondary_only | verified | not_found | verified | verified | not_found |
| 40 | Kerala PSC One Time Registration Photograph | current OTR | application / candidate_photograph | current_or_recent_official | verified | not_found | verified | verified | not_found |
| 41 | APPSC Forest Beat Officer / Assistant Beat Officer 2025 | 2025 | application / candidate_photograph | current_or_recent_official | verified | not_found | not_found | not_found | not_found |
| 42 | Common Admission Test 2025 | 2025 | application / candidate_photograph | secondary_only | verified | not_found | verified | verified | not_found |
| 43 | Management Aptitude Test 2026 | 2026 | application / candidate_photograph | current_or_recent_official | verified | not_found | verified | verified | not_found |
| 44 | MHT-CET 2026 | 2026 | application / candidate_photograph | current_or_recent_official | verified | not_found | verified | not_found | not_found |
| 45 | Karnataka Common Entrance Test 2026 | 2026 | application / candidate_photograph | secondary_only | verified | not_found | verified | verified | not_found |
| 46 | WBJEE 2026 | 2026 | application / candidate_photograph | secondary_only | verified | not_found | verified | verified | not_found |
| 47 | ICAI Examination Portal Photograph (current portal scope) | current | application / candidate_photograph | current_or_recent_official | verified | not_found | verified | verified | verified |
| 48 | ICSI Student Registration / Examination Account Photograph | current | application / candidate_photograph | current_or_recent_official | verified | not_found | conflicting | verified | not_found |
| 49 | Indian Army Agniveer CEE 2025-26 - online upload | 2025-26 | application / candidate_photograph | mixed_official_secondary | verified | not_found | conflicting | verified | not_found |
| 50 | Indian Army Agniveer CEE 2025-26 - rally/document verification | 2025-26 | document_verification / printed_copies | current_or_recent_official | verified | not_found | not_found | not_found | not_found |

**Distinct examination/recruitment identities:** 48. **Dataset records:** 50. The extra records are RBI Assistant live capture and Indian Army rally/document-verification photographs.

## 3. Output-specification snapshot

| Exam / record | Pixel dimensions | Physical / alternate dimension | DPI | Published file size | Formats | Filename | Source status |
|---|---|---|---:|---|---|---|---|
| UPSC Civil Services Examination 2026 | not_found | not_found | not_found | 20-200 KB | JPG | photo | current_or_recent_official |
| UPSC NDA & NA Examination (II) 2026 | not_found | not_found | not_found | 20-200 KB | JPG | photo | current_or_recent_official |
| UPSC Combined Defence Services Examination (II) 2026 | not_found | not_found | not_found | 20-200 KB | JPG | photo | current_or_recent_official |
| UPSC CAPF (Assistant Commandants) Examination 2026 | not_found | not_found | not_found | 20-200 KB | JPG | photo | current_or_recent_official |
| SSC Combined Graduate Level Examination 2026 | not_found | not_found | not_found | not_found | not_found | not_found | current_or_recent_official |
| SSC Combined Higher Secondary (10+2) Level Examination 2025 | not_found | not_found | not_found | not_found | not_found | not_found | current_or_recent_official |
| SSC Multi-Tasking Staff and Havaldar Examination 2025 | not_found | not_found | not_found | not_found | not_found | not_found | current_or_recent_official |
| SSC Constable (GD) Examination 2025 | not_found | not_found | not_found | not_found | not_found | not_found | current_or_recent_official |
| IBPS CRP PO/MT-XVI | 200×230 px preferred | 4.5 cm × 3.5 cm; 200 x 230 pixels (preferred) | 200 | 20-50 kb | JPG, JPEG | not_found | current_or_recent_official |
| IBPS CRP Customer Service Associates-XV | 200×230 px preferred | 4.5 cm × 3.5 cm; 200 x 230 pixels (preferred) | 200 | 20-50 kb | JPG, JPEG | not_found | current_or_recent_official |
| IBPS CRP Specialist Officers-XVI | 200×230 px preferred | 4.5 cm × 3.5 cm; 200 x 230 pixels (preferred) | 200 | 20-50 kb | JPG, JPEG | not_found | current_or_recent_official |
| IBPS CRP Regional Rural Banks-XIV | 200×230 px preferred | 4.5 cm × 3.5 cm; 200 x 230 pixels (preferred) | 200 | 20-50 kb | JPG, JPEG | not_found | current_or_recent_official |
| SBI Probationary Officers 2025 | 200×230 px preferred | 4.5 cm × 3.5 cm; 200 x 230 pixels (preferred) | 200 | 20-50 kb | JPG, JPEG | not_found | current_or_recent_official |
| SBI Junior Associates 2025 | 200×230 px preferred | 4.5 cm × 3.5 cm; 200 x 230 pixels (preferred) | 200 | 20-50 kb | JPG, JPEG | not_found | current_or_recent_official |
| LIC Assistant Administrative Officers (Generalist) 2025 | 200×230 px preferred | 4.5 cm × 3.5 cm; 200 x 230 pixels (preferred) | 200 | 20-50 kb | JPG, JPEG | not_found | current_or_recent_official |
| RBI Assistant - Panel Year 2025 | 200×230 px preferred | 4.5 cm × 3.5 cm; 200 x 230 pixels (preferred) | 200 | 20-50 kb | JPG, JPEG | not_found | current_or_recent_official |
| RBI Officers in Grade B 2026 - prior-cycle official fallback | 200×230 px preferred | 4.5 cm × 3.5 cm; 200 x 230 pixels (preferred) | 200 | 20-50 kb | JPG, JPEG | not_found | prior_cycle_official |
| NABARD Grade A 2025 | 200×230 px preferred | 4.5 cm × 3.5 cm; 200 x 230 pixels (preferred) | 200 | 20-50 kb | JPG, JPEG | not_found | current_or_recent_official |
| NIACL Administrative Officers 2025 | 200×230 px preferred | 4.5 cm × 3.5 cm; 200 x 230 pixels (preferred) | 200 | 20-50 kb | JPG, JPEG | not_found | current_or_recent_official |
| GIC Assistant Manager 2024-25 | 200×230 px preferred | not_found | not_found | 20-50 KB | JPG, JPEG | not_found | secondary_only |
| RBI Assistant - Panel Year 2025 (live photograph) | 240×240 px preferred | not_found | 200 | 20-50 KB | JPG, JPEG | not_found | current_or_recent_official |
| JEE (Main) 2026 | not_found | not_found | not_found | 10-200 kb | JPG, JPEG | not_found | current_or_recent_official |
| NEET (UG) 2026 | not_found | not_found | not_found | 10-200 kb | JPG, JPEG | not_found | current_or_recent_official |
| CUET (UG) 2026 | not_found | not_found | not_found | 10-200 kb | JPG, JPEG | not_found | current_or_recent_official |
| CUET (PG) 2026 | not_found | not_found | not_found | 10-200 kb | JPG, JPEG | not_found | current_or_recent_official |
| UGC-NET June 2026 | not_found | not_found | not_found | 10-200 kb | JPG, JPEG | not_found | current_or_recent_official |
| JEE (Advanced) 2026 | not_found | not_found | not_found | not_found | not_found | not_found | current_or_recent_official |
| GATE 2026 | 200×260 to 530×690 px | 3.5 cm width × 4.5 cm height; 200×260 to 530×690 pixels; aspect ratio 0.66 to 0.89 | not_found | 5-600 kB | JPEG, JPG | not_found | current_or_recent_official |
| RRB Level-1 Posts - CEN 08/2024 | 320×240 px | 35mmX45mm or 320 x 240 pixels | 100 | 50-100 KB | JPEG | not_found | current_or_recent_official |
| RRB NTPC Graduate - CEN 05/2024 | 320×240 px | 35mmX45mm or 320 x 240 pixels | 100 | 20-50 KB | JPEG | not_found | current_or_recent_official |
| CTET September 2026 | not_found | 3.5 cm (width) x 4.5 cm (height) | not_found | 10-100 KB | JPG, JPEG | not_found | current_or_recent_official |
| TNPSC Combined Technical Services Examination 2025 | 130×170 px | 3.5 cm width (130 pixels) × 4.5 cm height (170 pixels); candidate image 3.0 cm (115 pixels), imprint 1.5 cm (55 pixels) | 200 | 20-50 KB | JPG | Photograph.jpg | current_or_recent_official |
| CBSE Classes IX/XI Registration 2025-26 | not_found | not_found | not_found | up to 40 kb | JPG | <candidate_registration_number> | current_or_recent_official |
| MPSC General Online Application Photograph Instruction | not_found | 3.5 cm × 4.5 cm | not_found | up to 50 KB | JPG, JPEG | not_found | current_or_recent_official |
| UPPSC One Time Registration Photograph | not_found | not_found | not_found | up to 50 KB | not_found | not_found | current_or_recent_official |
| BPSC Current Recruitment Photograph Specification | 250×250 px | not_found | not_found | 20-50 KB | JPG | not_found | secondary_only |
| RPSC Current Online Application Photograph | conflicting | not_found | not_found | conflicting | JPG, JPEG | not_found | mixed_official_secondary |
| Karnataka PSC Current Recruitment Portal Photograph | 100×100 to 150×150 px | not_found | not_found | up to 200 KB | JPG, JPEG, PNG | not_found | secondary_only |
| WBPSC / WBCS Current Online Application Photograph | 138×177 px | not_found | not_found | 20-100 KB | JPG | not_found | secondary_only |
| Kerala PSC One Time Registration Photograph | 150×200 px | not_found | not_found | up to 30 Kb | JPG | not_found | current_or_recent_official |
| APPSC Forest Beat Officer / Assistant Beat Officer 2025 | not_found | not_found | not_found | not_found | not_found | not_found | current_or_recent_official |
| Common Admission Test 2025 | 1200×1200 px | not_found | not_found | up to 1 MB | JPEG, JPG | not_found | secondary_only |
| Management Aptitude Test 2026 | not_found | not_found | not_found | 10-50 kb | JPG, JPEG | not_found | current_or_recent_official |
| MHT-CET 2026 | not_found | 2 × 2 inch (50 × 50 mm) | not_found | 100-5 mixed: KB minimum; MB maximum | not_found | not_found | current_or_recent_official |
| Karnataka Common Entrance Test 2026 | not_found | 3.5 × 4.5 cm | not_found | up to 50 KB | JPG, JPEG | not_found | secondary_only |
| WBJEE 2026 | not_found | not_found | not_found | 10-200 KB | JPG, JPEG | not_found | secondary_only |
| ICAI Examination Portal Photograph (current portal scope) | not_found | not_found | not_found | up to 50 KB | JPEG | photo.jpeg | current_or_recent_official |
| ICSI Student Registration / Examination Account Photograph | not_found | not_found | not_found | conflicting | JPG, JPEG, PNG, GIF, BMP, PDF | not_found | current_or_recent_official |
| Indian Army Agniveer CEE 2025-26 - online upload | not_found | not_found | not_found | conflicting | JPG, JPEG | not_found | mixed_official_secondary |
| Indian Army Agniveer CEE 2025-26 - rally/document verification | not_found | not_found | not_found | not_found | not_found | not_found | current_or_recent_official |

## 4. Per-record evidence details

### 1. UPSC Civil Services Examination 2026

- **Body:** Union Public Service Commission
- **Cycle / stage / role:** 2026 / application / candidate_photograph
- **Jurisdiction / category:** India / central_recruitment
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | passport size | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 4 |
| `file_size.published_minimum` | verified | 20 | 20KB | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `file_size.published_maximum` | verified | 200 | 200KB | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `file_size.size_unit_as_published` | verified | "KB" | KB | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `formats.allowed_formats` | verified | ["JPG"] | jpg format | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `formats.preferred_format` | verified | "JPG" | jpg format | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `filename.mode` | verified | "exact" | named photo | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `filename.exact_filename` | verified | "photo" | named photo | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `filename.extension_required` | verified | true | jpg format | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `background.mode` | verified | "exact_colour" | plain white | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `background.required_colour` | verified | "white" | plain white | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `background.shadows_allowed` | verified | false | Shadows on the face or the background should not be there | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `composition.face_coverage_minimum` | verified | 75 | at least 75% | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.face_coverage_basis` | verified | "face_box_area" | area in the photo | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `composition.ears_visible` | verified | true | both ears | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `composition.face_centred` | verified | true | head in the centre | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `composition.frontal_pose` | verified | true | Frontal view | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `composition.eye_visibility` | verified | true | Eyes must be open | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "avoid glare", "condition": "Clear eyeglasses may be worn only without glare; dark/coloured glasses are unacceptable."} | avoid glare | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.smile` | verified | {"policy": "conditional", "source_wording": "no grinning", "condition": "Natural expression required; grinning, frowning and raised eyebrows are prohibited."} | no grinning | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.monochrome_accepted` | verified | false | colour photo | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.imprint.policy` | verified | "prohibited" | NOT to be signed | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.live_capture_required` | verified | true | live photo is mandatory | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `formats.colour_space`, `formats.extension_policy`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.instructions`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_maximum`, `composition.complete_hair_visible`, `composition.chin_visible`, `appearance.headwear`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 2. UPSC NDA & NA Examination (II) 2026

- **Body:** Union Public Service Commission
- **Cycle / stage / role:** 2026 / application / candidate_photograph
- **Jurisdiction / category:** India / defence
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | passport size | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 4 |
| `file_size.published_minimum` | verified | 20 | 20KB | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `file_size.published_maximum` | verified | 200 | 200KB | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `file_size.size_unit_as_published` | verified | "KB" | KB | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `formats.allowed_formats` | verified | ["JPG"] | jpg format | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `formats.preferred_format` | verified | "JPG" | jpg format | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `filename.mode` | verified | "exact" | named photo | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `filename.exact_filename` | verified | "photo" | named photo | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `filename.extension_required` | verified | true | jpg format | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `background.mode` | verified | "exact_colour" | plain white | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `background.required_colour` | verified | "white" | plain white | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `background.shadows_allowed` | verified | false | Shadows on the face or the background should not be there | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `composition.face_coverage_minimum` | verified | 75 | at least 75% | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.face_coverage_basis` | verified | "face_box_area" | area in the photo | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `composition.ears_visible` | verified | true | both ears | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `composition.face_centred` | verified | true | head in the centre | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `composition.frontal_pose` | verified | true | Frontal view | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `composition.eye_visibility` | verified | true | Eyes must be open | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "avoid glare", "condition": "Clear eyeglasses may be worn only without glare; dark/coloured glasses are unacceptable."} | avoid glare | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.smile` | verified | {"policy": "conditional", "source_wording": "no grinning", "condition": "Natural expression required; grinning, frowning and raised eyebrows are prohibited."} | no grinning | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.monochrome_accepted` | verified | false | colour photo | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.imprint.policy` | verified | "prohibited" | NOT to be signed | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.live_capture_required` | verified | true | live photo is mandatory | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `formats.colour_space`, `formats.extension_policy`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.instructions`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_maximum`, `composition.complete_hair_visible`, `composition.chin_visible`, `appearance.headwear`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 3. UPSC Combined Defence Services Examination (II) 2026

- **Body:** Union Public Service Commission
- **Cycle / stage / role:** 2026 / application / candidate_photograph
- **Jurisdiction / category:** India / defence
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | passport size | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 4 |
| `file_size.published_minimum` | verified | 20 | 20KB | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `file_size.published_maximum` | verified | 200 | 200KB | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `file_size.size_unit_as_published` | verified | "KB" | KB | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `formats.allowed_formats` | verified | ["JPG"] | jpg format | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `formats.preferred_format` | verified | "JPG" | jpg format | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `filename.mode` | verified | "exact" | named photo | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `filename.exact_filename` | verified | "photo" | named photo | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `filename.extension_required` | verified | true | jpg format | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `background.mode` | verified | "exact_colour" | plain white | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `background.required_colour` | verified | "white" | plain white | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `background.shadows_allowed` | verified | false | Shadows on the face or the background should not be there | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `composition.face_coverage_minimum` | verified | 75 | at least 75% | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.face_coverage_basis` | verified | "face_box_area" | area in the photo | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `composition.ears_visible` | verified | true | both ears | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `composition.face_centred` | verified | true | head in the centre | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `composition.frontal_pose` | verified | true | Frontal view | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `composition.eye_visibility` | verified | true | Eyes must be open | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "avoid glare", "condition": "Clear eyeglasses may be worn only without glare; dark/coloured glasses are unacceptable."} | avoid glare | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.smile` | verified | {"policy": "conditional", "source_wording": "no grinning", "condition": "Natural expression required; grinning, frowning and raised eyebrows are prohibited."} | no grinning | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.monochrome_accepted` | verified | false | colour photo | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.imprint.policy` | verified | "prohibited" | NOT to be signed | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.live_capture_required` | verified | true | live photo is mandatory | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `formats.colour_space`, `formats.extension_policy`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.instructions`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_maximum`, `composition.complete_hair_visible`, `composition.chin_visible`, `appearance.headwear`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 4. UPSC CAPF (Assistant Commandants) Examination 2026

- **Body:** Union Public Service Commission
- **Cycle / stage / role:** 2026 / application / candidate_photograph
- **Jurisdiction / category:** India / central_recruitment
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | passport size | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 4 |
| `file_size.published_minimum` | verified | 20 | 20KB | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `file_size.published_maximum` | verified | 200 | 200KB | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `file_size.size_unit_as_published` | verified | "KB" | KB | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `formats.allowed_formats` | verified | ["JPG"] | jpg format | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `formats.preferred_format` | verified | "JPG" | jpg format | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `filename.mode` | verified | "exact" | named photo | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `filename.exact_filename` | verified | "photo" | named photo | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `filename.extension_required` | verified | true | jpg format | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `background.mode` | verified | "exact_colour" | plain white | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `background.required_colour` | verified | "white" | plain white | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `background.shadows_allowed` | verified | false | Shadows on the face or the background should not be there | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `composition.face_coverage_minimum` | verified | 75 | at least 75% | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.face_coverage_basis` | verified | "face_box_area" | area in the photo | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `composition.ears_visible` | verified | true | both ears | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `composition.face_centred` | verified | true | head in the centre | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `composition.frontal_pose` | verified | true | Frontal view | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `composition.eye_visibility` | verified | true | Eyes must be open | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "avoid glare", "condition": "Clear eyeglasses may be worn only without glare; dark/coloured glasses are unacceptable."} | avoid glare | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.smile` | verified | {"policy": "conditional", "source_wording": "no grinning", "condition": "Natural expression required; grinning, frowning and raised eyebrows are prohibited."} | no grinning | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.monochrome_accepted` | verified | false | colour photo | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.imprint.policy` | verified | "prohibited" | NOT to be signed | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |
| `appearance.live_capture_required` | verified | true | live photo is mandatory | True | Instructions for Uploading Photo and Signature; p. 2-4; Upload of Latest Passport Size Photograph / Capture of Live Photograph | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `formats.colour_space`, `formats.extension_policy`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.instructions`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_maximum`, `composition.complete_hair_visible`, `composition.chin_visible`, `appearance.headwear`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 5. SSC Combined Graduate Level Examination 2026

- **Body:** Staff Selection Commission
- **Cycle / stage / role:** 2026 / application / live_capture
- **Jurisdiction / category:** India / central_recruitment
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | capture a photograph | True | Notice of Combined Graduate Level Examination, 2026; How to Apply / live photograph | 4 |
| `background.mode` | verified | "plain_background" | plain background | True | Notice of Combined Graduate Level Examination, 2026; How to Apply / live photograph | 5 |
| `background.instructions` | verified | "good light and plain background" | good light and plain background | True | Notice of Combined Graduate Level Examination, 2026; How to Apply / live photograph | 5 |
| `composition.face_centred` | verified | true | fully inside | True | Notice of Combined Graduate Level Examination, 2026; How to Apply / live photograph | 4 |
| `composition.frontal_pose` | verified | true | look straight ahead | True | Notice of Combined Graduate Level Examination, 2026; How to Apply / live photograph | 5 |
| `appearance.spectacles` | verified | {"policy": "prohibited", "source_wording": "glasses/spectacles"} | glasses/spectacles | True | Notice of Combined Graduate Level Examination, 2026; How to Apply / live photograph | 5 |
| `appearance.headwear` | verified | {"policy": "prohibited", "source_wording": "cap"} | cap | True | Notice of Combined Graduate Level Examination, 2026; How to Apply / live photograph | 5 |
| `appearance.face_mask` | verified | {"policy": "prohibited", "source_wording": "mask"} | mask | True | Notice of Combined Graduate Level Examination, 2026; How to Apply / live photograph | 5 |
| `appearance.live_capture_required` | verified | true | capture a photograph | True | Notice of Combined Graduate Level Examination, 2026; How to Apply / live photograph | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `file_size.published_minimum`, `file_size.published_maximum`, `file_size.size_unit_as_published`, `formats.allowed_formats`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.required_colour`, `background.shadows_allowed`, `background.gradient_allowed`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.eye_visibility`, `appearance.smile`, `appearance.facial_hair`, `appearance.monochrome_accepted`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 6. SSC Combined Higher Secondary (10+2) Level Examination 2025

- **Body:** Staff Selection Commission
- **Cycle / stage / role:** 2025 / application / live_capture
- **Jurisdiction / category:** India / central_recruitment
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | capture a photograph | True | Notice of Combined Higher Secondary (10+2) Level Examination, 2025; p. 12; Paragraphs 9.4-9.5 | 4 |
| `background.mode` | verified | "plain_background" | plain background | True | Notice of Combined Higher Secondary (10+2) Level Examination, 2025; p. 12; Paragraphs 9.4-9.5 | 5 |
| `background.instructions` | verified | "good light and plain background" | good light and plain background | True | Notice of Combined Higher Secondary (10+2) Level Examination, 2025; p. 12; Paragraphs 9.4-9.5 | 5 |
| `composition.face_centred` | verified | true | fully inside | True | Notice of Combined Higher Secondary (10+2) Level Examination, 2025; p. 12; Paragraphs 9.4-9.5 | 4 |
| `composition.frontal_pose` | verified | true | look straight ahead | True | Notice of Combined Higher Secondary (10+2) Level Examination, 2025; p. 12; Paragraphs 9.4-9.5 | 5 |
| `appearance.spectacles` | verified | {"policy": "prohibited", "source_wording": "glasses/spectacles"} | glasses/spectacles | True | Notice of Combined Higher Secondary (10+2) Level Examination, 2025; p. 12; Paragraphs 9.4-9.5 | 5 |
| `appearance.headwear` | verified | {"policy": "prohibited", "source_wording": "cap"} | cap | True | Notice of Combined Higher Secondary (10+2) Level Examination, 2025; p. 12; Paragraphs 9.4-9.5 | 5 |
| `appearance.face_mask` | verified | {"policy": "prohibited", "source_wording": "mask"} | mask | True | Notice of Combined Higher Secondary (10+2) Level Examination, 2025; p. 12; Paragraphs 9.4-9.5 | 5 |
| `appearance.live_capture_required` | verified | true | capture a photograph | True | Notice of Combined Higher Secondary (10+2) Level Examination, 2025; p. 12; Paragraphs 9.4-9.5 | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `file_size.published_minimum`, `file_size.published_maximum`, `file_size.size_unit_as_published`, `formats.allowed_formats`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.required_colour`, `background.shadows_allowed`, `background.gradient_allowed`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.eye_visibility`, `appearance.smile`, `appearance.facial_hair`, `appearance.monochrome_accepted`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 7. SSC Multi-Tasking Staff and Havaldar Examination 2025

- **Body:** Staff Selection Commission
- **Cycle / stage / role:** 2025 / application / live_capture
- **Jurisdiction / category:** India / central_recruitment
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | capture a photograph | True | Notice of Multi-Tasking (Non-Technical) Staff and Havaldar Examination, 2025; p. 13; Paragraphs 10.4-10.6 | 4 |
| `background.mode` | verified | "plain_background" | plain background | True | Notice of Multi-Tasking (Non-Technical) Staff and Havaldar Examination, 2025; p. 13; Paragraphs 10.4-10.6 | 5 |
| `background.instructions` | verified | "good light and plain background" | good light and plain background | True | Notice of Multi-Tasking (Non-Technical) Staff and Havaldar Examination, 2025; p. 13; Paragraphs 10.4-10.6 | 5 |
| `composition.face_centred` | verified | true | fully inside | True | Notice of Multi-Tasking (Non-Technical) Staff and Havaldar Examination, 2025; p. 13; Paragraphs 10.4-10.6 | 4 |
| `composition.frontal_pose` | verified | true | look straight ahead | True | Notice of Multi-Tasking (Non-Technical) Staff and Havaldar Examination, 2025; p. 13; Paragraphs 10.4-10.6 | 5 |
| `appearance.spectacles` | verified | {"policy": "prohibited", "source_wording": "glasses/spectacles"} | glasses/spectacles | True | Notice of Multi-Tasking (Non-Technical) Staff and Havaldar Examination, 2025; p. 13; Paragraphs 10.4-10.6 | 5 |
| `appearance.headwear` | verified | {"policy": "prohibited", "source_wording": "cap"} | cap | True | Notice of Multi-Tasking (Non-Technical) Staff and Havaldar Examination, 2025; p. 13; Paragraphs 10.4-10.6 | 5 |
| `appearance.face_mask` | verified | {"policy": "prohibited", "source_wording": "mask"} | mask | True | Notice of Multi-Tasking (Non-Technical) Staff and Havaldar Examination, 2025; p. 13; Paragraphs 10.4-10.6 | 5 |
| `appearance.live_capture_required` | verified | true | capture a photograph | True | Notice of Multi-Tasking (Non-Technical) Staff and Havaldar Examination, 2025; p. 13; Paragraphs 10.4-10.6 | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `file_size.published_minimum`, `file_size.published_maximum`, `file_size.size_unit_as_published`, `formats.allowed_formats`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.required_colour`, `background.shadows_allowed`, `background.gradient_allowed`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.eye_visibility`, `appearance.smile`, `appearance.facial_hair`, `appearance.monochrome_accepted`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 8. SSC Constable (GD) Examination 2025

- **Body:** Staff Selection Commission
- **Cycle / stage / role:** 2025 / application / live_capture
- **Jurisdiction / category:** India / central_recruitment
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | capture a photograph | True | Notice of Constable (GD) Examination, 2025; Online application photograph instructions | 4 |
| `background.mode` | verified | "plain_background" | plain background | True | Notice of Constable (GD) Examination, 2025; Online application photograph instructions | 5 |
| `background.instructions` | verified | "good light and plain background" | good light and plain background | True | Notice of Constable (GD) Examination, 2025; Online application photograph instructions | 5 |
| `composition.face_centred` | verified | true | fully inside | True | Notice of Constable (GD) Examination, 2025; Online application photograph instructions | 4 |
| `composition.frontal_pose` | verified | true | look straight ahead | True | Notice of Constable (GD) Examination, 2025; Online application photograph instructions | 5 |
| `appearance.spectacles` | verified | {"policy": "prohibited", "source_wording": "glasses/spectacles"} | glasses/spectacles | True | Notice of Constable (GD) Examination, 2025; Online application photograph instructions | 5 |
| `appearance.headwear` | verified | {"policy": "prohibited", "source_wording": "cap"} | cap | True | Notice of Constable (GD) Examination, 2025; Online application photograph instructions | 5 |
| `appearance.face_mask` | verified | {"policy": "prohibited", "source_wording": "mask"} | mask | True | Notice of Constable (GD) Examination, 2025; Online application photograph instructions | 5 |
| `appearance.live_capture_required` | verified | true | capture a photograph | True | Notice of Constable (GD) Examination, 2025; Online application photograph instructions | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `file_size.published_minimum`, `file_size.published_maximum`, `file_size.size_unit_as_published`, `formats.allowed_formats`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.required_colour`, `background.shadows_allowed`, `background.gradient_allowed`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.eye_visibility`, `appearance.smile`, `appearance.facial_hair`, `appearance.monochrome_accepted`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 9. IBPS CRP PO/MT-XVI

- **Body:** Institute of Banking Personnel Selection
- **Cycle / stage / role:** 2026-27 / application / candidate_photograph
- **Jurisdiction / category:** India / banking
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | preferred | True | Detailed Notification CRP PO/MT-XVI; Guidelines for scanning and upload of documents | 5 |
| `dimensions.preferred_width_px` | verified | 200 | 200 x 230 pixels | True | Detailed Notification CRP PO/MT-XVI; Guidelines for scanning and upload of documents | 5 |
| `dimensions.preferred_height_px` | verified | 230 | 200 x 230 pixels | True | Detailed Notification CRP PO/MT-XVI; Guidelines for scanning and upload of documents | 5 |
| `dpi` | verified | 200 | minimum of 200 dpi | True | Detailed Notification CRP PO/MT-XVI; Guidelines for scanning and upload of documents | 5 |
| `permitted_pixel_range` | verified | "4.5 cm × 3.5 cm; 200 x 230 pixels (preferred)" | 200 x 230 pixels (preferred) | True | Detailed Notification CRP PO/MT-XVI; Guidelines for scanning and upload of documents | 5 |
| `file_size.published_minimum` | verified | 20 | 20kb | True | Detailed Notification CRP PO/MT-XVI; Guidelines for scanning and upload of documents | 5 |
| `file_size.published_maximum` | verified | 50 | 50 kb | True | Detailed Notification CRP PO/MT-XVI; Guidelines for scanning and upload of documents | 5 |
| `file_size.size_unit_as_published` | verified | "kb" | kb | True | Detailed Notification CRP PO/MT-XVI; Guidelines for scanning and upload of documents | 5 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG or JPEG | True | Detailed Notification CRP PO/MT-XVI; Guidelines for scanning and upload of documents | 5 |
| `background.mode` | verified | "plain_light" | light-coloured, preferably white | True | Detailed Notification CRP PO/MT-XVI; Guidelines for scanning and upload of documents | 5 |
| `background.required_colour` | verified | "preferably white" | preferably white | True | Detailed Notification CRP PO/MT-XVI; Guidelines for scanning and upload of documents | 5 |
| `background.shadows_allowed` | verified | false | no harsh shadows | True | Detailed Notification CRP PO/MT-XVI; Guidelines for scanning and upload of documents | 5 |
| `composition.frontal_pose` | verified | true | Look straight | True | Detailed Notification CRP PO/MT-XVI; Guidelines for scanning and upload of documents | 5 |
| `composition.eye_visibility` | verified | true | eyes are clearly visible | True | Detailed Notification CRP PO/MT-XVI; Guidelines for scanning and upload of documents | 5 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "no reflections", "condition": "Permitted only when reflections are absent and eyes are clearly visible."} | no reflections | True | Detailed Notification CRP PO/MT-XVI; Guidelines for scanning and upload of documents | 5 |
| `appearance.headwear` | verified | {"policy": "conditional", "source_wording": "Religious headwear is allowed", "condition": "Caps/hats/dark glasses are not acceptable; religious headwear is allowed if it does not cover the face."} | Religious headwear is allowed | True | Detailed Notification CRP PO/MT-XVI; Guidelines for scanning and upload of documents | 5 |
| `appearance.monochrome_accepted` | verified | false | colour picture | True | Detailed Notification CRP PO/MT-XVI; Guidelines for scanning and upload of documents | 5 |
| `appearance.live_capture_required` | verified | true | live photograph | True | Detailed Notification CRP PO/MT-XVI; Guidelines for scanning and upload of documents | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `aspect_ratio`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 10. IBPS CRP Customer Service Associates-XV

- **Body:** Institute of Banking Personnel Selection
- **Cycle / stage / role:** 2025-26 / application / candidate_photograph
- **Jurisdiction / category:** India / banking
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | preferred | True | Detailed Notification CRP Customer Service Associates-XV; Guidelines for scanning and upload of documents | 5 |
| `dimensions.preferred_width_px` | verified | 200 | 200 x 230 pixels | True | Detailed Notification CRP Customer Service Associates-XV; Guidelines for scanning and upload of documents | 5 |
| `dimensions.preferred_height_px` | verified | 230 | 200 x 230 pixels | True | Detailed Notification CRP Customer Service Associates-XV; Guidelines for scanning and upload of documents | 5 |
| `dpi` | verified | 200 | minimum of 200 dpi | True | Detailed Notification CRP Customer Service Associates-XV; Guidelines for scanning and upload of documents | 5 |
| `permitted_pixel_range` | verified | "4.5 cm × 3.5 cm; 200 x 230 pixels (preferred)" | 200 x 230 pixels (preferred) | True | Detailed Notification CRP Customer Service Associates-XV; Guidelines for scanning and upload of documents | 5 |
| `file_size.published_minimum` | verified | 20 | 20kb | True | Detailed Notification CRP Customer Service Associates-XV; Guidelines for scanning and upload of documents | 5 |
| `file_size.published_maximum` | verified | 50 | 50 kb | True | Detailed Notification CRP Customer Service Associates-XV; Guidelines for scanning and upload of documents | 5 |
| `file_size.size_unit_as_published` | verified | "kb" | kb | True | Detailed Notification CRP Customer Service Associates-XV; Guidelines for scanning and upload of documents | 5 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG or JPEG | True | Detailed Notification CRP Customer Service Associates-XV; Guidelines for scanning and upload of documents | 5 |
| `background.mode` | verified | "plain_light" | light-coloured, preferably white | True | Detailed Notification CRP Customer Service Associates-XV; Guidelines for scanning and upload of documents | 5 |
| `background.required_colour` | verified | "preferably white" | preferably white | True | Detailed Notification CRP Customer Service Associates-XV; Guidelines for scanning and upload of documents | 5 |
| `background.shadows_allowed` | verified | false | no harsh shadows | True | Detailed Notification CRP Customer Service Associates-XV; Guidelines for scanning and upload of documents | 5 |
| `composition.frontal_pose` | verified | true | Look straight | True | Detailed Notification CRP Customer Service Associates-XV; Guidelines for scanning and upload of documents | 5 |
| `composition.eye_visibility` | verified | true | eyes are clearly visible | True | Detailed Notification CRP Customer Service Associates-XV; Guidelines for scanning and upload of documents | 5 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "no reflections", "condition": "Permitted only when reflections are absent and eyes are clearly visible."} | no reflections | True | Detailed Notification CRP Customer Service Associates-XV; Guidelines for scanning and upload of documents | 5 |
| `appearance.headwear` | verified | {"policy": "conditional", "source_wording": "Religious headwear is allowed", "condition": "Caps/hats/dark glasses are not acceptable; religious headwear is allowed if it does not cover the face."} | Religious headwear is allowed | True | Detailed Notification CRP Customer Service Associates-XV; Guidelines for scanning and upload of documents | 5 |
| `appearance.monochrome_accepted` | verified | false | colour picture | True | Detailed Notification CRP Customer Service Associates-XV; Guidelines for scanning and upload of documents | 5 |
| `appearance.live_capture_required` | verified | true | live photograph | True | Detailed Notification CRP Customer Service Associates-XV; Guidelines for scanning and upload of documents | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `aspect_ratio`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 11. IBPS CRP Specialist Officers-XVI

- **Body:** Institute of Banking Personnel Selection
- **Cycle / stage / role:** 2026-27 / application / candidate_photograph
- **Jurisdiction / category:** India / banking
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | preferred | True | Detailed Notification CRP Specialist Officers-XVI; Guidelines for scanning and upload of documents | 5 |
| `dimensions.preferred_width_px` | verified | 200 | 200 x 230 pixels | True | Detailed Notification CRP Specialist Officers-XVI; Guidelines for scanning and upload of documents | 5 |
| `dimensions.preferred_height_px` | verified | 230 | 200 x 230 pixels | True | Detailed Notification CRP Specialist Officers-XVI; Guidelines for scanning and upload of documents | 5 |
| `dpi` | verified | 200 | minimum of 200 dpi | True | Detailed Notification CRP Specialist Officers-XVI; Guidelines for scanning and upload of documents | 5 |
| `permitted_pixel_range` | verified | "4.5 cm × 3.5 cm; 200 x 230 pixels (preferred)" | 200 x 230 pixels (preferred) | True | Detailed Notification CRP Specialist Officers-XVI; Guidelines for scanning and upload of documents | 5 |
| `file_size.published_minimum` | verified | 20 | 20kb | True | Detailed Notification CRP Specialist Officers-XVI; Guidelines for scanning and upload of documents | 5 |
| `file_size.published_maximum` | verified | 50 | 50 kb | True | Detailed Notification CRP Specialist Officers-XVI; Guidelines for scanning and upload of documents | 5 |
| `file_size.size_unit_as_published` | verified | "kb" | kb | True | Detailed Notification CRP Specialist Officers-XVI; Guidelines for scanning and upload of documents | 5 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG or JPEG | True | Detailed Notification CRP Specialist Officers-XVI; Guidelines for scanning and upload of documents | 5 |
| `background.mode` | verified | "plain_light" | light-coloured, preferably white | True | Detailed Notification CRP Specialist Officers-XVI; Guidelines for scanning and upload of documents | 5 |
| `background.required_colour` | verified | "preferably white" | preferably white | True | Detailed Notification CRP Specialist Officers-XVI; Guidelines for scanning and upload of documents | 5 |
| `background.shadows_allowed` | verified | false | no harsh shadows | True | Detailed Notification CRP Specialist Officers-XVI; Guidelines for scanning and upload of documents | 5 |
| `composition.frontal_pose` | verified | true | Look straight | True | Detailed Notification CRP Specialist Officers-XVI; Guidelines for scanning and upload of documents | 5 |
| `composition.eye_visibility` | verified | true | eyes are clearly visible | True | Detailed Notification CRP Specialist Officers-XVI; Guidelines for scanning and upload of documents | 5 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "no reflections", "condition": "Permitted only when reflections are absent and eyes are clearly visible."} | no reflections | True | Detailed Notification CRP Specialist Officers-XVI; Guidelines for scanning and upload of documents | 5 |
| `appearance.headwear` | verified | {"policy": "conditional", "source_wording": "Religious headwear is allowed", "condition": "Caps/hats/dark glasses are not acceptable; religious headwear is allowed if it does not cover the face."} | Religious headwear is allowed | True | Detailed Notification CRP Specialist Officers-XVI; Guidelines for scanning and upload of documents | 5 |
| `appearance.monochrome_accepted` | verified | false | colour picture | True | Detailed Notification CRP Specialist Officers-XVI; Guidelines for scanning and upload of documents | 5 |
| `appearance.live_capture_required` | verified | true | live photograph | True | Detailed Notification CRP Specialist Officers-XVI; Guidelines for scanning and upload of documents | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `aspect_ratio`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 12. IBPS CRP Regional Rural Banks-XIV

- **Body:** Institute of Banking Personnel Selection
- **Cycle / stage / role:** 2025-26 / application / candidate_photograph
- **Jurisdiction / category:** India / banking
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | preferred | True | CRP Regional Rural Banks-XIV; Guidelines for scanning and upload of documents | 5 |
| `dimensions.preferred_width_px` | verified | 200 | 200 x 230 pixels | True | CRP Regional Rural Banks-XIV; Guidelines for scanning and upload of documents | 5 |
| `dimensions.preferred_height_px` | verified | 230 | 200 x 230 pixels | True | CRP Regional Rural Banks-XIV; Guidelines for scanning and upload of documents | 5 |
| `dpi` | verified | 200 | minimum of 200 dpi | True | CRP Regional Rural Banks-XIV; Guidelines for scanning and upload of documents | 5 |
| `permitted_pixel_range` | verified | "4.5 cm × 3.5 cm; 200 x 230 pixels (preferred)" | 200 x 230 pixels (preferred) | True | CRP Regional Rural Banks-XIV; Guidelines for scanning and upload of documents | 5 |
| `file_size.published_minimum` | verified | 20 | 20kb | True | CRP Regional Rural Banks-XIV; Guidelines for scanning and upload of documents | 5 |
| `file_size.published_maximum` | verified | 50 | 50 kb | True | CRP Regional Rural Banks-XIV; Guidelines for scanning and upload of documents | 5 |
| `file_size.size_unit_as_published` | verified | "kb" | kb | True | CRP Regional Rural Banks-XIV; Guidelines for scanning and upload of documents | 5 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG or JPEG | True | CRP Regional Rural Banks-XIV; Guidelines for scanning and upload of documents | 5 |
| `background.mode` | verified | "plain_light" | light-coloured, preferably white | True | CRP Regional Rural Banks-XIV; Guidelines for scanning and upload of documents | 5 |
| `background.required_colour` | verified | "preferably white" | preferably white | True | CRP Regional Rural Banks-XIV; Guidelines for scanning and upload of documents | 5 |
| `background.shadows_allowed` | verified | false | no harsh shadows | True | CRP Regional Rural Banks-XIV; Guidelines for scanning and upload of documents | 5 |
| `composition.frontal_pose` | verified | true | Look straight | True | CRP Regional Rural Banks-XIV; Guidelines for scanning and upload of documents | 5 |
| `composition.eye_visibility` | verified | true | eyes are clearly visible | True | CRP Regional Rural Banks-XIV; Guidelines for scanning and upload of documents | 5 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "no reflections", "condition": "Permitted only when reflections are absent and eyes are clearly visible."} | no reflections | True | CRP Regional Rural Banks-XIV; Guidelines for scanning and upload of documents | 5 |
| `appearance.headwear` | verified | {"policy": "conditional", "source_wording": "Religious headwear is allowed", "condition": "Caps/hats/dark glasses are not acceptable; religious headwear is allowed if it does not cover the face."} | Religious headwear is allowed | True | CRP Regional Rural Banks-XIV; Guidelines for scanning and upload of documents | 5 |
| `appearance.monochrome_accepted` | verified | false | colour picture | True | CRP Regional Rural Banks-XIV; Guidelines for scanning and upload of documents | 5 |
| `appearance.live_capture_required` | verified | true | live photograph | True | CRP Regional Rural Banks-XIV; Guidelines for scanning and upload of documents | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `aspect_ratio`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 13. SBI Probationary Officers 2025

- **Body:** State Bank of India
- **Cycle / stage / role:** 2025 / application / candidate_photograph
- **Jurisdiction / category:** India / banking
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | preferred | True | Recruitment of Probationary Officers - Detailed Advertisement 2025; p. 14; Guidelines for scanning and upload | 5 |
| `dimensions.preferred_width_px` | verified | 200 | 200 x 230 pixels | True | Recruitment of Probationary Officers - Detailed Advertisement 2025; p. 14; Guidelines for scanning and upload | 5 |
| `dimensions.preferred_height_px` | verified | 230 | 200 x 230 pixels | True | Recruitment of Probationary Officers - Detailed Advertisement 2025; p. 14; Guidelines for scanning and upload | 5 |
| `dpi` | verified | 200 | minimum of 200 dpi | True | Recruitment of Probationary Officers - Detailed Advertisement 2025; p. 14; Guidelines for scanning and upload | 5 |
| `permitted_pixel_range` | verified | "4.5 cm × 3.5 cm; 200 x 230 pixels (preferred)" | 200 x 230 pixels (preferred) | True | Recruitment of Probationary Officers - Detailed Advertisement 2025; p. 14; Guidelines for scanning and upload | 5 |
| `file_size.published_minimum` | verified | 20 | 20kb | True | Recruitment of Probationary Officers - Detailed Advertisement 2025; p. 14; Guidelines for scanning and upload | 5 |
| `file_size.published_maximum` | verified | 50 | 50 kb | True | Recruitment of Probationary Officers - Detailed Advertisement 2025; p. 14; Guidelines for scanning and upload | 5 |
| `file_size.size_unit_as_published` | verified | "kb" | kb | True | Recruitment of Probationary Officers - Detailed Advertisement 2025; p. 14; Guidelines for scanning and upload | 5 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG or JPEG | True | Recruitment of Probationary Officers - Detailed Advertisement 2025; p. 14; Guidelines for scanning and upload | 5 |
| `background.mode` | verified | "plain_light" | light-coloured, preferably white | True | Recruitment of Probationary Officers - Detailed Advertisement 2025; p. 14; Guidelines for scanning and upload | 5 |
| `background.required_colour` | verified | "preferably white" | preferably white | True | Recruitment of Probationary Officers - Detailed Advertisement 2025; p. 14; Guidelines for scanning and upload | 5 |
| `background.shadows_allowed` | verified | false | no harsh shadows | True | Recruitment of Probationary Officers - Detailed Advertisement 2025; p. 14; Guidelines for scanning and upload | 5 |
| `composition.frontal_pose` | verified | true | Look straight | True | Recruitment of Probationary Officers - Detailed Advertisement 2025; p. 14; Guidelines for scanning and upload | 5 |
| `composition.eye_visibility` | verified | true | eyes are clearly visible | True | Recruitment of Probationary Officers - Detailed Advertisement 2025; p. 14; Guidelines for scanning and upload | 5 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "no reflections", "condition": "Permitted only when reflections are absent and eyes are clearly visible."} | no reflections | True | Recruitment of Probationary Officers - Detailed Advertisement 2025; p. 14; Guidelines for scanning and upload | 5 |
| `appearance.headwear` | verified | {"policy": "conditional", "source_wording": "Religious headwear is allowed", "condition": "Caps/hats/dark glasses are not acceptable; religious headwear is allowed if it does not cover the face."} | Religious headwear is allowed | True | Recruitment of Probationary Officers - Detailed Advertisement 2025; p. 14; Guidelines for scanning and upload | 5 |
| `appearance.monochrome_accepted` | verified | false | colour picture | True | Recruitment of Probationary Officers - Detailed Advertisement 2025; p. 14; Guidelines for scanning and upload | 5 |
| `appearance.live_capture_required` | verified | true | live photograph | True | Recruitment of Probationary Officers - Detailed Advertisement 2025; p. 14; Guidelines for scanning and upload | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `aspect_ratio`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 14. SBI Junior Associates 2025

- **Body:** State Bank of India
- **Cycle / stage / role:** 2025 / application / candidate_photograph
- **Jurisdiction / category:** India / banking
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | preferred | True | Recruitment of Junior Associates - Detailed Advertisement 2025; Guidelines for scanning and upload | 5 |
| `dimensions.preferred_width_px` | verified | 200 | 200 x 230 pixels | True | Recruitment of Junior Associates - Detailed Advertisement 2025; Guidelines for scanning and upload | 5 |
| `dimensions.preferred_height_px` | verified | 230 | 200 x 230 pixels | True | Recruitment of Junior Associates - Detailed Advertisement 2025; Guidelines for scanning and upload | 5 |
| `dpi` | verified | 200 | minimum of 200 dpi | True | Recruitment of Junior Associates - Detailed Advertisement 2025; Guidelines for scanning and upload | 5 |
| `permitted_pixel_range` | verified | "4.5 cm × 3.5 cm; 200 x 230 pixels (preferred)" | 200 x 230 pixels (preferred) | True | Recruitment of Junior Associates - Detailed Advertisement 2025; Guidelines for scanning and upload | 5 |
| `file_size.published_minimum` | verified | 20 | 20kb | True | Recruitment of Junior Associates - Detailed Advertisement 2025; Guidelines for scanning and upload | 5 |
| `file_size.published_maximum` | verified | 50 | 50 kb | True | Recruitment of Junior Associates - Detailed Advertisement 2025; Guidelines for scanning and upload | 5 |
| `file_size.size_unit_as_published` | verified | "kb" | kb | True | Recruitment of Junior Associates - Detailed Advertisement 2025; Guidelines for scanning and upload | 5 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG or JPEG | True | Recruitment of Junior Associates - Detailed Advertisement 2025; Guidelines for scanning and upload | 5 |
| `background.mode` | verified | "plain_light" | light-coloured, preferably white | True | Recruitment of Junior Associates - Detailed Advertisement 2025; Guidelines for scanning and upload | 5 |
| `background.required_colour` | verified | "preferably white" | preferably white | True | Recruitment of Junior Associates - Detailed Advertisement 2025; Guidelines for scanning and upload | 5 |
| `background.shadows_allowed` | verified | false | no harsh shadows | True | Recruitment of Junior Associates - Detailed Advertisement 2025; Guidelines for scanning and upload | 5 |
| `composition.frontal_pose` | verified | true | Look straight | True | Recruitment of Junior Associates - Detailed Advertisement 2025; Guidelines for scanning and upload | 5 |
| `composition.eye_visibility` | verified | true | eyes are clearly visible | True | Recruitment of Junior Associates - Detailed Advertisement 2025; Guidelines for scanning and upload | 5 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "no reflections", "condition": "Permitted only when reflections are absent and eyes are clearly visible."} | no reflections | True | Recruitment of Junior Associates - Detailed Advertisement 2025; Guidelines for scanning and upload | 5 |
| `appearance.headwear` | verified | {"policy": "conditional", "source_wording": "Religious headwear is allowed", "condition": "Caps/hats/dark glasses are not acceptable; religious headwear is allowed if it does not cover the face."} | Religious headwear is allowed | True | Recruitment of Junior Associates - Detailed Advertisement 2025; Guidelines for scanning and upload | 5 |
| `appearance.monochrome_accepted` | verified | false | colour picture | True | Recruitment of Junior Associates - Detailed Advertisement 2025; Guidelines for scanning and upload | 5 |
| `appearance.live_capture_required` | verified | true | live photograph | True | Recruitment of Junior Associates - Detailed Advertisement 2025; Guidelines for scanning and upload | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `aspect_ratio`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 15. LIC Assistant Administrative Officers (Generalist) 2025

- **Body:** Life Insurance Corporation of India
- **Cycle / stage / role:** 2025 / application / candidate_photograph
- **Jurisdiction / category:** India / insurance
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | preferred | True | AAO Generalist Notification 2025; p. 9-10; Guidelines for scanning and upload | 5 |
| `dimensions.preferred_width_px` | verified | 200 | 200 x 230 pixels | True | AAO Generalist Notification 2025; p. 9-10; Guidelines for scanning and upload | 5 |
| `dimensions.preferred_height_px` | verified | 230 | 200 x 230 pixels | True | AAO Generalist Notification 2025; p. 9-10; Guidelines for scanning and upload | 5 |
| `dpi` | verified | 200 | minimum of 200 dpi | True | AAO Generalist Notification 2025; p. 9-10; Guidelines for scanning and upload | 5 |
| `permitted_pixel_range` | verified | "4.5 cm × 3.5 cm; 200 x 230 pixels (preferred)" | 200 x 230 pixels (preferred) | True | AAO Generalist Notification 2025; p. 9-10; Guidelines for scanning and upload | 5 |
| `file_size.published_minimum` | verified | 20 | 20kb | True | AAO Generalist Notification 2025; p. 9-10; Guidelines for scanning and upload | 5 |
| `file_size.published_maximum` | verified | 50 | 50 kb | True | AAO Generalist Notification 2025; p. 9-10; Guidelines for scanning and upload | 5 |
| `file_size.size_unit_as_published` | verified | "kb" | kb | True | AAO Generalist Notification 2025; p. 9-10; Guidelines for scanning and upload | 5 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG or JPEG | True | AAO Generalist Notification 2025; p. 9-10; Guidelines for scanning and upload | 5 |
| `background.mode` | verified | "plain_light" | light-coloured, preferably white | True | AAO Generalist Notification 2025; p. 9-10; Guidelines for scanning and upload | 5 |
| `background.required_colour` | verified | "preferably white" | preferably white | True | AAO Generalist Notification 2025; p. 9-10; Guidelines for scanning and upload | 5 |
| `background.shadows_allowed` | verified | false | no harsh shadows | True | AAO Generalist Notification 2025; p. 9-10; Guidelines for scanning and upload | 5 |
| `composition.frontal_pose` | verified | true | Look straight | True | AAO Generalist Notification 2025; p. 9-10; Guidelines for scanning and upload | 5 |
| `composition.eye_visibility` | verified | true | eyes are clearly visible | True | AAO Generalist Notification 2025; p. 9-10; Guidelines for scanning and upload | 5 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "no reflections", "condition": "Permitted only when reflections are absent and eyes are clearly visible."} | no reflections | True | AAO Generalist Notification 2025; p. 9-10; Guidelines for scanning and upload | 5 |
| `appearance.headwear` | verified | {"policy": "conditional", "source_wording": "Religious headwear is allowed", "condition": "Caps/hats/dark glasses are not acceptable; religious headwear is allowed if it does not cover the face."} | Religious headwear is allowed | True | AAO Generalist Notification 2025; p. 9-10; Guidelines for scanning and upload | 5 |
| `appearance.monochrome_accepted` | verified | false | colour picture | True | AAO Generalist Notification 2025; p. 9-10; Guidelines for scanning and upload | 5 |
| `appearance.live_capture_required` | verified | true | live photograph | True | AAO Generalist Notification 2025; p. 9-10; Guidelines for scanning and upload | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `aspect_ratio`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 16. RBI Assistant - Panel Year 2025

- **Body:** Reserve Bank of India
- **Cycle / stage / role:** 2025 / application / candidate_photograph
- **Jurisdiction / category:** India / banking
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | preferred | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `dimensions.preferred_width_px` | verified | 200 | 200 x 230 pixels | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `dimensions.preferred_height_px` | verified | 230 | 200 x 230 pixels | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `dpi` | verified | 200 | minimum of 200 dpi | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `permitted_pixel_range` | verified | "4.5 cm × 3.5 cm; 200 x 230 pixels (preferred)" | 200 x 230 pixels (preferred) | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `file_size.published_minimum` | verified | 20 | 20kb | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `file_size.published_maximum` | verified | 50 | 50 kb | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `file_size.size_unit_as_published` | verified | "kb" | kb | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG or JPEG | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `background.mode` | verified | "plain_light" | light-coloured, preferably white | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `background.required_colour` | verified | "preferably white" | preferably white | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `background.shadows_allowed` | verified | false | no harsh shadows | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `composition.frontal_pose` | verified | true | Look straight | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `composition.eye_visibility` | verified | true | eyes are clearly visible | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "no reflections", "condition": "Permitted only when reflections are absent and eyes are clearly visible."} | no reflections | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `appearance.headwear` | verified | {"policy": "conditional", "source_wording": "Religious headwear is allowed", "condition": "Caps/hats/dark glasses are not acceptable; religious headwear is allowed if it does not cover the face."} | Religious headwear is allowed | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `appearance.monochrome_accepted` | verified | false | colour picture | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `appearance.live_capture_required` | verified | true | live photograph | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `aspect_ratio`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 17. RBI Officers in Grade B 2026 - prior-cycle official fallback

- **Body:** Reserve Bank of India
- **Cycle / stage / role:** 2026 / application / candidate_photograph
- **Jurisdiction / category:** India / banking
- **Evidence tier:** `prior_cycle_official`
- **Scope note:** All positive specifications are from a prior-cycle official RBI source. They are not represented as current-cycle proof.

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | preferred | True | Officers in Grade B - official prior-cycle upload instructions; Guidelines for scanning and upload | 3 |
| `dimensions.preferred_width_px` | verified | 200 | 200 x 230 pixels | True | Officers in Grade B - official prior-cycle upload instructions; Guidelines for scanning and upload | 3 |
| `dimensions.preferred_height_px` | verified | 230 | 200 x 230 pixels | True | Officers in Grade B - official prior-cycle upload instructions; Guidelines for scanning and upload | 3 |
| `dpi` | verified | 200 | minimum of 200 dpi | True | Officers in Grade B - official prior-cycle upload instructions; Guidelines for scanning and upload | 3 |
| `permitted_pixel_range` | verified | "4.5 cm × 3.5 cm; 200 x 230 pixels (preferred)" | 200 x 230 pixels (preferred) | True | Officers in Grade B - official prior-cycle upload instructions; Guidelines for scanning and upload | 3 |
| `file_size.published_minimum` | verified | 20 | 20kb | True | Officers in Grade B - official prior-cycle upload instructions; Guidelines for scanning and upload | 3 |
| `file_size.published_maximum` | verified | 50 | 50 kb | True | Officers in Grade B - official prior-cycle upload instructions; Guidelines for scanning and upload | 3 |
| `file_size.size_unit_as_published` | verified | "kb" | kb | True | Officers in Grade B - official prior-cycle upload instructions; Guidelines for scanning and upload | 3 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG or JPEG | True | Officers in Grade B - official prior-cycle upload instructions; Guidelines for scanning and upload | 3 |
| `background.mode` | verified | "plain_light" | light-coloured, preferably white | True | Officers in Grade B - official prior-cycle upload instructions; Guidelines for scanning and upload | 3 |
| `background.required_colour` | verified | "preferably white" | preferably white | True | Officers in Grade B - official prior-cycle upload instructions; Guidelines for scanning and upload | 3 |
| `background.shadows_allowed` | verified | false | no harsh shadows | True | Officers in Grade B - official prior-cycle upload instructions; Guidelines for scanning and upload | 3 |
| `composition.frontal_pose` | verified | true | Look straight | True | Officers in Grade B - official prior-cycle upload instructions; Guidelines for scanning and upload | 3 |
| `composition.eye_visibility` | verified | true | eyes are clearly visible | True | Officers in Grade B - official prior-cycle upload instructions; Guidelines for scanning and upload | 3 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "no reflections", "condition": "Permitted only when reflections are absent and eyes are clearly visible."} | no reflections | True | Officers in Grade B - official prior-cycle upload instructions; Guidelines for scanning and upload | 3 |
| `appearance.headwear` | verified | {"policy": "conditional", "source_wording": "Religious headwear is allowed", "condition": "Caps/hats/dark glasses are not acceptable; religious headwear is allowed if it does not cover the face."} | Religious headwear is allowed | True | Officers in Grade B - official prior-cycle upload instructions; Guidelines for scanning and upload | 3 |
| `appearance.monochrome_accepted` | verified | false | colour picture | True | Officers in Grade B - official prior-cycle upload instructions; Guidelines for scanning and upload | 3 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `aspect_ratio`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 18. NABARD Grade A 2025

- **Body:** National Bank for Agriculture and Rural Development
- **Cycle / stage / role:** 2025 / application / candidate_photograph
- **Jurisdiction / category:** India / banking
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | preferred | True | Recruitment to Grade A, 2025 - Advertisement; Guidelines for scanning and upload | 4 |
| `dimensions.preferred_width_px` | verified | 200 | 200 x 230 pixels | True | Recruitment to Grade A, 2025 - Advertisement; Guidelines for scanning and upload | 4 |
| `dimensions.preferred_height_px` | verified | 230 | 200 x 230 pixels | True | Recruitment to Grade A, 2025 - Advertisement; Guidelines for scanning and upload | 4 |
| `dpi` | verified | 200 | minimum of 200 dpi | True | Recruitment to Grade A, 2025 - Advertisement; Guidelines for scanning and upload | 4 |
| `permitted_pixel_range` | verified | "4.5 cm × 3.5 cm; 200 x 230 pixels (preferred)" | 200 x 230 pixels (preferred) | True | Recruitment to Grade A, 2025 - Advertisement; Guidelines for scanning and upload | 4 |
| `file_size.published_minimum` | verified | 20 | 20kb | True | Recruitment to Grade A, 2025 - Advertisement; Guidelines for scanning and upload | 4 |
| `file_size.published_maximum` | verified | 50 | 50 kb | True | Recruitment to Grade A, 2025 - Advertisement; Guidelines for scanning and upload | 4 |
| `file_size.size_unit_as_published` | verified | "kb" | kb | True | Recruitment to Grade A, 2025 - Advertisement; Guidelines for scanning and upload | 4 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG or JPEG | True | Recruitment to Grade A, 2025 - Advertisement; Guidelines for scanning and upload | 4 |
| `background.mode` | verified | "plain_light" | light-coloured, preferably white | True | Recruitment to Grade A, 2025 - Advertisement; Guidelines for scanning and upload | 4 |
| `background.required_colour` | verified | "preferably white" | preferably white | True | Recruitment to Grade A, 2025 - Advertisement; Guidelines for scanning and upload | 4 |
| `background.shadows_allowed` | verified | false | no harsh shadows | True | Recruitment to Grade A, 2025 - Advertisement; Guidelines for scanning and upload | 4 |
| `composition.frontal_pose` | verified | true | Look straight | True | Recruitment to Grade A, 2025 - Advertisement; Guidelines for scanning and upload | 4 |
| `composition.eye_visibility` | verified | true | eyes are clearly visible | True | Recruitment to Grade A, 2025 - Advertisement; Guidelines for scanning and upload | 4 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "no reflections", "condition": "Permitted only when reflections are absent and eyes are clearly visible."} | no reflections | True | Recruitment to Grade A, 2025 - Advertisement; Guidelines for scanning and upload | 4 |
| `appearance.headwear` | verified | {"policy": "conditional", "source_wording": "Religious headwear is allowed", "condition": "Caps/hats/dark glasses are not acceptable; religious headwear is allowed if it does not cover the face."} | Religious headwear is allowed | True | Recruitment to Grade A, 2025 - Advertisement; Guidelines for scanning and upload | 4 |
| `appearance.monochrome_accepted` | verified | false | colour picture | True | Recruitment to Grade A, 2025 - Advertisement; Guidelines for scanning and upload | 4 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `aspect_ratio`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 19. NIACL Administrative Officers 2025

- **Body:** The New India Assurance Company Limited
- **Cycle / stage / role:** 2025 / application / candidate_photograph
- **Jurisdiction / category:** India / insurance
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | preferred | True | Recruitment of Administrative Officers 2025; p. 11; Guidelines for scanning and upload | 5 |
| `dimensions.preferred_width_px` | verified | 200 | 200 x 230 pixels | True | Recruitment of Administrative Officers 2025; p. 11; Guidelines for scanning and upload | 5 |
| `dimensions.preferred_height_px` | verified | 230 | 200 x 230 pixels | True | Recruitment of Administrative Officers 2025; p. 11; Guidelines for scanning and upload | 5 |
| `dpi` | verified | 200 | minimum of 200 dpi | True | Recruitment of Administrative Officers 2025; p. 11; Guidelines for scanning and upload | 5 |
| `permitted_pixel_range` | verified | "4.5 cm × 3.5 cm; 200 x 230 pixels (preferred)" | 200 x 230 pixels (preferred) | True | Recruitment of Administrative Officers 2025; p. 11; Guidelines for scanning and upload | 5 |
| `file_size.published_minimum` | verified | 20 | 20kb | True | Recruitment of Administrative Officers 2025; p. 11; Guidelines for scanning and upload | 5 |
| `file_size.published_maximum` | verified | 50 | 50 kb | True | Recruitment of Administrative Officers 2025; p. 11; Guidelines for scanning and upload | 5 |
| `file_size.size_unit_as_published` | verified | "kb" | kb | True | Recruitment of Administrative Officers 2025; p. 11; Guidelines for scanning and upload | 5 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG or JPEG | True | Recruitment of Administrative Officers 2025; p. 11; Guidelines for scanning and upload | 5 |
| `background.mode` | verified | "plain_light" | light-coloured, preferably white | True | Recruitment of Administrative Officers 2025; p. 11; Guidelines for scanning and upload | 5 |
| `background.required_colour` | verified | "preferably white" | preferably white | True | Recruitment of Administrative Officers 2025; p. 11; Guidelines for scanning and upload | 5 |
| `background.shadows_allowed` | verified | false | no harsh shadows | True | Recruitment of Administrative Officers 2025; p. 11; Guidelines for scanning and upload | 5 |
| `composition.frontal_pose` | verified | true | Look straight | True | Recruitment of Administrative Officers 2025; p. 11; Guidelines for scanning and upload | 5 |
| `composition.eye_visibility` | verified | true | eyes are clearly visible | True | Recruitment of Administrative Officers 2025; p. 11; Guidelines for scanning and upload | 5 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "no reflections", "condition": "Permitted only when reflections are absent and eyes are clearly visible."} | no reflections | True | Recruitment of Administrative Officers 2025; p. 11; Guidelines for scanning and upload | 5 |
| `appearance.headwear` | verified | {"policy": "conditional", "source_wording": "Religious headwear is allowed", "condition": "Caps/hats/dark glasses are not acceptable; religious headwear is allowed if it does not cover the face."} | Religious headwear is allowed | True | Recruitment of Administrative Officers 2025; p. 11; Guidelines for scanning and upload | 5 |
| `appearance.monochrome_accepted` | verified | false | colour picture | True | Recruitment of Administrative Officers 2025; p. 11; Guidelines for scanning and upload | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `aspect_ratio`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 20. GIC Assistant Manager 2024-25

- **Body:** General Insurance Corporation of India
- **Cycle / stage / role:** 2024-25 / application / candidate_photograph
- **Jurisdiction / category:** India / insurance
- **Evidence tier:** `secondary_only`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | preferred | False | GIC Assistant Manager photo specification reproduction | 2 |
| `dimensions.preferred_width_px` | verified | 200 | 200 x 230 pixels | False | GIC Assistant Manager photo specification reproduction | 2 |
| `dimensions.preferred_height_px` | verified | 230 | 200 x 230 pixels | False | GIC Assistant Manager photo specification reproduction | 2 |
| `file_size.published_minimum` | verified | 20 | 20 KB | False | GIC Assistant Manager photo specification reproduction | 2 |
| `file_size.published_maximum` | verified | 50 | 50 KB | False | GIC Assistant Manager photo specification reproduction | 2 |
| `file_size.size_unit_as_published` | verified | "KB" | KB | False | GIC Assistant Manager photo specification reproduction | 2 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG/JPEG | False | GIC Assistant Manager photo specification reproduction | 2 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.mode`, `background.required_colour`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.monochrome_accepted`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 21. RBI Assistant - Panel Year 2025 (live photograph)

- **Body:** Reserve Bank of India
- **Cycle / stage / role:** 2025 / application / live_capture
- **Jurisdiction / category:** India / banking
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | preferred | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `dimensions.preferred_width_px` | verified | 240 | 240 x 240 pixels | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `dimensions.preferred_height_px` | verified | 240 | 240 x 240 pixels | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `dpi` | verified | 200 | 200 DPI | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `file_size.published_minimum` | verified | 20 | 20 KB | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `file_size.published_maximum` | verified | 50 | 50 KB | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `file_size.size_unit_as_published` | verified | "KB" | KB | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | jpg / jpeg | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |
| `appearance.live_capture_required` | verified | true | live photograph | True | Recruitment for the Post of Assistant - Panel Year 2025; Paragraph 9.6 / upload instructions | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `aspect_ratio`, `permitted_pixel_range`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.mode`, `background.required_colour`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.monochrome_accepted`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 22. JEE (Main) 2026

- **Body:** National Testing Agency
- **Cycle / stage / role:** 2026 / application / candidate_photograph
- **Jurisdiction / category:** India / entrance
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | passport size | True | Information Bulletin - JEE (Main) 2026; p. 10; Application Procedure | 5 |
| `file_size.published_minimum` | verified | 10 | 10 kb | True | Information Bulletin - JEE (Main) 2026; p. 10; Application Procedure | 5 |
| `file_size.published_maximum` | verified | 200 | 200 kb | True | Information Bulletin - JEE (Main) 2026; p. 10; Application Procedure | 5 |
| `file_size.size_unit_as_published` | verified | "kb" | kb | True | Information Bulletin - JEE (Main) 2026; p. 10; Application Procedure | 5 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG/JPEG | True | Information Bulletin - JEE (Main) 2026; p. 10; Application Procedure | 5 |
| `background.mode` | verified | "exact_colour" | white background | True | Information Bulletin - JEE (Main) 2026; p. 10; Application Procedure | 5 |
| `background.required_colour` | verified | "white" | white background | True | Information Bulletin - JEE (Main) 2026; p. 10; Application Procedure | 5 |
| `composition.face_coverage_target` | verified | 80 | 80% face | True | Information Bulletin - JEE (Main) 2026; p. 10; Application Procedure | 5 |
| `appearance.face_coverage_basis` | verified | "unspecified" | 80% face | True | Information Bulletin - JEE (Main) 2026; p. 10; Application Procedure | 4 |
| `composition.ears_visible` | verified | true | including ears | True | Information Bulletin - JEE (Main) 2026; p. 10; Application Procedure | 5 |
| `appearance.face_mask` | verified | {"policy": "prohibited", "source_wording": "without mask"} | without mask | True | Information Bulletin - JEE (Main) 2026; p. 10; Application Procedure | 5 |
| `appearance.monochrome_accepted` | verified | false | colour | True | Information Bulletin - JEE (Main) 2026; p. 10; Application Procedure | 5 |
| `appearance.live_capture_required` | verified | true | live photograph | True | Information Bulletin - JEE (Main) 2026; p. 10; Application Procedure | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `composition.complete_hair_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 23. NEET (UG) 2026

- **Body:** National Testing Agency
- **Cycle / stage / role:** 2026 / application / candidate_photograph
- **Jurisdiction / category:** India / entrance
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | passport size | True | Information Bulletin - NEET (UG) 2026; p. 17; Upload of photograph | 5 |
| `file_size.published_minimum` | verified | 10 | 10 kb | True | Information Bulletin - NEET (UG) 2026; p. 17; Upload of photograph | 5 |
| `file_size.published_maximum` | verified | 200 | 200 kb | True | Information Bulletin - NEET (UG) 2026; p. 17; Upload of photograph | 5 |
| `file_size.size_unit_as_published` | verified | "kb" | kb | True | Information Bulletin - NEET (UG) 2026; p. 17; Upload of photograph | 5 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG/JPEG | True | Information Bulletin - NEET (UG) 2026; p. 17; Upload of photograph | 5 |
| `background.mode` | verified | "exact_colour" | white background | True | Information Bulletin - NEET (UG) 2026; p. 17; Upload of photograph | 5 |
| `background.required_colour` | verified | "white" | white background | True | Information Bulletin - NEET (UG) 2026; p. 17; Upload of photograph | 5 |
| `composition.face_coverage_target` | verified | 80 | 80% face | True | Information Bulletin - NEET (UG) 2026; p. 17; Upload of photograph | 5 |
| `appearance.face_coverage_basis` | verified | "unspecified" | 80% face | True | Information Bulletin - NEET (UG) 2026; p. 17; Upload of photograph | 4 |
| `composition.ears_visible` | verified | true | including ears | True | Information Bulletin - NEET (UG) 2026; p. 17; Upload of photograph | 5 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "spectacles only if used regularly", "condition": "Permitted only if spectacles are used regularly."} | spectacles only if used regularly | True | Information Bulletin - NEET (UG) 2026; p. 17; Upload of photograph | 5 |
| `appearance.face_mask` | verified | {"policy": "prohibited", "source_wording": "without mask"} | without mask | True | Information Bulletin - NEET (UG) 2026; p. 17; Upload of photograph | 5 |
| `appearance.monochrome_accepted` | verified | true | colour or black & white | True | Information Bulletin - NEET (UG) 2026; p. 17; Upload of photograph | 5 |
| `appearance.live_capture_required` | verified | true | live photograph | True | Information Bulletin - NEET (UG) 2026; p. 17; Upload of photograph | 5 |
| `appearance.attestation_required` | verified | false | need not be attested | True | Information Bulletin - NEET (UG) 2026; p. 17; Upload of photograph | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `composition.complete_hair_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.recency_maximum_days`.

### 24. CUET (UG) 2026

- **Body:** National Testing Agency
- **Cycle / stage / role:** 2026 / application / candidate_photograph
- **Jurisdiction / category:** India / entrance
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | passport size | True | Information Bulletin - CUET (UG) 2026; p. 9; Application Procedure | 5 |
| `file_size.published_minimum` | verified | 10 | 10 kb | True | Information Bulletin - CUET (UG) 2026; p. 9; Application Procedure | 5 |
| `file_size.published_maximum` | verified | 200 | 200 kb | True | Information Bulletin - CUET (UG) 2026; p. 9; Application Procedure | 5 |
| `file_size.size_unit_as_published` | verified | "kb" | kb | True | Information Bulletin - CUET (UG) 2026; p. 9; Application Procedure | 5 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG/JPEG | True | Information Bulletin - CUET (UG) 2026; p. 9; Application Procedure | 5 |
| `background.mode` | verified | "exact_colour" | white background | True | Information Bulletin - CUET (UG) 2026; p. 9; Application Procedure | 5 |
| `background.required_colour` | verified | "white" | white background | True | Information Bulletin - CUET (UG) 2026; p. 9; Application Procedure | 5 |
| `composition.face_coverage_target` | verified | 80 | 80% face | True | Information Bulletin - CUET (UG) 2026; p. 9; Application Procedure | 5 |
| `appearance.face_coverage_basis` | verified | "unspecified" | 80% face | True | Information Bulletin - CUET (UG) 2026; p. 9; Application Procedure | 4 |
| `composition.ears_visible` | verified | true | including ears | True | Information Bulletin - CUET (UG) 2026; p. 9; Application Procedure | 5 |
| `appearance.face_mask` | verified | {"policy": "prohibited", "source_wording": "without mask"} | without mask | True | Information Bulletin - CUET (UG) 2026; p. 9; Application Procedure | 5 |
| `appearance.monochrome_accepted` | verified | false | colour | True | Information Bulletin - CUET (UG) 2026; p. 9; Application Procedure | 5 |
| `appearance.live_capture_required` | verified | true | live photograph | True | Information Bulletin - CUET (UG) 2026; p. 9; Application Procedure | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `composition.complete_hair_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 25. CUET (PG) 2026

- **Body:** National Testing Agency
- **Cycle / stage / role:** 2026 / application / candidate_photograph
- **Jurisdiction / category:** India / entrance
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | passport size | True | Information Bulletin - CUET (PG) 2026; p. 5-6; Application Procedure | 5 |
| `file_size.published_minimum` | verified | 10 | 10 kb | True | Information Bulletin - CUET (PG) 2026; p. 5-6; Application Procedure | 5 |
| `file_size.published_maximum` | verified | 200 | 200 kb | True | Information Bulletin - CUET (PG) 2026; p. 5-6; Application Procedure | 5 |
| `file_size.size_unit_as_published` | verified | "kb" | kb | True | Information Bulletin - CUET (PG) 2026; p. 5-6; Application Procedure | 5 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG/JPEG | True | Information Bulletin - CUET (PG) 2026; p. 5-6; Application Procedure | 5 |
| `background.mode` | verified | "exact_colour" | white background | True | Information Bulletin - CUET (PG) 2026; p. 5-6; Application Procedure | 5 |
| `background.required_colour` | verified | "white" | white background | True | Information Bulletin - CUET (PG) 2026; p. 5-6; Application Procedure | 5 |
| `composition.face_coverage_target` | verified | 80 | 80% face | True | Information Bulletin - CUET (PG) 2026; p. 5-6; Application Procedure | 5 |
| `appearance.face_coverage_basis` | verified | "unspecified" | 80% face | True | Information Bulletin - CUET (PG) 2026; p. 5-6; Application Procedure | 4 |
| `composition.ears_visible` | verified | true | including ears | True | Information Bulletin - CUET (PG) 2026; p. 5-6; Application Procedure | 5 |
| `appearance.face_mask` | verified | {"policy": "prohibited", "source_wording": "without mask"} | without mask | True | Information Bulletin - CUET (PG) 2026; p. 5-6; Application Procedure | 5 |
| `appearance.monochrome_accepted` | verified | true | colour or black & white | True | Information Bulletin - CUET (PG) 2026; p. 5-6; Application Procedure | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `composition.complete_hair_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 26. UGC-NET June 2026

- **Body:** National Testing Agency
- **Cycle / stage / role:** June 2026 / application / candidate_photograph
- **Jurisdiction / category:** India / teaching_eligibility
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | passport size | True | Information Bulletin - UGC-NET June 2026; p. 28; Photograph provisions | 5 |
| `file_size.published_minimum` | verified | 10 | 10 kb | True | Information Bulletin - UGC-NET June 2026; p. 28; Photograph provisions | 5 |
| `file_size.published_maximum` | verified | 200 | 200 kb | True | Information Bulletin - UGC-NET June 2026; p. 28; Photograph provisions | 5 |
| `file_size.size_unit_as_published` | verified | "kb" | kb | True | Information Bulletin - UGC-NET June 2026; p. 28; Photograph provisions | 5 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG/JPEG | True | Information Bulletin - UGC-NET June 2026; p. 28; Photograph provisions | 5 |
| `background.mode` | verified | "exact_colour" | white background | True | Information Bulletin - UGC-NET June 2026; p. 28; Photograph provisions | 5 |
| `background.required_colour` | verified | "white" | white background | True | Information Bulletin - UGC-NET June 2026; p. 28; Photograph provisions | 5 |
| `composition.face_coverage_target` | verified | 80 | 80% face | True | Information Bulletin - UGC-NET June 2026; p. 28; Photograph provisions | 5 |
| `appearance.face_coverage_basis` | verified | "unspecified" | 80% face | True | Information Bulletin - UGC-NET June 2026; p. 28; Photograph provisions | 4 |
| `composition.ears_visible` | verified | true | including ears | True | Information Bulletin - UGC-NET June 2026; p. 28; Photograph provisions | 5 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "spectacles only if used regularly", "condition": "Permitted only if spectacles are used regularly."} | spectacles only if used regularly | True | Information Bulletin - UGC-NET June 2026; p. 28; Photograph provisions | 5 |
| `appearance.face_mask` | verified | {"policy": "prohibited", "source_wording": "without mask"} | without mask | True | Information Bulletin - UGC-NET June 2026; p. 28; Photograph provisions | 5 |
| `appearance.monochrome_accepted` | verified | true | colour or black & white | True | Information Bulletin - UGC-NET June 2026; p. 28; Photograph provisions | 5 |
| `appearance.attestation_required` | verified | false | need not be attested | True | Information Bulletin - UGC-NET June 2026; p. 28; Photograph provisions | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `composition.complete_hair_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`.

### 27. JEE (Advanced) 2026

- **Body:** Joint Admission Board / IIT Roorkee
- **Cycle / stage / role:** 2026 / application / candidate_photograph
- **Jurisdiction / category:** India / entrance
- **Evidence tier:** `current_or_recent_official`
- **Scope note:** The current brochure contained an attested passport photograph requirement in forms, but no candidate-facing pixel/file-size specification for the main online photograph was located.

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | passport size | True | Information Brochure - JEE (Advanced) 2026; Application / forms | 3 |
| `appearance.attestation_required` | verified | true | attested photograph | True | Information Brochure - JEE (Advanced) 2026; Application / forms | 3 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `file_size.published_minimum`, `file_size.published_maximum`, `file_size.size_unit_as_published`, `formats.allowed_formats`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.mode`, `background.required_colour`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.monochrome_accepted`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`.

### 28. GATE 2026

- **Body:** IIT Guwahati
- **Cycle / stage / role:** 2026 / application / candidate_photograph
- **Jurisdiction / category:** India / entrance
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "range" | minimum resolution is 200×260 pixels | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 5 |
| `dimensions.minimum_width_px` | verified | 200 | 200×260 pixels | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 5 |
| `dimensions.maximum_width_px` | verified | 530 | 530×690 pixels | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 5 |
| `dimensions.minimum_height_px` | verified | 260 | 200×260 pixels | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 5 |
| `dimensions.maximum_height_px` | verified | 690 | 530×690 pixels | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 5 |
| `permitted_pixel_range` | verified | "3.5 cm width × 4.5 cm height; 200×260 to 530×690 pixels; aspect ratio 0.66 to 0.89" | aspect ratio of the face must be between 0.66 and 0.89 | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 5 |
| `file_size.published_minimum` | verified | 5 | 5 kB | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 5 |
| `file_size.published_maximum` | verified | 600 | 600 kB | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 5 |
| `file_size.size_unit_as_published` | verified | "kB" | kB | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 5 |
| `formats.allowed_formats` | verified | ["JPEG", "JPG"] | JPEG/JPG | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 5 |
| `background.mode` | verified | "exact_colour" | white | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 5 |
| `background.required_colour` | verified | "white" | white | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 5 |
| `composition.face_coverage_minimum` | verified | 60 | 60-70% | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 5 |
| `composition.face_coverage_maximum` | verified | 70 | 60-70% | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 5 |
| `appearance.face_coverage_basis` | verified | "unspecified" | 60-70% | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 4 |
| `composition.chin_visible` | verified | true | chin | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 5 |
| `composition.frontal_pose` | verified | true | frontal face view | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 5 |
| `composition.eye_visibility` | verified | true | eyes | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 5 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "Normal spectacles are allowed", "condition": "Normal vision-correction spectacles are allowed only without glare."} | Normal spectacles are allowed | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 5 |
| `appearance.headwear` | verified | {"policy": "conditional", "source_wording": "except for religious reasons", "condition": "Prohibited except for religious reasons; full facial features and both face edges must remain visible."} | except for religious reasons | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 5 |
| `appearance.face_mask` | verified | {"policy": "prohibited", "source_wording": "Face covered by a mask"} | Face covered by a mask | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 5 |
| `appearance.monochrome_accepted` | verified | false | color photograph | True | GATE 2026 Information Brochure; p. 18-20; 6.7 Photograph and Signature Requirements | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.face_centred`, `appearance.smile`, `appearance.facial_hair`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 29. RRB Level-1 Posts - CEN 08/2024

- **Body:** Railway Recruitment Boards
- **Cycle / stage / role:** CEN 08/2024 / application / candidate_photograph
- **Jurisdiction / category:** India / railways
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "exact" | 320 x 240 pixels | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 5 |
| `dimensions.width_px` | verified | 320 | 320 x 240 pixels | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 5 |
| `dimensions.height_px` | verified | 240 | 320 x 240 pixels | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 5 |
| `dpi` | verified | 100 | minimum 100 DPI | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 5 |
| `permitted_pixel_range` | verified | "35mmX45mm or 320 x 240 pixels" | 35mmX45mm or 320 x 240 pixels | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 5 |
| `file_size.published_minimum` | verified | 50 | 50 | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 5 |
| `file_size.published_maximum` | verified | 100 | 100 | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 5 |
| `file_size.size_unit_as_published` | verified | "KB" | KB | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 5 |
| `formats.allowed_formats` | verified | ["JPEG"] | JPEG | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 5 |
| `background.mode` | verified | "plain_light" | white/light colour background | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 5 |
| `background.required_colour` | verified | "white or light colour" | white/light colour | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 5 |
| `composition.face_coverage_minimum` | verified | 50 | at least 50% | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 5 |
| `appearance.face_coverage_basis` | verified | "face_box_area" | area of the photograph | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 5 |
| `composition.chin_visible` | verified | true | chin | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 5 |
| `composition.frontal_pose` | verified | true | full-face view | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 5 |
| `composition.eye_visibility` | verified | true | Eyes should be clearly open | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 5 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "no glare/reflections", "condition": "Permitted only without glare/reflections and with eyes clearly visible."} | no glare/reflections | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 5 |
| `appearance.headwear` | verified | {"policy": "prohibited", "source_wording": "without cap"} | without cap | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 5 |
| `appearance.smile` | verified | {"policy": "conditional", "source_wording": "no grinning", "condition": "Natural expression; no grinning, frowning or raised eyebrows."} | no grinning | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 5 |
| `appearance.monochrome_accepted` | verified | false | Colour Passport Photograph | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 5 |
| `appearance.imprint.policy` | verified | "prohibited" | free from signature/name/dates | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 5 |
| `appearance.recency_maximum_days` | verified | 60 | must not be older than two months | True | CEN No. 08/2024 - Level 1 Posts; p. 25-26; Mandatory scanned documents | 4 |

**Fields not found in the checked source(s):** `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `aspect_ratio`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_maximum`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.face_centred`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.attestation_required`.

### 30. RRB NTPC Graduate - CEN 05/2024

- **Body:** Railway Recruitment Boards
- **Cycle / stage / role:** CEN 05/2024 / application / candidate_photograph
- **Jurisdiction / category:** India / railways
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "exact" | 320 x 240 pixels | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 5 |
| `dimensions.width_px` | verified | 320 | 320 x 240 pixels | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 5 |
| `dimensions.height_px` | verified | 240 | 320 x 240 pixels | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 5 |
| `dpi` | verified | 100 | minimum 100 DPI | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 5 |
| `permitted_pixel_range` | verified | "35mmX45mm or 320 x 240 pixels" | 35mmX45mm or 320 x 240 pixels | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 5 |
| `file_size.published_minimum` | verified | 20 | 20 | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 5 |
| `file_size.published_maximum` | verified | 50 | 50 | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 5 |
| `file_size.size_unit_as_published` | verified | "KB" | KB | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 5 |
| `formats.allowed_formats` | verified | ["JPEG"] | JPEG | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 5 |
| `background.mode` | verified | "plain_light" | white/light colour background | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 5 |
| `background.required_colour` | verified | "white or light colour" | white/light colour | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 5 |
| `composition.face_coverage_minimum` | verified | 50 | at least 50% | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 5 |
| `appearance.face_coverage_basis` | verified | "face_box_area" | area of the photograph | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 5 |
| `composition.chin_visible` | verified | true | chin | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 5 |
| `composition.frontal_pose` | verified | true | full-face view | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 5 |
| `composition.eye_visibility` | verified | true | Eyes should be clearly open | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 5 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "no glare/reflections", "condition": "Permitted only without glare/reflections and with eyes clearly visible."} | no glare/reflections | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 5 |
| `appearance.headwear` | verified | {"policy": "prohibited", "source_wording": "without cap"} | without cap | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 5 |
| `appearance.smile` | verified | {"policy": "conditional", "source_wording": "no grinning", "condition": "Natural expression; no grinning, frowning or raised eyebrows."} | no grinning | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 5 |
| `appearance.monochrome_accepted` | verified | false | Colour Passport Photograph | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 5 |
| `appearance.imprint.policy` | verified | "prohibited" | free from signature/name/dates | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 5 |
| `appearance.recency_maximum_days` | verified | 60 | must not be older than two months | True | CEN 05/2024 - NTPC Graduate; Mandatory scanned documents | 4 |

**Fields not found in the checked source(s):** `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `aspect_ratio`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_maximum`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.face_centred`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.attestation_required`.

### 31. CTET September 2026

- **Body:** Central Board of Secondary Education
- **Cycle / stage / role:** September 2026 / application / candidate_photograph
- **Jurisdiction / category:** India / teaching_eligibility
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | 3.5 cm (width) x 4.5 cm (height) | True | Information Bulletin - CTET September 2026; p. 2, 26; Online Uploading of Scanned Images | 5 |
| `permitted_pixel_range` | verified | "3.5 cm (width) x 4.5 cm (height)" | 3.5 cm (width) x 4.5 cm (height) | True | Information Bulletin - CTET September 2026; p. 2, 26; Online Uploading of Scanned Images | 5 |
| `file_size.published_minimum` | verified | 10 | 10 | True | Information Bulletin - CTET September 2026; p. 2, 26; Online Uploading of Scanned Images | 5 |
| `file_size.published_maximum` | verified | 100 | 100 | True | Information Bulletin - CTET September 2026; p. 2, 26; Online Uploading of Scanned Images | 5 |
| `file_size.size_unit_as_published` | verified | "KB" | KB | True | Information Bulletin - CTET September 2026; p. 2, 26; Online Uploading of Scanned Images | 5 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG/JPEG | True | Information Bulletin - CTET September 2026; p. 2, 26; Online Uploading of Scanned Images | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.mode`, `background.required_colour`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.monochrome_accepted`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 32. TNPSC Combined Technical Services Examination 2025

- **Body:** Tamil Nadu Public Service Commission
- **Cycle / stage / role:** 2025 / application / candidate_photograph
- **Jurisdiction / category:** Tamil Nadu / state_psc
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "exact" | 130 pixels width and 170 pixels height | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 5 |
| `dimensions.width_px` | verified | 130 | 130 pixels | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 5 |
| `dimensions.height_px` | verified | 170 | 170 pixels | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 5 |
| `dpi` | verified | 200 | 200 DPI | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 5 |
| `permitted_pixel_range` | verified | "3.5 cm width (130 pixels) × 4.5 cm height (170 pixels); candidate image 3.0 cm (115 pixels), imprint 1.5 cm (55 pixels)" | 130 pixels width and 170 pixels height | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 5 |
| `file_size.published_minimum` | verified | 20 | 20 KB | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 5 |
| `file_size.published_maximum` | verified | 50 | 50 KB | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 5 |
| `file_size.size_unit_as_published` | verified | "KB" | KB | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 5 |
| `formats.allowed_formats` | verified | ["JPG"] | Photograph.jpg | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 5 |
| `filename.mode` | verified | "exact" | Photograph.jpg | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 5 |
| `filename.exact_filename` | verified | "Photograph.jpg" | Photograph.jpg | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 5 |
| `filename.case_sensitive` | verified | true | Photograph.jpg | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 4 |
| `filename.extension_required` | verified | true | Photograph.jpg | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 5 |
| `background.mode` | verified | "exact_colour" | white background | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 5 |
| `background.required_colour` | verified | "white" | white background | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 5 |
| `composition.face_coverage_target` | verified | `not_found` | 115 pixels | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 4 |
| `composition.ears_visible` | verified | true | both ears | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 5 |
| `composition.frontal_pose` | verified | true | frontal view | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 5 |
| `appearance.imprint.policy` | verified | "required" | name of the applicant and the date | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 5 |
| `appearance.imprint.fields` | verified | ["candidate_name", "photograph_date"] | name of the applicant and the date | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 5 |
| `appearance.imprint.position` | verified | "bottom" | bottom | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 5 |
| `appearance.recency_maximum_days` | verified | 90 | last 3 months | True | Instructions to Candidates / Combined Technical Services 2025; p. 14; Photograph upload instructions | 4 |

**Fields not found in the checked source(s):** `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `aspect_ratio`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.pattern`, `filename.allowed_characters`, `filename.instructions`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.monochrome_accepted`, `appearance.live_capture_required`, `appearance.attestation_required`.

### 33. CBSE Classes IX/XI Registration 2025-26

- **Body:** Central Board of Secondary Education
- **Cycle / stage / role:** 2025-26 / application / candidate_photograph
- **Jurisdiction / category:** India / board_registration
- **Evidence tier:** `current_or_recent_official`
- **Scope note:** The document also specifies 1500×1200 pixels for a scanned sheet containing multiple pasted photos. That is not an individual-photo dimension and is excluded from the individual photograph fields.

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | passport size | True | Submission of Registration Data for Classes IX/XI, Session 2025-26; p. 18-19; Annexure C - Steps for Scanning and Uploading Photographs | 5 |
| `file_size.published_maximum` | verified | 40 | 40 kb | True | Submission of Registration Data for Classes IX/XI, Session 2025-26; p. 18-19; Annexure C - Steps for Scanning and Uploading Photographs | 5 |
| `file_size.size_unit_as_published` | verified | "kb" | kb | True | Submission of Registration Data for Classes IX/XI, Session 2025-26; p. 18-19; Annexure C - Steps for Scanning and Uploading Photographs | 5 |
| `formats.allowed_formats` | verified | ["JPG"] | jpg file | True | Submission of Registration Data for Classes IX/XI, Session 2025-26; p. 18-19; Annexure C - Steps for Scanning and Uploading Photographs | 5 |
| `filename.mode` | verified | "pattern" | registration number | True | Submission of Registration Data for Classes IX/XI, Session 2025-26; p. 18-19; Annexure C - Steps for Scanning and Uploading Photographs | 5 |
| `filename.pattern` | verified | "<candidate_registration_number>" | registration number | True | Submission of Registration Data for Classes IX/XI, Session 2025-26; p. 18-19; Annexure C - Steps for Scanning and Uploading Photographs | 5 |
| `filename.instructions` | verified | "Save the photograph with the candidate registration number." | registration number | True | Submission of Registration Data for Classes IX/XI, Session 2025-26; p. 18-19; Annexure C - Steps for Scanning and Uploading Photographs | 5 |
| `background.mode` | verified | "plain_background" | Solid colour backgrounds | True | Submission of Registration Data for Classes IX/XI, Session 2025-26; p. 18-19; Annexure C - Steps for Scanning and Uploading Photographs | 4 |
| `background.instructions` | verified | "Solid colour backgrounds are best." | Solid colour backgrounds are best | True | Submission of Registration Data for Classes IX/XI, Session 2025-26; p. 18-19; Annexure C - Steps for Scanning and Uploading Photographs | 4 |
| `composition.face_coverage_target` | verified | 80 | 80% of the image | True | Submission of Registration Data for Classes IX/XI, Session 2025-26; p. 18-19; Annexure C - Steps for Scanning and Uploading Photographs | 5 |
| `appearance.face_coverage_basis` | verified | "head_height" | composing 80% of the image | True | Submission of Registration Data for Classes IX/XI, Session 2025-26; p. 18-19; Annexure C - Steps for Scanning and Uploading Photographs | 4 |
| `composition.complete_hair_visible` | verified | true | top of the hair | True | Submission of Registration Data for Classes IX/XI, Session 2025-26; p. 18-19; Annexure C - Steps for Scanning and Uploading Photographs | 5 |
| `composition.face_centred` | verified | true | centered | True | Submission of Registration Data for Classes IX/XI, Session 2025-26; p. 18-19; Annexure C - Steps for Scanning and Uploading Photographs | 5 |
| `composition.frontal_pose` | verified | true | directly facing the camera | True | Submission of Registration Data for Classes IX/XI, Session 2025-26; p. 18-19; Annexure C - Steps for Scanning and Uploading Photographs | 5 |
| `composition.eye_visibility` | verified | true | Eyes must be open | True | Submission of Registration Data for Classes IX/XI, Session 2025-26; p. 18-19; Annexure C - Steps for Scanning and Uploading Photographs | 5 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "must not be tinted", "condition": "Tinted glasses are prohibited unless worn daily for medical purposes."} | must not be tinted | True | Submission of Registration Data for Classes IX/XI, Session 2025-26; p. 18-19; Annexure C - Steps for Scanning and Uploading Photographs | 5 |
| `appearance.smile` | verified | {"policy": "permitted", "source_wording": "smiling is allowed"} | smiling is allowed | True | Submission of Registration Data for Classes IX/XI, Session 2025-26; p. 18-19; Annexure C - Steps for Scanning and Uploading Photographs | 5 |
| `appearance.monochrome_accepted` | verified | false | full colour | True | Submission of Registration Data for Classes IX/XI, Session 2025-26; p. 18-19; Annexure C - Steps for Scanning and Uploading Photographs | 5 |
| `appearance.recency_maximum_days` | verified | 180 | last 6 months | True | Submission of Registration Data for Classes IX/XI, Session 2025-26; p. 18-19; Annexure C - Steps for Scanning and Uploading Photographs | 4 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `file_size.published_minimum`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.exact_filename`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `background.required_colour`, `background.shadows_allowed`, `background.gradient_allowed`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `composition.ears_visible`, `composition.chin_visible`, `appearance.headwear`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.attestation_required`.

### 34. MPSC General Online Application Photograph Instruction

- **Body:** Maharashtra Public Service Commission
- **Cycle / stage / role:** current portal guide / application / candidate_photograph
- **Jurisdiction / category:** Maharashtra / state_psc
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | 3.5 cm x 4.5 cm | True | Instructions for Filling the Application Form; Photograph instructions | 3 |
| `permitted_pixel_range` | verified | "3.5 cm × 4.5 cm" | 3.5 cm x 4.5 cm | True | Instructions for Filling the Application Form; Photograph instructions | 3 |
| `file_size.published_maximum` | verified | 50 | 50 KB | True | Instructions for Filling the Application Form; Photograph instructions | 3 |
| `file_size.size_unit_as_published` | verified | "KB" | KB | True | Instructions for Filling the Application Form; Photograph instructions | 3 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | .jpg or .jpeg | True | Instructions for Filling the Application Form; Photograph instructions | 3 |
| `background.mode` | verified | "plain_background" | solid colour background | True | Instructions for Filling the Application Form; Photograph instructions | 3 |
| `background.required_colour` | verified | "preferably blue, green or red" | preferably blue, green or red | True | Instructions for Filling the Application Form; Photograph instructions | 3 |
| `background.shadows_allowed` | verified | false | no shadows | True | Instructions for Filling the Application Form; Photograph instructions | 3 |
| `composition.frontal_pose` | verified | true | directly facing the camera | True | Instructions for Filling the Application Form; Photograph instructions | 3 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `file_size.published_minimum`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.monochrome_accepted`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 35. UPPSC One Time Registration Photograph

- **Body:** Uttar Pradesh Public Service Commission
- **Cycle / stage / role:** current OTR / application / candidate_photograph
- **Jurisdiction / category:** Uttar Pradesh / state_psc
- **Evidence tier:** `current_or_recent_official`
- **Scope note:** The official white-paper instruction is a scanning substrate instruction, not a white-background rule for the portrait.

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | crop only the photograph | True | OTR Photograph Instruction; Photo scanning workflow | 3 |
| `file_size.published_maximum` | verified | 50 | 50 KB | True | OTR Photograph Instruction; Photo scanning workflow | 3 |
| `file_size.size_unit_as_published` | verified | "KB" | KB | True | OTR Photograph Instruction; Photo scanning workflow | 3 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `file_size.published_minimum`, `formats.allowed_formats`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.mode`, `background.required_colour`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.monochrome_accepted`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 36. BPSC Current Recruitment Photograph Specification

- **Body:** Bihar Public Service Commission
- **Cycle / stage / role:** current / application / candidate_photograph
- **Jurisdiction / category:** Bihar / state_psc
- **Evidence tier:** `secondary_only`
- **Scope note:** No current official BPSC photo specification was located. Positive values are secondary-source leads, not official verification.

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "exact" | 250 x 250 | False | BPSC photo-resize specification page | 2 |
| `dimensions.width_px` | verified | 250 | 250 x 250 | False | BPSC photo-resize specification page | 2 |
| `dimensions.height_px` | verified | 250 | 250 x 250 | False | BPSC photo-resize specification page | 2 |
| `file_size.published_minimum` | verified | 20 | 20 KB | False | BPSC photo-resize specification page | 2 |
| `file_size.published_maximum` | verified | 50 | 50 KB | False | BPSC photo-resize specification page | 2 |
| `file_size.size_unit_as_published` | verified | "KB" | KB | False | BPSC photo-resize specification page | 2 |
| `formats.allowed_formats` | verified | ["JPG"] | JPG | False | BPSC photo-resize specification page | 2 |
| `background.mode` | verified | "plain_light" | light background | False | BPSC photo-resize specification page | 2 |

**Fields not found in the checked source(s):** `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.required_colour`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.monochrome_accepted`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 37. RPSC Current Online Application Photograph

- **Body:** Rajasthan Public Service Commission
- **Cycle / stage / role:** current / application / candidate_photograph
- **Jurisdiction / category:** Rajasthan / state_psc
- **Evidence tier:** `mixed_official_secondary`
- **Scope note:** The attestation requirement is official and form-specific. Numeric upload values are secondary and conflicting.

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | conflicting | exact (secondary; RPSC photo specification page) / unspecified (secondary; RPSC photograph size guide) | 240 x 320; 3.5 x 4.5 cm | False | RPSC photo specification page; RPSC photograph size guide | - |
| `dimensions.width_px` | verified | 240 | 240 x 320 | False | RPSC photo specification page | 2 |
| `dimensions.height_px` | verified | 320 | 240 x 320 | False | RPSC photo specification page | 2 |
| `file_size.published_minimum` | verified | 20 | 20 KB | False | RPSC photo specification page | 2 |
| `file_size.published_maximum` | conflicting | 50 (secondary; RPSC photo specification page) / 100 (secondary; RPSC photograph size guide) | 50 KB; 100 KB | False | RPSC photo specification page; RPSC photograph size guide | - |
| `file_size.size_unit_as_published` | verified | "KB" | KB | False | RPSC photo specification page | 2 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG/JPEG | False | RPSC photo specification page | 2 |
| `appearance.attestation_required` | verified | true | duly attested | True | Instructions for Candidates | 4 |

**Fields not found in the checked source(s):** `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.mode`, `background.required_colour`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.monochrome_accepted`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`.

### 38. Karnataka PSC Current Recruitment Portal Photograph

- **Body:** Karnataka Public Service Commission
- **Cycle / stage / role:** current / application / candidate_photograph
- **Jurisdiction / category:** Karnataka / state_psc
- **Evidence tier:** `secondary_only`
- **Scope note:** The value came from a vendor-hosted KPSC registration portal. The report does not represent the host as the Commission’s own domain.

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "range" | 100 x 100 pixels to 150 x 150 pixels | False | KPSC recruitment registration portal | 3 |
| `dimensions.minimum_width_px` | verified | 100 | 100 x 100 | False | KPSC recruitment registration portal | 3 |
| `dimensions.maximum_width_px` | verified | 150 | 150 x 150 | False | KPSC recruitment registration portal | 3 |
| `dimensions.minimum_height_px` | verified | 100 | 100 x 100 | False | KPSC recruitment registration portal | 3 |
| `dimensions.maximum_height_px` | verified | 150 | 150 x 150 | False | KPSC recruitment registration portal | 3 |
| `file_size.published_maximum` | verified | 200 | 200 KB | False | KPSC recruitment registration portal | 3 |
| `file_size.size_unit_as_published` | verified | "KB" | KB | False | KPSC recruitment registration portal | 3 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG", "PNG"] | JPG/JPEG/PNG | False | KPSC recruitment registration portal | 3 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `file_size.published_minimum`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.mode`, `background.required_colour`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.monochrome_accepted`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 39. WBPSC / WBCS Current Online Application Photograph

- **Body:** West Bengal Public Service Commission
- **Cycle / stage / role:** current / application / candidate_photograph
- **Jurisdiction / category:** West Bengal / state_psc
- **Evidence tier:** `secondary_only`
- **Scope note:** No current official WBPSC online-photo specification was located. Positive values are secondary-source leads.

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "exact" | 138 x 177 | False | WBCS photo specification page | 2 |
| `dimensions.width_px` | verified | 138 | 138 x 177 | False | WBCS photo specification page | 2 |
| `dimensions.height_px` | verified | 177 | 138 x 177 | False | WBCS photo specification page | 2 |
| `file_size.published_minimum` | verified | 20 | 20 KB | False | WBCS photo specification page | 2 |
| `file_size.published_maximum` | verified | 100 | 100 KB | False | WBCS photo specification page | 2 |
| `file_size.size_unit_as_published` | verified | "KB" | KB | False | WBCS photo specification page | 2 |
| `formats.allowed_formats` | verified | ["JPG"] | JPG | False | WBCS photo specification page | 2 |
| `background.mode` | verified | "plain_light" | light background | False | WBCS photo specification page | 2 |

**Fields not found in the checked source(s):** `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.required_colour`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.monochrome_accepted`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 40. Kerala PSC One Time Registration Photograph

- **Body:** Kerala Public Service Commission
- **Cycle / stage / role:** current OTR / application / candidate_photograph
- **Jurisdiction / category:** Kerala / state_psc
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "exact" | 150 pixels width and 200 pixels height | True | Kerala PSC FAQ / One Time Registration; Photograph upload FAQ | 4 |
| `dimensions.width_px` | verified | 150 | 150 pixels | True | Kerala PSC FAQ / One Time Registration; Photograph upload FAQ | 4 |
| `dimensions.height_px` | verified | 200 | 200 pixels | True | Kerala PSC FAQ / One Time Registration; Photograph upload FAQ | 4 |
| `file_size.published_maximum` | verified | 30 | 30 Kb | True | Kerala PSC FAQ / One Time Registration; Photograph upload FAQ | 4 |
| `file_size.size_unit_as_published` | verified | "Kb" | Kb | True | Kerala PSC FAQ / One Time Registration; Photograph upload FAQ | 4 |
| `formats.allowed_formats` | verified | ["JPG"] | JPG | True | Kerala PSC FAQ / One Time Registration; Photograph upload FAQ | 4 |
| `background.mode` | verified | "plain_light" | white/light coloured background | True | Kerala PSC FAQ / One Time Registration; Photograph upload FAQ | 4 |
| `composition.face_centred` | verified | true | face at the centre | True | Kerala PSC FAQ / One Time Registration; Photograph upload FAQ | 4 |
| `composition.frontal_pose` | verified | true | front facial pose | True | Kerala PSC FAQ / One Time Registration; Photograph upload FAQ | 4 |
| `composition.eye_visibility` | verified | true | eyes open | True | Kerala PSC FAQ / One Time Registration; Photograph upload FAQ | 4 |
| `appearance.headwear` | verified | {"policy": "conditional", "source_wording": "religious custom", "condition": "Cap/goggles prohibited except where required by religious custom; face and shoulders must remain clear."} | religious custom | True | Kerala PSC FAQ / One Time Registration; Photograph upload FAQ | 4 |
| `appearance.imprint.policy` | verified | "required" | name of the applicant and the date | True | Kerala PSC Notification No. 373/2024 | 5 |
| `appearance.imprint.fields` | verified | ["candidate_name", "photograph_date"] | name of the applicant and the date | True | Kerala PSC Notification No. 373/2024 | 5 |
| `appearance.imprint.position` | verified | "bottom" | bottom | True | Kerala PSC Notification No. 373/2024 | 5 |
| `appearance.recency_maximum_days` | verified | 180 | within six months | True | Kerala PSC Notification No. 373/2024 | 4 |

**Fields not found in the checked source(s):** `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `file_size.published_minimum`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.required_colour`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `appearance.spectacles`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.monochrome_accepted`, `appearance.live_capture_required`, `appearance.attestation_required`.

### 41. APPSC Forest Beat Officer / Assistant Beat Officer 2025

- **Body:** Andhra Pradesh Public Service Commission
- **Cycle / stage / role:** 2025 / application / candidate_photograph
- **Jurisdiction / category:** Andhra Pradesh / state_psc
- **Evidence tier:** `current_or_recent_official`
- **Scope note:** The notification states identity/attestation requirements but no pixel, DPI, file-size or file-format specification was located.

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | passport size | True | Forest Beat Officer / Assistant Beat Officer Notification 2025 | 4 |
| `appearance.monochrome_accepted` | verified | false | colour photograph | True | Forest Beat Officer / Assistant Beat Officer Notification 2025 | 4 |
| `appearance.attestation_required` | verified | true | attested by a Gazetted Officer | True | Forest Beat Officer / Assistant Beat Officer Notification 2025 | 4 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `file_size.published_minimum`, `file_size.published_maximum`, `file_size.size_unit_as_published`, `formats.allowed_formats`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.mode`, `background.required_colour`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`.

### 42. Common Admission Test 2025

- **Body:** Indian Institutes of Management
- **Cycle / stage / role:** 2025 / application / candidate_photograph
- **Jurisdiction / category:** India / management_entrance
- **Evidence tier:** `secondary_only`
- **Scope note:** The current official site was located, but the photo clause was not retrievable in this run. Positive values are from a secondary reproduction of the registration guide.

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "exact" | 1200 x 1200 pixels | False | Reproduction of CAT 2025 photograph instructions | 2 |
| `dimensions.width_px` | verified | 1200 | 1200 x 1200 pixels | False | Reproduction of CAT 2025 photograph instructions | 2 |
| `dimensions.height_px` | verified | 1200 | 1200 x 1200 pixels | False | Reproduction of CAT 2025 photograph instructions | 2 |
| `file_size.published_maximum` | verified | 1 | 1 MB | False | Reproduction of CAT 2025 photograph instructions | 2 |
| `file_size.size_unit_as_published` | verified | "MB" | MB | False | Reproduction of CAT 2025 photograph instructions | 2 |
| `formats.allowed_formats` | verified | ["JPEG", "JPG"] | JPEG/JPG | False | Reproduction of CAT 2025 photograph instructions | 2 |
| `background.mode` | verified | "plain_light" | white/off-white | False | Reproduction of CAT 2025 photograph instructions | 2 |
| `composition.frontal_pose` | verified | true | front view | False | Reproduction of CAT 2025 photograph instructions | 2 |
| `composition.eye_visibility` | verified | true | eyes open | False | Reproduction of CAT 2025 photograph instructions | 2 |
| `appearance.recency_maximum_days` | verified | 180 | not more than 6 months | False | Reproduction of CAT 2025 photograph instructions | 2 |

**Fields not found in the checked source(s):** `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `file_size.published_minimum`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.required_colour`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.monochrome_accepted`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.attestation_required`.

### 43. Management Aptitude Test 2026

- **Body:** All India Management Association
- **Cycle / stage / role:** 2026 / application / candidate_photograph
- **Jurisdiction / category:** India / management_entrance
- **Evidence tier:** `current_or_recent_official`
- **Scope note:** The current official page publishes 10-50 kb. A historical official guide published 5-50 kb; the older minimum is recorded as a cycle change, not as a current conflict.

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | passport size | True | Management Aptitude Test - current application page | 4 |
| `file_size.published_minimum` | verified | 10 | 10 kb | True | Management Aptitude Test - current application page | 4 |
| `file_size.published_maximum` | verified | 50 | 50 kb | True | Management Aptitude Test - current application page | 4 |
| `file_size.size_unit_as_published` | verified | "kb" | kb | True | Management Aptitude Test - current application page | 4 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | .jpg/.jpeg | True | MAT Guidelines - prior official cycle | 3 |
| `appearance.monochrome_accepted` | verified | false | colour photograph | True | MAT Guidelines - prior official cycle | 3 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.mode`, `background.required_colour`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 44. MHT-CET 2026

- **Body:** State Common Entrance Test Cell, Maharashtra
- **Cycle / stage / role:** 2026 / application / candidate_photograph
- **Jurisdiction / category:** Maharashtra / entrance
- **Evidence tier:** `current_or_recent_official`

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | 2 x 2 inch | True | MHT-CET 2026 Information Brochure; Photograph specifications | 5 |
| `permitted_pixel_range` | verified | "2 × 2 inch (50 × 50 mm)" | 2 x 2 inch | True | MHT-CET 2026 Information Brochure; Photograph specifications | 5 |
| `file_size.published_minimum` | verified | 100 | 100 KB | True | MHT-CET 2026 Information Brochure; Photograph specifications | 5 |
| `file_size.published_maximum` | verified | 5 | 5 MB | True | MHT-CET 2026 Information Brochure; Photograph specifications | 5 |
| `file_size.size_unit_as_published` | verified | "mixed: KB minimum; MB maximum" | 100 KB to 5 MB | True | MHT-CET 2026 Information Brochure; Photograph specifications | 5 |
| `background.mode` | verified | "plain_light" | plain light/white background | True | MHT-CET 2026 Information Brochure; Photograph specifications | 5 |
| `background.required_colour` | verified | "light or white" | light/white | True | MHT-CET 2026 Information Brochure; Photograph specifications | 5 |
| `background.shadows_allowed` | verified | false | no shadows | True | MHT-CET 2026 Information Brochure; Photograph specifications | 5 |
| `composition.face_coverage_target` | verified | 80 | 80% | True | MHT-CET 2026 Information Brochure; Photograph specifications | 5 |
| `appearance.face_coverage_basis` | verified | "unspecified" | 80% | True | MHT-CET 2026 Information Brochure; Photograph specifications | 4 |
| `composition.complete_hair_visible` | verified | true | full head | True | MHT-CET 2026 Information Brochure; Photograph specifications | 5 |
| `composition.face_centred` | verified | true | centered | True | MHT-CET 2026 Information Brochure; Photograph specifications | 5 |
| `composition.frontal_pose` | verified | true | full face/front | True | MHT-CET 2026 Information Brochure; Photograph specifications | 5 |
| `composition.eye_visibility` | verified | true | eyes open | True | MHT-CET 2026 Information Brochure; Photograph specifications | 5 |
| `appearance.spectacles` | verified | {"policy": "conditional", "source_wording": "avoid glare", "condition": "Spectacles permitted only without glare; tinted glasses are prohibited."} | avoid glare | True | MHT-CET 2026 Information Brochure; Photograph specifications | 5 |
| `appearance.headwear` | verified | {"policy": "conditional", "source_wording": "religious headwear exception", "condition": "Headwear prohibited except for religious reasons."} | religious headwear | True | MHT-CET 2026 Information Brochure; Photograph specifications | 5 |
| `appearance.smile` | verified | {"policy": "conditional", "source_wording": "neutral expression", "condition": "Neutral expression required."} | neutral expression | True | MHT-CET 2026 Information Brochure; Photograph specifications | 5 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `formats.allowed_formats`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `composition.ears_visible`, `composition.chin_visible`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.monochrome_accepted`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 45. Karnataka Common Entrance Test 2026

- **Body:** Karnataka Examinations Authority
- **Cycle / stage / role:** 2026 / application / candidate_photograph
- **Jurisdiction / category:** Karnataka / entrance
- **Evidence tier:** `secondary_only`
- **Scope note:** The official KEA portal was located, but the photo clause was not retrievable. Positive values are secondary-source leads.

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | 3.5 x 4.5 cm | False | KCET 2026 photograph specification | 2 |
| `permitted_pixel_range` | verified | "3.5 × 4.5 cm" | 3.5 x 4.5 cm | False | KCET 2026 photograph specification | 2 |
| `file_size.published_maximum` | verified | 50 | 50 KB | False | KCET 2026 photograph specification | 2 |
| `file_size.size_unit_as_published` | verified | "KB" | KB | False | KCET 2026 photograph specification | 2 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG/JPEG | False | KCET 2026 photograph specification | 2 |
| `background.mode` | verified | "exact_colour" | white background | False | KCET 2026 photograph specification | 2 |
| `background.required_colour` | verified | "white" | white background | False | KCET 2026 photograph specification | 2 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `file_size.published_minimum`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.monochrome_accepted`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 46. WBJEE 2026

- **Body:** West Bengal Joint Entrance Examinations Board
- **Cycle / stage / role:** 2026 / application / candidate_photograph
- **Jurisdiction / category:** West Bengal / entrance
- **Evidence tier:** `secondary_only`
- **Scope note:** The positive values come from a copy of the official bulletin hosted on a non-official domain. The official WBJEE site confirms the cycle, but the directly hosted PDF was not retrieved.

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | recent colour photograph | False | WBJEE 2026 Information Bulletin - reproduced copy | 3 |
| `file_size.published_minimum` | verified | 10 | 10 KB | False | WBJEE 2026 Information Bulletin - reproduced copy | 3 |
| `file_size.published_maximum` | verified | 200 | 200 KB | False | WBJEE 2026 Information Bulletin - reproduced copy | 3 |
| `file_size.size_unit_as_published` | verified | "KB" | KB | False | WBJEE 2026 Information Bulletin - reproduced copy | 3 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG/JPEG | False | WBJEE 2026 Information Bulletin - reproduced copy | 3 |
| `appearance.monochrome_accepted` | verified | false | colour photograph | False | WBJEE 2026 Information Bulletin - reproduced copy | 3 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.mode`, `background.required_colour`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 47. ICAI Examination Portal Photograph (current portal scope)

- **Body:** Institute of Chartered Accountants of India
- **Cycle / stage / role:** current / application / candidate_photograph
- **Jurisdiction / category:** India / professional_body
- **Evidence tier:** `current_or_recent_official`
- **Scope note:** This is scoped to the current ICAI examination portal page retrieved; it is not asserted as universal across every ICAI examination workflow.

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | passport size | True | Image Resize - ICAI examination portal | 4 |
| `file_size.published_maximum` | verified | 50 | 50KB | True | Image Resize - ICAI examination portal | 4 |
| `file_size.size_unit_as_published` | verified | "KB" | KB | True | Image Resize - ICAI examination portal | 4 |
| `formats.allowed_formats` | verified | ["JPEG"] | JPEG | True | Image Resize - ICAI examination portal | 4 |
| `formats.preferred_format` | verified | "JPEG" | photo.jpeg | True | Image Resize - ICAI examination portal | 4 |
| `filename.mode` | verified | "exact" | photo.jpeg | True | Image Resize - ICAI examination portal | 4 |
| `filename.exact_filename` | verified | "photo.jpeg" | photo.jpeg | True | Image Resize - ICAI examination portal | 4 |
| `background.mode` | verified | "plain_light" | light/white background | True | Image Resize - ICAI examination portal | 4 |
| `background.required_colour` | verified | "light or white" | light/white | True | Image Resize - ICAI examination portal | 4 |
| `appearance.monochrome_accepted` | verified | false | colour | True | Image Resize - ICAI examination portal | 4 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `file_size.published_minimum`, `formats.colour_space`, `formats.extension_policy`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 48. ICSI Student Registration / Examination Account Photograph

- **Body:** Institute of Company Secretaries of India
- **Cycle / stage / role:** current / application / candidate_photograph
- **Jurisdiction / category:** India / professional_body
- **Evidence tier:** `current_or_recent_official`
- **Scope note:** Official ICSI sources conflict on the minimum file size: 20 KB versus 21 KB. The report does not choose a winner.

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | student photo | True | ICSI Registration Instructions | 4 |
| `file_size.published_minimum` | conflicting | 20 (official; ICSI Registration Instructions) / 21 (official; Advisory - correct photo and signature in online account) | 20 KB; 21 KB | True | ICSI Registration Instructions; Advisory - correct photo and signature in online account | - |
| `file_size.published_maximum` | verified | 50 | 50 KB | True | ICSI Registration Instructions | 4 |
| `file_size.size_unit_as_published` | verified | "KB" | KB | True | ICSI Registration Instructions | 4 |
| `formats.allowed_formats` | verified | ["JPG", "JPEG", "PNG", "GIF", "BMP", "PDF"] | jpg/jpeg/png/gif/bmp/pdf | True | ICSI Registration Instructions | 4 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.mode`, `background.required_colour`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.facial_hair`, `appearance.face_mask`, `appearance.monochrome_accepted`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.recency_maximum_days`, `appearance.attestation_required`.

### 49. Indian Army Agniveer CEE 2025-26 - online upload

- **Body:** Indian Army
- **Cycle / stage / role:** 2025-26 / application / candidate_photograph
- **Jurisdiction / category:** India / defence
- **Evidence tier:** `mixed_official_secondary`
- **Scope note:** Official source verifies rally-stage appearance/provenance rules. Online-upload numeric values are secondary and conflicting.

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | passport size | True | Agniveer Recruitment Notification 2025-26; Photograph / rally documents | 4 |
| `file_size.published_minimum` | conflicting | 20 (secondary; Indian Army Agniveer upload specification) / 5 (secondary; Indian Army photograph size guide) | 20 KB; 5 KB | False | Indian Army Agniveer upload specification; Indian Army photograph size guide | - |
| `file_size.published_maximum` | conflicting | 50 (secondary; Indian Army Agniveer upload specification) / 20 (secondary; Indian Army photograph size guide) | 50 KB; 20 KB | False | Indian Army Agniveer upload specification; Indian Army photograph size guide | - |
| `formats.allowed_formats` | verified | ["JPG", "JPEG"] | JPG/JPEG | False | Indian Army Agniveer upload specification | 2 |
| `background.mode` | verified | "exact_colour" | white background | True | Agniveer Recruitment Notification 2025-26; Photograph / rally documents | 5 |
| `background.required_colour` | verified | "white" | white background | True | Agniveer Recruitment Notification 2025-26; Photograph / rally documents | 5 |
| `appearance.facial_hair` | verified | {"policy": "conditional", "source_wording": "clean shaven", "condition": "Clean-shaven photograph required except for Sikh candidates."} | clean shaven | True | Agniveer Recruitment Notification 2025-26; Photograph / rally documents | 5 |
| `appearance.recency_maximum_days` | verified | 90 | not more than three months old | True | Agniveer Recruitment Notification 2025-26; Photograph / rally documents | 4 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `file_size.size_unit_as_published`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.face_mask`, `appearance.monochrome_accepted`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.attestation_required`.

### 50. Indian Army Agniveer CEE 2025-26 - rally/document verification

- **Body:** Indian Army
- **Cycle / stage / role:** 2025-26 / document_verification / printed_copies
- **Jurisdiction / category:** India / defence
- **Evidence tier:** `current_or_recent_official`
- **Scope note:** The official notification requires printed copies at the rally and rejects photocopied/Photoshopped photographs. No printed-photo pixel/file specification applies.

| Field | Status | Value | Short exact evidence anchor | Official? | Source / location | Confidence |
|---|---|---|---|---|---|---:|
| `dimensions.mode` | verified | "unspecified" | passport size | True | Agniveer Recruitment Notification 2025-26; Photograph / rally documents | 5 |
| `background.mode` | verified | "exact_colour" | white background | True | Agniveer Recruitment Notification 2025-26; Photograph / rally documents | 5 |
| `background.required_colour` | verified | "white" | white background | True | Agniveer Recruitment Notification 2025-26; Photograph / rally documents | 5 |
| `appearance.facial_hair` | verified | {"policy": "conditional", "source_wording": "except Sikh candidates", "condition": "Clean-shaven photograph required except for Sikh candidates."} | except Sikh candidates | True | Agniveer Recruitment Notification 2025-26; Photograph / rally documents | 5 |
| `appearance.recency_maximum_days` | verified | 90 | not more than three months old | True | Agniveer Recruitment Notification 2025-26; Photograph / rally documents | 4 |

**Fields not found in the checked source(s):** `dimensions.width_px`, `dimensions.height_px`, `dimensions.minimum_width_px`, `dimensions.maximum_width_px`, `dimensions.minimum_height_px`, `dimensions.maximum_height_px`, `dimensions.preferred_width_px`, `dimensions.preferred_height_px`, `dpi`, `aspect_ratio`, `permitted_pixel_range`, `file_size.published_minimum`, `file_size.published_maximum`, `file_size.size_unit_as_published`, `formats.allowed_formats`, `formats.preferred_format`, `formats.colour_space`, `formats.extension_policy`, `filename.mode`, `filename.exact_filename`, `filename.pattern`, `filename.allowed_characters`, `filename.case_sensitive`, `filename.extension_required`, `filename.instructions`, `background.shadows_allowed`, `background.gradient_allowed`, `background.instructions`, `composition.face_coverage_target`, `composition.face_coverage_minimum`, `composition.face_coverage_maximum`, `appearance.face_coverage_basis`, `composition.complete_hair_visible`, `composition.ears_visible`, `composition.chin_visible`, `composition.face_centred`, `composition.frontal_pose`, `composition.eye_visibility`, `appearance.spectacles`, `appearance.headwear`, `appearance.smile`, `appearance.face_mask`, `appearance.monochrome_accepted`, `appearance.imprint.policy`, `appearance.imprint.fields`, `appearance.imprint.position`, `appearance.live_capture_required`, `appearance.attestation_required`.

## 5. Conflicts

### RPSC Current Online Application Photograph - `dimensions.mode`

- **exact** - secondary; RPSC photo specification page; https://form-mitra.com/rpsc
- **unspecified** - secondary; RPSC photograph size guide; https://examsize.com/rpsc-photo-signature-size/
- **Researcher view (opinion only):** Non-official sources disagree; no winner selected.

### RPSC Current Online Application Photograph - `file_size.published_maximum`

- **50** - secondary; RPSC photo specification page; https://form-mitra.com/rpsc
- **100** - secondary; RPSC photograph size guide; https://examsize.com/rpsc-photo-signature-size/
- **Researcher view (opinion only):** Secondary sources publish different maximum sizes.

### ICSI Student Registration / Examination Account Photograph - `file_size.published_minimum`

- **20** - official; ICSI Registration Instructions; https://smash.icsi.edu/Scripts/Registration/Instructions.aspx?ID=R2
- **21** - official; Advisory - correct photo and signature in online account; https://www.icsi.edu/webmodules/advisory_ensuringcorrectphotoandsignofstud_onlineaccount.pdf
- **Researcher view (opinion only):** Two official ICSI pages publish different minimums.

### Indian Army Agniveer CEE 2025-26 - online upload - `file_size.published_minimum`

- **20** - secondary; Indian Army Agniveer upload specification; https://testbook.com/indian-army-agniveer/apply-online
- **5** - secondary; Indian Army photograph size guide; https://photoresizer.com/indian-army-photo-size
- **Researcher view (opinion only):** Secondary sources disagree; official online-upload numeric limit was not located.

### Indian Army Agniveer CEE 2025-26 - online upload - `file_size.published_maximum`

- **50** - secondary; Indian Army Agniveer upload specification; https://testbook.com/indian-army-agniveer/apply-online
- **20** - secondary; Indian Army photograph size guide; https://photoresizer.com/indian-army-photo-size
- **Researcher view (opinion only):** Secondary sources disagree; official online-upload numeric limit was not located.

## 6. Exams/records with no locatable official output specification

- **GIC Assistant Manager 2024-25** - No current official numeric/file specification located in the checked source.
- **BPSC Current Recruitment Photograph Specification** - No current official BPSC photo specification was located. Positive values are secondary-source leads, not official verification.
- **RPSC Current Online Application Photograph** - The attestation requirement is official and form-specific. Numeric upload values are secondary and conflicting.
- **Karnataka PSC Current Recruitment Portal Photograph** - The value came from a vendor-hosted KPSC registration portal. The report does not represent the host as the Commission’s own domain.
- **WBPSC / WBCS Current Online Application Photograph** - No current official WBPSC online-photo specification was located. Positive values are secondary-source leads.
- **Common Admission Test 2025** - The current official site was located, but the photo clause was not retrievable in this run. Positive values are from a secondary reproduction of the registration guide.
- **Karnataka Common Entrance Test 2026** - The official KEA portal was located, but the photo clause was not retrievable. Positive values are secondary-source leads.
- **WBJEE 2026** - The positive values come from a copy of the official bulletin hosted on a non-official domain. The official WBJEE site confirms the cycle, but the directly hosted PDF was not retrieved.

## 7. Secondary-source sightings used as leads

- **GIC Assistant Manager 2024-25 - `dimensions.mode`:** `unspecified`; GIC Assistant Manager photo specification reproduction; https://testbook.com/gic-assistant-manager/apply-online. This is not represented as an official rule.
- **GIC Assistant Manager 2024-25 - `dimensions.preferred_width_px`:** `200`; GIC Assistant Manager photo specification reproduction; https://testbook.com/gic-assistant-manager/apply-online. This is not represented as an official rule.
- **GIC Assistant Manager 2024-25 - `dimensions.preferred_height_px`:** `230`; GIC Assistant Manager photo specification reproduction; https://testbook.com/gic-assistant-manager/apply-online. This is not represented as an official rule.
- **GIC Assistant Manager 2024-25 - `file_size.published_minimum`:** `20`; GIC Assistant Manager photo specification reproduction; https://testbook.com/gic-assistant-manager/apply-online. This is not represented as an official rule.
- **GIC Assistant Manager 2024-25 - `file_size.published_maximum`:** `50`; GIC Assistant Manager photo specification reproduction; https://testbook.com/gic-assistant-manager/apply-online. This is not represented as an official rule.
- **GIC Assistant Manager 2024-25 - `file_size.size_unit_as_published`:** `KB`; GIC Assistant Manager photo specification reproduction; https://testbook.com/gic-assistant-manager/apply-online. This is not represented as an official rule.
- **GIC Assistant Manager 2024-25 - `formats.allowed_formats`:** `['JPG', 'JPEG']`; GIC Assistant Manager photo specification reproduction; https://testbook.com/gic-assistant-manager/apply-online. This is not represented as an official rule.
- **BPSC Current Recruitment Photograph Specification - `dimensions.mode`:** `exact`; BPSC photo-resize specification page; https://form-mitra.com/bpsc. This is not represented as an official rule.
- **BPSC Current Recruitment Photograph Specification - `dimensions.width_px`:** `250`; BPSC photo-resize specification page; https://form-mitra.com/bpsc. This is not represented as an official rule.
- **BPSC Current Recruitment Photograph Specification - `dimensions.height_px`:** `250`; BPSC photo-resize specification page; https://form-mitra.com/bpsc. This is not represented as an official rule.
- **BPSC Current Recruitment Photograph Specification - `file_size.published_minimum`:** `20`; BPSC photo-resize specification page; https://form-mitra.com/bpsc. This is not represented as an official rule.
- **BPSC Current Recruitment Photograph Specification - `file_size.published_maximum`:** `50`; BPSC photo-resize specification page; https://form-mitra.com/bpsc. This is not represented as an official rule.
- **BPSC Current Recruitment Photograph Specification - `file_size.size_unit_as_published`:** `KB`; BPSC photo-resize specification page; https://form-mitra.com/bpsc. This is not represented as an official rule.
- **BPSC Current Recruitment Photograph Specification - `formats.allowed_formats`:** `['JPG']`; BPSC photo-resize specification page; https://form-mitra.com/bpsc. This is not represented as an official rule.
- **BPSC Current Recruitment Photograph Specification - `background.mode`:** `plain_light`; BPSC photo-resize specification page; https://form-mitra.com/bpsc. This is not represented as an official rule.
- **RPSC Current Online Application Photograph - `dimensions.mode`:** `exact`; RPSC photo specification page; https://form-mitra.com/rpsc. This is not represented as an official rule.
- **RPSC Current Online Application Photograph - `dimensions.mode`:** `unspecified`; RPSC photograph size guide; https://examsize.com/rpsc-photo-signature-size/. This is not represented as an official rule.
- **RPSC Current Online Application Photograph - `dimensions.width_px`:** `240`; RPSC photo specification page; https://form-mitra.com/rpsc. This is not represented as an official rule.
- **RPSC Current Online Application Photograph - `dimensions.height_px`:** `320`; RPSC photo specification page; https://form-mitra.com/rpsc. This is not represented as an official rule.
- **RPSC Current Online Application Photograph - `file_size.published_minimum`:** `20`; RPSC photo specification page; https://form-mitra.com/rpsc. This is not represented as an official rule.
- **RPSC Current Online Application Photograph - `file_size.published_maximum`:** `50`; RPSC photo specification page; https://form-mitra.com/rpsc. This is not represented as an official rule.
- **RPSC Current Online Application Photograph - `file_size.published_maximum`:** `100`; RPSC photograph size guide; https://examsize.com/rpsc-photo-signature-size/. This is not represented as an official rule.
- **RPSC Current Online Application Photograph - `file_size.size_unit_as_published`:** `KB`; RPSC photo specification page; https://form-mitra.com/rpsc. This is not represented as an official rule.
- **RPSC Current Online Application Photograph - `formats.allowed_formats`:** `['JPG', 'JPEG']`; RPSC photo specification page; https://form-mitra.com/rpsc. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `dimensions.mode`:** `range`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `dimensions.width_px`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `dimensions.height_px`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `dimensions.minimum_width_px`:** `100`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `dimensions.maximum_width_px`:** `150`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `dimensions.minimum_height_px`:** `100`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `dimensions.maximum_height_px`:** `150`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `dimensions.preferred_width_px`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `dimensions.preferred_height_px`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `dpi`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `aspect_ratio`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `permitted_pixel_range`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `file_size.published_minimum`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `file_size.published_maximum`:** `200`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `file_size.size_unit_as_published`:** `KB`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `formats.allowed_formats`:** `['JPG', 'JPEG', 'PNG']`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `formats.preferred_format`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `formats.colour_space`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `formats.extension_policy`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `filename.mode`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `filename.exact_filename`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `filename.pattern`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `filename.allowed_characters`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `filename.case_sensitive`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `filename.extension_required`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `filename.instructions`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `background.mode`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `background.required_colour`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `background.shadows_allowed`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `background.gradient_allowed`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `background.instructions`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `composition.face_coverage_target`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `composition.face_coverage_minimum`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `composition.face_coverage_maximum`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `appearance.face_coverage_basis`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `composition.complete_hair_visible`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `composition.ears_visible`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `composition.chin_visible`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `composition.face_centred`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `composition.frontal_pose`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `composition.eye_visibility`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `appearance.spectacles`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `appearance.headwear`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `appearance.smile`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `appearance.facial_hair`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `appearance.face_mask`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `appearance.monochrome_accepted`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `appearance.imprint.policy`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `appearance.imprint.fields`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `appearance.imprint.position`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `appearance.live_capture_required`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `appearance.recency_maximum_days`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **Karnataka PSC Current Recruitment Portal Photograph - `appearance.attestation_required`:** `None`; KPSC recruitment registration portal; https://apply.registernow.in/KPSC/Registration/. This is not represented as an official rule.
- **WBPSC / WBCS Current Online Application Photograph - `dimensions.mode`:** `exact`; WBCS photo specification page; https://form-mitra.com/wbcs. This is not represented as an official rule.
- **WBPSC / WBCS Current Online Application Photograph - `dimensions.width_px`:** `138`; WBCS photo specification page; https://form-mitra.com/wbcs. This is not represented as an official rule.
- **WBPSC / WBCS Current Online Application Photograph - `dimensions.height_px`:** `177`; WBCS photo specification page; https://form-mitra.com/wbcs. This is not represented as an official rule.
- **WBPSC / WBCS Current Online Application Photograph - `file_size.published_minimum`:** `20`; WBCS photo specification page; https://form-mitra.com/wbcs. This is not represented as an official rule.
- **WBPSC / WBCS Current Online Application Photograph - `file_size.published_maximum`:** `100`; WBCS photo specification page; https://form-mitra.com/wbcs. This is not represented as an official rule.
- **WBPSC / WBCS Current Online Application Photograph - `file_size.size_unit_as_published`:** `KB`; WBCS photo specification page; https://form-mitra.com/wbcs. This is not represented as an official rule.
- **WBPSC / WBCS Current Online Application Photograph - `formats.allowed_formats`:** `['JPG']`; WBCS photo specification page; https://form-mitra.com/wbcs. This is not represented as an official rule.
- **WBPSC / WBCS Current Online Application Photograph - `background.mode`:** `plain_light`; WBCS photo specification page; https://form-mitra.com/wbcs. This is not represented as an official rule.
- **Common Admission Test 2025 - `dimensions.mode`:** `exact`; Reproduction of CAT 2025 photograph instructions; https://www.reddit.com/r/CATpreparation/. This is not represented as an official rule.
- **Common Admission Test 2025 - `dimensions.width_px`:** `1200`; Reproduction of CAT 2025 photograph instructions; https://www.reddit.com/r/CATpreparation/. This is not represented as an official rule.
- **Common Admission Test 2025 - `dimensions.height_px`:** `1200`; Reproduction of CAT 2025 photograph instructions; https://www.reddit.com/r/CATpreparation/. This is not represented as an official rule.
- **Common Admission Test 2025 - `file_size.published_maximum`:** `1`; Reproduction of CAT 2025 photograph instructions; https://www.reddit.com/r/CATpreparation/. This is not represented as an official rule.
- **Common Admission Test 2025 - `file_size.size_unit_as_published`:** `MB`; Reproduction of CAT 2025 photograph instructions; https://www.reddit.com/r/CATpreparation/. This is not represented as an official rule.
- **Common Admission Test 2025 - `formats.allowed_formats`:** `['JPEG', 'JPG']`; Reproduction of CAT 2025 photograph instructions; https://www.reddit.com/r/CATpreparation/. This is not represented as an official rule.
- **Common Admission Test 2025 - `background.mode`:** `plain_light`; Reproduction of CAT 2025 photograph instructions; https://www.reddit.com/r/CATpreparation/. This is not represented as an official rule.
- **Common Admission Test 2025 - `composition.frontal_pose`:** `True`; Reproduction of CAT 2025 photograph instructions; https://www.reddit.com/r/CATpreparation/. This is not represented as an official rule.
- **Common Admission Test 2025 - `composition.eye_visibility`:** `True`; Reproduction of CAT 2025 photograph instructions; https://www.reddit.com/r/CATpreparation/. This is not represented as an official rule.
- **Common Admission Test 2025 - `appearance.recency_maximum_days`:** `180`; Reproduction of CAT 2025 photograph instructions; https://www.reddit.com/r/CATpreparation/. This is not represented as an official rule.
- **Karnataka Common Entrance Test 2026 - `dimensions.mode`:** `unspecified`; KCET 2026 photograph specification; https://engineering.careers360.com/articles/kcet-photo-signature-size-guidelines. This is not represented as an official rule.
- **Karnataka Common Entrance Test 2026 - `permitted_pixel_range`:** `3.5 × 4.5 cm`; KCET 2026 photograph specification; https://engineering.careers360.com/articles/kcet-photo-signature-size-guidelines. This is not represented as an official rule.
- **Karnataka Common Entrance Test 2026 - `file_size.published_maximum`:** `50`; KCET 2026 photograph specification; https://engineering.careers360.com/articles/kcet-photo-signature-size-guidelines. This is not represented as an official rule.
- **Karnataka Common Entrance Test 2026 - `file_size.size_unit_as_published`:** `KB`; KCET 2026 photograph specification; https://engineering.careers360.com/articles/kcet-photo-signature-size-guidelines. This is not represented as an official rule.
- **Karnataka Common Entrance Test 2026 - `formats.allowed_formats`:** `['JPG', 'JPEG']`; KCET 2026 photograph specification; https://engineering.careers360.com/articles/kcet-photo-signature-size-guidelines. This is not represented as an official rule.
- **Karnataka Common Entrance Test 2026 - `background.mode`:** `exact_colour`; KCET 2026 photograph specification; https://engineering.careers360.com/articles/kcet-photo-signature-size-guidelines. This is not represented as an official rule.
- **Karnataka Common Entrance Test 2026 - `background.required_colour`:** `white`; KCET 2026 photograph specification; https://engineering.careers360.com/articles/kcet-photo-signature-size-guidelines. This is not represented as an official rule.
- **WBJEE 2026 - `dimensions.mode`:** `unspecified`; WBJEE 2026 Information Bulletin - reproduced copy; https://www.collegeadmission.in/uploads/notices/exam/51/2026/pdf/1773303344-wbjee-2026-information-bulletin.pdf. This is not represented as an official rule.
- **WBJEE 2026 - `file_size.published_minimum`:** `10`; WBJEE 2026 Information Bulletin - reproduced copy; https://www.collegeadmission.in/uploads/notices/exam/51/2026/pdf/1773303344-wbjee-2026-information-bulletin.pdf. This is not represented as an official rule.
- **WBJEE 2026 - `file_size.published_maximum`:** `200`; WBJEE 2026 Information Bulletin - reproduced copy; https://www.collegeadmission.in/uploads/notices/exam/51/2026/pdf/1773303344-wbjee-2026-information-bulletin.pdf. This is not represented as an official rule.
- **WBJEE 2026 - `file_size.size_unit_as_published`:** `KB`; WBJEE 2026 Information Bulletin - reproduced copy; https://www.collegeadmission.in/uploads/notices/exam/51/2026/pdf/1773303344-wbjee-2026-information-bulletin.pdf. This is not represented as an official rule.
- **WBJEE 2026 - `formats.allowed_formats`:** `['JPG', 'JPEG']`; WBJEE 2026 Information Bulletin - reproduced copy; https://www.collegeadmission.in/uploads/notices/exam/51/2026/pdf/1773303344-wbjee-2026-information-bulletin.pdf. This is not represented as an official rule.
- **WBJEE 2026 - `appearance.monochrome_accepted`:** `False`; WBJEE 2026 Information Bulletin - reproduced copy; https://www.collegeadmission.in/uploads/notices/exam/51/2026/pdf/1773303344-wbjee-2026-information-bulletin.pdf. This is not represented as an official rule.
- **Indian Army Agniveer CEE 2025-26 - online upload - `file_size.published_minimum`:** `20`; Indian Army Agniveer upload specification; https://testbook.com/indian-army-agniveer/apply-online. This is not represented as an official rule.
- **Indian Army Agniveer CEE 2025-26 - online upload - `file_size.published_minimum`:** `5`; Indian Army photograph size guide; https://photoresizer.com/indian-army-photo-size. This is not represented as an official rule.
- **Indian Army Agniveer CEE 2025-26 - online upload - `file_size.published_maximum`:** `50`; Indian Army Agniveer upload specification; https://testbook.com/indian-army-agniveer/apply-online. This is not represented as an official rule.
- **Indian Army Agniveer CEE 2025-26 - online upload - `file_size.published_maximum`:** `20`; Indian Army photograph size guide; https://photoresizer.com/indian-army-photo-size. This is not represented as an official rule.
- **Indian Army Agniveer CEE 2025-26 - online upload - `formats.allowed_formats`:** `['JPG', 'JPEG']`; Indian Army Agniveer upload specification; https://testbook.com/indian-army-agniveer/apply-online. This is not represented as an official rule.

## 8. Access problems and human follow-up queue

- IBPS and some bank PDFs intermittently timed out; indexed official PDF text was used where available, and the official URL is retained.
- SSC CGL 2026 direct PDF retrieval was intermittent; the official notice URL and live-capture instructions are retained, but no upload file specification is asserted.
- RBI Grade B 2026 current page did not expose a retrievable photo annexure. The record is explicitly a prior-cycle official fallback.
- CAT 2025 registration-guide photograph instructions were not retrievable from the official public page without entering the registration workflow; secondary reproduction is labelled.
- BPSC, WBPSC and portions of RPSC/KCET did not yield current official numeric specifications. Secondary values are leads only.
- KPSC values came from a vendor-hosted registration portal. A human should verify the link from the Commission’s official site before using them operationally.
- WBJEE values came from a reproduced official bulletin on a non-official host; the current official site should be checked when its direct PDF is accessible.
- Indian Army official material verified rally-stage photograph rules, while online-upload numeric limits remained unresolved and conflicting across secondary sources.

## 9. Priority-2 selection: the additional 37

1. UPSC NDA & NA Examination (II) 2026
2. UPSC Combined Defence Services Examination (II) 2026
3. UPSC CAPF (Assistant Commandants) Examination 2026
4. SSC Combined Higher Secondary (10+2) Level Examination 2025
5. SSC Multi-Tasking Staff and Havaldar Examination 2025
6. SSC Constable (GD) Examination 2025
7. IBPS CRP Customer Service Associates-XV
8. IBPS CRP Specialist Officers-XVI
9. IBPS CRP Regional Rural Banks-XIV
10. SBI Junior Associates 2025
11. RBI Assistant - Panel Year 2025
12. RBI Officers in Grade B 2026 - prior-cycle official fallback
13. NABARD Grade A 2025
14. NIACL Administrative Officers 2025
15. GIC Assistant Manager 2024-25
16. CUET (UG) 2026
17. CUET (PG) 2026
18. UGC-NET June 2026
19. JEE (Advanced) 2026
20. RRB NTPC Graduate - CEN 05/2024
21. CTET September 2026
22. MPSC General Online Application Photograph Instruction
23. UPPSC One Time Registration Photograph
24. BPSC Current Recruitment Photograph Specification
25. RPSC Current Online Application Photograph
26. Karnataka PSC Current Recruitment Portal Photograph
27. WBPSC / WBCS Current Online Application Photograph
28. Kerala PSC One Time Registration Photograph
29. APPSC Forest Beat Officer / Assistant Beat Officer 2025
30. Common Admission Test 2025
31. Management Aptitude Test 2026
32. MHT-CET 2026
33. Karnataka Common Entrance Test 2026
34. WBJEE 2026
35. ICAI Examination Portal Photograph (current portal scope)
36. ICSI Student Registration / Examination Account Photograph
37. Indian Army Agniveer CEE 2025-26 - online upload

**Selection basis:** qualitative volume-informed coverage, not a fabricated numerical ranking. The list prioritises recurring high-volume national recruitment, banking and insurance recruitment, major national entrance/eligibility tests, large state PSC/CET systems, and professional-body portals. Current official applicant-volume figures were not consistently available across all bodies, so no exact candidate-count league table is claimed.

## 10. Important changes and non-equivalences

- **SSC:** current application modules use live capture; candidate-upload pixel/file rules for the photograph are therefore not supplied in the notices checked.
- **UPSC and NTA:** a scanned/uploaded photograph can coexist with mandatory live capture. The report does not treat the live image as having the scanned file’s technical limits.
- **RBI Assistant:** the scanned photograph uses a 200×230 preferred size, while the live image has a separately published 240×240 preferred size at 200 DPI. Separate records are emitted.
- **CBSE:** 1500×1200 pixels is a multiple-photo scanned-sheet workflow, not the individual candidate photograph. It is deliberately excluded from individual-photo dimensions.
- **IBPS/SBI/LIC/NIACL:** 200×230 pixels is explicitly **preferred**, so `dimensions.mode` remains `unspecified`, not `exact`.
- **MAT:** current official page says 10-50 kb, while an older official guide said 5-50 kb. This is recorded as a historical change, not a current-cycle conflict.

## 11. Source register

| ID | Document | Body | Date | Official | Type | URL | Note |
|---|---|---|---|---|---|---|---|
| UPSC-PHOTO-2026 | Instructions for Uploading Photo and Signature | Union Public Service Commission | 2026 | True | official_pdf | https://upsconline.nic.in/ngrp/assets/PDF/instruction-photo-signature-upload-upsc.pdf |  |
| SSC-CGL-2026 | Notice of Combined Graduate Level Examination, 2026 | Staff Selection Commission | 2026-05-21 | True | official_pdf | https://ssc.gov.in/api/attachment/uploads/masterData/NoticeBoards/Notice_of_adv_cgl_2025.pdf |  |
| SSC-CHSL-2025 | Notice of Combined Higher Secondary (10+2) Level Examination, 2025 | Staff Selection Commission | 2025-06-23 | True | official_pdf | https://ssc.gov.in/api/attachment/uploads/masterData/NoticeBoards/Notice_of_adv_chsl_2025.pdf |  |
| SSC-MTS-2025 | Notice of Multi-Tasking (Non-Technical) Staff and Havaldar Examination, 2025 | Staff Selection Commission | 2025-06-26 | True | official_pdf | https://ssc.gov.in/api/attachment/uploads/masterData/NoticeBoards/Notice_of_adv_mts_2025.pdf |  |
| SSC-GD-2025 | Notice of Constable (GD) Examination, 2025 | Staff Selection Commission | 2024-09-05 | True | official_pdf | https://ssc.gov.in/api/attachment/uploads/masterData/NoticeBoards/Notice_of_CTGD_2024_09_05.pdf |  |
| IBPS-PO-XVI | Detailed Notification CRP PO/MT-XVI | Institute of Banking Personnel Selection | 2026-06-30 | True | official_pdf | https://www.ibps.in/wp-content/uploads/Detailed-Notification_CRP-PO-XVI_Final_V1_30.06.2026.pdf |  |
| IBPS-CSA-XV | Detailed Notification CRP Customer Service Associates-XV | Institute of Banking Personnel Selection | 2025 | True | official_pdf | https://www.ibps.in/wp-content/uploads/DetailedNotification_CRP_CSA_XV_Final_for_Website.pdf |  |
| IBPS-SO-XVI | Detailed Notification CRP Specialist Officers-XVI | Institute of Banking Personnel Selection | 2026-06-30 | True | official_pdf | https://www.ibps.in/wp-content/uploads/Detailed-Notification-CRP-SPL-XVI_Final_V1_30.06.2026.pdf |  |
| IBPS-RRB-XIV | CRP Regional Rural Banks-XIV | Institute of Banking Personnel Selection | 2025-09-19 | True | official_pdf | https://www.ibps.in/wp-content/uploads/CRP-RRBs-XIV_Final_AD-19.9.25.pdf |  |
| SBI-PO-2025 | Recruitment of Probationary Officers - Detailed Advertisement 2025 | State Bank of India | 2025-06-23 | True | official_pdf | https://sbi.co.in/documents/77530/52947104/1_Detailed_Adv.2025_23.06.2025.pdf/54ca0942-3de1-afc4-45e8-f679fc552e7b?t=1750741324277 |  |
| SBI-JA-2025 | Recruitment of Junior Associates - Detailed Advertisement 2025 | State Bank of India | 2025-08-06 | True | official_pdf | https://sbi.co.in/documents/77530/52947104/JA%2B2025%2B-Detailed%2BAdvt.pdf/8f7ff18f-1972-21c8-9212-5a8cf85a7099?t=1754398573326 |  |
| LIC-AAO-2025 | AAO Generalist Notification 2025 | Life Insurance Corporation of India | 2025 | True | official_pdf | https://www.licindia.in/documents/d/guest/aao-generalist-notification-2025-final |  |
| RBI-ASST-2025 | Recruitment for the Post of Assistant - Panel Year 2025 | Reserve Bank of India | 2025 | True | official_webpage | https://opportunities.rbi.org.in/scripts/bs_viewcontent.aspx?Id=4912 |  |
| RBI-GRB-PRIOR | Officers in Grade B - official prior-cycle upload instructions | Reserve Bank of India | prior cycle | True | official_webpage | https://opportunities.rbi.org.in/Scripts/bs_viewcontent.aspx?Id=2836 | Prior-cycle official fallback; not proof that the 2026 portal is unchanged. |
| NABARD-GRA-2025 | Recruitment to Grade A, 2025 - Advertisement | National Bank for Agriculture and Rural Development | 2025-02-05 | True | official_pdf | https://www.nabard.org/auth/writereaddata/CareerNotices/0502252006Advertisement%20No.06%20dated%2005.02.2025.pdf |  |
| NIACL-AO-2025 | Recruitment of Administrative Officers 2025 | The New India Assurance Company Limited | 2025 | True | official_pdf | https://www.newindia.co.in/assets/docs/recruitment/RECRUITMENT%20OF%20ADMINISTRATIVE%20OFFICERS%202025/RECRUITMENT%20OF%20_5_50%20ADMINISTRATIVE%20OFFICERS%20%28GENERALISTS%20%26%20SPECIALISTS%29%20%28SCALE-I%29%20202_5.pdf |  |
| GIC-AM-2024 | Detailed Advertisement for Recruitment of Assistant Managers in GIC Re 2024 | General Insurance Corporation of India | 2024 | True | official_pdf | https://www.gicre.in/images/2024/Detailed_Advertisement_for_Recruitment_of_AMs_in_GIC_Re_2024_-_v3_-_Final.pdf |  |
| GIC-SECONDARY | GIC Assistant Manager photo specification reproduction | Testbook | 2024-25 | False | secondary_reference | https://testbook.com/gic-assistant-manager/apply-online | Used only where the official PDF was not text-retrievable; values are labelled secondary. |
| JEE-MAIN-2026 | Information Bulletin - JEE (Main) 2026 | National Testing Agency | 2025-11-02 | True | official_pdf | https://cdnbbsr.s3waas.gov.in/s3f8e59f4b2fe7c5705bf878bbd494ccdf/uploads/2025/11/202511021649722475.pdf |  |
| NEET-UG-2026 | Information Bulletin - NEET (UG) 2026 | National Testing Agency | 2026-02-23 | True | official_pdf | https://cdnbbsr.s3waas.gov.in/s37bc1ec1d9c3426357e69acd5bf320061/uploads/2026/02/202602231394640855.pdf |  |
| CUET-UG-2026 | Information Bulletin - CUET (UG) 2026 | National Testing Agency | 2026-01-03 | True | official_pdf | https://cdnbbsr.s3waas.gov.in/s3d1a21da7bca4abff8b0b61b87597de73/uploads/2026/01/202601031633478370.pdf |  |
| CUET-PG-2026 | Information Bulletin - CUET (PG) 2026 | National Testing Agency | 2025-12-16 | True | official_pdf | https://cdnbbsr.s3waas.gov.in/s388a839f2f6f1427879fc33ee4acf4f66/uploads/2025/12/202512161583029269.pdf |  |
| UGC-NET-2026 | Information Bulletin - UGC-NET June 2026 | National Testing Agency | 2026-04-30 | True | official_pdf | https://cdnbbsr.s3waas.gov.in/s301eee509ee2f68dc6014898c309e86bf/uploads/2026/04/202604301078678748.pdf |  |
| JEE-ADV-2026 | Information Brochure - JEE (Advanced) 2026 | Joint Admission Board / IIT Roorkee | 2026 | True | official_pdf | https://jeeadv.ac.in/documents/IBEnglish_2026_1.pdf |  |
| GATE-2026 | GATE 2026 Information Brochure | IIT Guwahati | 2025-09-28 | True | official_pdf | https://gate2026.iitg.ac.in/doc/IB/GATE2026-IB-28092025.pdf |  |
| RRB-L1-082024 | CEN No. 08/2024 - Level 1 Posts | Railway Recruitment Boards | 2025-01-22 | True | official_pdf | https://wcr.indianrailways.gov.in/uploads/files/1771596254046-CEN_%2008_2024_English.pdf |  |
| RRB-NTPC-052024 | CEN 05/2024 - NTPC Graduate | Railway Recruitment Boards | 2024-09 | True | official_pdf | https://rrbsecunderabad.gov.in/wp-content/uploads/2024/09/CEN-05-2024-NTPC-Graduate_ENG.pdf |  |
| CTET-SEP-2026 | Information Bulletin - CTET September 2026 | Central Board of Secondary Education | 2026-05-11 | True | official_pdf | https://cdnbbsr.s3waas.gov.in/s3443dec3062d0286986e21dc0631734c9/uploads/2026/05/202605111250310617.pdf |  |
| TNPSC-CTS-2025 | Instructions to Candidates / Combined Technical Services 2025 | Tamil Nadu Public Service Commission | 2026 | True | official_pdf | https://www.tnpsc.gov.in/static_pdf/document/instructions-to-candiates.pdf |  |
| CBSE-IX-XI-2526 | Submission of Registration Data for Classes IX/XI, Session 2025-26 | Central Board of Secondary Education | 2025-09-16 | True | official_pdf | https://www.cbse.gov.in/cbsenew/documents/Submission_Registration_Data_Class_IXXI2526_15092025.pdf |  |
| MPSC-GUIDE | Instructions for Filling the Application Form | Maharashtra Public Service Commission | undated | True | official_pdf | https://mpsconline.gov.in/downloads/Instructions-for-Filling-the-Application-Form.pdf | Official guide; undated. |
| UPPSC-OTR | OTR Photograph Instruction | Uttar Pradesh Public Service Commission | undated | True | official_pdf | https://uppsc.up.nic.in/CMS/OTR_DOC/OTR_PHOTO_INSTRUCTION.pdf |  |
| BPSC-PORTAL | BPSC official portal - searched for photograph specification | Bihar Public Service Commission | current | True | official_webpage | https://bpsc.bihar.gov.in/ |  |
| BPSC-SECONDARY | BPSC photo-resize specification page | Form Mitra | current | False | secondary_reference | https://form-mitra.com/bpsc |  |
| RPSC-GENERAL | Instructions for Candidates | Rajasthan Public Service Commission | 2025-02-27 | True | official_pdf | https://rpsc.rajasthan.gov.in/Static/InformationForCandidates/Instructions_for_Candidates.pdf |  |
| RPSC-SECONDARY-A | RPSC photo specification page | Form Mitra | current | False | secondary_reference | https://form-mitra.com/rpsc |  |
| RPSC-SECONDARY-B | RPSC photograph size guide | ExamSize | current | False | secondary_reference | https://examsize.com/rpsc-photo-signature-size/ |  |
| KPSC-PORTAL | KPSC recruitment registration portal | Karnataka Public Service Commission / portal operator | current | False | official_application_portal | https://apply.registernow.in/KPSC/Registration/ | Vendor-hosted application portal. Linkage to KPSC should be rechecked before operational use. |
| WBPSC-PORTAL | WBPSC official portal - searched for photo specification | West Bengal Public Service Commission | current | True | official_webpage | https://psc.wb.gov.in/ |  |
| WBPSC-SECONDARY | WBCS photo specification page | Form Mitra | current | False | secondary_reference | https://form-mitra.com/wbcs |  |
| KERALA-FAQ | Kerala PSC FAQ / One Time Registration | Kerala Public Service Commission | current | True | official_webpage | https://psc.kerala.gov.in/kpsc/faq.php |  |
| KERALA-NOTI-373 | Kerala PSC Notification No. 373/2024 | Kerala Public Service Commission | 2024 | True | official_pdf | https://keralapsc.gov.in/sites/default/files/2024-11/noti-373-24.pdf |  |
| APPSC-FBO-2025 | Forest Beat Officer / Assistant Beat Officer Notification 2025 | Andhra Pradesh Public Service Commission | 2025-07-14 | True | official_pdf | https://psc.ap.gov.in/Documents/NotificationDocuments/FBO_ABO_Notification_14072025.pdf |  |
| CAT-OFFICIAL | CAT 2025 official website / registration guide location | Indian Institutes of Management | 2025 | True | official_webpage | https://iimcat.ac.in/ | Current guide was not fully retrievable without the registration workflow. |
| CAT-SECONDARY | Reproduction of CAT 2025 photograph instructions | CAT applicant discussion / guide reproduction | 2025 | False | secondary_reference | https://www.reddit.com/r/CATpreparation/ | Secondary reproduction of the official registration guide; not an official source. |
| MAT-CURRENT | Management Aptitude Test - current application page | All India Management Association | 2026 | True | official_webpage | https://www.aima.in/content/testing-and-assessment/mat/mat |  |
| MAT-OLD | MAT Guidelines - prior official cycle | All India Management Association | 2017 | True | official_pdf | https://apps.aima.in/matdec17/Guidelines.pdf | Historical official source used only to identify a cycle change. |
| MHT-CET-2026 | MHT-CET 2026 Information Brochure | State Common Entrance Test Cell, Maharashtra | 2026-04-11 | True | official_pdf | https://cetcell.mahacet.org/wp-content/uploads/2023/12/MHT-CET-2026-Information-Brochure-Updated-on-11.04.2026.pdf |  |
| KCET-OFFICIAL | KEA official portal - KCET 2026 | Karnataka Examinations Authority | 2026 | True | official_webpage | https://cetonline.karnataka.gov.in/kea/ |  |
| KCET-SECONDARY | KCET 2026 photograph specification | Careers360 | 2026 | False | secondary_reference | https://engineering.careers360.com/articles/kcet-photo-signature-size-guidelines |  |
| WBJEE-OFFICIAL | WBJEE 2026 official website | West Bengal Joint Entrance Examinations Board | 2026 | True | official_webpage | https://wbjeeb.nic.in/wbjee/ |  |
| WBJEE-REPRO | WBJEE 2026 Information Bulletin - reproduced copy | CollegeAdmission.in | 2026 | False | secondary_reference | https://www.collegeadmission.in/uploads/notices/exam/51/2026/pdf/1773303344-wbjee-2026-information-bulletin.pdf | Copy of an official bulletin hosted on a non-official domain. |
| ICAI-RESIZE | Image Resize - ICAI examination portal | Institute of Chartered Accountants of India | current | True | official_application_portal | https://pqc.icaiexam.icai.org/INTT/Home/ImageResize |  |
| ICSI-INSTR | ICSI Registration Instructions | Institute of Company Secretaries of India | current | True | official_webpage | https://smash.icsi.edu/Scripts/Registration/Instructions.aspx?ID=R2 |  |
| ICSI-ADVISORY | Advisory - correct photo and signature in online account | Institute of Company Secretaries of India | undated | True | official_pdf | https://www.icsi.edu/webmodules/advisory_ensuringcorrectphotoandsignofstud_onlineaccount.pdf |  |
| ARMY-AGNIVEER-2526 | Agniveer Recruitment Notification 2025-26 | Indian Army | 2025-03-12 | True | official_pdf | https://www.joinindianarmy.nic.in/writereaddata/Portal/BRAVO_NotificationPDF/AGNIVEER_NOTIFICATION_ARUNACHAL_PRADESH_2025-26.pdf |  |
| ARMY-SECONDARY-A | Indian Army Agniveer upload specification | Testbook | 2026 | False | secondary_reference | https://testbook.com/indian-army-agniveer/apply-online |  |
| ARMY-SECONDARY-B | Indian Army photograph size guide | PhotoResizer | 2026 | False | secondary_reference | https://photoresizer.com/indian-army-photo-size |  |

## 12. Machine-readable sidecar

The companion `exam_photo_specs_2026.json` contains every field requested in the research specification for every record, including explicit `not_found` objects, evidence metadata, byte interpretations and conflict alternatives.