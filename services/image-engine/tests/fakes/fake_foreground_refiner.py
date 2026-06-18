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

        # Dummy validation report
        val_report = RefinedMaskValidationReport(
            is_valid=True,
            foreground_coverage_ratio=float(np.mean(trimap_arr == 255)),
            edge_transition_ratio=0.0,
            connectivity_improvement=True,
            coarse_iou=1.0,
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
