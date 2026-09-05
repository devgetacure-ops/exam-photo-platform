"""ONNX-backed BiRefNet subject matting provider (faster-matting Step 1).

Same weights, same maths as ``birefnet_segmenter.py``: the ONNX graph loaded
here is a direct export of the vendored PyTorch checkpoint
(``scripts/export_birefnet_onnx.py``), verified numerically equivalent to the
original to float tolerance before that export is trusted (see
``model-manifests/birefnet_onnx.json``). No quantisation, no architecture
change -- the only difference is the runtime that executes the graph.

Implements the same ``SubjectSegmentationProvider`` contract as
``BiRefNetSubjectSegmenter`` so it is a drop-in replacement in the pipeline,
selected via ``matting_backend="birefnet_onnx"``.

Design notes
------------
* onnxruntime is the only runtime dependency -- no torch, no transformers.
  That is the point: a deployment that only ever runs this backend does not
  need the ~2 GB ``matting`` extra, only ``onnxruntime``.
* Preprocessing (resize, ImageNet normalisation) and postprocessing (sigmoid,
  threshold, mask validation) are identical to
  ``BiRefNetSubjectSegmenter.segment_subject`` by construction -- both share
  the same fixed 512px square inference resolution and the same ImageNet
  mean/std, so the only place the two backends can diverge is the model
  graph itself, which is what the export's equivalence check guards.
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
    import onnxruntime as ort

    _ORT_AVAILABLE = True
except ImportError:
    _ORT_AVAILABLE = False


_IMAGENET_MEAN = (0.485, 0.456, 0.406)
_IMAGENET_STD = (0.229, 0.224, 0.225)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class BiRefNetONNXSubjectSegmenter(SubjectSegmentationProvider):
    """Subject segmentation provider backed by the ONNX export of BiRefNet."""

    def __init__(
        self,
        model_dir: Path,
        expected_sha256: str = "",
        weights_filename: str = "model.onnx",
        inference_size: int = 512,
        allow_unverified_model: bool = False,
    ) -> None:
        """Initialise the segmenter against a vendored ONNX model directory.

        ``model_dir`` must contain ``weights_filename`` as produced by
        ``scripts/export_birefnet_onnx.py``. Concurrent callers are
        serialised through one provider instance, matching
        ``BiRefNetSubjectSegmenter``.
        """
        self.model_dir = Path(model_dir)
        self.expected_sha256 = expected_sha256
        self.weights_filename = weights_filename
        self.inference_size = inference_size
        self.allow_unverified_model = allow_unverified_model
        self.provider_name = "BiRefNetONNXSubjectSegmenter"
        self.provider_version = "1.0.0"
        self._session: Optional[Any] = None
        self._model_verified = False
        self._lock = threading.RLock()

    def _ensure_initialized(self) -> None:
        if self._session is not None:
            return
        if not _ORT_AVAILABLE:
            raise SegmentationOutputError(
                "The 'birefnet_onnx' backend requires the optional "
                "'matting-onnx' extra (pip install -e \".[dev,matting-onnx]\")."
            )

        weights_path = self.model_dir / self.weights_filename
        if not weights_path.exists():
            raise ModelNotFoundError(
                f"BiRefNet ONNX weights not found at '{weights_path}'. "
                "Run scripts/export_birefnet_onnx.py to produce the model file."
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
                    "SHA-256 mismatch for BiRefNet ONNX weights:\n"
                    f"  Expected: {self.expected_sha256}\n"
                    f"  Got:      {actual}"
                )
        self._model_verified = True

        # onnxruntime's defaults are not the fastest configuration for this
        # graph on a desktop CPU. Measured on an 8-logical-core machine,
        # best-of-3 on a 1x3x512x512 input:
        #
        #     default                          6.03s
        #     intra_op=4,  parallel            5.59s
        #     intra_op=8,  parallel            5.89s
        #     intra_op=8,  SEQUENTIAL          4.78s   <- chosen
        #
        # Sequential execution wins because BiRefNet's graph is a deep chain
        # with little to run in parallel at the node level, so the inter-op
        # thread pool costs more in scheduling than it recovers. Threads are
        # left to onnxruntime's own count rather than pinned, since a fixed
        # number would be wrong on a machine with a different core count --
        # and a deployment box is not this one.
        options = ort.SessionOptions()
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self._session = ort.InferenceSession(
            str(weights_path),
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )

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
            assert self._session is not None

            img_rgb = image.convert("RGB")
            img_w, img_h = img_rgb.size

            t_inf_start = time.perf_counter()
            size = self.inference_size
            resized = img_rgb.resize((size, size), Image.Resampling.BILINEAR)
            arr = np.asarray(resized, dtype=np.float32) / 255.0
            arr = arr.transpose(2, 0, 1)[np.newaxis, ...]
            mean = np.array(_IMAGENET_MEAN, dtype=np.float32).reshape(1, 3, 1, 1)
            std = np.array(_IMAGENET_STD, dtype=np.float32).reshape(1, 3, 1, 1)
            tensor = ((arr - mean) / std).astype(np.float32)

            (logits,) = self._session.run(["logits"], {"pixel_values": tensor})
            logits = logits.squeeze().astype(np.float32)
            inf_dur = (time.perf_counter() - t_inf_start) * 1000.0

            if logits.ndim != 2:
                raise SegmentationOutputError(
                    f"Unexpected BiRefNet ONNX output shape: {logits.shape}"
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
                "model_variant": "birefnet_onnx",
                "inference_size": size,
                "image_width": img_w,
                "image_height": img_h,
                "total_pixels": img_w * img_h,
            }

            duration_ms = (time.perf_counter() - start_time) * 1000.0

            return SubjectSegmentationResult(
                provider_name=self.provider_name,
                provider_version=self.provider_version,
                model_name="birefnet_onnx",
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
            self._session = None
            self._model_verified = False

    def __enter__(self) -> "BiRefNetONNXSubjectSegmenter":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        # Keep the session warm across calls, matching
        # BiRefNetSubjectSegmenter; only an explicit close() releases it.
        pass


def load_manifest_defaults(
    repo_root: Path,
) -> tuple[Path, str, str, int]:
    """Resolve (model_dir, weights_filename, expected_sha256, inference_size)
    from model-manifests/birefnet_onnx.json, matching the pattern used for
    the PyTorch BiRefNet and MediaPipe segmenter manifests."""
    manifest_path = repo_root / "model-manifests" / "birefnet_onnx.json"
    with manifest_path.open(encoding="utf-8") as fh:
        manifest = json.load(fh)
    model_dir = repo_root / str(
        manifest.get("local_model_dir_default", "model-assets/birefnet_onnx")
    )
    return (
        model_dir,
        str(manifest["onnx_filename"]),
        str(manifest["onnx_sha256"]),
        int(manifest.get("inference_input_size", 512)),
    )
