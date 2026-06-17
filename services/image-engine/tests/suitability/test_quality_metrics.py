import pytest
from PIL import Image

from exam_photo.suitability.quality_metrics import calculate_image_quality_metrics


def test_solid_dark_image() -> None:
    # Uniformly dark
    img = Image.new("L", (100, 100), 10)
    metrics = calculate_image_quality_metrics(img)
    assert metrics["mean_luminance"] == 10.0
    assert metrics["luminance_std"] == 0.0
    assert metrics["dark_pixel_ratio"] == 1.0
    assert metrics["bright_pixel_ratio"] == 0.0
    assert metrics["clipped_shadow_ratio"] == 0.0  # since color is 10, not 0


def test_solid_bright_image() -> None:
    # Uniformly bright
    img = Image.new("L", (100, 100), 250)
    metrics = calculate_image_quality_metrics(img)
    assert metrics["mean_luminance"] == 250.0
    assert metrics["dark_pixel_ratio"] == 0.0
    assert metrics["bright_pixel_ratio"] == 1.0


def test_sharp_vs_blurred_patterns() -> None:
    # Sharp: black and white stripes
    sharp_img = Image.new("L", (100, 100), 0)
    for x in range(0, 100, 2):
        for y in range(100):
            sharp_img.putpixel((x, y), 255)

    # Blur the same image
    blur_img = sharp_img.filter(
        pytest.importorskip("PIL.ImageFilter").GaussianBlur(radius=5)
    )

    sharp_metrics = calculate_image_quality_metrics(sharp_img)
    blur_metrics = calculate_image_quality_metrics(blur_img)

    # Sharp should have significantly higher edge energy / sharpness heuristic
    assert (
        sharp_metrics["global_sharpness_heuristic"]
        > blur_metrics["global_sharpness_heuristic"]
    )


def test_transparency_metrics() -> None:
    # Fully opaque image
    opaque_img = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
    metrics = calculate_image_quality_metrics(opaque_img)
    assert metrics["transparent_pixel_ratio"] == 0.0
    assert metrics["partially_transparent_pixel_ratio"] == 0.0

    # Half transparent image
    trans_img = Image.new("RGBA", (100, 100), (255, 0, 0, 0))
    metrics_trans = calculate_image_quality_metrics(trans_img)
    assert metrics_trans["transparent_pixel_ratio"] == 1.0
    assert metrics_trans["partially_transparent_pixel_ratio"] == 0.0
