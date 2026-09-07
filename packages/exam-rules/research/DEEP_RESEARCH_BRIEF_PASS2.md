# Deep research brief — pass 2, remediation

Copy everything below the line into the research tool. Attach both zips from the
completion pass (`exam-deliverables.zip` and
`exam-upload-specifications-completion-2026-09-07.zip`) and the four original
research zips.

**Every list this brief needs is inline.** Last time an attachment did not arrive
and the run stalled at one record; that cannot happen again.

---

## Read this first

You did a completion pass on Indian examination upload specifications and
delivered 117 records. **The evidence discipline was right** — you refused to
promote secondary-source values even where that made your own numbers look
worse, you resolved both conflicts properly, and your checksums verified. Keep
all of that exactly as it is.

Four things came back short. This pass fixes them, and nothing else.

## The quality bar — your own work

Two deliveries arrived. The **1-record NEET (UG) 2026 record** from the first is
markedly better than the 117-record pass:

| | NEET record (pass 1) | Same exam in the 117-record pass |
|---|---:|---:|
| Deliverables listed | 18 | 5 |
| With a parsed file size | 13 | 0 |
| Rejection conditions | 8 | 0 |

**The NEET record is the standard. Apply that depth everywhere.** Going wide at
1.9 deliverables per examination produced records we cannot use; going deep on
one produced a record we can ship. Depth beats coverage here — an examination
done properly is worth more than five done thinly.

## Job 1 — five examinations are ONE field from usable (do these first)

Each of these has one blocking field verified and the other missing. One value
each unlocks the whole record. **This is the highest-value hour of the pass.**

| Examination | Has | Needs |
|---|---|---|
| MHT-CET 2026 | max file size | **allowed formats** |
| TNPSC Combined Civil Services Examination IV (Group IV Services) | max file size | **allowed formats** |
| Indian Navy Agniveer SSR/MR Recruitment | max file size | **allowed formats** |
| UPPSC One Time Registration Photograph | max file size | **allowed formats** |
| Kendriya Vidyalaya Sangathan Direct Recruitment Examination | allowed formats | **max file size** |

If an authority genuinely publishes a size without ever naming a format, say so
explicitly for that examination. That is a finding and we will record it as one.
Do not infer JPEG.

## Job 2 — rejection conditions: you returned zero

Your 117 records carry **no `rejection_conditions` at all**. Our existing
catalogue carries 204, and they are the half candidates actually fear — the
published statements about what gets an application thrown out.

For **every examination you touch in this pass**, capture the authority's own
published rejection statements, quoted verbatim, and attribute each to the
deliverable it names:

- "Applications with a blurred photograph will be rejected"
- "Photographs with coloured or dark backgrounds are liable to rejection"
- "Signature in capital letters will not be accepted"
- "Selfies are not accepted"

Rules:
- Quote them. Do not paraphrase or summarise.
- Attach each to the deliverable(s) it names — a signature condition is not a
  photograph condition. Where it names none, it is an application-wide condition.
- Where an authority publishes none, return an **empty list**. Do not write a
  sentence saying none was found; an empty list is the correct answer.

## Job 3 — 86 invented values across 24 live examinations

These are examinations candidates reach **today**, where we invented a plausible
number because none was found. Your last pass resolved 6 of 69. This is the most
commercially damaging gap we have and it is still open.

They are **not photograph values.** They are signature, thumb impression and
certificate values. The exact gaps:

| Examination | Deliverables and fields still needed |
|---|---|
| BPSC Current Recruitment Photograph Specification | Candidate signature [signature] -- format, max size, min size<br>Claim-supporting certificates [certificate_scan] -- max size |
| CUET (PG) 2026 | Candidate signature [signature] -- max size, min size<br>Category/PwD certificate [certificate_scan] -- max size |
| CUET (UG) 2026 | Candidate signature [signature] -- max size, min size<br>Category certificate [certificate_scan] -- max size<br>PwD certificate [certificate_scan] -- max size<br>Result-awaiting certificate [certificate_scan] -- max size |
| Common Admission Test 2025 | Candidate signature [signature] -- format, max size, min size<br>Category certificate [certificate_scan] -- max size<br>PwD certificate [certificate_scan] -- max size |
| GATE 2026 | Dyslexia certificate [certificate_scan] -- max size<br>SC/ST certificate [certificate_scan] -- max size<br>UDID/PwD certificate [certificate_scan] -- max size |
| IBPS CRP Customer Service Associates-XV | SSC/SSLC/Class 10 certificate [certificate_scan] -- max size<br>Scribe eligibility certificate [certificate_scan] -- max size |
| IBPS CRP PO/MT-XVI | SSC/SSLC/Class 10 certificate [certificate_scan] -- max size<br>Scribe eligibility certificate [certificate_scan] -- max size |
| IBPS CRP Regional Rural Banks-XIV | SSC/SSLC/Class 10 certificate [certificate_scan] -- max size<br>Scribe eligibility certificate [certificate_scan] -- max size |
| IBPS CRP Specialist Officers-XVI | SSC/SSLC/Class 10 certificate [certificate_scan] -- max size<br>Scribe eligibility certificate [certificate_scan] -- max size |
| ICAI Examination Portal Photograph (current portal scope) | Candidate signature [signature] -- max size, min size |
| ICSI Student Registration / Examination Account Photograph | Candidate signature [signature] -- format, max size, min size<br>Date-of-birth/Class X proof [certificate_scan] -- max size<br>Qualifying educational certificate [certificate_scan] -- max size |
| JEE (Main) 2026 | PwD/UDID certificate [certificate_scan] -- max size |
| Karnataka Common Entrance Test 2026 | Candidate signature [signature] -- format, max size, min size<br>Left thumb impression [thumb_impression] -- format, max size, min size<br>Parent/guardian signature [signature] -- format, max size, min size |
| Karnataka PSC Current Recruitment Portal Photograph | Candidate signature [signature] -- format, max size, min size<br>Claim-supporting certificates [certificate_scan] -- max size |
| Kerala PSC One Time Registration Photograph | Candidate signature [signature] -- format, max size, min size<br>Claim-supporting certificates [certificate_scan] -- max size |
| MPSC General Online Application Photograph Instruction | Candidate signature [signature] -- format, max size, min size<br>Claim-supporting certificates [certificate_scan] -- max size |
| Management Aptitude Test 2026 | Candidate signature [signature] -- format, max size, min size |
| NEET (UG) 2026 | **Mostly done in your pass-1 record.** Only: Left and right hand fingers and thumb impressions [thumb_impression] -- max size, min size |
| RRB Level-1 Posts - CEN 08/2024 | Candidate signature [signature] -- format, max size, min size<br>SC/ST certificate for free rail travel authority [certificate_scan] -- max size |
| RRB NTPC Graduate - CEN 05/2024 | Candidate signature [signature] -- format, max size, min size<br>SC/ST certificate for free rail travel authority [certificate_scan] -- max size |
| TNPSC Combined Technical Services Examination 2025 | Candidate signature [signature] -- format, max size, min size<br>Supporting certificates for claims [certificate_scan] -- max size |
| UGC-NET June 2026 | PwD certificate [certificate_scan] -- max size |
| WBJEE 2026 | Candidate signature [signature] -- format, max size, min size |
| WBPSC / WBCS Current Online Application Photograph | Candidate signature [signature] -- format, max size, min size<br>Claim-supporting certificates [certificate_scan] -- max size |

Note the four IBPS examinations share a portal and will likely share values —
but **verify each against its own notification**, and record them separately.

## Job 4 — five examinations your pass would remove from service

These five encode in our live catalogue today on secondary-source values. You
correctly declined to promote those values, but found nothing to replace them.
As things stand, adopting your pass **removes five working examinations**.

- BPSC Current Recruitment Photograph Specification
- GIC Assistant Manager 2024-25
- Karnataka Common Entrance Test 2026
- Karnataka PSC Current Recruitment Portal Photograph
- WBPSC / WBCS Current Online Application Photograph

For each, one of two outcomes, and **both are acceptable**:

1. An official value, sourced properly. Best case.
2. An explicit finding: **"the authority publishes no numeric upload
   specification; the values in circulation are secondary-source only."**

Outcome 2 is genuinely useful — it tells us the gap is real rather than
unresearched, and we will change what we show candidates accordingly. What is
not acceptable is silence, because silence looks identical to not having looked.

## Job 5 — the long tail

**87 of your 117 records have neither blocking field.** You can identify them
from your own output: every record in `exam_photo_specs_2026.json` where both
`file_size.published_maximum` and `formats.allowed_formats` are `not_found`.

Work them in the candidate-volume order your reconstructed worklist already
established, and **apply the NEET depth**. We would rather have 20 examinations
done to that standard than 87 done thinly.

**One clarification about `no_usable_photo_upload_specifications.md`.** Its 92
entries are every record this pass did not fully resolve — the 87 above plus
the 5 in Job 1. It records *"not established in this pass"*, which is not the
same as *"the authority publishes nothing"*. It is a worklist, not a set of
conclusions, and **nothing in it is closed**.

Where you do conclude an authority publishes nothing, say so in those words. We
treat that as a finding and stop paying to look for it. Both outcomes are
wanted; only silence is not.

Even where a photograph rule genuinely does not exist, **still capture that
examination's deliverables and rejection conditions** — an examination with no
photograph specification may well have a signature specification we can use.

## Do not redo

- **The 25 records where both blocking fields are already verified.** Settled.
- **The two conflict decisions.** RPSC (live capture, no numeric size) and
  Indian Army Agniveer online upload (neither secondary figure promoted) were
  both resolved correctly. Leave them.
- **The four SSC examinations** — CGL 2026, CHSL 2025, MTS 2025, Constable GD
  2025. They capture live; no upload specification exists.

## Output

Same two files, same schema, same field paths as your completion pass — that
format was correct and we can read it. Plus `coverage.md` in the style of your
pass-1 report, which was excellent: what you resolved, what you could not, and
**where you looked** for each failure.

Two rules about the shape of what you return:

1. **Never return a shorter deliverable list than the application actually has.**
   If an examination asks for eleven files, list eleven, even where ten have no
   published specification. A deliverable recorded with `not_found` values is
   information; a deliverable omitted is a silent gap we cannot see.
2. **`not_found` remains the correct answer** whenever evidence does not
   establish a value. Everything in this brief asks you to look harder, and
   nothing in it asks you to lower that bar. A guessed value is worse than a gap,
   because a gap is visible and a guess is not.
