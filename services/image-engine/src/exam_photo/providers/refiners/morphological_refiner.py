from __future__ import annotations

import time
from typing import Any, Optional

import numpy as np
from PIL import Image

from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.foreground_refinement import (
    ForegroundRefinementProvider,
    RefinedMaskResult,
    RefinedMaskValidationReport,
    RefinementConfig,
    RefinementValidationIssue,
)
from exam_photo.providers.refiners.errors import (
    RefinementInputError,
    RefinementOutputError,
)
from exam_photo.providers.segmenters.mask_validation import (
    count_connected_components_dsu,
)
from exam_photo.suitability.issue_codes import IssueSeverity, SuitabilityIssueCode


def _disk_offsets(radius: int) -> list[tuple[int, int]]:
    """Returns (dy, dx) offsets within a disk of given radius."""
    offsets = []
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dy * dy + dx * dx <= radius * radius:
                offsets.append((dy, dx))
    return offsets


def _erode(
    mask: np.ndarray[Any, Any], radius: int, offsets: list[tuple[int, int]]
) -> np.ndarray[Any, Any]:
    """Binary erosion: pixel is foreground only if ALL disk neighbours are foreground.

    Pads with background (False) to prevent boundary wraparound artifacts.
    """
    h, w = mask.shape
    padded = np.pad(mask, radius, mode="constant", constant_values=False)
    result = np.ones((h, w), dtype=bool)
    for dy, dx in offsets:
        shifted = padded[radius + dy : radius + dy + h, radius + dx : radius + dx + w]
        result &= shifted
    return result


def _dilate(
    mask: np.ndarray[Any, Any], radius: int, offsets: list[tuple[int, int]]
) -> np.ndarray[Any, Any]:
    """Binary dilation: pixel is foreground if ANY disk neighbour is foreground.

    Pads with background (False) to prevent boundary wraparound artifacts.
    """
    h, w = mask.shape
    padded = np.pad(mask, radius, mode="constant", constant_values=False)
    result = np.zeros((h, w), dtype=bool)
    for dy, dx in offsets:
        shifted = padded[radius + dy : radius + dy + h, radius + dx : radius + dx + w]
        result |= shifted
    return result


def _find_internal_holes(binary_mask: np.ndarray[Any, Any]) -> tuple[int, int]:
    """Finds internal holes in a binary mask (values 0 or 255).

    Returns (num_holes, max_hole_size_px).
    """
    h, w = binary_mask.shape
    max_size = 256
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

    # Invert mask: foreground (255) becomes 0, background (0) becomes 1
    bg = (mask == 0).astype(np.uint8)

    from collections import deque

    queue: deque[tuple[int, int]] = deque()

    # Flood fill starting from all border pixels of bg to identify external background
    for r in range(new_h):
        if bg[r, 0] == 1:
            bg[r, 0] = 2
            queue.append((r, 0))
        if bg[r, new_w - 1] == 1:
            bg[r, new_w - 1] = 2
            queue.append((r, new_w - 1))
    for c in range(1, new_w - 1):
        if bg[0, c] == 1:
            bg[0, c] = 2
            queue.append((0, c))
        if bg[new_h - 1, c] == 1:
            bg[new_h - 1, c] = 2
            queue.append((new_h - 1, c))

    while queue:
        r, c = queue.popleft()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < new_h and 0 <= nc < new_w:
                if bg[nr, nc] == 1:
                    bg[nr, nc] = 2
                    queue.append((nr, nc))

    # Now, any pixel with value 1 in bg is an internal hole!
    hole_count = 0
    max_hole_size = 0
    visited = np.zeros((new_h, new_w), dtype=bool)

    for r in range(new_h):
        for c in range(new_w):
            if bg[r, c] == 1 and not visited[r, c]:
                hole_count += 1
                hole_size = 0
                hq: deque[tuple[int, int]] = deque([(r, c)])
                visited[r, c] = True
                while hq:
                    curr_r, curr_c = hq.popleft()
                    hole_size += 1
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = curr_r + dr, curr_c + dc
                        if 0 <= nr < new_h and 0 <= nc < new_w:
                            if bg[nr, nc] == 1 and not visited[nr, nc]:
                                visited[nr, nc] = True
                                hq.append((nr, nc))
                max_hole_size = max(max_hole_size, hole_size)

    scale_factor = (h / new_h) * (w / new_w) if new_h > 0 else 1.0
    return hole_count, int(round(max_hole_size * scale_factor))


class MorphologicalForegroundRefiner(ForegroundRefinementProvider):
    """Refiner that performs boundary morphological operations using pure NumPy/Pillow."""

    def __init__(self) -> None:
        self.provider_name = "MorphologicalForegroundRefiner"
        self.provider_version = "1.0.0"

    def refine_mask(
        self,
        coarse_mask: Image.Image,
        probability_mask: np.ndarray[Any, Any],
        face: Optional[FaceDetection | list[FaceDetection]] = None,
        config: Optional[RefinementConfig] = None,
    ) -> RefinedMaskResult:
        start_time = time.perf_counter()
        cfg = config or RefinementConfig()

        # 1. Input Validation
        if not isinstance(coarse_mask, Image.Image):
            raise RefinementInputError("coarse_mask must be a PIL Image instance")
        if coarse_mask.mode != "L":
            raise RefinementInputError(
                f"coarse_mask must be L mode, got '{coarse_mask.mode}'"
            )

        if not isinstance(probability_mask, np.ndarray):
            raise RefinementInputError("probability_mask must be a numpy ndarray")
        if probability_mask.dtype != np.float32:
            raise RefinementInputError(
                f"probability_mask must be float32, got {probability_mask.dtype}"
            )
        if len(probability_mask.shape) != 2:
            raise RefinementInputError(
                f"probability_mask must be 2D, got shape {probability_mask.shape}"
            )

        img_w, img_h = coarse_mask.size
        mask_h, mask_w = probability_mask.shape
        if (img_w, img_h) != (mask_w, mask_h):
            raise RefinementInputError(
                f"Dimension mismatch between coarse_mask ({img_w}x{img_h}) and probability_mask ({mask_w}x{mask_h})"
            )

        if not np.all(np.isfinite(probability_mask)):
            raise RefinementInputError(
                "probability_mask must only contain finite values (no NaN or inf)"
            )

        if np.any((probability_mask < 0.0) | (probability_mask > 1.0)):
            raise RefinementInputError(
                "probability_mask values must strictly be in range [0.0, 1.0]"
            )

        # 2. Determine processing scale for morphology
        max_dim = 1024
        orig_w, orig_h = img_w, img_h
        if max(img_w, img_h) > max_dim:
            scale = max_dim / max(img_w, img_h)
            low_w = int(round(img_w * scale))
            low_h = int(round(img_h * scale))

            # Downscale coarse_mask and probability_mask
            coarse_mask_low = coarse_mask.resize(
                (low_w, low_h), Image.Resampling.NEAREST
            )
            prob_img = Image.fromarray(
                (probability_mask * 255.0).astype(np.uint8), mode="L"
            )
            prob_img_low = prob_img.resize((low_w, low_h), Image.Resampling.BILINEAR)
            prob_mask_low = np.array(prob_img_low, dtype=np.float32) / 255.0

            # Compute effective radius on the scaled dimensions
            radius = cfg.effective_radius(low_w, low_h)
        else:
            scale = 1.0
            low_w, low_h = img_w, img_h
            coarse_mask_low = coarse_mask
            prob_mask_low = probability_mask
            radius = cfg.effective_radius(img_w, img_h)

        offsets = _disk_offsets(radius)

        # 3. Morphological Sequence (Closing -> Opening) on low resolution
        mask_np_low = np.array(coarse_mask_low) > 127
        closed_low = _erode(_dilate(mask_np_low, radius, offsets), radius, offsets)
        opened_low = _dilate(_erode(closed_low, radius, offsets), radius, offsets)

        # 4. Face/Head Core Protection on low resolution
        cleaned_binary_low = opened_low.copy()
        if cfg.preserve_face_core and face is not None:
            faces_list = face if isinstance(face, list) else [face]
            for f in faces_list:
                face_box = f.bounding_box
                # If coordinates are normalized, scale them to low_w, low_h
                if (
                    face_box.left >= 0.0
                    and face_box.right <= 1.0
                    and face_box.top >= 0.0
                    and face_box.bottom <= 1.0
                    and (face_box.right - face_box.left) < 1.0
                ):
                    face_box = face_box.to_pixel(low_w, low_h)
                else:
                    # absolute: multiply by scale
                    face_box = face_box.__class__(
                        left=face_box.left * scale,
                        right=face_box.right * scale,
                        top=face_box.top * scale,
                        bottom=face_box.bottom * scale,
                    )

                face_w = face_box.right - face_box.left
                face_h = face_box.bottom - face_box.top

                inner_left = max(
                    0, min(int(round(face_box.left + face_w * 0.1)), low_w - 1)
                )
                inner_right = max(
                    0, min(int(round(face_box.right - face_w * 0.1)), low_w)
                )
                inner_top = max(
                    0, min(int(round(face_box.top + face_h * 0.1)), low_h - 1)
                )
                inner_bottom = max(
                    0, min(int(round(face_box.bottom - face_h * 0.1)), low_h)
                )

                if inner_right > inner_left and inner_bottom > inner_top:
                    cleaned_binary_low[
                        inner_top:inner_bottom, inner_left:inner_right
                    ] = True

        # 5. Alpha Smoothing in the boundary band on low resolution
        boundary_offsets = _disk_offsets(radius)
        eroded_boundary_low = _erode(cleaned_binary_low, radius, boundary_offsets)
        dilated_boundary_low = _dilate(cleaned_binary_low, radius, boundary_offsets)
        boundary_band_low = dilated_boundary_low ^ eroded_boundary_low

        cleaned_binary_float_low = cleaned_binary_low.astype(np.float32)
        alpha_low = np.where(
            boundary_band_low,
            (1.0 - cfg.probability_weight) * cleaned_binary_float_low
            + cfg.probability_weight * prob_mask_low,
            cleaned_binary_float_low,
        )

        sigma_low = cfg.gaussian_sigma * scale
        if sigma_low > 0:
            alpha_uint8_low = (alpha_low * 255.0).astype(np.uint8)
            alpha_img_low = Image.fromarray(alpha_uint8_low, mode="L")
            from PIL import ImageFilter

            blurred_img_low = alpha_img_low.filter(
                ImageFilter.GaussianBlur(radius=sigma_low)
            )
            blurred_alpha_low = np.array(blurred_img_low, dtype=np.float32) / 255.0
            alpha_low = np.where(boundary_band_low, blurred_alpha_low, alpha_low)

        alpha_low = np.clip(alpha_low, 0.0, 1.0)

        # 6. Trimap generation on low resolution
        trimap_radius_low = max(
            1, int(round(max(1, cfg.trimap_band_width_px // 2) * scale))
        )
        trimap_offsets_low = _disk_offsets(trimap_radius_low)
        eroded_trimap_low = _erode(
            cleaned_binary_low, trimap_radius_low, trimap_offsets_low
        )
        dilated_trimap_low = _dilate(
            cleaned_binary_low, trimap_radius_low, trimap_offsets_low
        )

        trimap_arr_low = np.zeros(cleaned_binary_low.shape, dtype=np.uint8)
        trimap_arr_low[dilated_trimap_low] = 128
        trimap_arr_low[eroded_trimap_low] = 255

        # 7. Upscale results back to original resolution if downscaled
        if scale != 1.0:
            # Upscale alpha
            alpha_low_img = Image.fromarray(
                (alpha_low * 255.0).astype(np.uint8), mode="L"
            )
            alpha_high_img = alpha_low_img.resize(
                (orig_w, orig_h), Image.Resampling.BILINEAR
            )
            alpha = np.array(alpha_high_img, dtype=np.float32) / 255.0
            alpha = np.clip(alpha, 0.0, 1.0)

            # Deriving refined binary mask from upscaled alpha
            binary_arr = np.where(alpha >= 0.5, 255, 0).astype(np.uint8)
            refined_binary_mask = Image.fromarray(binary_arr, mode="L")

            # Upscale trimap using NEAREST to maintain exact values 0, 128, 255
            trimap_low_img = Image.fromarray(trimap_arr_low, mode="L")
            trimap = trimap_low_img.resize((orig_w, orig_h), Image.Resampling.NEAREST)
        else:
            alpha = alpha_low
            binary_arr = np.where(alpha >= 0.5, 255, 0).astype(np.uint8)
            refined_binary_mask = Image.fromarray(binary_arr, mode="L")
            trimap = Image.fromarray(trimap_arr_low, mode="L")

        # 8. Validation on original resolution
        mask_np = np.array(coarse_mask) > 127
        validation_report = self._validate_refined_mask(
            coarse_mask, mask_np, alpha, refined_binary_mask, trimap, face
        )

        duration = (time.perf_counter() - start_time) * 1000.0

        try:
            return RefinedMaskResult(
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                refined_alpha_mask=alpha,
                refined_binary_mask=refined_binary_mask,
                trimap=trimap,
                input_width=orig_w,
                input_height=orig_h,
                effective_radius_px=radius
                if scale == 1.0
                else int(round(radius / scale)),
                refinement_duration_ms=duration,
                config_used=cfg,
                validation=validation_report,
            )
        except Exception as e:
            raise RefinementOutputError(
                f"Generated result failed contract validation: {e}"
            ) from e

    def _validate_refined_mask(
        self,
        coarse_mask_pil: Image.Image,
        coarse_mask_np: np.ndarray[Any, Any],
        refined_alpha_mask: np.ndarray[Any, Any],
        refined_binary_mask: Image.Image,
        trimap: Image.Image,
        face: Optional[FaceDetection | list[FaceDetection]] = None,
    ) -> RefinedMaskValidationReport:
        refined_arr = np.array(refined_binary_mask)
        refined_bin = np.where(refined_arr > 127, 255, 0).astype(np.uint8)
        foreground_coverage_ratio = float(np.mean(refined_bin == 255))

        edge_transition_ratio = float(
            np.sum((refined_alpha_mask > 1e-5) & (refined_alpha_mask < 1.0 - 1e-5))
            / refined_alpha_mask.size
        )

        coarse_bin = np.where(coarse_mask_np, 255, 0).astype(np.uint8)
        coarse_cc, _ = count_connected_components_dsu(coarse_bin)
        refined_cc, _ = count_connected_components_dsu(refined_bin)
        connectivity_improvement = refined_cc <= coarse_cc

        intersection = np.logical_and(coarse_mask_np, refined_arr > 127).sum()
        union = np.logical_or(coarse_mask_np, refined_arr > 127).sum()
        coarse_iou = float(intersection / union) if union > 0 else 1.0

        issue_codes = []
        issues = []

        # 1. Finite and range checks for alpha
        if (
            not np.all(np.isfinite(refined_alpha_mask))
            or np.any(refined_alpha_mask < -1e-5)
            or np.any(refined_alpha_mask > 1.00001)
        ):
            issue_codes.append("REFINEMENT_ALPHA_INVALID")
            issues.append(
                RefinementValidationIssue(
                    code=SuitabilityIssueCode.REFINEMENT_ALPHA_INVALID,
                    severity=IssueSeverity.ERROR,
                    blocking_for_processing=True,
                    confidence=1.0,
                )
            )

        # 2. Trimap value check
        trimap_arr = np.array(trimap)
        if np.any((trimap_arr != 0) & (trimap_arr != 128) & (trimap_arr != 255)):
            issue_codes.append("REFINEMENT_TRIMAP_INVALID")
            issues.append(
                RefinementValidationIssue(
                    code=SuitabilityIssueCode.REFINEMENT_TRIMAP_INVALID,
                    severity=IssueSeverity.ERROR,
                    blocking_for_processing=True,
                    confidence=1.0,
                )
            )

        # 3. Overall coverage checks
        coarse_coverage = float(np.mean(coarse_mask_np))
        if coarse_coverage > 0:
            coverage_ratio = foreground_coverage_ratio / coarse_coverage
            if coverage_ratio < 0.85:
                issue_codes.append("REFINEMENT_FOREGROUND_SHRANK_EXCESSIVELY")
                issues.append(
                    RefinementValidationIssue(
                        code=SuitabilityIssueCode.REFINEMENT_FOREGROUND_SHRANK_EXCESSIVELY,
                        severity=IssueSeverity.WARNING,
                        blocking_for_processing=False,
                        confidence=1.0,
                    )
                )
            elif coverage_ratio > 1.15:
                issue_codes.append("REFINEMENT_FOREGROUND_EXPANDED_EXCESSIVELY")
                issues.append(
                    RefinementValidationIssue(
                        code=SuitabilityIssueCode.REFINEMENT_FOREGROUND_EXPANDED_EXCESSIVELY,
                        severity=IssueSeverity.WARNING,
                        blocking_for_processing=False,
                        confidence=1.0,
                    )
                )

        # 4. Bounding box area shrinkage check
        y_indices, x_indices = np.where(coarse_mask_np)
        if len(y_indices) > 0:
            ymin, ymax = y_indices.min(), y_indices.max()
            xmin, xmax = x_indices.min(), x_indices.max()
            coarse_bbox_area = (ymax - ymin + 1) * (xmax - xmin + 1)

            ref_y, ref_x = np.where(refined_arr > 127)
            if len(ref_y) > 0:
                ref_ymin, ref_ymax = ref_y.min(), ref_y.max()
                ref_xmin, ref_xmax = ref_x.min(), ref_x.max()
                refined_bbox_area = (ref_ymax - ref_ymin + 1) * (
                    ref_xmax - ref_xmin + 1
                )

                if coarse_bbox_area > 0:
                    if refined_bbox_area / coarse_bbox_area < 0.85:
                        if (
                            "REFINEMENT_FOREGROUND_SHRANK_EXCESSIVELY"
                            not in issue_codes
                        ):
                            issue_codes.append(
                                "REFINEMENT_FOREGROUND_SHRANK_EXCESSIVELY"
                            )
                            issues.append(
                                RefinementValidationIssue(
                                    code=SuitabilityIssueCode.REFINEMENT_FOREGROUND_SHRANK_EXCESSIVELY,
                                    severity=IssueSeverity.WARNING,
                                    blocking_for_processing=False,
                                    confidence=1.0,
                                )
                            )

        # 5. Face coverage dropped check
        img_w, img_h = coarse_mask_pil.size
        if face is not None:
            faces_list = face if isinstance(face, list) else [face]
            for f in faces_list:
                face_box = f.bounding_box
                if (
                    face_box.left >= 0.0
                    and face_box.right <= 1.0
                    and face_box.top >= 0.0
                    and face_box.bottom <= 1.0
                    and (face_box.right - face_box.left) < 1.0
                ):
                    face_box = face_box.to_pixel(img_w, img_h)

                ymin, ymax = (
                    max(0, int(round(face_box.top))),
                    min(img_h, int(round(face_box.bottom))),
                )
                xmin, xmax = (
                    max(0, int(round(face_box.left))),
                    min(img_w, int(round(face_box.right))),
                )
                if ymax > ymin and xmax > xmin:
                    coarse_face_pixels = coarse_mask_np[ymin:ymax, xmin:xmax].sum()
                    refined_face_pixels = (
                        refined_arr[ymin:ymax, xmin:xmax] > 127
                    ).sum()
                    if coarse_face_pixels > 0:
                        face_ratio = refined_face_pixels / coarse_face_pixels
                        if face_ratio < 0.98:
                            issue_codes.append("REFINEMENT_FACE_COVERAGE_DROPPED")
                            issues.append(
                                RefinementValidationIssue(
                                    code=SuitabilityIssueCode.REFINEMENT_FACE_COVERAGE_DROPPED,
                                    severity=IssueSeverity.WARNING,
                                    blocking_for_processing=False,
                                    confidence=1.0,
                                )
                            )
                            break

        # 6. Head-region coverage dropped check
        if face is not None:
            faces_list = face if isinstance(face, list) else [face]
            for f in faces_list:
                face_box = f.bounding_box
                if (
                    face_box.left >= 0.0
                    and face_box.right <= 1.0
                    and face_box.top >= 0.0
                    and face_box.bottom <= 1.0
                    and (face_box.right - face_box.left) < 1.0
                ):
                    face_box = face_box.to_pixel(img_w, img_h)

                face_w = face_box.right - face_box.left
                face_h = face_box.bottom - face_box.top

                # Expand to head region
                head_ymin = max(0, int(round(face_box.top - face_h * 0.5)))
                head_ymax = min(img_h, int(round(face_box.bottom + face_h * 0.1)))
                head_xmin = max(0, int(round(face_box.left - face_w * 0.2)))
                head_xmax = min(img_w, int(round(face_box.right + face_w * 0.2)))

                if head_ymax > head_ymin and head_xmax > head_xmin:
                    coarse_head_pixels = coarse_mask_np[
                        head_ymin:head_ymax, head_xmin:head_xmax
                    ].sum()
                    refined_head_pixels = (
                        refined_arr[head_ymin:head_ymax, head_xmin:head_xmax] > 127
                    ).sum()
                    if coarse_head_pixels > 0:
                        head_ratio = refined_head_pixels / coarse_head_pixels
                        if head_ratio < 0.95:
                            issue_codes.append("REFINEMENT_HEAD_COVERAGE_DROPPED")
                            issues.append(
                                RefinementValidationIssue(
                                    code=SuitabilityIssueCode.REFINEMENT_HEAD_COVERAGE_DROPPED,
                                    severity=IssueSeverity.WARNING,
                                    blocking_for_processing=False,
                                    confidence=1.0,
                                )
                            )
                            break

        # 7. Connected components/Subject fragmented
        if refined_cc > 1:
            issue_codes.append("REFINEMENT_SUBJECT_FRAGMENTED")
            issues.append(
                RefinementValidationIssue(
                    code=SuitabilityIssueCode.REFINEMENT_SUBJECT_FRAGMENTED,
                    severity=IssueSeverity.WARNING,
                    blocking_for_processing=False,
                    confidence=1.0,
                )
            )

        # 8. Large internal holes
        hole_count, max_hole_size = _find_internal_holes(refined_arr)
        if hole_count > 0 and max_hole_size > 1000:
            issue_codes.append("REFINEMENT_LARGE_HOLES_DETECTED")
            issues.append(
                RefinementValidationIssue(
                    code=SuitabilityIssueCode.REFINEMENT_LARGE_HOLES_DETECTED,
                    severity=IssueSeverity.WARNING,
                    blocking_for_processing=False,
                    confidence=1.0,
                )
            )

        # 9. Excessive transition edge band
        if edge_transition_ratio > 0.15:
            issue_codes.append("REFINEMENT_EDGE_BAND_EXCESSIVE")
            issues.append(
                RefinementValidationIssue(
                    code=SuitabilityIssueCode.REFINEMENT_EDGE_BAND_EXCESSIVE,
                    severity=IssueSeverity.WARNING,
                    blocking_for_processing=False,
                    confidence=1.0,
                )
            )

        # 10. Coarse IoU check
        if coarse_iou < 0.90:
            if "REFINEMENT_COARSE_IOU_LOW" not in issue_codes:
                issue_codes.append("REFINEMENT_COARSE_IOU_LOW")
                issues.append(
                    RefinementValidationIssue(
                        code=SuitabilityIssueCode.REFINEMENT_COARSE_IOU_LOW,
                        severity=IssueSeverity.WARNING,
                        blocking_for_processing=False,
                        confidence=1.0,
                    )
                )

        if abs(foreground_coverage_ratio - coarse_coverage) > 0.15:
            if "REFINEMENT_COVERAGE_DIVERGED" not in issue_codes:
                issue_codes.append("REFINEMENT_COVERAGE_DIVERGED")
                issues.append(
                    RefinementValidationIssue(
                        code=SuitabilityIssueCode.REFINEMENT_COVERAGE_DIVERGED,
                        severity=IssueSeverity.WARNING,
                        blocking_for_processing=False,
                        confidence=1.0,
                    )
                )

        is_valid = (
            len([iss for iss in issues if iss.severity == IssueSeverity.ERROR]) == 0
        )

        return RefinedMaskValidationReport(
            is_valid=is_valid,
            foreground_coverage_ratio=foreground_coverage_ratio,
            edge_transition_ratio=edge_transition_ratio,
            connectivity_improvement=connectivity_improvement,
            coarse_iou=coarse_iou,
            issue_codes=issue_codes,
            issues=issues,
        )
