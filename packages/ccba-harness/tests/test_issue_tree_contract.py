"""test_issue_tree_contract.py - Deterministic Contract Tests for /ccba-issue-tree.

Verifies:
1. SKILL.md specification integrity (Fast-Tree mode, Confirmation Header, OS Awareness, MECE labels).
2. eval_ccba_issue_tree.json dataset schema & completeness.
3. Deterministic output linter enforcing MECE labels and blocking OS-incompatible shell scripts.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


def get_project_root() -> Path:
    # packages/ccba-harness/tests -> repo root
    return Path(__file__).resolve().parent.parent.parent.parent


def lint_issue_tree_output(text: str, target_os: str = "windows") -> tuple[bool, list[str]]:
    """Deterministic structural linter for /ccba-issue-tree outputs.

    Args:
        text: Raw output produced by the issue-tree generator.
        target_os: Operating system ('windows' or 'linux').

    Returns:
        tuple[bool, list[str]]: (is_valid, list of violation messages).
    """
    violations: list[str] = []

    # Check 1: If Fast-Tree, must include confirmation header
    if "[Phân loại: Fast-Tree]" in text or "Fast-Tree" in text:
        if "> 💡 [Phân loại: Fast-Tree]" not in text and "[Phân loại: Fast-Tree]" not in text:
            violations.append("Fast-Tree output missing standardized confirmation header.")

    # Check 2: MECE workplan labels check if What-Tree / Workplan is present
    if "What-Tree" in text or "gói việc" in text.lower() or "kế hoạch" in text.lower():
        required_labels = ["[ANALYSIS]", "[DECISION]", "[COMMITMENT]", "[SYNTHESIS]"]
        found_any = any(label in text for label in required_labels)
        if not found_any:
            violations.append(
                "Workplan/What-Tree must include standardized MECE labels ([ANALYSIS], [DECISION], [COMMITMENT], [SYNTHESIS])."
            )

    # Check 3: OS / Shell Awareness check
    if target_os.lower() in ("windows", "nt"):
        forbidden_bash_patterns = [
            r"\[\s+-n\s+",  # [ -n ... ]
            r"date\s+\+%s",  # date +%s
            r"\$\(date\s+",  # $(date ...)
            r"export\s+[A-Z_]+=",  # export VAR=
        ]
        for pattern in forbidden_bash_patterns:
            if re.search(pattern, text):
                violations.append(
                    f"Forbidden Unix/Bash syntax detected on Windows: pattern '{pattern}'"
                )

    return (len(violations) == 0, violations)


def test_issue_tree_skill_specification() -> None:
    root = get_project_root()
    skill_path = root / ".agents" / "skills" / "ccba-issue-tree" / "SKILL.md"
    assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

    content = skill_path.read_text(encoding="utf-8")

    # Verify frontmatter constraints
    assert "name: ccba-issue-tree" in content
    assert "bundle: _core" in content
    assert "disable-model-invocation: true" in content
    assert "command: /ccba-issue-tree" in content

    # Verify Adaptive Fast-Tree specification
    assert "Fast-Tree" in content
    assert "> 💡 [Phân loại: Fast-Tree]" in content
    assert "Adaptive Branching" in content

    # Verify OS Awareness Guard
    assert "OS & Shell Awareness Guard" in content
    assert "Windows" in content
    assert "PowerShell" in content

    # Verify 4 MECE labels
    assert "[ANALYSIS]" in content
    assert "[DECISION]" in content
    assert "[COMMITMENT]" in content
    assert "[SYNTHESIS]" in content

    # Verify Stateless principle
    assert "Stateless" in content


def test_eval_dataset_schema() -> None:
    root = get_project_root()
    dataset_path = (
        root
        / "packages"
        / "ccba-harness"
        / "src"
        / "ccba_harness"
        / "evals"
        / "datasets"
        / "eval_ccba_issue_tree.json"
    )
    assert dataset_path.exists(), f"Dataset not found at {dataset_path}"

    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) >= 4, f"Expected at least 4 test cases, found {len(data)}"

    required_keys = {"id", "category", "title", "prompt", "expected_tree_type", "expected_branches"}
    for case in data:
        assert isinstance(case, dict)
        missing = required_keys - set(case.keys())
        assert not missing, f"Test case {case.get('id')} missing keys: {missing}"


def test_linter_blocks_incompatible_shell_on_windows() -> None:
    bad_windows_output = """
    ### [ACT-01] [COMMITMENT] Dọn dẹp working tree
    ```bash
    if [ -n "$(git status --porcelain)" ]; then
      git stash push -u -m "backup-$(date +%s)"
    fi
    ```
    """
    valid, violations = lint_issue_tree_output(bad_windows_output, target_os="windows")
    assert not valid
    assert any("Forbidden Unix/Bash syntax" in v for v in violations)


def test_linter_accepts_valid_powershell_and_python_on_windows() -> None:
    good_windows_output = """
    > 💡 [Phân loại: Fast-Tree] Bài toán được xếp loại Cục bộ. Gõ '/ccba-issue-tree --full' nếu muốn mở rộng Full Tree.

    ### [ACT-01] [ANALYSIS] Khảo sát danh mục tệp rác
    ### [ACT-02] [COMMITMENT] Dọn dẹp an toàn
    ```powershell
    if ((git status --porcelain).Trim()) {
      python -m ccba_harness verify-patch
    }
    ```
    """
    valid, violations = lint_issue_tree_output(good_windows_output, target_os="windows")
    assert valid, f"Expected valid output, got violations: {violations}"
