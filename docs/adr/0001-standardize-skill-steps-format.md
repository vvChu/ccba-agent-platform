# 1. Standardize Skill Steps Format for Linter Validation

We decided to structure workflow steps in `SKILL.md` files as a flat, numbered list directly under the `## Quy trình thực hiện (Process)` header, and to format any nested lists as bullet points rather than numbers. This ensures that the custom linter `validate_skills.py` successfully parses and enforces the presence of Completion Criteria for all steps, while preventing regex matching conflicts on nested sub-steps.
