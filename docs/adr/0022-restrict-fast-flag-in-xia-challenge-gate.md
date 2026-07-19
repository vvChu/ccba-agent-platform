# Restrict --fast from fully bypassing the Challenge Hard Gate in ccba-xia

The `ccba-xia` skill's Pha 4 (Challenge) is a Hard Gate — no planning happens until trade-offs are confronted. The `--fast` flag was originally designed to skip this gate entirely for speed.

We decided to restrict `--fast` so it can never fully bypass Pha 4. Even in fast mode, the agent must self-generate and self-answer at least 3 critical challenge questions and record them in the implementation plan. The `--auto` flag remains unchanged (full process, auto-approved gates).

The alternative — letting `--fast` skip Challenge entirely — was rejected because porting external code carries inherently high risk (license violations, architectural conflicts, hidden dependencies). Saving a few minutes of analysis is not worth the cost of blindly transplanting incompatible code into the Platform.

## Consequences

- `--fast` plans will always carry a `[!WARNING]` header noting the abbreviated review.
- `--copy-raw` mode cannot be combined with `--fast`, since skipping both structural adaptation and critical review creates unacceptable risk.
