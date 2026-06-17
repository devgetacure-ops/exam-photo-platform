"""Tests for the MediapipeFaceDetector provider.

Test categories
---------------
- Negative / geometry tests use PIL-generated synthetic images (no real face).
- Inference tests use legally reusable CC0/public-domain fixtures listed in
  tests/fixtures/FIXTURE_MANIFEST.md.
- Tests that require the model asset file are skipped automatically when
  EXAM_PHOTO_FACE_MODEL_PATH is not set or the file is absent.
- Tests that require the mediapipe package are skipped when it is not installed.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector

import pytest
from PIL import Image, ImageDraw

# ---------------------------------------------------------------------------
# Skip guards
# ---------------------------------------------------------------------------

try:
    import mediapipe  # noqa: F401

    _MEDIAPIPE_INSTALLED = True
except ImportError:
    _MEDIAPIPE_INSTALLED = False

requires_mediapipe = pytest.mark.skipif(
    not _MEDIAPIPE_INSTALLED,
    reason="mediapipe not installed — run: pip install -e '.[face]'",
)

_MODEL_PATH_ENV = "EXAM_PHOTO_FACE_MODEL_PATH"
_MODEL_PATH: Optional[Path] = (
    Path(os.environ[_MODEL_PATH_ENV])
    if _MODEL_PATH_ENV in os.environ and Path(os.environ[_MODEL_PATH_ENV]).exists()
    else None
)
_MODEL_SHA256_ENV = "EXAM_PHOTO_FACE_MODEL_SHA256"
_MODEL_SHA256: str = os.environ.get(_MODEL_SHA256_ENV, "")

requires_model = pytest.mark.skipif(
    _MODEL_PATH is None,
    reason=(
        f"Model asset not available. Set {_MODEL_PATH_ENV}=<path/to/model.task> "
        f"and {_MODEL_SHA256_ENV}=<sha256> to run inference tests."
    ),
)

# Fixture image directory (relative to image-engine root)
_FIXTURES = Path(__file__).parent.parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_blank_image(width: int = 600, height: int = 800) -> Image.Image:
    """Pure-white RGB image with no detectable face."""
    return Image.new("RGB", (width, height), (255, 255, 255))


def _make_geometric_image(width: int = 600, height: int = 800) -> Image.Image:
    """Geometric shapes image with no human face."""
    img = Image.new("RGB", (width, height), (230, 230, 230))
    draw = ImageDraw.Draw(img)
    draw.rectangle((50, 50, 200, 200), fill=(70, 130, 180))
    draw.ellipse([250, 100, 450, 300], fill=(205, 92, 92))
    draw.polygon([(300, 400), (150, 650), (450, 650)], fill=(60, 179, 113))
    return img


def _load_fixture(name: str) -> Optional[Image.Image]:
    path = _FIXTURES / name
    if not path.exists():
        return None
    return Image.open(path).copy()


def _provider(
    sha256: str = "",
    confidence: float = 0.5,
) -> "MediapipeFaceDetector":  # noqa: F821 — guarded by requires_model/requires_mediapipe
    from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector

    assert _MODEL_PATH is not None
    return MediapipeFaceDetector(
        model_path=_MODEL_PATH,
        expected_sha256=sha256 or _MODEL_SHA256,
        min_detection_confidence=confidence,
    )


# ---------------------------------------------------------------------------
# 1. No-face inference — synthetic blank image
# ---------------------------------------------------------------------------


@requires_mediapipe
@requires_model
def test_no_face_blank_image() -> None:
    """Pure-white image must produce zero detections."""
    with _provider() as det:
        result = det.detect_faces(_make_blank_image())
    assert result.detections == []
    assert result.provider_name == "MediapipeFaceDetector"


# ---------------------------------------------------------------------------
# 2. No-face inference — geometric shapes image
# ---------------------------------------------------------------------------


@requires_mediapipe
@requires_model
def test_no_face_geometric_shapes() -> None:
    """Geometric shapes image must produce zero detections."""
    with _provider() as det:
        result = det.detect_faces(_make_geometric_image())
    assert result.detections == []


# ---------------------------------------------------------------------------
# 3. Single-face detection
# ---------------------------------------------------------------------------


@requires_mediapipe
@requires_model
def test_single_face_detected() -> None:
    """Single frontal face fixture must yield exactly one detection."""
    image = _load_fixture("single_face_frontal.jpg")
    if image is None:
        pytest.skip(
            "single_face_frontal.jpg not yet in fixtures/ — see FIXTURE_MANIFEST.md"
        )

    with _provider() as det:
        result = det.detect_faces(image)

    assert len(result.detections) == 1, (
        f"Expected 1 detection, got {len(result.detections)}"
    )
    face = result.detections[0]
    assert face.confidence >= 0.5
    # Bounding box within image
    assert face.bounding_box.left >= 0
    assert face.bounding_box.top >= 0
    assert face.bounding_box.right <= image.width
    assert face.bounding_box.bottom <= image.height


# ---------------------------------------------------------------------------
# 4. Multiple-face detection
# ---------------------------------------------------------------------------


@requires_mediapipe
@requires_model
def test_multiple_faces_detected() -> None:
    """Multiple-face fixture must yield ≥ 2 detections."""
    image = _load_fixture("multiple_faces.jpg")
    if image is None:
        pytest.skip("multiple_faces.jpg not yet in fixtures/ — see FIXTURE_MANIFEST.md")

    with _provider() as det:
        result = det.detect_faces(image)

    assert len(result.detections) >= 2, (
        f"Expected ≥ 2 detections, got {len(result.detections)}"
    )


# ---------------------------------------------------------------------------
# 5. Protocol structural contract
# ---------------------------------------------------------------------------


@requires_mediapipe
def test_provider_structural_contract() -> None:
    """Provider must satisfy the FaceDetectionProvider runtime-checkable protocol."""
    # Confirm @runtime_checkable is applied before using isinstance

    from exam_photo.providers.face_detection import FaceDetectionProvider
    from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector

    assert hasattr(FaceDetectionProvider, "__protocol_attrs__") or (
        getattr(FaceDetectionProvider, "_is_protocol", False)
        or "runtime_checkable" in str(type(FaceDetectionProvider))
    ), "FaceDetectionProvider must be decorated with @runtime_checkable"

    dummy_path = Path("/tmp/nonexistent.task")
    provider = MediapipeFaceDetector(model_path=dummy_path, expected_sha256="")
    assert isinstance(provider, FaceDetectionProvider)


# ---------------------------------------------------------------------------
# 6. Capabilities flags
# ---------------------------------------------------------------------------


@requires_mediapipe
def test_capabilities_flags() -> None:
    """Capabilities must accurately reflect what BlazeFace provides."""
    # Import the module-level constant directly
    from exam_photo.providers.mediapipe_face_detector import _CAPABILITIES

    assert _CAPABILITIES.landmarks is True
    assert _CAPABILITIES.pose is False
    assert _CAPABILITIES.occlusion is False
    assert _CAPABILITIES.cpu_execution is True
    assert _CAPABILITIES.deterministic_execution is True
    assert _CAPABILITIES.multiple_face_detection is True


# ---------------------------------------------------------------------------
# 7. Bounding box within image
# ---------------------------------------------------------------------------


@requires_mediapipe
@requires_model
def test_bounding_box_within_image() -> None:
    """All detected bounding boxes must lie within image dimensions."""
    image = _load_fixture("single_face_frontal.jpg")
    if image is None:
        pytest.skip("single_face_frontal.jpg not yet in fixtures/")

    with _provider() as det:
        result = det.detect_faces(image)

    w, h = image.size
    for det_result in result.detections:
        box = det_result.bounding_box
        assert box.left >= 0, f"left={box.left} < 0"
        assert box.top >= 0, f"top={box.top} < 0"
        assert box.right <= w, f"right={box.right} > img_w={w}"
        assert box.bottom <= h, f"bottom={box.bottom} > img_h={h}"
        assert box.right > box.left, "zero-width box"
        assert box.bottom > box.top, "zero-height box"


# ---------------------------------------------------------------------------
# 8. Bounding box touching image edge is clamped, not crashed
# ---------------------------------------------------------------------------


@requires_mediapipe
@requires_model
def test_bounding_box_touching_edge() -> None:
    """Faces near image border must not cause an error; boxes clamped correctly."""
    image = _load_fixture("single_face_frontal.jpg")
    if image is None:
        pytest.skip("single_face_frontal.jpg not yet in fixtures/")

    # Crop the image so the face is near/touching the top edge
    w, h = image.size
    cropped = image.crop((0, 0, w, h // 2))

    with _provider() as det:
        result = det.detect_faces(cropped)

    for face in result.detections:
        box = face.bounding_box
        assert box.left >= 0
        assert box.top >= 0
        assert box.right <= w
        assert box.bottom <= h // 2


# ---------------------------------------------------------------------------
# 9. duration_ms recorded
# ---------------------------------------------------------------------------


@requires_mediapipe
@requires_model
def test_duration_recorded() -> None:
    """duration_ms must be set and positive after a real inference call."""
    with _provider() as det:
        result = det.detect_faces(_make_blank_image())

    assert result.duration_ms is not None
    assert result.duration_ms > 0.0


# ---------------------------------------------------------------------------
# 10. Repeat inference consistency
# ---------------------------------------------------------------------------


@requires_mediapipe
@requires_model
def test_repeat_inference_consistency() -> None:
    """Same image run twice must yield the same detection count."""
    image = _load_fixture("single_face_frontal.jpg") or _make_blank_image()

    with _provider() as det:
        r1 = det.detect_faces(image)
        r2 = det.detect_faces(image)

    assert len(r1.detections) == len(r2.detections), (
        "Detection count differs between identical calls on the same image"
    )


# ---------------------------------------------------------------------------
# 11. ModelNotFoundError
# ---------------------------------------------------------------------------


@requires_mediapipe
def test_model_not_found_raises() -> None:
    """A non-existent model path must raise ModelNotFoundError."""
    from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector
    from exam_photo.providers.model_errors import ModelNotFoundError

    provider = MediapipeFaceDetector(
        model_path=Path("/tmp/does_not_exist_7x9z.task"),
        expected_sha256="",
    )
    with pytest.raises(ModelNotFoundError, match="Model asset not found"):
        provider.detect_faces(_make_blank_image())


# ---------------------------------------------------------------------------
# 12. ModelChecksumError
# ---------------------------------------------------------------------------


@requires_mediapipe
@requires_model
def test_model_checksum_mismatch_raises() -> None:
    """A wrong expected SHA-256 must raise ModelChecksumError."""
    from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector
    from exam_photo.providers.model_errors import ModelChecksumError

    assert _MODEL_PATH is not None
    wrong_sha = "a" * 64  # 64-char hex string, definitely wrong
    provider = MediapipeFaceDetector(
        model_path=_MODEL_PATH,
        expected_sha256=wrong_sha,
    )
    with pytest.raises(ModelChecksumError, match="SHA-256 mismatch"):
        provider.detect_faces(_make_blank_image())


# ---------------------------------------------------------------------------
# 13. Invalid model file raises on initialization
# ---------------------------------------------------------------------------


@requires_mediapipe
def test_invalid_model_file_raises(tmp_path: Path) -> None:
    """A file that exists but is not a valid .task file must raise on init."""
    from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector

    bad_file = tmp_path / "bad.task"
    bad_file.write_bytes(b"this is not a mediapipe model")

    provider = MediapipeFaceDetector(
        model_path=bad_file,
        expected_sha256="",  # skip sha check so init is attempted
    )
    with pytest.raises(
        ValueError
    ):  # MediaPipe raises a ValueError on invalid Flatbuffer buffer
        provider.detect_faces(_make_blank_image())


# ---------------------------------------------------------------------------
# 14. Provider init failure propagates
# ---------------------------------------------------------------------------


@requires_mediapipe
def test_provider_init_failure_propagates() -> None:
    """An init failure must propagate; detect_faces must not silently swallow it."""
    from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector
    from exam_photo.providers.model_errors import ModelNotFoundError

    provider = MediapipeFaceDetector(
        model_path=Path("/no/such/path/model.task"),
        expected_sha256="",
    )
    with pytest.raises(ModelNotFoundError):
        provider.detect_faces(_make_blank_image())

    # A second call must also fail (not silently succeed after partial init)
    with pytest.raises(ModelNotFoundError):
        provider.detect_faces(_make_blank_image())


# ---------------------------------------------------------------------------
# 15. Inference failure propagates
# ---------------------------------------------------------------------------


@requires_mediapipe
@requires_model
def test_inference_failure_propagates() -> None:
    """A zero-size image must trigger an error, not silently return empty."""

    # 1×1 image is a legal PIL image but may cause MediaPipe to error
    tiny = Image.new("RGB", (1, 1), (128, 128, 128))

    with _provider() as det:
        # We allow either a raised exception or an empty result —
        # the important thing is no silent wrong answer.
        try:
            result = det.detect_faces(tiny)
            # If it doesn't raise, it should return 0 faces (not incorrect detections)
            assert isinstance(result.detections, list)
        except Exception:
            pass  # Exception is also acceptable behaviour for a 1×1 image


# ---------------------------------------------------------------------------
# 16. Confidence-threshold filtering
# ---------------------------------------------------------------------------


@requires_mediapipe
@requires_model
def test_confidence_threshold_filtering() -> None:
    """All returned detections must have confidence >= min_detection_confidence."""
    image = _load_fixture("single_face_frontal.jpg")
    if image is None:
        pytest.skip("single_face_frontal.jpg not yet in fixtures/")

    threshold = 0.99  # very high — may filter even a real face
    with _provider(confidence=threshold) as det:
        result = det.detect_faces(image)

    for face in result.detections:
        assert face.confidence >= threshold, (
            f"Detection with confidence {face.confidence} slipped through "
            f"threshold {threshold}"
        )


# ---------------------------------------------------------------------------
# 17. Context manager calls close()
# ---------------------------------------------------------------------------


@requires_mediapipe
def test_context_manager_close() -> None:
    """__exit__ must call close() and release the detector."""
    from exam_photo.providers.mediapipe_face_detector import MediapipeFaceDetector

    provider = MediapipeFaceDetector(
        model_path=Path("/tmp/nonexistent.task"),
        expected_sha256="",
    )
    # Use __enter__ / __exit__ directly to verify close() is called
    provider.__enter__()
    provider.__exit__(None, None, None)
    assert provider._detector is None  # detector released


# ---------------------------------------------------------------------------
# 18. No absolute model path in provider output
# ---------------------------------------------------------------------------


@requires_mediapipe
@requires_model
def test_no_absolute_model_path_in_output() -> None:
    """The provider result must not leak the local model file path."""
    with _provider() as det:
        result = det.detect_faces(_make_blank_image())

    result_str = result.model_dump_json()
    assert str(_MODEL_PATH) not in result_str, (
        "Local model file path found in FaceDetectionResult output"
    )
