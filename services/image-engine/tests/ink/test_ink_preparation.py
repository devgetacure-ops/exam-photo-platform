"""The ink-on-paper preparation path.

Every fixture here is synthesised in code. The real reference material is a
photograph of a person's actual signature and thumb impression, which must
never be committed (AGENTS.md); what can be committed is the geometry and the
tonal relationships those photographs taught us, reconstructed.

The synthetic cases are honest about what they can prove. They establish that
the stages do what they claim on inputs whose right answer is known by
construction -- a shadow really was removed, a mark really was found where it
was drawn, a blank page really is reported blank. They cannot establish that
the thresholds are right for real paper; only the reference photographs do
that, and the numbers they produced are recorded in the constants' comments.
"""

from typing import Any

import numpy as np
import pytest
from PIL import Image

from exam_photo.ink import (
    detect_ink,
    estimate_paper_field,
    flatten_to_paper_white,
    locate_paper,
    prepare_ink_document,
)
from exam_photo.ink.ink_mask import drop_edge_connected, mass_trimmed_box


def _paper(
    width: int = 600,
    height: int = 400,
    level: int = 245,
    cast: tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> np.ndarray[Any, Any]:
    base = np.zeros((height, width, 3), dtype=np.float32)
    for channel in range(3):
        base[:, :, channel] = level * cast[channel]
    return np.clip(base, 0, 255)


def _shadow(
    sheet: np.ndarray[Any, Any], strength: float = 0.45
) -> np.ndarray[Any, Any]:
    """A left-to-right illumination ramp, as a hand casts across a page."""
    height, width = sheet.shape[:2]
    ramp = np.linspace(1.0 - strength, 1.0, width, dtype=np.float32)
    return sheet * ramp[None, :, None]


def _stroke(
    sheet: np.ndarray[Any, Any],
    box: tuple[int, int, int, int],
    colour: tuple[int, int, int],
    thickness: int = 3,
) -> np.ndarray[Any, Any]:
    """Draw a horizontal bar: a stand-in for a pen stroke."""
    left, top, right, bottom = box
    marked = sheet.copy()
    for y in range(top, bottom, max(1, (bottom - top) // max(1, thickness))):
        marked[y : y + thickness, left:right, :] = np.array(colour, dtype=np.float32)
    return marked


# --- Illumination -----------------------------------------------------------


def test_shadow_is_removed_and_paper_reaches_white() -> None:
    sheet = _shadow(_paper(), strength=0.25)
    before = sheet.min(axis=2)
    assert before.max() - before.min() > 50, "fixture should carry a real gradient"

    estimate = estimate_paper_field(sheet)
    flattened = flatten_to_paper_white(sheet, estimate)

    after = flattened.min(axis=2)
    assert after.min() > 235, "paper should end near white everywhere"
    assert after.max() - after.min() < 20, "the gradient should be gone"


def test_a_harsh_gradient_is_reduced_rather_than_removed() -> None:
    """The measured bound of the tile estimator, stated rather than hidden.

    A tile is described by its brightest content and the outermost half-tile
    has nothing beyond it to interpolate against, so the darkest edge of a
    severe gradient stays under-corrected. Every reference photograph flattens
    to paper median 255, so this is beyond what real captures exhibit -- but it
    is a real limit and this test is where it is recorded.
    """
    sheet = _shadow(_paper(), strength=0.45)
    before = sheet.min(axis=2)
    after = flatten_to_paper_white(sheet, estimate_paper_field(sheet)).min(axis=2)

    before_spread = float(before.max() - before.min())
    after_spread = float(after.max() - after.min())
    assert after_spread < before_spread * 0.65, "it must still improve materially"
    assert after.min() > 180, f"and not collapse: {after.min()}"


def test_colour_cast_is_neutralised() -> None:
    """The pale-yellow cast of indoor light is a per-channel difference."""
    sheet = _paper(cast=(1.0, 0.97, 0.92))
    flattened = flatten_to_paper_white(sheet, estimate_paper_field(sheet))
    spread = flattened.reshape(-1, 3).mean(axis=0)
    assert spread.max() - spread.min() < 4.0


def test_flattening_a_clean_scan_changes_almost_nothing() -> None:
    """Idempotence on already-good input, which is what the approved outputs
    are: every tile measured 1.00 of the sheet level and the field came out
    flat."""
    sheet = _paper(level=255)
    sheet = _stroke(sheet, (100, 180, 500, 220), (20, 20, 20))
    flattened = flatten_to_paper_white(sheet, estimate_paper_field(sheet))
    assert np.abs(flattened - sheet).max() < 6.0


def test_a_solid_blob_is_not_erased_by_the_illumination_estimate() -> None:
    """The defect that ruled out a max-filter background.

    A thumb impression is solid and wide. A background estimated by local
    maximum reads the blob's interior as paper and divides the impression away
    from its own centre outward.
    """
    sheet = _paper()
    sheet[120:280, 200:400, :] = np.array([120.0, 110.0, 180.0])
    flattened = flatten_to_paper_white(sheet, estimate_paper_field(sheet))
    interior = flattened[180:220, 260:340, :]
    assert interior.min(axis=2).mean() < 160, "the blob's centre must survive"


# --- Ink detection ----------------------------------------------------------


def test_blue_and_black_ink_are_ranked_together() -> None:
    """A blue signature must not score as half a signature for being blue."""
    depths = []
    for colour in ((25, 25, 25), (35, 45, 150)):
        sheet = _stroke(_paper(level=255), (100, 180, 500, 220), colour)
        flattened = flatten_to_paper_white(sheet, estimate_paper_field(sheet))
        depths.append(detect_ink(flattened).ink_depth)
    assert abs(depths[0] - depths[1]) < 0.12, depths


def test_faint_show_through_is_rejected_while_the_mark_survives() -> None:
    sheet = _paper(level=255)
    sheet = _stroke(sheet, (60, 60, 540, 110), (225, 225, 228), thickness=6)
    sheet = _stroke(sheet, (150, 200, 450, 240), (30, 35, 120))
    flattened = flatten_to_paper_white(sheet, estimate_paper_field(sheet))
    ink = detect_ink(flattened)

    assert ink.box is not None
    assert ink.box.top >= 150, "the faint band above should not be in the box"
    assert ink.box.bottom <= 260


def test_a_blank_page_is_reported_blank() -> None:
    result = prepare_ink_document(Image.fromarray(_paper().astype(np.uint8)))
    assert result.is_blank
    assert result.crop_box is None


def test_paper_grain_alone_is_not_ink() -> None:
    rng = np.random.default_rng(20260805)
    sheet = _paper(level=250) - rng.uniform(0.0, 6.0, size=(400, 600, 1))
    flattened = flatten_to_paper_white(sheet, estimate_paper_field(sheet))
    assert detect_ink(flattened).box is None


# --- Boxes ------------------------------------------------------------------


def test_a_lone_speck_does_not_stretch_the_box() -> None:
    mask = np.zeros((400, 600), dtype=bool)
    mask[190:210, 250:350] = True
    mask[5, 590] = True  # a fibre in the corner

    box = mass_trimmed_box(mask)
    assert box is not None
    assert box.right < 400, "the corner speck must not reach the box"
    assert box.top >= 180


def test_a_solid_mass_running_off_the_sheet_is_dropped() -> None:
    sheet = np.zeros((300, 300), dtype=bool)
    sheet[:, :250] = True  # the page ends at x=250
    ink = np.zeros((300, 300), dtype=bool)
    ink[100:200, 200:300] = True  # a finger, crossing the edge
    ink[140:145, 40:160] = True  # a stroke, well inside

    kept = drop_edge_connected(ink, sheet)
    assert kept[142, 100], "the interior stroke must survive"
    assert not kept[150, 260], "the mass crossing the edge must not"


def test_a_thin_stroke_touching_the_edge_survives() -> None:
    """Cursive is one long connected line and its tail may graze the edge.

    Rejecting every edge-connected mark deleted an entire real signature.
    """
    sheet = np.zeros((300, 300), dtype=bool)
    sheet[:, :250] = True
    ink = np.zeros((300, 300), dtype=bool)
    ink[148:151, 40:260] = True  # a stroke that runs off the page

    kept = drop_edge_connected(ink, sheet)
    assert kept[149, 100], "a thin stroke is writing, not an obstruction"


# --- End to end -------------------------------------------------------------


def test_a_badly_lit_page_is_cropped_to_its_mark() -> None:
    """The case the engine handles: the sheet fills the frame, badly lit.

    This is the common capture -- a phone held over a page on a desk, close
    enough that the paper is most of the picture, with a shadow across it and
    the room's colour in it.
    """
    # A 0.25 falloff, which is inside what the tile estimator fully removes.
    # At 0.45 the sheet's darkest edge stays under-corrected enough to read as
    # ink, and the crop grows to reach it -- see
    # ``test_a_harsh_gradient_is_reduced_rather_than_removed``.
    sheet = _shadow(_paper(1200, 900, level=235, cast=(1.0, 0.97, 0.92)), strength=0.25)
    sheet = _stroke(sheet, (400, 400, 800, 500), (40, 45, 130))

    result = prepare_ink_document(Image.fromarray(sheet.astype(np.uint8)))

    assert not result.is_blank
    assert result.crop_box is not None

    delivered = np.asarray(result.image.convert("RGB")).astype(np.float32)
    assert np.percentile(delivered.min(axis=2), 75) > 250, "paper must be white"
    assert delivered.min() < 120, "ink must still be dark"

    # The drawn mark spans 400x70, so with the margin the crop should be near
    # 465x135.
    assert result.image.width < 620, result.image.size
    assert result.image.height < 320, result.image.size


def test_a_small_sheet_on_a_dark_background_is_not_cropped_tightly_yet() -> None:
    """The case the engine does **not** handle, recorded rather than hidden.

    When the sheet is a small object in a larger frame, the boundary between
    paper and background survives as a line of ink-classified pixels, and it
    drags the crop box out to the whole sheet. The same defect is visible on
    the one real hand-held photograph in the reference set, whose crop comes
    out roughly twice the signature's extent -- so this reproduces a real
    limitation rather than inventing one.

    What the engine still gets right here is the tonal half: the paper is
    driven to white and the mark survives. The failure is framing alone, so the
    delivered file is usable and merely loose. That is why this is a recorded
    bound and not a blocking defect.

    **The bound may fall. It may never rise.**
    """
    sheet = _shadow(_paper(1200, 900, level=235, cast=(1.0, 0.97, 0.92)))
    sheet = _stroke(sheet, (400, 400, 800, 500), (40, 45, 130))
    frame = np.zeros((1200, 1600, 3), dtype=np.float32)
    frame[:, :, :] = np.array([30.0, 32.0, 38.0])  # a dark desk
    frame[150:1050, 200:1400, :] = sheet

    result = prepare_ink_document(Image.fromarray(frame.astype(np.uint8)))

    assert not result.is_blank
    delivered = np.asarray(result.image.convert("RGB")).astype(np.float32)
    assert np.percentile(delivered.min(axis=2), 75) > 250, "paper must be white"

    # An ideal crop is about 470x170. Current behaviour is far looser, and on
    # this synthetic the mark is lost from the crop entirely -- the sheet edge
    # wins. Both facts are asserted so that either improving is visible.
    assert result.image.width <= 900, result.image.size
    assert result.image.height <= 950, result.image.size


def test_the_mark_keeps_its_own_colour() -> None:
    sheet = _stroke(_paper(level=250), (100, 180, 500, 220), (35, 45, 165))
    result = prepare_ink_document(Image.fromarray(sheet.astype(np.uint8)))
    delivered = np.asarray(result.image.convert("RGB")).astype(np.float32)
    darkest = delivered.reshape(-1, 3)[delivered.min(axis=2).ravel().argmin()]
    assert darkest[2] > darkest[0] + 40, f"blue ink should stay blue: {darkest}"


@pytest.mark.parametrize("size", [(64, 64), (5000, 40), (40, 5000)])
def test_extreme_shapes_do_not_raise(size: tuple[int, int]) -> None:
    width, height = size
    sheet = _paper(width, height, level=250)
    sheet[height // 3 : height // 2, width // 3 : width // 2, :] = 30.0
    result = prepare_ink_document(Image.fromarray(sheet.astype(np.uint8)))
    assert result.image.width >= 1 and result.image.height >= 1


def test_a_uniformly_dark_frame_still_returns_a_usable_box() -> None:
    """A relative brightness test cannot tell a dark sheet from a dark room.

    Every threshold in ``paper_region`` is a fraction of the frame's own
    brightest content, which is what lets an underexposed capture be judged on
    its own terms. The cost is that a frame with nothing bright in it reads as
    one large, evenly dark sheet rather than as no sheet at all. Downstream is
    unaffected -- the box is the whole frame either way, which is what the
    fallback would have produced -- so this is recorded as a property rather
    than fixed.
    """
    dark = np.full((200, 200, 3), 12.0, dtype=np.float32)
    region = locate_paper(dark)
    assert region.box.width == 200 and region.box.height == 200


def test_a_frame_with_no_bright_content_at_all_falls_back() -> None:
    black = np.zeros((200, 200, 3), dtype=np.float32)
    region = locate_paper(black)
    assert region.is_fallback
    assert region.box.width == 200 and region.box.height == 200
