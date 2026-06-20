from pathlib import Path

import pytest

from exam_photo.cli import main

pytestmark = pytest.mark.mandatory_output_compression


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

    # Run cli command (fails since no face is detected)
    argv = [
        "compress-output",
        "--input",
        str(img_path),
        "--maximum-bytes",
        "50000",
    ]
    exit_code = main(argv)
    assert exit_code == 1


def test_cli_multiple_faces():
    repo_root = find_repo_root()
    img_path = repo_root / "tests" / "fixtures" / "multiple_faces.jpg"

    argv = [
        "compress-output",
        "--input",
        str(img_path),
        "--maximum-bytes",
        "50000",
    ]
    exit_code = main(argv)
    assert exit_code == 1


def test_cli_valid_compression(tmp_path):
    repo_root = find_repo_root()
    img_path = repo_root / "tests" / "fixtures" / "single_face_frontal.jpg"
    out_file = tmp_path / "compressed.jpg"

    argv = [
        "compress-output",
        "--input",
        str(img_path),
        "--target-width",
        "300",
        "--target-height",
        "400",
        "--maximum-bytes",
        "50000",
        "--save-output",
        str(out_file),
    ]
    exit_code = main(argv)
    assert exit_code == 0
    assert out_file.exists()
    assert out_file.stat().st_size <= 50000


def test_cli_overwrite_check(tmp_path):
    repo_root = find_repo_root()
    img_path = repo_root / "tests" / "fixtures" / "single_face_frontal.jpg"
    out_file = tmp_path / "compressed.jpg"

    # Pre-create the file
    out_file.touch()

    # Try to write without --overwrite (should fail)
    argv = [
        "compress-output",
        "--input",
        str(img_path),
        "--target-width",
        "300",
        "--target-height",
        "400",
        "--maximum-bytes",
        "50000",
        "--save-output",
        str(out_file),
    ]
    exit_code = main(argv)
    assert exit_code == 1

    # Try with --overwrite (should succeed)
    argv.append("--overwrite")
    exit_code = main(argv)
    assert exit_code == 0


def test_cli_save_invalid_vs_allowed(tmp_path):
    repo_root = find_repo_root()
    img_path = repo_root / "tests" / "fixtures" / "single_face_frontal.jpg"

    # Try to save to a very small size ceiling (e.g. 100 bytes)
    # This should fail validation because of maximum size exceeded / quality floor violation.
    out_invalid = tmp_path / "out_invalid.jpg"
    argv = [
        "compress-output",
        "--input",
        str(img_path),
        "--target-width",
        "300",
        "--target-height",
        "400",
        "--maximum-bytes",
        "100",
        "--safety-margin-bytes",
        "0",
        "--save-output",
        str(out_invalid),
    ]

    # Without --allow-invalid-output, it should not save
    exit_code = main(argv)
    assert exit_code == 1
    assert not out_invalid.exists()

    # With --allow-invalid-output, it should save but prefix the name
    argv_allowed = argv + ["--allow-invalid-output"]
    exit_code_allowed = main(argv_allowed)
    assert exit_code_allowed == 1

    # Path should have prefix "diagnostic_invalid_" prepended to the filename
    diagnostic_path = tmp_path / "diagnostic_invalid_out_invalid.jpg"
    assert diagnostic_path.exists()


def test_cli_rejects_same_input_and_output(tmp_path):
    repo_root = find_repo_root()
    img_path = repo_root / "tests" / "fixtures" / "single_face_frontal.jpg"

    # Copy the input image to a temp location so we can pretend we try to overwrite it
    local_input = tmp_path / "single_face_frontal.jpg"
    with open(img_path, "rb") as f_in:
        local_input.write_bytes(f_in.read())

    argv = [
        "compress-output",
        "--input",
        str(local_input),
        "--target-width",
        "300",
        "--target-height",
        "400",
        "--maximum-bytes",
        "50000",
        "--save-output",
        str(local_input),
    ]
    exit_code = main(argv)
    assert exit_code == 1
