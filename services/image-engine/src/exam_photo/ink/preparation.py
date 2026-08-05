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
from typing import Any, Optional

import numpy as np
from PIL import Image

from exam_photo.ink.illumination import estimate_paper_field, flatten_to_paper_white
from exam_photo.ink.ink_mask import (
    _MINIMUM_ABSOLUTE_DEPTH,
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

#: How far past the deepest ink the black point is set, as a multiple of the
#: ink depth. At 1.0 the single darkest pixel would map to pure black and every
#: other tone would be compressed beneath it; at 1.15 the deepest ink lands
#: near-black with a little headroom, which is what keeps a thumb impression's
#: densest area from flattening into a solid slab.
_BLACK_POINT_HEADROOM = 1.15

#: Dilation applied to the rejected-ink mask before it is whitened out, in
#: pixels of the rendered image. The rejection is computed on a downscaled copy,
#: so its boundary is coarse; without a margin the soft halo around a rejected
#: mass survives as a grey fringe.
_SUPPRESSION_MARGIN = 3


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


def _render(
    flattened: np.ndarray[Any, Any],
    ink_depth: float,
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
    white_point = 255.0 * (1.0 - _MINIMUM_ABSOLUTE_DEPTH)
    black_point = 255.0 * (1.0 - min(ink_depth * _BLACK_POINT_HEADROOM, 1.0))
    span = max(white_point - black_point, 1.0)

    rendered: np.ndarray[Any, Any] = (
        np.clip((flattened - black_point) / span, 0.0, 1.0) * 255.0
    )
    if keep is not None:
        rendered[~_dilate(keep, _KEEP_MARGIN)] = 255.0
    if suppress is not None and suppress.any():
        rendered[_dilate(suppress, _SUPPRESSION_MARGIN)] = 255.0
    return rendered


def prepare_ink_document(image: Image.Image) -> InkPreparation:
    """Prepare one photograph of a signature, thumb impression or declaration."""
    source = np.asarray(image.convert("RGB")).astype(np.float32)
    analysis, scale = _analysis_copy(source)

    cropped, sheet_mask, paper = crop_to_paper(analysis)
    estimate = estimate_paper_field(cropped, sheet_mask)
    flattened = flatten_to_paper_white(cropped, estimate)
    # Anything outside the sheet is not part of the document. Setting it to
    # white rather than cropping it away keeps the geometry simple and has the
    # same effect on every measurement that follows.
    flattened[~sheet_mask] = 255.0

    ink = detect_ink(flattened, sheet_mask)
    if ink.box is None:
        rendered = _render(flattened, max(ink.ink_depth, 1e-6), None, ink.rejected)
        return InkPreparation(
            image=Image.fromarray(rendered.astype(np.uint8)),
            paper=paper,
            ink=ink,
            crop_box=None,
            is_blank=True,
        )

    framed = framed_box(ink.box, flattened.shape[1], flattened.shape[0])

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
    final_ink = detect_ink(final_flat, region_mask)
    rendered = _render(
        final_flat,
        max(final_ink.ink_depth, 1e-6),
        final_ink.mask,
        final_ink.rejected,
    )

    return InkPreparation(
        image=Image.fromarray(rendered.astype(np.uint8)),
        paper=paper,
        ink=final_ink,
        crop_box=full_box,
        is_blank=False,
    )
