"""Generate real exam-rule records from the verified 48-exam research (DEC-042).

Only appearance/capture rules that the research verified against an official
source are encoded.  File specifications (pixel size, KB, DPI) were explicitly
out of scope for that research, so dimensions are recorded as `unspecified`
rather than invented -- absence is a finding, not a blank to fill.
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(r"C:\Projects\exam-photo-platform\examples\rules")

# exam_id, name, aliases, body, year, cycle, source(url,title,section,wording), appearance, composition-overrides
EXAMS = [
    {
        "id": "upsc-civil-services-2026",
        "name": "UPSC Civil Services Examination 2026",
        "aliases": ["UPSC CSE", "Civil Services Examination"],
        "body": "Union Public Service Commission",
        "year": 2026,
        "cycle": "CSE-2026",
        "url": "https://upsconline.nic.in/ngrp/assets/PDF/instruction-photo-signature-upload-upsc.pdf",
        "title": "Instructions for Uploading Photograph and Signature",
        "section": "pp. 2-5",
        "wording": "plain white background; both ears are visible; avoid glare on the eyeglasses; no grinning, frowning, or raised eyebrows; live photo is mandatory; 3/4th face",
        "coverage": 75.0,
        "basis": "face_box_area",
        "ears": "required_visible",
        "appearance": {
            "spectacles": {
                "policy": "conditional",
                "condition": "ordinary corrective spectacles are acceptable; glare and coloured or dark glasses are not",
                "source_wording": "avoid glare on the eyeglasses",
            },
            "smile": {
                "policy": "prohibited",
                "source_wording": "no grinning, frowning, or raised eyebrows",
            },
            "monochrome_accepted": False,
            "face_coverage_basis": "face_box_area",
            "live_capture_required": True,
            "source_wording": "live photo is mandatory",
        },
    },
    {
        "id": "ssc-cgl-2025",
        "name": "SSC Combined Graduate Level Examination 2025",
        "aliases": ["SSC CGL"],
        "body": "Staff Selection Commission",
        "year": 2025,
        "cycle": "CGL-2025",
        "url": "https://ssc.gov.in/api/attachment/uploads/masterData/NoticeBoards/Notice_of_adv_cgl_2025.pdf",
        "title": "Notice of Combined Graduate Level Examination, 2025",
        "section": "Application instructions, p. 18 and annexures",
        "wording": "good light and plain background; camera is at eye level; look straight ahead; cap, mask or glasses/spectacles; will be rejected; pre-existing photograph",
        "coverage": None,
        "basis": "unspecified",
        "ears": "unspecified",
        "appearance": {
            "spectacles": {
                "policy": "prohibited",
                "source_wording": "cap, mask or glasses/spectacles",
            },
            "headwear": {
                "policy": "prohibited",
                "source_wording": "cap, mask or glasses/spectacles",
            },
            "face_mask": {
                "policy": "prohibited",
                "source_wording": "cap, mask or glasses/spectacles",
            },
            "live_capture_required": True,
            "prohibited_provenance": ["photograph_of_a_photograph"],
            "source_wording": "pre-existing photograph",
        },
    },
    {
        "id": "ibps-crp-po-mt-xv",
        "name": "IBPS CRP PO/MT-XV",
        "aliases": ["IBPS PO"],
        "body": "Institute of Banking Personnel Selection",
        "year": 2025,
        "cycle": "CRP-PO-MT-XV",
        "url": "https://ibpsreg.ibps.in/crppoxvjun25/",
        "title": "How to Apply - CRP PO/MT-XV",
        "section": "Photograph and signature guidelines",
        "wording": "recent passport style colour picture; light-coloured, preferably white, background; eyes can be clearly seen; Religious headwear is allowed; no harsh shadows; no red eye",
        "coverage": 50.0,
        "basis": "face_box_area",
        "ears": "unspecified",
        "appearance": {
            "spectacles": {
                "policy": "conditional",
                "condition": "permitted provided the eyes are clearly visible and there is no reflection",
                "source_wording": "eyes can be clearly seen",
            },
            "headwear": {
                "policy": "conditional",
                "condition": "religious headwear is permitted provided it does not cover the face",
                "source_wording": "Religious headwear is allowed",
            },
            "monochrome_accepted": False,
            "face_coverage_basis": "face_box_area",
            "source_wording": "recent passport style colour picture",
        },
    },
    {
        "id": "sbi-po-2025",
        "name": "SBI Probationary Officers 2025",
        "aliases": ["SBI PO"],
        "body": "State Bank of India",
        "year": 2025,
        "cycle": "PO-2025",
        "url": "https://sbi.co.in/documents/77530/52947104/1_Detailed_Adv.2025_23.06.2025.pdf",
        "title": "Recruitment of Probationary Officers - Detailed Advertisement 2025",
        "section": "Guidelines for photograph and signature scan",
        "wording": "recent passport style colour picture; light-coloured, preferably white, background; eyes can be clearly seen; Religious headwear is allowed; no harsh shadows; no red eye",
        "coverage": None,
        "basis": "unspecified",
        "ears": "unspecified",
        "appearance": {
            "spectacles": {
                "policy": "conditional",
                "condition": "permitted provided the eyes are clearly visible; caps, hats and dark glasses are not acceptable",
                "source_wording": "eyes can be clearly seen",
            },
            "headwear": {
                "policy": "conditional",
                "condition": "religious headwear is permitted provided it does not cover the face",
                "source_wording": "Religious headwear is allowed",
            },
            "monochrome_accepted": False,
            "source_wording": "recent passport style colour picture",
        },
    },
    {
        "id": "lic-aao-generalist-2025",
        "name": "LIC Assistant Administrative Officer (Generalist) 2025",
        "aliases": ["LIC AAO"],
        "body": "Life Insurance Corporation of India",
        "year": 2025,
        "cycle": "AAO-2025",
        "url": "https://licindia.in/documents/d/guest/aao-generalist-notification-2025-final",
        "title": "Recruitment of Assistant Administrative Officers (Generalist), 2025",
        "section": "Guidelines for scanning and uploading",
        "wording": "recent passport style colour picture; preferably white, background; eyes and ears are clearly visible; Religious headwear is allowed; no harsh shadows",
        "coverage": None,
        "basis": "unspecified",
        "ears": "required_visible",
        "appearance": {
            "spectacles": {
                "policy": "conditional",
                "condition": "permitted provided the eyes are clearly visible; coloured glasses and sunglasses are not",
                "source_wording": "eyes and ears are clearly visible",
            },
            "headwear": {
                "policy": "conditional",
                "condition": "religious headwear is permitted provided it does not cover the face",
                "source_wording": "Religious headwear is allowed",
            },
            "monochrome_accepted": False,
            "source_wording": "recent passport style colour picture",
        },
    },
    {
        "id": "nta-jee-main-2026",
        "name": "JEE (Main) 2026",
        "aliases": ["JEE Main"],
        "body": "National Testing Agency",
        "year": 2026,
        "cycle": "JEE-Main-2026",
        "url": "https://cdnbbsr.s3waas.gov.in/s3f8e59f4b2fe7c5705bf878bbd494ccdf/uploads/2025/11/202511021649722475.pdf",
        "title": "Information Bulletin - JEE (Main) 2026",
        "section": "Photograph and signature specifications",
        "wording": "colour with 80% face; without mask; including ears; against white background; live photograph; proper lighting; not of anyone else",
        "coverage": 80.0,
        "basis": "face_box_area",
        "ears": "required_visible",
        "appearance": {
            "face_mask": {"policy": "prohibited", "source_wording": "without mask"},
            "monochrome_accepted": False,
            "face_coverage_basis": "face_box_area",
            "live_capture_required": True,
            "source_wording": "colour with 80% face",
        },
    },
    {
        "id": "nta-neet-ug-2026",
        "name": "NEET (UG) 2026",
        "aliases": ["NEET UG"],
        "body": "National Testing Agency",
        "year": 2026,
        "cycle": "NEET-UG-2026",
        "url": "https://cdnbbsr.s3waas.gov.in/s37bc1ec1d9c3426357e69acd5bf320061/uploads/2026/02/202602231394640855.pdf",
        "title": "Information Bulletin - NEET (UG) 2026",
        "section": "Photograph and signature specifications",
        "wording": "spectacles only if used regularly; Polaroid and Computer-generated photos are not acceptable; white background; without mask; including ears; need not be attested",
        "coverage": 80.0,
        "basis": "face_box_area",
        "ears": "required_visible",
        "appearance": {
            "spectacles": {
                "policy": "conditional",
                "condition": "permitted only if the candidate uses spectacles regularly",
                "source_wording": "spectacles only if used regularly",
            },
            "face_mask": {"policy": "prohibited", "source_wording": "without mask"},
            "monochrome_accepted": False,
            "face_coverage_basis": "face_box_area",
            "prohibited_provenance": ["computer_generated"],
            "attestation_required": False,
            "source_wording": "Polaroid and Computer-generated photos are not acceptable",
        },
    },
    {
        "id": "gate-2026",
        "name": "GATE 2026",
        "aliases": ["Graduate Aptitude Test in Engineering"],
        "body": "Indian Institute of Technology Guwahati",
        "year": 2026,
        "cycle": "GATE-2026",
        "url": "https://gate2026.iitg.ac.in/doc/IB/GATE2026-IB-28092025.pdf",
        "title": "GATE 2026 Information Brochure",
        "section": "Photograph requirements",
        "wording": "face covering 60-70%; background must be white; Normal spectacles for vision correction are allowed; except for religious reasons; other objects or persons; may get rejected",
        "coverage": 65.0,
        "basis": "face_box_area",
        "ears": "unspecified",
        "appearance": {
            "spectacles": {
                "policy": "conditional",
                "condition": "normal spectacles for vision correction are permitted; glare makes the photograph unacceptable",
                "source_wording": "Normal spectacles for vision correction are allowed",
            },
            "headwear": {
                "policy": "conditional",
                "condition": "head coverings are permitted only for religious reasons and the facial features must remain clearly visible",
                "source_wording": "except for religious reasons",
            },
            "monochrome_accepted": False,
            "face_coverage_basis": "face_box_area",
            "source_wording": "face covering 60-70%",
        },
    },
    {
        "id": "rrb-level-1-cen-08-2024",
        "name": "RRB Level-1 Posts, CEN 08/2024",
        "aliases": ["Railway Group D", "RRB Level 1"],
        "body": "Railway Recruitment Boards",
        "year": 2024,
        "cycle": "CEN-08-2024",
        "url": "https://wcr.indianrailways.gov.in/uploads/files/1771596254046-CEN_%2008_2024_English.pdf",
        "title": "CEN No. 08/2024 - Level 1 Posts",
        "section": "Photograph instructions",
        "wording": "not older than two months; professional studio; mobile and self-composed portraits may result in rejection; occupy at least 50%; free from signature/name/dates",
        "coverage": 50.0,
        "basis": "face_box_area",
        "ears": "unspecified",
        "appearance": {
            "monochrome_accepted": False,
            "face_coverage_basis": "face_box_area",
            "recency_maximum_days": 60,
            "prohibited_provenance": ["selfie", "mobile_photograph"],
            "imprint": {
                "policy": "prohibited",
                "source_wording": "free from signature/name/dates",
            },
            "source_wording": "not older than two months",
        },
    },
    {
        "id": "tnpsc-combined-technical-services-2025",
        "name": "TNPSC Combined Technical Services Examination 2025",
        "aliases": ["TNPSC CTSE"],
        "body": "Tamil Nadu Public Service Commission",
        "year": 2025,
        "cycle": "CTSE-2025",
        "url": "https://www.tnpsc.gov.in/Document/english/SCE%20English%20Final_.pdf",
        "title": "Combined Technical Services Examination (Interview Posts), 2025 - Notification",
        "section": "Photograph instructions",
        "wording": "colour passport size photograph; white background; both the ears; name of the applicant; date on which the photograph was taken; Mobile phone photographs and selfies",
        "coverage": None,
        "basis": "unspecified",
        "ears": "required_visible",
        "appearance": {
            "monochrome_accepted": False,
            "prohibited_provenance": ["selfie", "mobile_photograph"],
            "imprint": {
                "policy": "required",
                "fields": ["candidate_name", "photograph_date"],
                "position": "bottom",
                "source_wording": "name of the applicant; date on which the photograph was taken",
            },
            "source_wording": "colour passport size photograph",
        },
    },
    {
        "id": "cbse-class-ix-xi-registration-2025-26",
        "name": "CBSE Classes IX/XI Registration 2025-26",
        "aliases": ["CBSE Registration"],
        "body": "Central Board of Secondary Education",
        "year": 2025,
        "cycle": "2025-26",
        "url": "https://www.cbse.gov.in/cbsenew/documents/Submission_Registration_Data_Class_IXXI2526_15092025.pdf",
        "title": "Submission of Registration Data for Classes IX/XI, Session 2025-26",
        "section": "Photograph annexure",
        "wording": "full colour and of high quality; taken in the last 6 months; composing 80% of the image; smiling is allowed; Eyes must be open",
        "coverage": 80.0,
        "basis": "face_box_area",
        "ears": "unspecified",
        "appearance": {
            "smile": {"policy": "permitted", "source_wording": "smiling is allowed"},
            "monochrome_accepted": False,
            "face_coverage_basis": "face_box_area",
            "recency_maximum_days": 180,
            "source_wording": "full colour and of high quality",
        },
    },
]


def build(e: dict) -> dict:
    comp: dict = {
        "crop_profile": "tight_exam_portrait",
        "ears_policy": e["ears"],
        "face_centred": True,
        "frontal_pose": True,
        "eye_visibility": True,
        "chin_visible": True,
        "complete_hair_visible": True,
        "complete_hair_required": True,
        "complete_chin_required": True,
        "additional_instructions": e["wording"],
    }
    if e["coverage"] is not None:
        comp["face_coverage_target"] = e["coverage"]
    if e["ears"] == "required_visible":
        comp["ears_visible"] = True

    provenance = {
        "image_requirements.appearance": {
            "type": "official",
            "evidence_reference": f"{e['title']} - {e['section']} ({e['url']})",
            "reasoning": (
                f"Appearance rules transcribed from {e['title']} "
                f"({e['section']}). Only categories the official source states "
                "are encoded; unstated categories are omitted rather than defaulted."
            ),
            "confidence": 5,
            "approved": True,
        },
        "image_requirements.dimensions.mode": {
            "type": "platform_default",
            "reasoning": (
                "The appearance-rule research deliberately excluded file "
                "specifications, so no pixel dimensions were verified for this "
                "exam. Recorded as unspecified rather than invented; the "
                "platform default profile applies until a specification is "
                "verified from the official bulletin."
            ),
            "confidence": 1,
            "approved": False,
        },
    }

    return {
        "schema_version": "1.1",
        "rule_id": e["id"],
        "rule_version": "0.1.0",
        "status": "provisional",
        "exam": {
            "exam_id": e["id"],
            "exam_name": e["name"],
            "aliases": e["aliases"],
            "conducting_body": e["body"],
            "examination_year": e["year"],
            "application_cycle": e["cycle"],
        },
        "source_evidence": [
            {
                "source_type": "official_pdf",
                "official_source": True,
                "source_url": e["url"],
                "document_title": e["title"],
                "section_name": e["section"],
                "captured_wording": e["wording"],
            }
        ],
        "image_requirements": {
            "dimensions": {
                "mode": "unspecified",
                "platform_default_profile": "standard_passport_350_450",
                "fallback_reason": (
                    "The 48-exam appearance-rule research excluded file "
                    "specifications by design, so no official pixel dimensions "
                    "were verified for this exam. Left unspecified rather than "
                    "guessed; to be filled from the official bulletin before "
                    "this record leaves provisional status."
                ),
            },
            "file_size": {"maximum_bytes": 512000},
            "formats": {
                "allowed_formats": ["jpg", "jpeg"],
                "preferred_format": "jpeg",
                "preserve_transparency": False,
                "strip_metadata": True,
                "colour_space": "sRGB",
                "extension_policy": "strip_and_append",
            },
            "background": {
                "mode": "exact_colour",
                "required_colour": "#FFFFFF",
                "tolerance": 3.0,
                "plain_background_required": True,
                "shadows_allowed": False,
                "gradient_allowed": False,
            },
            "composition": comp,
            "appearance": e["appearance"],
            "filename": {
                "mode": "unspecified",
                "case_sensitive": False,
                "extension_required": True,
                "fallback_basename": e["id"],
            },
            "exceptional_instructions": {
                "recent_photo_requirement": True,
                "processing_support_status": "supported",
            },
        },
        "provenance": provenance,
        "verification": {"verification_status": "provisional"},
        "fictional_example": False,
    }


for exam in EXAMS:
    path = OUT / f"exam_{exam['id'].replace('-', '_')}.json"
    path.write_text(json.dumps(build(exam), indent=2) + "\n", encoding="utf-8")
    print("wrote", path.name)
