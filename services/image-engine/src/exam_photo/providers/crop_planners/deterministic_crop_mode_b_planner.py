from __future__ import annotations

import time
from typing import List, Optional

import numpy as np
from PIL import Image

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.crop_planning import (
    CropIssueCode,
    CropMode,
    CropModeBConfig,
    CropModeBResult,
    CropValidationIssue,
    CropValidationReport,
)
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.portrait_composition import PortraitCompositionResult
from exam_photo.suitability.issue_codes import IssueSeverity


class DeterministicCropModeBPlanner:
    """Local deterministic crop planner implementation for Crop Mode B.

    IMPORTANT SIZING SEMANTICS NOTE:
    For Indian exam photo specifications, target width and height ranges (e.g. min_width, max_width,
    min_height, max_height) are typically requirements for the FINAL resized output image.
    Because image resizing, scaling, and compression are out of scope for this planning milestone,
    these ranges are currently evaluated as constraints directly on the SOURCE-PIXEL crop window
    itself (i.e. compatibility planning). Resizing and final output generation will be implemented
    in a future milestone, at which point these constraints will map to the resized output size.
    """

    def __init__(self) -> None:
        self.provider_name = "DeterministicCropModeBPlanner"
        self.provider_version = "1.0.0"

    def plan_crop(
        self,
        image_width: int,
        image_height: int,
        face: FaceDetection,
        head_estimate: Optional[BoundingBox],
        refined_mask: Optional[Image.Image] = None,
        portrait_composition: Optional[PortraitCompositionResult] = None,
        config: Optional[CropModeBConfig] = None,
    ) -> CropModeBResult:
        start_time = time.perf_counter()
        cfg = config or CropModeBConfig()

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
        if image_width <= 0 or image_height <= 0:
            add_issue(CropIssueCode.CROP_B_INPUT_INVALID, IssueSeverity.ERROR, True)
            return self._empty_failed_result(cfg, start_time, issues, issue_codes)

        if face is None or not hasattr(face, "bounding_box"):
            add_issue(CropIssueCode.CROP_B_INPUT_INVALID, IssueSeverity.ERROR, True)
            return self._empty_failed_result(cfg, start_time, issues, issue_codes)

        # 2. Establish subject preservation box
        composition_box: Optional[BoundingBox] = None
        if portrait_composition is not None:
            preserve_box = portrait_composition.preservation_box
            composition_box = portrait_composition.preservation_box
        elif head_estimate is not None:
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

        h_head = preserve_box.height

        # Limit refined mask y-limit to protect hair, beard, scarf, neck
        if refined_mask is not None:
            mask_arr = np.array(refined_mask)
            y_limit = int(round(face.bounding_box.bottom))
            if y_limit > 0:
                x_start = max(
                    0, int(round(preserve_box.left - preserve_box.width * 0.35))
                )
                x_end = min(
                    image_width,
                    int(round(preserve_box.right + preserve_box.width * 0.35)),
                )
                sub_mask = mask_arr[0 : min(image_height, y_limit), x_start:x_end]
                ys_sub, xs_sub = np.where(sub_mask > 127)
                if len(ys_sub) > 0:
                    ys = ys_sub
                    xs = xs_sub + x_start
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

        # 3. Calculate target aspect and ideal size
        # Derive aspect ratio limits
        min_aspect = cfg.min_aspect_ratio
        if min_aspect is None:
            if cfg.min_width is not None and cfg.max_height is not None:
                min_aspect = cfg.min_width / cfg.max_height
            else:
                min_aspect = 0.1

        max_aspect = cfg.max_aspect_ratio
        if max_aspect is None:
            if cfg.max_width is not None and cfg.min_height is not None:
                max_aspect = cfg.max_width / cfg.min_height
            else:
                max_aspect = 10.0

        if min_aspect > max_aspect:
            # Range configuration error
            add_issue(CropIssueCode.CROP_B_RANGE_INVALID, IssueSeverity.ERROR, True)
            return self._empty_failed_result(cfg, start_time, issues, issue_codes)

        # Natural crop aspect
        aspect = max(min_aspect, min(cfg.preferred_aspect_ratio, max_aspect))

        # Size required for subject + margins
        w_subject = preserve_box.width
        h_subject = preserve_box.height

        min_h_crop_from_subject = h_subject / (
            1.0 - cfg.minimum_top_margin_ratio - cfg.minimum_bottom_margin_ratio
        )
        min_w_crop_from_subject = w_subject / (
            1.0 - 2.0 * cfg.minimum_side_margin_ratio
        )

        desired_crop_height = h_head / cfg.target_head_height_ratio

        # Sizing limits on height
        h_low = max(
            min_h_crop_from_subject,
            min_w_crop_from_subject / aspect,
            float(cfg.min_height or 0.0),
            float(cfg.min_width or 0.0) / aspect,
        )
        h_low = max(h_low, h_head / cfg.max_head_height_ratio)

        h_high = h_head / cfg.min_head_height_ratio
        if cfg.max_height is not None:
            h_high = min(h_high, float(cfg.max_height))
        if cfg.max_width is not None:
            h_high = min(h_high, float(cfg.max_width) / aspect)

        if h_low <= h_high:
            h_crop = max(h_low, min(desired_crop_height, h_high))
        else:
            # Conflicting constraints: prioritize preserving the subject and margins
            h_crop = h_low

        w_crop = h_crop * aspect

        # 4. Position calculation with containment and inward shifting
        face_box = face.bounding_box
        face_cx = (face_box.left + face_box.right) / 2.0
        face_cy = (face_box.top + face_box.bottom) / 2.0

        l_ideal = face_cx - w_crop / 2.0
        t_ideal = face_cy - cfg.preferred_face_center_y_ratio * h_crop

        # Containment limits (crop must contain the subject box)
        l_min = preserve_box.right - w_crop
        l_max = preserve_box.left
        t_min = preserve_box.bottom - h_crop
        t_max = preserve_box.top

        # Inward shifting with margin preservation
        min_side_margin_px = cfg.minimum_side_margin_ratio * w_crop
        l_margin_min = preserve_box.right + min_side_margin_px - w_crop
        l_margin_max = preserve_box.left - min_side_margin_px

        l_allowed_min = max(l_min, l_margin_min, 0.0)
        l_allowed_max = min(l_max, l_margin_max, float(image_width) - w_crop)

        if l_allowed_min <= l_allowed_max:
            ideal_l = max(l_allowed_min, min(l_ideal, l_allowed_max))
        else:
            # Fallback if margins cannot be satisfied
            l_fallback_min = max(l_min, 0.0)
            l_fallback_max = min(l_max, float(image_width) - w_crop)
            if l_fallback_min <= l_fallback_max:
                ideal_l = max(l_fallback_min, min(l_ideal, l_fallback_max))
            else:
                ideal_l = max(l_min, min(l_ideal, l_max))

        min_top_margin_px = cfg.minimum_top_margin_ratio * h_crop
        min_bottom_margin_px = cfg.minimum_bottom_margin_ratio * h_crop
        t_margin_min = preserve_box.bottom + min_bottom_margin_px - h_crop
        t_margin_max = preserve_box.top - min_top_margin_px

        t_allowed_min = max(t_min, t_margin_min, 0.0)
        t_allowed_max = min(t_max, t_margin_max, float(image_height) - h_crop)

        if t_allowed_min <= t_allowed_max:
            ideal_t = max(t_allowed_min, min(t_ideal, t_allowed_max))
        else:
            # Fallback if margins cannot be satisfied
            t_fallback_min = max(t_min, 0.0)
            t_fallback_max = min(t_max, float(image_height) - h_crop)
            if t_fallback_min <= t_fallback_max:
                ideal_t = max(t_fallback_min, min(t_ideal, t_fallback_max))
            else:
                ideal_t = max(t_min, min(t_ideal, t_max))

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

        clamped_l = max(0, min(ideal_l_rounded, image_width))
        clamped_t = max(0, min(ideal_t_rounded, image_height))
        clamped_r = max(clamped_l + 1, min(ideal_r_rounded, image_width))
        clamped_b = max(clamped_t + 1, min(ideal_b_rounded, image_height))

        if cfg.allow_padding:
            crop_box = ideal_crop_box
        else:
            crop_box = BoundingBox(
                left=float(clamped_l),
                top=float(clamped_t),
                right=float(clamped_r),
                bottom=float(clamped_b),
            )

        crop_box_width = clamped_r - clamped_l
        crop_box_height = clamped_b - clamped_t
        crop_box_aspect_ratio = crop_box_width / crop_box_height

        ideal_crop_width = ideal_r_rounded - ideal_l_rounded
        ideal_crop_height = ideal_b_rounded - ideal_t_rounded
        ideal_crop_aspect_ratio = ideal_crop_width / ideal_crop_height

        # 5. Padding detection
        ideal_crop_inside_source = (
            ideal_l_rounded >= 0
            and ideal_t_rounded >= 0
            and ideal_r_rounded <= image_width
            and ideal_b_rounded <= image_height
        )
        padding_required = not ideal_crop_inside_source
        can_crop_without_padding = ideal_crop_inside_source

        if padding_required:
            add_issue(
                CropIssueCode.CROP_B_PADDING_REQUIRED,
                IssueSeverity.ERROR if not cfg.allow_padding else IssueSeverity.WARNING,
                not cfg.allow_padding,
            )

        # 6. Preservation ratio checks
        head_coverage_ratio: Optional[float] = None
        head_preservation_valid: Optional[bool] = None
        preservation_reference_box = composition_box or head_estimate
        if preservation_reference_box is not None:
            inter = preservation_reference_box.intersection(crop_box)
            if inter is not None:
                head_coverage_ratio = inter.area / preservation_reference_box.area
            else:
                head_coverage_ratio = 0.0

            head_preservation_valid = head_coverage_ratio >= 0.999
            if not head_preservation_valid:
                add_issue(
                    CropIssueCode.CROP_B_HEAD_CLIPPED,
                    IssueSeverity.ERROR
                    if not cfg.allow_subject_clipping
                    else IssueSeverity.WARNING,
                    not cfg.allow_subject_clipping,
                )

        mask_preservation_ratio: Optional[float] = None
        mask_preservation_valid: Optional[bool] = None
        if refined_mask is not None:
            mask_arr = np.array(refined_mask)
            y_limit = int(round(face.bounding_box.bottom))
            if y_limit > 0:
                # Restrict columns to subject area of interest to avoid noise/shoulder pollution
                sub_l = int(round(preserve_box.left))
                sub_r = int(round(preserve_box.right))
                total_fg = np.sum(
                    mask_arr[0 : min(image_height, y_limit), sub_l:sub_r] > 127
                )
                if total_fg > 0:
                    y_start = max(0, min(clamped_t, y_limit))
                    y_end = max(0, min(clamped_b, y_limit))
                    x_start_crop = max(clamped_l, sub_l)
                    x_end_crop = min(clamped_r, sub_r)
                    fg_in_crop = np.sum(
                        mask_arr[y_start:y_end, x_start_crop:x_end_crop] > 127
                    )
                    mask_preservation_ratio = float(fg_in_crop / total_fg)
                    mask_preservation_valid = (
                        mask_preservation_ratio >= cfg.mask_preservation_threshold
                    )
                    if not mask_preservation_valid:
                        add_issue(
                            CropIssueCode.CROP_B_MASK_PRESERVATION_LOW,
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

        # Face containment
        face_contained = crop_box.contains(face_box)
        if not face_contained:
            add_issue(
                CropIssueCode.CROP_B_SOURCE_TOO_TIGHT,
                IssueSeverity.ERROR,
                True,
            )

        # 7. Margins calculations for validation
        top_margin_px = max(0, int(round(preserve_box.top - clamped_t)))
        bottom_margin_px = max(0, int(round(clamped_b - preserve_box.bottom)))
        left_margin_px = max(0, int(round(preserve_box.left - clamped_l)))
        right_margin_px = max(0, int(round(clamped_r - preserve_box.right)))

        if top_margin_px < cfg.minimum_top_margin_ratio * crop_box_height:
            add_issue(CropIssueCode.CROP_B_TOP_HAIR_RISK, IssueSeverity.WARNING, False)
        if bottom_margin_px < cfg.minimum_bottom_margin_ratio * crop_box_height:
            add_issue(CropIssueCode.CROP_B_CHIN_RISK, IssueSeverity.WARNING, False)
            add_issue(CropIssueCode.CROP_B_BEARD_RISK, IssueSeverity.WARNING, False)
            add_issue(
                CropIssueCode.CROP_B_HEAD_COVERING_RISK, IssueSeverity.WARNING, False
            )
        if (
            left_margin_px < cfg.minimum_side_margin_ratio * crop_box_width
            or right_margin_px < cfg.minimum_side_margin_ratio * crop_box_width
        ):
            add_issue(CropIssueCode.CROP_B_SIDE_HEAD_RISK, IssueSeverity.WARNING, False)

        # 8. Head-height ratio validation (based on actual executable crop box)
        head_height_ratio = h_head / crop_box_height
        if head_height_ratio < cfg.min_head_height_ratio:
            add_issue(CropIssueCode.CROP_B_HEAD_RATIO_LOW, IssueSeverity.ERROR, True)
        elif head_height_ratio > cfg.max_head_height_ratio:
            add_issue(CropIssueCode.CROP_B_HEAD_RATIO_HIGH, IssueSeverity.ERROR, True)

        # 9. Centering validation
        face_center_x_ratio = (face_cx - clamped_l) / crop_box_width
        face_center_y_ratio = (face_cy - clamped_t) / crop_box_height

        w_head = preserve_box.width
        eye_y = face.bounding_box.top + 0.3 * face.bounding_box.height
        if (
            face.landmarks is not None
            and face.landmarks.left_eye is not None
            and face.landmarks.right_eye is not None
        ):
            eye_y = (face.landmarks.left_eye.y + face.landmarks.right_eye.y) / 2.0

        has_portrait_reference = preservation_reference_box is not None
        head_width_ratio = w_head / crop_box_width if has_portrait_reference else None
        top_margin_ratio = (
            (preserve_box.top - clamped_t) / crop_box_height
            if has_portrait_reference
            else None
        )
        eye_line_ratio = (
            (eye_y - clamped_t) / crop_box_height if has_portrait_reference else None
        )
        crop_cx = (clamped_l + clamped_r) / 2.0
        center_offset_ratio = abs(face_cx - crop_cx) / crop_box_width
        torso_inclusion_ratio = (
            max(0.0, clamped_b - preserve_box.bottom) / crop_box_height
            if has_portrait_reference
            else None
        )

        face_centering_valid = (
            abs(face_center_x_ratio - cfg.preferred_face_center_x_ratio)
            <= cfg.maximum_face_center_x_deviation
            and abs(face_center_y_ratio - cfg.preferred_face_center_y_ratio)
            <= cfg.maximum_face_center_y_deviation
        )
        if not face_centering_valid:
            centering_severe = (
                abs(face_center_x_ratio - cfg.preferred_face_center_x_ratio)
                > 2.0 * cfg.maximum_face_center_x_deviation
                or abs(face_center_y_ratio - cfg.preferred_face_center_y_ratio)
                > 2.0 * cfg.maximum_face_center_y_deviation
            )
            add_issue(
                CropIssueCode.CROP_B_FACE_NOT_CENTERED,
                IssueSeverity.ERROR if centering_severe else IssueSeverity.WARNING,
                centering_severe,
            )

        # 10. Range checks compatibility
        width_within_range = None
        if cfg.min_width is not None or cfg.max_width is not None:
            in_range = True
            if cfg.min_width is not None and crop_box_width < cfg.min_width:
                in_range = False
            if cfg.max_width is not None and crop_box_width > cfg.max_width:
                in_range = False
            width_within_range = in_range
            if not in_range:
                add_issue(
                    CropIssueCode.CROP_B_WIDTH_OUT_OF_RANGE,
                    IssueSeverity.WARNING,
                    False,
                )

        height_within_range = None
        if cfg.min_height is not None or cfg.max_height is not None:
            in_range = True
            if cfg.min_height is not None and crop_box_height < cfg.min_height:
                in_range = False
            if cfg.max_height is not None and crop_box_height > cfg.max_height:
                in_range = False
            height_within_range = in_range
            if not in_range:
                add_issue(
                    CropIssueCode.CROP_B_HEIGHT_OUT_OF_RANGE,
                    IssueSeverity.WARNING,
                    False,
                )

        aspect_within_range = None
        if cfg.min_aspect_ratio is not None or cfg.max_aspect_ratio is not None:
            in_range = True
            if (
                cfg.min_aspect_ratio is not None
                and crop_box_aspect_ratio < cfg.min_aspect_ratio - 1e-4
            ):
                in_range = False
            if (
                cfg.max_aspect_ratio is not None
                and crop_box_aspect_ratio > cfg.max_aspect_ratio + 1e-4
            ):
                in_range = False
            aspect_within_range = in_range
            if not in_range:
                add_issue(
                    CropIssueCode.CROP_B_ASPECT_OUT_OF_RANGE, IssueSeverity.ERROR, True
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
            crop_inside_source=True,
            ideal_crop_inside_source=ideal_crop_inside_source,
            aspect_ratio_valid=(aspect_within_range is not False),
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

        return CropModeBResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            crop_mode=CropMode.HEAD_LED_RANGE,
            crop_box=crop_box,
            crop_box_width=crop_box_width,
            crop_box_height=crop_box_height,
            crop_box_aspect_ratio=crop_box_aspect_ratio,
            ideal_crop_box=ideal_crop_box,
            ideal_crop_width=ideal_crop_width,
            ideal_crop_height=ideal_crop_height,
            ideal_crop_aspect_ratio=ideal_crop_aspect_ratio,
            head_height_ratio=head_height_ratio,
            head_width_ratio=head_width_ratio,
            top_margin_ratio=top_margin_ratio,
            eye_line_ratio=eye_line_ratio,
            center_offset_ratio=center_offset_ratio,
            torso_inclusion_ratio=torso_inclusion_ratio,
            portrait_composition_box=composition_box,
            face_center_x_ratio=face_center_x_ratio,
            face_center_y_ratio=face_center_y_ratio,
            head_coverage_ratio=head_coverage_ratio,
            mask_preservation_ratio=mask_preservation_ratio,
            width_within_range=width_within_range,
            height_within_range=height_within_range,
            aspect_within_range=aspect_within_range,
            can_crop_without_padding=can_crop_without_padding,
            padding_required=padding_required,
            validation=validation_report,
            processing_duration_ms=duration,
            preview_image=None,
        )

    def _empty_failed_result(
        self,
        cfg: CropModeBConfig,
        start_time: float,
        issues: List[CropValidationIssue],
        issue_codes: List[CropIssueCode],
    ) -> CropModeBResult:
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
        return CropModeBResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            crop_mode=CropMode.HEAD_LED_RANGE,
            crop_box=BoundingBox(left=0.0, top=0.0, right=1.0, bottom=1.0),
            crop_box_width=1,
            crop_box_height=1,
            crop_box_aspect_ratio=1.0,
            ideal_crop_box=BoundingBox(left=0.0, top=0.0, right=1.0, bottom=1.0),
            ideal_crop_width=1,
            ideal_crop_height=1,
            ideal_crop_aspect_ratio=1.0,
            head_height_ratio=None,
            face_center_x_ratio=0.5,
            face_center_y_ratio=0.5,
            can_crop_without_padding=False,
            padding_required=False,
            validation=val,
            processing_duration_ms=duration,
        )
