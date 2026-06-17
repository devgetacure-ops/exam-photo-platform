from typing import Any, Dict, Optional

from PIL import Image

from exam_photo.providers.capabilities import ProviderCapabilities
from exam_photo.providers.face_detection import (
    FaceDetection,
    FaceDetectionProvider,
    FaceDetectionResult,
)


class FakeFaceDetector(FaceDetectionProvider):
    def __init__(
        self,
        capabilities: Optional[ProviderCapabilities] = None,
        detections: Optional[list[FaceDetection]] = None,
        warnings: Optional[list[str]] = None,
        raise_error: Optional[str] = None,
    ) -> None:
        self.capabilities = capabilities or ProviderCapabilities(
            multiple_face_detection=True,
            landmarks=True,
            pose=True,
            occlusion=True,
        )
        self.detections = detections or []
        self.warnings = warnings or []
        self.raise_error = raise_error

    def detect_faces(
        self,
        image: Image.Image,
        config: Optional[Dict[str, Any]] = None,
    ) -> FaceDetectionResult:
        if self.raise_error:
            raise RuntimeError(self.raise_error)
        return FaceDetectionResult(
            provider_name="FakeFaceDetector",
            provider_version="0.0.1-fake",
            capabilities=self.capabilities,
            detections=self.detections,
            warnings=self.warnings,
            duration_ms=5.0,
        )
