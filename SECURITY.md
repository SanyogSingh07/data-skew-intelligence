# Security Policy

## Supported Versions

The following versions of the Data Skew Intelligence Engine are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

## Reporting a Vulnerability

The project team and contributors take the security of this project seriously. If you believe you have discovered a vulnerability, security flaw, or sensitive data exposure, please follow the guidelines below:

### How to Report

1. **Do not create a public issue.** Please avoid disclosing security vulnerabilities publicly on GitHub issues or discussions until they have been resolved.
2. Submit a private report via **GitHub Private Vulnerability Reporting** under the [Security](https://github.com/SanyogSingh07/data-skew-intelligence/security) tab of this repository.
3. Alternatively, contact the maintainer directly via email: `127312273+SanyogSingh07@users.noreply.github.com`.

### What to Include in Your Report

To help us triage and resolve the issue quickly, please include:
- Description of the vulnerability and its potential impact
- Steps to reproduce the issue (proof-of-concept script, payloads, or CLI commands)
- Operating system, Python version, Java version, and PySpark version
- Any suggested remediations or patches

### Response Timeline

- **Initial Acknowledgement:** Within 48 hours of receipt.
- **Triage & Assessment:** Within 5 business days.
- **Remediation & Patch Release:** Coordinated with the reporter, aiming for resolution within 14 days.

---

## Security Best Practices in this Repository

- **Dependency Auditing:** Automated scanning via Dependabot for known CVEs in Python packages and GitHub Actions.
- **Static Analysis (SAST):** CodeQL automated security scanning on every push and pull request.
- **Secret Detection:** Secret scanning enabled to prevent accidental exposure of tokens, keys, and credentials.
- **Memory & Resource Safety:** JVM memory limits and worker isolation configured in Spark pipelines.
