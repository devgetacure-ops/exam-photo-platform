"""MediaPipe BlazeFace implementation of the FaceDetectionProvider protocol.

Design decisions
----------------
* Lazy initialisation: the ``mediapipe.tasks.vision.FaceDetector`` is created on
  the first ``detect_faces()`` call, not at import time.  This keeps the module
  importable even without the model asset present.
* Threading: Inference calls are serialized through a lock to prevent concurrent access to the shared detector instance.
* Model verification: SHA-256 of the model file is checked at every
  ``_ensure_initialized()`` call (before the detector is constructed, not at
  import time).
* Coordinate handling:
  - Bounding box: MediaPipe returns pixel-space ``origin_x, origin_y, width,
    height``.  These are validated, clamped, and converted to the canonical
    ``BoundingBox(left, top, right, bottom)`` model.
  - Keypoints: MediaPipe returns six normalised keypoints in [0, 1].  They are
    converted to absolute-pixel ``Point`` values by multiplying by the image
    dimensions and clamping.  Named fields that map to ``Landmarks`` named
    attributes are written directly; remaining keypoints go to
    ``custom_landmarks``.
* Resource lifecycle: ``close()`` releases the underlying detector.
  Context-manager protocol (``__enter__`` / ``__exit__``) is also supported.
"""

from __future__ import annotations

import hashlib
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image

from exam_photo.models.geometry import BoundingBox, Landmarks, Point
from exam_photo.providers.capabilities import ProviderCapabilities
from exam_photo.providers.face_detection import (
    FaceDetection,
    FaceDetectionResult,
)
from exam_photo.providers.model_errors import ModelChecksumError, ModelNotFoundError

# MediaPipe is an optional dependency (pip install -e ".[face]").
# Import is deferred to initialisation time so the module remains importable
# without mediapipe installed.
try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import (
        vision as mp_vision,
    )

    _MEDIAPIPE_AVAILABLE = True
except ImportError:  # pragma: no cover
    _MEDIAPIPE_AVAILABLE = False

_PROVIDER_NAME = "MediapipeFaceDetector"
_PROVIDER_VERSION = "1.0.0"

_CAPABILITIES = ProviderCapabilities(
    multiple_face_detection=True,
    landmarks=True,  # Six BlazeFace keypoints
    pose=False,  # FaceDetector task does not return pose angles
    eye_visibility=False,
    occlusion=False,  # No occlusion estimation
    head_bounds=False,
    hair_boundary_estimation=False,
    ear_visibility=False,
    chin_visibility=False,
    beard_boundary_visibility=False,
    confidence_values=True,
    cpu_execution=True,
    deterministic_execution=True,
)

# Maps MediaPipe BlazeFace keypoint index → Landmarks field name.
# Only indices with a direct Landmarks field are listed; the rest go to
# custom_landmarks.
_KEYPOINT_INDEX_TO_FIELD: Dict[int, str] = {
    0: "left_eye",
    1: "right_eye",
    2: "nose_tip",
    # index 3 = mouth_center (no direct field → custom_landmarks)
    # index 4 = left_ear_tragion (→ custom_landmarks)
    # index 5 = right_ear_tragion (→ custom_landmarks)
}

_KEYPOINT_INDEX_TO_CUSTOM: Dict[int, str] = {
    3: "mouth_center",
    4: "left_ear_tragion",
    5: "right_ear_tragion",
}


def _sha256_file(path: Path) -> str:
    """Return the lowercase hex SHA-256 digest of *path*."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


class MediapipeFaceDetector:
    """CPU face-detection provider backed by MediaPipe BlazeFace.

    Parameters
    ----------
    model_path:
        Path to the ``.task`` model asset file.  The file must be acquired
        manually using ``scripts/download_model.py`` before running inference.
    expected_sha256:
        Lowercase hex SHA-256 digest recorded in
        ``model-manifests/face-detector.json``.  Checked before the detector is
        initialised.  Pass an empty string only in tests that verify missing-file
        behaviour; do not disable in production.
    min_detection_confidence:
        Detections with confidence below this value are discarded.
        Defaults to ``0.5``.
    """

    def __init__(
        self,
        model_path: Path,
        expected_sha256: str,
        min_detection_confidence: float = 0.5,
    ) -> None:
        self._model_path = Path(model_path)
        self._expected_sha256 = expected_sha256.lower().strip()
        self._min_detection_confidence = min_detection_confidence
        self._detector: Optional[Any] = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Protocol interface
    # ------------------------------------------------------------------

    def detect_faces(
        self,
        image: Image.Image,
        config: Optional[Dict[str, Any]] = None,
    ) -> FaceDetectionResult:
        """Run face detection on a normalised PIL image.

        Parameters
        ----------
        image:
            Normalised PIL Image.  Internally converted to RGB uint8 for
            MediaPipe.
        config:
            Reserved for future per-call overrides; currently unused.

        Returns
        -------
        FaceDetectionResult
            Contains zero or more ``FaceDetection`` objects.  Detections whose
            confidence is below ``min_detection_confidence`` are excluded.
        """
        start = time.perf_counter()

        with self._lock:
            self._ensure_initialized()
            assert self._detector is not None  # narrow Optional for mypy

            img_w, img_h = image.size
            mp_image = self._to_mediapipe_image(image)
            mp_result = self._detector.detect(mp_image)

        detections: List[FaceDetection] = []
        warnings: List[str] = []

        for raw in mp_result.detections:
            score = float(raw.categories[0].score) if raw.categories else 0.0
            if score < self._min_detection_confidence:
                warnings.append(
                    f"Detection discarded: confidence {score:.3f} below "
                    f"threshold {self._min_detection_confidence}."
                )
                continue

            bbox = self._convert_bounding_box(raw.bounding_box, img_w, img_h, warnings)
            if bbox is None:
                continue

            landmarks = self._convert_keypoints(raw.keypoints, img_w, img_h)

            detections.append(
                FaceDetection(
                    bounding_box=bbox,
                    confidence=score,
                    landmarks=landmarks,
                    pose=None,
                    occlusion_indicators=None,
                    quality_indicators=None,
                    provider_metadata={"mediapipe_score": score},
                )
            )

        duration_ms = (time.perf_counter() - start) * 1000.0
        return FaceDetectionResult(
            provider_name=_PROVIDER_NAME,
            provider_version=_PROVIDER_VERSION,
            capabilities=_CAPABILITIES,
            detections=detections,
            warnings=warnings,
            duration_ms=duration_ms,
        )

    # ------------------------------------------------------------------
    # Resource lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Release the underlying MediaPipe detector and free its resources."""
        with self._lock:
            if self._detector is not None:
                try:
                    self._detector.close()
                except Exception:  # noqa: BLE001
                    pass
                self._detector = None

    def __enter__(self) -> "MediapipeFaceDetector":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_initialized(self) -> None:
        """Initialise the detector on first use.  Must be called under lock."""
        if self._detector is not None:
            return

        if not _MEDIAPIPE_AVAILABLE:
            raise ImportError(
                'mediapipe is not installed. Run: pip install -e ".[face]"'
            )

        self._verify_model()

        base_options = mp_python.BaseOptions(model_asset_path=str(self._model_path))
        options = mp_vision.FaceDetectorOptions(
            base_options=base_options,
            min_detection_confidence=self._min_detection_confidence,
        )
        self._detector = mp_vision.FaceDetector.create_from_options(options)

    def _verify_model(self) -> None:
        """Check that the model file exists and its SHA-256 matches."""
        if not self._model_path.exists():
            raise ModelNotFoundError(
                f"Model asset not found at '{self._model_path}'. "
                "Run scripts/download_model.py to acquire the model file."
            )
        if self._expected_sha256:
            actual = _sha256_file(self._model_path)
            if actual != self._expected_sha256:
                raise ModelChecksumError(
                    f"SHA-256 mismatch for '{self._model_path}'.\n"
                    f"  Expected: {self._expected_sha256}\n"
                    f"  Got:      {actual}\n"
                    "Delete the file and re-run scripts/download_model.py."
                )

    @staticmethod
    def _to_mediapipe_image(image: Image.Image) -> Any:
        """Convert a PIL Image to a MediaPipe Image object (RGB uint8)."""
        rgb = image.convert("RGB")
        import numpy as np  # local import; numpy is a mediapipe transitive dep

        return mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=np.asarray(rgb, dtype=np.uint8),
        )

    @staticmethod
    def _convert_bounding_box(
        raw_box: Any,
        img_w: int,
        img_h: int,
        warnings: List[str],
    ) -> Optional[BoundingBox]:
        """Convert a MediaPipe pixel-space bounding box to ``BoundingBox``.

        MediaPipe ``BoundingBox`` uses pixel-space ``origin_x, origin_y, width,
        height`` (not normalised).  Coordinates are clamped to image bounds.
        Detections with zero or negative area after clamping are discarded.
        """
        left = max(0, int(raw_box.origin_x))
        top = max(0, int(raw_box.origin_y))
        right = min(img_w, int(raw_box.origin_x + raw_box.width))
        bottom = min(img_h, int(raw_box.origin_y + raw_box.height))

        if right <= left or bottom <= top:
            warnings.append(
                f"Discarding detection: degenerate bounding box after clamping "
                f"({left},{top})-({right},{bottom}) for image {img_w}x{img_h}."
            )
            return None

        return BoundingBox(left=left, top=top, right=right, bottom=bottom)

    @staticmethod
    def _convert_keypoints(
        keypoints: Any,
        img_w: int,
        img_h: int,
    ) -> Optional[Landmarks]:
        """Convert MediaPipe normalised keypoints to absolute-pixel ``Landmarks``.

        BlazeFace returns six keypoints as normalised [0, 1] floats.  They are
        multiplied by image dimensions and clamped to produce absolute pixels.
        Named Landmarks fields (left_eye, right_eye, nose_tip) are populated
        directly; remaining keypoints go to ``custom_landmarks``.
        """
        if not keypoints:
            return None

        named: Dict[str, Optional[Point]] = {
            "left_eye": None,
            "right_eye": None,
            "nose_tip": None,
        }
        custom: Dict[str, Point] = {}

        for idx, kp in enumerate(keypoints):
            px = max(0, min(img_w, int(round(kp.x * img_w))))
            py = max(0, min(img_h, int(round(kp.y * img_h))))
            pt = Point(x=float(px), y=float(py))

            if idx in _KEYPOINT_INDEX_TO_FIELD:
                named[_KEYPOINT_INDEX_TO_FIELD[idx]] = pt
            elif idx in _KEYPOINT_INDEX_TO_CUSTOM:
                custom[_KEYPOINT_INDEX_TO_CUSTOM[idx]] = pt

        return Landmarks(
            left_eye=named.get("left_eye"),
            right_eye=named.get("right_eye"),
            nose_tip=named.get("nose_tip"),
            custom_landmarks=custom,
        )
