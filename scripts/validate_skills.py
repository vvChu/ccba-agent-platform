#!/usr/bin/env python3
"""validate_skills.py - CLI tool for validating CCBA Agent Skills.

Enforces guidelines from "Writing Great Agent Skills":
- Validates frontmatter (name, description, disable-model-invocation).
- Limits description length for model-invoked skills to 180 characters.
- Ensures all workflow/process steps contain a clear Completion Criterion.
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

# Enforce UTF-8 output on Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Patterns
FRONTMATTER_RE = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n", re.DOTALL)
STEP_LINE_RE = re.compile(r"^\s*([0-9]+)\.\s+(.*)$")

# Header keywords that indicate a workflow/steps section
WORKFLOW_HEADERS = {
    "workflow",
    "quy trình",
    "các bước",
    "steps",
    "hành động",
    "chuyển đổi",
    "tiến hành",
    "thực hiện",
}

# Header keywords that temporarily suspend steps parsing
EXCLUSION_HEADERS = {
    "lưu ý",
    "chú ý",
    "notes",
    "yêu cầu",
    "rules",
    "quy tắc",
    "tham chiếu",
    "reference",
    "giới thiệu",
    "introduction",
    "tổng quan",
    "overview",
    "chuẩn bị",
    "setup",
}


def parse_skill_file(file_path: Path) -> tuple[dict, str]:
    """Parse frontmatter and body of a SKILL.md file."""
    content = file_path.read_text(encoding="utf-8")

    # Extract frontmatter
    match = FRONTMATTER_RE.match(content)
    if not match:
        raise ValueError("Missing frontmatter delimiter '---'")

    yaml_block = match.group(1)
    try:
        meta = yaml.safe_load(yaml_block)
    except Exception as e:
        raise ValueError(f"Failed to parse frontmatter YAML: {e}") from e

    if meta is None:
        meta = {}
    elif not isinstance(meta, dict):
        raise ValueError("Frontmatter YAML is not a valid mapping/dictionary")

    body = content[match.end() :]
    return meta, body


def analyze_steps_completion_criteria(body: str) -> list[tuple[int, str]]:
    """Scan body for workflow steps and check for Completion Criteria.

    Returns:
        List of tuples: (line_number, error_message)
    """
    errors = []
    lines = body.splitlines()

    in_workflow_section = False
    workflow_trigger_level = None
    header_stack = []  # list of tuples: (level, text, is_workflow)
    in_code_block = False
    current_step_line = None
    current_step_num = None
    current_step_content: list[str] = []

    # We trace actual line numbers in the full file.
    # To do that, we count frontmatter lines too.
    # We will compute absolute line numbers by keeping track of the index.

    for idx, line in enumerate(lines):
        line_strip = line.strip()

        # Track code blocks to avoid parsing content inside them
        if line_strip.startswith("```"):
            in_code_block = not in_code_block
            if current_step_line is not None:
                current_step_content.append(line)
            continue

        if in_code_block:
            if current_step_line is not None:
                current_step_content.append(line)
            continue

        # Detect headers
        if line_strip.startswith("#"):
            # If we were tracking a step, evaluate it before changing headers
            if current_step_line is not None:
                step_body = "\n".join(current_step_content)
                if not (
                    "**Completion Criterion:**" in step_body
                    or "**Tiêu chí hoàn thành:**" in step_body
                ):
                    errors.append(
                        (
                            current_step_line,
                            f"Step {current_step_num} is missing a Completion Criterion ('**Completion Criterion:**' or '**Tiêu chí hoàn thành:**')",
                        )
                    )
                current_step_line = None
                current_step_num = None
                current_step_content = []

            # Calculate header level and clean text
            level = len(line_strip) - len(line_strip.lstrip("#"))
            header_text = line_strip.lstrip("#").strip().lower()

            # Pop from stack while level in stack >= new level
            while header_stack and header_stack[-1][0] >= level:
                header_stack.pop()

            # Determine is_workflow status
            is_exclusion = any(kw in header_text for kw in EXCLUSION_HEADERS)
            is_workflow_keyword = any(kw in header_text for kw in WORKFLOW_HEADERS)

            if is_workflow_keyword and not is_exclusion:
                is_workflow = True
            elif is_exclusion:
                is_workflow = False
            else:
                # Inherit from parent in stack if present, else False
                is_workflow = header_stack[-1][2] if header_stack else False

            header_stack.append((level, header_text, is_workflow))
            in_workflow_section = is_workflow

            # Track workflow trigger level
            if in_workflow_section:
                if workflow_trigger_level is None:
                    workflow_trigger_level = level
            else:
                workflow_trigger_level = None
            continue

        if not in_workflow_section:
            continue

        # ONLY validate steps if they are at the workflow trigger level
        current_level = header_stack[-1][0] if header_stack else 0
        if current_level != workflow_trigger_level:
            continue

        # Detect step starting line (e.g. "1. Do something")
        step_match = STEP_LINE_RE.match(line)
        if step_match:
            # If we already have a step in progress, validate it first
            if current_step_line is not None:
                step_body = "\n".join(current_step_content)
                if not (
                    "**Completion Criterion:**" in step_body
                    or "**Tiêu chí hoàn thành:**" in step_body
                ):
                    errors.append(
                        (
                            current_step_line,
                            f"Step {current_step_num} is missing a Completion Criterion ('**Completion Criterion:**' or '**Tiêu chí hoàn thành:**')",
                        )
                    )

            # Start new step
            current_step_line = idx + 1  # 1-indexed (in body coordinates, we will offset later)
            current_step_num = step_match.group(1)
            current_step_content = [line]
        elif current_step_line is not None:
            # Accumulate content for current step
            current_step_content.append(line)

    # Check the last step of the file
    if current_step_line is not None:
        step_body = "\n".join(current_step_content)
        if not (
            "**Completion Criterion:**" in step_body or "**Tiêu chí hoàn thành:**" in step_body
        ):
            errors.append(
                (
                    current_step_line,
                    f"Step {current_step_num} is missing a Completion Criterion ('**Completion Criterion:**' or '**Tiêu chí hoàn thành:**')",
                )
            )

    return errors


def validate_skill(file_path: Path) -> list[str]:
    """Validate a single SKILL.md file.

    Returns a list of error messages. Empty list if valid.
    """
    errors = []
    try:
        meta, body = parse_skill_file(file_path)
    except ValueError as e:
        return [f"[Critical Error] {e}"]

    # Find frontmatter end line to offset body line numbers
    content = file_path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(content)
    frontmatter_line_count = len(match.group(0).splitlines()) if match else 0

    # 1. Frontmatter Validation
    name = meta.get("name")
    if not name:
        errors.append("Frontmatter Error: Missing or empty 'name'")

    desc = meta.get("description")
    if not desc:
        errors.append("Frontmatter Error: Missing or empty 'description'")
    else:
        # Check model-invoked status
        # Matt Pocock uses disable-model-invocation: true.
        # CCBA may also support custom YAML tags like user-invocable or disable-model-invocation.
        # We check disable-model-invocation: true
        disable_model = meta.get("disable-model-invocation", False)

        # If model-invoked (disable_model is False), enforce length limit of 180 chars
        if not disable_model:
            desc_len = len(desc)
            if desc_len > 180:
                errors.append(
                    f"Frontmatter Error: 'description' is too long ({desc_len} chars). "
                    f"Max allowed for model-invoked skills is 180 chars to optimize context load."
                )

    # 2. Steps Completion Criteria Validation
    step_errors = analyze_steps_completion_criteria(body)
    for step_line, err_msg in step_errors:
        # Offset line number to match absolute file coordinates
        abs_line = frontmatter_line_count + step_line
        errors.append(f"[L{abs_line}] {err_msg}")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate CCBA Agent Skills.")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Specific SKILL.md file paths or directories to scan. If omitted, scans .agents/skills/ recursively.",
    )
    parser.add_argument("--root", default=".", help="Workspace root directory")
    args = parser.parse_args()

    project_root = Path(args.root).resolve()

    # Determine files to scan
    skill_files: list[Path] = []

    if args.paths:
        for p in args.paths:
            path_obj = Path(p)
            if not path_obj.is_absolute():
                path_obj = project_root / path_obj

            if path_obj.is_file():
                if path_obj.name == "SKILL.md":
                    skill_files.append(path_obj)
            elif path_obj.is_dir():
                skill_files.extend(path_obj.rglob("**/SKILL.md"))
    else:
        # Default scan directory
        default_skills_dir = project_root / ".agents" / "skills"
        if default_skills_dir.exists():
            skill_files.extend(default_skills_dir.rglob("**/SKILL.md"))

    if not skill_files:
        print("[Skills Validator] No SKILL.md files found to validate.")
        sys.exit(0)

    print(f"[Skills Validator] Scanning {len(skill_files)} skill(s)...")
    print("-" * 70)

    total_errors = 0
    files_with_errors = 0

    for file_path in skill_files:
        try:
            rel_path = file_path.relative_to(project_root)
        except ValueError:
            rel_path = file_path

        file_errors = validate_skill(file_path)
        if file_errors:
            files_with_errors += 1
            total_errors += len(file_errors)
            print(f"\n\x1b[4mFile: {rel_path}\x1b[0m")
            for err in file_errors:
                print(f"  \x1b[31m[ERROR]\x1b[0m {err}")

    print("-" * 70)
    if total_errors > 0:
        print(
            f"[Skills Validator] Validation FAILED. Found {total_errors} errors across {files_with_errors} file(s)."
        )
        print(
            "\x1b[31m[ERROR] Skills quality guidelines violated. Please fix the errors above.\x1b[0m"
        )
        sys.exit(1)
    else:
        print("\x1b[32m[OK] All skills validated successfully! No issues detected.\x1b[0m")
        sys.exit(0)


if __name__ == "__main__":
    main()
