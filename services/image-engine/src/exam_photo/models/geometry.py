import math
from typing import Dict, Optional

from pydantic import BaseModel, Field, model_validator


class Point(BaseModel):
    x: float
    y: float


class BoundingBox(BaseModel):
    left: float
    top: float
    right: float
    bottom: float

    @model_validator(mode="after")
    def validate_box(self) -> "BoundingBox":
        for field in ("left", "top", "right", "bottom"):
            val = getattr(self, field)
            if not math.isfinite(val):
                raise ValueError(f"{field} must be finite.")
        if self.right <= self.left:
            raise ValueError(
                f"right ({self.right}) must be greater than left ({self.left})."
            )
        if self.bottom <= self.top:
            raise ValueError(
                f"bottom ({self.bottom}) must be greater than top ({self.top})."
            )
        return self

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.bottom - self.top

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def centre(self) -> Point:
        return Point(x=(self.left + self.right) / 2.0, y=(self.top + self.bottom) / 2.0)

    def intersection(self, other: "BoundingBox") -> Optional["BoundingBox"]:
        x_left = max(self.left, other.left)
        y_top = max(self.top, other.top)
        x_right = min(self.right, other.right)
        y_bottom = min(self.bottom, other.bottom)

        if x_right <= x_left or y_bottom <= y_top:
            return None
        return BoundingBox(left=x_left, top=y_top, right=x_right, bottom=y_bottom)

    def contains(self, other: "BoundingBox") -> bool:
        return (
            self.left <= other.left
            and self.top <= other.top
            and self.right >= other.right
            and self.bottom >= other.bottom
        )

    def clamp(self, max_width: float, max_height: float) -> "BoundingBox":
        new_left = max(0.0, min(self.left, max_width))
        new_top = max(0.0, min(self.top, max_height))
        new_right = max(0.0, min(self.right, max_width))
        new_bottom = max(0.0, min(self.bottom, max_height))

        if new_right <= new_left:
            delta = min(1.0, max_width * 0.01) if max_width > 0 else 0.0
            if new_left >= max_width:
                new_left = max(0.0, max_width - delta)
                new_right = max_width
            else:
                new_right = min(max_width, new_left + delta)
            if new_right <= new_left and max_width > 0:
                new_left = 0.0
                new_right = max_width

        if new_bottom <= new_top:
            delta = min(1.0, max_height * 0.01) if max_height > 0 else 0.0
            if new_top >= max_height:
                new_top = max(0.0, max_height - delta)
                new_bottom = max_height
            else:
                new_bottom = min(max_height, new_top + delta)
            if new_bottom <= new_top and max_height > 0:
                new_top = 0.0
                new_bottom = max_height

        return BoundingBox(
            left=new_left, top=new_top, right=new_right, bottom=new_bottom
        )

    def to_pixel(self, img_w: int, img_h: int) -> "BoundingBox":
        return BoundingBox(
            left=self.left * img_w,
            top=self.top * img_h,
            right=self.right * img_w,
            bottom=self.bottom * img_h,
        )

    def to_normalized(self, img_w: int, img_h: int) -> "BoundingBox":
        if img_w <= 0 or img_h <= 0:
            raise ValueError("Dimensions must be positive to normalize.")
        return BoundingBox(
            left=self.left / img_w,
            top=self.top / img_h,
            right=self.right / img_w,
            bottom=self.bottom / img_h,
        )


class Landmarks(BaseModel):
    left_eye: Optional[Point] = None
    right_eye: Optional[Point] = None
    nose_tip: Optional[Point] = None
    mouth_left: Optional[Point] = None
    mouth_right: Optional[Point] = None
    chin: Optional[Point] = None
    custom_landmarks: Dict[str, Point] = Field(default_factory=dict)


class PoseEstimate(BaseModel):
    yaw: float
    pitch: float
    roll: float
    confidence: float
    method: str
