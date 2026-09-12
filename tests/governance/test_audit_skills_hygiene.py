"""test_audit_skills_hygiene.py - Automated Governance Tests for Skills Hygiene (HUB-ADR-0058).

Verifies:
1. Real platform workspace satisfies 100% of skills hygiene standards (69 skills GREEN, 0 RED, 0 YELLOW).
2. Negative tests for Frontmatter SSOT (metadata.version, metadata.author, syntax errors).
3. Negative tests for Clean Dead Wood & ClaudeKit remnants.
4. Negative tests for ADR-0057 Directory Hygiene (stray root files, non-.md in references/).
5. Negative tests for Windows PowerShell Compatibility (bashisms, xargs, command substitution $(...)).
6. Negative tests for Safe Headless Process Invocation (Start-Process try/catch).
7. Negative tests for broken relative links in references/ ([SKILL.md](SKILL.md)).
8. Negative & positive tests for Level 3 Reference Index and Router INDEX.md deep resolution.
9. CLI argument handling (--check, --file, --report, --json, --verbose).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from scripts.governance.audit_skills_hygiene import (
    audit_all_skills,
    audit_skill,
    check_skills_hygiene,
    main,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _create_minimal_valid_skill(skill_dir: Path, name: str = "test-skill") -> Path:
    """Helper to create a fully compliant minimal skill directory."""
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md = skill_dir / "SKILL.md"
    content = f"""---
name: {name}
description: Minimal compliant test skill for hygiene test suite.
user-invocable: true
metadata:
  author: CCBA
  version: 1.0.0
bundle: _core
tier: kernel
---
# {name}

Process and workflow description.

## Process

1. First step.
   **Tiêu chí hoàn thành:** Step 1 completed.
"""
    skill_md.write_text(content, encoding="utf-8")
    return skill_md


# ---------------------------------------------------------------------------
# 1. Real Codebase Verification
# ---------------------------------------------------------------------------


def test_real_codebase_skills_hygiene_100_percent_compliant() -> None:
    """Verify that all active skills in the real workspace pass 100% of hygiene standards."""
    results = audit_all_skills(PROJECT_ROOT)
    assert len(results) >= 60, f"Expected >= 60 skills, found {len(results)}"

    red_skills = [r for r in results if r.status == "RED"]
    yellow_skills = [r for r in results if r.status == "YELLOW"]

    assert len(red_skills) == 0, (
        f"Detected {len(red_skills)} RED skills:\n"
        + "\n".join(
            f"  * {r.name}: {[i.detail for i in r.issues if i.severity == 'RED']}"
            for r in red_skills
        )
    )
    assert len(yellow_skills) == 0, (
        f"Detected {len(yellow_skills)} YELLOW skills:\n"
        + "\n".join(
            f"  * {r.name}: {[i.detail for i in r.issues if i.severity == 'YELLOW']}"
            for r in yellow_skills
        )
    )

    clean, msg = check_skills_hygiene(PROJECT_ROOT)
    assert clean is True
    assert "100% compliant" in msg


# ---------------------------------------------------------------------------
# 2. Metadata Governance Tests
# ---------------------------------------------------------------------------


def test_audit_catches_missing_metadata_version(tmp_path: Path) -> None:
    """Verify missing metadata.version triggers a YELLOW warning."""
    skill_dir = tmp_path / "skill-no-ver"
    _create_minimal_valid_skill(skill_dir, "skill-no-ver")

    # Overwrite SKILL.md without metadata.version
    (skill_dir / "SKILL.md").write_text(
        """---
name: skill-no-ver
description: Missing version test.
metadata:
  author: CCBA
---
# Skill
""",
        encoding="utf-8",
    )

    res = audit_skill(skill_dir)
    assert res.status == "YELLOW"
    assert any("Missing metadata.version" in i.detail for i in res.issues)


def test_audit_catches_missing_metadata_author(tmp_path: Path) -> None:
    """Verify missing metadata.author triggers a RED violation."""
    skill_dir = tmp_path / "skill-no-author"
    _create_minimal_valid_skill(skill_dir, "skill-no-author")

    # Overwrite SKILL.md without metadata.author
    (skill_dir / "SKILL.md").write_text(
        """---
name: skill-no-author
description: Missing author test.
metadata:
  version: 1.0.0
---
# Skill
""",
        encoding="utf-8",
    )

    res = audit_skill(skill_dir)
    assert res.status == "RED"
    assert any("Missing or empty metadata.author" in i.detail for i in res.issues)


def test_audit_catches_corrupt_or_missing_frontmatter(tmp_path: Path) -> None:
    """Verify missing or malformed YAML frontmatter triggers a RED violation."""
    skill_dir = tmp_path / "skill-no-fm"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Pure Markdown without frontmatter\n", encoding="utf-8")

    res = audit_skill(skill_dir)
    assert res.status == "RED"
    assert any("Missing YAML frontmatter" in i.detail for i in res.issues)


# ---------------------------------------------------------------------------
# 3. Clean Dead Wood Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "forbidden_content,expected_label",
    [
        ("/ck:review-code", "ClaudeKit Command (/ck:*)"),
        ("Use /ultrathink before proceeding.", "ClaudeKit Command (/ultrathink)"),
        ("Run git-manager commit", "ClaudeKit Tool (git-manager)"),
        ("<tasks>\n<task>Task 1</task>\n</tasks>", "Claude Tasks XML tag (<tasks>)"),
        ("Call TaskCreate to track work.", "Claude Native Tasks"),
        ("Invoke AskUserQuestion for input.", "Claude Tool (AskUserQuestion)"),
        ("Refer to code-reviewer.md template.", "Missing ClaudeKit Template (code-reviewer.md)"),
        ("Read codebase-summary.md file.", "Missing ClaudeKit File (codebase-summary.md)"),
    ],
)
def test_audit_catches_dead_wood_remnants(
    tmp_path: Path, forbidden_content: str, expected_label: str
) -> None:
    """Verify ClaudeKit remnants and dead wood tags trigger RED violations."""
    skill_dir = tmp_path / "skill-deadwood"
    _create_minimal_valid_skill(skill_dir, "skill-deadwood")

    # Append forbidden pattern to SKILL.md
    with open(skill_dir / "SKILL.md", "a", encoding="utf-8") as f:
        f.write(f"\n{forbidden_content}\n")

    res = audit_skill(skill_dir)
    assert res.status == "RED"
    assert any(expected_label in i.detail for i in res.issues)


# ---------------------------------------------------------------------------
# 4. ADR-0057 Directory Hygiene Tests
# ---------------------------------------------------------------------------


def test_audit_catches_stray_markdown_at_root(tmp_path: Path) -> None:
    """Verify stray markdown files at skill root trigger RED violation."""
    skill_dir = tmp_path / "skill-stray"
    _create_minimal_valid_skill(skill_dir, "skill-stray")

    # Create stray root file
    (skill_dir / "EXTRA_NOTES.md").write_text("# Stray notes\n", encoding="utf-8")

    res = audit_skill(skill_dir)
    assert res.status == "RED"
    assert any("Stray markdown file at skill root: EXTRA_NOTES.md" in i.detail for i in res.issues)


def test_audit_catches_non_markdown_in_references(tmp_path: Path) -> None:
    """Verify non-markdown files inside references/ trigger RED violation."""
    skill_dir = tmp_path / "skill-non-md"
    _create_minimal_valid_skill(skill_dir, "skill-non-md")

    ref_dir = skill_dir / "references"
    ref_dir.mkdir()
    (ref_dir / "data.json").write_text('{"key": "value"}', encoding="utf-8")

    res = audit_skill(skill_dir)
    assert res.status == "RED"
    assert any("Non-markdown file in references/: data.json" in i.detail for i in res.issues)


# ---------------------------------------------------------------------------
# 5. Windows PowerShell Compatibility (Bashisms)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bashism_line,expected_detail",
    [
        ("export OPENAI_API_KEY=test", "Bashism environment export"),
        ("sudo apt install build-essential", "Linux package manager invocation"),
        ("grep -rn 'pattern' src/", "Bashism grep flag"),
        ("| grep 'pattern'", "Bashism bare grep invocation"),
        ("2>/dev/null", "Bashism error redirection"),
        ("cat list.txt | xargs rm -f", "Bashism xargs invocation"),
        ("COMMIT=$(git rev-parse HEAD)", "Bashism command substitution"),
    ],
)
def test_audit_catches_bashisms(tmp_path: Path, bashism_line: str, expected_detail: str) -> None:
    """Verify bash commands incompatible with Windows PowerShell trigger RED violations."""
    skill_dir = tmp_path / "skill-bashism"
    _create_minimal_valid_skill(skill_dir, "skill-bashism")

    with open(skill_dir / "SKILL.md", "a", encoding="utf-8") as f:
        f.write(f"\n{bashism_line}\n")

    res = audit_skill(skill_dir)
    assert res.status == "RED"
    assert any(expected_detail in i.detail for i in res.issues)


def test_audit_allows_benign_grep_and_linux_code_blocks(tmp_path: Path) -> None:
    """Verify benign grep usage in prose and explicit Linux code blocks are permitted."""
    skill_dir = tmp_path / "skill-benign"
    _create_minimal_valid_skill(skill_dir, "skill-benign")

    content_to_append = """
Dùng `git grep` hoặc `Select-String / grep` để tìm kiếm từ khóa.
Xem xét Semgrep hoặc semgrep quy chuẩn.

```bash (linux)
export LINUX_ONLY=1
sudo apt update
```
"""
    with open(skill_dir / "SKILL.md", "a", encoding="utf-8") as f:
        f.write(content_to_append)

    res = audit_skill(skill_dir)
    assert res.status == "GREEN"
    assert len(res.issues) == 0


# ---------------------------------------------------------------------------
# 6. Safe Headless Process Invocation & Relative Links
# ---------------------------------------------------------------------------


def test_audit_catches_start_process_without_try_catch(tmp_path: Path) -> None:
    """Verify Start-Process without try/catch fallback block triggers RED violation."""
    skill_dir = tmp_path / "skill-headless"
    _create_minimal_valid_skill(skill_dir, "skill-headless")

    with open(skill_dir / "SKILL.md", "a", encoding="utf-8") as f:
        f.write("\nStart-Process 'https://example.com'\n")

    res = audit_skill(skill_dir)
    assert res.status == "RED"
    assert any("Start-Process without try/catch" in i.detail for i in res.issues)


def test_audit_permits_start_process_with_try_catch(tmp_path: Path) -> None:
    """Verify Start-Process wrapped in try/catch passes cleanly."""
    skill_dir = tmp_path / "skill-headless-safe"
    _create_minimal_valid_skill(skill_dir, "skill-headless-safe")

    safe_block = """
try {
    Start-Process 'https://example.com'
} catch {
    Write-Host "Fallback to terminal output"
}
"""
    with open(skill_dir / "SKILL.md", "a", encoding="utf-8") as f:
        f.write(safe_block)

    res = audit_skill(skill_dir)
    assert res.status == "GREEN"


def test_audit_catches_broken_skill_link_in_references(tmp_path: Path) -> None:
    """Verify [SKILL.md](SKILL.md) in references/ triggers RED violation."""
    skill_dir = tmp_path / "skill-link"
    _create_minimal_valid_skill(skill_dir, "skill-link")

    ref_dir = skill_dir / "references"
    ref_dir.mkdir()
    (ref_dir / "guide.md").write_text(
        "Quay lại [SKILL.md](SKILL.md) để xem chi tiết.\n", encoding="utf-8"
    )

    res = audit_skill(skill_dir)
    assert res.status == "RED"
    assert any("Broken link [SKILL.md](SKILL.md) in references/" in i.detail for i in res.issues)


# ---------------------------------------------------------------------------
# 7. Level 3 Progressive Disclosure & Deep Router INDEX.md Resolution
# ---------------------------------------------------------------------------


def test_audit_level3_missing_index_table(tmp_path: Path) -> None:
    """Verify having references without Level 3 Reference Index triggers YELLOW."""
    skill_dir = tmp_path / "skill-l3-missing"
    _create_minimal_valid_skill(skill_dir, "skill-l3-missing")

    ref_dir = skill_dir / "references"
    ref_dir.mkdir()
    (ref_dir / "doc1.md").write_text("# Doc 1\n", encoding="utf-8")

    res = audit_skill(skill_dir)
    assert res.status == "YELLOW"
    assert any("lacks Level 3 Reference Index" in i.detail for i in res.issues)


def test_audit_level3_deep_router_resolution(tmp_path: Path) -> None:
    """Verify deep router INDEX.md properly covers subfolder references."""
    skill_dir = tmp_path / "skill-router"
    _create_minimal_valid_skill(skill_dir, "skill-router")

    # Set up references/domain/INDEX.md and references/domain/item.md
    domain_dir = skill_dir / "references" / "domain"
    domain_dir.mkdir(parents=True)
    (domain_dir / "INDEX.md").write_text(
        "# Domain Router\n\n- [Item](item.md): Detailed item.\n", encoding="utf-8"
    )
    (domain_dir / "item.md").write_text("# Item Details\n", encoding="utf-8")

    # SKILL.md indexes the router
    l3_table = """
## Bảng Tham Chiếu Cấp 3 (Progressive Disclosure)

| Tài liệu | Vai trò |
| :--- | :--- |
| `references/domain/INDEX.md` | Bộ điều hướng nghiệp vụ Domain |
"""
    with open(skill_dir / "SKILL.md", "a", encoding="utf-8") as f:
        f.write(l3_table)

    res = audit_skill(skill_dir)
    assert res.status == "GREEN", f"Unexpected issues: {[i.detail for i in res.issues]}"


def test_audit_level3_catches_uncovered_reference_in_router(tmp_path: Path) -> None:
    """Verify reference file omitted from router INDEX.md triggers YELLOW warning."""
    skill_dir = tmp_path / "skill-uncovered"
    _create_minimal_valid_skill(skill_dir, "skill-uncovered")

    domain_dir = skill_dir / "references" / "domain"
    domain_dir.mkdir(parents=True)
    (domain_dir / "INDEX.md").write_text("# Domain Router (empty)\n", encoding="utf-8")
    (domain_dir / "unindexed.md").write_text("# Unindexed File\n", encoding="utf-8")

    l3_table = """
## Progressive Disclosure

| Tài liệu | Vai trò |
| :--- | :--- |
| `references/domain/INDEX.md` | Bộ điều hướng nghiệp vụ Domain |
"""
    with open(skill_dir / "SKILL.md", "a", encoding="utf-8") as f:
        f.write(l3_table)

    res = audit_skill(skill_dir)
    assert res.status == "YELLOW"
    assert any("Reference files not indexed in Level 3 table" in i.detail for i in res.issues)


# ---------------------------------------------------------------------------
# 8. CLI Integration Tests
# ---------------------------------------------------------------------------


def test_cli_single_skill_pass(tmp_path: Path) -> None:
    """Verify CLI audit for a single valid skill returns exit code 0."""
    skill_dir = tmp_path / "cli-skill"
    skill_md = _create_minimal_valid_skill(skill_dir, "cli-skill")

    exit_code = main(["--file", str(skill_md), "--check"])
    assert exit_code == 0


def test_cli_single_skill_fail(tmp_path: Path) -> None:
    """Verify CLI audit for a skill with bashism returns exit code 1."""
    skill_dir = tmp_path / "cli-fail-skill"
    skill_md = _create_minimal_valid_skill(skill_dir, "cli-fail-skill")
    with open(skill_md, "a", encoding="utf-8") as f:
        f.write("\nexport BAD_VAR=1\n")

    exit_code = main(["--file", str(skill_md), "--check"])
    assert exit_code == 1


def test_cli_json_and_report_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify CLI --json outputs valid JSON and --report writes report file."""
    skill_dir = tmp_path / "cli-json-skill"
    skill_md = _create_minimal_valid_skill(skill_dir, "cli-json-skill")
    report_file = tmp_path / "out_report.md"

    exit_code = main([
        "--file",
        str(skill_md),
        "--json",
        "--report",
        str(report_file),
    ])
    assert exit_code == 0
    assert report_file.exists()
    assert report_file.read_text(encoding="utf-8").startswith("# 📊")

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "PASS"
    assert data["total"] == 1
    assert data["green_count"] == 1


def test_check_skills_hygiene_handles_workflow_file(tmp_path: Path) -> None:
    """Verify check_skills_hygiene safely ignores workflow targets."""
    wf_file = tmp_path / ".agents" / "workflows" / "sample_wf.md"
    wf_file.parent.mkdir(parents=True)
    wf_file.write_text("# Workflow\n", encoding="utf-8")

    clean, msg = check_skills_hygiene(PROJECT_ROOT, target_path=wf_file)
    assert clean is True
    assert "workflow" in msg.lower()


# ---------------------------------------------------------------------------
# 9. Advanced Adversarial & Edge Case Tests
# ---------------------------------------------------------------------------


def test_audit_permits_ripgrep_in_markdown(tmp_path: Path) -> None:
    """Verify that ripgrep -i does not trigger false positive bashism."""
    skill_dir = tmp_path / "skill-ripgrep"
    _create_minimal_valid_skill(skill_dir, "skill-ripgrep")

    with open(skill_dir / "SKILL.md", "a", encoding="utf-8") as f:
        f.write("\nUse ripgrep -i to search for patterns rapidly.\n")

    res = audit_skill(skill_dir)
    assert res.status == "GREEN"
    assert len(res.issues) == 0


def test_audit_catches_export_with_numbers_and_lowercase(tmp_path: Path) -> None:
    """Verify export VAR_1= and export apiKey= are caught as bashisms."""
    skill_dir = tmp_path / "skill-export-vars"
    _create_minimal_valid_skill(skill_dir, "skill-export-vars")

    with open(skill_dir / "SKILL.md", "a", encoding="utf-8") as f:
        f.write("\nexport S3_BUCKET_1=prod\nexport api_key='secret'\n")

    res = audit_skill(skill_dir)
    assert res.status == "RED"
    bashism_issues = [i for i in res.issues if i.category == "Windows Bashism"]
    assert len(bashism_issues) == 2


def test_audit_catches_command_substitution_with_quotes_and_flags(tmp_path: Path) -> None:
    """Verify $(git log -1 --format="%h") is caught as command substitution."""
    skill_dir = tmp_path / "skill-subst"
    _create_minimal_valid_skill(skill_dir, "skill-subst")

    with open(skill_dir / "SKILL.md", "a", encoding="utf-8") as f:
        f.write('\nCOMMIT=$(git log -1 --format="%h")\n')

    res = audit_skill(skill_dir)
    assert res.status == "RED"
    assert any("Bashism command substitution" in i.detail for i in res.issues)


def test_audit_catches_unprotected_start_process_among_safe_blocks(tmp_path: Path) -> None:
    """Verify an unprotected Start-Process is flagged even if preceded by a safe try/catch block."""
    skill_dir = tmp_path / "skill-mixed-headless"
    _create_minimal_valid_skill(skill_dir, "skill-mixed-headless")

    content = """
try {
    Start-Process 'https://example.com'
} catch {
    Write-Host "fallback"
}

# Unprotected call
Start-Process 'https://unprotected.com'
"""
    with open(skill_dir / "SKILL.md", "a", encoding="utf-8") as f:
        f.write(content)

    res = audit_skill(skill_dir)
    assert res.status == "RED"
    headless_issues = [i for i in res.issues if i.category == "Safe Headless Process"]
    assert len(headless_issues) == 1
    # Line number should point to the unprotected Start-Process (around line 23)
    assert headless_issues[0].line_no > 18


def test_audit_level3_multi_level_transitive_router_resolution(tmp_path: Path) -> None:
    """Verify 3+ tier nested routers transitively resolve coverage without loop or failure."""
    skill_dir = tmp_path / "skill-transitive"
    _create_minimal_valid_skill(skill_dir, "skill-transitive")

    # infra/INDEX.md -> cloud/INDEX.md -> aws.md
    cloud_dir = skill_dir / "references" / "infra" / "cloud"
    cloud_dir.mkdir(parents=True)
    (skill_dir / "references" / "infra" / "INDEX.md").write_text(
        "# Infra\n- [cloud](cloud/INDEX.md)\n", encoding="utf-8"
    )
    (cloud_dir / "INDEX.md").write_text("# Cloud\n- [aws](aws.md)\n", encoding="utf-8")
    (cloud_dir / "aws.md").write_text("# AWS Docs\n", encoding="utf-8")

    l3_table = """
## Progressive Disclosure

| Tài liệu | Vai trò |
| :--- | :--- |
| `references/infra/INDEX.md` | Bộ điều hướng hạ tầng |
"""
    with open(skill_dir / "SKILL.md", "a", encoding="utf-8") as f:
        f.write(l3_table)

    res = audit_skill(skill_dir)
    assert res.status == "GREEN", f"Unexpected issues: {[i.detail for i in res.issues]}"


def test_audit_level3_master_references_index_resolution(tmp_path: Path) -> None:
    """Verify references/INDEX.md routes reference files directly under references/."""
    skill_dir = tmp_path / "skill-master-idx"
    _create_minimal_valid_skill(skill_dir, "skill-master-idx")

    ref_dir = skill_dir / "references"
    ref_dir.mkdir(parents=True)
    (ref_dir / "INDEX.md").write_text("# Master\n- [guide](guide.md)\n", encoding="utf-8")
    (ref_dir / "guide.md").write_text("# Guide\n", encoding="utf-8")

    l3_table = """
## Progressive Disclosure

| Tài liệu | Vai trò |
| :--- | :--- |
| `references/INDEX.md` | Master Reference Router |
"""
    with open(skill_dir / "SKILL.md", "a", encoding="utf-8") as f:
        f.write(l3_table)

    res = audit_skill(skill_dir)
    assert res.status == "GREEN", f"Unexpected issues: {[i.detail for i in res.issues]}"


def test_audit_level3_directory_reference_in_table(tmp_path: Path) -> None:
    """Verify referring to a directory like `references/sub/` covers its INDEX.md and sub-files."""
    skill_dir = tmp_path / "skill-dir-ref"
    _create_minimal_valid_skill(skill_dir, "skill-dir-ref")

    sub_dir = skill_dir / "references" / "sub"
    sub_dir.mkdir(parents=True)
    (sub_dir / "INDEX.md").write_text("# Sub\n- [module](module.md)\n", encoding="utf-8")
    (sub_dir / "module.md").write_text("# Module\n", encoding="utf-8")

    l3_table = """
## Progressive Disclosure

| Thư mục | Vai trò |
| :--- | :--- |
| `references/sub/` | Sub Router Folder |
"""
    with open(skill_dir / "SKILL.md", "a", encoding="utf-8") as f:
        f.write(l3_table)

    res = audit_skill(skill_dir)
    assert res.status == "GREEN", f"Unexpected issues: {[i.detail for i in res.issues]}"


def test_cli_no_check_returns_zero_on_violations(tmp_path: Path) -> None:
    """Verify CLI with --no-check returns exit code 0 even if skill has violations."""
    skill_dir = tmp_path / "cli-no-check"
    skill_md = _create_minimal_valid_skill(skill_dir, "cli-no-check")
    with open(skill_md, "a", encoding="utf-8") as f:
        f.write("\nexport BAD_VAR=1\n")

    exit_code = main(["--file", str(skill_md), "--no-check"])
    assert exit_code == 0

