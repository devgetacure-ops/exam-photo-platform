from __future__ import annotations

import numpy as np
import pytest
from PIL import Image

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.foreground_decontamination import (
    decontaminate_foreground_edges,
)
from exam_photo.providers.premultiplied_compositing import (
    premultiply_crop_resize_composite,
    safe_crop_numpy,
)

pytestmark = pytest.mark.mandatory_engine_quality


def test_decontamination_limits_and_scope() -> None:
    # Create an image with distinct foreground, background and uncertain bands
    # Image: 10x10. Foreground: center 4x4. Background: outside.
    # Alpha mask:
    alpha = np.zeros((10, 10), dtype=np.float32)
    # Definite foreground (>= 0.95)
    alpha[3:7, 3:7] = 1.0
    # Uncertain boundary band (0.05 < alpha < 0.95)
    alpha[2, 3:7] = 0.5
    alpha[7, 3:7] = 0.5
    alpha[3:7, 2] = 0.5
    alpha[3:7, 7] = 0.5
    # Definite background (<= 0.05): everything else remains 0.0

    # Let's set some distinct colors:
    # Foreground is bright red [255, 0, 0]
    # Background is bright blue [0, 0, 255]
    # Uncertain pixels have color blending with background (e.g. half red, half blue)
    img_data = np.zeros((10, 10, 3), dtype=np.uint8)
    img_data[3:7, 3:7] = [255, 0, 0]  # pure foreground

    # Uncertain pixels
    for r in range(10):
        for c in range(10):
            if alpha[r, c] == 0.5:
                img_data[r, c] = [128, 0, 128]  # blend
            elif alpha[r, c] == 0.0:
                img_data[r, c] = [0, 0, 255]  # background

    image = Image.fromarray(img_data, mode="RGB")

    # Run decontamination
    decon_image, issues = decontaminate_foreground_edges(
        image, alpha, max_search_distance=5, outlier_threshold=0.8
    )

    decon_arr = np.array(decon_image)

    # 1. Decontamination Scope: Opaque foreground pixels (alpha >= 0.95) must remain unchanged
    np.testing.assert_allclose(decon_arr[3:7, 3:7], img_data[3:7, 3:7])

    # 2. Decontamination Boundary: Definite background (alpha <= 0.05) must remain unchanged
    bg_mask = alpha <= 0.05
    for r in range(10):
        for c in range(10):
            if bg_mask[r, c]:
                np.testing.assert_allclose(decon_arr[r, c], img_data[r, c])

    # 3. Uncertain pixels should be decontaminated (color propagated from nearby foreground, i.e., closer to red)
    uncertain_mask = (alpha > 0.05) & (alpha < 0.95)
    for r in range(10):
        for c in range(10):
            if uncertain_mask[r, c]:
                # Should be decontaminated to pure red [255, 0, 0] since its nearest neighbor is red
                np.testing.assert_allclose(decon_arr[r, c], [255, 0, 0])


def test_decontamination_uncertain_handling() -> None:
    # Test case where propagation cannot resolve everything (e.g. no opaque foreground)
    image = Image.new("RGB", (10, 10), (128, 128, 128))
    alpha = (
        np.ones((10, 10), dtype=np.float32) * 0.5
    )  # all uncertain, no opaque foreground
    decon, issues = decontaminate_foreground_edges(image, alpha)
    assert "EDGE_DECONTAMINATION_UNCERTAIN" in issues


def test_premultiplied_crop_and_resize_out_of_bounds() -> None:
    # Test safe crop handles out of bounds crop box without raising errors
    rgb = np.ones((10, 10, 3), dtype=np.float32)
    alpha = np.ones((10, 10), dtype=np.float32)

    # Crop box that goes partially out of bounds
    crop_box = BoundingBox(left=-5, top=-5, right=5, bottom=5)
    cropped_rgb, cropped_alpha = safe_crop_numpy(rgb, alpha, crop_box)

    assert cropped_rgb.shape == (10, 10, 3)
    assert cropped_alpha.shape == (10, 10)

    # Out of bounds portion should be padded with zeros (fully transparent background)
    # Pixels corresponding to src coords 0..4 (which is dst coords 5..9) should be 1
    # Pixels corresponding to dst coords 0..4 should be 0
    np.testing.assert_allclose(cropped_alpha[0:5, :], 0.0)
    np.testing.assert_allclose(cropped_alpha[:, 0:5], 0.0)
    np.testing.assert_allclose(cropped_alpha[5:10, 5:10], 1.0)


def test_premultiplied_resizing_fringe_reduction() -> None:
    # Test that premultiplied resizing produces cleaner composites (reduces fringe residuals)
    # when composited over a target background compared to conventional resizing.

    # We create a 100x100 white object on a black background
    rgb = np.ones((100, 100, 3), dtype=np.float32)  # foreground is all white
    # Let's say the original image has a black background, so boundary pixels are blended
    # image = alpha * white + (1 - alpha) * black = alpha
    alpha = np.zeros((100, 100), dtype=np.float32)
    alpha[25:75, 25:75] = 1.0
    # Soft transition edge
    alpha[24, 25:75] = 0.5
    alpha[75, 25:75] = 0.5
    alpha[25:75, 24] = 0.5
    alpha[25:75, 75] = 0.5

    image_data = (rgb * alpha[..., None] * 255.0).astype(np.uint8)
    image = Image.fromarray(image_data, mode="RGB")

    crop_box = BoundingBox(left=20, top=20, right=80, bottom=80)
    target_size = (30, 30)
    bg_color = (255, 0, 0)  # composite onto red background

    # 1. Premultiplied compositing
    res_premult = premultiply_crop_resize_composite(
        image, alpha, crop_box, target_size, bg_color
    )
    arr_premult = np.array(res_premult, dtype=np.float32) / 255.0

    # 2. Conventional compositing (resizing before blending, which causes fringing)
    # Let's simulate conventional scaling of the raw RGB image and alpha separately
    cropped_img = image.crop((20, 20, 80, 80))
    resized_img = cropped_img.resize(target_size, Image.Resampling.BILINEAR)
    arr_conv_img = np.array(resized_img, dtype=np.float32) / 255.0

    cropped_alpha = alpha[20:80, 20:80]
    alpha_pil = Image.fromarray((cropped_alpha * 255.0).astype(np.uint8), mode="L")
    resized_alpha_pil = alpha_pil.resize(target_size, Image.Resampling.BILINEAR)
    resized_alpha = np.array(resized_alpha_pil, dtype=np.float32) / 255.0

    bg_arr = np.array(bg_color, dtype=np.float32) / 255.0
    arr_conv = (
        arr_conv_img * resized_alpha[..., None]
        + bg_arr * (1.0 - resized_alpha)[..., None]
    )

    # In conventional composition, the boundary pixels will contain dark bleeding from the original
    # black background because they were resized without premultiplication.
    # Therefore, arr_conv will have lower red/white intensity (darker fringes) at the transition.
    # Let's compare the sum of squared differences or residuals to the ideal pure white/red blend.
    # Ideal composite: alpha * white + (1 - alpha) * red = alpha * [1,1,1] + (1-alpha)*[1,0,0] = [1, alpha, alpha]
    ideal = np.zeros((30, 30, 3), dtype=np.float32)
    ideal[..., 0] = 1.0
    ideal[..., 1] = resized_alpha
    ideal[..., 2] = resized_alpha

    err_premult = np.sum((arr_premult - ideal) ** 2)
    err_conv = np.sum((arr_conv - ideal) ** 2)

    # The premultiplied version must be much closer to the ideal blend (virtually zero error)
    # whereas the conventional version has large errors due to black bleeding.
    assert err_premult < err_conv
    assert err_premult < 5.0
