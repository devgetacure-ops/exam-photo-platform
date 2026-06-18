from typing import List, Optional

import numpy as np
from PIL import Image

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.subject_segmentation import (
    MaskValidationReport,
    SegmentationCapabilities,
    SegmentationConfig,
    SegmentationStatusValue,
    SegmentationValidationIssue,
    SubjectSegmentationProvider,
    SubjectSegmentationResult,
)


class FakeSubjectSegmenter(SubjectSegmentationProvider):
    def __init__(
        self,
        is_valid: bool = True,
        foreground_coverage_ratio: float = 0.5,
        connected_components_count: int = 1,
        issue_codes: Optional[List[str]] = None,
        raise_error: Optional[Exception] = None,
    ) -> None:
        self.is_valid = is_valid
        self.foreground_coverage_ratio = foreground_coverage_ratio
        self.connected_components_count = connected_components_count
        self.issue_codes = issue_codes or []
        self.raise_error = raise_error

    def segment_subject(
        self,
        image: Image.Image,
        face: Optional[FaceDetection] = None,
        head_estimate: Optional[BoundingBox] = None,
        config: Optional[SegmentationConfig] = None,
    ) -> SubjectSegmentationResult:
        if self.raise_error is not None:
            raise self.raise_error

        w, h = image.size
        prob_mask = np.zeros((h, w), dtype=np.float32)
        num_pixels = int(w * h * self.foreground_coverage_ratio)
        prob_mask.flat[:num_pixels] = 1.0

        binary_mask_arr = np.where(prob_mask >= 0.5, 255, 0).astype(np.uint8)
        coarse_mask = Image.fromarray(binary_mask_arr, mode="L")

        from exam_photo.suitability.issue_codes import (
            IssueSeverity,
            SuitabilityIssueCode,
        )

        issues_list = []
        clean_codes = []
        for code in self.issue_codes:
            # Map code to SuitabilityIssueCode
            if isinstance(code, str):
                issue_code = SuitabilityIssueCode(code)
            else:
                issue_code = code
            clean_codes.append(issue_code.value)

            is_error = issue_code in (
                SuitabilityIssueCode.SEGMENTATION_MASK_EMPTY,
                SuitabilityIssueCode.SEGMENTATION_MASK_FULL_FRAME,
                SuitabilityIssueCode.SEGMENTATION_FACE_NOT_CONTAINED,
                SuitabilityIssueCode.SEGMENTATION_FOREGROUND_COVERAGE_LOW,
                SuitabilityIssueCode.SEGMENTATION_FOREGROUND_COVERAGE_HIGH,
            )
            issues_list.append(
                SegmentationValidationIssue(
                    code=issue_code,
                    severity=IssueSeverity.ERROR if is_error else IssueSeverity.WARNING,
                    blocking_for_processing=is_error,
                )
            )

        val_report = MaskValidationReport(
            is_valid=self.is_valid,
            foreground_coverage_ratio=self.foreground_coverage_ratio,
            uncertain_pixel_ratio=0.05,
            connected_components_count=self.connected_components_count,
            largest_component_ratio=1.0,
            image_edge_contact=False,
            face_contained=True if face is not None else None,
            head_region_coverage_ratio=1.0 if head_estimate is not None else None,
            issue_codes=clean_codes,
            issues=issues_list,
        )

        caps = SegmentationCapabilities(
            probability_masks=True,
            category_mask=False,
            multiclass=True,
            hair_class=True,
            face_skin_class=True,
            clothes_class=True,
            accessories_class=True,
            multiple_people_supported=True,
            instance_separation=False,
            cpu_execution=True,
            local_execution=True,
        )

        return SubjectSegmentationResult(
            provider_name="FakeSubjectSegmenter",
            provider_version="0.0.1-fake",
            model_name="fake_model",
            model_version="1.0-fake",
            capabilities=caps,
            provider_status=SegmentationStatusValue.SUCCESS,
            probability_mask=prob_mask,
            coarse_mask=coarse_mask,
            input_width=w,
            input_height=h,
            mask_width=w,
            mask_height=h,
            threshold_used=0.5,
            foreground_coverage_ratio=self.foreground_coverage_ratio,
            warnings=[],
            processing_duration=0.1,
            mask_validation=val_report,
        )
