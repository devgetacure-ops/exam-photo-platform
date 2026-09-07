# Deep research brief — per-examination facts for candidates

Copy everything below the line into the research tool. **Every list it needs is
inline**; nothing has to be attached.

---

## What this is for

An Indian exam-document preparation service shows a short carousel of facts on
each examination's page. The facts already there are derived from each
authority's own published upload rules — sizes, formats, rejection conditions —
so they are true by construction.

This brief is for the half that cannot be derived: **things a candidate would
find genuinely interesting or useful about the examination itself.**

The product's whole position is that it is more trustworthy than the coaching
sites and aggregators a candidate would otherwise read. **A single invented or
stale fact costs more than the entire feature is worth.** Everything below
follows from that.

## The one rule

**Every fact carries an official source URL and the date you read it. A fact
without both is not published — it is dropped.**

Not softened, not marked "approximately", not sourced to a news article.
Dropped. An empty carousel on one examination costs nothing; a confident wrong
statement costs the trust the product is built on.

## What to find

Aim for **3 to 6 facts per examination**. Fewer is fine. Nothing is fine.

**1. Scale.** How many candidates applied, registered or appeared, for a named
cycle. `"Over 2.4 million candidates registered for NEET (UG) 2025."` Source:
the authority's own press release, annual report, or PIB. This is the most
reliably available and the most interesting.

**2. The application process itself.** Things that surprise people, published
by the authority: that a one-time registration is reused across years, that a
correction window exists and when, that the fee differs by category, that an
application is only complete once a confirmation page is generated.

**3. What the authority tells candidates to bring or keep.** Admit card, photo
ID, the same photograph as the application, printouts. Published instructions
only.

**4. Structure worth knowing.** Number of papers, duration, that a paper is
computer-based, that there are multiple shifts with normalisation, how many
attempts are permitted.

**5. History, where the authority states it.** When the examination was first
held, that it replaced an earlier one, that a conducting body changed.

## What not to find

**Anything you cannot source to the authority.** No coaching sites, no
aggregators, no YouTube, no "commonly known".

**No live dates.** Do not state that applications open on a date, close on a
date, or that the examination is on a date — unless you attach the `cycle` it
belongs to and phrase it in the past. A stale deadline shown as current is the
one fact here that can make a candidate miss the examination entirely. `"For
the 2025 cycle the correction window ran for one week in March"` is fine.
`"Applications close on 15 March"` is not.

**No eligibility advice.** Age limits, qualification requirements, attempt
limits *as they apply to an individual*, reservation entitlements. A candidate
who relies on a wrong one loses a year. If eligibility is genuinely
interesting, state it as what the authority published for a named cycle and
nothing more.

**No difficulty, pass rates framed as difficulty, cut-offs, or predictions.**
Not our business and not verifiable.

**No advice of any kind.** Not "apply early", not "keep your photograph
handy". The facts speak; we do not counsel.

**Nothing about a named individual.** No toppers, no officials.

## Output

One JSON file, `exam_trivia_2026.json`:

```json
{
  "generated_at": "2026-09-20",
  "exams": {
    "neet-ug-2026": [
      {
        "kind": "volume",
        "text": "Over 2.4 million candidates registered for NEET (UG) 2025.",
        "source_url": "https://pib.gov.in/PressReleasePage.aspx?PRID=...",
        "source_title": "PIB release, Ministry of Education",
        "official_source": true,
        "as_of": "2026-09-20",
        "cycle": "2025",
        "confidence": 5
      }
    ]
  }
}
```

Field rules, enforced by the importer — an entry failing any of them is
**silently dropped**, so getting these right is the difference between research
that ships and research that does not:

| Field | Rule |
|---|---|
| `text` | One sentence. Plain. No adjectives doing persuasion. |
| `source_url` | Required. The authority's own domain, or PIB. |
| `official_source` | Must be `true`. There is no other accepted value. |
| `as_of` | Required. The date you read the source. |
| `cycle` | **Required** for `kind` of `window` or `deadline`. |
| `kind` | One of `volume`, `process`, `exam_day`, `structure`, `history`, `window`. |

Key each examination by the **exact id** in the table below. An unrecognised key
is reported as unmatched and shown to nobody, so it is research you paid for and
cannot use.

## The 52 examinations

| Examination | Key |
|---|---|
| Andhra Pradesh Teacher Eligibility Test | `andhra-pradesh-teacher-eligibility-test` |
| BSSC Second Inter-Level Combined Competitive Examination | `bssc-second-inter-level-combined-competitive-examination` |
| CBSE Classes IX/XI Registration 2025-26 | `cbse-classes-ix-xi-registration-2025-26` |
| CTET September 2026 | `ctet-september-2026` |
| CUET (PG) 2026 | `cuet-pg-2026` |
| CUET (UG) 2026 | `cuet-ug-2026` |
| Common Admission Test 2025 | `common-admission-test-2025` |
| GATE 2026 | `gate-2026` |
| GIC Assistant Manager 2024-25 | `gic-assistant-manager-2024-25` |
| IBPS CRP Customer Service Associates-XV | `ibps-crp-customer-service-associates-xv` |
| IBPS CRP PO/MT-XVI | `ibps-crp-po-mt-xvi` |
| IBPS CRP Regional Rural Banks-XIV | `ibps-crp-regional-rural-banks-xiv` |
| IBPS CRP Specialist Officers-XVI | `ibps-crp-specialist-officers-xvi` |
| ICAI Examination Portal Photograph (current portal scope) | `icai-examination-portal-photograph-current-portal-scope` |
| ICSI Student Registration / Examination Account Photograph | `icsi-student-registration-examination-account-photograph` |
| JEE (Main) 2026 | `jee-main-2026` |
| Joint CSIR-UGC NET | `joint-csir-ugc-net` |
| Karnataka Common Entrance Test 2026 | `karnataka-common-entrance-test-2026` |
| Karnataka PSC Current Recruitment Portal Photograph | `karnataka-psc-current-recruitment-portal-photograph` |
| Kerala Engineering Architecture Medical Entrance Examination | `kerala-engineering-architecture-medical-entrance-examination` |
| Kerala PSC One Time Registration Photograph | `kerala-psc-one-time-registration-photograph` |
| LIC Assistant Administrative Officers (Generalist) 2025 | `lic-assistant-administrative-officers-generalist-2025` |
| MPSC General Online Application Photograph Instruction | `mpsc-general-online-application-photograph-instruction` |
| Maharashtra Teacher Eligibility Test (MAHA TET) | `maharashtra-teacher-eligibility-test-maha-tet` |
| Management Aptitude Test 2026 | `management-aptitude-test-2026` |
| NABARD Grade A 2025 | `nabard-grade-a-2025` |
| NEET (UG) 2026 | `neet-ug-2026` |
| NIACL Administrative Officers 2025 | `niacl-administrative-officers-2025` |
| OSSSC Combined Recruitment Examination | `osssc-combined-recruitment-examination` |
| RBI Assistant - Panel Year 2025 | `rbi-assistant-panel-year-2025` |
| RBI Assistant - Panel Year 2025 (live photograph) | `rbi-assistant-panel-year-2025-live-photograph-live-capture` |
| RBI Officers in Grade B 2026 - prior-cycle official fallback | `rbi-officers-in-grade-b-2026-prior-cycle-official-fallback` |
| RPF Constable | `rpf-constable` |
| RPF Sub-Inspector | `rpf-sub-inspector` |
| RRB Level-1 Posts - CEN 08/2024 | `rrb-level-1-posts-cen-08-2024` |
| RRB Ministerial and Isolated Categories | `rrb-ministerial-and-isolated-categories` |
| RRB NTPC Graduate - CEN 05/2024 | `rrb-ntpc-graduate-cen-05-2024` |
| SBI Junior Associates 2025 | `sbi-junior-associates-2025` |
| SBI Probationary Officers 2025 | `sbi-probationary-officers-2025` |
| TNPSC Combined Civil Services Examination I (Group I) | `tnpsc-combined-civil-services-examination-i-group-i` |
| TNPSC Combined Civil Services Examination II (Group II/IIA) | `tnpsc-combined-civil-services-examination-ii-group-ii-iia` |
| TNPSC Combined Civil Services Examination IV (Group IV Services) | `tnpsc-combined-civil-services-examination-iv-group-iv-services` |
| TNPSC Combined Technical Services Examination 2025 | `tnpsc-combined-technical-services-examination-2025` |
| UGC-NET June 2026 | `ugc-net-june-2026` |
| UPSC CAPF (Assistant Commandants) Examination 2026 | `upsc-capf-assistant-commandants-examination-2026` |
| UPSC Civil Services Examination 2026 | `upsc-civil-services-examination-2026` |
| UPSC Combined Defence Services Examination (II) 2026 | `upsc-combined-defence-services-examination-ii-2026` |
| UPSC NDA & NA Examination (II) 2026 | `upsc-nda-na-examination-ii-2026` |
| WBJEE 2026 | `wbjee-2026` |
| WBPSC / WBCS Current Online Application Photograph | `wbpsc-wbcs-current-online-application-photograph` |
| West Bengal School Service Commission SLST Assistant Teacher Recruitment | `west-bengal-school-service-commission-slst-assistant-teacher-recruitment` |
| Xavier Aptitude Test | `xavier-aptitude-test` |

Four of these are **portal records rather than single examinations** — Karnataka
PSC, Kerala PSC, MPSC and WBPSC/WBCS describe a commission's application portal
across its recruitments. Facts about the commission and its portal fit them;
facts about one recruitment do not.

## Also hand back

`coverage.md`: which examinations you found nothing for, and where you looked.
A documented dead end stops us paying to search it twice, and finding nothing
official for a state commission is a perfectly good result.
