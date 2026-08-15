# 32. Monorepo Hierarchical AGENTS.md for CCBA Packages

Date: 2026-08-15
Status: Approved

## Context
The CCBA Agent Services Platform operates as a Python monorepo housing 8 core packages under `packages/` (`ccba-ai`, `ccba-harness`, `ccba-legal-intel`, `ccba-maskara`, `ccba-notebooklm`, `ccba-ooxml`, `ccba-pdf-prep`, `mdconverter`). Without package-level instruction files, package-specific architectural contracts (such as Public Deep Seams, isolated test targets, and domain boundaries) were either missing or forced into global documentation, inflating the base prompt context.

Following Matt Pocock's "A Complete Guide To AGENTS.md" on monorepo instruction merging, the platform establishes package-level `AGENTS.md` files.

## Decisions

1. **Package-Level AGENTS.md Invariant**:
   - Each package under `packages/{package_name}/` MUST maintain a lightweight `AGENTS.md` file (3-6 lines).
   - Content structure:
     1. **Package Purpose**: One-sentence domain scope.
     2. **Public Deep Seams**: Entry points and exported public interfaces that external callers must use.
     3. **Scoped Test Command**: Package-specific fast test invocation (e.g., `pytest packages/{pkg}/tests`).

2. **Root AGENTS.md Delegation**:
   - The root `.agents/AGENTS.md` maintains a monorepo navigation breadcrumb indicating that packages possess localized `AGENTS.md` files for package-specific development.

## Consequences
- AI Agents working on package-specific files automatically inherit contextual deep seams without context pollution at the platform level.
- Reinforces Deep Module encapsulation across all 8 internal packages.
