"""Shared API test setup."""

import pytest


@pytest.fixture(autouse=True)
def _fresh_rate_limits():
    """Each test starts with empty rate-limit windows (DEC-134).

    The service is module-level, so without this a suite that prepares many
    files from one kit would trip the hourly limit partway through.
    """
    from exam_photo.api.app import service

    service._kit_rate_limit._hits.clear()
    service._ip_rate_limit._hits.clear()
    yield
