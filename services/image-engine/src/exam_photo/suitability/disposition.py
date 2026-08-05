"""Accept / warn / block disposition policy (DEC-041).

The rule this module implements is deliberately narrow: **block only when the
engine cannot produce a truthful output; otherwise produce, and report what is
risky.**  Blocking and warning demand the same corrective action from a
candidate -- retake the photograph -- so blocking buys no extra protection
while removing the deliverable.  The error costs are asymmetric: a wrong
warning is an annoyance, a wrong block loses the user on a false premise.

Only signals whose reliability has been measured appear here.  Sunglasses, head
coverings and eye closure are deliberately absent: measured over the 40-photo
adversarial set, neither the eye-blink blendshape nor eye-region darkness
separates them from narrow eyes, deep-set eyes or ordinary shadow (photo 12
wears sunglasses and scores normally on both; photos 13 and 37 score guilty and
wear none).  DEC-041 forbids promoting a signal before its reliability is
measured, and this one has now been measured and rejected.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from exam_photo.suitability.issue_codes import SuitabilityIssueCode


class Disposition(str, Enum):
    """What the platform does with the photograph."""

    ACCEPT = "accept"
    WARN = "warn"
    BLOCK = "block"


class FindingLevel(str, Enum):
    """How loudly the interface should present a finding.

    ``LIKELY_REJECTION`` is shown as an acknowledgement step with retaking as
    the primary action; ``POSSIBLE_ISSUE`` is an inline notice.  Neither stops
    the download -- that separation between "the engine refuses" and "the
    interface asks you to confirm" is what makes it safe to warn on signals
    that can occasionally be wrong.
    """

    LIKELY_REJECTION = "likely_rejection"
    POSSIBLE_ISSUE = "possible_issue"


class AppearanceFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: SuitabilityIssueCode
    level: FindingLevel
    message: str
    remedy: str
    measured_value: Optional[float] = None


class AppearanceSignals(BaseModel):
    """Measurements the disposition policy consumes.

    Kept separate from the policy so the thresholds can be tested without a
    model, and so the measurement code can change without touching the rule.
    """

    model_config = ConfigDict(extra="forbid")

    image_width: int = Field(gt=0)
    image_height: int = Field(gt=0)

    face_count: int = Field(ge=0)
    # The confidence tier the detector had to drop to before finding anything.
    # A face found only at the lowest tier is not trustworthy enough to block on.
    detection_confidence: Optional[float] = None
    primary_face_height_px: Optional[float] = None
    # Height of the second-largest face over the largest. A distant bystander
    # is not ambiguity about who the subject is; a second face of comparable
    # size is.
    second_face_height_ratio: float = 0.0

    landmarks_available: bool = False
    yaw_degrees: Optional[float] = None
    pitch_degrees: Optional[float] = None
    roll_degrees: Optional[float] = None

    # Luminance and dark fraction are measured over the FACE region, not the
    # frame; a night portrait with a well-lit face is correctly exposed.
    mean_luminance: Optional[float] = None
    dark_pixel_fraction: Optional[float] = None
    mean_saturation: Optional[float] = None
    # Laplacian variance of the face resampled to a fixed box, so the value
    # does not scale with how many pixels the face happens to occupy.
    face_sharpness: Optional[float] = None

    target_height_px: Optional[int] = None
    target_head_height_ratio: Optional[float] = None


class DispositionReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    disposition: Disposition
    findings: List[AppearanceFinding] = Field(default_factory=list)
    block_reason: Optional[str] = None

    @property
    def likely_rejections(self) -> List[AppearanceFinding]:
        return [f for f in self.findings if f.level == FindingLevel.LIKELY_REJECTION]


# --- Thresholds -------------------------------------------------------------
#
# Every value below is calibrated against the 40-photo adversarial set and is
# stated with the separation actually observed, so a later change can tell
# whether it is moving a boundary or crossing a measurement.

# A second face must be at least half the height of the primary one before the
# subject is genuinely ambiguous. Measured: the only comparable second faces are
# 0.98 and 0.85 (two genuine two-person photographs); background bystanders are
# not detected at all, and the crop removes them regardless.
_AMBIGUOUS_SECOND_FACE_RATIO = 0.50

# ...and it must have been found without dropping to the detector's lowest
# tier. Measured: one photograph of a single person in front of a printed
# banner yields a spurious second "face" at 0.15 and at no higher tier, with no
# landmarks on it. Blocking on that would reject a perfectly usable photograph.
_MIN_CONFIDENCE_TO_BLOCK = 0.25

# Underexposure is judged on the FACE region, never the frame (see
# ``appearance_signals``): the two darkest-framed photographs in the
# adversarial set carry faces at luminance 98 and 93 and were classed ideal by
# a reviewer, so a frame-based threshold produced two false likely-rejections.
#
# This bound is deliberately provisional. Across all 40 photographs the darkest
# measured face reads 78, so the set contains no genuinely underexposed face
# and offers no positive example to calibrate against. The threshold therefore
# sits comfortably below every observed face rather than inside a measured gap,
# and should be revisited when a genuinely dark-faced photograph exists to test
# it. Erring low is the correct direction: a missed warning costs a candidate a
# retake, a false one costs the platform a user.
_SEVERE_UNDEREXPOSURE_LUMINANCE = 55.0
_SEVERE_UNDEREXPOSURE_DARK_FRACTION = 0.35

# Measured: the one black-and-white photograph reads mean saturation 0.0; the
# least saturated colour photograph reads 13.5.
_MONOCHROME_SATURATION = 5.0

# Head-pose tolerances. No conducting body publishes a numeric tolerance (see
# DEC-042), so these are engineering judgement rather than a cited rule, and
# they are therefore warnings only.
_EXTREME_YAW = 35.0
_EXTREME_PITCH = 30.0
_WARN_YAW = 20.0
_WARN_PITCH = 20.0
_WARN_ROLL = 15.0

# Enlargement of real source detail beyond which the output is visibly soft.
#
# Measured over the earlier 60-photo reference set: every output size class
# that downscaled the source was visually clean (median 0.41x to 0.94x), while
# the one class needing a median 4.41x enlargement carried every visible
# artefact the reviewer reported. The boundary therefore sits between those,
# not at 2.0: a threshold of 2.0 fired on 38 of the 40 adversarial photographs
# when their target was the most demanding size class, and a warning that
# fires on almost everything trains users to ignore it.
_WARN_UPSCALE_FACTOR = 3.0

# Normalised face sharpness below which the face reads soft. Measured on the
# adversarial set: the one photograph a reviewer labelled blurred scores 48,
# while the lowest of the ten labelled perfect scores 97. This sits between
# them, nearer the positive.
#
# It stays a POSSIBLE_ISSUE rather than a LIKELY_REJECTION despite bodies such
# as SSC listing blur as an explicit rejection ground, because the calibration
# rests on a single labelled positive. Three further photographs fall below it
# (a night selfie and two distant subjects) which are plausibly soft but were
# labelled for other defects, so the true positive rate is unknown. Promote it
# only when more labelled blurred photographs exist.
_SOFT_FACE_SHARPNESS = 70.0

# The detector's face box covers brow-to-chin, not the crown-to-chin head span
# the composition targets are expressed against. Measured across the reference
# set, the head span runs about 1.5x the detector box height, so comparing a
# head-height requirement directly against the box would overstate the needed
# enlargement by roughly half again.
_FACE_BOX_TO_HEAD_SPAN = 1.5


def evaluate_disposition(
    signals: AppearanceSignals,
    *,
    monochrome_accepted: Optional[bool] = None,
) -> DispositionReport:
    """Decide accept / warn / block for one photograph.

    ``monochrome_accepted`` comes from the exam's appearance rules (DEC-042).
    ``None`` means the conducting body did not specify it, which is not the
    same as permission -- an unspecified rule produces no finding at all,
    because inventing one would be exactly the silent assumption the contract
    forbids.
    """
    findings: List[AppearanceFinding] = []

    # --- Block conditions: the output would be meaningless or untruthful ---

    if signals.face_count == 0:
        return DispositionReport(
            disposition=Disposition.BLOCK,
            block_reason=(
                "No face could be found in this photograph, so there is no "
                "portrait to produce."
            ),
            findings=[
                AppearanceFinding(
                    code=SuitabilityIssueCode.SUITABILITY_NO_FACE,
                    level=FindingLevel.LIKELY_REJECTION,
                    message="No face was detected in the uploaded photograph.",
                    remedy=(
                        "Upload a photograph where your face is clearly visible "
                        "and facing the camera."
                    ),
                )
            ],
        )

    confident_enough = (
        signals.detection_confidence is not None
        and signals.detection_confidence >= _MIN_CONFIDENCE_TO_BLOCK
    )
    if (
        signals.face_count > 1
        and signals.second_face_height_ratio >= _AMBIGUOUS_SECOND_FACE_RATIO
        and confident_enough
    ):
        # Choosing a face here would silently produce a photograph of possibly
        # the wrong person, which is an untruthful output rather than a risky
        # one. That is the distinction that makes this a block.
        return DispositionReport(
            disposition=Disposition.BLOCK,
            block_reason=(
                "More than one person appears in this photograph, so it is not "
                "clear whose passport photograph to produce."
            ),
            findings=[
                AppearanceFinding(
                    code=SuitabilityIssueCode.SUITABILITY_MULTIPLE_FACES,
                    level=FindingLevel.LIKELY_REJECTION,
                    message=(
                        f"{signals.face_count} faces of similar size were "
                        "detected in this photograph."
                    ),
                    remedy="Upload a photograph containing only yourself.",
                    measured_value=signals.second_face_height_ratio,
                )
            ],
        )

    # --- Likely rejection: produced, but the exam will probably refuse it ---

    if (
        signals.mean_luminance is not None
        and signals.dark_pixel_fraction is not None
        and signals.mean_luminance < _SEVERE_UNDEREXPOSURE_LUMINANCE
        and signals.dark_pixel_fraction > _SEVERE_UNDEREXPOSURE_DARK_FRACTION
    ):
        findings.append(
            AppearanceFinding(
                code=SuitabilityIssueCode.SUITABILITY_UNDEREXPOSED_SEVERE,
                level=FindingLevel.LIKELY_REJECTION,
                message="This photograph is very dark.",
                remedy=(
                    "Retake it facing a window or in a well-lit room, with the "
                    "light in front of you rather than behind you."
                ),
                measured_value=signals.mean_luminance,
            )
        )

    # A face the detector is confident about, on which the dense landmarker
    # then finds nothing, is in practice a profile or a heavily occluded face.
    # Measured: this is what fires on the one true side-profile photograph.
    if not signals.landmarks_available and confident_enough:
        findings.append(
            AppearanceFinding(
                code=SuitabilityIssueCode.SUITABILITY_POSE_EXTREME,
                level=FindingLevel.LIKELY_REJECTION,
                message=(
                    "Your face could not be read in detail, which usually means "
                    "it is turned to the side or partly covered."
                ),
                remedy=(
                    "Retake the photograph looking straight at the camera with "
                    "your whole face visible."
                ),
            )
        )
    elif signals.landmarks_available:
        yaw = abs(signals.yaw_degrees or 0.0)
        pitch = abs(signals.pitch_degrees or 0.0)
        roll = abs(signals.roll_degrees or 0.0)
        if yaw >= _EXTREME_YAW or pitch >= _EXTREME_PITCH:
            findings.append(
                AppearanceFinding(
                    code=SuitabilityIssueCode.SUITABILITY_POSE_EXTREME,
                    level=FindingLevel.LIKELY_REJECTION,
                    message="Your head is turned well away from the camera.",
                    remedy="Retake the photograph facing the camera directly.",
                    measured_value=max(yaw, pitch),
                )
            )
        elif yaw >= _WARN_YAW or pitch >= _WARN_PITCH or roll >= _WARN_ROLL:
            findings.append(
                AppearanceFinding(
                    code=SuitabilityIssueCode.SUITABILITY_POSE_WARNING,
                    level=FindingLevel.POSSIBLE_ISSUE,
                    message="Your head is slightly turned or tilted.",
                    remedy=(
                        "Face the camera squarely and keep your head level for "
                        "the best chance of acceptance."
                    ),
                    measured_value=max(yaw, pitch, roll),
                )
            )

    if (
        monochrome_accepted is False
        and signals.mean_saturation is not None
        and signals.mean_saturation < _MONOCHROME_SATURATION
    ):
        findings.append(
            AppearanceFinding(
                code=SuitabilityIssueCode.SUITABILITY_LOW_CONTRAST_WARNING,
                level=FindingLevel.LIKELY_REJECTION,
                message=(
                    "This photograph appears to be black and white, and this "
                    "exam requires a colour photograph."
                ),
                remedy="Upload a colour photograph.",
                measured_value=signals.mean_saturation,
            )
        )

    # --- Possible issue: worth saying, not worth alarming over ---

    if (
        signals.face_sharpness is not None
        and signals.face_sharpness < _SOFT_FACE_SHARPNESS
    ):
        findings.append(
            AppearanceFinding(
                code=SuitabilityIssueCode.SUITABILITY_BLUR_WARNING,
                level=FindingLevel.POSSIBLE_ISSUE,
                message="Your face looks soft or slightly out of focus.",
                remedy=(
                    "Retake the photograph holding the camera steady, with your "
                    "face in focus and reasonably close."
                ),
                measured_value=signals.face_sharpness,
            )
        )

    if (
        signals.target_height_px
        and signals.primary_face_height_px
        and signals.target_head_height_ratio
    ):
        required_head_px = signals.target_height_px * signals.target_head_height_ratio
        available_head_px = signals.primary_face_height_px * _FACE_BOX_TO_HEAD_SPAN
        upscale = required_head_px / max(1.0, available_head_px)
        if upscale >= _WARN_UPSCALE_FACTOR:
            findings.append(
                AppearanceFinding(
                    code=SuitabilityIssueCode.SUITABILITY_RESOLUTION_WARNING,
                    level=FindingLevel.POSSIBLE_ISSUE,
                    message=(
                        "Your face is small in this photograph, so the finished "
                        "photo has to be enlarged and may look soft."
                    ),
                    remedy=(
                        "Retake the photograph standing closer to the camera, "
                        "or use a higher-resolution photograph."
                    ),
                    measured_value=upscale,
                )
            )

    return DispositionReport(
        disposition=Disposition.WARN if findings else Disposition.ACCEPT,
        findings=findings,
    )
