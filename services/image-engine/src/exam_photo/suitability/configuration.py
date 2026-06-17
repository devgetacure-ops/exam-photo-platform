from pydantic import BaseModel, Field, model_validator


class SuitabilityThresholds(BaseModel):
    minimum_source_width: int = Field(default=300, gt=0)
    minimum_source_height: int = Field(default=300, gt=0)
    minimum_source_pixels: int = Field(default=90000, gt=0)

    # Blur thresholds (using edge-energy heuristic)
    blur_warning_threshold: float = Field(default=10.0, gt=0.0)
    blur_blocking_threshold: float = Field(default=5.0, gt=0.0)

    # Luminance boundaries (0-255 scale)
    mean_luminance_warning_low: float = Field(default=60.0, ge=0.0)
    mean_luminance_warning_high: float = Field(default=220.0, ge=0.0)
    mean_luminance_blocking_low: float = Field(default=30.0, ge=0.0)
    mean_luminance_blocking_high: float = Field(default=245.0, ge=0.0)

    shadow_clipping_threshold: float = Field(default=0.15, ge=0.0, le=1.0)
    highlight_clipping_threshold: float = Field(default=0.15, ge=0.0, le=1.0)
    low_contrast_threshold: float = Field(default=20.0, gt=0.0)

    # Transparency bounds (ratio of pixels)
    transparent_pixel_warning_threshold: float = Field(default=0.05, ge=0.0, le=1.0)
    transparent_pixel_blocking_threshold: float = Field(default=0.20, ge=0.0, le=1.0)

    face_confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    multiple_face_handling_policy: str = "reject"  # reject | allow

    pose_warning_yaw: float = Field(default=15.0, ge=0.0)
    pose_warning_pitch: float = Field(default=15.0, ge=0.0)
    pose_warning_roll: float = Field(default=15.0, ge=0.0)

    pose_blocking_yaw: float = Field(default=30.0, ge=0.0)
    pose_blocking_pitch: float = Field(default=30.0, ge=0.0)
    pose_blocking_roll: float = Field(default=30.0, ge=0.0)

    @model_validator(mode="after")
    def validate_thresholds(self) -> "SuitabilityThresholds":
        # Ensure blocking thresholds are strictly more restrictive or equal to warnings where relevant
        if self.blur_blocking_threshold > self.blur_warning_threshold:
            raise ValueError(
                "blur_blocking_threshold cannot be higher (softer) than warning_threshold."
            )
        if self.mean_luminance_blocking_low > self.mean_luminance_warning_low:
            raise ValueError(
                "mean_luminance_blocking_low must be less than or equal to warning_low."
            )
        if self.mean_luminance_blocking_high < self.mean_luminance_warning_high:
            raise ValueError(
                "mean_luminance_blocking_high must be greater than or equal to warning_high."
            )
        if (
            self.transparent_pixel_blocking_threshold
            < self.transparent_pixel_warning_threshold
        ):
            raise ValueError(
                "transparent_pixel_blocking_threshold must be greater than or equal to warning_threshold."
            )

        # Pose checks
        if self.pose_blocking_yaw < self.pose_warning_yaw:
            raise ValueError("pose_blocking_yaw must be >= warning.")
        if self.pose_blocking_pitch < self.pose_warning_pitch:
            raise ValueError("pose_blocking_pitch must be >= warning.")
        if self.pose_blocking_roll < self.pose_warning_roll:
            raise ValueError("pose_blocking_roll must be >= warning.")
        return self
