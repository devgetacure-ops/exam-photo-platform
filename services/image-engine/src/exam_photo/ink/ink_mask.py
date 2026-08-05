"""Telling ink from everything else still on the page.

After the paper has been located and its illumination divided out, what remains
dark is *mostly* ink. Not entirely. The reference input is a signature written
on the back of a printed receipt, and the receipt's printing shows through the
paper: a full page of ghosted text, upside down, sitting behind the signature.
It is real, it is on the page, and it must not reach the output -- the portal
wants a signature, not a signature over a menu.

Show-through separates from ink on contrast, not on colour. Both are grey-ish
or blue-ish; what differs is depth. Ink is laid on the surface at full opacity,
show-through is attenuated by the thickness of the paper. So the rule is a
relative one: measure the darkest ink present, and keep only marks that reach a
usable fraction of it.

That relative form matters more than the threshold value. A fixed cut-off would
be wrong for a pencil signature on the same paper, and wrong again for a bold
marker on a thin sheet. What is stable across those is that the writing the
candidate meant to submit is the darkest thing they put on the page.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
from PIL import Image

from exam_photo.models.geometry import BoundingBox

#: Percentile of the darkest pixels taken as "how dark is the real ink here",
#: expressed as a fraction from the dark end. Not the minimum, which on a JPEG
#: is a compression artefact rather than a measurement, and not a mean over the
#: whole mark, which a broad soft stroke would drag toward the paper.
#:
#: 0.1 rather than 1.0 because the reference is meaningless once the mark is
#: smaller than the percentile. A signature in the corner of an A4 sheet covers
#: well under 1% of it, and reading the depth at the 99th percentile then
#: measures paper, reports no ink present, and returns the page as blank --
#: which a synthetic case here does reproduce. At the 99.9th the same reading
#: holds down to a tenth of that size.
#:
#: The cost on the reference set is nil to slightly positive. Ink coverage
#: moves 6.00% -> 5.47% and 4.69% -> 4.69% on the two approved outputs, and the
#: hard photograph's crop *tightens* from 861 to 712 pixels wide, because a
#: deeper reference lifts the absolute threshold past more of the show-through.
_INK_DEPTH_PERCENTILE = 0.1

#: A mark is ink if it reaches this fraction of the way from paper to the
#: darkest ink present.
#:
#: Chosen by sweeping it against the reference set and reading ink coverage,
#: because coverage is the quantity the approved outputs actually pin down.
#: Percentage of the sheet classified as ink:
#:
#: | image                        | 0.35  | 0.45  | 0.55  | 0.65  | 0.75  |
#: |------------------------------|-------|-------|-------|-------|-------|
#: | approved signature, black    | 4.79  | 4.68  | 4.59  | 4.51  | 4.41  |
#: | approved signature, blue     | 8.14  | 6.96  | 5.87  | 4.89  | 3.85  |
#: | hard photograph, blue        | 8.01  | 7.08  | 5.22  | 3.89  | 2.86  |
#:
#: The hard photograph is the one that decides it. Its extra content is the
#: receipt printing showing through the paper, so the correct threshold is the
#: one that lands it on the same coverage as a clean capture of the same kind
#: of mark. At 0.55 it measures 5.22% against 4.59% and 5.87% for the two
#: approved outputs -- inside their range. At 0.35 it measures 8.01%, half
#: again as much ink as the signature contains, which is the show-through
#: arriving. At 0.75 it drops to 2.86%, below both, which is stroke being lost.
_INK_DEPTH_FRACTION = 0.55

#: Below this absolute depth nothing is ink, whatever the relative test says.
#:
#: Its job is the blank page. With no ink present the darkest 1% is paper
#: texture, and the relative test alone -- which measures everything against
#: the darkest thing present -- would faithfully promote that grain to a
#: signature. Measured after flattening, bare paper sits at median depth 0.000
#: on the two approved outputs and 0.021-0.046 on the two thumb captures, whose
#: paper is visibly textured. 0.10 clears all four.
#:
#: What has *not* been measured is the faint end: no pencil or dried-out-pen
#: sample exists in the reference set, so whether a genuinely pale mark clears
#: 0.10 is unknown. That is a gap in the set, not a claim about the bound.
_MINIMUM_ABSOLUTE_DEPTH = 0.10

#: Fraction of the ink bounding box's longer side added as margin on all four
#: sides.
#:
#: The approved outputs disagree considerably about how much white should
#: surround a signature. Margins as a fraction of the delivered frame measure
#: L 0.102 R 0.070 T 0.047 B 0.047 on one, and L 0.187 R 0.177 T 0.163 B 0.221
#: on the other -- a spread of 0.047 to 0.221 with no agreed value inside it.
#: 0.08 of the longer side lands the delivered margins inside that observed
#: range for both, which is as much as two samples can honestly support.
_INK_MARGIN_FRACTION = 0.08


@dataclass(frozen=True)
class InkMaskResult:
    """Which pixels are ink, and how confidently."""

    mask: np.ndarray[Any, Any]
    #: Tight box around the ink, before any margin is added. ``None`` when the
    #: page appears blank.
    box: BoundingBox | None
    #: Fraction of the searched area that is ink. The approved outputs measure
    #: 0.049-0.083; a value far above that suggests something other than
    #: writing was captured.
    coverage: float
    #: Depth of the darkest ink, 0.0-1.0 below paper white. Near zero means
    #: there is nothing on the page.
    ink_depth: float
    #: Pixels that were classified as ink and then rejected as not belonging to
    #: the document -- a finger, the desk beyond the sheet's edge. Carried so
    #: rendering can force them to paper. Rejecting them from the crop-box
    #: calculation alone leaves the object still drawn inside the crop.
    rejected: np.ndarray[Any, Any]


def _depth_below_paper(flattened: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    """How far below paper white each pixel sits, on 0.0-1.0.

    Taken from the channel *minimum*: a pixel is ink-like if **any** channel
    has gone dark. Bare paper, once flattened, is bright in all three, so its
    minimum is high and its depth near zero.

    The channel maximum is the tempting choice and it is wrong. A blue
    ballpoint keeps a strong blue channel, so its maximum stays high and it
    reads as barely marked. Measured on the reference photographs, the same
    approved outputs score at their 99th percentile: by maximum, 0.698 for the
    blue signature against 0.894 for the black one; by minimum, 0.903 and
    0.902. The maximum marks a blue signature down by a fifth purely for being
    blue, which puts it under any threshold set against black ink. The minimum
    ranks them together, which is what they are.

    A weighted luminance has the same defect more mildly and adds a channel
    weighting that has no meaning for ink.
    """
    depth: np.ndarray[Any, Any] = np.clip(1.0 - flattened.min(axis=2) / 255.0, 0.0, 1.0)
    return depth


#: Working edge for the edge-connectivity flood. The flood costs one pass per
#: pixel of the widest region it has to cross, so it is done small and the
#: verdict scaled back up. What it decides -- "does this mark run off the sheet"
#: -- is a property of large shapes and survives the downscale.
_CONNECTIVITY_EDGE = 400

#: Erosion steps that define "solid" at the connectivity working resolution.
#: Two steps clear anything under about five pixels across, which at a 400-pixel
#: working edge is handwriting: the reference signature's strokes measure 1-2
#: pixels there and vanish entirely, while the swallowed finger measures 40-90
#: pixels across and survives with room to spare.
_SOLID_EROSION_STEPS = 2


def drop_edge_connected(
    ink: np.ndarray[Any, Any], sheet: np.ndarray[Any, Any]
) -> np.ndarray[Any, Any]:
    """Remove marks that run off the edge of the located sheet.

    The reference photograph is held between finger and thumb, and one finger
    catches enough light to pass the paper test, so it joins the sheet as a
    single bright region rather than as an enclosed hole -- which puts it out of
    reach of the hole-size limit in ``paper_region``. What still distinguishes
    it is position: it is contiguous with the outside world, and a signature is
    not.

    Reaching the edge is necessary but deliberately **not sufficient**, and the
    reference photograph is what forced that. Cursive script is one long
    connected stroke, and the tail of this signature runs close enough to the
    sheet's edge to join it; rejecting every edge-connected mark deleted the
    whole signature and took ink coverage from 5.44% to 0.65%. The second
    condition is solidity. A finger is a filled mass dozens of pixels across;
    handwriting is a line a few pixels wide whatever route it takes. Only marks
    that are both edge-connected *and* survive an erosion are dropped.

    The cost is a genuinely broad mark pressed against the edge of the paper --
    a thumb impression on the very corner of the sheet. That is accepted, and
    it is also the case where the candidate has most likely run the impression
    off the page.
    """
    if not ink.any() or sheet.all():
        return ink

    height, width = ink.shape
    scale = _CONNECTIVITY_EDGE / max(height, width)
    if scale < 1.0:
        small_size = (max(1, int(width * scale)), max(1, int(height * scale)))
        small_ink = np.asarray(
            Image.fromarray((ink * 255).astype(np.uint8)).resize(
                small_size, resample=Image.Resampling.NEAREST
            )
        ).astype(bool)
        small_sheet = np.asarray(
            Image.fromarray((sheet * 255).astype(np.uint8)).resize(
                small_size, resample=Image.Resampling.NEAREST
            )
        ).astype(bool)
    else:
        small_ink, small_sheet = ink, sheet

    outside = ~small_sheet
    seed = small_ink & (
        np.roll(outside, 1, 0)
        | np.roll(outside, -1, 0)
        | np.roll(outside, 1, 1)
        | np.roll(outside, -1, 1)
        | outside
    )
    # The frame edge counts as outside too: a sheet filling the whole photograph
    # has no ``outside`` at all, and a mark running off the picture is in the
    # same position as one running off the paper.
    border = np.zeros_like(small_ink)
    border[0, :] = border[-1, :] = True
    border[:, 0] = border[:, -1] = True
    seed |= small_ink & border
    if not seed.any():
        return ink

    reached = seed
    for _ in range(max(small_ink.shape)):
        grown = reached.copy()
        grown[1:, :] |= reached[:-1, :]
        grown[:-1, :] |= reached[1:, :]
        grown[:, 1:] |= reached[:, :-1]
        grown[:, :-1] |= reached[:, 1:]
        grown &= small_ink
        if np.array_equal(grown, reached):
            break
        reached = grown

    # Solidity: only what survives an erosion is a mass rather than a line.
    solid = small_ink
    for _ in range(_SOLID_EROSION_STEPS):
        shrunk = solid.copy()
        shrunk[1:, :] &= solid[:-1, :]
        shrunk[:-1, :] &= solid[1:, :]
        shrunk[:, 1:] &= solid[:, :-1]
        shrunk[:, :-1] &= solid[:, 1:]
        solid = shrunk
    # Grown back so the whole mass is dropped, not just its core.
    for _ in range(_SOLID_EROSION_STEPS * 3):
        grown = solid.copy()
        grown[1:, :] |= solid[:-1, :]
        grown[:-1, :] |= solid[1:, :]
        grown[:, 1:] |= solid[:, :-1]
        grown[:, :-1] |= solid[:, 1:]
        solid = grown & small_ink
    reached &= solid

    if scale < 1.0:
        rejected = np.asarray(
            Image.fromarray((reached * 255).astype(np.uint8)).resize(
                (width, height), resample=Image.Resampling.NEAREST
            )
        ).astype(bool)
    else:
        rejected = reached
    kept: np.ndarray[Any, Any] = ink & ~rejected
    return kept


#: A local-density filter was written here and removed.
#:
#: The intent was to drop the residue of the sheet's edge -- what survives the
#: border erosion as a line of marks tracing where the paper met the desk --
#: on the theory that writing is locally dense and an edge artefact is not.
#: Measured on the reference photograph over the region holding that edge
#: against the region holding the signature, at three window sizes:
#:
#: | window | signature p10/p50/p90 | edge p10/p50/p90   |
#: |--------|-----------------------|--------------------|
#: | 11x11  | 0.182 / 0.289 / 0.397 | 0.083 / 0.231 / 0.405 |
#: | 21x21  | 0.116 / 0.184 / 0.261 | 0.036 / 0.172 / 0.254 |
#: | 41x41  | 0.090 / 0.129 / 0.175 | 0.019 / 0.095 / 0.177 |
#:
#: The distributions overlap almost completely at every scale, and the edge
#: region carries 2,243 ink pixels against the signature's 2,226 -- it is not
#: sparse residue at all, it is a line as substantial as the writing. A
#: threshold anywhere between them removes as much signature as edge, and the
#: version that shipped briefly changed ink coverage by 0.06 percentage points
#: while moving the crop box not at all.
#:
#: Removed rather than tuned, per the standing rule that a signal whose
#: reliability has not been demonstrated should not ship: a filter that cannot
#: fail is worse than no filter, because it reads as protection. The looseness
#: it was meant to fix is instead recorded as a known bound.


#: Gap that still counts as "together", as a fraction of the longer edge.
#: Writing is a run of marks separated by small gaps -- between letters, between
#: the two halves of a name -- and the whole run is one thing. At 0.025 a
#: 400-pixel working copy bridges 10 pixels, which merged every stroke of the
#: reference signature into a single cluster while leaving the sheet's edge, a
#: hundred pixels away across bare paper, on its own.
_CLUSTER_GAP_FRACTION = 0.025

#: A cluster is kept if it holds at least this share of the largest cluster's
#: ink. Not "keep only the largest": a signature and its separate initial, or a
#: declaration written on three lines, are several clusters and all of them
#: belong. Measured on the reference photograph, the signature cluster holds
#: 4,118 ink pixels and the sheet-edge cluster 1,942, a ratio of 0.47 -- so the
#: bound sits above that, and a second genuine line of writing would have to be
#: less than a fifth of the first before it were dropped.
_CLUSTER_MASS_RATIO = 0.55

#: Ceiling on how many clusters are examined. A page of writing is a handful;
#: anything past this is speckle and the loop is a runaway guard, not a policy.
_MAXIMUM_CLUSTERS = 12


def keep_dominant_clusters(ink: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    """Keep the marks that sit together, drop the ones that sit alone.

    The sheet's own edge survives everything before this. It is dark enough to
    be ink, it is not solid so the solidity test spares it, it is not sparse so
    a density test cannot see it -- measured, it carries 2,243 pixels at the
    same local density as the writing -- and it is not connected to the writing.
    What it is, is *far away*: it runs along the boundary of the page while the
    signature sits in the middle of it, and between them is bare paper.

    So the marks are grouped by proximity and the small distant groups are
    dropped. This is the test that finally separates them, and it is the right
    shape of test: "is this part of the writing" is a question about company,
    not about darkness or thickness.
    """
    if not ink.any():
        return ink

    height, width = ink.shape
    scale = _CONNECTIVITY_EDGE / max(height, width)
    if scale < 1.0:
        size = (max(1, int(width * scale)), max(1, int(height * scale)))
        small = np.asarray(
            Image.fromarray((ink * 255).astype(np.uint8)).resize(
                size, resample=Image.Resampling.NEAREST
            )
        ).astype(bool)
    else:
        small = ink
    if not small.any():
        return ink

    gap = max(1, round(max(small.shape) * _CLUSTER_GAP_FRACTION))
    bridged = small
    for _ in range(gap):
        spread = bridged.copy()
        spread[1:, :] |= bridged[:-1, :]
        spread[:-1, :] |= bridged[1:, :]
        spread[:, 1:] |= bridged[:, :-1]
        spread[:, :-1] |= bridged[:, 1:]
        bridged = spread

    remaining = bridged
    clusters: list[tuple[int, np.ndarray[Any, Any]]] = []
    for _ in range(_MAXIMUM_CLUSTERS):
        if not remaining.any():
            break
        ys, xs = np.nonzero(remaining)
        seed = np.zeros_like(remaining)
        seed[ys[0], xs[0]] = True
        for _ in range(sum(remaining.shape)):
            grown = seed.copy()
            grown[1:, :] |= seed[:-1, :]
            grown[:-1, :] |= seed[1:, :]
            grown[:, 1:] |= seed[:, :-1]
            grown[:, :-1] |= seed[:, 1:]
            grown &= remaining
            if np.array_equal(grown, seed):
                break
            seed = grown
        clusters.append((int((small & seed).sum()), seed))
        remaining = remaining & ~seed

    if not clusters:
        return ink

    best = max(mass for mass, _ in clusters)
    if best <= 0:
        return ink
    keep_small = np.zeros_like(small)
    for mass, region in clusters:
        if mass >= best * _CLUSTER_MASS_RATIO:
            keep_small |= region

    if scale < 1.0:
        keep = np.asarray(
            Image.fromarray((keep_small * 255).astype(np.uint8)).resize(
                (width, height), resample=Image.Resampling.NEAREST
            )
        ).astype(bool)
    else:
        keep = keep_small
    kept: np.ndarray[Any, Any] = ink & keep
    return kept if kept.any() else ink


def detect_ink(
    flattened: np.ndarray[Any, Any],
    sheet: "np.ndarray[Any, Any] | None" = None,
    cluster: bool = False,
) -> InkMaskResult:
    """Find the ink on a flattened, paper-white image."""
    depth = _depth_below_paper(flattened)
    ink_depth = float(np.percentile(depth, 100.0 - _INK_DEPTH_PERCENTILE))

    empty = np.zeros(depth.shape, dtype=bool)
    if ink_depth < _MINIMUM_ABSOLUTE_DEPTH:
        return InkMaskResult(
            mask=empty,
            box=None,
            coverage=0.0,
            ink_depth=ink_depth,
            rejected=empty,
        )

    threshold = max(ink_depth * _INK_DEPTH_FRACTION, _MINIMUM_ABSOLUTE_DEPTH)
    raw = depth >= threshold
    mask = drop_edge_connected(raw, sheet) if sheet is not None else raw
    if cluster:
        mask = keep_dominant_clusters(mask)
    rejected = raw & ~mask
    coverage = float(mask.mean())
    if not mask.any():
        return InkMaskResult(mask, None, 0.0, ink_depth, rejected)

    box = mass_trimmed_box(mask)
    return InkMaskResult(mask, box, coverage, ink_depth, rejected)


#: Fraction of ink pixels the box must contain. The remainder is discarded from
#: whichever edge is cheapest, which is what makes the box robust to specks.
#:
#: A plain extremal bounding box is not usable here. Ink detection returns a few
#: scattered pixels far from the writing -- a fibre in the paper, a speck of
#: dirt, the darker line where the sheet's edge curls -- and one such pixel in a
#: corner stretches the box to the whole sheet. Measured on the reference
#: photograph, the extremal box covered 100% of the located sheet while the
#: signature occupies about a fifth of it.
#:
#: 0.995 rather than 1.0 discards half a percent of ink mass. On the approved
#: outputs, where there are no specks, that costs the very tip of the lightest
#: stroke and moves the box by 1-3 pixels.
_INK_MASS_KEPT = 0.995


def mass_trimmed_box(mask: np.ndarray[Any, Any]) -> "BoundingBox | None":
    """Smallest box holding ``_INK_MASS_KEPT`` of the ink, trimmed per axis.

    Trimming is done independently on each axis using the ink's row and column
    profiles. The alternative -- dropping small connected components -- also
    works and costs a labelling pass over a full-resolution mask; the profiles
    are two sums and answer the same question for this shape of noise.
    """
    if not mask.any():
        return None
    total = float(mask.sum())
    budget = total * (1.0 - _INK_MASS_KEPT) / 2.0

    def bounds(profile: np.ndarray[Any, Any]) -> tuple[int, int]:
        cumulative = np.cumsum(profile)
        low = int(np.searchsorted(cumulative, budget, side="left"))
        high = int(np.searchsorted(cumulative, total - budget, side="left"))
        return min(low, profile.size - 1), min(max(high, low), profile.size - 1)

    top, bottom = bounds(mask.sum(axis=1).astype(np.float64))
    left, right = bounds(mask.sum(axis=0).astype(np.float64))
    return BoundingBox(
        left=float(left),
        top=float(top),
        right=float(right + 1),
        bottom=float(bottom + 1),
    )


def framed_box(box: BoundingBox, width: int, height: int) -> BoundingBox:
    """Grow the ink box by the margin the approved outputs carry."""
    margin = max(box.width, box.height) * _INK_MARGIN_FRACTION
    left = max(0.0, box.left - margin)
    top = max(0.0, box.top - margin)
    right = min(float(width), box.right + margin)
    bottom = min(float(height), box.bottom + margin)
    return BoundingBox(
        left=float(round(left)),
        top=float(round(top)),
        right=float(max(round(left) + 1, round(right))),
        bottom=float(max(round(top) + 1, round(bottom))),
    )
