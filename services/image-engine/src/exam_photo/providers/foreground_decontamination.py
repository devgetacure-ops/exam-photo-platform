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
    h, w, _c = img_rgb.shape

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

    # Iterative propagation over the uncertain edge only.  The previous
    # implementation allocated and shifted several full-resolution HxW and
    # HxWx3 arrays on every iteration.  For a 10 MP phone photo that moved
    # gigabytes of memory even though only the thin uncertain-alpha boundary
    # can change.  Sparse coordinate gathers preserve the same four-neighbour
    # propagation rule while making work proportional to the edge band.
    for _step in range(max_search_distance):
        resolve_y, resolve_x = np.nonzero(to_resolve)
        if resolve_y.size == 0:
            break

        accum_rgb = np.zeros((resolve_y.size, 3), dtype=np.float32)
        count = np.zeros(resolve_y.size, dtype=np.float32)

        up = (resolve_y > 0) & known_flag[np.maximum(resolve_y - 1, 0), resolve_x]
        down = (resolve_y + 1 < h) & known_flag[
            np.minimum(resolve_y + 1, h - 1), resolve_x
        ]
        left = (resolve_x > 0) & known_flag[resolve_y, np.maximum(resolve_x - 1, 0)]
        right = (resolve_x + 1 < w) & known_flag[
            resolve_y, np.minimum(resolve_x + 1, w - 1)
        ]

        if np.any(up):
            accum_rgb[up] += known_rgb[resolve_y[up] - 1, resolve_x[up]]
            count[up] += 1.0
        if np.any(down):
            accum_rgb[down] += known_rgb[resolve_y[down] + 1, resolve_x[down]]
            count[down] += 1.0
        if np.any(left):
            accum_rgb[left] += known_rgb[resolve_y[left], resolve_x[left] - 1]
            count[left] += 1.0
        if np.any(right):
            accum_rgb[right] += known_rgb[resolve_y[right], resolve_x[right] + 1]
            count[right] += 1.0

        resolved = count > 0
        if not np.any(resolved):
            break

        resolved_y = resolve_y[resolved]
        resolved_x = resolve_x[resolved]
        known_rgb[resolved_y, resolved_x] = accum_rgb[resolved] / count[resolved, None]
        known_flag[resolved_y, resolved_x] = True
        to_resolve[resolved_y, resolved_x] = False

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
