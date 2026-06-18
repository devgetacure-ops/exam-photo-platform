from typing import Any, Optional

import numpy as np
from PIL import Image

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.subject_segmentation import (
    MaskValidationReport,
    SegmentationConfig,
)


def count_connected_components_dsu(
    binary_mask: np.ndarray[Any, Any], max_size: int = 128
) -> tuple[int, float]:
    """Calculates connected components using a fast DSU algorithm in native Python.

    Downsamples the mask if larger than max_size to maintain CPU efficiency.
    Returns (component_count, largest_component_ratio).
    """
    h, w = binary_mask.shape
    if h > max_size or w > max_size:
        scale = max_size / max(h, w)
        new_h = int(round(h * scale))
        new_w = int(round(w * scale))

        img = Image.fromarray(binary_mask)
        img_resized = img.resize((new_w, new_h), resample=Image.Resampling.NEAREST)
        mask = np.array(img_resized)
    else:
        mask = binary_mask
        new_h, new_w = h, w

    parent: dict[int, int] = {}

    def find(x: int) -> int:
        path = []
        while parent[x] != x:
            path.append(x)
            x = parent[x]
        for node in path:
            parent[node] = x
        return x

    def union(x: int, y: int) -> None:
        root_x = find(x)
        root_y = find(y)
        if root_x != root_y:
            parent[root_x] = root_y

    coord_to_idx = {}
    idx_counter = 0
    for r in range(new_h):
        for c in range(new_w):
            if mask[r, c] == 255:
                coord_to_idx[(r, c)] = idx_counter
                parent[idx_counter] = idx_counter
                idx_counter += 1

    if idx_counter == 0:
        return 0, 0.0

    # 8-connected union
    for (r, c), idx in coord_to_idx.items():
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if (nr, nc) in coord_to_idx:
                    nidx = coord_to_idx[(nr, nc)]
                    union(idx, nidx)

    # Count sizes of each component
    sizes: dict[int, int] = {}
    for idx in range(idx_counter):
        root = find(idx)
        sizes[root] = sizes.get(root, 0) + 1

    # Ignore noise components (less than 5 pixels at max_size)
    filtered_sizes = {root: sz for root, sz in sizes.items() if sz >= 5}
    if not filtered_sizes:
        largest = max(sizes.values()) if sizes else 0
        return len(sizes), (largest / idx_counter if idx_counter > 0 else 0.0)

    count = len(filtered_sizes)
    largest = max(filtered_sizes.values())
    largest_ratio = largest / idx_counter

    return count, largest_ratio


def validate_segmentation_mask(
    probability_mask: np.ndarray[Any, Any],
    binary_mask: np.ndarray[Any, Any],
    config: SegmentationConfig,
    face: Optional[FaceDetection] = None,
    head_estimate: Optional[BoundingBox] = None,
) -> MaskValidationReport:
    """Validates the generated probability and coarse binary foreground masks."""
    h, w = binary_mask.shape
    issue_codes: list[str] = []

    # 1. Basic properties
    total_pixels = h * w
    foreground_count = np.sum(binary_mask == 255)
    foreground_coverage = foreground_count / total_pixels

    # Coverage validations
    if foreground_coverage < config.minimum_foreground_coverage:
        issue_codes.append("SEGMENTATION_FOREGROUND_COVERAGE_LOW")
    if foreground_coverage > config.maximum_foreground_coverage:
        issue_codes.append("SEGMENTATION_FOREGROUND_COVERAGE_HIGH")

    # Empty/full frame checks
    if foreground_count == 0:
        issue_codes.append("SEGMENTATION_MASK_EMPTY")
    if foreground_count == total_pixels:
        issue_codes.append("SEGMENTATION_MASK_FULL_FRAME")

    # 2. Uncertain-edge ratio
    uncertain_count = np.sum(
        (probability_mask >= config.uncertain_low_threshold)
        & (probability_mask <= config.uncertain_high_threshold)
    )
    uncertain_edge_ratio = uncertain_count / total_pixels
    if (
        uncertain_edge_ratio > 0.35
    ):  # threshold warning code if edge is excessively wide
        issue_codes.append("SEGMENTATION_UNCERTAIN_EDGE_HIGH")

    # 3. Connected components & fragmentation
    comp_count, largest_ratio = count_connected_components_dsu(binary_mask)
    if comp_count > 1:
        issue_codes.append("SEGMENTATION_MULTIPLE_MAJOR_COMPONENTS")
    if largest_ratio < 0.75:
        issue_codes.append("SEGMENTATION_FOREGROUND_FRAGMENTED")

    # 4. Bounding Box & edge contact
    foreground_indices = np.argwhere(binary_mask == 255)
    bbox: Optional[BoundingBox] = None
    edge_contact = False

    if len(foreground_indices) > 0:
        top_idx = int(np.min(foreground_indices[:, 0]))
        bottom_idx = int(np.max(foreground_indices[:, 0]))
        left_idx = int(np.min(foreground_indices[:, 1]))
        right_idx = int(np.max(foreground_indices[:, 1]))

        bbox = BoundingBox(
            left=float(left_idx),
            top=float(top_idx),
            right=float(right_idx + 1),
            bottom=float(bottom_idx + 1),
        )

        edge_contact = (
            top_idx == 0 or bottom_idx == h - 1 or left_idx == 0 or right_idx == w - 1
        )
        if edge_contact:
            issue_codes.append("SEGMENTATION_EDGE_CONTACT_WARNING")

    # 5. Face containment (against whole foreground probability)
    face_contained: Optional[bool] = None
    if face is not None:
        face_box = face.bounding_box
        face_w = face_box.right - face_box.left
        face_h = face_box.bottom - face_box.top

        # Evaluate central face region (eroded by 10% to avoid edge noise)
        inner_left = max(0, min(int(round(face_box.left + face_w * 0.1)), w - 1))
        inner_right = max(0, min(int(round(face_box.right - face_w * 0.1)), w))
        inner_top = max(0, min(int(round(face_box.top + face_h * 0.1)), h - 1))
        inner_bottom = max(0, min(int(round(face_box.bottom - face_h * 0.1)), h))

        if inner_right > inner_left and inner_bottom > inner_top:
            face_region_prob = probability_mask[
                inner_top:inner_bottom, inner_left:inner_right
            ]
            # Calculate face coverage: fraction of pixels above the foreground threshold
            face_pixels_above = np.sum(face_region_prob >= config.foreground_threshold)
            face_coverage = face_pixels_above / face_region_prob.size

            face_contained = bool(face_coverage >= config.minimum_face_mask_coverage)
            if not face_contained:
                issue_codes.append("SEGMENTATION_FACE_NOT_CONTAINED")
        else:
            face_contained = False
            issue_codes.append("SEGMENTATION_FACE_NOT_CONTAINED")

    # 6. Head region overlap comparison
    head_coverage_ratio: Optional[float] = None
    if head_estimate is not None:
        head_left = max(0, min(int(round(head_estimate.left)), w - 1))
        head_right = max(0, min(int(round(head_estimate.right)), w))
        head_top = max(0, min(int(round(head_estimate.top)), h - 1))
        head_bottom = max(0, min(int(round(head_estimate.bottom)), h))

        if head_right > head_left and head_bottom > head_top:
            head_region_mask = binary_mask[head_top:head_bottom, head_left:head_right]
            head_coverage_ratio = (
                np.sum(head_region_mask == 255) / head_region_mask.size
            )

            if head_coverage_ratio < config.minimum_head_mask_coverage:
                issue_codes.append("SEGMENTATION_HEAD_REGION_LOW_COVERAGE")
        else:
            head_coverage_ratio = 0.0
            issue_codes.append("SEGMENTATION_HEAD_REGION_LOW_COVERAGE")

    is_valid = not any(
        code
        for code in issue_codes
        if code
        in [
            "SEGMENTATION_MASK_EMPTY",
            "SEGMENTATION_MASK_FULL_FRAME",
            "SEGMENTATION_FACE_NOT_CONTAINED",
            "SEGMENTATION_FOREGROUND_COVERAGE_LOW",
            "SEGMENTATION_FOREGROUND_COVERAGE_HIGH",
        ]
    )

    return MaskValidationReport(
        is_valid=is_valid,
        foreground_coverage_ratio=foreground_coverage,
        uncertain_edge_ratio=uncertain_edge_ratio,
        connected_components_count=comp_count,
        largest_component_ratio=largest_ratio,
        mask_bounding_box=bbox,
        image_edge_contact=edge_contact,
        face_contained=face_contained,
        head_region_coverage_ratio=head_coverage_ratio,
        issue_codes=issue_codes,
    )
