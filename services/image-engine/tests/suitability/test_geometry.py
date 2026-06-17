import pytest

from exam_photo.models.geometry import BoundingBox, Point


def test_point() -> None:
    pt = Point(x=10.5, y=20.5)
    assert pt.x == 10.5
    assert pt.y == 20.5


def test_bounding_box_valid() -> None:
    box = BoundingBox(left=0.0, top=0.0, right=100.0, bottom=200.0)
    assert box.width == 100.0
    assert box.height == 200.0
    assert box.area == 20000.0
    assert box.centre.x == 50.0
    assert box.centre.y == 100.0


def test_bounding_box_invalid() -> None:
    with pytest.raises(ValueError):
        BoundingBox(left=100.0, top=0.0, right=50.0, bottom=100.0)

    with pytest.raises(ValueError):
        BoundingBox(left=0.0, top=100.0, right=50.0, bottom=50.0)

    with pytest.raises(ValueError):
        BoundingBox(left=float("nan"), top=0.0, right=100.0, bottom=200.0)


def test_bounding_box_intersection() -> None:
    box1 = BoundingBox(left=10.0, top=10.0, right=50.0, bottom=50.0)
    box2 = BoundingBox(left=30.0, top=30.0, right=70.0, bottom=70.0)
    inter = box1.intersection(box2)
    assert inter is not None
    assert inter.left == 30.0
    assert inter.top == 30.0
    assert inter.right == 50.0
    assert inter.bottom == 50.0

    box3 = BoundingBox(left=60.0, top=60.0, right=100.0, bottom=100.0)
    assert box1.intersection(box3) is None


def test_bounding_box_contains() -> None:
    box1 = BoundingBox(left=0.0, top=0.0, right=100.0, bottom=100.0)
    box2 = BoundingBox(left=10.0, top=10.0, right=90.0, bottom=90.0)
    assert box1.contains(box2) is True
    assert box2.contains(box1) is False


def test_bounding_box_clamp() -> None:
    box = BoundingBox(left=-10.0, top=-10.0, right=120.0, bottom=120.0)
    clamped = box.clamp(100.0, 100.0)
    assert clamped.left == 0.0
    assert clamped.top == 0.0
    assert clamped.right == 100.0
    assert clamped.bottom == 100.0


def test_bounding_box_clamp_out_of_bounds() -> None:
    box_right = BoundingBox(left=110.0, top=0.0, right=120.0, bottom=100.0)
    clamped_right = box_right.clamp(100.0, 100.0)
    assert clamped_right.left >= 0.0
    assert clamped_right.right <= 100.0
    assert clamped_right.right > clamped_right.left

    box_bottom = BoundingBox(left=0.0, top=110.0, right=100.0, bottom=120.0)
    clamped_bottom = box_bottom.clamp(100.0, 100.0)
    assert clamped_bottom.top >= 0.0
    assert clamped_bottom.bottom <= 100.0
    assert clamped_bottom.bottom > clamped_bottom.top


def test_coordinate_conversions() -> None:
    box = BoundingBox(left=0.1, top=0.2, right=0.9, bottom=0.8)
    pixel = box.to_pixel(1000, 2000)
    assert pixel.left == 100.0
    assert pixel.top == 400.0
    assert pixel.right == 900.0
    assert pixel.bottom == 1600.0

    normalized = pixel.to_normalized(1000, 2000)
    assert abs(normalized.left - 0.1) < 1e-6
    assert abs(normalized.bottom - 0.8) < 1e-6
