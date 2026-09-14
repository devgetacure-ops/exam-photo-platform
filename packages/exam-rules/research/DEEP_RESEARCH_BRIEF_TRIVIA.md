# Research prompt — "Worth knowing" facts for every examination

**For the owner, not the research tool.** Copy everything below the line into
the research AI. It is self-contained: the examination list, the rules and the
output format are all inline. If the tool cannot cover 131 examinations
in one run, run it again with the same prompt and add "continue from the
examinations listed under Not reached in the previous coverage.md". Put the JSON
it returns somewhere outside the repository first: each fact is checked against
its page and rewritten from its passage before it is committed as
`packages/exam-rules/research/exam_trivia_2026.json` (see
`exam_trivia_2026_curation.md`). The importer (`scripts/generate_exam_facts.py`,
DEC-078 and DEC-082) then drops any entry that breaks the rules below.

---

## Your task

You already know these examinations. You researched their application upload
rules — photograph, signature, thumb impression, declaration and document
specifications — for an Indian exam-document preparation service. This task
uses that familiarity for something different, so **do not research upload
rules again**. The service already shows every one of those on the
examination's page.

Find short, verifiable facts **about each examination itself** that a candidate
would find genuinely useful or interesting. They appear in a panel called
"Worth knowing" on that examination's page, one sentence at a time, each with a
link to where it came from.

## Why the bar is this high

The service's whole position is that it can be trusted more than the coaching
sites and aggregators a candidate would otherwise read. **One invented or
out-of-date fact costs more than the entire panel is worth.** A candidate who
knows their examination well and spots one wrong sentence stops trusting the
measurements beside it. An examination with no facts costs nothing.

## The one rule

**Every fact comes back with the direct URL, the name of whoever published
it, the date you read it, and the exact passage it rests on, copied from the
page. A fact missing any of these is not published — it is dropped.** Not
softened, not marked "approximately". Dropped. Every figure in your sentence
must appear in that passage, and the passage must be on the page at that URL:
both are checked by machine against the page itself.

**Prefer the official source:** the conducting authority's own website, or a
notification, information bulletin, brochure or press note it published; a
government domain (`gov.in`, `nic.in`, a state government's domain); the Press
Information Bureau (`pib.gov.in`); the Gazette of India or a state gazette;
answers given in Parliament (`sansad.in`). Mark these `official_source: true`.

**A reputable publication is also accepted** (DEC-082): a national or regional
news organisation, or an established education publisher. Mark these
`official_source: false`. The site names the publisher beside the fact — "Reported
by The Indian Express" — so it is never read as the examination's own word.
An IIT or university learning platform that is not the conducting body is a
publication, not an official source.

**Never a source:** YouTube, Scribd, flipbook or document-upload hosts, cloud
storage links, Telegram, social media, forums, Wikipedia, and sites that copy
another site's content. Nobody stands behind what they carry.

## What to look for

Aim for **3 to 6 facts per examination**. Fewer is fine. None is fine.

| `kind` | What it covers | Shape of a sentence |
|---|---|---|
| `volume` | How many candidates registered, applied or appeared, **for a named cycle**, using the source's own verb and number | "Over N lakh candidates registered for [examination] [cycle]." |
| `process` | How applying works, as the authority publishes it: one-time registration reused across recruitments, a correction window existing, an application being complete only once a confirmation page is generated, the stages a selection has | "An application is complete only after the confirmation page is generated." |
| `exam_day` | What the authority tells candidates to bring, keep or not bring | "Candidates must bring the same photograph that was uploaded with the application." |
| `structure` | Number of papers, computer-based or pen-and-paper, duration, shifts and normalisation, languages offered, negative marking — **for a named cycle** | "For the [cycle] cycle the examination was computer-based and held in N shifts." |
| `history` | When it was first held, what it replaced, a change of conducting body — **only where an official source states it** | "The examination was first held in [year]." |
| `window` | Something that happened in a time window, **always past tense, always with its cycle** | "For the [cycle] cycle the correction window was open for N days." |

The right-hand column shows the shape of a sentence. **It is not a fact**;
every figure comes from a source you read.

## What never to include

- **Upload rules** — file sizes, formats, dimensions, photograph or signature
  requirements. Already shown on the page.
- **Live dates.** Never that applications open, close, or that the examination
  is held on a date, as though it were current. Anything time-bound is past
  tense with its cycle named. A stale deadline shown as current is the one
  fact here that can make a candidate miss their examination. Do not use the
  kind `deadline`.
- **Eligibility**, as it applies to a person: age limits, qualifications,
  attempt limits, reservation or relaxation entitlements. A candidate who acts
  on a wrong one loses a year.
- **Fee amounts.** They change between cycles and candidates act on them.
- **Difficulty, cut-offs, pass rates, results, rankings or predictions.**
- **Any figure you calculated.** No percentages you worked out, no "about" or
  "nearly" the source did not say, no comparisons such as "one of the largest"
  unless the source says exactly that.
- **Advice of any kind.** Not "apply early", not "keep your documents ready".
  The facts speak for themselves.
- **Named individuals** — toppers, officials, anyone.

## Writing each fact

- **One sentence, at most 220 characters**, in plain English. No adjectives
  doing persuasion.
- **Numbers exactly as the source prints them**, including "lakh" and "crore"
  where the source uses them.
- **Name the cycle inside the sentence** whenever the fact belongs to a cycle
  or year.
- **Call the examination what its authority calls it.**
- If the source is in Hindi or a regional language, **translate faithfully**,
  keep the original sentence in `source_quote`, and add "(translated from
  Hindi)" or the language to `source_title`.

## Records that are portals, not single examinations

Some records describe a commission's application portal or one-time
registration rather than one examination — their names say "Portal", "One
Time Registration", "Online Application" or "Registration". For those, facts
about the commission and how its portal works fit; a fact about one particular
recruitment does not. Several records name a specific cycle, such as a 2026
sitting: a fact from an earlier cycle is fine as long as that cycle is named in
the sentence.

## Output: two files

### 1. `exam_trivia_2026.json`

```json
{
  "generated_at": "YYYY-MM-DD",
  "exams": {
    "neet-ug-2026": [
      {
        "kind": "volume",
        "text": "One sentence, as described above.",
        "source_url": "https://the-direct-page-or-pdf",
        "source_title": "What the source is, and the page number for a PDF",
        "source_quote": "The exact passage copied from the page.",
        "publisher": "Who published it, as the site should name them",
        "official_source": true,
        "as_of": "YYYY-MM-DD",
        "cycle": "2025",
        "confidence": 5
      }
    ]
  }
}
```

Every entry is checked on import. **One that fails any rule below is dropped
without a warning**, so these rules are the difference between research that
ships and research that is thrown away:

| Field | Rule |
|---|---|
| key | The **exact key** from the table below. A key that matches no examination is shown to nobody. |
| `kind` | One of `volume`, `process`, `exam_day`, `structure`, `history`, `window`. |
| `text` | The fact, one sentence, as described above. |
| `source_url` | **Required.** The direct page or PDF, not a home page. |
| `source_title` | What the source is, such as "Information bulletin 2025, page 14". |
| `source_quote` | **Required.** The passage copied exactly from the page, long enough to contain every figure in `text`. Not shown to candidates; it is how each fact is checked, by machine, against the page. |
| `publisher` | **Required.** The authority or publication, as it should be named on the site: "Press Information Bureau", "The Indian Express". |
| `official_source` | `true` for the conducting authority or a government publisher; `false` for a publication. |
| `as_of` | **Required.** The date you read the source, `YYYY-MM-DD`. |
| `cycle` | **Required** for `window`, and for any fact about a particular year or cycle. |
| `confidence` | 1 to 5. 5 means the source states it in so many words. **Anything below 4, leave out.** |

Leave out examinations you found nothing for rather than writing an empty
list. Return valid JSON only, UTF-8, with no comments inside it.

### 2. `coverage.md`

- **Found nothing:** each examination with no facts, and where you looked. A
  documented dead end stops the same search being paid for twice, and finding
  nothing official for a state commission is a perfectly good result.
- **Not reached:** any examination you did not get to, in table order, so a
  later run can continue from exactly there.
- **Doubts:** anything you left out because two official sources disagreed.

## The examinations (131)

Work through them in this order. The "also called" column is there to help you
recognise each one; the key is what goes in the JSON.

| Examination | Conducting body | Also called | Key |
|---|---|---|---|
| All India Sainik Schools Entrance Examination | National Testing Agency | AISSEE, Sainik School Entrance | `all-india-sainik-schools-entrance-examination` |
| Andhra Pradesh Teacher Eligibility Test | Department of School Education Andhra Pradesh | AP TET | `andhra-pradesh-teacher-eligibility-test` |
| AP Mega DSC Teacher Recruitment | Government of Andhra Pradesh | AP DSC, Mega DSC, AP Teacher Recruitment | `ap-mega-dsc-teacher-recruitment` |
| AP POLYCET | State Board of Technical Education and Training Andhra Pradesh | POLYCET, AP Polytechnic | `ap-polycet` |
| APPSC Forest Beat Officer / Assistant Beat Officer 2025 | Andhra Pradesh Public Service Commission | APPSC FBO, AP Forest Beat Officer | `appsc-forest-beat-officer-assistant-beat-officer-2025` |
| APPSC Group I Services Examination | Andhra Pradesh Public Service Commission | APPSC Group 1, AP Group I | `appsc-group-i-services-examination` |
| APPSC Group II Services Examination | Andhra Pradesh Public Service Commission | APPSC Group 2, AP Group II | `appsc-group-ii-services-examination` |
| Assam Direct Recruitment Grade III | State Level Recruitment Commission Assam | ADRE Grade III, Assam ADRE, Assam Grade 3 | `assam-direct-recruitment-grade-iii` |
| Assam Direct Recruitment Grade IV | State Level Recruitment Commission Assam | ADRE Grade IV, Assam Grade 4 | `assam-direct-recruitment-grade-iv` |
| Bihar B.Ed Common Entrance Test | Lalit Narayan Mithila University / Bihar CET-B.Ed | Bihar BEd CET, Bihar BEd | `bihar-b-ed-common-entrance-test` |
| Bihar D.El.Ed Joint Entrance Examination | Bihar School Examination Board | Bihar DElEd, BSEB DElEd | `bihar-d-el-ed-joint-entrance-examination` |
| Bihar Police Constable Recruitment | Central Selection Board of Constable, Bihar | Bihar Police, Bihar Police Constable, CSBC Bihar Police | `bihar-police-constable-recruitment` |
| Bihar Secondary Teacher Eligibility Test | Bihar School Examination Board | Bihar STET, BSEB STET, STET Bihar | `bihar-secondary-teacher-eligibility-test` |
| BITS Admission Test | Birla Institute of Technology and Science Pilani | BITSAT, BITS Pilani | `bits-admission-test` |
| BPSC Online Application | Bihar Public Service Commission | BPSC, Bihar PSC | `bpsc-online-application` |
| BPSC Teacher Recruitment Examination (TRE) | Bihar Public Service Commission | BPSC TRE, Bihar Teacher Recruitment, BPSC Teacher | `bpsc-teacher-recruitment-examination-tre` |
| BSSC Second Inter-Level Combined Competitive Examination | Bihar Staff Selection Commission | BSSC Inter Level, Bihar SSC Inter Level | `bssc-second-inter-level-combined-competitive-examination` |
| CBSE Classes IX/XI Registration 2025-26 | Central Board of Secondary Education | CBSE Registration, CBSE Class 9 Registration, CBSE Class 11 Registration | `cbse-classes-ix-xi-registration-2025-26` |
| CG Vyapam Pre-B.Ed Entrance Examination | Chhattisgarh Professional Examination Board | CG Pre BEd, Vyapam Pre BEd, CG Vyapam BEd | `cg-vyapam-pre-b-ed-entrance-examination` |
| Common Admission Test 2025 | Indian Institutes of Management | CAT 2025, CAT, IIM CAT | `common-admission-test-2025` |
| CTET September 2026 | Central Board of Secondary Education | Central Teacher Eligibility Test, CTET | `ctet-september-2026` |
| CUET (PG) 2026 | National Testing Agency | CUET PG, Common University Entrance Test PG | `cuet-pg-2026` |
| CUET (UG) 2026 | National Testing Agency | CUET UG, CUET, Common University Entrance Test | `cuet-ug-2026` |
| Delhi Police Constable (Executive) | Staff Selection Commission / Delhi Police | Delhi Police Constable, Delhi Police | `delhi-police-constable-executive` |
| DSSSB Recruitment Examinations | Delhi Subordinate Services Selection Board | DSSSB, Delhi SSSB | `dsssb-recruitment-examinations` |
| GATE 2026 | IIT Guwahati | Graduate Aptitude Test in Engineering, GATE | `gate-2026` |
| GIC Assistant Manager 2024-25 | General Insurance Corporation of India | GIC AM | `gic-assistant-manager-2024-25` |
| Gujarat Police Lokrakshak Recruitment | Gujarat Police Recruitment Board | Gujarat Lokrakshak, LRD, Gujarat Police Constable | `gujarat-police-lokrakshak-recruitment` |
| Gujarat Police PSI Recruitment | Gujarat Police Recruitment Board | Gujarat PSI, Gujarat Police Sub Inspector | `gujarat-police-psi-recruitment` |
| GUJCET | Gujarat Secondary and Higher Secondary Education Board | Gujarat CET, Gujarat Common Entrance Test | `gujcet` |
| Haryana CET Group C | Haryana Staff Selection Commission | HSSC CET Group C, Haryana Group C | `haryana-cet-group-c` |
| Haryana Teacher Eligibility Test | Board of School Education Haryana | HTET, Haryana TET | `haryana-teacher-eligibility-test` |
| HSSC CET Group D | Haryana Staff Selection Commission | Haryana CET Group D, HSSC Group D | `hssc-cet-group-d` |
| IBPS CRP Customer Service Associates-XV | Institute of Banking Personnel Selection | IBPS Clerk, IBPS CSA, IBPS Clerical | `ibps-crp-customer-service-associates-xv` |
| IBPS CRP PO/MT-XVI | Institute of Banking Personnel Selection | IBPS PO, IBPS PO MT, IBPS CRP PO | `ibps-crp-po-mt-xvi` |
| IBPS CRP Regional Rural Banks-XIV | Institute of Banking Personnel Selection | IBPS RRB, IBPS Regional Rural Banks | `ibps-crp-regional-rural-banks-xiv` |
| IBPS CRP Specialist Officers-XVI | Institute of Banking Personnel Selection | IBPS SO, IBPS Specialist Officer | `ibps-crp-specialist-officers-xvi` |
| ICAI Examination Portal | Institute of Chartered Accountants of India | ICAI, CA, CA Foundation, CA Intermediate | `icai-examination-portal` |
| ICSI Student Registration and Examination | Institute of Company Secretaries of India | ICSI, CS, Company Secretary | `icsi-student-registration-and-examination` |
| Indian Air Force Agniveervayu Recruitment | Indian Air Force | Agniveervayu, IAF Agniveer, Air Force Agniveer | `indian-air-force-agniveervayu-recruitment` |
| Indian Army Agniveer CEE 2025-26 - online upload | Indian Army | Agniveer, Army Agniveer, Agniveer CEE, Agnipath | `indian-army-agniveer-cee-2025-26-online-upload` |
| Indian Army Agniveer Recruitment | Indian Army | Agniveer, Army Agniveer, Agnipath | `indian-army-agniveer-recruitment` |
| Jawahar Navodaya Vidyalaya Selection Test Class VI | Navodaya Vidyalaya Samiti / CBSE | JNVST, Navodaya Class 6, Navodaya Vidyalaya Entrance | `jawahar-navodaya-vidyalaya-selection-test-class-vi` |
| JEE (Advanced) 2026 | Joint Admission Board / IIT Roorkee | JEE Advanced, JEE Adv, IIT JEE | `jee-advanced-2026` |
| JEE (Main) 2026 | National Testing Agency | JEE Main, JEE, JEE Mains, Joint Entrance Examination Main | `jee-main-2026` |
| Jharkhand Police Constable Recruitment | Jharkhand Staff Selection Commission | Jharkhand Police, JSSC Constable | `jharkhand-police-constable-recruitment` |
| JKSSB Police Constable Recruitment | Jammu & Kashmir Services Selection Board | JKSSB Constable, JK Police Constable | `jkssb-police-constable-recruitment` |
| Joint CSIR-UGC NET | National Testing Agency / CSIR | CSIR NET, CSIR UGC NET | `joint-csir-ugc-net` |
| Joint Entrance Examination Council Uttar Pradesh Polytechnic Entrance | Joint Entrance Examination Council Uttar Pradesh | JEECUP, UP Polytechnic | `joint-entrance-examination-council-uttar-pradesh-polytechnic-entrance` |
| JSSC Combined Graduate Level Examination | Jharkhand Staff Selection Commission | JSSC CGL, Jharkhand CGL | `jssc-combined-graduate-level-examination` |
| Karnataka Common Entrance Test 2026 | Karnataka Examinations Authority | KCET 2026, KCET, Karnataka CET | `karnataka-common-entrance-test-2026` |
| Karnataka PSC Online Application | Karnataka Public Service Commission | KPSC, Karnataka PSC | `karnataka-psc-online-application` |
| Karnataka Teacher Eligibility Test | School Education Department Karnataka | KARTET, Karnataka TET | `karnataka-teacher-eligibility-test` |
| Kendriya Vidyalaya Sangathan Direct Recruitment Examination | Kendriya Vidyalaya Sangathan | KVS, KVS Recruitment, Kendriya Vidyalaya | `kendriya-vidyalaya-sangathan-direct-recruitment-examination` |
| Kerala Engineering Architecture Medical Entrance Examination | Commissioner for Entrance Examinations Kerala | KEAM, Kerala KEAM | `kerala-engineering-architecture-medical-entrance-examination` |
| Kerala PSC One Time Registration | Kerala Public Service Commission | Kerala PSC, KPSC Kerala | `kerala-psc-one-time-registration` |
| LIC Assistant Administrative Officers (Generalist) 2025 | Life Insurance Corporation of India | LIC AAO, LIC Assistant Administrative Officer | `lic-assistant-administrative-officers-generalist-2025` |
| MAH MBA/MMS CET | State Common Entrance Test Cell Maharashtra | MAH MBA CET, MBA CET, MAH CET MBA | `mah-mba-mms-cet` |
| Maharashtra Police Recruitment | Maharashtra Police | Maharashtra Police, Maharashtra Police Constable | `maharashtra-police-recruitment` |
| Maharashtra Teacher Eligibility Test (MAHA TET) | Maharashtra State Council of Examination | MAHATET, Maharashtra TET | `maharashtra-teacher-eligibility-test-maha-tet` |
| Management Aptitude Test 2026 | All India Management Association | MAT 2026, MAT, AIMA MAT | `management-aptitude-test-2026` |
| MHT-CET 2026 | State Common Entrance Test Cell, Maharashtra | Maharashtra Common Entrance Test, MHT CET, MHCET | `mht-cet-2026` |
| MP Patwari Recruitment Examination | Madhya Pradesh Employees Selection Board | MP Patwari, MPESB Patwari, Madhya Pradesh Patwari | `mp-patwari-recruitment-examination` |
| MP Police Constable Recruitment Test | Madhya Pradesh Employees Selection Board | MP Police, MP Police Constable, MPESB Constable | `mp-police-constable-recruitment-test` |
| MP Primary School Teacher Eligibility Test | Madhya Pradesh Employees Selection Board | MP TET, MPTET Primary, MP Varg 3 | `mp-primary-school-teacher-eligibility-test` |
| MPSC Online Application | Maharashtra Public Service Commission | MPSC, Maharashtra PSC | `mpsc-online-application` |
| NABARD Grade A 2025 | National Bank for Agriculture and Rural Development | NABARD Grade A, NABARD Assistant Manager | `nabard-grade-a-2025` |
| NEET (UG) 2026 | National Testing Agency | NEET UG, NEET, National Eligibility cum Entrance Test | `neet-ug-2026` |
| NEET-PG | National Board of Examinations in Medical Sciences | — | `neet-pg` |
| NIACL Administrative Officers 2025 | The New India Assurance Company Limited | NIACL AO, New India Assurance AO | `niacl-administrative-officers-2025` |
| Odisha Joint Entrance Examination (OJEE) | OJEE Committee | OJEE, Odisha JEE | `odisha-joint-entrance-examination-ojee` |
| OSSSC Combined Recruitment Examination | Odisha Sub-ordinate Staff Selection Commission | OSSSC, Odisha SSSC | `osssc-combined-recruitment-examination` |
| Rajasthan CET Graduate Level | Rajasthan Staff Selection Board | Rajasthan CET Graduate, RSSB CET Graduate Level | `rajasthan-cet-graduate-level` |
| Rajasthan CET Senior Secondary Level | Rajasthan Staff Selection Board | Rajasthan CET, Rajasthan CET 12th Level, RSSB CET Senior Secondary | `rajasthan-cet-senior-secondary-level` |
| Rajasthan Eligibility Examination for Teachers (REET) | Board of Secondary Education Rajasthan | REET, Rajasthan TET | `rajasthan-eligibility-examination-for-teachers-reet` |
| Rajasthan Grade IV Recruitment | Rajasthan Staff Selection Board | Rajasthan Grade 4, RSSB Grade IV, RSMSSB Grade IV | `rajasthan-grade-iv-recruitment` |
| Rajasthan Patwari Recruitment | Rajasthan Staff Selection Board | Rajasthan Patwari, RSSB Patwari | `rajasthan-patwari-recruitment` |
| Rajasthan Police Constable Recruitment | Rajasthan Police | Rajasthan Police, Rajasthan Police Constable | `rajasthan-police-constable-recruitment` |
| Rajasthan Pre-D.El.Ed Examination (BSTC) | Vardhman Mahaveer Open University / designated authority | BSTC, Rajasthan BSTC, Rajasthan Pre DElEd | `rajasthan-pre-d-el-ed-examination-bstc` |
| Rajasthan Pre-Teacher Education Test | Rajasthan PTET conducting university | PTET, Rajasthan PTET | `rajasthan-pre-teacher-education-test` |
| RBI Assistant - Panel Year 2025 | Reserve Bank of India | RBI Assistant | `rbi-assistant-panel-year-2025` |
| RBI Officers in Grade B 2026 | Reserve Bank of India | RBI Grade B, RBI Officer Grade B | `rbi-officers-in-grade-b-2026` |
| RPF Constable | Railway Protection Force / RRB | RPF, Railway Protection Force Constable | `rpf-constable` |
| RPF Sub-Inspector | Railway Protection Force / RRB | RPF SI, Railway Protection Force Sub Inspector | `rpf-sub-inspector` |
| RPSC Online Application | Rajasthan Public Service Commission | RPSC, Rajasthan PSC | `rpsc-online-application` |
| RRB JE/DMS/CMA | Railway Recruitment Boards | RRB JE, RRB Junior Engineer, Railway Junior Engineer | `rrb-je-dms-cma` |
| RRB Level-1 Posts - CEN 08/2024 | Railway Recruitment Boards | RRB Group D, Railway Group D, RRB Level 1 | `rrb-level-1-posts-cen-08-2024` |
| RRB Ministerial and Isolated Categories | Railway Recruitment Boards | RRB Ministerial | `rrb-ministerial-and-isolated-categories` |
| RRB NTPC Graduate - CEN 05/2024 | Railway Recruitment Boards | RRB NTPC, NTPC, Railway NTPC | `rrb-ntpc-graduate-cen-05-2024` |
| RRB Paramedical Categories | Railway Recruitment Boards | RRB Paramedical, Railway Paramedical | `rrb-paramedical-categories` |
| RRB Section Controller | Railway Recruitment Boards | Railway Section Controller | `rrb-section-controller` |
| RRB Technician | Railway Recruitment Boards | Railway Technician | `rrb-technician` |
| SBI Junior Associates 2025 | State Bank of India | SBI Clerk, SBI Junior Associate, SBI JA | `sbi-junior-associates-2025` |
| SBI Probationary Officers 2025 | State Bank of India | SBI PO, SBI Probationary Officer | `sbi-probationary-officers-2025` |
| SSC Combined Graduate Level Examination 2026 | Staff Selection Commission | SSC CGL, CGL | `ssc-combined-graduate-level-examination-2026-live-capture` |
| SSC Combined Higher Secondary (10+2) Level Examination 2025 | Staff Selection Commission | SSC CHSL, CHSL, SSC 10+2 | `ssc-combined-higher-secondary-10-2-level-examination-2025-live-capture` |
| SSC Constable (GD) Examination 2025 | Staff Selection Commission | SSC GD, SSC Constable GD, GD Constable | `ssc-constable-gd-examination-2025-live-capture` |
| SSC Junior Engineer Examination | Staff Selection Commission | SSC JE, SSC Junior Engineer | `ssc-junior-engineer-examination` |
| SSC Multi-Tasking Staff and Havaldar Examination 2025 | Staff Selection Commission | SSC MTS, MTS, SSC Havaldar | `ssc-multi-tasking-staff-and-havaldar-examination-2025-live-capture` |
| SSC Selection Post Phase XIII | Staff Selection Commission | SSC Selection Post, SSC Phase 13, Selection Post Phase 13 | `ssc-selection-post-phase-xiii` |
| SSC Stenographer Grade C & D Examination | Staff Selection Commission | SSC Stenographer, SSC Steno | `ssc-stenographer-grade-c-d-examination` |
| SSC Sub-Inspector in Delhi Police and CAPFs Examination | Staff Selection Commission | SSC CPO, SSC SI, Delhi Police SI | `ssc-sub-inspector-in-delhi-police-and-capfs-examination` |
| Telangana DSC Teacher Recruitment | Government of Telangana | TG DSC, TS DSC, Telangana DSC | `telangana-dsc-teacher-recruitment` |
| Telangana Teacher Eligibility Test (TG TET) | Department of School Education Telangana | TS TET, Telangana TET, TG TET | `telangana-teacher-eligibility-test-tg-tet` |
| TG EAPCET | JNTU Hyderabad / TGCHE | TS EAMCET, Telangana EAMCET, EAMCET | `tg-eapcet` |
| TG/TS POLYCET | State Board of Technical Education and Training Telangana | TS POLYCET, TG POLYCET, Telangana Polytechnic | `tg-ts-polycet` |
| TGPSC Group I Services Examination | Telangana Public Service Commission | TGPSC Group 1, TSPSC Group 1, Telangana Group I | `tgpsc-group-i-services-examination` |
| TGPSC Group II Services Examination | Telangana Public Service Commission | TGPSC Group 2, TSPSC Group 2, Telangana Group II | `tgpsc-group-ii-services-examination` |
| TGPSC Group III Services Examination | Telangana Public Service Commission | TGPSC Group 3, TSPSC Group 3, Telangana Group III | `tgpsc-group-iii-services-examination` |
| TNPSC Combined Civil Services Examination I (Group I) | Tamil Nadu Public Service Commission | TNPSC Group 1, TNPSC Group I | `tnpsc-combined-civil-services-examination-i-group-i` |
| TNPSC Combined Civil Services Examination II (Group II/IIA) | Tamil Nadu Public Service Commission | TNPSC Group 2, TNPSC Group II, TNPSC Group 2A | `tnpsc-combined-civil-services-examination-ii-group-ii-iia` |
| TNPSC Combined Civil Services Examination IV (Group IV Services) | Tamil Nadu Public Service Commission | TNPSC Group 4, TNPSC Group IV, TNPSC CCSE IV | `tnpsc-combined-civil-services-examination-iv-group-iv-services` |
| TNPSC Combined Technical Services Examination 2025 | Tamil Nadu Public Service Commission | TNPSC CTS, TNPSC Combined Technical Services | `tnpsc-combined-technical-services-examination-2025` |
| TSPSC Group IV Services | Telangana State Public Service Commission | TSPSC Group 4, Telangana Group IV | `tspsc-group-iv-services` |
| UGC-NET June 2026 | National Testing Agency | UGC NET, NET, National Eligibility Test | `ugc-net-june-2026` |
| UP B.Ed Joint Entrance Examination | Bundelkhand University Jhansi | UP BEd JEE, UP BEd | `up-b-ed-joint-entrance-examination` |
| UPPSC Combined State/Upper Subordinate Services Examination (PCS) | Uttar Pradesh Public Service Commission | UPPSC PCS, UP PCS | `uppsc-combined-state-upper-subordinate-services-examination-pcs` |
| UPPSC One Time Registration | Uttar Pradesh Public Service Commission | UPPSC, UPPSC OTR | `uppsc-one-time-registration` |
| UPPSC Review Officer / Assistant Review Officer | Uttar Pradesh Public Service Commission | UPPSC RO ARO, RO ARO, UP Review Officer | `uppsc-review-officer-assistant-review-officer` |
| UPSC CAPF (Assistant Commandants) Examination 2026 | Union Public Service Commission | CAPF AC 2026, CAPF, UPSC CAPF, CAPF AC, Central Armed Police Forces | `upsc-capf-assistant-commandants-examination-2026` |
| UPSC Civil Services Examination 2026 | Union Public Service Commission | CSE 2026, UPSC CSE, CSE, IAS, Civil Services Examination, UPSC Prelims | `upsc-civil-services-examination-2026` |
| UPSC Combined Defence Services Examination (II) 2026 | Union Public Service Commission | CDS II 2026, CDS, UPSC CDS, Combined Defence Services | `upsc-combined-defence-services-examination-ii-2026` |
| UPSC Engineering Services Examination | Union Public Service Commission | ESE, UPSC ESE, IES, Engineering Services Examination | `upsc-engineering-services-examination` |
| UPSC NDA & NA Examination (II) 2026 | Union Public Service Commission | NDA II 2026, NDA, UPSC NDA, NDA NA, National Defence Academy | `upsc-nda-na-examination-ii-2026` |
| UPSSSC Preliminary Eligibility Test (PET) | Uttar Pradesh Subordinate Services Selection Commission | UPSSSC PET, UP PET | `upsssc-preliminary-eligibility-test-pet` |
| Uttar Pradesh Police Constable Recruitment | Uttar Pradesh Police Recruitment and Promotion Board | UP Police, UP Police Constable, UP Constable, UPPRPB | `uttar-pradesh-police-constable-recruitment` |
| WBJEE 2026 | West Bengal Joint Entrance Examinations Board | West Bengal Joint Entrance Examination, WBJEE | `wbjee-2026` |
| WBPSC / WBCS Online Application | West Bengal Public Service Commission | WBPSC, WBCS, West Bengal PSC | `wbpsc-wbcs-online-application` |
| West Bengal Primary Teacher Eligibility Test | West Bengal Board of Primary Education | WB TET, WB Primary TET | `west-bengal-primary-teacher-eligibility-test` |
| West Bengal School Service Commission SLST Assistant Teacher Recruitment | West Bengal School Service Commission | WBSSC SLST, SLST, West Bengal SSC Teacher | `west-bengal-school-service-commission-slst-assistant-teacher-recruitment` |
| Xavier Aptitude Test | XLRI Xavier School of Management | XAT, XLRI XAT | `xavier-aptitude-test` |
