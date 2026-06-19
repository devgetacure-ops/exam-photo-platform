from pathlib import Path

import pytest

from exam_photo.cli import main

pytestmark = pytest.mark.mandatory_output_preparation


def find_repo_root() -> Path:
    curr = Path(__file__).resolve().parent
    for _ in range(5):
        if (curr / "AGENTS.md").exists():
            return curr
        curr = curr.parent
    return Path(__file__).resolve().parent.parent


def test_cli_no_face(tmp_path):
    repo_root = find_repo_root()
    img_path = repo_root / "tests" / "fixtures" / "blank_white_600x800.jpg"

    # Run cli command
    argv = [
        "prepare-output",
        "--input",
        str(img_path),
        "--target-width",
        "300",
        "--target-height",
        "400",
    ]
    exit_code = main(argv)
    assert exit_code == 1


def test_cli_multiple_faces():
    repo_root = find_repo_root()
    img_path = repo_root / "tests" / "fixtures" / "multiple_faces.jpg"

    argv = [
        "prepare-output",
        "--input",
        str(img_path),
        "--target-width",
        "300",
        "--target-height",
        "400",
    ]
    exit_code = main(argv)
    assert exit_code == 1


def test_cli_aspect_mismatch():
    repo_root = find_repo_root()
    img_path = repo_root / "tests" / "fixtures" / "single_face_frontal.jpg"

    # 600x800 has 0.75 aspect, target 300x300 has 1.0 (exact mode aspect mismatch)
    argv = [
        "prepare-output",
        "--input",
        str(img_path),
        "--resize-mode",
        "exact",
        "--target-width",
        "300",
        "--target-height",
        "300",
    ]
    exit_code = main(argv)
    assert exit_code == 1


def test_cli_overwrite_check(tmp_path):
    repo_root = find_repo_root()
    img_path = repo_root / "tests" / "fixtures" / "single_face_frontal.jpg"
    out_file = tmp_path / "output.png"

    # Create the output file beforehand
    out_file.touch()

    # Run without overwrite
    argv = [
        "prepare-output",
        "--input",
        str(img_path),
        "--target-width",
        "300",
        "--target-height",
        "400",
        "--save-preview",
        str(out_file),
    ]
    exit_code = main(argv)
    assert exit_code == 1

    # Run with overwrite
    argv.append("--overwrite")
    exit_code_overwrite = main(argv)
    assert exit_code_overwrite == 0


def test_cli_save_preview_valid_vs_invalid(tmp_path):
    repo_root = find_repo_root()
    img_path = repo_root / "tests" / "fixtures" / "single_face_frontal.jpg"

    # 1. Save valid preview (should succeed and save output.png)
    out_valid = tmp_path / "output_valid.png"
    argv = [
        "prepare-output",
        "--input",
        str(img_path),
        "--target-width",
        "300",
        "--target-height",
        "400",
        "--save-preview",
        str(out_valid),
    ]
    assert main(argv) == 0
    assert out_valid.exists()

    # 2. Save invalid preview with default --save-preview (should return 1 and NOT save)
    out_invalid = tmp_path / "output_invalid.png"
    argv_invalid = [
        "prepare-output",
        "--input",
        str(img_path),
        "--target-width",
        "300",
        "--target-height",
        "400",
        "--enhancement-mode",
        "conservative",
        "--brightness",
        "1.5",  # unsafe enhancement -> invalid
        "--save-preview",
        str(out_invalid),
    ]
    assert main(argv_invalid) == 1
    assert not out_invalid.exists()

    # 3. Save invalid preview with --allow-invalid-preview (should return 1 and save diagnostic_invalid_... name)
    out_invalid_allowed = tmp_path / "output_invalid_allowed.png"
    argv_allowed = [
        "prepare-output",
        "--input",
        str(img_path),
        "--target-width",
        "300",
        "--target-height",
        "400",
        "--enhancement-mode",
        "conservative",
        "--brightness",
        "1.5",  # unsafe enhancement -> invalid
        "--save-preview",
        str(out_invalid_allowed),
        "--allow-invalid-preview",
    ]
    assert main(argv_allowed) == 1
    # Check that it saved as "diagnostic_invalid_output_invalid_allowed.png"
    diagnostic_path = tmp_path / "diagnostic_invalid_output_invalid_allowed.png"
    assert diagnostic_path.exists()
