from exam_photo.providers.background_composers.solid_background_composer import (
    SolidBackgroundComposer,
)
from exam_photo.providers.background_composition import (
    BackgroundComposer,
    BackgroundCompositionConfig,
    BackgroundCompositionIssueCode,
    BackgroundCompositionResult,
    BackgroundCompositionValidationIssue,
    BackgroundCompositionValidationReport,
    BackgroundMode,
)
from exam_photo.providers.capabilities import ProviderCapabilities
from exam_photo.providers.crop_planners.deterministic_crop_mode_b_planner import (
    DeterministicCropModeBPlanner,
)
from exam_photo.providers.crop_planners.deterministic_crop_planner import (
    DeterministicCropPlanner,
)
from exam_photo.providers.crop_planning import (
    CropConfig,
    CropIssueCode,
    CropMode,
    CropModeBConfig,
    CropModeBResult,
    CropPlanner,
    CropPlanResult,
    CropValidationIssue,
    CropValidationReport,
)
from exam_photo.providers.face_detection import (
    FaceDetection,
    FaceDetectionProvider,
    FaceDetectionResult,
)
from exam_photo.providers.foreground_refinement import (
    ForegroundRefinementProvider,
    RefinedMaskResult,
    RefinedMaskValidationReport,
    RefinementConfig,
    RefinementValidationIssue,
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
from exam_photo.providers.output_preparation import (
    EnhancementMode,
    OutputPreparationConfig,
    OutputPreparationIssueCode,
    OutputPreparationResult,
    OutputPreparationValidationReport,
    OutputPreparer,
    ResampleMethod,
    ResizeMode,
)
from exam_photo.providers.output_preparers.deterministic_output_preparer import (
    DeterministicOutputPreparer,
)
from exam_photo.providers.refiners.morphological_refiner import (
    MorphologicalForegroundRefiner,
)
from exam_photo.providers.subject_segmentation import (
    MaskValidationReport,
    SegmentationCapabilities,
    SegmentationClassCoverage,
    SegmentationConfig,
    SegmentationStatusValue,
    SegmentationValidationIssue,
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
    "SegmentationClassCoverage",
    "SegmentationValidationIssue",
    "ForegroundRefinementProvider",
    "RefinedMaskResult",
    "RefinedMaskValidationReport",
    "RefinementConfig",
    "RefinementValidationIssue",
    "MorphologicalForegroundRefiner",
    "CropMode",
    "CropIssueCode",
    "CropValidationIssue",
    "CropConfig",
    "CropValidationReport",
    "CropPlanResult",
    "CropPlanner",
    "DeterministicCropPlanner",
    "CropModeBConfig",
    "CropModeBResult",
    "DeterministicCropModeBPlanner",
    "BackgroundMode",
    "BackgroundCompositionIssueCode",
    "BackgroundCompositionValidationIssue",
    "BackgroundCompositionConfig",
    "BackgroundCompositionValidationReport",
    "BackgroundCompositionResult",
    "BackgroundComposer",
    "SolidBackgroundComposer",
    "ResizeMode",
    "ResampleMethod",
    "EnhancementMode",
    "OutputPreparationIssueCode",
    "OutputPreparationConfig",
    "OutputPreparationValidationReport",
    "OutputPreparationResult",
    "OutputPreparer",
    "DeterministicOutputPreparer",
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
