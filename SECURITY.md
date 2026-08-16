# Security Policy

This repository is a sanitized educational DevSecOps portfolio project.

- No production credentials, API keys, private keys, cloud account identifiers, or real customer data are intentionally included.
- Local secrets belong in `.env` or an external secret manager; `.env` is ignored by Git.
- The CI/CD workflow includes secret detection, static analysis, dependency auditing, and container vulnerability scanning.
- The optional AWS deployment uses GitHub OIDC rather than long-lived AWS access keys.

If you discover sensitive information that may have been published accidentally, please report it privately instead of opening a public issue.
