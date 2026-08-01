from __future__ import annotations

from typing import Any

import numpy as np
from PIL import Image


def decontaminate_foreground_edges(
    image: Image.Image,
    alpha: np.ndarray[Any, Any],
    # Propagation advances one pixel per iteration, so this is the furthest a
    # semi-transparent pixel can be from opaque foreground and still have its
    # colour corrected.  Anything beyond it keeps background colour and shows up
    # as a grey outline after compositing, so this must cover the matting band
    # width the refiner produces.
    max_search_distance: int = 24,
    outlier_threshold: float = 0.5,
) -> tuple[Image.Image, list[str]]:
    """Applies color decontamination strictly within the uncertain boundary region (0.05 < alpha < 0.95).

    Propagates color from opaque foreground pixels (alpha >= 0.95) to decontaminate
    background color spill.
    """
    if not isinstance(image, Image.Image):
        raise TypeError("image must be a PIL Image instance")
    if not isinstance(alpha, np.ndarray):
        raise TypeError("alpha must be a numpy ndarray")
    if alpha.dtype != np.float32:
        raise TypeError("alpha must be a float32 array")
    if alpha.shape != (image.height, image.width):
        raise ValueError(
            f"alpha shape {alpha.shape} does not match image size {image.size}"
        )

    img_rgb = np.array(image.convert("RGB"), dtype=np.float32) / 255.0
    h, w, c = img_rgb.shape

    opaque_mask = alpha >= 0.95
    uncertain_mask = (alpha > 0.05) & (alpha < 0.95)

    if not np.any(uncertain_mask):
        return image.copy(), []

    if not np.any(opaque_mask):
        return image.copy(), ["EDGE_DECONTAMINATION_UNCERTAIN"]

    known_rgb = img_rgb.copy()
    known_flag = opaque_mask.copy()
    to_resolve = uncertain_mask.copy()

    issues: list[str] = []

    # Iterative propagation
    for _step in range(max_search_distance):
        if not np.any(to_resolve):
            break

        # Shift flags to find neighbors
        shifted_up = np.pad(
            known_flag, ((1, 0), (0, 0)), mode="constant", constant_values=False
        )[:-1, :]
        shifted_down = np.pad(
            known_flag, ((0, 1), (0, 0)), mode="constant", constant_values=False
        )[1:, :]
        shifted_left = np.pad(
            known_flag, ((0, 0), (1, 0)), mode="constant", constant_values=False
        )[:, :-1]
        shifted_right = np.pad(
            known_flag, ((0, 0), (0, 1)), mode="constant", constant_values=False
        )[:, 1:]

        has_known_neighbor = (
            shifted_up | shifted_down | shifted_left | shifted_right
        ) & to_resolve

        if not np.any(has_known_neighbor):
            break

        accum_rgb = np.zeros((h, w, 3), dtype=np.float32)
        count = np.zeros((h, w), dtype=np.float32)

        # Shift RGBs
        rgb_up = np.pad(known_rgb, ((1, 0), (0, 0), (0, 0)), mode="edge")[:-1, :, :]
        rgb_down = np.pad(known_rgb, ((0, 1), (0, 0), (0, 0)), mode="edge")[1:, :, :]
        rgb_left = np.pad(known_rgb, ((0, 0), (1, 0), (0, 0)), mode="edge")[:, :-1, :]
        rgb_right = np.pad(known_rgb, ((0, 0), (0, 1), (0, 0)), mode="edge")[:, 1:, :]

        # Accumulate directions
        mask_up = shifted_up & has_known_neighbor
        accum_rgb[mask_up] += rgb_up[mask_up]
        count[mask_up] += 1

        # Accumulate down
        mask_down = shifted_down & has_known_neighbor
        accum_rgb[mask_down] += rgb_down[mask_down]
        count[mask_down] += 1

        # Accumulate left
        mask_left = shifted_left & has_known_neighbor
        accum_rgb[mask_left] += rgb_left[mask_left]
        count[mask_left] += 1

        # Accumulate right
        mask_right = shifted_right & has_known_neighbor
        accum_rgb[mask_right] += rgb_right[mask_right]
        count[mask_right] += 1

        resolved_mask = has_known_neighbor & (count > 0)
        known_rgb[resolved_mask] = (
            accum_rgb[resolved_mask] / count[resolved_mask][..., None]
        )
        known_flag[resolved_mask] = True
        to_resolve[resolved_mask] = False

    if np.any(to_resolve):
        issues.append("EDGE_DECONTAMINATION_UNCERTAIN")

    decon_mask = uncertain_mask & (~to_resolve)
    if np.any(decon_mask):
        diff = np.linalg.norm(known_rgb[decon_mask] - img_rgb[decon_mask], axis=-1)
        if np.any(diff > outlier_threshold):
            issues.append("EDGE_COLOUR_RECOVERY_OUTLIER")

    final_rgb = img_rgb.copy()
    final_rgb[uncertain_mask & ~to_resolve] = known_rgb[uncertain_mask & ~to_resolve]

    final_img_uint8 = np.clip(final_rgb * 255.0, 0.0, 255.0).astype(np.uint8)
    decontaminated_image = Image.fromarray(final_img_uint8, mode="RGB")

    return decontaminated_image, issues
