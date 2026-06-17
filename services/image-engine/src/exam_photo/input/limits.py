from typing import Set

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InputLimits(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Development safety defaults
    maximum_encoded_byte_size: int = Field(default=10 * 1024 * 1024, gt=0)  # 10 MB
    maximum_width: int = Field(default=8192, gt=0)
    maximum_height: int = Field(default=8192, gt=0)
    maximum_total_pixel_count: int = Field(
        default=16777216, gt=0
    )  # 8192 * 2048 equivalent

    allowed_actual_formats: Set[str] = Field(default_factory=lambda: {"jpeg", "png"})
    strict_extension: bool = False

    multi_frame_policy: str = "reject"  # reject | allow
    truncated_image_policy: str = "reject"  # reject | allow
    extension_mismatch_policy: str = "warn"  # warn | reject

    @model_validator(mode="after")
    def validate_limits_coherency(self) -> "InputLimits":
        if not self.allowed_actual_formats:
            raise ValueError("allowed_actual_formats set cannot be empty.")

        # Ensure only jpeg and png are configured in allowed formats
        supported = {"jpeg", "png"}
        for fmt in self.allowed_actual_formats:
            if fmt not in supported:
                raise ValueError(
                    f"Format '{fmt}' is not supported by this engine version."
                )

        if self.strict_extension:
            self.extension_mismatch_policy = "reject"

        # Validate policies
        valid_policies = {"reject", "allow"}
        if self.multi_frame_policy not in valid_policies:
            raise ValueError(f"multi_frame_policy must be one of {valid_policies}")
        if self.truncated_image_policy not in valid_policies:
            raise ValueError(f"truncated_image_policy must be one of {valid_policies}")
        if self.extension_mismatch_policy not in {"warn", "reject"}:
            raise ValueError(
                "extension_mismatch_policy must be one of {'warn', 'reject'}"
            )

        return self
