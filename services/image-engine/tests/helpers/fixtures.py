from pathlib import Path


def get_fixtures_dir() -> Path:
    """Dynamically locates the canonical tests/fixtures directory at the repository root."""
    current = Path(__file__).resolve().parent
    for _ in range(5):
        candidate = current / "tests" / "fixtures"
        if candidate.exists() and (candidate / "FIXTURE_MANIFEST.md").exists():
            return candidate
        current = current.parent
    raise RuntimeError("Canonical tests/fixtures directory not found.")


FIXTURES_DIR = get_fixtures_dir()
