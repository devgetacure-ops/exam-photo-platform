import numpy as np
import pytest
from PIL import Image
from pydantic import ValidationError

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.foreground_refinement import (
    RefinementConfig,
)
from exam_photo.providers.refiners.errors import (
    RefinementInputError,
)
from exam_photo.providers.refiners.morphological_refiner import (
    MorphologicalForegroundRefiner,
    _disk_offsets,
)
from tests.fakes.fake_foreground_refiner import FakeForegroundRefiner


def test_refinement_config_validation() -> None:
    # Test valid configuration values
    cfg = RefinementConfig(
        morphology_radius_px=5,
        morphology_radius_ratio=0.01,
        min_radius_px=3,
        max_radius_px=20,
        gaussian_sigma=2.0,
        probability_weight=0.5,
        trimap_band_width_px=15,
        preserve_face_core=False,
    )
    assert cfg.morphology_radius_px == 5
    assert cfg.gaussian_sigma == 2.0
    assert cfg.preserve_face_core is False

    # Test out of bounds validations
    with pytest.raises(ValidationError):
        RefinementConfig(morphology_radius_px=0)  # ge=1
    with pytest.raises(ValidationError):
        RefinementConfig(morphology_radius_px=35)  # le=30
    with pytest.raises(ValidationError):
        RefinementConfig(morphology_radius_ratio=-0.01)  # ge=0.0
    with pytest.raises(ValidationError):
        RefinementConfig(probability_weight=1.5)  # le=1.0
    with pytest.raises(ValidationError):
        RefinementConfig(alpha_snap_low_threshold=0.8, alpha_snap_high_threshold=0.2)


def test_refinement_config_size_aware_radius() -> None:
    # Case 1: morphology_radius_ratio is None -> uses morphology_radius_px directly
    cfg = RefinementConfig(morphology_radius_px=5, morphology_radius_ratio=None)
    assert cfg.effective_radius(600, 800) == 5
    assert cfg.effective_radius(3250, 4333) == 5

    # Case 2: normal size-aware ratio
    cfg = RefinementConfig(
        morphology_radius_ratio=0.005, min_radius_px=2, max_radius_px=15
    )
    # min(600, 800) = 600 * 0.005 = 3
    assert cfg.effective_radius(600, 800) == 3

    # Case 3: min radius clamp
    # min(200, 200) = 200 * 0.005 = 1 -> clamped to min_radius_px (2)
    assert cfg.effective_radius(200, 200) == 2

    # Case 4: max radius clamp
    # min(4000, 5000) = 4000 * 0.005 = 20 -> clamped to max_radius_px (15)
    assert cfg.effective_radius(4000, 5000) == 15


def test_disk_offsets() -> None:
    # Radius 1: 5 points (0,0), (0,1), (0,-1), (1,0), (-1,0)
    offsets_r1 = _disk_offsets(1)
    assert len(offsets_r1) == 5
    assert (0, 0) in offsets_r1
    assert (0, 1) in offsets_r1
    assert (1, 0) in offsets_r1

    # Radius 2: 13 points
    offsets_r2 = _disk_offsets(2)
    assert len(offsets_r2) == 13

    # Radius 3: 29 points
    offsets_r3 = _disk_offsets(3)
    assert len(offsets_r3) == 29

    # Symmetry check
    for dy, dx in offsets_r3:
        assert (-dy, -dx) in offsets_r3
        assert (dy, -dx) in offsets_r3
        assert (-dy, dx) in offsets_r3


def test_refinement_input_validation() -> None:
    refiner = MorphologicalForegroundRefiner()
    image = Image.new("RGB", (100, 100), (128, 128, 128))
    coarse = Image.new("L", (100, 100), 0)
    prob = np.zeros((100, 100), dtype=np.float32)

    # 1. Invalid coarse mask class
    with pytest.raises(RefinementInputError):
        refiner.refine_mask(image, "not a PIL Image", prob)  # type: ignore[arg-type]

    # 2. Invalid coarse mask mode
    invalid_mode = Image.new("RGB", (100, 100), (0, 0, 0))
    with pytest.raises(RefinementInputError):
        refiner.refine_mask(image, invalid_mode, prob)

    # 3. Invalid probability mask class
    with pytest.raises(RefinementInputError):
        refiner.refine_mask(image, coarse, "not a numpy array")  # type: ignore[arg-type]

    # 4. Invalid probability mask dtype
    wrong_dtype = np.zeros((100, 100), dtype=np.int32)
    with pytest.raises(RefinementInputError):
        refiner.refine_mask(image, coarse, wrong_dtype)

    # 5. Invalid probability mask shape (not 2D)
    wrong_shape_3d = np.zeros((100, 100, 1), dtype=np.float32)
    with pytest.raises(RefinementInputError):
        refiner.refine_mask(image, coarse, wrong_shape_3d)

    # 6. Mismatch in dimensions
    mismatch_prob = np.zeros((120, 100), dtype=np.float32)
    with pytest.raises(RefinementInputError):
        refiner.refine_mask(image, coarse, mismatch_prob)


def test_morphological_closing_fills_holes() -> None:
    refiner = MorphologicalForegroundRefiner()

    # Create a 20x20 foreground block with a single 1x1 hole at (10, 10)
    coarse_arr = np.zeros((30, 30), dtype=np.uint8)
    coarse_arr[5:25, 5:25] = 255
    coarse_arr[10, 10] = 0  # 1-pixel hole

    coarse_mask = Image.fromarray(coarse_arr, mode="L")
    prob_mask = (coarse_arr / 255.0).astype(np.float32)
    image = Image.new("RGB", coarse_mask.size, (128, 128, 128))

    # With radius=2, morphology closing should fill the hole
    cfg = RefinementConfig(morphology_radius_px=2, morphology_radius_ratio=None)
    res = refiner.refine_mask(image, coarse_mask, prob_mask, config=cfg)

    refined_bin_arr = np.array(res.refined_binary_mask)
    # The pixel at (10, 10) should now be foreground (255)
    assert refined_bin_arr[10, 10] == 255
    # The coverage should have improved (no holes in the inner region)
    assert np.all(refined_bin_arr[7:23, 7:23] == 255)


def test_morphological_opening_removes_noise() -> None:
    refiner = MorphologicalForegroundRefiner()

    # Create a 20x20 foreground block with a single 1x1 noise speckle at (2, 2)
    coarse_arr = np.zeros((30, 30), dtype=np.uint8)
    coarse_arr[5:25, 5:25] = 255
    coarse_arr[2, 2] = 255  # noise speckle

    coarse_mask = Image.fromarray(coarse_arr, mode="L")
    prob_mask = (coarse_arr / 255.0).astype(np.float32)
    image = Image.new("RGB", coarse_mask.size, (128, 128, 128))

    cfg = RefinementConfig(morphology_radius_px=2, morphology_radius_ratio=None)
    res = refiner.refine_mask(image, coarse_mask, prob_mask, config=cfg)

    refined_bin_arr = np.array(res.refined_binary_mask)
    # The noise speckle at (2, 2) should be removed (0)
    assert refined_bin_arr[2, 2] == 0
    # The main block should be preserved
    assert refined_bin_arr[10, 10] == 255


def test_face_core_preservation() -> None:
    refiner = MorphologicalForegroundRefiner()

    # Create a small mask where a face region lies
    # Width=100, Height=100
    coarse_arr = np.zeros((100, 100), dtype=np.uint8)
    # Entire image is foreground, but we'll test erosion protection
    coarse_arr[10:90, 10:90] = 255

    coarse_mask = Image.fromarray(coarse_arr, mode="L")
    prob_mask = (coarse_arr / 255.0).astype(np.float32)
    image = Image.new("RGB", coarse_mask.size, (128, 128, 128))

    # Face box: Left=30, Top=30, Right=70, Bottom=70 (pixel space)
    face_box = BoundingBox(left=30.0, top=30.0, right=70.0, bottom=70.0)
    face = FaceDetection(
        bounding_box=face_box,
        confidence=0.95,
    )

    # Use a large morphology radius that would normally erode the entire block
    cfg = RefinementConfig(
        morphology_radius_px=25, morphology_radius_ratio=None, preserve_face_core=True
    )
    res = refiner.refine_mask(image, coarse_mask, prob_mask, face=face, config=cfg)

    refined_bin_arr = np.array(res.refined_binary_mask)
    # The face core (10% inward from [30,30]-[70,70] is [34,34]-[66,66])
    # should be preserved (255) because of guardrails
    assert refined_bin_arr[50, 50] == 255
    assert np.all(refined_bin_arr[34:66, 34:66] == 255)


def test_trimap_values() -> None:
    refiner = MorphologicalForegroundRefiner()
    coarse_arr = np.zeros((50, 50), dtype=np.uint8)
    coarse_arr[10:40, 10:40] = 255
    coarse_mask = Image.fromarray(coarse_arr, mode="L")
    prob_mask = (coarse_arr / 255.0).astype(np.float32)
    image = Image.new("RGB", coarse_mask.size, (128, 128, 128))

    res = refiner.refine_mask(image, coarse_mask, prob_mask)
    trimap_arr = np.array(res.trimap)

    # Trimap values must contain only {0, 128, 255}
    unique_vals = set(np.unique(trimap_arr))
    assert unique_vals.issubset({0, 128, 255})
    assert 128 in unique_vals  # there should be an uncertainty boundary band


def test_refined_alpha_range() -> None:
    refiner = MorphologicalForegroundRefiner()
    coarse_arr = np.zeros((50, 50), dtype=np.uint8)
    coarse_arr[10:40, 10:40] = 255
    coarse_mask = Image.fromarray(coarse_arr, mode="L")
    # Add random probability values in [0, 1] to test alpha blending
    np.random.seed(42)
    prob_mask = np.random.rand(50, 50).astype(np.float32)
    image = Image.new("RGB", coarse_mask.size, (128, 128, 128))

    res = refiner.refine_mask(image, coarse_mask, prob_mask)
    alpha = res.refined_alpha_mask

    assert alpha.dtype == np.float32
    assert np.all(alpha >= 0.0)
    assert np.all(alpha <= 1.0)


def test_fake_foreground_refiner() -> None:
    refiner = FakeForegroundRefiner()
    coarse_arr = np.zeros((50, 50), dtype=np.uint8)
    coarse_arr[10:40, 10:40] = 255
    coarse_mask = Image.fromarray(coarse_arr, mode="L")
    prob_mask = (coarse_arr / 255.0).astype(np.float32)
    image = Image.new("RGB", coarse_mask.size, (128, 128, 128))

    res = refiner.refine_mask(image, coarse_mask, prob_mask)
    assert res.provider_name == "FakeForegroundRefiner"
    assert res.input_width == 50
    assert res.input_height == 50
    assert np.allclose(res.refined_alpha_mask, prob_mask)


def test_refinement_nan_inf_range_validations() -> None:
    refiner = MorphologicalForegroundRefiner()
    coarse = Image.new("L", (100, 100), 0)
    image = Image.new("RGB", coarse.size, (128, 128, 128))

    # NaN check
    prob_nan = np.zeros((100, 100), dtype=np.float32)
    prob_nan[0, 0] = np.nan
    with pytest.raises(RefinementInputError):
        refiner.refine_mask(image, coarse, prob_nan)

    # Inf check
    prob_inf = np.zeros((100, 100), dtype=np.float32)
    prob_inf[0, 0] = np.inf
    with pytest.raises(RefinementInputError):
        refiner.refine_mask(image, coarse, prob_inf)

    # Below zero check
    prob_neg = np.zeros((100, 100), dtype=np.float32)
    prob_neg[0, 0] = -0.5
    with pytest.raises(RefinementInputError):
        refiner.refine_mask(image, coarse, prob_neg)

    # Above one check
    prob_large = np.zeros((100, 100), dtype=np.float32)
    prob_large[0, 0] = 1.5
    with pytest.raises(RefinementInputError):
        refiner.refine_mask(image, coarse, prob_large)


def test_provider_name_correctness() -> None:
    refiner = MorphologicalForegroundRefiner()
    assert refiner.provider_name == "MorphologicalForegroundRefiner"
