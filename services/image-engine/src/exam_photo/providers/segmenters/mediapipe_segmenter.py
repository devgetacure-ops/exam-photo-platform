from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Optional

import numpy as np
from PIL import Image

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.subject_segmentation import (
    SegmentationCapabilities,
    SegmentationConfig,
    SegmentationStatusValue,
    SubjectSegmentationProvider,
    SubjectSegmentationResult,
)

try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import (
        vision as mp_vision,
    )

    _MEDIAPIPE_AVAILABLE = True
except ImportError:
    _MEDIAPIPE_AVAILABLE = False


class MediapipeSubjectSegmenter(SubjectSegmentationProvider):
    """Subject segmentation provider utilizing MediaPipe ImageSegmenter."""

    def __init__(self, model_path: Path, expected_sha256: str = "") -> None:
        self.model_path = model_path
        self.expected_sha256 = expected_sha256
        self.provider_name = "MediapipeSubjectSegmenter"
        self.provider_version = "1.0.0"
        self._segmenter: Optional[Any] = None
        self._model_verified = False

    def _verify_model(self) -> None:
        if self._model_verified:
            return

        if not self.model_path.exists():
            from exam_photo.providers.model_errors import ModelNotFoundError

            raise ModelNotFoundError(f"Model asset not found at {self.model_path}")

        if self.expected_sha256:
            import hashlib

            digest = hashlib.sha256()
            with self.model_path.open("rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    digest.update(chunk)
            actual_sha = digest.hexdigest()
            if actual_sha != self.expected_sha256:
                from exam_photo.providers.model_errors import ModelChecksumError

                raise ModelChecksumError(
                    f"SHA-256 mismatch for segmenter model:\n  Expected: {self.expected_sha256}\n  Got:      {actual_sha}"
                )

        self._model_verified = True

    def segment_subject(
        self,
        image: Image.Image,
        face: Optional[FaceDetection] = None,
        head_estimate: Optional[BoundingBox] = None,
        config: Optional[dict[str, Any]] = None,
    ) -> SubjectSegmentationResult:
        start_time = time.perf_counter()

        if not _MEDIAPIPE_AVAILABLE:
            raise RuntimeError(
                "mediapipe is not installed. Install with: pip install -e '.[face]'"
            )

        cfg = SegmentationConfig(**(config or {}))
        self._verify_model()

        if self._segmenter is None:
            base_options = mp_python.BaseOptions(model_asset_path=str(self.model_path))
            options = mp_vision.ImageSegmenterOptions(
                base_options=base_options,
                running_mode=mp_vision.RunningMode.IMAGE,
                output_confidence_masks=True,
                output_category_mask=False,
            )
            try:
                self._segmenter = mp_vision.ImageSegmenter.create_from_options(options)
            except Exception as e:
                raise ValueError(
                    f"Failed to initialize MediaPipe ImageSegmenter: {e}"
                ) from e

        # Convert PIL Image to mediapipe.Image
        img_arr = np.array(image.convert("RGB"))
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_arr)

        try:
            res = self._segmenter.segment(mp_image)
        except Exception as e:
            raise RuntimeError(f"MediaPipe segmentation inference failed: {e}") from e

        if not res.confidence_masks:
            raise ValueError("MediaPipe segmenter returned no confidence masks.")

        first_mask = res.confidence_masks[0].numpy_view()
        mask_h, mask_w = first_mask.shape
        num_masks = len(res.confidence_masks)

        if num_masks == 6:
            # SelfieMulticlass model
            bg_prob = res.confidence_masks[0].numpy_view()
            if bg_prob.shape != (mask_h, mask_w):
                raise ValueError("Confidence mask shape mismatch")
            # Verify and sum non-background probabilities or use 1.0 - background
            for i in range(1, 6):
                arr = res.confidence_masks[i].numpy_view()
                if arr.shape != (mask_h, mask_w):
                    raise ValueError(f"Confidence mask {i} shape mismatch")
            foreground_probability = 1.0 - bg_prob
            multiclass_flag = True
        elif num_masks in (1, 2):
            # Binary model
            if num_masks == 2:
                bg_prob = res.confidence_masks[0].numpy_view()
                fg_prob = res.confidence_masks[1].numpy_view()
                if bg_prob.shape != (mask_h, mask_w) or fg_prob.shape != (
                    mask_h,
                    mask_w,
                ):
                    raise ValueError("Confidence mask shape mismatch")
                foreground_probability = 1.0 - bg_prob
            else:
                foreground_probability = res.confidence_masks[0].numpy_view()
            multiclass_flag = False

        # Handle small floating point errors safely
        foreground_probability = np.clip(foreground_probability, 0.0, 1.0)

        # Resize probability mask if it differs from source dimensions
        img_w, img_h = image.size
        if (mask_w, mask_h) != (img_w, img_h):
            prob_img = Image.fromarray(foreground_probability, mode="F")
            prob_img_resized = prob_img.resize(
                (img_w, img_h), resample=Image.Resampling.BILINEAR
            )
            probability_mask = np.array(prob_img_resized, dtype=np.float32)
        else:
            probability_mask = foreground_probability

        # Apply coarse threshold AFTER resizing
        binary_mask_arr = np.where(
            probability_mask >= cfg.foreground_threshold, 255, 0
        ).astype(np.uint8)
        coarse_mask = Image.fromarray(binary_mask_arr, mode="L")

        # Run mask validation
        from exam_photo.providers.segmenters.mask_validation import (
            validate_segmentation_mask,
        )

        validation_report = validate_segmentation_mask(
            probability_mask=probability_mask,
            binary_mask=binary_mask_arr,
            config=cfg,
            face=face,
            head_estimate=head_estimate,
        )

        capabilities = SegmentationCapabilities(
            probability_masks=True,
            category_mask=False,
            multiclass=multiclass_flag,
            hair_class=multiclass_flag,
            face_skin_class=multiclass_flag,
            clothes_class=multiclass_flag,
            accessories_class=multiclass_flag,
            multiple_people_supported=True,
            instance_separation=False,
            cpu_execution=True,
            local_execution=True,
        )

        safe_metadata = {
            "model_variant": "selfie_multiclass_256x256"
            if num_masks == 6
            else "selfie_bin_general",
            "runtime_mask_width": mask_w,
            "runtime_mask_height": mask_h,
            "image_width": img_w,
            "image_height": img_h,
            "total_pixels": img_w * img_h,
        }

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        return SubjectSegmentationResult(
            provider_name=self.provider_name,
            provider_version=self.provider_version,
            model_name="selfie_multiclass" if num_masks == 6 else "selfie_binary",
            model_version="latest",
            capabilities=capabilities,
            provider_status=SegmentationStatusValue.SUCCESS,
            probability_mask=probability_mask,
            coarse_mask=coarse_mask,
            input_width=img_w,
            input_height=img_h,
            mask_width=img_w,
            mask_height=img_h,
            threshold_used=cfg.foreground_threshold,
            foreground_coverage_ratio=validation_report.foreground_coverage_ratio,
            warnings=[],
            processing_duration=duration_ms,
            safe_internal_metadata=safe_metadata,
            mask_validation=validation_report,
        )

    def close(self) -> None:
        if self._segmenter is not None:
            self._segmenter.close()
            self._segmenter = None

    def __enter__(self) -> MediapipeSubjectSegmenter:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
