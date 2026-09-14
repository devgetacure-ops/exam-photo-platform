"""A photograph in a signature's place is refused; a real mark never is (note 23).

Negative first: every measured real or synthetic mark and impression must pass.
"""

from exam_photo.suitability.not_ink import (
    REFUSAL_CODE,
    REFUSAL_TEXT,
    looks_like_a_photograph,
)


def test_no_face_is_never_a_photograph_whatever_the_frame() -> None:
    for kind in ("signature", "thumb_impression"):
        assert looks_like_a_photograph(kind, [], 0.05, True) is False


def test_the_most_face_like_real_and_synthetic_ink_is_never_refused() -> None:
    # Owner's thumb impressions: 0.36, sheet 97%. Synthetic faint impressions:
    # up to 0.566, sheet 97%. Synthetic marks: up to 0.275, sheet 97%.
    assert looks_like_a_photograph("thumb_impression", [0.36], 0.97, False) is False
    assert looks_like_a_photograph("thumb_impression", [0.566], 0.97, False) is False
    assert looks_like_a_photograph("signature", [0.275], 0.97, False) is False
    # A real signature on a desk, sheet a third of the frame, no face.
    assert looks_like_a_photograph("signature", [], 0.34, False) is False


def test_a_confident_face_refuses_a_signature_upload() -> None:
    assert looks_like_a_photograph("signature", [0.5], 1.0, False) is True
    assert looks_like_a_photograph("signature", [0.2, 0.93], 0.13, False) is True


def test_a_weaker_face_refuses_a_signature_only_in_a_scene() -> None:
    # The street photograph from note 23: 0.42, sheet 9% of the frame.
    assert looks_like_a_photograph("signature", [0.42], 0.09, False) is True
    assert looks_like_a_photograph("signature", [0.42], 0.9, False) is False


def test_a_thumb_impression_upload_needs_a_confident_face_in_a_scene() -> None:
    assert looks_like_a_photograph("thumb_impression", [0.97], 1.0, True) is True
    assert looks_like_a_photograph("thumb_impression", [0.93], 0.13, False) is True
    assert looks_like_a_photograph("thumb_impression", [0.45], 0.09, False) is False


def test_other_kinds_of_file_are_never_checked() -> None:
    # A certificate may carry the candidate's own photograph.
    assert looks_like_a_photograph("certificate_scan", [0.99], 0.1, True) is False


def test_the_refusal_says_what_to_upload_instead() -> None:
    for kind in ("signature", "thumb_impression"):
        assert "plain white paper" in REFUSAL_TEXT[kind]
        assert REFUSAL_CODE[kind].startswith("UPLOAD_NOT_A_")
