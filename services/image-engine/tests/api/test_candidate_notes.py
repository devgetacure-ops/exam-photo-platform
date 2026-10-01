"""Notes the engine writes for the candidate reach the candidate (DEC-116)."""

from exam_photo.api.service import candidate_notes
from exam_photo.suitability.disposition import AppearanceFinding, FindingLevel
from exam_photo.suitability.issue_codes import SuitabilityIssueCode


def _finding(**overrides: object) -> dict[str, object]:
    base = AppearanceFinding(
        code=SuitabilityIssueCode.REFINEMENT_LARGE_HOLES_DETECTED,
        level=FindingLevel.POSSIBLE_ISSUE,
        message="We had trouble separating you from the background.",
        remedy="A plain wall behind you gives a cleaner result.",
    ).model_dump(mode="json")
    base.update(overrides)
    return base


def test_a_finding_is_private_unless_it_was_written_for_the_candidate() -> None:
    assert AppearanceFinding.model_fields["tell_candidate"].default is False
    assert candidate_notes([_finding()]) == []


def test_a_note_is_one_sentence_pair_and_is_said_once() -> None:
    note = _finding(tell_candidate=True)
    assert candidate_notes([note, note]) == [
        "We had trouble separating you from the background. "
        "A plain wall behind you gives a cleaner result."
    ]


def test_nothing_reported_means_nothing_said() -> None:
    assert candidate_notes(None) == []
    assert candidate_notes([]) == []
    assert candidate_notes(["not a finding"]) == []
