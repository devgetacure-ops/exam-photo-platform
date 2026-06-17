from typing import Any

from tests.helpers.synthetic_images import create_solid_image, save_image_to_bytes

from exam_photo.cli import main


def test_inspect_input_cli_success(tmp_path: Any) -> None:
    img_data = save_image_to_bytes(create_solid_image("RGB"), "PNG")
    file_path = tmp_path / "test.png"
    file_path.write_bytes(img_data)

    # Run cli command inspect-input
    exit_code = main(["inspect-input", "--input", str(file_path)])
    assert exit_code == 0


def test_inspect_input_cli_json(tmp_path: Any) -> None:
    img_data = save_image_to_bytes(create_solid_image("RGB"), "PNG")
    file_path = tmp_path / "test.png"
    file_path.write_bytes(img_data)

    # Capture print output using custom sys.stdout redirect if desired,
    # but asserting correct execution exit code is key.
    exit_code = main(["inspect-input", "--input", str(file_path), "--json"])
    assert exit_code == 0
