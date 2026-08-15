# 36. Brownfield Spoke Adoption and Non-Destructive Onboarding

Date: 2026-08-15
Status: Approved

## Context
Previously, the platform's initialization workflow (`/ccba-init-spoke`) assumed greenfield projects (empty or newly created directories). Running `init-spoke` on an existing, mature repository (e.g. `IDOP-CCBA-WAY`) posed severe risks:
1. **Destructive Overwriting**: Re-scaffolding unconditionally overwrote `.md/workspace_context.yaml`, destroying custom document groups (`governance_constitution`, `system_blueprint`), milestones, and custom reading sequences.
2. **Constitution Drift**: Overwriting existing tailored `AGENTS.md` and `CLAUDE.md` with generic templates.
3. **Execution Friction**: Lack of automated stack detection (e.g. PowerShell/SPFx vs Python vs Node.js) required manual intervention.

## Decisions

1. **Dedicated Non-Destructive Spoke Adopter Engine (`/ccba-adopt-spoke`)**:
   - Establish `scripts/spoke/spoke_adopter.py` and CLI `scripts/adopt_spoke.py` designed specifically for brownfield projects.
   - Implement a 3-tier Discovery Matrix assessing existing Git repos, language stacks, existing `.md/` structures, tailored `AGENTS.md`, and custom data models.

2. **Additive Schema Merging Protocol**:
   - `workspace_context.yaml` is merged non-destructively: all existing Spoke fields (custom milestones, document groups, databases) are preserved 100%.
   - Platform compatibility keys (`project.name`, `project.type`, `project.mode`, `project.hub_path`, `must_read`, `do_not_touch`) are injected additively.
   - Automatic timestamped backup (`workspace_context.yaml.bak_<timestamp>`) is created prior to any file modification.

3. **Brownfield Safety Guard in `/ccba-init-spoke`**:
   - `/ccba-init-spoke` actively inspects the target directory. If existing `.md/`, `workspace_context.yaml`, or substantive source code is detected, it blocks re-initialization and safely redirects to `/ccba-adopt-spoke`.

4. **Automated Security & Registration Pipeline**:
   - Installs the Maskara pre-commit hook in `.git/hooks/pre-commit` if a Git repository is present.
   - Selectively injects skills and workflows matching the detected project type (`_core` + detected bundle) and registers the Spoke in the encrypted Hub Spoke Registry.

## Consequences
- Completely eliminates risk of data loss or configuration destruction when connecting existing enterprise projects to CCBA Platform.
- Streamlines onboarding of mature consulting, software, and BIM delivery workspaces.
- Maintains backwards and forwards compatibility across all Spoke configurations.
