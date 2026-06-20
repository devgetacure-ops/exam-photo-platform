# Exam Photo Image Engine Service

This is the Python package foundation for the Indian Exam-Photo Compliance platform's image-processing engine.

## Status
- **Status**: Milestone 14 implemented locally; repository verification pending visible CI run.
- **Milestone Reference**: Milestone 14 (Full CLI Orchestration and Final Validation).

## Setup Instructions

Create virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate
# Install with dev and face-detection dependencies
pip install -e .[dev,face]
```

## Running Verification Checks
* **Download face detector model weights**:
  ```bash
  python ../../scripts/download_model.py --variant short_range --yes
  ```
* **Download segmenter model weights**:
  ```bash
  python ../../scripts/download_segmenter.py --variant selfie_bin_general --yes
  ```
* **Format**: `ruff format --check .`
* **Lint**: `ruff check .`
* **Type-check**: `mypy src tests`
* **Test**: `pytest`
* **Validate Rule Command**: `python -m exam_photo validate-rule <file_path>`
* **Estimate Head Command**: `python -m exam_photo estimate-head --input <file_path>`
* **Segment Subject Command**: `python -m exam_photo segment-subject --input <file_path>`
* **Plan Crop Mode A Command**: `python -m exam_photo plan-crop-mode-a --input <file_path> --target-width 300 --target-height 400`
* **Plan Crop Mode B Command**: `python -m exam_photo plan-crop-mode-b --input <file_path>`
* **Prepare Output Command**: `python -m exam_photo prepare-output --input <file_path> --target-width 300 --target-height 400`
* **Compress Output Command**: `python -m exam_photo compress-output --input <file_path> --target-width 300 --target-height 400 --maximum-bytes 50000`
* **Process Rule Command**: `python -m exam_photo process-rule --input <file_path> --rule <rule_path> --output-dir <output_dir> --save-output`



