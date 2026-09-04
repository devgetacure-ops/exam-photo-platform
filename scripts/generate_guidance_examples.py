"""Generate the accepted/rejected example images used on the exam pages.

Why photographs rather than drawings: a candidate is judging their own photo
against a standard, and a diagram of a head in a box cannot tell them whether
*theirs* is cropped too tight. A photograph can.

Why one portrait rather than several: every "wrong" example is derived from the
same source frame, so framing is the only thing that differs between them. A
gallery of different people would let a reader attribute the difference to the
person instead of to the mistake.

The source is `assets/reference-portrait.jpg` -- a synthetic (GAN-generated)
face, not a photograph of any living person, so no real likeness is used to
advertise a commercial service. See `assets/README.md` for its provenance and
for why the portraits under `tests/fixtures/` must never be used here: every
one of those was chosen as an engine EDGE CASE (a side profile, a turban,
spectacles, low contrast), so using one as the ideal teaches the reverse of
the rule.

Known gap: the reference face is European. The audience is Indian candidates
and the ideal photo should look like someone they recognise. The generator
that produced it ignored its own age filter on non-default ethnicities and
returned children, so this is a placeholder to be replaced rather than a
settled choice -- drop a better portrait at the same path and re-run.

    python scripts/generate_guidance_examples.py

The script refuses to run without the source rather than falling back to a
fixture, because a wrong "ideal" is worse than a missing one.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

REPO_ROOT = Path(__file__).resolve().parents[1]
#: The ideal reference photograph. Deliberately *not* a `tests/fixtures/`
#: portrait -- those are engine edge cases, not the standard to match.
SOURCE = REPO_ROOT / "assets" / "reference-portrait.jpg"
OUT_DIR = REPO_ROOT / "apps" / "web" / "public" / "examples"

#: Small on purpose -- these sit beside a form and only have to communicate
#: framing. The 3:4 ratio matches the reference portrait exactly: resizing a
#: 3:4 source into a 4:5 tile squashes the face, and a platform whose first
#: principle is "never distort to hit a target" cannot ship a stretched
#: example of the thing it refuses to do.
TILE = (240, 320)
QUALITY = 82


def _passport_crop(source: Image.Image) -> Image.Image:
    """The reference, at tile size.

    The source portrait is already the ideal composition -- head centred, a
    margin above the hair, shoulders meeting the bottom edge, plain ground --
    so this is a resize rather than a crop. Everything below derives its
    mistake from *this* frame, which is what keeps framing the only variable
    between the examples.
    """
    return source.resize(TILE, Image.LANCZOS)


def _too_far(source: Image.Image) -> Image.Image:
    """The most common mistake: a full-body or half-body shot."""
    good = _passport_crop(source)
    canvas = Image.new("RGB", TILE, (232, 232, 230))
    small = good.resize((int(TILE[0] * 0.42), int(TILE[1] * 0.42)), Image.LANCZOS)
    canvas.paste(small, ((TILE[0] - small.width) // 2, int(TILE[1] * 0.12)))
    return canvas


def _too_tight(source: Image.Image) -> Image.Image:
    """Cropped into the hair and chin, which most portals reject."""
    width, height = source.size
    box = (
        int(width * 0.17),
        int(height * 0.17),
        int(width * 0.83),
        int(height * 0.72),
    )
    return source.crop(box).resize(TILE, Image.LANCZOS)


def _blurred(source: Image.Image) -> Image.Image:
    return _passport_crop(source).filter(ImageFilter.GaussianBlur(radius=2.6))


def _too_dark(source: Image.Image) -> Image.Image:
    return ImageEnhance.Brightness(_passport_crop(source)).enhance(0.42)


def _side_shadow(source: Image.Image) -> Image.Image:
    """Uneven light across the face -- a named rejection cause on many exams."""
    good = _passport_crop(source).convert("RGB")
    shadow = Image.new("L", TILE, 255)
    draw = ImageDraw.Draw(shadow)
    for x in range(TILE[0]):
        # A smooth ramp across the whole width. A steep one reads as a pasted
        # band rather than as light falling unevenly on a face.
        ratio = x / (TILE[0] - 1)
        value = int(255 * (0.30 + 0.70 * ratio**1.4))
        draw.line([(x, 0), (x, TILE[1])], fill=min(255, value))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=26))
    black = Image.new("RGB", TILE, (0, 0, 0))
    return Image.composite(good, black, shadow)


def _pen(
    draw: ImageDraw.ImageDraw,
    control: list[tuple[float, float]],
    start_width: float,
    end_width: float,
    slant: float = 0.18,
) -> list[tuple[float, float]]:
    """Stroke a Bezier with a width that tapers, like a pen leaving paper.

    Constant-width lines are what make a drawn "signature" read as a squiggle:
    real handwriting varies with pressure and speed. The slant shears the whole
    stroke, which is what gives cursive its forward lean.
    """
    n = len(control) - 1
    steps = 110
    points: list[tuple[float, float]] = []
    for step in range(steps + 1):
        t_ = step / steps
        x = y = 0.0
        for index, (px, py) in enumerate(control):
            basis = math.comb(n, index) * (t_**index) * ((1 - t_) ** (n - index))
            x += px * basis
            y += py * basis
        points.append((x - y * slant, y))

    for index in range(len(points) - 1):
        ratio = index / max(1, len(points) - 2)
        width = max(1.0, start_width + (end_width - start_width) * ratio)
        draw.line([points[index], points[index + 1]], fill=(16, 16, 24), width=int(round(width)))
        # Round the joins so a tapering stroke does not read as facets.
        if width > 2:
            r = width / 2
            cx, cy = points[index]
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(16, 16, 24))
    return points


def _signature(good: bool) -> Image.Image:
    """A signature written as a signature.

    Composed as cursive letterforms with tapering strokes and a forward slant,
    rather than an abstract wave -- a candidate comparing their own signature
    against this has to recognise it as handwriting for the comparison to mean
    anything.

    The rejected variant is the same mark running off the edge of the paper.
    That is the one failure the ink pipeline cannot repair: a clipped stroke is
    no longer the candidate's signature, and no amount of cleaning restores it.
    """
    size = (420, 170)
    canvas = Image.new("RGB", size, (255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    # Written off the left edge for the rejected variant.
    dx = -104.0 if not good else 0.0
    base = 112.0

    def at(x: float, y: float) -> tuple[float, float]:
        return (x + dx, y)

    # Capital R: stem, bowl, leg.
    _pen(draw, [at(74, 42), at(66, 74), at(60, 100), at(58, base)], 3.0, 5.0)
    _pen(draw, [at(74, 44), at(112, 34), at(120, 66), at(80, 74)], 4.5, 3.0)
    _pen(draw, [at(84, 74), at(104, 86), at(112, 100), at(126, base + 4)], 3.0, 4.5)

    # Connecting run into a cursive "a".
    _pen(draw, [at(126, base + 4), at(140, 96), at(150, 78), at(162, 76)], 4.0, 3.0)
    _pen(draw, [at(162, 76), at(140, 78), at(138, 108), at(164, 104)], 3.0, 3.5)
    _pen(draw, [at(164, 76), at(168, 92), at(166, 104), at(176, base)], 3.0, 4.0)

    # "n" -- two shoulders.
    _pen(draw, [at(176, base), at(182, 92), at(184, 78), at(190, 76)], 3.5, 3.0)
    _pen(draw, [at(190, 76), at(204, 74), at(206, 92), at(206, base)], 3.0, 3.5)
    _pen(draw, [at(206, 96), at(212, 78), at(224, 74), at(230, 96)], 3.0, 3.5)

    # Trailing flourish that lifts away, as a real hand does.
    _pen(draw, [at(230, 96), at(262, 116), at(300, 74), at(348, 60)], 4.0, 1.2)

    # Underline swash, thinning to nothing.
    _pen(draw, [at(66, 136), at(150, 150), at(250, 138), at(340, 122)], 3.2, 1.0, slant=0.0)

    if not good:
        # The paper edge the mark has run past.
        draw.line([(0, 0), (0, size[1])], fill=(210, 210, 210), width=2)
    return canvas


def main() -> int:
    if not SOURCE.exists():
        print(f"No reference portrait at {SOURCE}.")
        print()
        print("It must be the photo a candidate should be trying to match:")
        print("  - facing the camera square on, looking into the lens")
        print("  - neutral expression, eyes open, nothing covering the face")
        print("  - even light, no shadow across the face")
        print("  - plain light background")
        print("  - head and shoulders, portrait orientation, >= 800px tall")
        print()
        print("A synthetic/AI-generated face is preferred: no real person's")
        print("likeness is then used to advertise a commercial service.")
        print()
        print("Refusing to fall back to a test fixture -- those are engine edge")
        print("cases (side profile, turban, spectacles), and a wrong 'ideal'")
        print("teaches the wrong lesson.")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source = Image.open(SOURCE).convert("RGB")

    outputs = {
        "photo-good.jpg": _passport_crop(source),
        "photo-too-far.jpg": _too_far(source),
        "photo-too-tight.jpg": _too_tight(source),
        "photo-blurred.jpg": _blurred(source),
        "photo-too-dark.jpg": _too_dark(source),
        "photo-shadow.jpg": _side_shadow(source),
        "signature-good.jpg": _signature(good=True),
        "signature-clipped.jpg": _signature(good=False),
    }

    for name, image in outputs.items():
        path = OUT_DIR / name
        image.save(path, "JPEG", quality=QUALITY, optimize=True)
        print(f"{name:26s} {path.stat().st_size / 1024:6.1f} KB")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
