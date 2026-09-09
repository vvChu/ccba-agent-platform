# ccba-setup-pre-commit — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Hướng dẫn cấu hình pre-commit linter hooks và bảo vệ mã nguồn
> **Mô tả gốc:** Set up Python pre-commit framework with Ruff, MyPy, PyMarkdown, and local CCBA validators (validate_docs, validate_skills). Incorporates Maskara pre-commit hook. Run once before first commit.

---

# Setup Python Pre-Commit Hooks

Scaffold the project-level Git pre-commit hooks for a CCBA Spoke or Hub project using Python's `pre-commit` framework:

- **Ruff** — fast linter and formatter.
- **MyPy** — static type checking.
- **PyMarkdown** — markdown linter.
- **CCBA Docs/Skills Validators** — runs local custom checks on docs/skills.
- **Maskara hook** — prevents committing API keys and credentials.

## Steps

### 1. Detect package manager and virtual environment
- Ensure we are inside a virtual environment (`.venv` or global).
- Detect package manager: `uv` (recommended), `pip`, or `poetry`.

### 2. Install pre-commit dependency
- If using `uv`: `uv pip install pre-commit`
- If using `pip`: `pip install pre-commit`
- If using `poetry`: `poetry add -D pre-commit`

### 3. Copy `.pre-commit-config.yaml`
Check if `.pre-commit-config.yaml` already exists in the repo root.
- If it exists, do NOT overwrite: show differences or ask user.
- If it does not exist, copy the template `.pre-commit-config.yaml.template` from this skill's resources folder to `.pre-commit-config.yaml` at the repo root.

### 4. Install Git hook scripts
Run the following command to bind pre-commit hooks to `.git/hooks/pre-commit`:
```bash
pre-commit install
```
Ensure that if this is a Spoke, the **Maskara pre-commit hook** is also registered or appended.

### 5. Run first smoke test
Run pre-commit checks on all files to verify they work:
```bash
pre-commit run --all-files
```

### 6. Verify and commit
Check that `.pre-commit-config.yaml` exists, and commit it with message `chore: setup python pre-commit hooks`.
