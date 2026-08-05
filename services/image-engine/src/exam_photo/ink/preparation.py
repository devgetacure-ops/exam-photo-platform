"""Turning a photograph of ink on paper into the file a portal will accept.

The stages, and why they are in this order:

1. **Find the sheet.** Everything after this assumes it is looking at paper, so
   the hand holding the page and the desk under it are excluded first. Skipping
   this and thresholding the whole frame reads the desk as the darkest thing in
   the picture and the signature as a mid-tone.
2. **Divide out the illumination.** Shadow, gradient and colour cast are
   properties of the room. Removing them here rather than later means every
   subsequent measurement is against paper white, so the thresholds can be
   stated once instead of per-photograph.
3. **Detect the ink.** Relative to the darkest mark present, so it works for a
   faint blue biro and a heavy black marker without a per-ink setting.
4. **Crop to the ink.** The candidate photographs a whole sheet; the portal
   wants the mark.
5. **Render.** Paper to pure white, ink to full strength, keeping its hue.

The tonal step is aggressive by design and that is the difference between this
and the photograph pipeline. See the package docstring: on a face, correction
is restrained because the subject is a person; on paper, the paper carries no
information and the mark's identity is its shape, which nothing here touches.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import numpy as np
from PIL import Image

from exam_photo.ink.illumination import estimate_paper_field, flatten_to_paper_white
from exam_photo.ink.ink_mask import (
    InkMaskResult,
    detect_ink,
    framed_box,
)
from exam_photo.ink.paper_region import PaperRegion, crop_to_paper
from exam_photo.models.geometry import BoundingBox

#: Longest edge the analysis runs at. The stages measure distributions and
#: locate a rectangle; neither needs sensor resolution, and the reference
#: captures arrive at up to 4095 px. The *rendering* is done on the original
#: pixels, so nothing is lost -- only the search is downscaled.
_ANALYSIS_EDGE = 1400

#: Dilation applied to the rejected-ink mask before it is whitened out, in
#: pixels of the rendered image. The rejection is computed on a downscaled copy,
#: so its boundary is coarse; without a margin the soft halo around a rejected
#: mass survives as a grey fringe.
_SUPPRESSION_MARGIN = 3


class InkTreatment(str, Enum):
    """How hard to work on a mark, decided by what the mark is.

    Three settings, because these deliverables want different things and one
    compromise served none of them.

    ``MARK`` is a signature: a few thin strokes on a page, where everything
    that is not a stroke is noise -- show-through, ruling, dirt, the shadow of
    a fold. Clearing the page is most of the value, and the mark loses nothing
    by it, because a pen stroke is either there or it is not.

    ``IMPRESSION`` is a thumb or finger impression, and the opposite is true.
    The deliverable *is* the ridge pattern, which lives in a continuous range of
    density, and every operation that decides "this pixel is ink and that one is
    not" destroys some of it. Measured on the reference impression, clearing the
    page outside the detected ink punched visible holes through the pattern.
    So this treatment does the minimum that still fixes the capture: correct the
    lighting, crop to the impression, balance the levels gently, and otherwise
    leave it alone.

    ``PAGE`` is a whole document -- a handwritten declaration, a certificate, a
    mark sheet. It differs from the other two on *framing* rather than tone: the
    deliverable is the sheet, not what is written on it, so it is never cropped
    to its content. A declaration cropped to its writing would lose the heading
    above and the date below; a certificate cropped to its text would lose the
    seal. Tonally it is the most conservative of the three, because a document
    can carry faint content that matters -- a light stamp, a watermark, a carbon
    impression -- and clipping that away is altering the document rather than
    correcting the capture, which the integrity rule forbids.
    """

    MARK = "mark"
    IMPRESSION = "impression"
    PAGE = "page"


#: White point per treatment, as depth below paper. Everything lighter than
#: this becomes pure paper, and that clipping is how a scan gets a clean page.
#:
#: A mark takes 0.10: it also has the ink mask clearing the page, and a pen
#: stroke has no faint outer half to lose.
#:
#: An impression takes 0.01, which is almost no clipping at all, and the
#: measurement behind that is stark. An impression fades outward -- its edge is
#: genuinely faint ink, not a boundary -- so a white point cuts straight through
#: the subject. Share of the non-paper pixels that get erased, on the two
#: reference impressions:
#:
#: | white point depth | value | closer capture | further capture |
#: |-------------------|-------|----------------|-----------------|
#: | 0.09              |  232  |     51.7%      |      74.6%      |
#: | 0.06              |  240  |     40.4%      |      69.3%      |
#: | 0.03              |  247  |     15.1%      |      41.8%      |
#: | 0.02              |  250  |      9.2%      |      22.0%      |
#: | 0.01              |  252  |      ~0%       |      ~0%        |
#:
#: 0.09 was chosen earlier by sweeping for the cleanest *paper*, which is the
#: wrong thing to optimise: it was discarding three quarters of the impression
#: to do it, and the product owner saw the loss immediately. The paper does not
#: need the help -- flattening already leaves it at 248 median and 252 at the
#: third quartile -- so the clip is set where it removes nothing.
_WHITE_POINT_DEPTH = {
    InkTreatment.MARK: 0.10,
    InkTreatment.IMPRESSION: 0.01,
    # A page is cleaned only of what is unambiguously bare paper. Anything
    # further risks a faint stamp or a carbon impression, and losing those
    # would be altering the document rather than correcting the capture.
    InkTreatment.PAGE: 0.03,
}

#: Black-point headroom per treatment, as a multiple of the deepest ink.
#:
#: The black point is 255 * (1 - ink_depth * headroom), so *lower* headroom
#: raises the black point and deepens the result: at 1.0 the deepest ink lands
#: exactly on black, and below 1.0 the darkest part of a stroke clips to solid.
#:
#: A mark takes 0.90. A signature wants its strokes to read as ink rather than
#: as grey, and clipping the stroke's core costs nothing because the core is
#: uniform anyway -- what carries the shape is the boundary, which sits well
#: above the black point and keeps its gradation.
#:
#: An impression takes 1.35, well the other way. Its densest area must stay
#: distinguishable from its second-densest, because that difference is ridge
#: detail; clipping the core would flatten the middle of the print into a slab.
_BLACK_POINT_HEADROOM_BY_TREATMENT = {
    InkTreatment.MARK: 0.90,
    InkTreatment.IMPRESSION: 1.35,
    # Between the two. A document wants its text to read as black, but it also
    # carries printed greys -- rule lines, tint blocks, a photocopied
    # photograph -- that must stay distinguishable from the text.
    InkTreatment.PAGE: 1.10,
}


#: Extra margin for an impression, added to the mark margin. The ink box is
#: drawn where the impression crosses the ink threshold, but the impression
#: continues past that as fading ridge detail, so a box tight to the threshold
#: cuts the outer pattern off. Measured on the reference impressions, tone
#: continues 6-9% of the box's size beyond it on every side.
_IMPRESSION_EXTRA_MARGIN = 0.09


@dataclass(frozen=True)
class InkPreparation:
    """The prepared image and what was measured on the way to it."""

    image: Image.Image
    paper: PaperRegion
    ink: InkMaskResult
    crop_box: Optional[BoundingBox]
    #: True when no mark was found and the input was passed through unchanged
    #: apart from tonal correction. The caller decides what to do about it;
    #: this module does not refuse, on the same reasoning as DEC-041.
    is_blank: bool


def _analysis_copy(rgb: np.ndarray[Any, Any]) -> tuple[np.ndarray[Any, Any], float]:
    height, width = rgb.shape[:2]
    scale = _ANALYSIS_EDGE / max(height, width)
    if scale >= 1.0:
        return rgb, 1.0
    resized = Image.fromarray(rgb.astype(np.uint8)).resize(
        (max(1, int(width * scale)), max(1, int(height * scale))),
        resample=Image.Resampling.LANCZOS,
    )
    return np.asarray(resized).astype(np.float32), scale


def _dilate(mask: np.ndarray[Any, Any], steps: int) -> np.ndarray[Any, Any]:
    grown = mask
    for _ in range(steps):
        spread = grown.copy()
        spread[1:, :] |= grown[:-1, :]
        spread[:-1, :] |= grown[1:, :]
        spread[:, 1:] |= grown[:, :-1]
        spread[:, :-1] |= grown[:, 1:]
        grown = spread
    return grown


#: Dilation of the ink mask before it is used to clear the page, in pixels.
#: A stroke's own antialiased edge falls below the ink threshold and is
#: therefore outside the mask; without a margin it is cut off square and the
#: mark ends up with a hard, jagged outline.
_KEEP_MARGIN = 3


#: How faint a pixel may be and still be kept, as a fraction of the deepest
#: ink, when it lies next to something already accepted as ink.
#:
#: The detection threshold answers "is there writing here", and it has to be
#: strict or show-through passes. Rendering asks a different question -- "is
#: this pixel part of the writing that was found" -- and the strict answer is
#: wrong for it. A pen stroke varies along its length: it thins on a curve, it
#: skips where the ball lifted, it fades at the end of a letter. Those parts
#: fall under the detection threshold, get cleared as background, and the letter
#: arrives with holes in it -- visible on the reference signature as breaks in
#: the D and the G.
#:
#: 0.28 of the deepest ink keeps the faint interior of a stroke while still
#: sitting above the reference photograph's show-through, which measures 0.06 to
#: 0.29 of the deepest ink *and is nowhere near the writing*, which is the other
#: half of the guard below.
_KEEP_DEPTH_FRACTION = 0.28

#: How far from accepted ink the loose threshold is allowed to reach, as a
#: fraction of the longer edge. This is what stops the loose threshold from
#: readmitting show-through: faint pixels are kept only where they adjoin a
#: stroke, and show-through covers the parts of the page that the writing does
#: not.
_KEEP_REACH_FRACTION = 0.02


def _keep_mask(
    flattened: np.ndarray[Any, Any],
    strict: np.ndarray[Any, Any],
    ink_depth: float,
) -> np.ndarray[Any, Any]:
    """Everything that belongs to the writing, including its faint parts."""
    if not strict.any():
        return strict
    depth = np.clip(1.0 - flattened.min(axis=2) / 255.0, 0.0, 1.0)
    loose = depth >= max(ink_depth * _KEEP_DEPTH_FRACTION, 0.04)
    reach = max(2, round(max(flattened.shape[:2]) * _KEEP_REACH_FRACTION))
    near: np.ndarray[Any, Any] = loose & _dilate(strict, reach)
    return near


def _render(
    flattened: np.ndarray[Any, Any],
    ink_depth: float,
    treatment: InkTreatment,
    keep: "np.ndarray[Any, Any] | None" = None,
    suppress: "np.ndarray[Any, Any] | None" = None,
) -> np.ndarray[Any, Any]:
    """Paper to white, ink to full strength, every tone in between preserved.

    A **levels stretch**, per channel: everything at or above the white point
    becomes paper, everything at or below the black point becomes full-strength
    ink, and the range between the two is stretched linearly across.

    This replaced an alpha composite -- ink opacity ramped against a single
    flat ink colour -- which was wrong in a way the numbers hid and the eye did
    not. On a signature it merely thinned the strokes. On a thumb impression it
    was destructive: an impression is a *continuous* field of density whose
    ridge pattern lives entirely in the mid-tones, and mapping every tone onto
    one colour by opacity shredded a solid inked oval into blotchy speckle. The
    ridge detail is the only reason the impression is being collected at all.

    A stretch keeps that structure because it is monotonic: two tones that
    differed before still differ after, only further apart. Hue survives for
    the same reason -- all three channels get the same linear map, so a blue
    ballpoint stays blue and in fact deepens, which matters because several
    bodies require ink of a stated colour.

    The white point is set **just above paper grain**, not at the ink
    threshold, and that division of labour is the point. Clipping at the ink
    threshold is what a document scanner does to kill show-through, and on a
    signature it works; on a thumb impression it destroys the subject. An
    impression's lighter half sits below the ink threshold by construction --
    that is what makes it lighter -- so clipping there erases half the ridge
    pattern and leaves a blotchy shell. Measured on the reference impression,
    a white point at the ink threshold puts everything above value 160 to pure
    white, and much of the impression lives at 170-200.

    So the tonal curve stays gentle and the *ink mask* does the removing:
    ``keep`` marks what survives, everything else becomes paper. Show-through
    is below the ink threshold and therefore outside the mask, so it is cleared
    just as thoroughly as before -- but by a test that knows what it is looking
    at, rather than by a brightness cut-off that cannot tell faint ink from
    faint bleed.

    ``suppress`` marks pixels that were classified as ink and then rejected --
    a finger, the edge of the desk. They are forced to paper. Without this the
    rejection only ever affected where the crop was placed, and the rejected
    object was still rendered inside it: on the reference photograph a finger
    came through as a large grey smear across the corner of the output.
    """
    white_point = 255.0 * (1.0 - _WHITE_POINT_DEPTH[treatment])
    headroom = _BLACK_POINT_HEADROOM_BY_TREATMENT[treatment]
    black_point = 255.0 * (1.0 - min(ink_depth * headroom, 1.0))
    span = max(white_point - black_point, 1.0)

    rendered: np.ndarray[Any, Any] = (
        np.clip((flattened - black_point) / span, 0.0, 1.0) * 255.0
    )
    if keep is not None and treatment is InkTreatment.MARK:
        rendered[~_dilate(keep, _KEEP_MARGIN)] = 255.0
    if suppress is not None and suppress.any():
        rendered[_dilate(suppress, _SUPPRESSION_MARGIN)] = 255.0
    return rendered


def _prepare_page(
    source: np.ndarray[Any, Any],
    analysis: np.ndarray[Any, Any],
    scale: float,
    paper: PaperRegion,
    ink: InkMaskResult,
) -> InkPreparation:
    """Deliver the whole sheet, corrected but not cropped to its content."""
    inv = 1.0 / scale if scale > 0 else 1.0
    box = BoundingBox(
        left=max(0.0, paper.box.left * inv),
        top=max(0.0, paper.box.top * inv),
        right=min(float(source.shape[1]), paper.box.right * inv),
        bottom=min(float(source.shape[0]), paper.box.bottom * inv),
    )
    region = source[int(box.top) : int(box.bottom), int(box.left) : int(box.right), :]
    if region.size == 0:
        region, box = analysis, paper.box

    # No sheet mask is applied. On a mark it sets the world outside the paper to
    # white; on a page the sheet *is* the frame, and the mask's own boundary
    # would print as a white rim just inside the document's edge.
    estimate = estimate_paper_field(region)
    flattened = flatten_to_paper_white(region, estimate)
    rendered = _render(flattened, max(ink.ink_depth, 1e-6), InkTreatment.PAGE)
    return InkPreparation(
        image=Image.fromarray(rendered.astype(np.uint8)),
        paper=paper,
        ink=ink,
        crop_box=box,
        is_blank=False,
    )


def prepare_ink_document(
    image: Image.Image, treatment: InkTreatment = InkTreatment.MARK
) -> InkPreparation:
    """Prepare one photograph of a signature, impression, declaration or page."""
    source = np.asarray(image.convert("RGB")).astype(np.float32)
    analysis, scale = _analysis_copy(source)

    cropped, sheet_mask, paper = crop_to_paper(analysis)
    estimate = estimate_paper_field(cropped, sheet_mask)
    flattened = flatten_to_paper_white(cropped, estimate)
    # Anything outside the sheet is not part of the document. Setting it to
    # white rather than cropping it away keeps the geometry simple and has the
    # same effect on every measurement that follows.
    flattened[~sheet_mask] = 255.0

    # Grouping by proximity is for writing only. An impression is a single
    # mass and has nothing to be grouped with, and a page is not cropped to its
    # content at all, so neither is grouped.
    cluster = treatment is InkTreatment.MARK
    ink = detect_ink(flattened, sheet_mask, cluster)

    if treatment is InkTreatment.PAGE:
        # A page is framed by the sheet, not by what is written on it. Cropping
        # to content would take the heading off a declaration and the seal off a
        # certificate, and a blank page is still a page: it is delivered rather
        # than reported empty, because a form with nothing filled in is the
        # candidate's problem to notice, not this module's to hide.
        return _prepare_page(source, analysis, scale, paper, ink)

    if ink.box is None:
        rendered = _render(
            flattened, max(ink.ink_depth, 1e-6), treatment, None, ink.rejected
        )
        return InkPreparation(
            image=Image.fromarray(rendered.astype(np.uint8)),
            paper=paper,
            ink=ink,
            crop_box=None,
            is_blank=True,
        )

    extra = _IMPRESSION_EXTRA_MARGIN if treatment is InkTreatment.IMPRESSION else 0.0
    framed = framed_box(ink.box, flattened.shape[1], flattened.shape[0], extra)

    # Map the box back onto the original pixels and render there. The search ran
    # downscaled; the delivered file should carry the resolution the candidate
    # actually captured, because a signature reduced to a 1400-pixel analysis
    # copy and then enlarged is a signature blurred for no reason.
    inv = 1.0 / scale if scale > 0 else 1.0
    left = max(0.0, (paper.box.left + framed.left) * inv)
    top = max(0.0, (paper.box.top + framed.top) * inv)
    full_box = BoundingBox(
        left=left,
        top=top,
        right=min(
            float(source.shape[1]),
            max(left + 1.0, (paper.box.left + framed.right) * inv),
        ),
        bottom=min(
            float(source.shape[0]),
            max(top + 1.0, (paper.box.top + framed.bottom) * inv),
        ),
    )
    region = source[
        int(full_box.top) : int(full_box.bottom),
        int(full_box.left) : int(full_box.right),
        :,
    ]

    # The sheet mask has to come with it. Without it the hand holding the page
    # is simply back: the final pass would estimate its illumination as if it
    # were paper and then render it as the darkest ink in the frame. That is
    # exactly what the first version of this function did.
    region_mask = np.asarray(
        Image.fromarray(
            (
                sheet_mask[
                    int(framed.top) : int(framed.bottom),
                    int(framed.left) : int(framed.right),
                ]
                * 255
            ).astype(np.uint8)
        ).resize(
            (max(1, region.shape[1]), max(1, region.shape[0])),
            resample=Image.Resampling.NEAREST,
        )
    ).astype(bool)

    if region.size == 0:
        region, region_mask = cropped, sheet_mask

    final_estimate = estimate_paper_field(region, region_mask)
    final_flat = flatten_to_paper_white(region, final_estimate)
    final_flat[~region_mask] = 255.0
    # Deliberately **not** clustered a second time. Grouping by proximity picks
    # where to crop; once the crop is made, whatever it excluded is already
    # gone, and running the test again inside the frame can only remove content
    # that the first pass decided to keep.
    #
    # It did exactly that. Clustering happens at a fixed working resolution, so
    # the same page cropped is a different scale from the same page whole, and
    # line spacing that bridged before the crop failed to bridge after it. A
    # five-line declaration came out with its short final line rendered blank
    # inside a crop drawn to include it.
    final_ink = detect_ink(final_flat, region_mask)
    rendered = _render(
        final_flat,
        max(final_ink.ink_depth, 1e-6),
        treatment,
        _keep_mask(final_flat, final_ink.mask, max(final_ink.ink_depth, 1e-6)),
        final_ink.rejected,
    )

    return InkPreparation(
        image=Image.fromarray(rendered.astype(np.uint8)),
        paper=paper,
        ink=final_ink,
        crop_box=full_box,
        is_blank=False,
    )
