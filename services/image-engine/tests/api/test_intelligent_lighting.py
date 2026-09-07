"""The candidate's control over the lighting correction (DEC-074).

The correction itself is DEC-043 and is already calibrated and tested. What is
new is that it is now the candidate's decision, taken before they pay, and
that the service says what it actually did rather than only that the switch
was on.

Three properties, and the middle one is the whole point of the feature:

* **Off means untouched.** Not "a smaller correction" -- none.
* **On does not mean changed.** A photograph that needs nothing gets nothing,
  and the response says so, which is what lets the interface tell a candidate
  their photograph was already good.
* **The choice is recorded**, because they made it before paying and what they
  bought must be what they previewed.
"""

from unittest.mock import patch

import pytest

from exam_photo.api.jobs import JobRegistry
from exam_photo.api.service import ApiProcessingService
from exam_photo.api.settings import ApiSettings
from exam_photo.api.storage import LocalArtifactStore
from exam_photo.orchestration.rule_pipeline import RulePipelineConfig
from exam_photo.suitability.enhancement_planner import (
    EnhancementPlan,
    FaceToneMeasurements,
    plan_enhancement,
)


@pytest.fixture
def api(tmp_path):
    """A service against a temporary root. No pipeline is ever built."""
    settings = ApiSettings(artifact_root=tmp_path / "artifacts")
    service = ApiProcessingService(settings)
    service.store = LocalArtifactStore(tmp_path / "artifacts")
    service.registry = JobRegistry(tmp_path / "artifacts")
    return service


def _healthy() -> FaceToneMeasurements:
    """A correctly exposed face with nothing wrong with it."""
    return FaceToneMeasurements(
        mean_luminance=128.0,
        tonal_range_p5_p95=160.0,
        shadow_clipped_fraction=0.0,
        highlight_clipped_fraction=0.0,
        blue_minus_red=-60.0,
        sharpness=140.0,
    )


def _flat() -> FaceToneMeasurements:
    """A hazy, low-contrast capture -- a defect, not a subject."""
    return FaceToneMeasurements(
        mean_luminance=120.0,
        tonal_range_p5_p95=40.0,
        shadow_clipped_fraction=0.0,
        highlight_clipped_fraction=0.0,
        blue_minus_red=-60.0,
        sharpness=140.0,
    )


# ----------------------------------------------------------------------
# The default, and what it means
# ----------------------------------------------------------------------


def test_the_correction_is_on_by_default():
    """Safe to default on precisely because it declines to touch a good photo."""
    assert RulePipelineConfig().enhancement_enabled is True


def test_a_photograph_that_needs_nothing_is_left_alone():
    """The owner's requirement, and the reason the default can be on."""
    plan = plan_enhancement(_healthy())

    assert plan.is_noop
    assert plan.applied == []
    assert plan.brightness_adjustment == 1.0
    assert plan.contrast_adjustment == 1.0
    assert plan.sharpness_adjustment == 1.0


def test_a_photograph_with_a_real_defect_is_corrected():
    plan = plan_enhancement(_flat())

    assert not plan.is_noop
    assert plan.applied


def test_a_correction_never_exceeds_its_cap():
    """Identity preservation: enough to help, never enough to look processed."""
    plan = plan_enhancement(_flat())

    assert 0.88 <= plan.brightness_adjustment <= 1.12
    assert 0.88 <= plan.contrast_adjustment <= 1.12
    assert 0.80 <= plan.sharpness_adjustment <= 1.20


def test_applying_a_noop_plan_returns_the_image_untouched():
    from PIL import Image

    image = Image.new("RGB", (16, 16), (120, 90, 70))
    from exam_photo.suitability.enhancement_planner import apply_enhancement

    assert apply_enhancement(image, EnhancementPlan()) is image


# ----------------------------------------------------------------------
# The switch reaches the pipeline
# ----------------------------------------------------------------------


def test_the_config_carries_the_candidates_choice():
    assert RulePipelineConfig(enhancement_enabled=False).enhancement_enabled is False


def test_the_switch_reaches_the_pipeline_config_from_the_http_form(api, tmp_path):
    """The wiring this change actually added: form field -> service -> config.

    Captures the `RulePipelineConfig` the service builds, because that is the
    thing the pipeline reads. A flag that stops anywhere short of it is a
    toggle that does nothing, which is the failure worth catching.
    """
    seen: list = []

    class CapturingPipeline:
        def process_rule(self, image_bytes, rule_dict, config):
            seen.append(config)
            raise RuntimeError("stop here: the config is what we came for")

    with patch.object(
        ApiProcessingService, "_get_pipeline", return_value=CapturingPipeline()
    ):
        api.process_job_sync(
            job_id="job_off",
            image_bytes=b"not-a-real-image",
            rule_dict={},
            enhancement_enabled=False,
        )

    assert seen and seen[0].enhancement_enabled is False


def test_the_switch_defaults_on_through_the_same_path(api):
    seen: list = []

    class CapturingPipeline:
        def process_rule(self, image_bytes, rule_dict, config):
            seen.append(config)
            raise RuntimeError("stop here")

    with patch.object(
        ApiProcessingService, "_get_pipeline", return_value=CapturingPipeline()
    ):
        api.process_job_sync(job_id="job_on", image_bytes=b"x", rule_dict={})

    assert seen and seen[0].enhancement_enabled is True


def test_the_choice_is_recorded_on_the_job(api):
    """They chose before paying, so what they bought must be what they saw."""

    class CapturingPipeline:
        def process_rule(self, image_bytes, rule_dict, config):
            raise RuntimeError("stop here")

    with patch.object(
        ApiProcessingService, "_get_pipeline", return_value=CapturingPipeline()
    ):
        api.process_job_sync(
            job_id="job_rec",
            image_bytes=b"x",
            rule_dict={},
            enhancement_enabled=False,
        )

    assert api.registry.get_job("job_rec").enhancement_enabled is False


def test_the_gate_is_read_from_the_config_not_hardcoded():
    """Guards against the flag being added and then never consulted."""
    import inspect

    import exam_photo.orchestration.rule_pipeline as pipeline_module

    source = inspect.getsource(pipeline_module)
    assert "if config.enhancement_enabled" in source


# ----------------------------------------------------------------------
# What is not negotiable
# ----------------------------------------------------------------------


def test_a_correctly_exposed_dark_subject_is_never_lightened():
    """Identity preservation. The trigger is compressed range, not luminance."""
    dark_but_correct = FaceToneMeasurements(
        mean_luminance=62.0,
        tonal_range_p5_p95=150.0,
        shadow_clipped_fraction=0.0,
        highlight_clipped_fraction=0.0,
        blue_minus_red=-55.0,
        sharpness=140.0,
    )

    plan = plan_enhancement(dark_but_correct)

    assert plan.is_noop
    assert plan.brightness_adjustment == 1.0


@pytest.mark.parametrize("luminance", [40.0, 70.0, 100.0, 160.0, 200.0])
def test_no_luminance_alone_triggers_a_correction(luminance):
    """No absolute target: a face is never driven toward a preferred brightness."""
    measurements = FaceToneMeasurements(
        mean_luminance=luminance,
        tonal_range_p5_p95=150.0,
        shadow_clipped_fraction=0.0,
        highlight_clipped_fraction=0.0,
        blue_minus_red=-55.0,
        sharpness=140.0,
    )

    assert plan_enhancement(measurements).is_noop


# ----------------------------------------------------------------------
# Switching between the two variants, instantly (DEC-076)
# ----------------------------------------------------------------------


def _prepared_with_both(api, job_id="job_var"):
    """A finished job holding both lighting variants, as the pipeline leaves it."""
    from exam_photo.api.contracts import ApiJobStatus

    record = api.registry.create_job(job_id, 1800)
    record.status = ApiJobStatus.SUCCEEDED
    record.requirement_type = "photograph"
    record.output_filename = "UPSC_photograph.jpg"
    record.output_media_type = "image/jpeg"
    record.alternate_output_filename = "UPSC_photograph__alt.jpg"
    record.enhancement_enabled = True
    record.enhancements_applied = ["Lifted a flat, low-contrast capture"]
    api.store.write_file(job_id, "UPSC_photograph.jpg", b"ENHANCED-BYTES")
    api.store.write_file(job_id, "UPSC_photograph__alt.jpg", b"PLAIN-BYTES-XX")
    api.registry.update_job(record)
    return record


def test_switching_exchanges_the_contents(api):
    record = _prepared_with_both(api)

    api.set_enhancement(record, False)

    assert api.store.read_file("job_var", "UPSC_photograph.jpg") == b"PLAIN-BYTES-XX"
    assert (
        api.store.read_file("job_var", "UPSC_photograph__alt.jpg") == b"ENHANCED-BYTES"
    )


def test_switching_keeps_the_examinations_required_filename(api):
    """The trap. Several portals reject an upload on its name alone, so a
    variant switch must never change what the delivered file is called."""
    record = _prepared_with_both(api)

    api.set_enhancement(record, False)

    assert record.output_filename == "UPSC_photograph.jpg"
    assert "__alt" not in record.output_filename


def test_switching_back_restores_the_original(api):
    record = _prepared_with_both(api)

    api.set_enhancement(record, False)
    api.set_enhancement(record, True)

    assert api.store.read_file("job_var", "UPSC_photograph.jpg") == b"ENHANCED-BYTES"
    assert record.enhancement_enabled is True


def test_switching_records_the_new_size(api):
    record = _prepared_with_both(api)

    api.set_enhancement(record, False)

    assert record.output_byte_size == len(b"PLAIN-BYTES-XX")


def test_switching_to_what_is_already_selected_does_nothing(api):
    record = _prepared_with_both(api)

    api.set_enhancement(record, True)

    assert api.store.read_file("job_var", "UPSC_photograph.jpg") == b"ENHANCED-BYTES"


def test_a_job_with_no_alternate_cannot_be_switched(api):
    """A photograph that needed nothing has one variant, not two."""
    from exam_photo.api.contracts import ApiJobStatus

    record = api.registry.create_job("job_single", 1800)
    record.status = ApiJobStatus.SUCCEEDED
    record.output_filename = "out.jpg"
    api.store.write_file("job_single", "out.jpg", b"ONLY-ONE")
    api.registry.update_job(record)

    with pytest.raises(LookupError, match="no alternate"):
        api.set_enhancement(record, False)


def test_a_missing_alternate_file_leaves_the_job_untouched(api):
    record = _prepared_with_both(api)
    api.store.delete_job_directory("job_var")
    api.store.write_file("job_var", "UPSC_photograph.jpg", b"ENHANCED-BYTES")

    with pytest.raises(LookupError):
        api.set_enhancement(record, False)

    assert record.enhancement_enabled is True
    assert api.store.read_file("job_var", "UPSC_photograph.jpg") == b"ENHANCED-BYTES"


def test_the_alternate_name_is_derived_predictably():
    from exam_photo.api.service import _alternate_filename

    assert _alternate_filename("UPSC_photo.jpg") == "UPSC_photo__alt.jpg"
    assert _alternate_filename("scan.pdf") == "scan__alt.pdf"
    assert _alternate_filename("noextension") == "noextension__alt"
