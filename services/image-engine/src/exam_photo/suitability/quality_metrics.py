from typing import Any, Dict

from PIL import Image, ImageFilter


def calculate_image_quality_metrics(image: Image.Image) -> Dict[str, Any]:
    """Calculates image-wide metrics deterministically using standard PIL operations.

    Limitations:
    - These are global metrics. A bright background may skew mean luminance while the face remains dark.
    - A detailed background may raise sharpness while the face is blurred.
    """
    w, h = image.size
    total_pixels = w * h

    # Get luminance channel (L)
    # If image mode is not L or RGB/RGBA, convert to standard RGBA first
    if image.mode not in ("RGB", "RGBA", "L"):
        working_img = image.convert("RGBA")
    else:
        working_img = image

    # Convert to grayscale to compute luminance statistics
    l_img = working_img.convert("L")
    histogram = l_img.histogram()

    # Mean and standard deviation of luminance
    sum_pixels = sum(histogram)
    mean_luminance = sum(i * count for i, count in enumerate(histogram)) / sum_pixels

    variance = (
        sum(count * ((i - mean_luminance) ** 2) for i, count in enumerate(histogram))
        / sum_pixels
    )
    luminance_std = variance**0.5

    # Shadow & highlight ratios (clipping at boundaries 0 and 255)
    clipped_shadow_count = histogram[0]
    clipped_highlight_count = histogram[255]

    clipped_shadow_ratio = clipped_shadow_count / total_pixels
    clipped_highlight_ratio = clipped_highlight_count / total_pixels

    # Dark / bright pixel ratios (conservative thresholds, e.g. dark < 50, bright > 205)
    dark_pixel_ratio = sum(histogram[i] for i in range(50)) / total_pixels
    bright_pixel_ratio = sum(histogram[i] for i in range(206, 256)) / total_pixels

    # Transparency ratios
    transparent_pixel_ratio = 0.0
    partially_transparent_pixel_ratio = 0.0

    if "A" in image.mode:
        alpha = image.getchannel("A")
        alpha_hist = alpha.histogram()
        # 0 is fully transparent, 255 is fully opaque
        transparent_pixels = alpha_hist[0]
        opaque_pixels = alpha_hist[255]
        partial_pixels = sum_pixels - transparent_pixels - opaque_pixels

        transparent_pixel_ratio = transparent_pixels / total_pixels
        partially_transparent_pixel_ratio = partial_pixels / total_pixels

    # Sharpness Heuristic: Edge Energy heuristic
    # Apply standard Sobel-like filter (FIND_EDGES) and calculate mean intensity of the result
    edge_img = l_img.filter(ImageFilter.FIND_EDGES)
    edge_hist = edge_img.histogram()
    edge_sum = sum(i * count for i, count in enumerate(edge_hist))
    edge_energy = edge_sum / total_pixels

    return {
        "normalized_width": w,
        "normalized_height": h,
        "total_pixels": total_pixels,
        "mean_luminance": mean_luminance,
        "luminance_std": luminance_std,
        "dark_pixel_ratio": dark_pixel_ratio,
        "bright_pixel_ratio": bright_pixel_ratio,
        "clipped_shadow_ratio": clipped_shadow_ratio,
        "clipped_highlight_ratio": clipped_highlight_ratio,
        "transparent_pixel_ratio": transparent_pixel_ratio,
        "partially_transparent_pixel_ratio": partially_transparent_pixel_ratio,
        "global_sharpness_heuristic": edge_energy,
    }
