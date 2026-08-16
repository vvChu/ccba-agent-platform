---
name: git-guardrails
description: Guardrails to block or request explicit user permission before executing
  dangerous git operations (force push, hard reset, clean, etc.) via terminal.
disable-model-invocation: true
bundle: _software
---
# Setup Git Guardrails

Establish runtime guardrails to intercept and prevent the Agent from executing dangerous or destructive Git operations automatically.

## Destructive Git Operations

The following commands are classified as destructive/dangerous:

- `git push` (all variants including `--force` and `--delete`)
- `git reset --hard`
- `git clean -f` / `git clean -fd`
- `git branch -D`
- `git checkout .` / `git restore .` (any command that discards local uncommitted changes globally)

## Safe Execution Rules

1. **Explicit Permission Required:** The Agent MUST NEVER automatically execute any of the destructive Git commands listed above via terminal tool commands without obtaining explicit, granular permission from the user for that specific command instance.
2. **Use of Permission Request:** If a destructive command is necessary:
   - Request approval using the `ask_permission` tool (Action: `command`, Target: the prefix of the command).
   - Alternatively, output a visible text message stating the exact command, explain the necessity, and ask the user to explicitly approve or execute it.
3. **Failsafe:** If the user has not explicitly typed approval or approved the command via the interface, the Agent must treat the execution of that command as blocked.
