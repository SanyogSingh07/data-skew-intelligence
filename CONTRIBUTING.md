# Contributing to Data Skew Intelligence Engine

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## 🚀 Getting Started

### Development Setup

```bash
# Clone the repository
git clone https://github.com/SanyogSingh07/data-skew-intelligence.git
cd data-skew-intelligence

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS/Linux

# Install all dependencies (including dev tools)
pip install -r requirements-dev.txt
```

### Prerequisites

| Tool | Version | Purpose |
|:-----|:--------|:--------|
| Python | 3.11+ | Runtime |
| Java JDK | 17+ | PySpark dependency |
| Git | Latest | Version control |

---

## 📋 How to Contribute

### Reporting Bugs

1. Check existing [Issues](https://github.com/SanyogSingh07/data-skew-intelligence/issues) to avoid duplicates
2. Use the bug report template (if available)
3. Include: Python version, Java version, OS, error output, and reproduction steps

### Suggesting Features

1. Open a [Discussion](https://github.com/SanyogSingh07/data-skew-intelligence/discussions) or Issue
2. Describe the use case and expected behavior
3. Include code examples or mockups if possible

### Pull Requests

1. Fork the repository
2. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes following the code style guidelines below
4. Run the test suite and linter:
   ```bash
   ruff check .
   pytest -q --cov=.
   ```
5. Commit with a descriptive message:
   ```bash
   git commit -m "feat: add XYZ capability to mitigation engine"
   ```
6. Push and open a Pull Request against `main`

---

## 🎨 Code Style

This project uses **[Ruff](https://docs.astral.sh/ruff/)** for linting and formatting:

- **Line length:** 120 characters
- **Selected rules:** `E` (pycodestyle), `F` (pyflakes), `I` (isort), `B` (bugbear)
- **Ignored rules:** `E402` (module-level imports), `E501` (line length handled by formatter)

```bash
# Check for issues
ruff check .

# Auto-fix
ruff check --fix .
```

### Commit Message Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Use Case |
|:-------|:---------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation changes |
| `test:` | Adding or modifying tests |
| `refactor:` | Code restructuring (no behavior change) |
| `perf:` | Performance improvements |
| `ci:` | CI/CD changes |

---

## 🧪 Testing

All contributions must pass the existing test suite:

```bash
# Full suite
pytest

# With coverage
pytest -q --cov=. --cov-report=term-missing

# Specific module
pytest tests/test_mitigation.py -v
```

### Writing Tests

- Place tests in the `tests/` directory
- Follow the naming convention `test_<module>.py`
- Use fixtures from `tests/conftest.py`
- Aim for meaningful assertions, not just coverage

---

## 📂 Project Structure Guidelines

| Directory | Purpose |
|:----------|:--------|
| `spark/` | PySpark computation — sessions, metrics, mitigation |
| `ml/` | scikit-learn training, evaluation, prediction |
| `cli/` | Terminal interface (Typer + Rich) |
| `visualization/` | Charts (Matplotlib), theme, site export |
| `core/` | Pipeline orchestration & configuration |
| `tests/` | All pytest tests |
| `docs/` | Architecture documents & screenshots |

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
