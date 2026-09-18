# CCBA Agent Services Platform

Hub-and-spoke monorepo for CCBA agent services. This repository is the **Hub** (shared skills, workflows, packages, and scripts) used by Spoke projects.

## Build, test, and lint commands

Run from repository root.

```bash
# Install workspace packages (CI-aligned)
uv pip install -e "packages/ccba-harness" --system
uv pip install -e "packages/ccba-ai[dev]" --system
uv pip install -e "packages/ccba-legal-intel[dev]" --system
uv pip install -e "packages/ccba-notebooklm[dev]" --system
uv pip install -e "packages/ccba-ooxml[dev]" --system
uv pip install -e "packages/ccba-pdf-prep[dev]" --system
uv pip install -e "packages/mdconverter[dev]" --system

# Test suites used in repo
pytest packages/mdconverter/tests/ -v --cov=src/mdconverter --cov-report=term-missing
python -m unittest discover -s scripts/tests
python scripts/run_harness_evals.py --all

# Single-test examples
pytest packages/mdconverter/tests/test_registry.py::TestConverterRegistry::test_auto_select_for_pdf -v
python -m unittest scripts.tests.test_validate_docs.TestValidateDocs.test_extract_code_references

# Lint / type check
ruff check packages/
ruff format packages/
mypy packages/*/src

# Docs/markdown validation used by hooks and workflows
python scripts/validate_docs.py . --src scripts,packages --changed
python -m pymarkdown scan README.md PLATFORM.md
```

## High-level architecture

- **Workspace model**: root `pyproject.toml` uses `uv` workspace members (`packages/*`) and centralizes lint/type config for package code.
- **Hub assets**:
  - `.agents/skills/` + `.agents/workflows/`: reusable agent behavior and automation.
  - `.md/`: central knowledge and legal-document data.
  - `scripts/`: lifecycle hooks, docs validation, privacy scan, and CI helper tooling.
- **Service modules** (pip-installable under `packages/`): `ccba-ai`, `ccba-harness`, `ccba-legal-intel`, `ccba-notebooklm`, `ccba-ooxml`, `ccba-pdf-prep`, `mdconverter`.
- **mdconverter flow**:
  - Typer CLI (`mdconverter.cli`) dispatches to command modules.
  - `ConversionPipeline` orchestrates analyze → convert → post-process → cache.
  - Converter selection is registry-based (`ConverterRegistry`) with priority order registered in `mdconverter.core.__init__`.
  - Post-processing is protocol-based (`PostProcessor`), with VN legal processing wired as default.
- **ccba-ai flow**:
  - `from ccba_ai import ai` exposes module-level singleton clients over an OpenAI-compatible gateway.
  - Built-in privacy hooks scan both input/output content.
  - Includes sync and async clients plus MCP server entry point (`ccba-mcp`).
- **Hook orchestration**:
  - `scripts/hook_runner.py` runs `session-init`, `pre-tool`, `post-tool`.
  - `pre-tool` combines privacy, naming, scout-block, and simplify-gate checks; `post-tool` runs brand enforcement.

## Key repository conventions

- Follow the **Hub constitution** in `.agents/AGENTS.md` (Layer 1): this repo is treated as Hub; Reuse-First and CCBA legal/identity constraints are mandatory.
- Python baseline: **3.10+**, strict mypy, ruff line length 100, double quotes.
- Keep imports **absolute within package** (e.g., `from mdconverter.core...`).
- `mdconverter` reads converter-specific env settings from `.env` at CWD (Pydantic settings), while `ccba-ai` client also searches upward for `.env`/`.env.ai-gateway`; avoid assuming one env-loading behavior across packages.
- For legal (VBPL) outputs, preserve required status markers/disclaimer conventions from `.agents/AGENTS.md` and `packages/mdconverter/docs/user-guide/vn-legal.md`.
- Use `scripts/validate_docs.py` for markdown correctness checks and `scripts/maskara.py scan --root .` for privacy/security scan alignment with CI.
- **PR Review & Merge Danger**: When summarizing or reviewing PRs, always classify the **Merge Danger**:
  - **Door**: `Two-way` (trivial to revert, isolated fix) vs `One-way` (hard/costly to revert, breaking change, DB/contract migration).
  - **Blast Radius**: `Localized` (single internal func/file) vs `Package-wide` vs `Monorepo-wide` vs `Spoke-affecting` (breaks downstream Spoke repos).
