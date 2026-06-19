import time
from typing import Any, Optional

import numpy as np
from PIL import Image, ImageColor

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.background_composition import (
    BackgroundCompositionConfig,
    BackgroundCompositionIssueCode,
    BackgroundCompositionResult,
    BackgroundCompositionValidationIssue,
    BackgroundCompositionValidationReport,
)
from exam_photo.suitability.issue_codes import IssueSeverity


class SolidBackgroundComposer:
    provider_name = "SolidBackgroundComposer"
    provider_version = "1.0.0"

    def compose_background(
        self,
        image: Image.Image,
        refined_alpha_mask: np.ndarray[Any, Any],
        config: Optional[BackgroundCompositionConfig] = None,
        crop_box: Optional[BoundingBox] = None,
    ) -> BackgroundCompositionResult:
        start_time = time.perf_counter()

        if config is None:
            config = BackgroundCompositionConfig()

        is_valid = True
        issues: list[BackgroundCompositionValidationIssue] = []
        issue_codes: list[BackgroundCompositionIssueCode] = []

        def add_issue(
            code: BackgroundCompositionIssueCode,
            severity: IssueSeverity = IssueSeverity.ERROR,
            blocking: bool = True,
        ) -> None:
            nonlocal is_valid
            if blocking:
                is_valid = False
            issue_codes.append(code)
            issues.append(
                BackgroundCompositionValidationIssue(
                    code=code, severity=severity, blocking_for_processing=blocking
                )
            )

        # 1. Validate Image
        if image is None or not isinstance(image, Image.Image):
            add_issue(BackgroundCompositionIssueCode.BACKGROUND_INPUT_INVALID)
            return self._build_failed_result(
                config, start_time, is_valid, issue_codes, issues, report_flags={}
            )

        if image.width <= 0 or image.height <= 0:
            add_issue(BackgroundCompositionIssueCode.BACKGROUND_INPUT_INVALID)
            return self._build_failed_result(
                config, start_time, is_valid, issue_codes, issues, report_flags={}
            )

        # 2. Validate Alpha Mask
        if refined_alpha_mask is None or not isinstance(refined_alpha_mask, np.ndarray):
            add_issue(BackgroundCompositionIssueCode.BACKGROUND_ALPHA_INVALID)
            return self._build_failed_result(
                config,
                start_time,
                is_valid,
                issue_codes,
                issues,
                report_flags={"input_dimensions_valid": True},
            )

        if refined_alpha_mask.ndim != 2:
            add_issue(BackgroundCompositionIssueCode.BACKGROUND_ALPHA_INVALID)
            return self._build_failed_result(
                config,
                start_time,
                is_valid,
                issue_codes,
                issues,
                report_flags={"input_dimensions_valid": True},
            )

        if refined_alpha_mask.dtype not in (np.float32, np.float64):
            add_issue(BackgroundCompositionIssueCode.BACKGROUND_ALPHA_INVALID)
            return self._build_failed_result(
                config,
                start_time,
                is_valid,
                issue_codes,
                issues,
                report_flags={"input_dimensions_valid": True},
            )

        if not np.isfinite(refined_alpha_mask).all():
            add_issue(BackgroundCompositionIssueCode.BACKGROUND_ALPHA_INVALID)
            return self._build_failed_result(
                config,
                start_time,
                is_valid,
                issue_codes,
                issues,
                report_flags={
                    "input_dimensions_valid": True,
                    "alpha_dimensions_valid": True,
                },
            )

        if np.any(refined_alpha_mask < 0.0) or np.any(refined_alpha_mask > 1.0):
            add_issue(BackgroundCompositionIssueCode.BACKGROUND_ALPHA_INVALID)
            return self._build_failed_result(
                config,
                start_time,
                is_valid,
                issue_codes,
                issues,
                report_flags={
                    "input_dimensions_valid": True,
                    "alpha_dimensions_valid": True,
                },
            )

        h, w = refined_alpha_mask.shape
        if w != image.width or h != image.height:
            add_issue(BackgroundCompositionIssueCode.BACKGROUND_MASK_SIZE_MISMATCH)
            return self._build_failed_result(
                config,
                start_time,
                is_valid,
                issue_codes,
                issues,
                report_flags={
                    "input_dimensions_valid": True,
                    "alpha_dimensions_valid": False,
                    "alpha_values_valid": True,
                },
            )

        # 3. Crop-aware composition
        working_img = image.convert("RGBA")
        working_alpha = refined_alpha_mask.copy()

        if crop_box is not None:
            c_left = int(crop_box.left)
            c_top = int(crop_box.top)
            c_right = int(crop_box.right)
            c_bottom = int(crop_box.bottom)

            if (
                c_left < 0
                or c_top < 0
                or c_right > w
                or c_bottom > h
                or crop_box.width <= 0
                or crop_box.height <= 0
            ):
                add_issue(BackgroundCompositionIssueCode.BACKGROUND_INPUT_INVALID)
                return self._build_failed_result(config, start_time, is_valid, issue_codes, issues, report_flags={"input_dimensions_valid": True, "alpha_dimensions_valid": True, "alpha_values_valid": True})
            
            working_img = working_img.crop((c_left, c_top, c_right, c_bottom))
            working_alpha = working_alpha[c_top:c_bottom, c_left:c_right]

        final_w, final_h = working_img.width, working_img.height

        # 4. Build solid background
        try:
            rgb_color = ImageColor.getrgb(config.target_colour_hex)
        except ValueError:
            add_issue(BackgroundCompositionIssueCode.BACKGROUND_COLOUR_INVALID)
            return self._build_failed_result(config, start_time, is_valid, issue_codes, issues, report_flags={"input_dimensions_valid": True, "alpha_dimensions_valid": True, "alpha_values_valid": True, "target_colour_valid": False})

        bg_color_tuple = (rgb_color[0], rgb_color[1], rgb_color[2], 255)
        bg_img = Image.new("RGBA", (final_w, final_h), color=bg_color_tuple)

        # 5. Alpha composite
        fg_arr = np.array(working_img, dtype=np.float32)
        bg_arr = np.array(bg_img, dtype=np.float32)
        alpha_3d = working_alpha[..., None]

        composed_arr = fg_arr * alpha_3d + bg_arr * (1.0 - alpha_3d)

        if config.allow_transparent_output:
            composed_arr[..., 3] = working_alpha * 255.0
        else:
            composed_arr[..., 3] = 255.0

        composed_image = Image.fromarray(np.clip(composed_arr, 0, 255).astype(np.uint8))
        if not config.allow_transparent_output:
            composed_image = composed_image.convert("RGB")

        # 6 & 7. Coverage validation
        total_pixels = final_w * final_h
        fg_pixels = np.count_nonzero(working_alpha >= config.alpha_threshold)
        coverage_ratio = float(fg_pixels / total_pixels) if total_pixels > 0 else 0.0

        if coverage_ratio < config.minimum_foreground_coverage:
            add_issue(BackgroundCompositionIssueCode.BACKGROUND_FOREGROUND_TOO_SMALL)
        elif coverage_ratio > config.maximum_foreground_coverage:
            add_issue(BackgroundCompositionIssueCode.BACKGROUND_FOREGROUND_TOO_LARGE)

        # 8. Halo / Fringe risk heuristics
        # Edge transition ratio: pixels with 0.1 < alpha < 0.9
        transition_pixels = np.count_nonzero(
            (working_alpha > 0.1) & (working_alpha < 0.9)
        )
        transition_ratio = (
            float(transition_pixels / total_pixels) if total_pixels > 0 else 0.0
        )

        # Low confidence edge: 0.3 < alpha < 0.7
        low_conf_pixels = np.count_nonzero(
            (working_alpha > 0.3) & (working_alpha < 0.7)
        )
        low_conf_ratio = (
            float(low_conf_pixels / total_pixels) if total_pixels > 0 else 0.0
        )

        halo_risk = transition_ratio
        fringe_risk = low_conf_ratio

        if halo_risk > 0.05:
            add_issue(
                BackgroundCompositionIssueCode.BACKGROUND_EDGE_HALO_RISK,
                severity=IssueSeverity.WARNING,
                blocking=False,
            )
        if fringe_risk > 0.02:
            add_issue(
                BackgroundCompositionIssueCode.BACKGROUND_EDGE_FRINGE_RISK,
                severity=IssueSeverity.WARNING,
                blocking=False,
            )
        if low_conf_ratio > 0.03 and not config.allow_low_confidence_edges:
            add_issue(
                BackgroundCompositionIssueCode.BACKGROUND_LOW_ALPHA_CONFIDENCE,
                severity=IssueSeverity.WARNING,
                blocking=False,
            )

        clipping_detected = False
        # Simple clipping check: if top of alpha mask touches top of image strongly
        if final_h > 0:
            top_edge_alpha = working_alpha[0, :]
            if np.any(top_edge_alpha > config.alpha_threshold):
                clipping_detected = True
                if not config.allow_subject_clipping:
                    add_issue(
                        BackgroundCompositionIssueCode.BACKGROUND_SUBJECT_CLIPPING_RISK
                    )

        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000.0

        report = BackgroundCompositionValidationReport(
            is_valid=is_valid,
            issue_codes=issue_codes,
            issues=issues,
            input_dimensions_valid=True,
            alpha_dimensions_valid=True,
            alpha_values_valid=True,
            target_colour_valid=True,
            foreground_coverage_ratio=coverage_ratio,
            edge_transition_ratio=transition_ratio,
            low_confidence_edge_ratio=low_conf_ratio,
            estimated_halo_risk_ratio=halo_risk,
            estimated_fringe_risk_ratio=fringe_risk,
            subject_clipping_detected=clipping_detected,
            mask_aware_validation_available=True,
        )

        return BackgroundCompositionResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            mode=config.mode,
            target_colour_hex=config.target_colour_hex,
            source_width=image.width,
            source_height=image.height,
            composed_width=final_w,
            composed_height=final_h,
            foreground_coverage_ratio=coverage_ratio,
            validation=report,
            processing_duration_ms=duration_ms,
            composed_image=composed_image,
            alpha_mask=working_alpha,
        )

    def _build_failed_result(
        self,
        config: BackgroundCompositionConfig,
        start_time: float,
        is_valid: bool,
        issue_codes: list[BackgroundCompositionIssueCode],
        issues: list[BackgroundCompositionValidationIssue],
        report_flags: dict[str, bool],
    ) -> BackgroundCompositionResult:
        end_time = time.perf_counter()

        report = BackgroundCompositionValidationReport(
            is_valid=is_valid,
            issue_codes=issue_codes,
            issues=issues,
            input_dimensions_valid=report_flags.get("input_dimensions_valid", False),
            alpha_dimensions_valid=report_flags.get("alpha_dimensions_valid", False),
            alpha_values_valid=report_flags.get("alpha_values_valid", False),
            target_colour_valid=report_flags.get("target_colour_valid", True),
            mask_aware_validation_available=False,
        )

        return BackgroundCompositionResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            mode=config.mode,
            target_colour_hex=config.target_colour_hex,
            source_width=0,
            source_height=0,
            composed_width=0,
            composed_height=0,
            validation=report,
            processing_duration_ms=(end_time - start_time) * 1000.0,
        )
