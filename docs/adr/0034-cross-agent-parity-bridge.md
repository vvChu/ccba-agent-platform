# 34. Cross-Agent Parity Bridge for AGENTS.md and CLAUDE.md

Date: 2026-08-15
Status: Approved

## Context
Various AI coding agent tools look for configuration files in specific root locations. While many open tools recognize `/AGENTS.md`, Anthropic's Claude Code natively expects `/CLAUDE.md` at the repository root. Previously, the platform's constitution was confined to `.agents/AGENTS.md`, leaving the workspace root without standardized entry points for third-party agent tools.

Following Matt Pocock's "A Complete Guide To AGENTS.md" on cross-tool interoperability and `CLAUDE.md` symlinking/bridging, the platform establishes root configuration parity.

## Decisions

1. **Root Configuration Parity**:
   - Establish `/AGENTS.md` at the repository root containing the minimal platform anchor and progressive disclosure breadcrumbs.
   - Maintain `/CLAUDE.md` referencing `/AGENTS.md` (or symlinked) to guarantee native auto-discovery for Claude Code and related tools.
   - Keep `.agents/AGENTS.md` synchronized or redirected to the root standard.

2. **Unified Progressive Entry Point**:
   - Both root configuration files point to the same modular rules in `docs/rules/` and skills in `.agents/skills/`.

## Consequences
- Guarantees seamless onboarding and behavior compliance regardless of whether engineers use Antigravity, Claude Code, Cursor, or OpenCode agents.
- Standardizes the platform's open ecosystem alignment.
