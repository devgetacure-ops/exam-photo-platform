import numpy as np
import pytest
from PIL import Image

from exam_photo.providers.background_composers.solid_background_composer import (
    SolidBackgroundComposer,
)
from exam_photo.providers.background_composition import (
    BackgroundCompositionConfig,
    BackgroundCompositionIssueCode,
    BackgroundMode,
)


@pytest.fixture
def dummy_image() -> Image.Image:
    """Create a simple 100x100 dummy image."""
    return Image.new("RGB", (100, 100), color="blue")


@pytest.fixture
def dummy_alpha_mask() -> np.ndarray:
    """Create a 100x100 alpha mask with a solid square in the middle."""
    mask = np.zeros((100, 100), dtype=np.float32)
    mask[25:75, 25:75] = 1.0
    return mask


@pytest.fixture
def composer() -> SolidBackgroundComposer:
    return SolidBackgroundComposer()


@pytest.mark.mandatory_background
def test_solid_background_composition_success(
    composer: SolidBackgroundComposer,
    dummy_image: Image.Image,
    dummy_alpha_mask: np.ndarray,
) -> None:
    """Test valid background composition."""
    config = BackgroundCompositionConfig(
        mode=BackgroundMode.PLAIN_WHITE, target_colour_hex="#FFFFFF"
    )
    result = composer.compose_background(dummy_image, dummy_alpha_mask, config)

    assert result.validation.is_valid is True
    assert result.composed_width == 100
    assert result.composed_height == 100
    assert result.foreground_coverage_ratio == 0.25  # (50x50) / 10000
    assert result.composed_image is not None
    assert result.composed_image.mode == "RGB"
    assert result.validation.target_colour_valid is True


@pytest.mark.mandatory_background
def test_solid_background_composition_invalid_mask_shape(
    composer: SolidBackgroundComposer,
    dummy_image: Image.Image,
) -> None:
    """Test background composition fails when mask dimensions mismatch."""
    invalid_mask = np.ones((50, 50), dtype=np.float32)
    config = BackgroundCompositionConfig()
    result = composer.compose_background(dummy_image, invalid_mask, config)

    assert result.validation.is_valid is False
    assert (
        BackgroundCompositionIssueCode.BACKGROUND_MASK_SIZE_MISMATCH
        in result.validation.issue_codes
    )


@pytest.mark.mandatory_background
def test_solid_background_composition_clipping_risk(
    composer: SolidBackgroundComposer,
    dummy_image: Image.Image,
) -> None:
    """Test background composition detects subject clipping at the top edge."""
    # Mask touches the top edge
    mask = np.zeros((100, 100), dtype=np.float32)
    mask[0:50, 25:75] = 1.0

    config = BackgroundCompositionConfig(allow_subject_clipping=False)
    result = composer.compose_background(dummy_image, mask, config)

    assert result.validation.is_valid is False
    assert (
        BackgroundCompositionIssueCode.BACKGROUND_SUBJECT_CLIPPING_RISK
        in result.validation.issue_codes
    )


@pytest.mark.mandatory_background
def test_solid_background_composition_foreground_too_small(
    composer: SolidBackgroundComposer,
    dummy_image: Image.Image,
) -> None:
    """Test foreground coverage ratio below minimum."""
    # Tiny mask
    mask = np.zeros((100, 100), dtype=np.float32)
    mask[50:51, 50:51] = 1.0

    config = BackgroundCompositionConfig(minimum_foreground_coverage=0.1)
    result = composer.compose_background(dummy_image, mask, config)

    assert result.validation.is_valid is False
    assert (
        BackgroundCompositionIssueCode.BACKGROUND_FOREGROUND_TOO_SMALL
        in result.validation.issue_codes
    )


@pytest.mark.mandatory_background
def test_solid_background_composition_invalid_color_config() -> None:
    """Test invalid hex color is rejected by config."""
    with pytest.raises(ValueError):
        BackgroundCompositionConfig(target_colour_hex="not-a-color")
