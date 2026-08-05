"""Preparation of ink-on-paper deliverables: signatures, thumb impressions and
handwritten declarations.

This is a different problem from the photograph pipeline and is deliberately
governed by the opposite rule.

A photograph of a face is barely touched: DEC-043 permits only a restrained
correction of the capture, because anything stronger starts changing the
subject and the subject is a person's identity. A photograph of ink on paper is
the reverse. The subject is a mark whose *shape* is the identity; the paper
around it carries no information at all, and the lighting carries none either.
So the tonal correction here can be as aggressive as it needs to be -- drive
the paper to white, drive the ink to its own colour at full strength -- and it
is only doing what a flatbed scanner would have done had one been available.

What must not change is the geometry of the strokes. Nothing in this package
thins, thickens, smooths, straightens, joins or redraws a mark. A signature
comes out as the person wrote it and a thumb impression keeps every ridge it
arrived with; the tonal curve moves brightness, never boundaries.
"""

from exam_photo.ink.illumination import (
    PaperFieldEstimate,
    estimate_paper_field,
    flatten_to_paper_white,
)
from exam_photo.ink.ink_mask import InkMaskResult, detect_ink
from exam_photo.ink.paper_region import PaperRegion, crop_to_paper, locate_paper
from exam_photo.ink.preparation import (
    InkPreparation,
    InkTreatment,
    prepare_ink_document,
)

__all__ = [
    "InkMaskResult",
    "InkPreparation",
    "InkTreatment",
    "PaperFieldEstimate",
    "PaperRegion",
    "crop_to_paper",
    "detect_ink",
    "estimate_paper_field",
    "flatten_to_paper_white",
    "locate_paper",
    "prepare_ink_document",
]
