# Public Web App MVP (apps/web)

This is the first user-facing web application MVP for the Indian Exam-Photo Compliance Platform. It is built using Next.js App Router, TypeScript, and Tailwind CSS.

> [!WARNING]
> The web app is an MVP frontend for the local processing API. It is not production-ready until authentication, deployment controls, rate limiting, and storage policies are added.

## Features

1. **Step-by-Step Compliance Flow**:
   - **Step 1 (Rule Selection)**: Select from built-in sample configurations or upload a custom JSON rule schema.
   - **Step 2 (Photo Upload)**: Drag-and-drop or select candidate images (< 5MB, JPEG/PNG/WebP).
   - **Step 3 (Run Processing)**: Synchronously submit requests to the local compliance API.
   - **Step 4 (Validation Results & Actions)**: Review full compliance diagnostic reports, preview output JPEGs, download compliant photos, and trigger complete file wipes.

2. **Privacy Lifecycle**:
   - Zero local caching: No candidate photos, image data, or reports are saved in browser `localStorage` or `sessionStorage`.
   - Immediate Object URL Revocation: Memory-only blob URLs used for image previews and download triggers are immediately revoked on deletion, file reset, or component unmount to protect biometrics.
   - Manual Wipeout: Clicking "Delete Job & Files" makes an API request to wipe all files from disk, and resets all local frontend states.

3. **Local Rule Configuration Console**:
   - Access at `/admin/rules` gated behind the `NEXT_PUBLIC_ENABLE_RULE_ADMIN=true` environment variable.
   - Accidental-exposure warning banner indicating that this console is a local accidental-exposure guard and not a production authentication mechanism.
   - Interactive forms to edit core rule identifiers, exam information, sizing requirements, background rules, composition targets, filenames, and exceptional instructions.
   - Preservation of unrecognized/advanced fields in rule JSON during edits.
   - Revert actions to reset workspace draft state back to original imported/loaded rule.
   - Integration with stateless validation API `POST /v1/rules/validate`.

## Development Setup

### 1. Start the local API Server with CORS enabled

To allow the browser to interact with the API, CORS must be enabled when running the server:

```powershell
# Windows PowerShell
$env:EXAM_PHOTO_LOCAL_CORS_ENABLED="true"
python -m exam_photo serve-api --host 127.0.0.1 --port 8000
```

### 2. Run the Next.js development server

From the `apps/web/` directory:

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Sync Notice for Sample Rules

The sample rule files located in `public/rules/`:
- `public/rules/sample_exact_300x400_50kb_white_bg.json`
- `public/rules/sample_range_200_300_width_230_400_height_50kb_white_bg.json`

must remain exactly duplicated and synchronized with the canonical examples inside the root `examples/rules/` directory to prevent rule drift.

## Quality and Verification

Run the test suite, linter, typecheckers, and production build checks:

```bash
# Typecheck
npm run typecheck

# Lint
npm run lint

# Vitest Suite
npm test

# Production Compile
npm run build
```
