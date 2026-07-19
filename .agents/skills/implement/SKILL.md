---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets.

Use `/ccba-tdd` where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, use `/ccba-code-review` to review the work.

Before committing, check if any **structural changes** were made (new/renamed/deleted directories, packages, scripts, skills, or workflows). If yes, run `python scripts/update_arch_stats.py` to auto-update architecture metrics, and update `architecture-sync/SKILL.md` if necessary. CI will block your PR if you forget to do this.

Commit your work to the current branch.

