from typing import Optional


def detect_signature_format(data: bytes) -> Optional[str]:
    """Inspects file headers to detect standard formats.

    Returns "jpeg", "png", or None if signature is unsupported.
    """
    if len(data) >= 3 and data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if len(data) >= 8 and data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if len(data) >= 4 and data.startswith(b"GIF8"):
        return "gif"
    return None
