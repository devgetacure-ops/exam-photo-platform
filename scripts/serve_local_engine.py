"""Run the engine API for manually testing the web app on this machine.

Optional settings come from ``services/image-engine/.env.local``, which git
ignores: one ``KEY=value`` per line. Test-mode keys for Razorpay, SMTP or
Turnstile go there, in a file that is never committed and never pasted into a
command. Only the names of what was loaded are printed, never the values.

Browser access from the local web app is switched on unless the file says
otherwise. Everything else takes the engine's own defaults, including the
purchase gate, so what you test is what a candidate would get.
"""

import os
import runpy
import sys
from pathlib import Path

ENGINE_ROOT = Path(__file__).resolve().parent.parent / "services" / "image-engine"
ENV_FILE = ENGINE_ROOT / ".env.local"


def load_env_file(path: Path) -> list[str]:
    """Load KEY=value lines into the environment; return the keys loaded."""
    loaded: list[str] = []
    if not path.is_file():
        return loaded
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key or not value:
            continue
        os.environ.setdefault(key, value)
        loaded.append(key)
    return loaded


def main() -> None:
    names = load_env_file(ENV_FILE)
    os.environ.setdefault("EXAM_PHOTO_LOCAL_CORS_ENABLED", "true")
    print(
        "Settings loaded from .env.local: "
        + (", ".join(sorted(names)) if names else "none (engine defaults)"),
        flush=True,
    )
    os.chdir(ENGINE_ROOT)
    sys.argv = ["exam_photo", "serve-api", "--host", "127.0.0.1", "--port", "8000"]
    runpy.run_module("exam_photo", run_name="__main__", alter_sys=True)


if __name__ == "__main__":
    main()
