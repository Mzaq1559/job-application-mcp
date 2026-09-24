# Security Policy

## Reporting a vulnerability

Please do not open a public GitHub issue for an undisclosed security vulnerability.

Report security issues privately through GitHub's available security reporting mechanism or contact the maintainer through the repository profile.

Include, when possible:
- A clear description of the vulnerability.
- The affected component or file.
- Reproduction steps or proof of concept.
- Potential security impact.
- Suggested mitigation.

Never include real access tokens, passwords, private resumes, personal application data, or other secrets in a report.

## Priority areas

Security reports are especially important for:
- OAuth 2.1 and JWT validation
- Authorization and cross-user data access
- File upload validation and path traversal
- SQL injection and unsafe database queries
- Secret or credential exposure
- Container and deployment configuration
- MCP transport authentication
- Sensitive data appearing in logs

Please give the maintainer reasonable time to investigate and release a fix before public disclosure.
