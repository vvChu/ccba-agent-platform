# CCBA Agent Services Platform

Hub-and-Spoke monorepo for Vietnamese construction (BIM) AI agent services.
Hub contains tools (skills, workflows, knowledge, service modules); Spokes contain project context.

## Architecture

Two pip-installable packages under `packages/`:

| Package | Purpose | Entry Point |
|---------|---------|-------------|
| **mdconverter** | PDF/DOCX/HTML → Markdown with Vietnamese legal doc support | `mdconvert` CLI (Typer) |
| **ccba-ai** | AI Gateway client — 22 models, 1 endpoint (OpenAI-compatible) | `from ccba_ai import ai` |

Key patterns:
- **Converter registry**: `@ConverterRegistry.register("name", priority=N)` — auto-selects by extension + priority
- **Plugin system**: Entry-point-based (`pyproject.toml`), dynamic loading via `PluginManager`
- **Settings**: Pydantic `BaseSettings` with `MDCONVERT_` env prefix, `.env` at CWD only (no recursive search)
- **Async**: Converters use `async def convert()` throughout

See [PLATFORM.md](../PLATFORM.md) for detailed architecture and extension guide.

## Build & Test

```bash
# Install (from repo root)
pip install -e "packages/mdconverter[dev,llm]"
pip install -e "packages/ccba-ai"

# Or use the setup script
./install.ps1

# Test
pytest packages/mdconverter/tests/ -v --cov=src/mdconverter --cov-report=term-missing

# Lint & format
ruff check packages/
ruff format packages/

# Type check (strict mode)
mypy packages/*/src
```

## Code Style

- **Python ≥ 3.10** — use `match`, `str | None` union syntax
- **Line length**: 100 (ruff-enforced)
- **Quotes**: double `"`
- **Type annotations**: required on all functions (mypy strict)
- **Async**: preferred for I/O-bound operations
- **Dataclasses/Pydantic v2**: preferred over manual `__init__`
- **Imports**: absolute within package (`from mdconverter.core.base import BaseConverter`)

## Git Conventions

**Branches**: `feature/`, `fix/`, `docs/`, `refactor/`, `experiment/` + short description  
**Commits**: conventional — `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`  
**PR requirements**: all tests pass (3.10/3.11/3.12, Linux/Mac/Windows), linting passes, 1 maintainer review

See [CONTRIBUTING.md](../CONTRIBUTING.md) for full workflow and agent commands (`/new-feature`, `/create-pr`, `/release-feature`).

## Vietnamese Legal Documents (VBPL)

This project processes Vietnamese legal texts. Critical rules:

- **Never** present draft VBPL as enacted or fabricate reference numbers
- **Always** include legal disclaimer: *"Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý..."*
- **Transition period** (until 01/07/2026): Luật Xây dựng 2014 → 2025 in progress; note "Giai đoạn chuyển tiếp"
- **Document structure**: `## Chương I` → `### Điều 8` → `#### 8.1` → `a. Điểm a...` (blank line before list items)
- **Status markers**: draft → "DỰ THẢO", superseded → "HẾT HIỆU LỰC"

Full rules: [.agents/AGENTS.md](../.agents/AGENTS.md)
Formatting patterns: [.md/knowledge/session_learnings.md](../.md/knowledge/session_learnings.md)  
VN legal plugin docs: [docs/user-guide/vn-legal.md](../docs/user-guide/vn-legal.md)

## CCBA Identity

- **Official documents**: formal Vietnamese, professional, concise
- **Technical reports**: mixed Vietnamese-English (technical terms in English)
- **Footer**: *Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

Full branding guide: [.agents/AGENTS.md](../.agents/AGENTS.md#2-ccba-identity-voice-ban-sac-phong-cach-giao-tiep)

## Environment

- **Windows primary** (PowerShell) — beware OneDrive Unicode path issues with NFC/NFD
- **Optional `.env`** at project root: `AI_GATEWAY_URL`, `AI_GATEWAY_KEY`, `AI_MODEL`, `LLAMA_CLOUD_API_KEY`
- **No secrets in code** — all credentials via env vars

## Pitfalls

- Missing `[llm]` extra → `ImportError` for Gemini/LlamaParse providers
- Package not installed in editable mode → `ModuleNotFoundError: mdconverter`
- Plugin not loading → check entry-point in `pyproject.toml` and `PluginManager.load_plugins()` call
- OneDrive Unicode paths → use `[System.IO.Directory]::GetDirectories()` instead of `Get-ChildItem`
