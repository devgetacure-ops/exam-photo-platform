"""Strand-level alpha in the matte's soft band, read from the photograph itself.

BiRefNet predicts *where the subject is*, not *how much of each pixel is hair*.
On fine or curly hair its boundary is a smooth hull 5-30 px wide that ignores
the strands, and compositing that hull over white reads as a milky smear: the
flyaway strands the original shows are gone and the crown looks airbrushed.

Where the background behind the hair is plain -- the common case, a wall -- the
photograph already says how much of each edge pixel is hair: a pixel's colour
lies between the local background colour B and the local hair colour F, and its
position on that line is its alpha (``alpha = (I - B) . (F - B) / |F - B|^2``).
This module estimates B and F from the model's own confident pixels nearby and
moves alpha toward that estimate, **only** where the estimate can be trusted:

* the background around the pixel is plain (low local colour variance), and
* hair and background differ clearly in colour.

Where either fails -- skin against a skin-coloured wall, dark hair against a
dark room, a busy background -- the weight is zero and the model's alpha is
returned unchanged. So the change can only make the edge follow the photograph
more closely, never invent an edge the photograph does not show; and a guard
rejects the whole correction if it would move the matte by more than a soft
band's worth. See DEC-138.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from exam_photo.providers.refiners.morphological_refiner import box_filter


@dataclass(frozen=True)
class StrandMattingResult:
    alpha: np.ndarray[Any, Any]
    applied: bool
    band_pixels: int
    changed_pixels: int
    mean_abs_change: float
    reason: str


# Confident regions the colour estimates are taken from.
_DEFINITE_BG = 0.02
_DEFINITE_FG = 0.98
# How far outside the model's soft band a strand may be recovered (px). Flyaway
# strands sit just beyond BiRefNet's hull; further out is background.
_OUTSIDE_REACH = 6
# How far inside the hull a gap between curls may be opened (px).
_INSIDE_REACH = 3
# Colour separation (RGB distance, 0-1 scale) below which hair and background
# are too alike to read alpha from colour, and the span over which trust ramps.
_SEPARATION_MIN = 0.12
_SEPARATION_RAMP = 0.15
# How far (RGB distance) a background pixel may sit from the local wall colour
# and still count as wall when the wall is re-estimated without the strands.
_WALL_SIGMA = 0.10
# Output pixels per source pixel above which per-pixel alpha shows as steps.
# Measured on the labelled set: 0.7-0.9x improved; 1.4x (33), 1.8x (35, 4) and
# 2.5x (38) turned the soft fringe into a staircase.
_MAX_MAGNIFICATION = 1.35
_MAGNIFICATION_RAMP = 0.25
# Distance (RGB, 0-1) from the wall-to-hair line beyond which a pixel is not a
# mix of the two -- a highlight, a reflection -- and its colour says nothing
# about alpha; trust falls to zero across the ramp below it.
_RESIDUAL_MAX = 0.09
_RESIDUAL_RAMP = 0.05
# Local background standard deviation above which the background is too busy.
_PLAIN_MAX = 0.08
_PLAIN_RAMP = 0.04
# A recovered pixel outside the hull must read as clearly hair, not noise.
_OUTSIDE_MIN_ALPHA = 0.55
# A pixel is only made more transparent if it reads as clearly background.
_INSIDE_MAX_ALPHA = 0.2
# How much of a change survives relative to its 3x3 neighbourhood: a one-pixel
# line keeps 3/9 x 2.4 = 80%, an isolated pixel 1/9 x 2.4 = 27%.
_COHERENCE = 2.4
# Snap the last few percent at each end so wall grain does not become a veil.
_SNAP = 0.02
# The whole correction is refused if it moves the band this much on average.
_MAX_MEAN_CHANGE = 0.30


def _dilate(mask: np.ndarray[Any, Any], radius: int) -> np.ndarray[Any, Any]:
    if radius <= 0:
        return mask
    return box_filter(mask.astype(np.float32), radius) > 0.0


def _normalised_mean(
    image: np.ndarray[Any, Any], weight: np.ndarray[Any, Any], radius: int
) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any], np.ndarray[Any, Any]]:
    """Mean and standard deviation of ``image`` over the weighted neighbourhood."""
    w = weight.astype(np.float32)
    support = box_filter(w, radius)
    safe = np.maximum(support, 1e-6)
    mean = np.stack(
        [box_filter(image[..., c] * w, radius) / safe for c in range(3)], -1
    )
    sq = np.stack(
        [box_filter(image[..., c] ** 2 * w, radius) / safe for c in range(3)], -1
    )
    var = np.clip(sq - mean**2, 0.0, None).sum(-1)
    return mean, np.sqrt(var), support


def recover_strand_alpha(
    image_rgb: np.ndarray[Any, Any],
    alpha: np.ndarray[Any, Any],
    radius: int | None = None,
    magnification: float = 1.0,
) -> StrandMattingResult:
    """Return ``alpha`` with its soft band moved toward the photograph's own edge.

    ``image_rgb`` is HxWx3 in [0, 1]; ``alpha`` is HxW float32 in [0, 1], the
    model's matte for the same pixels. Pixels outside the band are returned
    bit-for-bit unchanged.
    """
    if image_rgb.shape[:2] != alpha.shape:
        raise ValueError("image and alpha must have the same height and width")
    a0 = np.clip(alpha.astype(np.float32), 0.0, 1.0)
    h, w = a0.shape
    # Where the output enlarges the source, every source pixel becomes a block,
    # and a crisp per-pixel edge becomes a staircase -- worse than the model's
    # soft one. Full strength at about 1:1, none by 1.35x enlargement.
    strength = float(
        np.clip((_MAX_MAGNIFICATION - magnification) / _MAGNIFICATION_RAMP, 0.0, 1.0)
    )
    if strength <= 0.0:
        return StrandMattingResult(
            a0, False, 0, 0, 0.0, f"source enlarged {magnification:.2f}x"
        )
    if radius is None:
        radius = int(max(6, min(24, round(min(h, w) * 0.03))))

    soft = (a0 > _DEFINITE_BG) & (a0 < _DEFINITE_FG)
    if not soft.any():
        return StrandMattingResult(a0, False, 0, 0, 0.0, "no soft band")
    bg = a0 <= _DEFINITE_BG
    fg = a0 >= _DEFINITE_FG
    near_soft = _dilate(soft, _OUTSIDE_REACH)
    band = soft | (near_soft & bg) | (_dilate(soft, _INSIDE_REACH) & fg)

    img = image_rgb.astype(np.float32)
    # The soft band can be as wide as the neighbourhood, so a pixel deep in it
    # may have background within reach but no confident hair: hair colour is
    # read from twice as far. Hair colour varies slowly; walls are what must be
    # judged locally, because plainness is a local property.
    b_mean, _b_std, _ = _normalised_mean(img, bg, radius)
    # The flyaway strands the model missed are themselves in its "background",
    # and they would make the wall look busy and its colour darker. A second
    # pass keeps only background pixels that look like the wall around them.
    wall_like = np.exp(-((img - b_mean) ** 2).sum(-1) / (2 * _WALL_SIGMA**2))
    b_mean, b_std, b_support = _normalised_mean(img, bg * wall_like, radius)
    f_mean, _f_std, f_support = _normalised_mean(img, fg, 2 * radius)

    d = f_mean - b_mean
    sep = np.sqrt((d**2).sum(-1))
    ac = ((img - b_mean) * d).sum(-1) / np.maximum((d**2).sum(-1), 1e-6)
    ac = np.clip(ac, 0.0, 1.0)

    # A true edge pixel is a mix of two colours, so it lies on the line from
    # wall to hair. A highlight on shiny hair is as light as the wall but a
    # different colour -- it lies off that line -- and must not be read as wall.
    residual = np.sqrt(((img - (b_mean + ac[..., None] * d)) ** 2).sum(-1))

    trust = np.clip((sep - _SEPARATION_MIN) / _SEPARATION_RAMP, 0.0, 1.0)
    trust *= np.clip((_RESIDUAL_MAX - residual) / _RESIDUAL_RAMP, 0.0, 1.0)
    trust *= np.clip((_PLAIN_MAX - b_std) / _PLAIN_RAMP, 0.0, 1.0)
    # both sides must actually be present nearby, or the estimate is a guess
    area = float((2 * radius + 1) ** 2)
    trust *= np.clip(b_support / (0.15 * area), 0.0, 1.0)
    trust *= np.clip(f_support / (0.15 * 4 * area), 0.0, 1.0)
    trust *= band * strength
    # No hard seam where trust switches on or off -- but smoothing may only
    # lower a pixel's trust, never lend it trust its own colour did not earn.
    trust = np.minimum(trust, box_filter(trust.astype(np.float32), 1) / 9.0) * band

    # outside the hull, only a clear strand may appear
    outside = band & bg
    ac = np.where(outside & (ac < _OUTSIDE_MIN_ALPHA), 0.0, ac)
    # Anywhere in the band, a pixel may only be made *more* transparent where
    # it reads as clearly wall. Hair the camera lightened at the edge, or a
    # highlight, reads as half wall; thinning it leaves white specks inside the
    # silhouette, which is worse than the model's own soft value.
    ac = np.where((ac < a0) & (ac > _INSIDE_MAX_ALPHA), a0, ac)

    delta = (trust * (ac - a0)).astype(np.float32)
    # A change must be backed by its neighbours. A strand is a line and keeps
    # most of its change; a lone pixel of wall grain or JPEG ringing is a speck
    # and keeps almost none of it -- that speck reads as salt on the hairline.
    for sign in (1.0, -1.0):
        part = np.maximum(sign * delta, 0.0)
        support = box_filter(part, 1) / 9.0
        delta = np.where(
            sign * delta > 0, sign * np.minimum(part, _COHERENCE * support), delta
        )
    out = a0 + delta
    out = np.where(out < _SNAP, 0.0, np.where(out > 1.0 - _SNAP, 1.0, out))
    out = np.where(band, out, a0).astype(np.float32)

    changed = np.abs(out - a0) > 1e-3
    n_band = int(band.sum())
    mean_change = float(np.abs(out - a0)[band].mean()) if n_band else 0.0
    if mean_change > _MAX_MEAN_CHANGE:
        return StrandMattingResult(
            a0, False, n_band, 0, mean_change, "change exceeds guard"
        )
    return StrandMattingResult(
        out, True, n_band, int(changed.sum()), mean_change, "applied"
    )
