# ADR-0021: Dual-Mode Workspace & BIGBIM Skills Retention

## Status
Accepted — 2026-07-19

## Context
Architecture review (Grill with Docs + Wayfinder, 2026-07-19) evaluated the
codebase structure of CCBA Agent Platform with empirical data from 3 research
subagents covering 77 skills, 33 scripts, and 7,635 files in `.md/`.

Two key decisions emerged:

1. **BIGBIM skills should NOT be merged.** Initial proposal suggested consolidating
   5 bigbim-* skills into a single "bigbim-quality-gate" Deep Skill. Data showed
   all 5 are deep modules (91–114 lines of content each) with zero trigger keyword
   overlap and no cross-delegation. Merging would create a 500+ line monolith
   violating KISS.

2. **Workspace structure should support multiple modes.** The `.md/` directory
   structure was designed for construction/consulting projects but creates friction
   for software development. A `project.mode` field in `workspace_context.yaml`
   now controls workspace structure: `software` (minimal `.md/`), `delivery`
   (full `.md/`), or `hybrid` (both).

## Decision
- Retain all 5 bigbim-* skills as independent peer modules.
- Introduce `project.mode: software | delivery | hybrid` in workspace_context.yaml.
- Remove dead config fields (`agent_boundaries`, `output_dirs`, `project.role`).
- Remove redundant catalog entries for 3 markdown sub-skills (table-reconstructor,
  form-template-cleaner, relative-link-patcher); keep markdown-processing as sole
  dispatcher.

## Consequences
- Future architecture scans should not re-propose merging bigbim-* skills.
- `ccba-init-spoke.md` must branch directory creation logic based on `project.mode`.
- Software Spokes get a clean workspace without construction-specific directories.
- Hub uses `mode: hybrid` to maintain both domain knowledge and software tooling.
