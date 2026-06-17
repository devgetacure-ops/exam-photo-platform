"""Test package foundation boundaries and contract configurations."""

import pytest

from exam_photo import __version__, process_candidate_photo, validate_compliance


def test_package_metadata() -> None:
    """Verify package exposes correct metadata version."""
    assert __version__ == "0.1.0"


def test_process_photo_raises_not_implemented() -> None:
    """Verify image processing endpoint raises NotImplementedError."""
    with pytest.raises(NotImplementedError) as exc_info:
        process_candidate_photo(b"fake-data", {})
    assert "not implemented in Milestone 2" in str(exc_info.value)


def test_validate_compliance_raises_not_implemented() -> None:
    """Verify validation reporter endpoint raises NotImplementedError."""
    with pytest.raises(NotImplementedError) as exc_info:
        validate_compliance(b"fake-data", {})
    assert "not implemented in Milestone 2" in str(exc_info.value)
