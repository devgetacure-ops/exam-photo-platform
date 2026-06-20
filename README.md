# Indian Exam-Photo Compliance Platform

A specialized photo compliance and automated preparation platform designed to help candidates format, crop, and verify their application photographs according to structured examination cycle rules in India.

---

## 1. Product Summary
This platform processes candidate photographs by checking and conforming them to the official constraints of selected examinations (dimensions, file sizes, backgrounds, output filenames, and formats). The core promise is a simple, one-click experience converting a standard source photo into a fully compliant upload-ready file.

---

## 2. Current Repository Status & Milestone Scope

> [!NOTE]
> This repository has implemented **Milestone 17: Local Rule Configuration Console, Schema Validation, and Admin Data Entry Dashboard.**
> - **Input image normalization, suitability evaluation, and face/segmentation detection are fully integrated.**
> - **Crop Mode A and B plans, solid background composition, resizing, and quality-aware compression search are fully implemented.**
> - **Local FastAPI service and persistent manifest manager are integrated on localhost.**
> - **Public user Next.js App Router application is implemented, featuring rule selection, photo upload, validation diagnostics, download, and URL-revoking secure deletion.**
> - **Local developer rule configuration console (/admin/rules) is implemented under gated local flags, and backend stateless validation API (POST /v1/rules/validate) is operational without local disk writes.**

### What is Implemented:
* Repository directory structure, configuration templates, and Git policies.
* Neutral repository operating contract ([AGENTS.md](AGENTS.md)) and [CONTRIBUTING.md](CONTRIBUTING.md).
* Permanent product documentation under `docs/` detailing architectural choices, MVP scope, rules schemas, pipeline specifications, and development roadmaps.
* Canonical JSON Schema and Pydantic rules model validation checker (`validate-rule` CLI command).
* Secure, limits-based input image normalization, orientation transpose correction, metadata stripping, sRGB profile mapping (`inspect-input` CLI command).
* Suitability evaluation framework with local offline face-detection (MediaPipe) and landmark-assisted geometric head-box estimation.
* Coarse portrait segmentation (MediaPipe multiclass/binary) with connected component (DSU) and face/head containment mask validation.
* Geometry models (BoundingBox, Point) with safety clamping math.
* Crop Mode A exact-aspect crop planning CLI and provider interfaces.
* Crop Mode B face/head-led natural range crop planning CLI and provider interfaces.
* Solid Background Composition with foreground coverage validation and clipping risk detection.
* Output dimensioning, format conversion (e.g. RGBA to RGB), and restrained brightness/contrast/sharpness enhancement (`prepare-output` CLI command).
* Quality-aware compression loop with binary quality search, EXIF metadata stripping, and decode-after-encode verification (`compress-output` CLI command).
* End-to-end rule pipeline resolver, safe PII-free filename generation, and final validation against exam constraints (`process-rule` CLI command).
* Local Processing API exposing pipeline execution, opaque job IDs, relative route URLs, persistent manifests, manual deletion, and expired folder TTL cleanup (`serve-api` CLI command).
* Public user Next.js App Router application MVP (`apps/web`) supporting rule selection, photo upload, validation diagnostics, download, and URL-revoking secure deletion.
* Local developer rule configuration console (`/admin/rules`) and stateless validation API route (`POST /v1/rules/validate`) gated behind `NEXT_PUBLIC_ENABLE_RULE_ADMIN=true`.

### What is NOT Implemented:
* Production databases, authentication, payments, cloud storage adapters.


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
* **Start local API server**:
  ```bash
  python -m exam_photo serve-api --host 127.0.0.1 --port 8000
  ```
  > [!WARNING]
  > The API server is designed for local development and testing only (`127.0.0.1` by default). Do not expose this service to the public network (`0.0.0.0`) without adding appropriate transport layer security (SSL), authentication/authorization, and rate limiting controls.

---

## 6. Privacy & Security Warning

> [!CAUTION]
> Uploaded photographs are sensitive biometric data. Under no circumstances should real candidate photographs, generated files containing real candidate information, or facial embeddings be checked into Git. Use only synthetic or licensed public domain assets from `tests/fixtures/`.

---

## 7. Reference Links
* **Product Foundation Source Document**: [Product Foundation v1.2 PDF](docs/source/Exam_Photo_Compliance_Platform_Product_Foundation_v1.2.pdf)
* **Operating Contract**: [AGENTS.md](AGENTS.md)
* **Contribution Guide**: [CONTRIBUTING.md](CONTRIBUTING.md)
