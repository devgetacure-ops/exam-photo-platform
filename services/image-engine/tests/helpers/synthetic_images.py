import io
from typing import Any

from PIL import Image, ImageDraw


def create_solid_image(
    mode: str = "RGB",
    size: tuple[int, int] = (100, 100),
    color: Any = None,
) -> Image.Image:
    if color is None:
        color = 128 if mode == "L" else (255, 0, 0)
    image = Image.new(mode, size, color)
    draw = ImageDraw.Draw(image)
    rect_color = 255 if mode == "L" else (0, 255, 0)
    draw.rectangle((10.0, 10.0, 90.0, 90.0), fill=rect_color)
    return image


def save_image_to_bytes(
    image: Image.Image,
    fmt: str = "PNG",
    **kwargs: Any,
) -> bytes:
    stream = io.BytesIO()
    image.save(stream, format=fmt, **kwargs)
    return stream.getvalue()


def create_rotated_exif_jpeg(
    orientation: int,
    size: tuple[int, int] = (100, 100),
) -> bytes:
    image = create_solid_image("RGB", size)
    exif = image.getexif()
    exif[274] = orientation  # Orientation tag
    return save_image_to_bytes(image, "JPEG", exif=exif)


def create_multiframe_gif() -> bytes:
    frame1 = create_solid_image("RGB", (100, 100), (255, 0, 0))
    frame2 = create_solid_image("RGB", (100, 100), (0, 0, 255))
    stream = io.BytesIO()
    frame1.save(
        stream,
        format="GIF",
        save_all=True,
        append_images=[frame2],
        duration=100,
        loop=0,
    )
    return stream.getvalue()
