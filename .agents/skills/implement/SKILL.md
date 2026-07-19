---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets.

Use `/ccba-tdd` where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, use `/ccba-code-review` to review the work.

Before committing, check if any **structural changes** were made (new/renamed/deleted directories, packages, scripts, skills, or workflows). If yes, run the `architecture-sync` skill to update affected documentation. At minimum, verify that hardcoded statistics (skill count, workflow count, package count) in `README.md` and `PLATFORM.md` still match reality.

Commit your work to the current branch.

