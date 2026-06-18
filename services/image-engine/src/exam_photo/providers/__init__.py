from exam_photo.providers.capabilities import ProviderCapabilities
from exam_photo.providers.face_detection import (
    FaceDetection,
    FaceDetectionProvider,
    FaceDetectionResult,
)
from exam_photo.providers.head_estimation import (
    BoundaryVisibilityValue,
    HeadBoundaryVisibility,
    HeadEstimationConfig,
    HeadEstimationProvider,
    HeadEstimationResult,
)
from exam_photo.providers.landmark_geometric_head_estimator import (
    LandmarkGeometricHeadEstimator,
)
from exam_photo.providers.model_errors import ModelChecksumError, ModelNotFoundError
from exam_photo.providers.subject_segmentation import (
    MaskValidationReport,
    SegmentationCapabilities,
    SegmentationConfig,
    SegmentationStatusValue,
    SubjectSegmentationProvider,
    SubjectSegmentationResult,
)

__all__ = [
    "ProviderCapabilities",
    "FaceDetection",
    "FaceDetectionResult",
    "FaceDetectionProvider",
    "BoundaryVisibilityValue",
    "HeadBoundaryVisibility",
    "HeadEstimationResult",
    "HeadEstimationProvider",
    "HeadEstimationConfig",
    "LandmarkGeometricHeadEstimator",
    "ModelNotFoundError",
    "ModelChecksumError",
    "SegmentationStatusValue",
    "SegmentationCapabilities",
    "SegmentationConfig",
    "MaskValidationReport",
    "SubjectSegmentationResult",
    "SubjectSegmentationProvider",
]

# MediapipeFaceDetector and MediapipeSubjectSegmenter are exported lazily
# to avoid ImportError when the optional 'face' extra is not installed.
try:
    from exam_photo.providers.mediapipe_face_detector import (  # noqa: F401
        MediapipeFaceDetector,
    )
    from exam_photo.providers.segmenters.mediapipe_segmenter import (  # noqa: F401
        MediapipeSubjectSegmenter,
    )

    __all__ += ["MediapipeFaceDetector", "MediapipeSubjectSegmenter"]
except ImportError:  # pragma: no cover
    pass
