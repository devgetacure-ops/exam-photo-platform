from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from PIL import Image
from pydantic import BaseModel, Field

from exam_photo.models.geometry import BoundingBox, Landmarks, PoseEstimate
from exam_photo.providers.capabilities import ProviderCapabilities


class FaceDetection(BaseModel):
    bounding_box: BoundingBox
    confidence: float
    landmarks: Optional[Landmarks] = None
    pose: Optional[PoseEstimate] = None
    occlusion_indicators: Optional[Dict[str, bool]] = None
    quality_indicators: Optional[Dict[str, float]] = None
    provider_metadata: Optional[Dict[str, Any]] = None


class FaceDetectionResult(BaseModel):
    provider_name: str
    provider_version: str
    capabilities: ProviderCapabilities
    detections: List[FaceDetection] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    duration_ms: Optional[float] = None


@runtime_checkable
class FaceDetectionProvider(Protocol):
    def detect_faces(
        self,
        image: Image.Image,
        config: Optional[Dict[str, Any]] = None,
    ) -> FaceDetectionResult:
        """Runs face detection on the normalized PIL image."""
        ...
