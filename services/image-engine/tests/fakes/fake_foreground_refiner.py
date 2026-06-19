from __future__ import annotations

import time
from typing import Any, Optional

import numpy as np
from PIL import Image

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.foreground_refinement import (
    ForegroundRefinementProvider,
    RefinedMaskResult,
    RefinedMaskValidationReport,
    RefinementConfig,
)


class FakeForegroundRefiner(ForegroundRefinementProvider):
    """Fake refiner that returns the coarse mask converted to refinement formats."""

    def __init__(self) -> None:
        self.provider_name = "FakeForegroundRefiner"
        self.provider_version = "1.0.0"

    def refine_mask(
        self,
        coarse_mask: Image.Image,
        probability_mask: np.ndarray[Any, Any],
        face: Optional[FaceDetection | list[FaceDetection]] = None,
        config: Optional[RefinementConfig] = None,
        head_estimate: Optional[BoundingBox] = None,
    ) -> RefinedMaskResult:
        start_time = time.perf_counter()
        cfg = config or RefinementConfig()

        img_w, img_h = coarse_mask.size
        # Just convert coarse_mask directly to float32 alpha
        coarse_arr = np.array(coarse_mask)
        alpha = (coarse_arr / 255.0).astype(np.float32)

        # Trimap: 0 for 0, 255 for 255
        trimap_arr = np.where(coarse_arr > 127, 255, 0).astype(np.uint8)
        trimap = Image.fromarray(trimap_arr, mode="L")

        refined_binary = coarse_mask.copy()

        # Dummy validation report with all fields populated
        coarse_cov = float(np.mean(coarse_arr > 127))
        bbox = BoundingBox(left=0.0, top=0.0, right=float(img_w), bottom=float(img_h))
        val_report = RefinedMaskValidationReport(
            is_valid=True,
            foreground_coverage_before=coarse_cov,
            foreground_coverage_after=coarse_cov,
            foreground_coverage_delta=0.0,
            coarse_iou=1.0,
            edge_transition_ratio=0.0,
            unknown_trimap_ratio=0.0,
            definite_foreground_ratio=coarse_cov,
            definite_background_ratio=1.0 - coarse_cov,
            connected_components_before=1,
            connected_components_after=1,
            connectivity_improvement=True,
            face_coverage_before=None,
            face_coverage_after=None,
            face_coverage_delta=None,
            head_region_coverage_before=None,
            head_region_coverage_after=None,
            head_region_coverage_delta=None,
            bounding_box_before=bbox,
            bounding_box_after=bbox,
            large_hole_count=0,
            largest_hole_ratio=0.0,
            issue_codes=[],
            issues=[],
        )

        duration = (time.perf_counter() - start_time) * 1000.0

        return RefinedMaskResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            refined_alpha_mask=alpha,
            refined_binary_mask=refined_binary,
            trimap=trimap,
            input_width=img_w,
            input_height=img_h,
            effective_radius_px=cfg.effective_radius(img_w, img_h),
            refinement_duration_ms=duration,
            config_used=cfg,
            validation=val_report,
        )
