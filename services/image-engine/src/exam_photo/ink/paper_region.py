"""Finding the sheet of paper inside a photograph of one.

The reference input for this module is a phone photograph of a signature on the
back of a receipt: the sheet occupies rather less than half the frame, a hand
holds it from above, and the rest is a dark desk. Two thirds of that image is
not paper, and both of the things that are not paper would wreck the steps that
follow -- the desk is darker than any ink and would dominate a tonal stretch,
and the hand is a large mid-tone that an illumination estimate would read as
badly-lit paper.

The test is brightness *and* colourlessness together, because neither alone
separates the three. Paper is bright and grey. The desk is dark and grey. A
hand is mid-bright and distinctly orange. Only the conjunction picks out paper,
and the two thresholds are relative to the frame's own brightest content so
that an underexposed capture is judged on its own terms rather than against an
absolute that assumes good light.
"""

from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
from PIL import Image

from exam_photo.models.geometry import BoundingBox

#: Working resolution for the search. The paper's outline is a large, smooth
#: shape; resolving it at full sensor resolution costs time and buys nothing,
#: and the result is a rectangle that gets scaled back up.
_WORKING_EDGE = 320

#: A pixel counts as paper-bright at or above this fraction of the frame's
#: bright level.
#:
#: This bound is deliberately loose, because measurement showed brightness does
#: not separate paper from anything. Sampled regions of the hard signature
#: photograph, as a fraction of the frame's p98 brightness (242):
#:
#: | region            | p5   | p95  |
#: |-------------------|------|------|
#: | paper, clean      | 0.88 | 0.96 |
#: | paper, near ink   | 0.74 | 1.03 |
#: | paper, shadow edge| 0.11 | 0.83 |
#: | hand, lit finger  | 0.45 | 0.98 |
#: | hand, upper       | 0.38 | 0.60 |
#: | desk, under paper | 0.65 | 0.73 |
#: | desk, top-left    | 0.03 | 0.60 |
#:
#: The ranges overlap everywhere: the paper's shadowed edge is darker than the
#: desk, and a blown-out finger is brighter than clean paper. A bound tight
#: enough to exclude the hand would amputate the shadowed edge of the sheet.
#: 0.45 is set to drop only what is unambiguously in shadow, and the
#: discrimination is left to saturation below.
_BRIGHT_RATIO = 0.45

#: A pixel counts as paper-grey below this saturation. **This is the test that
#: does the work.** Same regions, same photograph:
#:
#: | region            | p5    | p50   | p95   |
#: |-------------------|-------|-------|-------|
#: | paper, clean      | 0.046 | 0.057 | 0.070 |
#: | paper, near ink   | 0.051 | 0.060 | 0.317 |
#: | paper, shadow edge| 0.036 | 0.062 | 0.500 |
#: | hand, upper       | 0.566 | 0.613 | 0.653 |
#: | hand, thumb       | 0.367 | 0.600 | 0.670 |
#: | desk, under paper | 0.465 | 0.523 | 0.592 |
#: | desk, top-left    | 0.000 | 0.594 | 0.657 |
#:
#: Paper sits at 0.036-0.070 through its body; skin and desk sit at 0.37-0.73
#: through theirs. The bound at 0.20 is inside that gap with room on both
#: sides. The upper tails on the paper rows are the ink and the shadow boundary,
#: which are supposed to be excluded -- they leave holes in the mask, and a
#: bounding box does not care about holes.
#:
#: The known failure is a blown-out highlight on a finger, which measures 0.013
#: and passes both tests. It is answered structurally rather than by tuning:
#: only the largest connected region is taken, and a highlight is never the
#: largest thing in a photograph of a document.
#:
#: A tinted sheet -- the pale green of some application forms -- also measures
#: under 0.20, which is intended. The test is for "not skin", not for "white".
_GREY_SATURATION = 0.20

#: The paper must occupy at least this fraction of the frame for the search to
#: claim it found a sheet. Below it, the largest bright-grey blob is more likely
#: a highlight than a document, and reporting no region is better than cropping
#: to a reflection.
_MINIMUM_AREA_FRACTION = 0.02

#: Grown outward by this fraction of the region's own size before cropping.
#: The mask tends to stop just inside the sheet where the edge is in shadow,
#: and a signature written close to the edge would otherwise lose its tail.
_REGION_PADDING = 0.02

#: Largest enclosed region that counts as a hole in the sheet rather than
#: something the sheet has merely surrounded. See ``_fill_holes``.
_MAXIMUM_HOLE_FRACTION = 0.02

#: Erosion steps applied to the sheet mask, at the working resolution, when the
#: sheet's own edge is visible in the frame. The paper/background boundary
#: leaves a band of shadow and partial pixels that reads as ink all the way
#: round, and it is that band -- not the writing -- that holds the crop box open
#: across the whole sheet. Six steps at a 320-pixel working edge is a border of
#: roughly 2%.
_EROSION_STEPS_BORDERED = 6

#: Erosion steps when no sheet edge is in frame, because the image is already a
#: crop or a scan. Then there is no boundary band to remove and the "sheet" is
#: the whole picture, so eroding eats the mark itself: measured on an approved
#: signature output, six steps took its delivered aspect from 3.84 to 4.14 by
#: trimming the strokes nearest the edge. Two steps still clears the one-to-three
#: pixel rim that JPEG ringing leaves at a hard border.
_EROSION_STEPS_FULL = 2

#: Below this share of the frame, the sheet is taken to have a visible edge and
#: the wider erosion applies. The reference photographs sit either side of it
#: with room to spare: the hand-held slip occupies 0.40 of its frame, while the
#: already-cropped captures occupy 0.90 to 1.00.
_BORDERED_AREA_FRACTION = 0.85


@dataclass(frozen=True)
class PaperRegion:
    """Where the sheet is, and how confident the search is that it is a sheet."""

    box: BoundingBox
    #: Per-pixel sheet membership at the input's resolution, holes filled.
    #:
    #: The box alone is not enough and the reference photograph shows why: the
    #: sheet is held between finger and thumb, so its bounding box still
    #: contains a wedge of hand at each side and a corner of desk. Ink detection
    #: run inside that box reads the hand as the darkest thing on the page. The
    #: mask is what lets those pixels be set aside.
    mask: np.ndarray[Any, Any]
    #: Fraction of the frame the sheet occupies. Near 1.0 means the photograph
    #: is already a scan or a tight crop.
    area_fraction: float
    #: True when the search found nothing sheet-like and the box is the whole
    #: frame. The caller still gets a usable box; it just carries no claim.
    is_fallback: bool


def _label_largest(mask: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    """Return the largest 4-connected component of a boolean mask.

    A two-pass union-find labelling. The alternative -- iterative dilation
    until stable -- is simpler to write and unboundedly slower on exactly the
    input that matters, a sheet spanning the frame.
    """
    height, width = mask.shape
    labels = np.zeros((height, width), dtype=np.int32)
    parent: list[int] = [0]

    def find(x: int) -> int:
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:
            parent[x], x = root, parent[x]
        return root

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    for y in range(height):
        row = mask[y]
        for x in range(width):
            if not row[x]:
                continue
            up = labels[y - 1, x] if y > 0 else 0
            left = labels[y, x - 1] if x > 0 else 0
            if up and left:
                labels[y, x] = min(up, left)
                union(up, left)
            elif up or left:
                labels[y, x] = up or left
            else:
                parent.append(len(parent))
                labels[y, x] = len(parent) - 1

    if len(parent) == 1:
        return np.zeros_like(mask)

    resolved = np.array([find(i) for i in range(len(parent))], dtype=np.int32)
    flat = resolved[labels]
    counts = np.bincount(flat.ravel())
    counts[0] = 0
    if counts.max() == 0:
        return np.zeros_like(mask)
    largest: np.ndarray[Any, Any] = flat == int(counts.argmax())
    return largest


def _fill_holes(mask: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    """Close the mask over small regions fully enclosed by it.

    The brightness-and-greyness test excludes the ink along with the hand,
    because ink is neither bright nor grey. That leaves the signature as a set
    of holes punched through the middle of the sheet -- and a mask with the
    signature missing would set the signature aside as "not paper", which is
    the one thing on the page that must survive.

    Only *small* holes are closed, and the size limit is load-bearing rather
    than defensive. On the reference photograph a blown-out highlight on one
    finger passes the paper test, which bridges that finger to the sheet; the
    finger's own shadowed side is then enclosed between the highlight and the
    sheet edge, and unrestricted filling adopts the whole finger as paper. Ink
    detection then reports it, and since it reaches the frame edge it stretches
    the crop to the full sheet. Measured on that photograph, the swallowed
    finger is 6.8% of the sheet's area while the largest genuine hole -- the
    thickest part of a signature stroke -- is 0.05%. The limit at 2% is two
    orders of magnitude above the strokes and well under the finger.
    """
    background = ~mask
    height, width = mask.shape
    labels = np.zeros((height, width), dtype=np.int32)
    parent: list[int] = [0]

    def find(x: int) -> int:
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:
            parent[x], x = root, parent[x]
        return root

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    for y in range(height):
        row = background[y]
        for x in range(width):
            if not row[x]:
                continue
            up = labels[y - 1, x] if y > 0 else 0
            left = labels[y, x - 1] if x > 0 else 0
            if up and left:
                labels[y, x] = min(up, left)
                union(up, left)
            elif up or left:
                labels[y, x] = up or left
            else:
                parent.append(len(parent))
                labels[y, x] = len(parent) - 1

    if len(parent) == 1:
        return mask

    resolved = np.array([find(i) for i in range(len(parent))], dtype=np.int32)
    flat = resolved[labels]
    outside = set(flat[0, :].tolist()) | set(flat[-1, :].tolist())
    outside |= set(flat[:, 0].tolist()) | set(flat[:, -1].tolist())
    outside.discard(0)
    if not outside:
        return np.ones_like(mask)

    counts = np.bincount(flat.ravel())
    limit = mask.sum() * _MAXIMUM_HOLE_FRACTION
    fillable = {
        label
        for label in range(1, len(counts))
        if label not in outside and counts[label] <= limit
    }
    if not fillable:
        return mask
    return mask | np.isin(flat, np.array(sorted(fillable), dtype=np.int32))


def _erode(mask: np.ndarray[Any, Any], iterations: int) -> np.ndarray[Any, Any]:
    """Shrink the mask inward by ``iterations`` 4-connected steps.

    The sheet's own rim survives the brightness test just often enough to be a
    problem: it is a one-to-three pixel line of shadow all the way round the
    page, it sits inside the mask, and it is dark, so ink detection reports the
    outline of the sheet as a mark and the crop grows to contain it. Removing a
    thin border removes the line. The cost is any ink written within that
    border of the paper's edge, which is why it is thin.
    """
    result = mask
    for _ in range(iterations):
        shrunk = result.copy()
        shrunk[1:, :] &= result[:-1, :]
        shrunk[:-1, :] &= result[1:, :]
        shrunk[:, 1:] &= result[:, :-1]
        shrunk[:, :-1] &= result[:, 1:]
        shrunk[0, :] = False
        shrunk[-1, :] = False
        shrunk[:, 0] = False
        shrunk[:, -1] = False
        result = shrunk
    return result


def locate_paper(rgb: np.ndarray[Any, Any]) -> PaperRegion:
    """Find the sheet of paper. Never raises; falls back to the whole frame."""
    height, width = rgb.shape[:2]
    full = BoundingBox(left=0.0, top=0.0, right=float(width), bottom=float(height))

    scale = _WORKING_EDGE / max(height, width)
    if scale < 1.0:
        small = np.asarray(
            Image.fromarray(rgb.astype(np.uint8)).resize(
                (max(1, int(width * scale)), max(1, int(height * scale))),
                resample=Image.Resampling.BILINEAR,
            )
        ).astype(np.float32)
    else:
        small = rgb.astype(np.float32)

    channel_max = small.max(axis=2)
    channel_min = small.min(axis=2)
    saturation = np.where(
        channel_max > 0,
        (channel_max - channel_min) / np.maximum(channel_max, 1e-6),
        0.0,
    )
    everything = np.ones((height, width), dtype=bool)
    bright_level = float(np.percentile(channel_max, 98))
    if bright_level <= 0:
        return PaperRegion(full, everything, 1.0, is_fallback=True)

    candidate = (channel_max >= bright_level * _BRIGHT_RATIO) & (
        saturation <= _GREY_SATURATION
    )
    if not candidate.any():
        return PaperRegion(full, everything, 1.0, is_fallback=True)

    filled = _fill_holes(_label_largest(candidate))
    # How much erosion depends on whether there is an edge to erode. A sheet
    # photographed whole has a boundary band that must go; an image that is
    # already a tight crop has none, and eroding it only eats the mark.
    steps = (
        _EROSION_STEPS_BORDERED
        if float(filled.mean()) < _BORDERED_AREA_FRACTION
        else _EROSION_STEPS_FULL
    )
    sheet = _erode(filled, steps)
    if not sheet.any():
        return PaperRegion(full, everything, 1.0, is_fallback=True)
    area_fraction = float(sheet.mean())
    if area_fraction < _MINIMUM_AREA_FRACTION:
        return PaperRegion(full, everything, 1.0, is_fallback=True)

    ys, xs = np.nonzero(sheet)
    sy = height / small.shape[0]
    sx = width / small.shape[1]
    x0 = float(xs.min()) * sx
    x1 = (float(xs.max()) + 1.0) * sx
    y0 = float(ys.min()) * sy
    y1 = (float(ys.max()) + 1.0) * sy

    pad_x = (x1 - x0) * _REGION_PADDING
    pad_y = (y1 - y0) * _REGION_PADDING
    x0 = max(0.0, x0 - pad_x)
    y0 = max(0.0, y0 - pad_y)
    x1 = min(float(width), x1 + pad_x)
    y1 = min(float(height), y1 + pad_y)

    box = BoundingBox(
        left=float(round(x0)),
        top=float(round(y0)),
        right=float(max(round(x0) + 1, round(x1))),
        bottom=float(max(round(y0) + 1, round(y1))),
    )
    full_mask = np.asarray(
        Image.fromarray((sheet * 255).astype(np.uint8)).resize(
            (width, height), resample=Image.Resampling.NEAREST
        )
    ).astype(bool)
    return PaperRegion(box, full_mask, area_fraction, is_fallback=False)


def crop_to_paper(
    rgb: np.ndarray[Any, Any], region: Optional[PaperRegion] = None
) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any], PaperRegion]:
    """Crop to the located sheet, returning the cropped image and its mask."""
    found = region if region is not None else locate_paper(rgb)
    box = found.box
    top, bottom = int(box.top), int(box.bottom)
    left, right = int(box.left), int(box.right)
    return (
        rgb[top:bottom, left:right, :],
        found.mask[top:bottom, left:right],
        found,
    )
