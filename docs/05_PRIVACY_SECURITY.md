# Privacy and Security Specification (05_PRIVACY_SECURITY.md)

This document specifies the privacy and security requirements for handling candidate photographs, metadata, and backend operations.

> **Reviewed 2026-08-04. The requirements below remain correct; the
> implementation does not yet meet them.** The processing API is currently
> local-only by design, with no TLS, authentication or rate limiting, and cannot
> face the public as built. Closing that gap is Milestone 25, and the data
> lifecycle work is Milestone 26.
>
> **Legal input is required, not optional.** Candidate face photographs are
> sensitive personal data and India's Digital Personal Data Protection Act 2023
> applies to processing them. Engineering can implement controls, but what
> compliance requires -- lawful basis, consent wording, retention limits,
> breach obligations, and whether processing may occur outside India -- is not
> an engineering decision and must be settled by someone qualified before
> launch.

---

## 1. Privacy Lifecycle

- **Encrypted Transfer**: All data in transit must be encrypted using TLS 1.3/HTTPS.
- **Private Object Storage**: Raw uploads, intermediate copies, and output images must be stored in secure, private directories or object storage buckets.
- **Short-Lived Signed Access**: Frontend access to previews and downloads must use temporary signed URLs.
- **No Permanent Public URLs**: Static public image URLs are strictly prohibited.
- **Restricted Internal Access**: Direct access to storage directories or buckets is restricted to administrators with audit logging.
- **Configurable Retention**: The platform must support configurable deletion schedules.
  - > [!NOTE]
  - > **Image Retention Period**: still **unresolved**, and now assigned to Milestone 26. It should be set by what the DPDP Act and the platform's stated purpose allow, not by operational convenience: the lawful purpose ends when the candidate has downloaded their photograph, so the default should be the shortest window that still supports a retry.
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
