"""The lighting switch is offered only for a change a person could see (DEC-095).

Owner's note K1: on the 40-photograph set a sharpening-only correction moved
the face by 0.2-0.3 levels while the switch was still offered; colour-cast and
contrast corrections moved it by 4.6-23 levels.
"""

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

from exam_photo.orchestration.lighting_visibility import (
    VISIBLE_CHANGE_LEVELS,
    lighting_change_is_visible,
    mean_face_difference,
)


def _portrait() -> Image.Image:
    """A synthetic head on white: a skin-toned ellipse with some texture."""
    rng = np.random.default_rng(7)
    canvas = np.full((531, 413, 3), 255, dtype=np.uint8)
    yy, xx = np.mgrid[0:531, 0:413]
    face = ((xx - 206) / 120) ** 2 + ((yy - 250) / 170) ** 2 <= 1
    texture = rng.integers(-12, 12, size=(531, 413, 1))
    skin = np.clip(np.array([182, 140, 112]) + texture, 0, 255)
    canvas[face] = skin[face]
    return Image.fromarray(canvas)


def test_an_identical_pair_is_not_a_visible_change():
    image = _portrait()
    assert mean_face_difference(image, image.copy()) == 0.0
    assert not lighting_change_is_visible(image, image.copy())


def test_a_light_sharpen_is_not_a_visible_change():
    original = _portrait()
    sharpened = original.filter(
        ImageFilter.UnsharpMask(radius=1, percent=20, threshold=3)
    )
    assert mean_face_difference(sharpened, original) < VISIBLE_CHANGE_LEVELS
    assert not lighting_change_is_visible(sharpened, original)


def test_a_contrast_correction_is_a_visible_change():
    original = _portrait()
    corrected = ImageEnhance.Contrast(original).enhance(1.10)
    corrected = ImageEnhance.Brightness(corrected).enhance(1.06)
    assert lighting_change_is_visible(corrected, original)


def test_frames_of_different_sizes_are_never_treated_as_the_same():
    assert lighting_change_is_visible(_portrait(), _portrait().resize((200, 230)))


def test_the_background_does_not_dilute_the_measurement():
    """A change confined to the face still counts when the frame is mostly white."""
    original = _portrait()
    corrected = original.copy()
    face = Image.eval(original.crop((120, 120, 290, 400)), lambda v: min(255, v + 8))
    corrected.paste(face, (120, 120))
    assert lighting_change_is_visible(corrected, original)
