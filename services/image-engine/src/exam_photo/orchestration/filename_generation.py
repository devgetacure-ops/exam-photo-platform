import re
from pathlib import Path
from typing import Optional

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
