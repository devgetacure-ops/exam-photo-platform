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
from exam_photo.ink.ink_mask import InkMaskResult, detect_ink, framed_box
from exam_photo.ink.paper_region import PaperRegion, crop_to_paper
from exam_photo.models.geometry import BoundingBox

#: Longest edge the analysis runs at. The stages measure distributions and
#: locate a rectangle; neither needs sensor resolution, and the reference
#: captures arrive at up to 4095 px. The *rendering* is done on the original
#: pixels, so nothing is lost -- only the search is downscaled.
_ANALYSIS_EDGE = 1400

#: Depth at or above which ink is rendered at full strength, as a fraction of
#: the darkest ink present. Below the ink threshold everything goes to white;
#: between the two, the stroke's own edge softness is preserved by a linear
#: ramp. Without the ramp a stroke gets a hard jagged border and stops looking
#: like handwriting.
_FULL_STRENGTH_FRACTION = 0.85


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


def _render(
    flattened: np.ndarray[Any, Any], depth: np.ndarray[Any, Any], ink_depth: float
) -> np.ndarray[Any, Any]:
    """Paper to white, ink to full strength, hue preserved.

    The ramp between the two thresholds is what keeps a stroke looking drawn
    rather than stencilled: a stroke's edge is genuinely part-covered, and
    forcing every ink pixel to full opacity turns a smooth curve into a
    staircase at any size the portal displays it.
    """
    ink_floor = max(ink_depth * 0.55, 0.10)
    ink_ceiling = max(ink_depth * _FULL_STRENGTH_FRACTION, ink_floor + 1e-3)
    alpha = np.clip((depth - ink_floor) / (ink_ceiling - ink_floor), 0.0, 1.0)

    # The ink's own colour, taken from the pixels that are unambiguously ink so
    # a part-covered edge does not dilute it. Preserved rather than forced to
    # black: a blue signature is blue, and several bodies require ink of a
    # stated colour, so turning every mark black would destroy the evidence
    # that the candidate complied.
    core = depth >= ink_ceiling
    if core.sum() >= 16:
        ink_colour = np.percentile(flattened[core], 20.0, axis=0)
    else:
        ink_colour = np.array([0.0, 0.0, 0.0], dtype=np.float32)

    white = np.full_like(flattened, 255.0)
    rendered: np.ndarray[Any, Any] = (
        white * (1.0 - alpha[:, :, None])
        + ink_colour[None, None, :] * alpha[:, :, None]
    )
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
        depth = np.clip(1.0 - flattened.min(axis=2) / 255.0, 0.0, 1.0)
        rendered = _render(flattened, depth, max(ink.ink_depth, 1e-6))
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
    final_depth = np.clip(1.0 - final_flat.min(axis=2) / 255.0, 0.0, 1.0)
    final_ink = detect_ink(final_flat, region_mask)
    rendered = _render(final_flat, final_depth, max(final_ink.ink_depth, 1e-6))

    return InkPreparation(
        image=Image.fromarray(rendered.astype(np.uint8)),
        paper=paper,
        ink=final_ink,
        crop_box=full_box,
        is_blank=False,
    )
