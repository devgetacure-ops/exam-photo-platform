# Exam Photo Image Engine Service

This is the Python package foundation for the Indian Exam-Photo Compliance platform's image-processing engine.

## Status
- **Status**: Milestone 7 completed: repository-verified provisional coarse subject-segmentation baseline.
- **Milestone Reference**: Milestone 7 (Portrait-Segmentation and Coarse Foreground-Mask Generation).

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
* **Validate Rule Command**: `python -m exam_photo.cli validate-rule <file_path>`
* **Estimate Head Command**: `python -m exam_photo.cli estimate-head --input <file_path>`
* **Segment Subject Command**: `python -m exam_photo.cli segment-subject --input <file_path>`


