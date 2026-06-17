from typing import Any

import pytest

from exam_photo.input.errors import ImageInspectionError, InputErrorCode
from exam_photo.input.limits import InputLimits
from exam_photo.input.normalization import normalize_image_input


def test_corrupted_image_rejected() -> None:
    # JPEG starts with FF D8 FF, but append junk bytes
    corrupted_data = b"\xff\xd8\xffjunkjunkjunk"
    with pytest.raises(ImageInspectionError) as exc_info:
        normalize_image_input(corrupted_data, "photo.jpg", InputLimits())
    assert exc_info.value.code in [
        InputErrorCode.INPUT_DECODE_FAILED,
        InputErrorCode.INPUT_CORRUPTED,
    ]


def test_multiframe_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    from PIL import Image
    from tests.helpers.synthetic_images import create_solid_image, save_image_to_bytes

    img = create_solid_image("RGB", (20, 20))
    png_data = save_image_to_bytes(img, "PNG")

    original_open = Image.open

    def mock_open(*args: Any, **kwargs: Any) -> Image.Image:
        opened = original_open(*args, **kwargs)
        # Mock animation properties
        opened.n_frames = 2
        opened.is_animated = True
        opened.load = lambda: None  # type: ignore[assignment,return-value]
        return opened

    import PIL

    monkeypatch.setattr(PIL.Image, "open", mock_open)

    with pytest.raises(ImageInspectionError) as exc_info:
        normalize_image_input(png_data, "photo.png", InputLimits())
    assert exc_info.value.code == InputErrorCode.INPUT_MULTIFRAME_UNSUPPORTED
