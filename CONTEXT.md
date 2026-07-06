# CCBA Agent Platform Context

The CCBA Agent Services Platform is a framework to develop and coordinate AI agent skills, workflows, and compliance checks across construction consulting projects.

## Language

**Hub**:
The central repository containing the master constitution, catalogs, reusable skills, and templates.
_Avoid_: Central, upstream

**Spoke**:
A downstream project-specific workspace that inherits and syncs bundles of skills/workflows from the Hub.
_Avoid_: Sub-project, spoke repo

**Skill**:
A structured set of agent guidelines, scripts, and completion criteria defined in a `SKILL.md` file.
_Avoid_: Tool, plugin

**Workflow**:
A markdown script registered as a Slash Command that directs agent actions sequentially.
_Avoid_: Scenario, command line script

**Bundle**:
A grouping of related skills and workflows organized by domain area (e.g., `_core`, `_software`, `_qc`, `_consulting`).
_Avoid_: Package bundle, module

**Hierarchical Section Parser**:
The parsing algorithm in `validate_skills.py` that tracks Markdown heading levels using a stack to determine which lines belong to a workflow section.

**Exclusion Headers**:
A set of common static headings (such as "Lưu ý", "Tham chiếu") that temporarily disable step-validation checking to prevent false positives.

**Plan Lock**:
A file-based locking mechanism (`.plan.lock`) to prevent lost updates when multiple agents concurrently modify phase status.

**Target Line Override**:
A formatting preservation technique where only specific key-value pairs (like status) in frontmatter are overwritten instead of full file re-serialization.


