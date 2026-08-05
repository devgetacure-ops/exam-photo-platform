"""Dense face landmark refinement for an already-detected face (DEC-032).

The crop planner needs two points precisely: the chin (it sets the bottom of
the head span and the chin/beard protection line) and the eye line (it is a
hard composition constraint).  BlazeFace supplies neither directly -- the chin
is approximated by the detector box bottom, and the eyes come from two coarse
keypoints that a subject's spectacles or sunglasses can displace.

Measured on the 60-photo reference set, the box-bottom chin proxy carries a
mean error of -0.045 face heights on primary detections (9 of 49 exceeding
0.10) and -0.143 on detections recovered at reduced confidence.  Every
downstream quantity -- head span, crown estimate, crop height -- inherits that
error, which is why recovered photos crop loose.

This provider does NOT replace face detection.  BlazeFace has better coverage
on raw candidate photos (58/60 versus this landmarker's 54/60), so detection
and face counting stay with the detector and this refines what it found.  It
also deliberately leaves ``bounding_box`` untouched: the head estimator's
expansion ratios are calibrated against BlazeFace box dimensions, so resizing
the box here would silently invalidate them.
"""

from __future__ import annotations

import hashlib
import math
import threading
from pathlib import Path
from typing import Any, Optional

import numpy as np
from PIL import Image

from exam_photo.models.geometry import Landmarks, Point, PoseEstimate
from exam_photo.providers.face_detection import FaceDetection
from exam_photo.providers.model_errors import ModelChecksumError, ModelNotFoundError

try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision as mp_vision

    _MEDIAPIPE_AVAILABLE = True
except ImportError:
    _MEDIAPIPE_AVAILABLE = False


# Canonical MediaPipe FaceMesh indices.
_IDX_CHIN = 152
_IDX_IRIS_RIGHT = 468
_IDX_IRIS_LEFT = 473
_IDX_EYE_RIGHT_OUTER = 33
_IDX_EYE_LEFT_OUTER = 263

# A refined chin further than this many face-box heights from the detector's
# own estimate is treated as a mismatch (the landmarker locking onto a
# different face) and discarded rather than trusted.
_MAX_CHIN_DEVIATION_FACE_HEIGHTS = 0.45

# Margin (as a multiple of the BlazeFace box's own width/height) expanded on
# each side before handing the region to the dense landmarker.  The
# landmarker task runs its own internal face detector tuned for a face that
# fills a reasonable fraction of the frame; on a full 1200x1800-class photo
# where the detected face is only ~15% of the frame height, that internal
# detector finds nothing at any confidence threshold (verified on photo 6-3:
# 0 faces from confidence 0.5 down to 0.01 on the full frame, 1 face
# immediately once cropped).  Cropping first also removes the two-tier
# chin-estimate fallback that was needed only because refinement so often
# failed outright -- with the crop, the dense chin lands correctly on
# reference photos where the face-box-bottom proxy overshot into the neck.
_CROP_MARGIN_RATIO = 1.5


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class MediapipeFaceLandmarker:
    """Refines the chin and eye line of a detected face using dense landmarks."""

    def __init__(
        self,
        model_path: Path,
        expected_sha256: str = "",
        allow_unverified_model: bool = False,
        min_confidence: float = 0.25,
    ) -> None:
        self.model_path = Path(model_path)
        self.expected_sha256 = expected_sha256
        self.allow_unverified_model = allow_unverified_model
        self.min_confidence = min_confidence
        self.provider_name = "MediapipeFaceLandmarker"
        self.provider_version = "1.0.0"
        self._landmarker: Optional[Any] = None
        self._lock = threading.RLock()

    def _ensure_initialized(self) -> None:
        if self._landmarker is not None:
            return
        if not _MEDIAPIPE_AVAILABLE:
            raise RuntimeError(
                "Face landmark refinement requires the 'face' extra "
                '(pip install -e ".[dev,face]").'
            )
        if not self.model_path.exists():
            raise ModelNotFoundError(
                f"Face landmarker asset not found at '{self.model_path}'. "
                "Run scripts/download_face_landmarker.py to acquire it."
            )
        if not self.allow_unverified_model:
            if not self.expected_sha256 or len(self.expected_sha256) != 64:
                raise ModelChecksumError(
                    "A valid 64-character SHA-256 checksum is required for "
                    f"verification: got '{self.expected_sha256}'"
                )
            actual = _sha256_file(self.model_path)
            if actual != self.expected_sha256:
                raise ModelChecksumError(
                    "SHA-256 mismatch for face landmarker asset:\n"
                    f"  Expected: {self.expected_sha256}\n"
                    f"  Got:      {actual}"
                )

        options = mp_vision.FaceLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=str(self.model_path)),
            num_faces=1,
            min_face_detection_confidence=self.min_confidence,
            min_face_presence_confidence=self.min_confidence,
            output_face_blendshapes=False,
            # Head pose feeds the frontal-pose warning (DEC-041).  Blend shapes
            # stay off: measured over the 40-photo adversarial set, the
            # eye-blink score does not separate sunglasses or closed eyes from
            # narrow or deep-set eyes, so nothing consumes it and it would only
            # cost time.
            output_facial_transformation_matrixes=True,
        )
        self._landmarker = mp_vision.FaceLandmarker.create_from_options(options)

    def refine(self, image: Image.Image, face: FaceDetection) -> FaceDetection:
        """Return ``face`` with a precise chin and eye line where possible.

        Returns the input unchanged when the landmarker finds nothing or its
        reading disagrees with the detector badly enough to suggest it locked
        onto a different face.  Refinement is an improvement, never a
        precondition, so callers do not need to handle a failure case.
        """
        full_rgb = np.asarray(image.convert("RGB"))
        img_height, img_width = full_rgb.shape[:2]
        face_box = face.bounding_box

        crop_x0 = max(0, int(face_box.left - _CROP_MARGIN_RATIO * face_box.width))
        crop_y0 = max(0, int(face_box.top - _CROP_MARGIN_RATIO * face_box.height))
        crop_x1 = min(
            img_width, int(face_box.right + _CROP_MARGIN_RATIO * face_box.width)
        )
        crop_y1 = min(
            img_height, int(face_box.bottom + _CROP_MARGIN_RATIO * face_box.height)
        )
        if crop_x1 <= crop_x0 or crop_y1 <= crop_y0:
            return face

        rgb = np.ascontiguousarray(full_rgb[crop_y0:crop_y1, crop_x0:crop_x1])
        crop_height, crop_width = rgb.shape[:2]

        with self._lock:
            self._ensure_initialized()
            assert self._landmarker is not None

            result = self._landmarker.detect(
                mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            )

        # Whether a dense face was found at all is reported separately from
        # whether its reading was accepted.  Downstream suitability treats "the
        # landmarker could not read this face" as evidence of an extreme pose
        # or a covered face (DEC-041), and that inference is only valid for a
        # genuine detection failure -- not for a face that was read fine but
        # whose chin was rejected as implausible below.
        def tagged(found: bool) -> FaceDetection:
            metadata = dict(face.provider_metadata or {})
            metadata["dense_landmarks_found"] = found
            return face.model_copy(update={"provider_metadata": metadata})

        if not result.face_landmarks:
            return tagged(False)

        marks = result.face_landmarks[0]
        if len(marks) <= _IDX_CHIN:
            return tagged(False)

        def to_point(index: int) -> Point:
            lm = marks[index]
            return Point(
                x=float(lm.x * crop_width + crop_x0),
                y=float(lm.y * crop_height + crop_y0),
            )

        chin = to_point(_IDX_CHIN)
        face_box = face.bounding_box
        deviation = abs(chin.y - face_box.bottom) / max(1.0, face_box.height)
        if deviation > _MAX_CHIN_DEVIATION_FACE_HEIGHTS:
            return tagged(True)

        if len(marks) > _IDX_IRIS_LEFT:
            left_eye = to_point(_IDX_IRIS_LEFT)
            right_eye = to_point(_IDX_IRIS_RIGHT)
        else:
            left_eye = to_point(_IDX_EYE_LEFT_OUTER)
            right_eye = to_point(_IDX_EYE_RIGHT_OUTER)

        existing = face.landmarks
        custom = dict(existing.custom_landmarks) if existing else {}
        custom["refined_chin"] = chin
        custom["refined_left_iris"] = left_eye
        custom["refined_right_iris"] = right_eye

        refined = Landmarks(
            left_eye=left_eye,
            right_eye=right_eye,
            nose_tip=existing.nose_tip if existing else None,
            mouth_left=existing.mouth_left if existing else None,
            mouth_right=existing.mouth_right if existing else None,
            chin=chin,
            custom_landmarks=custom,
        )

        metadata = dict(face.provider_metadata or {})
        metadata["dense_landmarks_found"] = True
        update: dict[str, Any] = {
            "landmarks": refined,
            "provider_metadata": metadata,
        }
        pose = self._pose_from_result(result)
        if pose is not None:
            update["pose"] = pose
        return face.model_copy(update=update)

    @staticmethod
    def _pose_from_result(result: Any) -> Optional[PoseEstimate]:
        """Extract head yaw/pitch/roll from the landmarker's transform matrix.

        The matrix maps the canonical face model into the camera frame, so its
        rotation submatrix is the head pose.  Returned in degrees with the
        usual convention: yaw positive turning to the subject's left, pitch
        positive looking up, roll positive tilting clockwise in the image.
        """
        matrices = getattr(result, "facial_transformation_matrixes", None)
        if not matrices:
            return None
        rotation = np.asarray(matrices[0], dtype=np.float64)[:3, :3]
        # Guard against a degenerate matrix rather than emitting a NaN pose.
        cos_pitch = math.sqrt(rotation[0, 0] ** 2 + rotation[1, 0] ** 2)
        if not math.isfinite(cos_pitch):
            return None
        if cos_pitch > 1e-6:
            pitch = math.degrees(math.atan2(rotation[2, 1], rotation[2, 2]))
            yaw = math.degrees(math.atan2(-rotation[2, 0], cos_pitch))
            roll = math.degrees(math.atan2(rotation[1, 0], rotation[0, 0]))
        else:
            # Gimbal lock: roll is not separable from yaw, so report it as zero
            # rather than inventing a value.
            pitch = math.degrees(math.atan2(-rotation[1, 2], rotation[1, 1]))
            yaw = math.degrees(math.atan2(-rotation[2, 0], cos_pitch))
            roll = 0.0
        if not all(math.isfinite(v) for v in (yaw, pitch, roll)):
            return None
        return PoseEstimate(
            yaw=yaw,
            pitch=pitch,
            roll=roll,
            confidence=1.0,
            method="mediapipe_face_landmarker_transform_matrix",
        )

    def close(self) -> None:
        with self._lock:
            if self._landmarker is not None:
                self._landmarker.close()
                self._landmarker = None

    def __enter__(self) -> "MediapipeFaceLandmarker":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


def load_manifest_defaults(repo_root: Path) -> tuple[Path, str]:
    """Resolve (model_path, expected_sha256) from model-manifests/face-landmarker.json."""
    import json

    manifest_path = repo_root / "model-manifests" / "face-landmarker.json"
    with manifest_path.open(encoding="utf-8") as fh:
        manifest = json.load(fh)
    model_path = repo_root / str(
        manifest.get("local_model_path_default", "model-assets/face_landmarker.task")
    )
    return model_path, str(manifest["sha256"])
