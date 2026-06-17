# Privacy and Security Specification (05_PRIVACY_SECURITY.md)

This document specifies the privacy and security requirements for handling candidate photographs, metadata, and backend operations.

---

## 1. Privacy Lifecycle

- **Encrypted Transfer**: All data in transit must be encrypted using TLS 1.3/HTTPS.
- **Private Object Storage**: Raw uploads, intermediate copies, and output images must be stored in secure, private directories or object storage buckets.
- **Short-Lived Signed Access**: Frontend access to previews and downloads must use temporary signed URLs.
- **No Permanent Public URLs**: Static public image URLs are strictly prohibited.
- **Restricted Internal Access**: Direct access to storage directories or buckets is restricted to administrators with audit logging.
- **Configurable Retention**: The platform must support configurable deletion schedules.
  - > [!NOTE]
  - > **Image Retention Period**: The final retention period remains **unresolved** pending further product requirements. It is logged in the Decision Log.
- **Complete Deletion Lifecycle**: The deletion runner must purge:
  1. Original source uploads.
  2. Intermediate files, crops, and segmentations.
  3. Final output files.
- **Audit Logging**: Maintain write and delete audit logs containing timestamps and anonymized transaction identifiers, but excluding raw files, facial landmarks, or identifiable user names.
- **Model Training Restriction**: Uploaded images must never be used for AI model training or refinement without explicit, separate consent.
- **Facial Embedding Retention**: Retaining facial landmarks or biometric embeddings after session completion is prohibited.

---

## 2. Secure Processing Boundaries

- **Safe Image Decoding**: Decode images inside sandboxed configurations with maximum limits to prevent decompression bomb exploits.
  - **Maximum Input Byte Limit**: Standard upload limit is 10 MB.
  - **Maximum Dimension Limit**: Standard upload resolution limit is 8192 x 8192 pixels.
- **File-Signature Verification**: Perform validation on file magic numbers instead of relying solely on the file extension or the browser's Content-Type header.
- **Content-Type Validation**: Restrict processing to `image/jpeg` and `image/png`.
- **Safe Filename Handling**: Automatically sanitize filename strings to prevent directory-traversal attacks (e.g., removing `../` and stripping special characters).
- **Safe Errors**: Expose user-facing error messages containing clear usability recommendations without leaks of stack traces or internal directories.

---

## 3. Secret Management

- Credentials, storage signatures, and API keys must be kept outside source repositories.
- Use environment variables (`.env`) for local development, which are excluded from source control via `.gitignore`.
