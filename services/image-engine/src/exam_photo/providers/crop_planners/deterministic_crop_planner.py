from __future__ import annotations

import math
import time
from typing import Any, List, Optional

import numpy as np
from PIL import Image

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.crop_planning import (
    CropConfig,
    CropIssueCode,
    CropMode,
    CropPlanner,
    CropPlanResult,
    CropValidationIssue,
    CropValidationReport,
)
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.suitability.issue_codes import IssueSeverity


class DeterministicCropPlanner(CropPlanner):
    """Local deterministic crop planner implementation for Crop Mode A."""

    def __init__(self) -> None:
        self.provider_name = "DeterministicCropPlanner"
        self.provider_version = "1.0.0"

    def plan_crop(
        self,
        image_width: int,
        image_height: int,
        face: FaceDetection,
        head_estimate: Optional[BoundingBox],
        refined_mask: Optional[Image.Image] = None,
        alpha_mask: Optional[np.ndarray[Any, Any]] = None,
        config: Optional[CropConfig] = None,
    ) -> CropPlanResult:
        start_time = time.perf_counter()
        cfg = config or CropConfig(target_aspect_ratio=1.0)

        issues: List[CropValidationIssue] = []
        issue_codes: List[CropIssueCode] = []

        def add_issue(
            code: CropIssueCode, severity: IssueSeverity, blocking: bool
        ) -> None:
            if code not in issue_codes:
                issue_codes.append(code)
                issues.append(
                    CropValidationIssue(
                        code=code,
                        severity=severity,
                        blocking_for_processing=blocking,
                        confidence=1.0,
                    )
                )

        # 1. Invalid input validation
        # Guard against zero/negative image dimensions
        if image_width <= 0 or image_height <= 0:
            add_issue(CropIssueCode.CROP_INPUT_INVALID, IssueSeverity.ERROR, True)
            return self._empty_failed_result(cfg, start_time, issues, issue_codes)

        # Guard against missing/multiple faces passed (if wrapped/passed incorrectly)
        if face is None or not hasattr(face, "bounding_box"):
            add_issue(CropIssueCode.CROP_INPUT_INVALID, IssueSeverity.ERROR, True)
            return self._empty_failed_result(cfg, start_time, issues, issue_codes)

        # 2. Resolve target aspect ratio and integer ratio scaling
        ratio_w: Optional[int] = None
        ratio_h: Optional[int] = None
        target_aspect: float

        if cfg.target_width is not None and cfg.target_height is not None:
            tw, th = cfg.target_width, cfg.target_height
            g = math.gcd(tw, th)
            ratio_w = tw // g
            ratio_h = th // g
            target_aspect = tw / th
        elif cfg.target_aspect_ratio is not None:
            target_aspect = cfg.target_aspect_ratio
        else:
            # Pydantic validation handles this, but defensive fallback
            add_issue(
                CropIssueCode.CROP_TARGET_ASPECT_MISSING, IssueSeverity.ERROR, True
            )
            return self._empty_failed_result(cfg, start_time, issues, issue_codes)

        # 3. Establish subject preservation box
        if head_estimate is not None:
            preserve_box = head_estimate
        else:
            # Fallback face-derived expanded box
            face_box = face.bounding_box
            face_w = face_box.width
            face_h = face_box.height
            preserve_box = BoundingBox(
                left=max(0.0, face_box.left - face_w * 0.25),
                top=max(0.0, face_box.top - face_h * 0.60),
                right=min(float(image_width), face_box.right + face_w * 0.25),
                bottom=min(float(image_height), face_box.bottom + face_h * 0.30),
            )

        # Refined mask refinement bounds expansion (Secondary validation / constraint)
        if refined_mask is not None:
            mask_arr = np.array(refined_mask)
            y_limit = int(round(preserve_box.bottom))
            if y_limit > 0:
                ys, xs = np.where(mask_arr[0:y_limit, :] > 127)
                if len(ys) > 0:
                    upper_mask_bbox = BoundingBox(
                        left=float(np.min(xs)),
                        top=float(np.min(ys)),
                        right=float(np.max(xs)),
                        bottom=float(np.max(ys)),
                    )
                    preserve_box = BoundingBox(
                        left=min(preserve_box.left, upper_mask_bbox.left),
                        top=min(preserve_box.top, upper_mask_bbox.top),
                        right=max(preserve_box.right, upper_mask_bbox.right),
                        bottom=max(preserve_box.bottom, upper_mask_bbox.bottom),
                    )

        # 4. Calculate minimal dimensions satisfying margins
        w_subject = preserve_box.width
        h_subject = preserve_box.height

        min_h_crop_from_subject = h_subject / (
            1.0 - cfg.minimum_top_margin_ratio - cfg.minimum_bottom_margin_ratio
        )
        min_w_crop_from_subject = w_subject / (
            1.0 - 2.0 * cfg.minimum_side_margin_ratio
        )

        # Minimum required height and width
        h_min = max(min_h_crop_from_subject, min_w_crop_from_subject / target_aspect)
        w_min = h_min * target_aspect

        # Aspect Size resolution via multiples if integer ratio is active
        w_crop: float
        h_crop: float
        if ratio_w is not None and ratio_h is not None:
            k_w = math.ceil(min_w_crop_from_subject / ratio_w)
            k_h = math.ceil(min_h_crop_from_subject / ratio_h)
            k = max(k_w, k_h)
            w_crop = float(ratio_w * k)
            h_crop = float(ratio_h * k)
        else:
            w_crop = w_min
            h_crop = h_min

        # 5. Position calculations under containment intervals
        face_box = face.bounding_box
        face_cx = (face_box.left + face_box.right) / 2.0
        face_cy = (face_box.top + face_box.bottom) / 2.0

        # Ideal top/left
        l_ideal = face_cx - w_crop / 2.0
        t_ideal = face_cy - cfg.preferred_face_center_y_ratio * h_crop

        # Containment limits (crop must contain the subject box)
        l_min = preserve_box.right - w_crop
        l_max = preserve_box.left
        t_min = preserve_box.bottom - h_crop
        t_max = preserve_box.top

        # Tight source detection: if subject size exceeds crop capacity
        source_too_tight = (l_max < l_min) or (t_min > t_max)
        if source_too_tight:
            add_issue(
                CropIssueCode.CROP_SOURCE_TOO_TIGHT,
                IssueSeverity.ERROR
                if not cfg.allow_subject_clipping
                else IssueSeverity.WARNING,
                not cfg.allow_subject_clipping,
            )

        # Containment interval projection helper
        def project(val: float, vmin: float, vmax: float) -> float:
            if vmin > vmax:
                return (vmin + vmax) / 2.0
            return max(vmin, min(val, vmax))

        # Position before clamping to image bounds
        ideal_l = project(l_ideal, l_min, l_max)
        ideal_t = project(t_ideal, t_min, t_max)

        ideal_l_rounded = int(round(ideal_l))
        ideal_t_rounded = int(round(ideal_t))
        ideal_r_rounded = ideal_l_rounded + int(round(w_crop))
        ideal_b_rounded = ideal_t_rounded + int(round(h_crop))

        ideal_crop_box = BoundingBox(
            left=float(ideal_l_rounded),
            top=float(ideal_t_rounded),
            right=float(ideal_r_rounded),
            bottom=float(ideal_b_rounded),
        )

        # Clamping to source boundaries
        clamped_l = max(0, min(ideal_l_rounded, image_width))
        clamped_t = max(0, min(ideal_t_rounded, image_height))
        clamped_r = max(clamped_l + 1, min(ideal_r_rounded, image_width))
        clamped_b = max(clamped_t + 1, min(ideal_b_rounded, image_height))

        crop_box = BoundingBox(
            left=float(clamped_l),
            top=float(clamped_t),
            right=float(clamped_r),
            bottom=float(clamped_b),
        )

        # Padding detection
        ideal_crop_inside_source = (
            ideal_l_rounded >= 0
            and ideal_t_rounded >= 0
            and ideal_r_rounded <= image_width
            and ideal_b_rounded <= image_height
        )
        padding_required = not ideal_crop_inside_source
        can_crop_without_padding = ideal_crop_inside_source
        crop_inside_source = True

        if padding_required:
            add_issue(CropIssueCode.CROP_PADDING_REQUIRED, IssueSeverity.WARNING, False)
            add_issue(
                CropIssueCode.CROP_BOX_OUT_OF_BOUNDS,
                IssueSeverity.ERROR if not cfg.allow_padding else IssueSeverity.WARNING,
                not cfg.allow_padding,
            )

        # 6. Preservation ratio checks
        head_coverage_ratio: Optional[float] = None
        if head_estimate is not None:
            inter = head_estimate.intersection(crop_box)
            if inter is not None:
                head_coverage_ratio = inter.area / head_estimate.area
            else:
                head_coverage_ratio = 0.0

            head_preservation_valid = head_coverage_ratio >= 0.999
            if not head_preservation_valid:
                add_issue(
                    CropIssueCode.CROP_HEAD_CLIPPED,
                    IssueSeverity.ERROR
                    if not cfg.allow_subject_clipping
                    else IssueSeverity.WARNING,
                    not cfg.allow_subject_clipping,
                )
        else:
            head_preservation_valid = None

        # Mask preservation ratio
        mask_preservation_ratio: Optional[float] = None
        mask_preservation_valid: Optional[bool] = None
        if refined_mask is not None:
            mask_arr = np.array(refined_mask)
            y_limit = int(round(preserve_box.bottom))
            if y_limit > 0:
                total_fg = np.sum(mask_arr[0:y_limit, :] > 127)
                if total_fg > 0:
                    y_start = max(0, min(clamped_t, y_limit))
                    y_end = max(0, min(clamped_b, y_limit))
                    fg_in_crop = np.sum(
                        mask_arr[y_start:y_end, clamped_l:clamped_r] > 127
                    )
                    mask_preservation_ratio = float(fg_in_crop / total_fg)
                    mask_preservation_valid = (
                        mask_preservation_ratio >= cfg.mask_preservation_threshold
                    )
                    if not mask_preservation_valid:
                        add_issue(
                            CropIssueCode.CROP_MASK_PRESERVATION_LOW,
                            IssueSeverity.ERROR
                            if not cfg.allow_subject_clipping
                            else IssueSeverity.WARNING,
                            not cfg.allow_subject_clipping,
                        )
                else:
                    mask_preservation_ratio = 1.0
                    mask_preservation_valid = True
            else:
                mask_preservation_ratio = 1.0
                mask_preservation_valid = True

        # Face containment check
        face_contained = crop_box.contains(face_box)
        if not face_contained:
            add_issue(
                CropIssueCode.CROP_SOURCE_TOO_TIGHT,
                IssueSeverity.ERROR,
                True,
            )

        # 7. Margins calculations for validation
        top_margin_px = max(0, int(round(preserve_box.top - clamped_t)))
        bottom_margin_px = max(0, int(round(clamped_b - preserve_box.bottom)))
        left_margin_px = max(0, int(round(preserve_box.left - clamped_l)))
        right_margin_px = max(0, int(round(clamped_r - preserve_box.right)))

        # Margin risk flags (relative to final crop height/width)
        crop_h_actual = clamped_b - clamped_t
        crop_w_actual = clamped_r - clamped_l

        if top_margin_px < cfg.minimum_top_margin_ratio * crop_h_actual:
            add_issue(CropIssueCode.CROP_TOP_HAIR_RISK, IssueSeverity.WARNING, False)
        if bottom_margin_px < cfg.minimum_bottom_margin_ratio * crop_h_actual:
            add_issue(CropIssueCode.CROP_CHIN_RISK, IssueSeverity.WARNING, False)
            add_issue(CropIssueCode.CROP_BEARD_RISK, IssueSeverity.WARNING, False)
            add_issue(
                CropIssueCode.CROP_HEAD_COVERING_RISK, IssueSeverity.WARNING, False
            )
        if (
            left_margin_px < cfg.minimum_side_margin_ratio * crop_w_actual
            or right_margin_px < cfg.minimum_side_margin_ratio * crop_w_actual
        ):
            add_issue(CropIssueCode.CROP_SIDE_HEAD_RISK, IssueSeverity.WARNING, False)

        # 8. Aspect and Centering errors
        ideal_crop_width = ideal_r_rounded - ideal_l_rounded
        ideal_crop_height = ideal_b_rounded - ideal_t_rounded
        crop_box_width = clamped_r - clamped_l
        crop_box_height = clamped_b - clamped_t

        crop_box_aspect_ratio = (
            crop_box_width / crop_box_height if crop_box_height > 0 else 1.0
        )
        ideal_crop_aspect_ratio = (
            ideal_crop_width / ideal_crop_height if ideal_crop_height > 0 else 1.0
        )

        if padding_required and not cfg.allow_padding:
            aspect_ratio_error = abs(crop_box_aspect_ratio - target_aspect)
        else:
            aspect_ratio_error = abs(ideal_crop_aspect_ratio - target_aspect)

        aspect_ratio_valid = aspect_ratio_error <= 1e-4

        if not aspect_ratio_valid:
            add_issue(
                CropIssueCode.CROP_ASPECT_RATIO_MISMATCH, IssueSeverity.ERROR, True
            )

        # Centering check
        face_center_x_ratio = (face_cx - ideal_l_rounded) / ideal_crop_width
        face_center_y_ratio = (face_cy - ideal_t_rounded) / ideal_crop_height

        face_centering_valid = (
            abs(face_center_x_ratio - 0.5) <= 0.05
            and abs(face_center_y_ratio - cfg.preferred_face_center_y_ratio)
            <= cfg.maximum_face_center_y_deviation
        )

        centering_severe = (
            abs(face_center_x_ratio - 0.5) > 0.15
            or abs(face_center_y_ratio - cfg.preferred_face_center_y_ratio)
            > 2.0 * cfg.maximum_face_center_y_deviation
        )

        if centering_severe:
            add_issue(CropIssueCode.CROP_FACE_NOT_CENTERED, IssueSeverity.ERROR, True)
        elif not face_centering_valid:
            add_issue(
                CropIssueCode.CROP_FACE_NOT_CENTERED, IssueSeverity.WARNING, False
            )

        subject_clipping_detected = (
            not face_contained
            or (head_preservation_valid is False)
            or (mask_preservation_valid is False)
        )

        is_valid = (
            len(
                [
                    iss
                    for iss in issues
                    if iss.blocking_for_processing
                    or iss.severity == IssueSeverity.ERROR
                ]
            )
            == 0
        )

        validation_report = CropValidationReport(
            is_valid=is_valid,
            issue_codes=issue_codes,
            issues=issues,
            crop_inside_source=crop_inside_source,
            ideal_crop_inside_source=ideal_crop_inside_source,
            aspect_ratio_valid=aspect_ratio_valid,
            face_contained=face_contained,
            head_preservation_valid=head_preservation_valid,
            mask_preservation_valid=mask_preservation_valid,
            padding_required=padding_required,
            valid_without_padding=can_crop_without_padding,
            subject_clipping_detected=subject_clipping_detected,
            top_margin_px=top_margin_px,
            bottom_margin_px=bottom_margin_px,
            left_margin_px=left_margin_px,
            right_margin_px=right_margin_px,
            head_estimate_unavailable=(head_estimate is None),
            segmentation_refinement_failed_or_skipped=(refined_mask is None),
            mask_aware_validation_unavailable=(refined_mask is None),
            fallback_source="face-only geometry" if head_estimate is None else None,
            face_centering_valid=face_centering_valid,
        )

        duration = (time.perf_counter() - start_time) * 1000.0

        return CropPlanResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            crop_mode=CropMode.EXACT_ASPECT,
            crop_box=crop_box,
            crop_box_width=crop_box_width,
            crop_box_height=crop_box_height,
            crop_box_aspect_ratio=crop_box_aspect_ratio,
            ideal_crop_box=ideal_crop_box,
            ideal_crop_width=ideal_crop_width,
            ideal_crop_height=ideal_crop_height,
            ideal_crop_aspect_ratio=ideal_crop_aspect_ratio,
            target_aspect_ratio=target_aspect,
            aspect_ratio_error=aspect_ratio_error,
            padding_required=padding_required,
            can_crop_without_padding=can_crop_without_padding,
            # Deprecated / compatibility fields
            crop_width=crop_box_width,
            crop_height=crop_box_height,
            crop_aspect_ratio=crop_box_aspect_ratio,
            face_center_x_ratio=face_center_x_ratio,
            face_center_y_ratio=face_center_y_ratio,
            head_coverage_ratio=head_coverage_ratio,
            mask_preservation_ratio=mask_preservation_ratio,
            validation=validation_report,
            processing_duration_ms=duration,
            preview_image=None,
        )

    def _empty_failed_result(
        self,
        cfg: CropConfig,
        start_time: float,
        issues: List[CropValidationIssue],
        issue_codes: List[CropIssueCode],
    ) -> CropPlanResult:
        duration = (time.perf_counter() - start_time) * 1000.0
        val = CropValidationReport(
            is_valid=False,
            issue_codes=issue_codes,
            issues=issues,
            crop_inside_source=False,
            ideal_crop_inside_source=False,
            aspect_ratio_valid=False,
            face_contained=False,
            padding_required=False,
            valid_without_padding=False,
            subject_clipping_detected=True,
            face_centering_valid=False,
        )
        return CropPlanResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            crop_mode=CropMode.EXACT_ASPECT,
            crop_box=BoundingBox(left=0.0, top=0.0, right=1.0, bottom=1.0),
            crop_box_width=1,
            crop_box_height=1,
            crop_box_aspect_ratio=1.0,
            ideal_crop_box=BoundingBox(left=0.0, top=0.0, right=1.0, bottom=1.0),
            ideal_crop_width=1,
            ideal_crop_height=1,
            ideal_crop_aspect_ratio=1.0,
            target_aspect_ratio=1.0,
            aspect_ratio_error=0.0,
            padding_required=False,
            can_crop_without_padding=False,
            crop_width=1,
            crop_height=1,
            crop_aspect_ratio=1.0,
            face_center_x_ratio=0.5,
            face_center_y_ratio=0.5,
            validation=val,
            processing_duration_ms=duration,
        )
