# Exam Photo Image Engine Service

This is the Python package foundation for the Indian Exam-Photo Compliance platform's image-processing engine.

## Status
- **Status**: Landmark-Assisted Geometric Head-Box Estimation & Suitability.
- **Milestone Reference**: Milestone 6 (Landmark-Assisted Geometric Head-Box Estimation).

## Setup Instructions

Create virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate
# Install with dev and face-detection dependencies
pip install -e .[dev,face]
```

## Running Verification Checks
* **Download model weights**:
  ```bash
  python ../../scripts/download_model.py --variant short_range --yes
  ```
* **Format**: `ruff format --check .`
* **Lint**: `ruff check .`
* **Type-check**: `mypy src tests`
* **Test**: `pytest`
* **Validate Rule Command**: `python -m exam_photo.cli validate-rule <file_path>`


