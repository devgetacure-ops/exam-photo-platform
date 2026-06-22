from __future__ import annotations

from typing import Any

import numpy as np
from PIL import Image

from exam_photo.models.geometry import BoundingBox


def safe_crop_numpy(
    rgb: np.ndarray[Any, Any],
    alpha: np.ndarray[Any, Any],
    crop_box: BoundingBox,
) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
    """Safely crops RGB (H, W, 3) and alpha (H, W) arrays to the given crop_box.

    If the crop box goes out of bounds, pads the out-of-bounds regions with zeros
    (fully transparent).
    """
    h, w = alpha.shape
    c_left = int(round(crop_box.left))
    c_top = int(round(crop_box.top))
    c_right = int(round(crop_box.right))
    c_bottom = int(round(crop_box.bottom))

    target_w = c_right - c_left
    target_h = c_bottom - c_top

    # Calculate overlap bounds
    src_x0 = max(0, c_left)
    src_y0 = max(0, c_top)
    src_x1 = min(w, c_right)
    src_y1 = min(h, c_bottom)

    # Destination offsets within the cropped output
    dst_x0 = src_x0 - c_left
    dst_y0 = src_y0 - c_top
    dst_x1 = src_x1 - c_left
    dst_y1 = src_y1 - c_top

    cropped_rgb = np.zeros((target_h, target_w, 3), dtype=rgb.dtype)
    cropped_alpha = np.zeros((target_h, target_w), dtype=alpha.dtype)

    if (src_x1 > src_x0) and (src_y1 > src_y0):
        cropped_rgb[dst_y0:dst_y1, dst_x0:dst_x1] = rgb[src_y0:src_y1, src_x0:src_x1]
        cropped_alpha[dst_y0:dst_y1, dst_x0:dst_x1] = alpha[
            src_y0:src_y1, src_x0:src_x1
        ]

    return cropped_rgb, cropped_alpha


def premultiply_crop_resize_composite(
    image: Image.Image,
    alpha: np.ndarray[Any, Any],
    crop_box: BoundingBox,
    target_size: tuple[int, int],
    background_color: tuple[int, int, int],
    allow_transparent_output: bool = False,
) -> Image.Image:
    """Performs premultiplied-alpha cropping, resizing, and background composition.

    Prevents dark/bright edge fringes by resizing the premultiplied foreground and
    alpha channel together.
    """
    # 1. Convert inputs to float32 numpy arrays in [0.0, 1.0]
    img_rgb = np.array(image.convert("RGB"), dtype=np.float32) / 255.0

    # 2. Crop safely (handling out-of-bounds coordinates)
    cropped_rgb, cropped_alpha = safe_crop_numpy(img_rgb, alpha, crop_box)

    # 3. Premultiply foreground RGB with alpha
    premultiplied_rgb = cropped_rgb * cropped_alpha[..., None]

    # 4. Resize premultiplied RGB and alpha together using PIL Bilinear resampling
    target_w, target_h = target_size

    # Resize premultiplied RGB
    premult_uint8 = np.clip(premultiplied_rgb * 255.0, 0.0, 255.0).astype(np.uint8)
    premult_pil = Image.fromarray(premult_uint8, mode="RGB")
    resized_premult_pil = premult_pil.resize(
        (target_w, target_h), Image.Resampling.BILINEAR
    )
    resized_premult_rgb = np.array(resized_premult_pil, dtype=np.float32) / 255.0

    # Resize alpha
    alpha_uint8 = np.clip(cropped_alpha * 255.0, 0.0, 255.0).astype(np.uint8)
    alpha_pil = Image.fromarray(alpha_uint8, mode="L")
    resized_alpha_pil = alpha_pil.resize(
        (target_w, target_h), Image.Resampling.BILINEAR
    )
    resized_alpha = np.array(resized_alpha_pil, dtype=np.float32) / 255.0

    # 5. Composite onto background
    bg_rgb_arr = np.array(background_color, dtype=np.float32) / 255.0
    composed_rgb = resized_premult_rgb + bg_rgb_arr * (1.0 - resized_alpha)[..., None]
    composed_rgb = np.clip(composed_rgb, 0.0, 1.0)

    # 6. Return as PIL Image with correct transparency mode
    if allow_transparent_output:
        composed_rgba = np.dstack((composed_rgb, resized_alpha))
        final_uint8 = np.clip(composed_rgba * 255.0, 0.0, 255.0).astype(np.uint8)
        return Image.fromarray(final_uint8, mode="RGBA")
    else:
        final_uint8 = np.clip(composed_rgb * 255.0, 0.0, 255.0).astype(np.uint8)
        return Image.fromarray(final_uint8, mode="RGB")
