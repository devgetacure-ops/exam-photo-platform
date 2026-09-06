# Examinations with no usable upload rules

**The worklist for the next research pass.** 96 examinations: 89 newly
discovered and 7 already in the catalogue but blocked. The 89 account for
**77,506,027 candidates** between them.

Generated 2026-09-07 from the four research deliveries, cross-checked against
what `scripts/encode_exam_rules.py` actually requires.

## What the encoder needs

A rule record is built only when **both** of these are present:

| Field | Example published wording |
|---|---|
| `file_size.published_maximum` | "photograph must not exceed 50 KB" |
| `formats.allowed_formats` | "JPEG only" / "JPG, JPEG or PNG" |

Pixel dimensions are **welcome but optional** — an examination publishing only
"JPEG, under 50 KB" is encodable and lands in the "size and format only" tier.
Missing either one blocks the examination entirely. That is the whole reason
these 96 produce nothing.

Two rules the research must keep (DEC-049): **absent is not permissive** — where
an authority publishes no format, record `not_found` rather than assuming JPEG;
and **every value carries its source URL and the raw published wording**.

## Section 1 — 89 newly discovered examinations

### Why these have no rules

The package was scoped to **market discovery, not rule extraction**. It set out
to find every nationwide examination above 100,000 candidates and prove the
volume with sources — which it did, and did well. It deliberately stopped before
pulling each authority's photograph and signature specifications, and says so
itself: *"Market-volume evidence does not silently become a technical upload
rule."* This is phase one of two, not a failed extraction.

**9 of the 89 have an official government source recorded. The other
80 have none** — their volume was proved from press releases and news
coverage. So for most of this list the first task is not extracting a value, it
is **locating the authority's own notification or portal instructions page**.

| Reason recorded by the research | Exams |
|---|---:|
| High volume proved; the authority's upload rules were never retrieved | 40 |
| Source located, per-field values not extracted from it | 28 |
| Shared RSSB asset rules found; per-exam values missing | 4 |
| Some field-level values verified, but not size and format together | 4 |
| Substantial official rules found, but not these two fields | 3 |
| 2026 cycle rules not yet published or not yet read | 3 |
| Current cycle needs re-checking against the authority | 1 |
| Cycle not announced at the research cutoff | 1 |
| Cycle verified; rules await authority confirmation | 1 |
| An older cycle's rules are known; the current cycle is unverified | 1 |
| Only some stage requirements were captured | 1 |
| Flagged for remediation; evidence incomplete | 1 |
| Cycle verified; the numbers still need fetching from the authority | 1 |

### The list, by candidate volume

`Already known` is what the package carries — do not re-fetch it. `Official
source` is blank where no authority document has been located yet.

| # | Examination | Conducting body | Candidates | Missing | Already known | Official source |
|---:|---|---|---:|---|---|---|
| 1 | Uttar Pradesh Police Constable Recruitment | Uttar Pradesh Police Recruitment and Promotion Board | 4,817,441 | file size, format | — | — |
| 2 | RPF Constable | Railway Protection Force / RRB | 4,530,288 | file size, format | — | — |
| 3 | Indian Army Agniveer Recruitment | Indian Army | 3,709,000 | file size, format | — | [link](https://www.pib.gov.in/Pressreleasepage.Aspx?Lang=2&PRID=1884353&Reg=3) |
| 4 | Delhi Police Constable (Executive) | Staff Selection Commission / Delhi Police | 3,243,083 | file size, format | — | — |
| 5 | SSC Selection Post Phase XIII | Staff Selection Commission | 2,939,401 | file size, format | capture_mode | — |
| 6 | BSSC Second Inter-Level Combined Competitive Examination | Bihar Staff Selection Commission | 2,600,000 | file size, format | — | — |
| 7 | Jawahar Navodaya Vidyalaya Selection Test Class VI | Navodaya Vidyalaya Samiti / CBSE | 2,541,347 | file size, format | — | [link](https://cbseit.in/cbse/PE/documents/UPCOMING_PROJECTS_18112025.pdf) |
| 8 | UPSSSC Preliminary Eligibility Test (PET) | Uttar Pradesh Subordinate Services Selection Commission | 2,531,996 | file size, format | — | — |
| 9 | Rajasthan Grade IV Recruitment | Rajasthan Staff Selection Board | 2,475,000 | file size, format | capture_policy | — |
| 10 | Kendriya Vidyalaya Sangathan Direct Recruitment Examination | Kendriya Vidyalaya Sangathan | 1,999,634 | file size, format | — | [link](https://www.education.gov.in/sites/upload_files/mhrd/files/document-reports/AR_2023-24_en.pdf) |
| 11 | Assam Direct Recruitment Grade III | State Level Recruitment Commission Assam | 1,850,000 | file size, format | — | — |
| 12 | Maharashtra Police Recruitment | Maharashtra Police | 1,776,000 | file size, format | — | — |
| 13 | Bihar Police Constable Recruitment | Central Selection Board of Constable, Bihar | 1,673,586 | file size, format | — | — |
| 14 | Rajasthan CET Senior Secondary Level | Rajasthan Staff Selection Board | 1,540,000 | file size, format | capture_policy | — |
| 15 | RPF Sub-Inspector | Railway Protection Force / RRB | 1,535,635 | file size, format | — | — |
| 16 | Rajasthan Eligibility Examination for Teachers (REET) | Board of Secondary Education Rajasthan | 1,429,822 | file size, format | — | — |
| 17 | TNPSC Combined Civil Services Examination IV (Group IV Services) | Tamil Nadu Public Service Commission | 1,389,738 | format | file_size, filename, height, imprint, scan_resolution, width | — |
| 18 | HSSC CET Group D | Haryana Staff Selection Commission | 1,376,183 | file size, format | — | — |
| 19 | Assam Direct Recruitment Grade IV | State Level Recruitment Commission Assam | 1,370,000 | file size, format | — | — |
| 20 | Haryana CET Group C | Haryana Staff Selection Commission | 1,348,893 | file size, format | — | — |
| 21 | Rajasthan CET Graduate Level | Rajasthan Staff Selection Board | 1,304,144 | file size, format | capture_policy | — |
| 22 | MP Patwari Recruitment Examination | Madhya Pradesh Employees Selection Board | 1,279,000 | file size, format | — | — |
| 23 | Gujarat Police Lokrakshak Recruitment | Gujarat Police Recruitment Board | 1,150,000 | file size, format | — | — |
| 24 | MHT-CET | State Common Entrance Test Cell Maharashtra | 1,142,610 | format | background, expression, face_coverage_target, file_size, physical_size | — |
| 25 | UPPSC Review Officer / Assistant Review Officer | Uttar Pradesh Public Service Commission | 1,076,004 | file size, format | — | — |
| 26 | MP Police Constable Recruitment Test | Madhya Pradesh Employees Selection Board | 978,059 | file size, format | — | [link](https://esb.mp.gov.in/statistical_information/Schedule_2025.pdf) |
| 27 | Indian Navy Agniveer SSR/MR Recruitment | Indian Navy | 955,000 | file size, format | — | [link](https://www.pib.gov.in/Pressreleasepage.Aspx?Lang=2&PRID=1884353&Reg=3) |
| 28 | TSPSC Group IV Services | Telangana State Public Service Commission | 951,321 | file size, format | — | — |
| 29 | RRB Technician | Railway Recruitment Boards | 841,525 | file size, format | — | — |
| 30 | TNPSC Combined Civil Services Examination II (Group II/IIA) | Tamil Nadu Public Service Commission | 793,966 | file size, format | — | — |
| 31 | Indian Air Force Agniveervayu Recruitment | Indian Air Force | 749,899 | file size, format | — | — |
| 32 | SSC Sub-Inspector in Delhi Police and CAPFs Examination | Staff Selection Commission | 734,157 | file size, format | — | — |
| 33 | Rajasthan Patwari Recruitment | Rajasthan Staff Selection Board | 676,011 | file size, format | capture_policy | — |
| 34 | JSSC Combined Graduate Level Examination | Jharkhand Staff Selection Commission | 640,000 | file size, format | — | — |
| 35 | UPPSC Combined State/Upper Subordinate Services Examination (PCS) | Uttar Pradesh Public Service Commission | 626,387 | file size, format | — | — |
| 36 | West Bengal Primary Teacher Eligibility Test | West Bengal Board of Primary Education | 619,102 | file size, format | — | — |
| 37 | Rajasthan Pre-D.El.Ed Examination (BSTC) | Vardhman Mahaveer Open University / designated authority | 605,242 | file size, format | — | — |
| 38 | Maharashtra Teacher Eligibility Test (MAHA TET) | Maharashtra State Council of Examination | 600,125 | file size, format | — | — |
| 39 | West Bengal School Service Commission SLST Assistant Teacher Recruitment | West Bengal School Service Commission | 590,000 | file size, format | — | — |
| 40 | RRB JE/DMS/CMA | Railway Recruitment Boards | 574,351 | file size, format | capture_mode, preexisting_image_allowed | — |
| 41 | TGPSC Group II Services Examination | Telangana Public Service Commission | 551,855 | file size, format | — | — |
| 42 | JKSSB Police Constable Recruitment | Jammu & Kashmir Services Selection Board | 550,000 | file size, format | — | — |
| 43 | TGPSC Group III Services Examination | Telangana Public Service Commission | 536,400 | file size, format | — | — |
| 44 | Rajasthan Police Constable Recruitment | Rajasthan Police | 524,740 | file size, format | — | — |
| 45 | Gujarat Police PSI Recruitment | Gujarat Police Recruitment Board | 499,000 | file size, format | — | — |
| 46 | SSC Junior Engineer Examination | Staff Selection Commission | 483,557 | file size, format | — | — |
| 47 | APPSC Group II Services Examination | Andhra Pradesh Public Service Commission | 483,000 | file size, format | — | — |
| 48 | BPSC Teacher Recruitment Examination (TRE) | Bihar Public Service Commission | 463,000 | file size, format | — | — |
| 49 | RRB Ministerial and Isolated Categories | Railway Recruitment Boards | 446,013 | file size, format | — | — |
| 50 | Bihar Secondary Teacher Eligibility Test | Bihar School Examination Board | 442,214 | file size, format | — | — |
| 51 | UP B.Ed Joint Entrance Examination | Bundelkhand University Jhansi | 441,030 | file size, format | — | — |
| 52 | RRB Section Controller | Railway Recruitment Boards | 433,748 | file size, format | — | — |
| 53 | Joint Entrance Examination Council Uttar Pradesh Polytechnic Entrance | Joint Entrance Examination Council Uttar Pradesh | 425,993 | file size, format | — | — |
| 54 | DSSSB Major Recruitment Examination Family | Delhi Subordinate Services Selection Board | 414,201 | file size, format | — | [link](https://dsssb.delhi.gov.in/sites/default/files/DSSSB/circulars-orders/annual_report_2024-25_s.pdf) |
| 55 | TGPSC Group I Services Examination | Telangana Public Service Commission | 403,667 | file size, format | — | — |
| 56 | AP Mega DSC Teacher Recruitment | Government of Andhra Pradesh | 336,300 | file size, format | — | — |
| 57 | Karnataka Common Entrance Test (KCET) | Karnataka Examinations Authority | 330,479 | file size, format | — | — |
| 58 | Bihar D.El.Ed Joint Entrance Examination | Bihar School Examination Board | 323,313 | file size, format | — | — |
| 59 | RRB Paramedical Categories | Railway Recruitment Boards | 319,396 | file size, format | capture_mode, pose, spectacles_allowed | — |
| 60 | TG EAPCET | JNTU Hyderabad / TGCHE | 300,147 | file size, format | — | — |
| 61 | Common Admission Test (CAT) | Indian Institutes of Management | 295,000 | file size, format | — | — |
| 62 | Telangana DSC Teacher Recruitment | Government of Telangana | 279,956 | file size, format | — | — |
| 63 | NEET-PG | National Board of Examinations in Medical Sciences | 273,183 | file size, format | — | — |
| 64 | Rajasthan Pre-Teacher Education Test | Rajasthan PTET conducting university | 273,000 | file size, format | — | — |
| 65 | Andhra Pradesh Teacher Eligibility Test | Department of School Education Andhra Pradesh | 267,789 | file size, format | — | — |
| 66 | MP Primary School Teacher Eligibility Test | Madhya Pradesh Employees Selection Board | 266,982 | file size, format | — | — |
| 67 | AP EAPCET | JNTU Kakinada / APSCHE | 258,545 | file size, format | — | — |
| 68 | OSSSC Combined Recruitment Examination | Odisha Sub-ordinate Staff Selection Commission | 250,000 | file size, format | — | — |
| 69 | TNPSC Combined Civil Services Examination I (Group I) | Tamil Nadu Public Service Commission | 238,255 | file size, format | — | — |
| 70 | Haryana Teacher Eligibility Test | Board of School Education Haryana | 233,294 | file size, format | — | [link](https://prms.prharyana.gov.in/press-release/3244) |
| 71 | All India Sainik Schools Entrance Examination | National Testing Agency | 196,661 | file size, format | — | [link](https://cdnbbsr.s3waas.gov.in/s388a839f2f6f1427879fc33ee4acf4f66/uploads/2026/02/20260227853124735.pdf) |
| 72 | Joint CSIR-UGC NET | National Testing Agency / CSIR | 195,241 | file size, format | — | — |
| 73 | CG Vyapam Pre-B.Ed Entrance Examination | Chhattisgarh Professional Examination Board | 190,000 | file size, format | — | — |
| 74 | Telangana Teacher Eligibility Test (TG TET) | Department of School Education Telangana | 183,653 | file size, format | — | — |
| 75 | AP POLYCET | State Board of Technical Education and Training Andhra Pradesh | 177,581 | file size, format | — | — |
| 76 | MAH MBA/MMS CET | State Common Entrance Test Cell Maharashtra | 157,281 | file size, format | — | — |
| 77 | Karnataka Teacher Eligibility Test | School Education Department Karnataka | 155,167 | file size, format | — | — |
| 78 | BITS Admission Test | Birla Institute of Technology and Science Pilani | 150,730 | file size, format | — | — |
| 79 | APPSC Group I Services Examination | Andhra Pradesh Public Service Commission | 148,881 | file size, format | — | — |
| 80 | Kerala Engineering Architecture Medical Entrance Examination | Commissioner for Entrance Examinations Kerala | 148,146 | file size, format | — | — |
| 81 | Jharkhand Police Constable Recruitment | Jharkhand Staff Selection Commission | 144,308 | file size, format | — | — |
| 82 | Xavier Aptitude Test | XLRI Xavier School of Management | 142,235 | file size, format | — | — |
| 83 | UPSC Engineering Services Examination | Union Public Service Commission | 141,058 | file size, format | — | — |
| 84 | GUJCET | Gujarat Secondary and Higher Secondary Education Board | 136,071 | file size, format | — | — |
| 85 | West Bengal Joint Entrance Examination (WBJEE) | West Bengal Joint Entrance Examinations Board | 120,857 | file size, format | — | — |
| 86 | TG/TS POLYCET | State Board of Technical Education and Training Telangana | 106,716 | file size, format | — | — |
| 87 | Odisha Joint Entrance Examination (OJEE) | OJEE Committee | 103,434 | file size, format | — | — |
| 88 | Bihar B.Ed Common Entrance Test | Lalit Narayan Mithila University / Bihar CET-B.Ed | — | file size, format | — | — |
| 89 | SSC Stenographer Grade C & D Examination | Staff Selection Commission | — | file size, format | — | [link](https://www.sscwr.net/noticeboard/Stenographers%20Grade%20_C_D_Examination%2C%202025%20%E2%80%93%20Information%20regarding%20City.pdf) |

## Section 2 — 7 examinations already in the catalogue, blocked

In `packages/exam-rules/research/exam_photo_specs_2026.json`, skipped by the
encoder today. **Two are blocked by conflicting evidence rather than missing
evidence** — there the task is to decide which published figure is current and
authoritative, not to find a number.

| Examination | Blocked by | Detail |
|---|---|---|
| JEE (Advanced) 2026 | missing evidence | file size (not_found), format (not_found) |
| UPPSC One Time Registration Photograph | missing evidence | format (not_found) |
| RPSC Current Online Application Photograph | **conflict to resolve** | dimensions.mode, file_size.published_maximum |
| APPSC Forest Beat Officer / Assistant Beat Officer 2025 | missing evidence | file size (not_found), format (not_found) |
| MHT-CET 2026 | missing evidence | format (not_found) |
| Indian Army Agniveer CEE 2025-26 - online upload | **conflict to resolve** | file_size.published_minimum, file_size.published_maximum |
| Indian Army Agniveer CEE 2025-26 - rally/document verification | missing evidence | file size (not_found), format (not_found) |

> The most recent delivery (`exam-research-2`) re-researched JEE (Advanced) and
> MHT-CET and returned `not_found` on the blocking fields again. If a second
> attempt also finds nothing, the honest conclusion may be that these
> authorities do not publish a format at all — which is a finding worth
> recording rather than a gap worth re-researching a third time.

## Section 3 — 4 examinations research cannot help

All four SSC examinations photograph the candidate through the portal. **No
research will ever produce an upload specification for them**, because there is
no upload. They carry 8 signature deliverables between them that the platform
could prepare, unreachable only because a rule record currently requires a
photograph specification. **That is an engine change, not a research task** —
do not commission research for these.

- SSC Combined Graduate Level Examination 2026
- SSC Combined Higher Secondary (10+2) Level Examination 2025
- SSC Multi-Tasking Staff and Havaldar Examination 2025
- SSC Constable (GD) Examination 2025

## Note on overlap

**MHT-CET appears in both Section 1 and Section 2.** The newly discovered record
carries a file size the catalogue's record does not; neither carries a format.
Merging them still will not encode it — the format blocks both sides.

