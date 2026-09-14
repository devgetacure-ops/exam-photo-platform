import re
from pathlib import Path
from typing import Optional, Sequence

from pydantic import BaseModel, ConfigDict

WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


class FilenameGenerationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_name: str = "exam_photo"
    extension: str = "jpg"
    max_length: int = 80
    allow_candidate_name: bool = False


def sanitize_filename_part(part: str) -> str:
    # Prohibit path separators and traversal
    if "/" in part or "\\" in part or ".." in part:
        raise ValueError("Path separators or traversal sequences are prohibited.")

    # Prohibit control characters
    part = "".join(ch for ch in part if ord(ch) >= 32 and ord(ch) != 127)

    # Allow only A-Z a-z 0-9 _ - .
    sanitized = re.sub(r"[^A-Za-z0-9_\-\.]", "_", part)
    return sanitized


def generate_safe_filename(
    name_suggestion: str,
    output_dir: Optional[Path] = None,
    overwrite: bool = False,
    config: Optional[FilenameGenerationConfig] = None,
) -> str:
    cfg = config or FilenameGenerationConfig()

    # Determine extension
    ext = cfg.extension.lower().strip().replace(".", "")
    if not ext:
        ext = "jpg"

    # Extract base name candidate
    base = name_suggestion.strip()
    if not base:
        base = cfg.base_name

    # Strip extension from the end of base if present
    if base.lower().endswith("." + ext):
        base = base[: -len("." + ext)]
    elif base.lower().endswith(".jpeg") and ext == "jpg":
        base = base[:-5]
    elif base.lower().endswith(".jpg") and ext == "jpeg":
        base = base[:-4]

    # Sanitize base name
    base = sanitize_filename_part(base)

    # Enforce PII protection (do not include email, roll number, etc.)
    # If the user suggested candidate information that looks like an email or roll number, fall back to default
    if "@" in name_suggestion or re.search(r"\b\d{6,}\b", name_suggestion):
        base = cfg.base_name

    # Check Windows reserved names
    if base.upper() in WINDOWS_RESERVED_NAMES:
        raise ValueError(f"Filename base '{base}' is a Windows reserved name.")

    # Truncate base name to satisfy max length constraints
    max_base_len = cfg.max_length - len(ext) - 1
    if max_base_len <= 0:
        raise ValueError(
            "Filename max_length config is too short to fit the extension."
        )

    if len(base) > max_base_len:
        base = base[:max_base_len]

    filename = f"{base}.{ext}"

    # Handle duplicates in output directory
    if output_dir is not None and not overwrite:
        out_path = Path(output_dir)
        if (out_path / filename).exists():
            counter = 1
            while True:
                suffix = f"_{counter:03d}"
                # Recalculate truncation for suffix
                tmp_max_base_len = max_base_len - len(suffix)
                tmp_base = base
                if len(tmp_base) > tmp_max_base_len:
                    tmp_base = tmp_base[:tmp_max_base_len]
                candidate = f"{tmp_base}{suffix}.{ext}"
                if not (out_path / candidate).exists():
                    filename = candidate
                    break
                counter += 1

    return filename


# ---------------------------------------------------------------------------
# The standard name for a file an examination does not name itself
# ---------------------------------------------------------------------------

#: The word for each kind of file. Anything else -- a certificate, an identity
#: document -- is named by its requirement, because "certificate" alone would
#: not tell a Class X marksheet from a caste certificate in a downloads folder.
_FILE_WORD = {
    "photograph": "photo",
    "signature": "signature",
    "thumb_impression": "thumb",
    "handwritten_declaration": "declaration",
}
_PREFIX_MAX = 16
_WORD_MAX = 24

#: Where an examination's own short form reads badly in a file name, keyed by
#: exam_id. The generated list is reviewed by the owner; corrections go here.
FILE_PREFIX_OVERRIDES: dict[str, str] = {}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _trim_words(slug: str, limit: int) -> str:
    if len(slug) <= limit:
        return slug
    cut = slug[:limit]
    if "-" in cut:
        cut = cut[: cut.rindex("-")]
    return cut.strip("-")


def exam_file_prefix(exam_id: str, aliases: Sequence[str]) -> str:
    """The examination part of a file name: its short form, as candidates type it."""
    if exam_id in FILE_PREFIX_OVERRIDES:
        return FILE_PREFIX_OVERRIDES[exam_id]
    for alias in aliases:
        slug = _slug(alias)
        if slug and len(slug) <= _PREFIX_MAX:
            return slug
    return _trim_words(_slug(exam_id), _PREFIX_MAX) or "exam"


def standard_file_stem(
    exam_id: str,
    aliases: Sequence[str],
    requirement_type: str,
    requirement_id: Optional[str] = None,
    same_type_count: int = 1,
) -> str:
    """``<exam>_<file>``, e.g. ``neet-ug_photo``, for a file with no published name.

    A published exact name always wins over this; see the callers. Two files of
    one kind in the same application (an English and a Hindi signature) are
    told apart by their requirement, so the archive never holds two of a name.
    """
    word = _FILE_WORD.get(requirement_type)
    if word is None or (same_type_count > 1 and requirement_id):
        base = re.sub(r"^candidate[_-]", "", requirement_id or requirement_type)
        word = _trim_words(_slug(base), _WORD_MAX) or _slug(requirement_type)
    return f"{exam_file_prefix(exam_id, aliases)}_{word}"


def standard_file_stems(
    exam_id: str,
    aliases: Sequence[str],
    requirements: Sequence[tuple[str, str]],
) -> dict[str, str]:
    """Standard stems for every ``(requirement_type, requirement_id)`` of one exam.

    Unique across the application. Two requirements whose names still meet
    after trimming -- Karnataka PSC lists two claim-supporting certificates --
    are numbered in the order the examination lists them, so a ZIP never
    carries two files of one name.
    """
    type_counts: dict[str, int] = {}
    for requirement_type, _ in requirements:
        type_counts[requirement_type] = type_counts.get(requirement_type, 0) + 1
    stems: dict[str, str] = {}
    seen: dict[str, int] = {}
    for requirement_type, requirement_id in requirements:
        stem = standard_file_stem(
            exam_id,
            aliases,
            requirement_type,
            requirement_id,
            type_counts[requirement_type],
        )
        seen[stem] = seen.get(stem, 0) + 1
        if seen[stem] > 1:
            stem = f"{stem}-{seen[stem]}"
        stems[requirement_id] = stem
    return stems
