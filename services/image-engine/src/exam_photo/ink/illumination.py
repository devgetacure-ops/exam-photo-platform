"""Estimating the paper's illumination, so it can be divided back out.

A phone photograph of a sheet of paper is not evenly lit. There is a gradient
across the sheet, often a shadow from the hand holding it, and a colour cast
from whatever light was in the room -- the pale yellow that makes a scan look
old. All three are properties of the capture, not of the document, and all
three are removed by the same operation: estimate what the *paper alone* looks
like at every point, then divide the image by it.

The estimate is built on a coarse tile grid rather than by blurring the image,
and that choice is the whole difficulty of this module.

The obvious background estimate -- max-filter the image and blur it -- works
for thin strokes and fails badly on a thumb impression. Inside a solid inked
blob the local maximum is still ink, so the estimated "paper" there is the ink
itself, the division returns roughly 1.0, and the impression is erased from its
own centre outward. Measured on the reference thumb photograph, a 9-pixel
max-filter left the impression sitting at luminance 160-200 against paper at
255, when it should have been the darkest thing in the frame.

The tile grid avoids this by refusing to guess. A tile whose bright end is far
below the sheet's overall paper level is not paper -- it is covered by ink, or
by a hand, or it is off the sheet -- so it is marked unknown and filled in from
its neighbours instead of being believed.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
from PIL import Image

#: Tiles across the longer edge. At 12, a 1000-pixel image gets ~83-pixel
#: tiles: coarse enough that a tile usually contains some bare paper even where
#: a signature crosses it, fine enough to follow the illumination gradient of a
#: hand-held sheet. The grid is resolution-independent by construction, so the
#: estimate does not change when the same photograph arrives at a different
#: size.
_TILE_COUNT = 12

#: Percentile taken within a tile as its paper level. The bright end rather than
#: the mean, because a tile is a mixture of paper and ink and only the paper
#: part is being measured. Not the maximum: a specular highlight off a glossy
#: sheet is brighter than the paper and would drag the estimate up, taking the
#: real paper with it into grey.
_TILE_PAPER_PERCENTILE = 90.0

#: A tile is believed only if its paper level reaches this fraction of the
#: sheet's overall level. Below it the tile is mostly not paper.
#:
#: Measured across the reference set, tile ratio against the sheet level:
#:
#: - Thumb impression, close capture: tiles lying inside the impression measure
#:   0.68-0.78; every bare-paper tile measures 0.90-1.03. The bound at 0.80
#:   falls in the gap.
#: - Thumb impression, distant capture: 0.87-1.03 throughout. The impression is
#:   small against the frame, so no tile is ink-dominated and every tile is
#:   believed, which is the right answer.
#: - Both approved outputs: every tile at 1.00. The field comes out flat and
#:   the division is a no-op, so running this on an already-clean scan changes
#:   nothing.
#: - Hard signature photograph: paper 0.90-1.09, desk 0.07-0.20, and the hand
#:   spread continuously across 0.50-0.90 with no gap anywhere. **This case does
#:   not separate on this statistic and is not asked to.** The hand and the desk
#:   are removed by cropping to the paper region first (see
#:   ``ink.paper_region``); by the time this runs, the frame is nearly all
#:   paper and the bound only has to reject ink.
_TILE_VALID_RATIO = 0.80

#: Iterations of neighbour-fill for unknown tiles. Each pass reaches one tile
#: further, so this spans a run of unknown tiles up to 24 wide -- twice the grid
#: -- which is more than an image entirely covered in ink could need.
_FILL_ITERATIONS = 24


@dataclass(frozen=True)
class PaperFieldEstimate:
    """The estimated appearance of bare paper at every pixel, per channel."""

    field: np.ndarray[Any, Any]
    #: Fraction of tiles that held believable paper. Low values mean the
    #: estimate is mostly interpolation, which is worth reporting rather than
    #: hiding: it is the signal that the photograph is mostly not paper.
    paper_tile_fraction: float
    #: The sheet's overall paper level, 0-255, before any correction. A low
    #: value means an underexposed capture.
    paper_level: float


def _tile_bounds(length: int, count: int) -> list[tuple[int, int]]:
    edges = np.linspace(0, length, count + 1).round().astype(int)
    return [(int(edges[i]), int(max(edges[i + 1], edges[i] + 1))) for i in range(count)]


def _fill_unknown(grid: np.ndarray[Any, Any], known: np.ndarray[Any, Any]) -> None:
    """Fill unknown tiles from their known neighbours, in place.

    Repeated averaging of whatever neighbours are already known. It is a
    diffusion rather than an extrapolation on purpose: an unknown region gets
    the illumination of the paper that surrounds it, which is the most that can
    honestly be said about paper nobody can see.
    """
    for _ in range(_FILL_ITERATIONS):
        if known.all():
            return
        padded_value = np.pad(grid, ((1, 1), (1, 1), (0, 0)), mode="edge")
        padded_known = np.pad(known, ((1, 1), (1, 1)), mode="edge").astype(np.float32)
        total = np.zeros_like(grid)
        weight = np.zeros_like(known, dtype=np.float32)
        for dy in (0, 1, 2):
            for dx in (0, 1, 2):
                if dy == 1 and dx == 1:
                    continue
                h, w = known.shape
                neighbour_known = padded_known[dy : dy + h, dx : dx + w]
                neighbour_value = padded_value[dy : dy + h, dx : dx + w, :]
                total += neighbour_value * neighbour_known[:, :, None]
                weight += neighbour_known
        newly = (~known) & (weight > 0)
        if not newly.any():
            return
        grid[newly] = total[newly] / weight[newly][:, None]
        known |= newly


def estimate_paper_field(
    rgb: np.ndarray[Any, Any],
    paper_mask: "np.ndarray[Any, Any] | None" = None,
) -> PaperFieldEstimate:
    """Estimate bare paper's appearance at every pixel, per colour channel.

    Per channel rather than on luminance alone, because the room's colour cast
    is exactly a per-channel difference in the paper level. Dividing each
    channel by its own field neutralises the cast in the same pass that
    flattens the shadow, and leaves the ink's own hue untouched -- the ink is
    not what the field was measured from.

    ``paper_mask`` excludes pixels known not to be the sheet. Without it, a
    tile straddling the edge of the paper measures the hand holding it and
    reports that as the illumination there, which brightens the neighbouring
    paper toward the hand's tone.
    """
    height, width = rgb.shape[:2]
    longer = max(height, width)
    rows = max(2, round(_TILE_COUNT * height / longer))
    cols = max(2, round(_TILE_COUNT * width / longer))
    row_bounds = _tile_bounds(height, rows)
    col_bounds = _tile_bounds(width, cols)

    grid = np.zeros((rows, cols, 3), dtype=np.float32)
    sampled = np.zeros((rows, cols), dtype=bool)
    for r, (y0, y1) in enumerate(row_bounds):
        for c, (x0, x1) in enumerate(col_bounds):
            tile = rgb[y0:y1, x0:x1, :].reshape(-1, 3)
            if paper_mask is not None:
                keep = paper_mask[y0:y1, x0:x1].reshape(-1)
                # A tile needs enough sheet in it to be measured at all. Below a
                # quarter, the percentile is being taken over a handful of
                # pixels at the sheet's edge, which is exactly where the
                # illumination is least representative.
                if keep.mean() < 0.25:
                    continue
                tile = tile[keep]
                if tile.size == 0:
                    continue
            grid[r, c, :] = np.percentile(tile, _TILE_PAPER_PERCENTILE, axis=0)
            sampled[r, c] = True

    # The sheet's own level, taken from the brighter tiles so that a photograph
    # which is half desk is still measured against its paper.
    luminance = grid.max(axis=2)
    if sampled.any():
        paper_level = float(np.percentile(luminance[sampled], 75))
    else:
        paper_level = float(np.percentile(luminance, 75))
    known = sampled & (luminance >= paper_level * _TILE_VALID_RATIO)
    paper_tile_fraction = float(known.mean())

    if not known.any():
        # Nothing in the frame looks like paper. Fall back to a flat field at
        # the brightest level present, which leaves the image essentially
        # unchanged rather than inventing a correction from nothing.
        flat = np.full(
            (height, width, 3), max(float(luminance.max()), 1.0), dtype=np.float32
        )
        return PaperFieldEstimate(flat, paper_tile_fraction, paper_level)

    _fill_unknown(grid, known.copy())

    # Bilinear upsample of the grid to full resolution. The grid is small, so
    # this is cheap, and the smoothness is wanted: illumination varies slowly
    # and a field with tile edges in it would print those edges onto the paper.
    #
    # A tile's value describes its brightest content, which sits somewhere
    # inside the tile rather than at its centre, and the outermost half-tile has
    # nothing beyond it to interpolate against. On a gentle gradient this is
    # invisible; on a harsh one it under-corrects the darkest edge. Measured on
    # a synthetic 45% falloff across the page, the darkest edge recovers to 192
    # of 255 while the rest of the sheet reaches white -- the gradient is
    # reduced by roughly half rather than removed.
    #
    # Left as is deliberately. Every reference photograph flattens to paper
    # median 255, so the residual is below what real captures exhibit, and an
    # extrapolated-grid version of this step was tried and made the field
    # unstable on small images. The bound is recorded here rather than hidden;
    # a capture with a genuinely harsh gradient is the case that would need it.
    field_image = Image.fromarray(np.clip(grid, 1.0, 255.0).astype(np.uint8)).resize(
        (width, height), resample=Image.Resampling.BILINEAR
    )
    field = np.asarray(field_image).astype(np.float32)
    return PaperFieldEstimate(np.maximum(field, 1.0), paper_tile_fraction, paper_level)


def flatten_to_paper_white(
    rgb: np.ndarray[Any, Any], estimate: PaperFieldEstimate
) -> np.ndarray[Any, Any]:
    """Divide the illumination back out, putting bare paper at pure white.

    Values above white clip rather than being rescaled. A brighter-than-paper
    pixel is a highlight, and preserving the difference between two shades of
    white would be preserving nothing.
    """
    flattened: np.ndarray[Any, Any] = np.clip(rgb / estimate.field * 255.0, 0.0, 255.0)
    return flattened
