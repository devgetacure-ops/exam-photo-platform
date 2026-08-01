"""BiRefNet-based subject matting provider (DEC-031).

Implements the same ``SubjectSegmentationProvider`` contract as
``MediapipeSubjectSegmenter`` so it is a drop-in replacement in the pipeline:
downstream code (mask refinement, portrait composition, crop planning,
background composition) is unaware which model produced the mask.

Design notes
------------
* Import is lazy: ``torch``/``transformers`` are only imported inside
  ``_ensure_initialized``, so this module -- and therefore the package -- stays
  importable without the optional ``matting`` extra installed, matching the
  pattern used by ``mediapipe_face_detector.py``.
* BiRefNet returns a single soft foreground probability map (no multiclass
  breakdown), so ``class_coverage`` is always ``None`` and
  ``SegmentationCapabilities.multiclass`` is ``False``.
* Inference runs at a fixed square resolution (default 512px -- see
  DEC-031's resolution sweep) regardless of source size, then the result is
  resized back with bilinear interpolation.  512 was measured to match 1024's
  edge-alignment quality while running roughly 7x faster on CPU.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Any, Optional

import numpy as np
from PIL import Image

from exam_photo.models.geometry import BoundingBox
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.model_errors import ModelChecksumError, ModelNotFoundError
from exam_photo.providers.segmenters.errors import SegmentationOutputError
from exam_photo.providers.subject_segmentation import (
    SegmentationCapabilities,
    SegmentationConfig,
    SegmentationStatusValue,
    SubjectSegmentationProvider,
    SubjectSegmentationResult,
)

try:
    import torch
    from transformers import AutoModelForImageSegmentation

    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False


_IMAGENET_MEAN = (0.485, 0.456, 0.406)
_IMAGENET_STD = (0.229, 0.224, 0.225)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class BiRefNetSubjectSegmenter(SubjectSegmentationProvider):
    """Subject segmentation provider backed by a local BiRefNet checkpoint."""

    def __init__(
        self,
        model_dir: Path,
        expected_sha256: str = "",
        weights_filename: str = "model.safetensors",
        inference_size: int = 512,
        allow_unverified_model: bool = False,
    ) -> None:
        """Initialise the segmenter against a vendored model directory.

        ``model_dir`` must contain the files produced by
        ``scripts/download_birefnet.py`` (model code, config, and
        ``weights_filename``).  Concurrent callers are serialised through one
        provider instance, matching ``MediapipeSubjectSegmenter``.
        """
        self.model_dir = Path(model_dir)
        self.expected_sha256 = expected_sha256
        self.weights_filename = weights_filename
        self.inference_size = inference_size
        self.allow_unverified_model = allow_unverified_model
        self.provider_name = "BiRefNetSubjectSegmenter"
        self.provider_version = "1.0.0"
        self._model: Optional[Any] = None
        self._model_verified = False
        self._lock = threading.RLock()

    def _ensure_initialized(self) -> None:
        if self._model is not None:
            return
        if not _TORCH_AVAILABLE:
            raise SegmentationOutputError(
                "BiRefNet requires the optional 'matting' extra "
                '(pip install -e ".[dev,matting]").'
            )

        weights_path = self.model_dir / self.weights_filename
        if not weights_path.exists():
            raise ModelNotFoundError(
                f"BiRefNet weights not found at '{weights_path}'. "
                "Run scripts/download_birefnet.py to acquire the model files."
            )

        if not self.allow_unverified_model:
            if not self.expected_sha256 or len(self.expected_sha256) != 64:
                raise ModelChecksumError(
                    "A valid 64-character SHA-256 checksum is required for "
                    f"verification: got '{self.expected_sha256}'"
                )
            actual = _sha256_file(weights_path)
            if actual != self.expected_sha256:
                raise ModelChecksumError(
                    "SHA-256 mismatch for BiRefNet weights:\n"
                    f"  Expected: {self.expected_sha256}\n"
                    f"  Got:      {actual}"
                )
        self._model_verified = True

        model = AutoModelForImageSegmentation.from_pretrained(
            str(self.model_dir), trust_remote_code=True
        )
        # Checkpoints ship in half precision; CPU conv kernels require float32.
        model.float()
        model.eval()
        torch.set_num_threads(max(1, (torch.get_num_threads())))
        self._model = model
        self._mean = torch.tensor(_IMAGENET_MEAN).view(1, 3, 1, 1)
        self._std = torch.tensor(_IMAGENET_STD).view(1, 3, 1, 1)

    def segment_subject(
        self,
        image: Image.Image,
        face: Optional[FaceDetection | list[FaceDetection]] = None,
        head_estimate: Optional[BoundingBox] = None,
        config: Optional[SegmentationConfig] = None,
    ) -> SubjectSegmentationResult:
        start_time = time.perf_counter()
        cfg = config or SegmentationConfig()

        with self._lock:
            self._ensure_initialized()
            assert self._model is not None

            img_rgb = image.convert("RGB")
            img_w, img_h = img_rgb.size

            t_inf_start = time.perf_counter()
            size = self.inference_size
            resized = img_rgb.resize((size, size), Image.Resampling.BILINEAR)
            arr = np.asarray(resized, dtype=np.float32) / 255.0
            tensor = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)
            tensor = (tensor - self._mean) / self._std

            with torch.no_grad():
                out = self._model(tensor)
            pred = out[-1] if isinstance(out, (list, tuple)) else out
            if isinstance(pred, (list, tuple)):
                pred = pred[-1]
            logits = pred.squeeze().cpu().numpy().astype(np.float32)
            inf_dur = (time.perf_counter() - t_inf_start) * 1000.0

            if logits.ndim != 2:
                raise SegmentationOutputError(
                    f"Unexpected BiRefNet output shape: {logits.shape}"
                )

            t_ext_start = time.perf_counter()
            probs = 1.0 / (1.0 + np.exp(-logits))
            probs = np.clip(probs, 0.0, 1.0).astype(np.float32)
            ext_dur = (time.perf_counter() - t_ext_start) * 1000.0

            t_res_start = time.perf_counter()
            if (size, size) != (img_w, img_h):
                prob_img = Image.fromarray(probs, mode="F")
                probability_mask = np.array(
                    prob_img.resize((img_w, img_h), Image.Resampling.BILINEAR),
                    dtype=np.float32,
                )
            else:
                probability_mask = probs

            binary_mask_arr = np.where(
                probability_mask >= cfg.foreground_threshold, 255, 0
            ).astype(np.uint8)
            coarse_mask = Image.fromarray(binary_mask_arr, mode="L")
            res_dur = (time.perf_counter() - t_res_start) * 1000.0

            t_val_start = time.perf_counter()
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
            val_dur = (time.perf_counter() - t_val_start) * 1000.0

            capabilities = SegmentationCapabilities(
                probability_masks=True,
                category_mask=False,
                multiclass=False,
                hair_class=False,
                face_skin_class=False,
                clothes_class=False,
                accessories_class=False,
                multiple_people_supported=False,
                instance_separation=False,
                cpu_execution=True,
                local_execution=True,
            )

            safe_metadata = {
                "model_variant": "birefnet",
                "inference_size": size,
                "image_width": img_w,
                "image_height": img_h,
                "total_pixels": img_w * img_h,
            }

            duration_ms = (time.perf_counter() - start_time) * 1000.0

            return SubjectSegmentationResult(
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                model_name="birefnet",
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
                inference_duration_ms=inf_dur,
                mask_extraction_duration_ms=ext_dur,
                resize_threshold_duration_ms=res_dur,
                validation_duration_ms=val_dur,
                safe_internal_metadata=safe_metadata,
                class_coverage=None,
                mask_validation=validation_report,
            )

    def close(self) -> None:
        with self._lock:
            self._model = None
            self._model_verified = False

    def __enter__(self) -> "BiRefNetSubjectSegmenter":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        # Keep the (expensive to load) model warm across calls, unlike the
        # MediaPipe segmenter which is cheap to reinitialise per call.  The
        # pipeline still calls this as a context manager for interface
        # parity; only an explicit close() releases the model.
        pass


def load_manifest_defaults(
    repo_root: Path,
) -> tuple[Path, str, str, int]:
    """Resolve (model_dir, weights_filename, expected_sha256, inference_size)
    from model-manifests/birefnet.json, matching the pattern used by the CLI
    for the face detector and MediaPipe segmenter manifests."""
    manifest_path = repo_root / "model-manifests" / "birefnet.json"
    with manifest_path.open(encoding="utf-8") as fh:
        manifest = json.load(fh)
    model_dir = repo_root / str(
        manifest.get("local_model_dir_default", "model-assets/birefnet")
    )
    return (
        model_dir,
        str(manifest["weights_filename"]),
        str(manifest["weights_sha256"]),
        int(manifest.get("inference_input_size", 512)),
    )
