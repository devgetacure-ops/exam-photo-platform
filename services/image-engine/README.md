# Exam Photo Image Engine Service

This is the Python package foundation for the Indian Exam-Photo Compliance platform's image-processing engine.

## Status
- **Status**: Secure Image Input Normalization & Suitability Framework.
- **Milestone Reference**: Milestone 4.

## Setup Instructions

Create virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

## Running Verification Checks
* **Format**: `ruff format --check .`
* **Lint**: `ruff check .`
* **Type-check**: `mypy src tests`
* **Test**: `pytest`
* **Validate Rule Command**: `python -m exam_photo validate-rule <file_path>`

