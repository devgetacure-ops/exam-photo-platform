# Worth knowing — curation of the 2026-09-13 research delivery

Generated alongside `exam_trivia_2026.json`. The research delivery held 169 facts
for 132 examinations. Every source page was fetched and every fact checked
against it before any sentence was written (DEC-082).

- **Published: 127 facts for 105 examinations** — 37 from the conducting authority or a government publisher, 90 from a named publication.
- **Dropped: 42**, each listed below with the reason.

Every published sentence was rewritten from the passage kept in its `source_quote`,
and a check refuses to write the file if a figure in a sentence is not in its passage
or a passage is not on its page. Pages the fetcher could not reach were read in a
browser; those passages are the rendered page text.

## Dropped

| Examination | Reason |
|---|---|
| `all-india-sainik-schools-entrance-examination` | no publisher mapping for cdnbbsr.s3waas.gov.in |
| `appsc-forest-beat-officer-assistant-beat-officer-2025` | file host or clone site, not a publisher |
| `bits-admission-test` | the figure is not on the page; the match was an unrelated INR 1.5 lakh grant |
| `bpsc-online-application` | figure or wording not found on the page |
| `bpsc-online-application` | figure or wording not found on the page |
| `bpsc-teacher-recruitment-examination-tre` | figure or wording not found on the page |
| `cbse-classes-ix-xi-registration-2025-26` | file host or clone site, not a publisher |
| `cg-vyapam-pre-b-ed-entrance-examination` | page unavailable |
| `cuet-pg-2026` | the pattern is not in the page text |
| `cuet-pg-2026` | the marking scheme is not in the page text |
| `gate-2026` | the format sentence is not in the page text |
| `gujarat-police-lokrakshak-recruitment` | figure or wording not found on the page |
| `gujarat-police-psi-recruitment` | figure or wording not found on the page |
| `ibps-crp-po-mt-xvi` | file host or clone site, not a publisher |
| `ibps-crp-po-mt-xvi` | file host or clone site, not a publisher |
| `ibps-crp-regional-rural-banks-xiv` | the mains table could not be read from the PDF text |
| `icsi-student-registration-and-examination` | figure or wording not found on the page |
| `icsi-student-registration-and-examination` | figure or wording not found on the page |
| `jawahar-navodaya-vidyalaya-selection-test-class-vi` | no publisher mapping for cbseit.in |
| `jee-advanced-2026` | the language-toggle answer is not in the page text |
| `jee-main-2026` | the paper pattern is not in the page text |
| `jharkhand-police-constable-recruitment` | a count of cancelled applications, not something a candidate can use |
| `karnataka-psc-online-application` | the source is a garbled copy of a KPSC notice |
| `kendriya-vidyalaya-sangathan-direct-recruitment-examination` | no publisher mapping for www.education.gov.in |
| `mp-police-constable-recruitment-test` | an unlabelled statistical table; which column is registered and which appeared cannot be told |
| `mp-primary-school-teacher-eligibility-test` | page unavailable |
| `neet-ug-2026` | the subject split is not in the page text |
| `rbi-officers-in-grade-b-2026` | file host or clone site, not a publisher |
| `rrb-ntpc-graduate-cen-05-2024` | no publisher mapping for www.rrbcdg.gov.in |
| `rrb-ntpc-graduate-cen-05-2024` | no publisher mapping for www.rrbkolkata.gov.in |
| `ssc-combined-graduate-level-examination-2026-live-capture` | the pattern is not in the page text |
| `ssc-combined-graduate-level-examination-2026-live-capture` | the sections are not in the page text |
| `ssc-multi-tasking-staff-and-havaldar-examination-2025-live-capture` | the page text is not in English and the claim cannot be matched |
| `ssc-multi-tasking-staff-and-havaldar-examination-2025-live-capture` | the page text is not in English and the claim cannot be matched |
| `tnpsc-combined-civil-services-examination-i-group-i` | the figure is not in the page text |
| `tnpsc-combined-technical-services-examination-2025` | the paper structure is not in the extracted text |
| `upsc-capf-assistant-commandants-examination-2026` | file host or clone site, not a publisher |
| `upsc-capf-assistant-commandants-examination-2026` | figure or wording not found on the page |
| `upsc-engineering-services-examination` | figure or wording not found on the page |
| `wbpsc-wbcs-online-application` | page unavailable |
| `wbpsc-wbcs-online-application` | page unavailable |
| `west-bengal-primary-teacher-eligibility-test` | no publisher mapping for wbbpe.wb.gov.in |

## The 2026-09-15 delivery (the 27 examinations with nothing to show)

The owner's research held 65 facts for the 27 examinations the first curation
left empty, keyed by their pre-audit ids (mapped through
`exam_id_renames_2026_09_14.json`). It carried a summary of each source but no
passage, so every page was downloaded and read again (DEC-095).

- **Published: 35 facts for 17 examinations**, each cut from its page between a
  start and an end phrase and checked by `scripts/verify_fact_passages.py`
  (`--as-of 2026-09-15`: 35 checked, 0 failed). Each keeps a kind the card
  shows (volume, process, structure, history, window).
- **Corrected**: BPSC TRE 3.0's vacancies are 87,709 on the page, not "roughly
  87,700".
- **Merged: 2**: WBPSC's two portal facts are one sentence from one page, and
  West Bengal TET's format and structure facts are one sentence from one table.
- **Dropped: 28.** Ten examinations still have nothing to show.

| Examination | Reason |
|---|---|
| `all-india-sainik-schools-entrance-examination` (2) | the cited bulletin returns 404 |
| `bpsc-online-application` | the portal page shows only a registration form, not the claim |
| `cbse-classes-ix-xi-registration-2025-26` | the circular is a scanned image with no text |
| `gujarat-police-lokrakshak-recruitment` (2) | the cited rules PDF returns 404 |
| `gujarat-police-psi-recruitment` | the 472 figure is not on the page; it matched only inside 12472 |
| `gujarat-police-psi-recruitment` | the publisher refused the request (403) |
| `icsi-student-registration-and-examination` (2) | the cited FAQ returns 404 |
| `jawahar-navodaya-vidyalaya-selection-test-class-vi` (3) | the cited annual report returns 404 |
| `jharkhand-police-constable-recruitment` | the publisher refused the request |
| `jharkhand-police-constable-recruitment` | confidence 3, an aggregator's summary |
| `karnataka-psc-online-application` | a notice mirrored on a file host, not a publisher |
| `karnataka-psc-online-application` | confidence 3, an aggregator's summary |
| `mp-primary-school-teacher-eligibility-test` (2) | the publisher refused the request (403) |
| `rrb-ntpc-graduate-cen-05-2024` (3) | rrbcdg.gov.in serves its home page for the PDF |
| `tnpsc-combined-civil-services-examination-i-group-i` (2) | the press releases' Tamil text extracts garbled; only the figures can be read |
| `tnpsc-combined-civil-services-examination-i-group-i` | Group I cannot be picked out of the results table |
| `tnpsc-combined-technical-services-examination-2025` (2) | the 2025 streams and dates are not on the cited pages |
| `upsc-capf-assistant-commandants-examination-2026` | the cited notification URL serves UPSC's home page |
