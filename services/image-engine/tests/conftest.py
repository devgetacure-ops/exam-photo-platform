from typing import Any
import pytest
import sys

# Track skipped mandatory segmentation tests
_skipped_mandatory_nodes: list[str] = []


def pytest_runtest_makereport(item: Any, call: Any) -> None:
    if call.excinfo is not None and call.excinfo.errisinstance(pytest.skip.Exception):
        if item.get_closest_marker("mandatory_segmentation"):
            _skipped_mandatory_nodes.append(item.nodeid)


def pytest_sessionfinish(session: Any, exitstatus: Any) -> None:
    if _skipped_mandatory_nodes:
        print(
            "\nERROR: Mandatory segmentation test(s) were skipped!\n"
            "Skipped tests:\n"
            + "\n".join(f"  - {node}" for node in _skipped_mandatory_nodes),
            file=sys.stderr,
        )
        session.exitstatus = 1
