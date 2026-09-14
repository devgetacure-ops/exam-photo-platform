"""The only image the browser is given before payment (DEC-063, amended).

The candidate has to be able to judge what was made for them before they buy
it, and the platform has to still have something to sell afterwards. The
first version leaned too far towards the second: half resolution at JPEG
quality 72 looked soft, and the owner's concern (testing note B) was that a
blurry preview reads as a blurry product and loses the sale. So the preview is
now sharp on any screen, and the protection is carried by the mark:

- **Never the file's own size.** The preview's long edge is a fixed display
  size, never the finished file's pixel dimensions, so it cannot meet an
  examination's pixel specification even if the mark were somehow removed.
- **A mark that says what the file is.** Tiled over the whole frame at two
  angles, crossing the face and every edge: PREVIEW ONLY, NOT FOR SUBMISSION,
  and the examination, dimensions, size, format and filename of the file being
  sold -- so it is different for every examination and every file, and an
  escaped copy names itself. Removing marks that cross a face damages the face,
  which is what makes removal pointless.

Burned in is still the whole point: the mark is rasterised into a re-encoded
image, so there is no layer to strip and no original underneath it.

A PDF deliverable now gets a preview of its first page, rendered with
pypdfium2 (Apache-2.0 / BSD-3-Clause). DEC-052 governs the *delivered* file,
which is never re-rendered; a picture of page one for the candidate to judge
is a different thing.

Nothing here knows about jobs, payment or HTTP. It takes the bytes of a
finished file and returns the bytes of its preview.
"""

import io
import math
import re
from dataclasses import dataclass
from typing import Optional, Sequence, Union

from PIL import Image, ImageDraw, ImageFont

#: Previews are always JPEG. The output may carry transparency; the preview is
#: flattened onto white before it is marked, so a candidate never judges their
#: photograph against whatever the browser happens to paint behind it.
PREVIEW_MEDIA_TYPE = "image/jpeg"

#: The name the preview is stored under, inside the job directory.
PREVIEW_FILENAME = "preview.jpg"

#: The fixed words of the mark. The file's own details follow them.
DEFAULT_WATERMARK_TEXT = "PREVIEW ONLY - NOT FOR SUBMISSION"

#: The preview's long edge. Large enough to be sharp at any size the page shows
#: it, on a high-density phone screen too; and a constant, so it is never the
#: finished file's own dimensions.
PREVIEW_LONG_EDGE = 800

#: Used instead when the finished file's long edge is exactly the constant, so
#: the preview still cannot be the file's size.
_PREVIEW_LONG_EDGE_ALTERNATE = 760

#: The preview is not the deliverable and its bytes are not budgeted against a
#: rule, so it is encoded for sharpness.
_PREVIEW_JPEG_QUALITY = 88

_WATERMARK_ANGLE_DEGREES = 30
_CROSSING_ANGLE_DEGREES = -30
#: White at this alpha stays readable over hair and a light background without
#: hiding the face underneath it.
_INK_ALPHA = 130
#: The crossing pass is lighter, so the two together cover the frame without
#: turning the face grey.
_CROSSING_INK_ALPHA = 85
#: A dark offset behind the white, so the mark survives over a pale background
#: where white alone would vanish.
_SHADOW_ALPHA = 70
_SHADOW_OFFSET = 2


class PreviewUnavailableError(Exception):
    """Raised when no preview can be made of a file.

    The caller reports the absence rather than claiming a watermark it did not
    apply, and never falls back to the clean file.
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
        """Whether the preview's pixel size differs from the file it was made from."""
        return (self.width, self.height) != (self.source_width, self.source_height)


def _preview_size(width: int, height: int) -> tuple[int, int]:
    """The preview's pixel size: a fixed long edge, the file's own shape."""
    long_edge = max(width, height)
    target_long = (
        _PREVIEW_LONG_EDGE_ALTERNATE
        if long_edge == PREVIEW_LONG_EDGE
        else PREVIEW_LONG_EDGE
    )
    factor = target_long / long_edge
    return max(1, int(round(width * factor))), max(1, int(round(height * factor)))


def watermark_line(text: str, details: Sequence[str]) -> str:
    """The mark's words: the fixed phrase, then the file's details, in ASCII.

    ASCII only, because the mark is drawn in Pillow's bundled font, where a
    missing glyph would silently become a box.
    """
    parts = [text, *[d for d in details if d and d.strip()]]
    joined = " - ".join(part.strip() for part in parts)
    joined = joined.replace("×", "x").replace("–", "-").replace("—", "-")
    return re.sub(r"[^\x20-\x7e]", "", joined)


def _load_font(size: int) -> Union[ImageFont.ImageFont, ImageFont.FreeTypeFont]:
    """Pillow's bundled scalable font (``pyproject.toml`` pins Pillow for it)."""
    return ImageFont.load_default(size=size)


def _tiled_mark(
    size: tuple[int, int],
    text: str,
    angle: float,
    ink_alpha: int,
    font_divisor: int,
) -> Image.Image:
    """One phrase, tiled across the whole frame at an angle.

    Drawn on a square as wide as the image's diagonal and then rotated, so the
    image rectangle is still covered edge to edge after rotation.
    """
    width, height = size
    short_edge = min(width, height)
    font = _load_font(max(12, short_edge // font_divisor))

    left, top, right, bottom = font.getbbox(text)
    text_width = max(1, right - left)
    text_height = max(1, bottom - top)

    span = int(math.ceil(math.hypot(width, height))) + 2 * text_height
    canvas = Image.new("RGBA", (span, span), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    step_x = text_width + text_height * 3
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
            draw.text((x, y), text, font=font, fill=(255, 255, 255, ink_alpha))
            x += step_x
        y += step_y
        row += 1

    rotated = canvas.rotate(angle, resample=Image.BICUBIC)
    offset_x = (span - width) // 2
    offset_y = (span - height) // 2
    return rotated.crop((offset_x, offset_y, offset_x + width, offset_y + height))


def _flatten(image_bytes: bytes) -> tuple[Image.Image, int, int]:
    """Decode a finished image to RGB, over white where it carries alpha."""
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


def _first_pdf_page(pdf_bytes: bytes) -> tuple[Image.Image, int, int]:
    """Page one of a PDF as an image, for the candidate to judge.

    The size reported as the source is the page's own in points, which is never
    a pixel specification, so the preview is always "reduced" from it.
    """
    try:
        import pypdfium2 as pdfium
    except ImportError as error:  # pragma: no cover - dependency is declared
        raise PreviewUnavailableError("No PDF renderer is installed") from error
    try:
        document = pdfium.PdfDocument(pdf_bytes)
        try:
            if len(document) < 1:
                raise PreviewUnavailableError("The PDF has no pages")
            page = document[0]
            page_width, page_height = page.get_size()
            long_points = max(page_width, page_height) or 1.0
            scale = PREVIEW_LONG_EDGE / long_points
            bitmap = page.render(scale=scale)
            image = bitmap.to_pil().convert("RGB")
            return image, int(round(page_width)), int(round(page_height))
        finally:
            document.close()
    except PreviewUnavailableError:
        raise
    except Exception as error:
        raise PreviewUnavailableError("The PDF could not be rendered") from error


def render_watermarked_preview(
    image_bytes: bytes,
    *,
    text: str = DEFAULT_WATERMARK_TEXT,
    details: Sequence[str] = (),
    media_type: Optional[str] = None,
) -> WatermarkedPreview:
    """Make the watermarked preview of a finished image or PDF.

    ``details`` are the file's own facts -- examination, dimensions, size,
    format, filename -- added to the mark after the fixed words.

    Raises ``PreviewUnavailableError`` when the file cannot be previewed. The
    caller must report that absence rather than fall back to the clean file.
    """
    is_pdf = image_bytes.startswith(b"%PDF-") or media_type == "application/pdf"
    if not is_pdf and media_type is not None and not media_type.startswith("image/"):
        raise PreviewUnavailableError(f"No preview renderer for {media_type}")

    if is_pdf:
        source, source_width, source_height = _first_pdf_page(image_bytes)
    else:
        source, source_width, source_height = _flatten(image_bytes)
    if source_width < 1 or source_height < 1:
        raise PreviewUnavailableError("The finished file has no pixels")

    if is_pdf:
        # Rendered straight at the display size; a page's size in points is
        # never a pixel specification, so there is nothing to step away from.
        display = source
    else:
        target = _preview_size(source.width, source.height)
        display = source.resize(target, Image.LANCZOS)

    line = watermark_line(text, details)
    marked = Image.alpha_composite(
        display.convert("RGBA"),
        _tiled_mark(display.size, line, _WATERMARK_ANGLE_DEGREES, _INK_ALPHA, 24),
    )
    marked = Image.alpha_composite(
        marked,
        _tiled_mark(
            display.size,
            watermark_line(text, ()),
            _CROSSING_ANGLE_DEGREES,
            _CROSSING_INK_ALPHA,
            16,
        ),
    ).convert("RGB")

    # Compositing does not carry EXIF forward, but ``info`` does travel: a JPEG
    # ``COM`` comment on the finished file once reached the preview intact.
    # Cleared explicitly, because a preview leaves the service as pixels only.
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
