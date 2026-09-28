# Upload rules for 22 examinations

**Fulfilled 28 September**: the rows arrived as `packages/exam-rules/research/delivery_2026_09_27/uploads_22_rows.csv` and all 22 are in the catalogue (DEC-114).

These 22 examinations are in the 2026-09-27 delivery's exam sheet, but it has no upload rows for them, so the catalogue has nothing to build their photograph from (DEC-114). Everything else from the delivery is already in.

What to hand back: **one CSV with the same columns as the delivery's uploads sheet** (`packages/exam-rules/research/delivery_2026_09_27/uploads.csv`), one row per uploaded file, using the row numbers below. It is imported with the same script as the rest.

## The 22 examinations

| row_no | Examination (exactly as in the delivery) | Conducting body |
|---|---|---|
| 191 | UPSC Indian Forest Service Examination (UPSC IFoS Main Examination) | Union Public Service Commission (UPSC), New Delhi |
| 192 | UPSC Combined Medical Services Examination (UPSC CMS) | Union Public Service Commission (UPSC), New Delhi |
| 193 | UPSC Indian Economic Service / Indian Statistical Service Examination (IES / ISS) | Union Public Service Commission (UPSC), New Delhi |
| 194 | UPSC Combined Geo-Scientist Examination (CGSE) | Union Public Service Commission (UPSC), New Delhi |
| 195 | UPSC Central Bureau of Investigation DSP Limited Departmental Competitive Examination (CBI DSP LDCE) | Union Public Service Commission (UPSC), New Delhi |
| 196 | UPSC Central Industrial Security Force Assistant Commandants Executive LDCE (CISF AC EXE LDCE) | Union Public Service Commission (UPSC), New Delhi |
| 197 | UPSC Combined Section Officers / Stenographers Grade B / Grade 1 LDCE | Union Public Service Commission (UPSC), New Delhi |
| 198 | UPSC Direct Recruitment by Online Recruitment Application (UPSC ORA Advertisements) | Union Public Service Commission (UPSC), New Delhi |
| 201 | Railway Recruitment Cell East Central Railway General Departmental Competitive Examination (RRC ECR GDCE) | Railway Recruitment Cell (RRC), East Central Railway, Hajipur, Bihar |
| 202 | UGC Recognised State Eligibility Tests (Kerala SET, KSET Karnataka, JKSET/LASET, WB SET) | UGC Accompanying State Nodal Agencies (LBS Kerala, KEA Karnataka, University of Jammu, WBCSC West Bengal) |
| 204 | Small Industries Development Bank of India Assistant Manager Grade A & Manager Grade B (SIDBI Grade A / B) | Small Industries Development Bank of India (SIDBI), Lucknow / Mumbai |
| 205 | Pension Fund Regulatory and Development Authority Officer Grade A Assistant Manager (PFRDA Grade A) | Pension Fund Regulatory and Development Authority (PFRDA), New Delhi |
| 206 | United India Insurance Company Administrative Officer Scale I Recruitment (UIIC AO) | United India Insurance Company Limited (UIIC), Chennai |
| 208 | Foreign Dental Screening Test (FDST for BDS / MDS Graduates) | National Board of Examinations in Medical Sciences (NBEMS), New Delhi on behalf of DCI |
| 209 | Diplomate of National Board Final Examination (DNB Final / DrNB Final Theory) | National Board of Examinations in Medical Sciences (NBEMS), New Delhi |
| 212 | Indian Navy Agniveer Senior Secondary Recruit & Matric Recruit (Navy Agniveer SSR / MR) | Indian Navy, Ministry of Defence, New Delhi |
| 213 | Indian Navy Direct Entry Petty Officer / Chief Petty Officer (Sports Quota Recruitment) | The Directorate of Naval Physical Training and Sports (DNPTS), IHQ MoD (Navy), New Delhi |
| 214 | Indian Army Technical Graduate Course (Army TGC-140 / TGC-141) | Directorate General of Recruiting, Integrated HQ of MoD (Army), New Delhi |
| 215 | Army Dental Corps Short Service Commission (Army Dental Corps SSC) | Directorate General Armed Forces Medical Services (DGAFMS), Ministry of Defence, New Delhi |
| 216 | Assam Rifles Technical and Tradesman Recruitment Rally | Headquarters Directorate General Assam Rifles, Laitkor, Shillong, Meghalaya |
| 217 | Indo-Tibetan Border Police Head Constable Recruitment (ITBP HC Education & Stress Counsellor / Motor Mechanic) | Indo-Tibetan Border Police Force (ITBP), Ministry of Home Affairs, New Delhi |
| 218 | Central Reserve Police Force Meritorious Sports Persons Recruitment (CRPF Sports Quota GD Constable) | Central Reserve Police Force (CRPF), Ministry of Home Affairs, New Delhi |


## Prompt to give the research tool

```text
I am attaching a list of 22 Indian examinations/recruitments. For EACH one, find every
file the candidate must UPLOAD in the online application (photograph, signature, left
thumb impression, handwritten declaration, live/webcam photo, ID proof, certificates,
category/PwD documents, scribe forms, etc.).

Use any sources: the official notice/bulletin/portal first, then previous cycles'
notices, coaching and exam-prep sites, job portals, YouTube walkthroughs of the form,
and candidates' screenshots. Do not answer "not found": keep searching until every
file has values. Where sources disagree, pick the value most sources agree on (an
official source outranks others; the current cycle outranks older ones) and write
CONFLICT with the other values and their sources.

Return ONE CSV, one row per uploaded file, with exactly these columns and in this order:

row_no, exam_name, file_name, mandatory_or_conditional, stage, formats, min_size,
max_size, size_unit, pixel_width, pixel_height, pixel_rule, physical_size, dpi,
colour_or_bw, background, face_coverage, photo_recency, spectacles, headwear,
face_mask, name_date_on_photo, signature_or_thumb_rules, file_naming, other_checks,
selected_value_basis, sources_agreeing, confidence, conflict,
conflicting_values_with_sources, exact_passage, source_url, source_type,
page_or_section, date_checked

Rules for the columns:
- row_no and exam_name: copy exactly from the list I give you.
- file_name: what the portal calls the file, e.g. "Candidate Photograph",
  "Candidate Signature", "Left Thumb Impression".
- min_size / max_size: numbers only (e.g. 20 and 50); size_unit: KB or MB.
- formats: e.g. "JPG, JPEG" or "PDF".
- pixel_width / pixel_height: numbers only (e.g. 200 and 230). For a range write
  "200 to 300". Leave blank if the notice gives no pixel size.
- pixel_rule: the size wording, and whether it is exact, preferred, minimum or a range.
- name_date_on_photo: start with "Mandatory:" if a name and/or date must be printed on
  the photo, and say which; otherwise "Not required".
- spectacles / headwear / face_mask: e.g. "Allowed without glare", "Not permitted
  unless religious", "Not allowed".
- photo_recency: e.g. "Within 3 months".
- exact_passage: the sentence(s) quoted from the source.
- source_url: a full link (https://...) to the page or PDF you took it from.
- date_checked: YYYY-MM-DD.

Give me the CSV only, no commentary.
```

## How it goes in

Append the returned rows to `packages/exam-rules/research/delivery_2026_09_27/uploads.csv`, then re-run the DEC-114 pipeline (restore the two corpus JSONs and the trivia file first, so the merge starts from the committed state):

```bash
python scripts/import_tabular_delivery.py --delivery packages/exam-rules/research/delivery_2026_09_27 --out <scratch> --trivia packages/exam-rules/research/exam_trivia_2026.json
python scripts/merge_research_delivery.py --delivery <scratch>
python scripts/encode_exam_rules.py --specs packages/exam-rules/research/exam_photo_specs_2026.json --deliverables packages/exam-rules/research/exam_deliverables_2026.json --out examples/rules --report docs/EXAM_RULE_GAP_REGISTER.md
python scripts/generate_exam_facts.py
```
