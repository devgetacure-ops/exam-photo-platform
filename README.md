# Indian Exam-Photo Compliance Platform

A specialized photo compliance and automated preparation platform designed to help candidates format, crop, and verify their application photographs according to structured examination cycle rules in India.

---

## 1. Product Summary
This platform processes candidate photographs by checking and conforming them to the official constraints of selected examinations (dimensions, file sizes, backgrounds, output filenames, and formats). The core promise is a simple, one-click experience converting a standard source photo into a fully compliant upload-ready file.

---

## 2. Current Repository Status & Milestone Scope

> [!NOTE]
> This repository has completed **Milestone 6 (Landmark-Assisted Geometric Head-Box Estimation)**.
> - **Input image normalization and suitability evaluation are fully implemented.**
> - **Local face-detection (MediaPipe) and landmark-assisted geometric head-box estimation are fully integrated and verified.**
> - **Automated cropping and background replacement are scheduled for next milestones.**

### What is Implemented:
* Repository directory structure, configuration templates, and Git policies.
* Neutral repository operating contract ([AGENTS.md](AGENTS.md)) and [CONTRIBUTING.md](CONTRIBUTING.md).
* Permanent product documentation under `docs/` detailing architectural choices, MVP scope, rules schemas, pipeline specifications, and development roadmaps.
* Canonical JSON Schema and Pydantic rules model validation checker (`validate-rule` CLI command).
* Secure, limits-based input image normalization, orientation transpose correction, metadata stripping, sRGB profile mapping (`inspect-input` CLI command).
* Suitability evaluation framework with local offline face-detection (MediaPipe) and landmark-assisted geometric head-box estimation.
* Geometry models (BoundingBox, Point) with safety clamping math.

### What is NOT Implemented:
* Background replacement/removal algorithms (scheduled for Milestone 7).
* final cropping, resizing, and output compressed photo generation algorithms (scheduled for Milestone 8).
* Public and admin console web applications.
* Production databases, authentication, payments, storage lifecycle handlers.


---

## 3. Repository Structure

```text
exam-photo-platform/
├── AGENTS.md                  # Neutral repo operating contract
├── CONTRIBUTING.md            # Contribution guidelines & workflows
├── README.md                  # This landing documentation
├── .gitignore                 # Protection from secret/image leaks
├── .editorconfig              # Editor code styling rules
├── docs/                      # Technical & product specs
│   ├── source/                # Stored source PDF files
│   ├── 00_PRODUCT_DECISIONS.md
│   ├── 01_MVP_SCOPE.md
│   ├── 02_TECHNICAL_ARCHITECTURE.md
│   ├── 03_EXAM_RULE_SCHEMA.md
│   ├── 04_IMAGE_PIPELINE_SPEC.md
│   ├── 05_PRIVACY_SECURITY.md
│   ├── 06_QA_STRATEGY.md
│   ├── 07_REQUIREMENTS_TRACEABILITY.md
│   ├── 08_DECISION_LOG.md
│   └── 09_DEVELOPMENT_ROADMAP.md
├── apps/                      # Future applications
│   ├── web/                   # Public user web application
│   └── admin/                 # Rule administration application
├── services/                  # Business logic services
│   └── image-engine/          # Python engine library
├── packages/                  # Monorepo library packages
│   ├── exam-rules/            # Shared rules parser/validator
│   └── shared-contracts/      # Shared interface definitions
├── examples/                  # Example configurations
│   └── rules/                 # Fictional JSON exam configurations
├── tests/                     # Global testing assets
│   ├── fixtures/              # Synthetic/consented test image configs
│   └── golden-images/         # Ground truth outputs
└── scripts/                   # Shared scripts and tools
```

---

## 4. Local Prerequisites & Setup

### Prerequisites
* Python 3.10 or newer (Python 3.11/3.12 recommended)
* Git


### Python image-engine Setup
All commands should be executed inside `services/image-engine`.

1. **Create and Activate Virtual Environment**:
   ```bash
   cd services/image-engine
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

2. **Install Package and Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -e .[dev]
   ```

---

## 5. Development & Verification Commands

Use these commands inside `services/image-engine` to run repository verification tasks:

* **Formatting check**:
  ```bash
  ruff format --check .
  ```
* **Linting check**:
  ```bash
  ruff check .
  ```
* **Type checking**:
  ```bash
  mypy src tests
  ```
* **Run unit tests**:
  ```bash
  pytest
  ```
* **Validate a JSON rule file**:
  ```bash
  python -m exam_photo validate-rule <path_to_json_file>
  # Example:
  python -m exam_photo validate-rule ../../examples/rules/sample_exact_dimensions.json
  ```

---

## 6. Privacy & Security Warning

> [!CAUTION]
> Uploaded photographs are sensitive biometric data. Under no circumstances should real candidate photographs, generated files containing real candidate information, or facial embeddings be checked into Git. Use only synthetic or licensed public domain assets from `tests/fixtures/`.

---

## 7. Reference Links
* **Product Foundation Source Document**: [Product Foundation v1.2 PDF](docs/source/Exam_Photo_Compliance_Platform_Product_Foundation_v1.2.pdf)
* **Operating Contract**: [AGENTS.md](AGENTS.md)
* **Contribution Guide**: [CONTRIBUTING.md](CONTRIBUTING.md)
