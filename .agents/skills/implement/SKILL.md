---
name: implement
description: Implement a piece of work based on a spec or set of tickets.
disable-model-invocation: true
bundle: _core
triggers:
- implement
- implement spec
- implement ticket
---
Implement the work described by the user in the spec or tickets.

Use `/ccba-tdd` where possible, at pre-agreed seams.

## Context Budget Management & Early Escalation
 
To prevent context exhaustion (which causes misleading "User cancelled agent execution" errors):
 
1. **Scoped Tests Only**: Always run pytest on individual test files (`python scripts/safe_pytest.py -f tests/test_specific.py`), never on entire directories.
2. **Loop Budget & Early Escalation**:
   - Maximum **5 edit→test cycles** per seam/test file.
   - **Early Escalation (Cycle 3)**: If test still fails after **3 attempts** due to deep logic errors, concurrency, or multi-file dependencies, STOP blind guessing. Formulate a **Deep Problem Brief** (Failure Manifest, Tested Hypotheses, Code Seams, Error Logs).
   - **Hard Stop (Cycle 5)**: If 5 attempts fail, stop immediately, commit WIP, and activate **Boost Escalation Gate** (recommend the user run `/boost [brief]` for deep multi-agent reasoning).
3. **Full Suite — Once at the End**: Run the complete test suite only **once** at the very end, preferably via `python scripts/safe_pytest.py --allow-unscoped` to detach from the daemon process.
4. **Invalid Args Signal**: If you encounter `invalid tool call (invalid_args)` errors twice in a row, stop immediately — context budget is nearly depleted. Commit WIP and inform the user.

## Completion Steps

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, use `/ccba-code-review` to review the work.

Before committing, check if any **structural changes** were made (new/renamed/deleted directories, packages, scripts, skills, or workflows). If yes, run `python scripts/update_arch_stats.py` to auto-update architecture metrics, and update `architecture-sync/SKILL.md` if necessary. CI will block your PR if you forget to do this.

Commit your work to the current branch.

