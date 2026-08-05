"""Does the ink path hold up on captures nobody has seen?

The reference set is five photographs. Every constant in ``exam_photo.ink`` was
measured against them, which makes those five well served and says nothing
about the sixth. This module is the answer to that: a sweep over the ways a
capture can differ, asserting the properties that must hold for *any* of them
rather than the numbers that happen to hold for one.

The properties are deliberately weak and structural:

- a page with a mark on it is not reported blank
- the delivered crop actually contains the mark
- the delivered paper is light and the delivered mark is dark
- an impression keeps its range of tone rather than being reduced to two levels

They are weak on purpose. Strong assertions here would be assertions about
synthetic images, and synthetic images are not what the engine has to survive.
What these catch is the failure that matters -- a whole class of capture coming
out unusable -- without pretending the fixtures are ground truth.

The variation covered is what a phone in a room does: ink colour and strength,
exposure, colour temperature, uneven light, paper tone, capture distance,
focus, sensor noise, and for marks the printed matter showing through from the
other side of the sheet.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
import pytest
from PIL import Image, ImageFilter

from exam_photo.ink import InkTreatment, prepare_ink_document

#: The sweep builds and processes ~100 synthetic captures and takes minutes.
#: Marked so the fast subset can skip it, and run as its own CI stage -- the
#: same treatment the model-backed suites get.
pytestmark = pytest.mark.ink_robustness


@dataclass(frozen=True)
class Capture:
    """One synthetic photograph and the ground truth that generated it."""

    pixels: np.ndarray[Any, Any]
    mark_box: tuple[int, int, int, int]
    label: str


def _draw_mark(
    canvas: np.ndarray[Any, Any],
    ink: tuple[float, float, float],
    strength: float,
    rng: np.random.Generator,
) -> tuple[int, int, int, int]:
    """A looping cursive-like stroke of varying thickness.

    Varying thickness matters: a stroke that is uniformly dark is the easy
    case, and the defect that prompted this -- letters arriving with holes in
    them -- lives precisely in the thin parts.
    """
    height, width = canvas.shape[:2]
    left, right = int(width * 0.18), int(width * 0.82)
    centre = height // 2
    amplitude = height * 0.16

    xs = np.arange(left, right)
    ys = centre + amplitude * np.sin(xs / (width * 0.055))
    ys += amplitude * 0.4 * np.sin(xs / (width * 0.017))

    top, bottom = height, 0
    for x, y in zip(xs, ys, strict=True):
        # Thickness and opacity both vary along the stroke, as a ballpoint's do.
        thickness = 2 + int(2.5 * (1 + np.sin(x / (width * 0.03))))
        opacity = strength * (0.55 + 0.45 * (1 + np.sin(x / (width * 0.011))) / 2)
        y0 = max(0, int(y) - thickness)
        y1 = min(height, int(y) + thickness)
        for channel in range(3):
            canvas[y0:y1, int(x), channel] *= 1.0 - opacity
            canvas[y0:y1, int(x), channel] += ink[channel] * opacity
        top, bottom = min(top, y0), max(bottom, y1)
    del rng
    return left, top, right, bottom


def _draw_impression(
    canvas: np.ndarray[Any, Any],
    ink: tuple[float, float, float],
    strength: float,
) -> tuple[int, int, int, int]:
    """An oval of continuously varying density, fading at its edge."""
    height, width = canvas.shape[:2]
    ys, xs = np.mgrid[0:height, 0:width]
    ry, rx = height * 0.34, width * 0.30
    radial = ((ys - height / 2) / ry) ** 2 + ((xs - width / 2) / rx) ** 2
    density = np.clip(1.0 - radial, 0.0, 1.0) ** 0.6
    ridges = 0.55 + 0.45 * np.clip(np.sin(ys / 6.0 + np.cos(xs / 40.0)), 0, 1)
    opacity = density * ridges * strength
    for channel in range(3):
        canvas[:, :, channel] *= 1.0 - opacity
        canvas[:, :, channel] += ink[channel] * opacity
    inside = density > 0.02
    ys_i, xs_i = np.nonzero(inside)
    return int(xs_i.min()), int(ys_i.min()), int(xs_i.max()), int(ys_i.max())


def _build(
    treatment: InkTreatment,
    ink: tuple[float, float, float],
    strength: float,
    paper_level: float,
    cast: tuple[float, float, float],
    gradient: float,
    size: tuple[int, int],
    sheet_inset: float,
    show_through: bool,
    blur: float,
    noise: float,
    label: str,
    exposure: float = 1.0,
) -> Capture:
    """``paper_level`` is the paper's own tone; ``exposure`` is the camera.

    They are separate on purpose and the distinction is not academic. A dark
    photograph scales the ink down with the paper and keeps their ratio, so the
    contrast is still there to recover. Cream or grey paper, or pale ink, lowers
    the *ratio* -- a different problem, and the engine has to survive both.
    Conflating them produced a fixture labelled "underexposed" that was really
    "ink barely darker than paper", which is a case worth testing under its own
    name rather than by accident.
    """
    rng = np.random.default_rng(abs(hash(label)) % (2**32))
    width, height = size
    sheet = np.full((height, width, 3), paper_level, dtype=np.float32)

    if show_through:
        # Printed matter on the reverse of the sheet: grey, low contrast, and
        # spread over the whole page rather than where the writing is.
        for row in range(int(height * 0.08), height, max(8, height // 22)):
            sheet[row : row + 2, int(width * 0.05) : int(width * 0.95), :] *= 0.90

    if treatment is InkTreatment.MARK:
        box = _draw_mark(sheet, ink, strength, rng)
    else:
        box = _draw_impression(sheet, ink, strength)

    for channel, factor in enumerate(cast):
        sheet[:, :, channel] *= factor
    if gradient > 0:
        ramp = np.linspace(1.0 - gradient, 1.0, width, dtype=np.float32)
        sheet *= ramp[None, :, None]

    if sheet_inset > 0:
        pad_x, pad_y = int(width * sheet_inset), int(height * sheet_inset)
        frame = np.full(
            (height + 2 * pad_y, width + 2 * pad_x, 3), 34.0, dtype=np.float32
        )
        frame[pad_y : pad_y + height, pad_x : pad_x + width, :] = sheet
        box = (box[0] + pad_x, box[1] + pad_y, box[2] + pad_x, box[3] + pad_y)
        sheet = frame

    # The camera comes last: it darkens the scene it is given, ink and paper
    # together.
    sheet *= exposure
    if noise > 0:
        sheet += rng.normal(0.0, noise, size=sheet.shape).astype(np.float32)
    sheet = np.clip(sheet, 0, 255)

    image = Image.fromarray(sheet.astype(np.uint8))
    if blur > 0:
        image = image.filter(ImageFilter.GaussianBlur(radius=blur))
    return Capture(np.asarray(image).astype(np.float32), box, label)


#: The variation axes. Each case changes one or two things from a plausible
#: baseline, so a failure names its own cause.
_MARK_CASES = [
    ("black ink, good light", (25, 25, 28), 0.95, 246, (1, 1, 1), 0.0, 0.0, 0.0, 0.0),
    ("blue ink", (38, 46, 150), 0.92, 246, (1, 1, 1), 0.0, 0.0, 0.0, 0.0),
    ("faint blue ink", (95, 105, 175), 0.62, 246, (1, 1, 1), 0.0, 0.0, 0.0, 0.0),
    ("pencil, very faint", (120, 120, 125), 0.48, 246, (1, 1, 1), 0.0, 0.0, 0.0, 0.0),
    ("underexposed", (25, 25, 28), 0.95, 246, (1, 1, 1), 0.0, 0.0, 0.0, 0.0, 0.48),
    ("badly underexposed", (30, 32, 40), 0.9, 246, (1, 1, 1), 0, 0, 0.0, 0.0, 0.30),
    ("overexposed", (60, 60, 66), 0.9, 254, (1, 1, 1), 0.0, 0.0, 0.0, 0.0),
    ("grey recycled paper", (25, 25, 28), 0.95, 186, (1, 1, 1), 0.0, 0.0, 0.0, 0.0),
    ("pale ink on grey paper", (128, 128, 132), 0.6, 186, (1, 1, 1), 0, 0, 0.0, 0.0),
    ("warm indoor light", (25, 25, 28), 0.95, 240, (1.0, 0.94, 0.84), 0.0, 0.0, 0, 0),
    ("cool light", (25, 25, 28), 0.95, 240, (0.90, 0.95, 1.0), 0.0, 0.0, 0.0, 0.0),
    ("shadow across page", (25, 25, 28), 0.95, 244, (1, 1, 1), 0.28, 0.0, 0.0, 0.0),
    ("held over a desk", (30, 34, 120), 0.9, 240, (1.0, 0.96, 0.9), 0.12, 0.22, 0, 0),
    ("show-through", (35, 40, 140), 0.9, 248, (1, 1, 1), 0.0, 0.0, 0.0, 0.0),
    ("show-through + desk", (35, 40, 140), 0.9, 244, (1.0, 0.97, 0.92), 0.1, 0.2, 0, 0),
    ("soft focus", (25, 25, 28), 0.95, 246, (1, 1, 1), 0.0, 0.0, 2.2, 0.0),
    ("noisy sensor", (25, 25, 28), 0.95, 240, (1, 1, 1), 0.0, 0.0, 0.0, 6.0),
    ("noisy and dim", (30, 30, 36), 0.88, 246, (1, 1, 1), 0.1, 0.0, 0.8, 7.0, 0.55),
]

_IMPRESSION_CASES = [
    ("purple pad, good light", (110, 100, 190), 0.85, 246, (1, 1, 1), 0.0, 0.0, 0.0, 0),
    ("black pad", (40, 40, 45), 0.9, 246, (1, 1, 1), 0.0, 0.0, 0.0, 0.0),
    ("blue pad, light press", (120, 130, 200), 0.55, 246, (1, 1, 1), 0, 0, 0.0, 0.0),
    ("heavy press", (70, 60, 150), 0.98, 246, (1, 1, 1), 0.0, 0.0, 0.0, 0.0),
    ("underexposed", (110, 100, 190), 0.85, 246, (1, 1, 1), 0, 0, 0.0, 0.0, 0.48),
    ("grey recycled paper", (110, 100, 190), 0.85, 190, (1, 1, 1), 0, 0, 0.0, 0.0),
    ("warm light", (110, 100, 190), 0.85, 238, (1.0, 0.94, 0.84), 0.0, 0.0, 0.0, 0),
    ("shadow across page", (110, 100, 190), 0.85, 244, (1, 1, 1), 0.26, 0, 0.0, 0),
    ("on a desk, distant", (110, 100, 190), 0.85, 240, (1, 1, 1), 0.1, 0.3, 0, 0),
    ("soft focus", (110, 100, 190), 0.85, 246, (1, 1, 1), 0.0, 0.0, 2.0, 0.0),
    ("noisy sensor", (110, 100, 190), 0.85, 240, (1, 1, 1), 0.0, 0.0, 0.0, 6.0),
]

_SIZES = [(900, 600), (2400, 1600)]


def _cases(treatment: InkTreatment, table: list[Any]) -> list[tuple[str, Capture]]:
    built = []
    for size in _SIZES:
        for row in table:
            (
                name,
                ink,
                strength,
                level,
                cast,
                gradient,
                inset,
                blur,
                noise,
            ) = row[:9]
            exposure = float(row[9]) if len(row) > 9 else 1.0
            label = f"{treatment.value}/{name}/{size[0]}x{size[1]}"
            shape = size if treatment is InkTreatment.MARK else (size[1], size[0])
            built.append(
                (
                    label,
                    _build(
                        treatment,
                        tuple(float(c) for c in ink),  # type: ignore[arg-type]
                        strength,
                        float(level),
                        cast,
                        gradient,
                        shape,
                        inset,
                        "show-through" in name,
                        blur,
                        noise,
                        label,
                        exposure,
                    ),
                )
            )
    return built


_ALL_MARKS = _cases(InkTreatment.MARK, _MARK_CASES)
_ALL_IMPRESSIONS = _cases(InkTreatment.IMPRESSION, _IMPRESSION_CASES)


def _delivered(capture: Capture, treatment: InkTreatment) -> np.ndarray[Any, Any]:
    result = prepare_ink_document(
        Image.fromarray(capture.pixels.astype(np.uint8)), treatment
    )
    assert not result.is_blank, f"{capture.label}: reported blank with a mark on it"
    return np.asarray(result.image.convert("RGB")).astype(np.float32)


@pytest.mark.parametrize("label,capture", _ALL_MARKS, ids=[c[0] for c in _ALL_MARKS])
def test_a_mark_survives_every_capture(label: str, capture: Capture) -> None:
    delivered = _delivered(capture, InkTreatment.MARK)
    value = delivered.min(axis=2)

    assert np.percentile(value, 60) > 235, f"{label}: paper is not light"
    assert value.min() < 110, f"{label}: nothing dark survived"
    inked = (value < 200).mean()
    assert 0.005 < inked < 0.45, f"{label}: ink coverage implausible at {inked:.3f}"


@pytest.mark.parametrize(
    "label,capture", _ALL_IMPRESSIONS, ids=[c[0] for c in _ALL_IMPRESSIONS]
)
def test_an_impression_survives_every_capture(label: str, capture: Capture) -> None:
    delivered = _delivered(capture, InkTreatment.IMPRESSION)
    value = delivered.min(axis=2)

    assert np.percentile(value, 85) > 225, f"{label}: paper is not light"
    assert value.min() < 150, f"{label}: nothing dark survived"

    # The property that distinguishes an impression from a mark: it must arrive
    # as a *range* of density, not as ink-or-paper. Anything less than this and
    # the ridge pattern has been thresholded away.
    mid = ((value > 120) & (value < 240)).mean()
    assert mid > 0.03, f"{label}: tonal range collapsed, mid-tones {mid:.3f}"


@pytest.mark.parametrize("label,capture", _ALL_MARKS, ids=[c[0] for c in _ALL_MARKS])
def test_the_crop_keeps_the_whole_mark(label: str, capture: Capture) -> None:
    """The delivered aspect should follow the mark, not the page.

    A crop that missed the mark, or kept the whole sheet, both show up here:
    the drawn stroke is about 4:1 and a page is not.
    """
    result = prepare_ink_document(
        Image.fromarray(capture.pixels.astype(np.uint8)), InkTreatment.MARK
    )
    assert result.crop_box is not None, label
    left, top, right, bottom = capture.mark_box
    aspect = result.image.width / max(result.image.height, 1)
    drawn_aspect = (right - left) / max(bottom - top, 1)
    assert aspect > drawn_aspect * 0.35, (
        f"{label}: crop {result.image.size} is far taller than the mark"
    )


def test_a_blank_page_is_still_reported_blank_under_every_light() -> None:
    """The counterpart to the sweep: nothing must invent a mark."""
    for level, cast, gradient in (
        (246, (1, 1, 1), 0.0),
        (120, (1, 1, 1), 0.0),
        (240, (1.0, 0.94, 0.84), 0.0),
        (244, (1, 1, 1), 0.25),
    ):
        sheet = np.full((600, 900, 3), float(level), dtype=np.float32)
        for channel, factor in enumerate(cast):
            sheet[:, :, channel] *= factor
        if gradient:
            ramp = np.linspace(1.0 - gradient, 1.0, 900, dtype=np.float32)
            sheet *= ramp[None, :, None]
        result = prepare_ink_document(Image.fromarray(sheet.astype(np.uint8)))
        assert result.is_blank, f"invented a mark at level={level} cast={cast}"


def _declaration(
    width: int = 1400, height: int = 900, lines: int = 5, level: float = 246.0
) -> np.ndarray[Any, Any]:
    """Several lines of writing, the last one short.

    A handwritten declaration is the deliverable that stresses proximity
    grouping hardest: the lines are separate clusters, they must all survive,
    and the last line of a paragraph is much shorter than the rest -- so a rule
    that keeps clusters by relative size would drop exactly the line that ends
    the sentence.
    """
    sheet = np.full((height, width, 3), level, dtype=np.float32)
    top = int(height * 0.16)
    spacing = int(height * 0.15)
    for index in range(lines):
        y = top + index * spacing
        length = 0.72 if index < lines - 1 else 0.26
        right = int(width * (0.14 + length))
        for x in range(int(width * 0.14), right):
            wobble = int(6 * np.sin(x / 23.0))
            sheet[y + wobble : y + wobble + 5, x, :] = np.array([32.0, 36.0, 120.0])
    return sheet


def test_every_line_of_a_declaration_survives() -> None:
    sheet = _declaration()
    result = prepare_ink_document(
        Image.fromarray(sheet.astype(np.uint8)), InkTreatment.MARK
    )
    assert result.crop_box is not None

    # Five lines spanning 0.16 to about 0.76 of the height. If grouping dropped
    # the short final line the crop would stop well above the bottom one.
    box = result.crop_box
    assert box.top < 900 * 0.20, f"first line missing: {box}"
    assert box.bottom > 900 * 0.74, f"a lower line was dropped: {box}"

    # Every line must be present, not just the extremes: split the delivered
    # frame into as many bands as there are lines and require ink in each. A
    # crop that spans top to bottom while having dropped a middle line would
    # pass a bounds check and fail this.
    delivered = np.asarray(result.image.convert("L")).astype(np.float32)
    bands = np.array_split(delivered, 5, axis=0)
    empty = [index for index, band in enumerate(bands) if band.min() > 160]
    assert not empty, f"no ink in band(s) {empty} of 5 -- a line was dropped"
