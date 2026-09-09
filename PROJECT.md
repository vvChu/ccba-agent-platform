# Project: CCBA Agent Platform Standardization & Harmonization

## Architecture
- **Skill Layer**: `.agents/skills/<skill_name>/SKILL.md`, `references/*.md`, `templates/*.md`
- **Catalog Registry**: `.agents/skills/platform-loader/catalog.yaml` compiled from `SKILL.md` frontmatter via `scripts/governance/compile_catalog.py`
- **Governance & Validation**: `scripts/validate_skills.py` backed by `packages/ccba-harness/src/ccba_harness/skill_validator.py`
- **CI Test Suite**: `tests/governance/test_workflow_script_parity.py`, `test_taxonomy_integrity.py`, `test_orchestrator_parity.py`
- **Documentation & Templates**: Root documents (`README.md`, `PLATFORM.md`, `CONTEXT.md`, `AGENTS.md`, `.agents/AGENTS.md`), skill templates in `ccba-setup-skills/templates/`

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Frontmatter Command Activation | Set `user-invocable: true` and `command: /<name>` in frontmatter of all 24 Standalone/Master skills and active rituals | M1 | Survey (Explorer 1) |
| 2 | GPI Metrics Backfill | Backfill GPI metrics blocks from `BLUEPRINT-2026-SKILLS-001` so `validate_skills.py --enforce-gpi` passes for all skills | M1 | Survey (Explorer 1) |
| 3 | Catalog Compilation & Check | Regenerate `.agents/skills/platform-loader/catalog.yaml` via `compile_catalog.py` and verify zero drift with `--check` | M1 | Survey (Explorer 1) |
| 4 | Sanitization of `ccba-ask` & boundaries | Replace phantom commands (`/ccba-to-tickets`, `/ccba-triage`, etc.) in `ccba-ask/SKILL.md` & `PHASE-BOUNDARIES.md` | M2 | Survey (Explorer 2) |
| 5 | Sanitization of Spoke Templates | Sanitize outdated commands and aliases in `ccba-setup-skills/templates/*.md` | M2 | Survey (Explorer 2) |
| 6 | Top-level Documentation Sanitization | Clean up unregistered slash commands across `README.md`, `PLATFORM.md`, `CONTEXT.md`, `AGENTS.md`, `.agents/AGENTS.md` | M2 | Survey (Explorer 2) |
| 7 | Broken Relative Links Resolution | Fix all 14 broken relative markdown links in `.agents/skills/**` (in `references/` and templates) | M3 | Survey (Explorer 2) |
| 8 | Upgrade `skill_validator.py` | Add `validate_markdown_links()`, `audit_slash_commands()`, and `audit_skill_directory()` in `ccba-harness` | M4 | Survey (Explorer 3) |
| 9 | Upgrade `test_workflow_script_parity.py` | Expand document collection to `SKILLS_DIR.rglob("*.md")` to enforce valid links in all `references/*.md` | M4 | Survey (Explorer 3) |
| 10 | Upgrade `test_taxonomy_integrity.py` | Add tests enforcing zero unregistered slash commands in skills/README and standalone catalog parity | M4 | Survey (Explorer 3) |
| 11 | End-to-End Acceptance & Hardening | Run all test suites, verify 100% pass, zero drift, zero broken links, clean Forensic Audit | M5 | Acceptance Criteria |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Standalone Skills Command Activation & Catalog Compilation | Feature 1, 2, 3: Frontmatters, GPI backfill, compile `catalog.yaml` | none | DONE |
| M2 | Documentation & Template Drift Sanitization | Feature 4, 5, 6: Sanitize `ccba-ask`, templates, root docs | M1 | DONE |
| M3 | Broken Relative Links Resolution | Feature 7: Fix all 14 broken relative links in `.agents/skills/**` | none | DONE |
| M4 | Automated CI Parity Gate Enforcement | Feature 8, 9, 10: Upgrade `skill_validator.py` & governance test suites | M1, M2, M3 | DONE |
| M5 | Final Acceptance & Forensic Verification | Feature 11: 100% CI pass, zero unregistered commands, Forensic Auditor clean | M1, M2, M3, M4 | DONE |

## Interface Contracts
### Frontmatter ↔ Catalog Compiler (`compile_catalog.py`)
- Each user-invocable skill MUST declare:
  ```yaml
  name: <skill-name>
  description: <description>
  user-invocable: true
  command: /<canonical-name>
  ```
- `compile_catalog.py` extracts `command` and updates `catalog.yaml` under `services.<category>.<skill-name>.command`.
- `compile_catalog.py --check` returns exit code 0 when frontmatter commands match `catalog.yaml` exactly.

### Frontmatter ↔ Skills Validator (`validate_skills.py --enforce-gpi`)
- Skills must contain valid YAML frontmatter and pass Gate 0, Gate 1, and GPI threshold (GPI >= 12.0) with S, K, A, P metrics.

### Skill Documentation ↔ Slash Command Linter (`SkillValidator` & `test_taxonomy_integrity.py`)
- Slash commands matching `/[a-z0-9_-]+` in markdown text must be registered in `catalog.yaml` or be an allowed host/system command (e.g. `/boost`).
- HTML tags (e.g. `</div>`), URLs (e.g. `/path`), and file paths (e.g. `/src`) must be suppressed from slash command checks.

### Markdown Links ↔ Link Linter (`test_workflow_script_parity.py` & `SkillValidator`)
- All relative links `[text](target)` in all `*.md` files under `.agents/skills/` must resolve to an existing file on disk, excluding code blocks and URL anchors.

## Code Layout
- `packages/ccba-harness/src/ccba_harness/skill_validator.py`: Core skill validator library.
- `scripts/governance/compile_catalog.py`: Catalog generator & drift check script.
- `scripts/validate_skills.py`: Skills validation CLI.
- `tests/governance/`: Pytest test suite for platform governance.
- `.agents/skills/`: All 67 skills definitions and reference documents.
