"""Real progress for a preparation still running (DEC-075).

The interface wants a ring that fills while the photograph is made. The only
dishonest way to build that is a timer, so what is pinned here is that the
number comes from the work: it moves when a stage completes, it never goes
backwards, and it never reads full while the candidate is still waiting.
"""

import pytest
from fastapi.testclient import TestClient

from exam_photo.api.app import app
from exam_photo.api.jobs import JobRegistry
from exam_photo.api.progress import (
    STAGE_LABELS,
    STAGE_WEIGHTS,
    ProgressRegistry,
)
from exam_photo.api.settings import ApiSettings
from exam_photo.api.storage import LocalArtifactStore

client = TestClient(app, raise_server_exceptions=False)

TOKEN = "prg_abc123"


@pytest.fixture
def progress(tmp_path):
    return ProgressRegistry(tmp_path / "artifacts")


@pytest.fixture
def api(tmp_path):
    from exam_photo.api.app import service

    original = (service.settings, service.store, service.registry, service.progress)
    service.settings = ApiSettings(artifact_root=tmp_path / "artifacts")
    service.store = LocalArtifactStore(tmp_path / "artifacts")
    service.registry = JobRegistry(tmp_path / "artifacts")
    service.progress = ProgressRegistry(tmp_path / "artifacts")
    try:
        yield service
    finally:
        (
            service.settings,
            service.store,
            service.registry,
            service.progress,
        ) = original


# ----------------------------------------------------------------------
# The number comes from the work
# ----------------------------------------------------------------------


def test_progress_starts_at_nothing(progress):
    state = progress.start(TOKEN)

    assert state.fraction == 0.0
    assert state.finished is False


def test_each_completed_stage_moves_it(progress):
    progress.start(TOKEN)

    progress.advance(TOKEN, "input_normalization")
    first = progress.get(TOKEN).fraction
    progress.advance(TOKEN, "face_detection")
    second = progress.get(TOKEN).fraction

    assert 0.0 < first < second


def test_the_expensive_stages_carry_the_weight(progress):
    """Two BiRefNet inferences are about eight of the ten seconds, and the bar
    has to reflect that or it stalls for most of the wait."""
    heavy = STAGE_WEIGHTS["subject_segmentation"] + STAGE_WEIGHTS["mask_refinement"]

    assert heavy > 0.6
    assert STAGE_WEIGHTS["filename_generation"] < 0.01


def test_it_never_goes_backwards(progress):
    """A bar that retreats reads as a fault even when the work is fine."""
    progress.start(TOKEN)
    progress.advance(TOKEN, "subject_segmentation")
    high = progress.get(TOKEN).fraction

    progress.advance(TOKEN, "filename_generation")

    assert progress.get(TOKEN).fraction >= high


def test_a_repeated_stage_is_counted_once(progress):
    progress.start(TOKEN)
    progress.advance(TOKEN, "subject_segmentation")
    once = progress.get(TOKEN).fraction
    progress.advance(TOKEN, "subject_segmentation")

    assert progress.get(TOKEN).fraction == once


def test_it_never_reads_full_while_the_candidate_is_waiting(progress):
    """Only finishing may show 100%."""
    progress.start(TOKEN)
    for stage in STAGE_WEIGHTS:
        progress.advance(TOKEN, stage)

    assert progress.get(TOKEN).fraction <= 0.99
    assert progress.get(TOKEN).finished is False


def test_finishing_completes_it(progress):
    progress.start(TOKEN)
    progress.advance(TOKEN, "subject_segmentation")
    progress.finish(TOKEN)

    state = progress.get(TOKEN)
    assert state.fraction == 1.0
    assert state.finished is True
    assert state.failed is False


def test_a_failure_finishes_it_too(progress):
    """A poller must never be left watching a bar that will not move again."""
    progress.start(TOKEN)
    progress.finish(TOKEN, failed=True)

    state = progress.get(TOKEN)
    assert state.finished is True
    assert state.failed is True


def test_advancing_after_finishing_does_nothing(progress):
    progress.start(TOKEN)
    progress.finish(TOKEN)
    progress.advance(TOKEN, "subject_segmentation")

    assert progress.get(TOKEN).fraction == 1.0


# ----------------------------------------------------------------------
# What the candidate is told
# ----------------------------------------------------------------------


def test_every_weighted_stage_has_something_to_say():
    """ "Foreground decontamination" is precise and means nothing to anybody."""
    for stage in STAGE_WEIGHTS:
        assert stage in STAGE_LABELS
        assert STAGE_LABELS[stage][0].isupper()


def test_the_label_follows_the_stage(progress):
    progress.start(TOKEN)
    progress.advance(TOKEN, "subject_segmentation")

    assert progress.get(TOKEN).label == "Separating you from the background"


# ----------------------------------------------------------------------
# Robustness: progress may never cost a candidate their photograph
# ----------------------------------------------------------------------


def test_a_malformed_token_is_ignored_rather_than_raising(progress):
    assert progress.start("../../escape") is None
    progress.advance("../../escape", "subject_segmentation")  # must not raise
    progress.finish("../../escape")  # must not raise
    assert progress.get("../../escape") is None


def test_advancing_an_unknown_token_does_nothing(progress):
    progress.advance("prg_never_started", "subject_segmentation")

    assert progress.get("prg_never_started") is None


def test_a_corrupt_progress_file_reads_as_absent(progress):
    progress.start(TOKEN)
    (progress.root / f"{TOKEN}.json").write_text("{not json", encoding="utf-8")

    assert progress.get(TOKEN) is None


def test_stale_progress_is_swept(progress, tmp_path):
    import os
    import time

    progress.start(TOKEN)
    path = progress.root / f"{TOKEN}.json"
    old = time.time() - 10_000
    os.utime(path, (old, old))

    assert progress.sweep() == 1
    assert not path.exists()


def test_a_live_file_is_not_swept(progress):
    progress.start(TOKEN)

    assert progress.sweep() == 0
    assert progress.get(TOKEN) is not None


# ----------------------------------------------------------------------
# Over HTTP
# ----------------------------------------------------------------------


def test_polling_returns_the_state(api):
    api.progress.start(TOKEN)
    api.progress.advance(TOKEN, "face_detection")

    body = client.get(f"/v1/progress/{TOKEN}").json()

    assert body["stage"] == "face_detection"
    assert body["label"] == "Finding your face"
    assert 0.0 < body["fraction"] < 1.0


def test_an_unknown_token_is_404_not_a_zeroed_state(api):
    """ "Never heard of it" and "not started yet" are different answers, and a
    client that cannot tell them apart waits forever on a typo."""
    assert client.get("/v1/progress/prg_nothing").status_code == 404


def test_a_malformed_token_is_404_and_reads_no_file(api):
    assert client.get("/v1/progress/not-a-token").status_code == 404
