# CCBA Agent Services Platform — Copilot Agent Instructions

Hub-and-spoke monorepo for CCBA agent services. This repository is the **Hub** (shared skills, workflows, packages, and scripts) used by Spoke projects.

---

## 0. Session Bootstrap (do this first)

Before planning or coding anything:

1. **Read session learnings**: `cat .md/knowledge/session_learnings.md` — loads active architectural invariants and known workarounds.
2. **Check the catalog** before writing any new utility: `cat .agents/skills/platform-loader/catalog.yaml` — Reuse-First Gate (ADR-0057). Document reuse decision in your plan.
3. **Confirm environment**: `git remote get-url origin` — if it contains `ccba-agent-platform`, you are in **Hub** mode; all Hub-only guardrails apply.

---

## 1. Build, test, and lint commands

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
uv pip install -e "packages/ccba-maskara[dev]" --system
uv pip install -e "packages/ccba-qc-core[dev]" --system

# Test suites — always scope to the affected package; never run unscoped pytest
pytest packages/mdconverter/tests/ -v --cov=src/mdconverter --cov-report=term-missing
python -m unittest discover -s scripts/tests
python scripts/eval/run_harness_evals.py --all

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

# Privacy/security scan before committing
python scripts/maskara.py scan --root .

# Catalog parity check (required after any skill change)
python scripts/governance/compile_catalog.py --check
```

---

## 2. High-level architecture

- **Workspace model**: root `pyproject.toml` uses `uv` workspace members (`packages/*`) and centralizes lint/type config for package code.
- **Hub assets**:
  - `.agents/skills/` + `.agents/workflows/`: reusable agent behavior and automation.
  - `.md/`: central knowledge and legal-document data. Root `.md/` includes `workspace_context.yaml` plus top-level directories such as `data/`, `dogfood/`, `extracted_docs/`, `knowledge/`, `projects/`, `reports/`, `scratch/`, `seminars/`, `wayfinder/`, and `youtube-learn/`.
  - `scripts/`: lifecycle hooks, docs validation, privacy scan, and CI helper tooling.
- **Service modules** (`packages/`): `ccba-ai`, `ccba-harness`, `ccba-legal-intel`, `ccba-maskara`, `ccba-notebooklm`, `ccba-ooxml`, `ccba-pdf-prep`, `ccba-qc-core`, `mdconverter`.
- **mdconverter flow**:
  - Typer CLI (`mdconverter.cli`) dispatches to command modules.
  - `ConversionPipeline` orchestrates analyze → convert → post-process → cache.
  - Converter selection is registry-based (`ConverterRegistry`) with priority order registered in `mdconverter.core.__init__`.
  - Post-processing is protocol-based (`PostProcessor`), with VN legal processing wired as default.
- **ccba-ai flow**:
  - `from ccba_ai import ai` exposes module-level singleton clients over an OpenAI-compatible gateway.
  - Built-in privacy hooks scan both input/output content.
  - Includes sync and async clients plus MCP server entry point (`ccba-mcp`).
  - Gemini embeddings use model `gemini-embedding-2` (3072 dims) with `extra_body={"drop_params": True}`.
- **Hook orchestration**:
  - `scripts/hook_runner.py` runs `session-init`, `pre-tool`, `post-tool`.
  - `pre-tool` combines privacy, naming, scout-block, and simplify-gate checks; `post-tool` runs brand enforcement.
- **SKILL.md stat counters** in `README.md`/`PLATFORM.md` are auto-generated; regenerate with `python scripts/scaffolding/arch_stats.py` instead of hand-editing.

---

## 3. Key repository conventions

- **Hub constitution**: follow Layer 1 rules in `.agents/AGENTS.md`; this repository runs in Hub mode, so Reuse-First and CCBA legal/identity constraints are mandatory.
- **Python baseline**: 3.10+, strict mypy, ruff line length 100, double quotes.
- **Imports**: absolute within package (e.g., `from mdconverter.core...`). Never import `_*` private symbols across packages.
- **Env loading**: `mdconverter` reads `.env` at CWD; `ccba-ai` searches upward for `.env`/`.env.ai-gateway`. Do not assume shared env-loading behavior.
- **Legal outputs**: preserve required status markers/disclaimer conventions from `.agents/AGENTS.md` and `packages/mdconverter/docs/user-guide/vn-legal.md`.
- **Docs validation**: `scripts/validate_docs.py` for markdown; `scripts/maskara.py scan --root .` for privacy/security alignment with CI.
- **Never call** `sys.stdout.reconfigure()` / `sys.stderr.reconfigure()` at module top-level — put it inside `main()`/entrypoints to avoid breaking pytest I/O capture.
- **Windows subprocess**: always pass `encoding="utf-8", errors="replace"` with `text=True`.
- **Directory deletion on Windows**: use `safe_rmtree` pattern (`shutil.rmtree(..., onerror=...)` that `chmod`s failing paths to `stat.S_IWRITE` then retries).
- **Simplify gate**: commits touching >400 LOC or >8 files are blocked by `pre-tool` hooks; add `# APPROVED: <reason>` comment to bypass.

---

## 4. Skill governance (required for any `.agents/skills/` change)

When creating or modifying any `SKILL.md`:

1. **Two-Stage Gate** (ADR-0057):
   - Gate 0 — Determinism: if 100% solvable by deterministic code → goes in `packages/*/src` as a Deep Seam, NOT a skill.
   - Gate 1 — Orchestration: if multi-step multi-agent coordinator → Tier 3 Composite Orchestrator.
2. **GPI score**: `GPI = 2.5S + 2.0K + 2.0A − 1.5P`. GPI ≥ 12.0 → Tier 2B Standalone Kernel Skill; GPI < 12.0 → Tier 2A Progressive Reference.
3. **Validate**: `python scripts/validate_skills.py --file .agents/skills/<name>/SKILL.md --enforce-gpi`
4. **Recompile** (mandatory after any SKILL.md create/edit/version bump):
   ```bash
   python scripts/governance/compile_catalog.py
   python scripts/governance/compile_skills_docs.py --write
   python scripts/sync_hub_adr_matrix.py
   ```
5. Skill names must use `ccba-*` or `bigbim-*` namespace in frontmatter.

---

## 5. Pull request requirements

Follow `.github/pull_request_template.md` exactly. Key mandatory items:

- **Merge Danger Assessment**:
  - **Door**: Two-way (reversible) or One-way (irreversible) change?
  - **Blast Radius**: Localized / Package-wide / Monorepo-wide / Spoke-affecting?
- **CI checklist**: catalog parity, dependency contracts, ruff, mypy, pytest, Hub-Spoke compatibility.
- **Branch naming**: `type/short-description` (e.g., `feat/add-auth`, `fix/query-timeout`).
- **Commit format**: `type(scope): description` in English. Valid types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`.
- **Atomic commits**: one logical unit per commit; never `git add . && git commit` everything together.
- **Security scan**: run `python scripts/maskara.py scan --root .` and confirm no secrets before committing.

---

## 6. Execution guardrails

- **Scoped tests only**: never run unscoped `pytest` on the full repo; always specify `packages/{pkg}/tests/`.
- **Zero polling**: after launching a background task, do NOT poll its status in a loop. Stop the turn; the runtime sends a reactive wakeup when done.
- **TDD retry cap**: max 5 edit→test rounds per seam. Escalate at round 3 (package a Deep Problem Brief); hard stop at round 5.
- **Context budget**: if you see `invalid_args` errors twice in a row, stop immediately, commit WIP, summarize state, and ask the user to open a new session.
- **Single-writer**: in multi-agent scenarios, only the Lead/Orchestrator writes to the codebase; subagents output PatchBlocks only.
- **Max workers**: 3 parallel subagents at a time; never spawn subagents of subagents (depth limit = 1).

---

## 7. Legal data invariants (ADR-0059)

- **Never fabricate VBPL clauses**: all legal citations must mirror verbatim text from official gazette sources with SHA-256 provenance.
- **Missing source**: acquire via `TVPLCrawler` or request the file from the user — do not proceed with synthetic content.
- **Current law baseline (from 01/07/2026)**: cite only in-force documents. Currently in force: Luật Xây dựng 2025 (`135/2025/QH15`), NĐ 217/2026/NĐ-CP (replaces NĐ 175 & 15), NĐ 207/2026/NĐ-CP (replaces NĐ 06). Do NOT cite superseded legislation.
- **CLI retrieval preferred**: use `python -m ccba_legal get-clause --doc <id> --clause <id>` (< 500 tokens) rather than opening raw `.md` legal files (~60 k tokens).

---

## 8. Known workarounds / error log

| Symptom | Workaround |
|---|---|
| Gemini embeddings HTTP 400 | Pass `extra_body={"drop_params": True}` and use model `gemini-embedding-2` (3072 dims) |
| Windows `subprocess` decode error | Add `encoding="utf-8", errors="replace"` to `subprocess.run(..., text=True)` |
| `rmtree` fails on Windows read-only paths | Use `safe_rmtree` with `onerror` that calls `chmod(stat.S_IWRITE)` then retries |
| `sys.stdout.reconfigure` breaks pytest | Move call inside `main()`; never at module top-level |
| `defusedxml` missing in `ccba-legal-intel` | Declared in `packages/ccba-legal-intel/pyproject.toml`; run `uv pip install -e "packages/ccba-legal-intel[dev]" --system` |
| Maskara byte-offset mis-redact with non-ASCII | `detect_secrets_in_text` returns str offsets; `apply_raw_redactions` uses byte offsets — perform redaction on `str`, not `bytes` |
| `spoke_registry.yaml` encrypted, discovery fails | Generate `spoke_registry_decrypted.yaml` locally (gitignored) for hub-mediated spoke discovery |
| arch_stats counts wrong in README/PLATFORM | Run `python scripts/scaffolding/arch_stats.py` to regenerate; never hand-edit marker lines |
