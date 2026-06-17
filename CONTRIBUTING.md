# Contribution Guidelines (CONTRIBUTING.md)

Welcome! This document defines the development and contribution workflow for the Indian Exam-Photo Compliance Platform. Please read the [AGENTS.md](AGENTS.md) operating contract before proposing changes.

---

## 1. Development Sequence

All code changes and contributions must follow this sequence:

1. **Inspect current implementation**: Read existing tests and package scripts.
2. **Read documentation**: Ensure you review specifications under `docs/` related to your task.
3. **Identify Requirement IDs**: Trace your target task to stable requirement IDs in [Requirements Traceability Matrix](docs/07_REQUIREMENTS_TRACEABILITY.md).
4. **Define precise scope**: Avoid boundary creep. Do not implement features scheduled for future milestones.
5. **Identify unresolved decisions**: Refer to [Decision Log](docs/08_DECISION_LOG.md). If your work introduces a new ambiguity, document it first.
6. **Implement**: Write code conforming to coding standards.
7. **Add or update tests**: Ensure functional updates have corresponding unit or integration tests.
8. **Run formatting**: Ensure code meets format guidelines (`ruff format`).
9. **Run linting**: Ensure no lint errors remain (`ruff check`).
10. **Run type checking**: Run type assertions (`mypy`).
11. **Run tests**: Validate that all unit, regression, and integration tests pass successfully (`pytest`).
12. **Update documentation**: Keep docs updated to match changed features.
13. **Update requirements traceability**: Update status flags in [07_REQUIREMENTS_TRACEABILITY.md](docs/07_REQUIREMENTS_TRACEABILITY.md).
14. **Update decision log**: Log updates or approved decisions in [08_DECISION_LOG.md](docs/08_DECISION_LOG.md).
15. **Inspect generated files**: Check outputs and build bundles before packaging.
16. **Inspect Git status**: Ensure no cache directory or secret file is accidentally tracked.
17. **Provide a completion summary**: Detail what was changed, verified, and trace links to completed tickets.

---

## 2. Code Quality & Standards

- **Python**: Target version Python 3.10+. Use strict typing, type checking (`mypy`), linting (`ruff`), and testing (`pytest`).

- **Error Handling**: Placeholders must explicitly raise `NotImplementedError` rather than returning mocked compliance outcomes.
- **Privacy-Safe Fixture Rules**:
  - Never commit real candidate photos or generated processed outputs.
  - Test fixtures must only use synthetic, licensed, or public-domain images.
  - Do not commit secrets, environment variables (`.env`), or machine-learning model weight files to the repository.

---

## 3. Version Control & Git Guidelines

- **Branch Naming**: Use clear, descriptive branches: `feature/req-id-description` or `bugfix/issue-id-description`.
- **Commit Messages**: Use clean conventional commits format (e.g., `feat(engine): init crop mode validation interfaces`).
- **Pull Requests**:
  - Reference relevant requirement IDs.
  - Include execution verification commands and results in your PR summary.
  - Link updated traceability items.
