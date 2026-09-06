"""The only image the browser is given before payment (DEC-063).

The candidate has to be able to judge what was made for them before they buy
it, and the platform has to still have something to sell afterwards. Those
pull in opposite directions, and the resolution is a copy that is honestly
representative and deliberately not the product: the finished file at reduced
resolution, with a mark burned into the pixels.

Burned in is the whole point. A watermark drawn by the page is drawn on an
image the page already holds, so the clean file is on the candidate's machine
before the mark exists and the mark protects nothing; an overlay served
alongside the original is a stylesheet away from being switched off. This
module rasterises the mark into a re-encoded downscale, so there is no layer
to strip and no original underneath it.

The two protections do different jobs:

- **Reduced resolution** means the preview cannot meet the examination's own
  pixel specification, so it is not submittable even with the mark gone.
- **The mark** carries the gate on its own for the few examinations whose
  output is already so small that halving it would still leave something a
  portal would accept.

Nothing here knows about jobs, payment or HTTP. It takes the bytes of a
finished file and returns the bytes of its preview.
"""

import io
import math
from dataclasses import dataclass
from typing import Optional, Union

from PIL import Image, ImageDraw, ImageFont

#: Previews are always JPEG. The output may carry transparency; the preview is
#: flattened onto white before it is marked, so a candidate never judges their
#: photograph against whatever the browser happens to paint behind it.
PREVIEW_MEDIA_TYPE = "image/jpeg"

#: The name the preview is stored under, inside the job directory.
PREVIEW_FILENAME = "preview.jpg"

#: Burned into the pixels, so the mark also travels with the image if one
#: escapes the page it was shown on. ASCII only: it is drawn in Pillow's
#: bundled font, where a missing glyph would silently become a box.
DEFAULT_WATERMARK_TEXT = "PREVIEW - NOT FOR SUBMISSION"

#: Half the long edge. Any downscale at all breaks the examination's pixel
#: specification; a half is enough to be plainly not the product while leaving
#: the face large enough to judge.
_PREVIEW_SCALE = 0.5

#: Below this the preview is served at the finished file's own size. A few
#: examinations specify a photograph under 200 px on its long edge, and a
#: candidate cannot judge their own face at a hundred pixels. For those the
#: mark is the whole of the gate -- recorded in DEC-063 rather than left as a
#: silent floor here.
_MIN_PREVIEW_LONG_EDGE = 200

#: Re-encoded well below the compression loop's quality, because the preview
#: is not the deliverable and its bytes are not budgeted against a rule.
_PREVIEW_JPEG_QUALITY = 72

_WATERMARK_ANGLE_DEGREES = 30
#: White at this alpha stays readable over hair and over a light background
#: without hiding the face underneath it.
_INK_ALPHA = 140
#: A dark offset behind the white, so the mark survives over a pale background
#: where white alone would vanish.
_SHADOW_ALPHA = 70
_SHADOW_OFFSET = 2


class PreviewUnavailableError(Exception):
    """Raised when no preview can be made of a file.

    A PDF deliverable is the ordinary case: rendering a page needs a rasteriser
    this repository deliberately does not carry. The caller reports the absence
    rather than claiming a watermark it did not apply.
    """


@dataclass(frozen=True)
class WatermarkedPreview:
    """A preview, and what is true about it."""

    content: bytes
    media_type: str
    width: int
    height: int
    source_width: int
    source_height: int

    @property
    def is_reduced(self) -> bool:
        """Whether the preview is smaller than the file it was made from."""
        return (self.width, self.height) != (self.source_width, self.source_height)


def _preview_size(width: int, height: int) -> tuple[int, int]:
    """The preview's pixel size, from the finished file's."""
    long_edge = max(width, height)
    target_long = max(int(round(long_edge * _PREVIEW_SCALE)), _MIN_PREVIEW_LONG_EDGE)
    if target_long >= long_edge:
        return width, height
    factor = target_long / long_edge
    return max(1, int(round(width * factor))), max(1, int(round(height * factor)))


def _load_font(size: int) -> Union[ImageFont.ImageFont, ImageFont.FreeTypeFont]:
    """Pillow's bundled scalable font, at a size proportional to the image.

    ``load_default(size=...)`` arrived in Pillow 10.1; before it the only
    built-in font was a bitmap fixed at one size, which would put the same
    small mark on a 200 px signature and a 1200 px declaration. The floor in
    ``pyproject.toml`` is set for this.
    """
    return ImageFont.load_default(size=size)


def _tiled_mark(size: tuple[int, int], text: str) -> Image.Image:
    """The mark itself: one phrase, tiled across the whole frame at an angle.

    Tiled rather than placed, because a single mark in a corner is one crop
    away from being gone. The tile is drawn on a square as wide as the image's
    diagonal and then rotated, so that after rotation the image rectangle --
    whose corners sit on that square's inscribed circle -- is still covered
    edge to edge.
    """
    width, height = size
    short_edge = min(width, height)
    font = _load_font(max(11, short_edge // 11))

    left, top, right, bottom = font.getbbox(text)
    text_width = max(1, right - left)
    text_height = max(1, bottom - top)

    span = int(math.ceil(math.hypot(width, height))) + 2 * text_height
    canvas = Image.new("RGBA", (span, span), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    step_x = text_width + max(text_width // 3, text_height * 2)
    step_y = text_height * 3

    row = 0
    y = -text_height
    while y < span:
        # Every other row is offset by half a step, so the mark does not form
        # clean vertical corridors for an inpainting tool to follow.
        x = -text_width + (step_x // 2 if row % 2 else 0)
        while x < span:
            draw.text(
                (x + _SHADOW_OFFSET, y + _SHADOW_OFFSET),
                text,
                font=font,
                fill=(0, 0, 0, _SHADOW_ALPHA),
            )
            draw.text((x, y), text, font=font, fill=(255, 255, 255, _INK_ALPHA))
            x += step_x
        y += step_y
        row += 1

    rotated = canvas.rotate(_WATERMARK_ANGLE_DEGREES, resample=Image.BICUBIC)
    offset_x = (span - width) // 2
    offset_y = (span - height) // 2
    return rotated.crop((offset_x, offset_y, offset_x + width, offset_y + height))


def _flatten(image_bytes: bytes) -> tuple[Image.Image, int, int]:
    """Decode a finished file to RGB, over white where it carries alpha."""
    try:
        with Image.open(io.BytesIO(image_bytes)) as opened:
            opened.load()
            source_width, source_height = opened.size
            if opened.mode in ("RGBA", "LA", "P"):
                converted = opened.convert("RGBA")
                flattened = Image.new("RGB", converted.size, (255, 255, 255))
                flattened.paste(converted, mask=converted.split()[-1])
            else:
                flattened = opened.convert("RGB")
    except Exception as error:
        raise PreviewUnavailableError(
            "The finished file could not be decoded"
        ) from error
    return flattened, source_width, source_height


def render_watermarked_preview(
    image_bytes: bytes,
    *,
    text: str = DEFAULT_WATERMARK_TEXT,
    media_type: Optional[str] = None,
) -> WatermarkedPreview:
    """Make the watermarked, reduced-resolution preview of a finished file.

    ``media_type`` is the finished file's own, used only to refuse early on
    something that was never going to decode as an image.

    Raises ``PreviewUnavailableError`` when the file cannot be previewed. The caller
    must report that absence rather than fall back to the clean file, which is
    the failure DEC-063 exists to prevent.
    """
    if media_type is not None and not media_type.startswith("image/"):
        raise PreviewUnavailableError(f"No preview renderer for {media_type}")

    flattened, source_width, source_height = _flatten(image_bytes)
    if source_width < 1 or source_height < 1:
        raise PreviewUnavailableError("The finished file has no pixels")

    target = _preview_size(source_width, source_height)
    reduced = (
        flattened
        if target == (source_width, source_height)
        else flattened.resize(target, Image.LANCZOS)
    )

    marked = Image.alpha_composite(
        reduced.convert("RGBA"), _tiled_mark(reduced.size, text)
    ).convert("RGB")

    # Compositing does not carry EXIF forward, but ``info`` does travel: a JPEG
    # ``COM`` comment on the finished file was reaching the preview intact and
    # being written straight back out.  Cleared explicitly, because a preview
    # leaves the service as pixels and nothing else.
    marked.info.clear()
    buffer = io.BytesIO()
    marked.save(buffer, "JPEG", quality=_PREVIEW_JPEG_QUALITY, optimize=True)

    return WatermarkedPreview(
        content=buffer.getvalue(),
        media_type=PREVIEW_MEDIA_TYPE,
        width=marked.width,
        height=marked.height,
        source_width=source_width,
        source_height=source_height,
    )
