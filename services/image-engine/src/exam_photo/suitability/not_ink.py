"""Is this upload a photograph rather than a signature or a thumb impression?

Testing note 23: a street photograph uploaded in a signature's place was
"prepared" into noise. The owner asked for it to be refused. DEC-041 allows a
refusal only for a genuinely wrong subject, and a candidate whose real
signature or impression is turned away has lost more than one who uploads the
wrong file and is told so -- so the check is built to be certain before it
fires.

**The signal is a face**, from the short-range BlazeFace detector the
photograph pipeline already carries. Measured on 2026-09-14:

| set | highest face confidence | sheet of paper |
|---|---|---|
| owner's ink set: 3 signatures | 0.00 | 34-93% of the frame |
| owner's ink set: 2 thumb impressions | 0.36 | 97%, found |
| 116 synthetic marks (the ink robustness sweep) | 0.28 | 97%, found |
| 116 synthetic impressions, faint and blue pads | **0.57** | 97%, found |
| 40-photo labelled set | 0.98; 34 of 40 at >= 0.5 | no sheet, or under half, in most |
| the street photograph from note 23 (a screenshot crop) | 0.42 | 9% |

Colourfulness and the share of dark pixels were measured too and do not
separate: a real signature photographed on a dark desk reads as colourful and
dark as any portrait.

An impression's whorl can look face-like to the detector, so the two kinds of
file get different rules:

- **Signature**: refused at a face of 0.5 or more (the most face-like mark
  measured is 0.28), or at 0.4 or more when no sheet fills the frame.
- **Thumb impression**: refused only at a face of 0.5 or more **and** no sheet
  filling the frame -- a real impression is photographed on a page that fills
  it, whatever the detector thinks of the whorl.

A detector that cannot be loaded never refuses anything.
"""

from __future__ import annotations

from typing import Sequence

#: A face this confident is a photograph of a person.
CERTAIN_FACE_CONFIDENCE = 0.5
#: A weaker face counts only in a frame that is not mostly paper.
LIKELY_FACE_CONFIDENCE = 0.4
#: Below this share of the frame, the largest sheet-like region is not a page
#: the candidate photographed up close.
SCENE_PAPER_AREA = 0.5


def _is_scene(paper_area_fraction: float, paper_is_fallback: bool) -> bool:
    return paper_is_fallback or paper_area_fraction < SCENE_PAPER_AREA


def looks_like_a_photograph(
    kind: str,
    face_confidences: Sequence[float],
    paper_area_fraction: float,
    paper_is_fallback: bool,
) -> bool:
    """True when an upload for ``kind`` is a photograph, not ink on paper."""
    best = max(face_confidences, default=0.0)
    scene = _is_scene(paper_area_fraction, paper_is_fallback)
    if kind == "signature":
        return best >= CERTAIN_FACE_CONFIDENCE or (
            best >= LIKELY_FACE_CONFIDENCE and scene
        )
    if kind == "thumb_impression":
        return best >= CERTAIN_FACE_CONFIDENCE and scene
    return False


#: What a candidate is told, per kind of file. Plain words and what to do.
REFUSAL_TEXT = {
    "signature": (
        "This looks like a photograph, not a signature. Sign on plain white "
        "paper and take a photo of just the signature."
    ),
    "thumb_impression": (
        "This looks like a photograph, not a thumb impression. Press your thumb "
        "on plain white paper and take a photo of just the impression."
    ),
}

#: The issue code recorded on the job, per kind of file.
REFUSAL_CODE = {
    "signature": "UPLOAD_NOT_A_SIGNATURE",
    "thumb_impression": "UPLOAD_NOT_A_THUMB_IMPRESSION",
}
