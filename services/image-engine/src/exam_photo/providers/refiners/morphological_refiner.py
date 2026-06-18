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


def _erode(mask: np.ndarray[Any, Any], radius: int, offsets: list[tuple[int, int]]) -> np.ndarray[Any, Any]:
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

        # 2. Compute effective radius
        radius = cfg.effective_radius(img_w, img_h)
        offsets = _disk_offsets(radius)

        # 3. Morphological Sequence (Closing -> Opening)
        mask_np = np.array(coarse_mask) > 127
        closed = _erode(_dilate(mask_np, radius, offsets), radius, offsets)
        opened = _dilate(_erode(closed, radius, offsets), radius, offsets)

        # 4. Face/Head Core Protection
        cleaned_binary = opened.copy()
        if cfg.preserve_face_core and face is not None:
            faces_list = face if isinstance(face, list) else [face]
            for f in faces_list:
                face_box = f.bounding_box
                # If coordinates are normalized, scale them to pixel space
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

                inner_left = max(
                    0, min(int(round(face_box.left + face_w * 0.1)), img_w - 1)
                )
                inner_right = max(
                    0, min(int(round(face_box.right - face_w * 0.1)), img_w)
                )
                inner_top = max(
                    0, min(int(round(face_box.top + face_h * 0.1)), img_h - 1)
                )
                inner_bottom = max(
                    0, min(int(round(face_box.bottom - face_h * 0.1)), img_h)
                )

                if inner_right > inner_left and inner_bottom > inner_top:
                    cleaned_binary[inner_top:inner_bottom, inner_left:inner_right] = (
                        True
                    )

        # 5. Alpha Smoothing in the boundary band
        boundary_offsets = _disk_offsets(radius)
        eroded_boundary = _erode(cleaned_binary, radius, boundary_offsets)
        dilated_boundary = _dilate(cleaned_binary, radius, boundary_offsets)
        boundary_band = dilated_boundary ^ eroded_boundary

        cleaned_binary_float = cleaned_binary.astype(np.float32)
        alpha = np.where(
            boundary_band,
            (1.0 - cfg.probability_weight) * cleaned_binary_float
            + cfg.probability_weight * probability_mask,
            cleaned_binary_float,
        )

        if cfg.gaussian_sigma > 0:
            alpha_uint8 = (alpha * 255.0).astype(np.uint8)
            alpha_img = Image.fromarray(alpha_uint8, mode="L")
            from PIL import ImageFilter

            blurred_img = alpha_img.filter(
                ImageFilter.GaussianBlur(radius=cfg.gaussian_sigma)
            )
            blurred_alpha = np.array(blurred_img, dtype=np.float32) / 255.0
            alpha = np.where(boundary_band, blurred_alpha, alpha)

        alpha = np.clip(alpha, 0.0, 1.0)

        # 6. Output Generation
        binary_arr = np.where(alpha >= 0.5, 255, 0).astype(np.uint8)
        refined_binary_mask = Image.fromarray(binary_arr, mode="L")

        # Trimap generation
        trimap_radius = max(1, cfg.trimap_band_width_px // 2)
        trimap_offsets = _disk_offsets(trimap_radius)
        eroded_trimap = _erode(cleaned_binary, trimap_radius, trimap_offsets)
        dilated_trimap = _dilate(cleaned_binary, trimap_radius, trimap_offsets)

        trimap_arr = np.zeros(cleaned_binary.shape, dtype=np.uint8)
        trimap_arr[dilated_trimap] = 128
        trimap_arr[eroded_trimap] = 255
        trimap = Image.fromarray(trimap_arr, mode="L")

        # 7. Validation
        validation_report = self._validate_refined_mask(
            coarse_mask, mask_np, alpha, refined_binary_mask
        )

        duration = (time.perf_counter() - start_time) * 1000.0

        try:
            return RefinedMaskResult(
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                refined_alpha_mask=alpha,
                refined_binary_mask=refined_binary_mask,
                trimap=trimap,
                input_width=img_w,
                input_height=img_h,
                effective_radius_px=radius,
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

        if coarse_iou < 0.90:
            issue_codes.append("REFINEMENT_COARSE_IOU_LOW")
            issues.append(
                RefinementValidationIssue(
                    code=SuitabilityIssueCode("REFINEMENT_COARSE_IOU_LOW"),
                    severity=IssueSeverity.WARNING,
                    blocking_for_processing=False,
                    confidence=1.0,
                )
            )

        coarse_coverage = float(np.mean(coarse_mask_np))
        if abs(foreground_coverage_ratio - coarse_coverage) > 0.15:
            issue_codes.append("REFINEMENT_COVERAGE_DIVERGED")
            issues.append(
                RefinementValidationIssue(
                    code=SuitabilityIssueCode("REFINEMENT_COVERAGE_DIVERGED"),
                    severity=IssueSeverity.WARNING,
                    blocking_for_processing=False,
                    confidence=1.0,
                )
            )

        is_valid = len(issues) == 0

        return RefinedMaskValidationReport(
            is_valid=is_valid,
            foreground_coverage_ratio=foreground_coverage_ratio,
            edge_transition_ratio=edge_transition_ratio,
            connectivity_improvement=connectivity_improvement,
            coarse_iou=coarse_iou,
            issue_codes=issue_codes,
            issues=issues,
        )
