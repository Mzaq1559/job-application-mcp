# Contributing to Job Application MCP

Thanks for your interest in contributing.

Job Application MCP is intended to grow into a serious, extensible MCP platform for managing the job-application lifecycle. Contributions are welcome in the form of bug fixes, tests, documentation, architecture improvements, integrations, security improvements, and new MCP capabilities.

## Development workflow

The `community` branch is the community integration branch.

1. Fork the repository.
2. Create a focused branch from `community`.
3. Make the smallest complete change that solves the problem.
4. Add or update tests where appropriate.
5. Run:
   ```bash
   pytest -q
   ruff check .
   ```
6. Update documentation when behavior or configuration changes.
7. Open a pull request targeting `community`.
8. Explain what changed, why, how it was tested, and any compatibility or migration concerns.

The `main` branch is reserved for reviewed, release-ready changes.

## Good contribution areas

- MCP tools and job-application workflow improvements
- AI-assisted analysis with explicit anti-fabrication safeguards
- Resume parsing and document handling
- Alembic migrations and PostgreSQL hardening
- Durable file/object storage
- Authentication, authorization, and multi-user isolation
- Integration tests for HTTP/OAuth/MCP
- Observability, logging, error handling, Docker, and deployment
- Documentation, examples, accessibility, and developer experience
- Security fixes

Do not add scraping, credential harvesting, bot-driven applications, or unauthorized automation against third-party job platforms.

## Code guidelines

- Keep business logic in `src/job_application_mcp/services/`.
- Keep MCP boundary schemas explicit and validated.
- Prefer small, testable functions.
- Do not introduce hidden network calls into user-provided-data workflows.
- Never unnecessarily log secrets, access tokens, resume contents, or other sensitive data.
- Preserve the user-control principle: the server may prepare and track an application, but it does not submit applications to third-party platforms.

## Pull request checklist

- [ ] Clear purpose and focused scope.
- [ ] Tests added or updated where needed.
- [ ] `pytest -q` passes.
- [ ] `ruff check .` passes.
- [ ] Documentation/configuration updated if necessary.
- [ ] No secrets or personal data committed.
- [ ] No unauthorized scraping or application automation introduced.
- [ ] PR explains testing and deployment/database impact.

## Licensing

This repository is source-available, not OSI-approved open source. Personal evaluation, learning, and non-commercial contribution are permitted under the project license.

Commercial deployment, hosted/SaaS use, and inclusion in a paid product require a separate commercial license. A contribution does not grant the contributor commercial rights.

By submitting a pull request, you agree that your contribution may be incorporated into the project and distributed by the maintainer under the project's current license or a separate commercial license.

See [LICENSE](LICENSE) for the full terms.
