"""test_skill_taxonomy_linter.py - Unit tests for ADR-0066 Slash Command Distribution & COND-01 GPI.

Tests:
1. Rejection of interactive commands with bundle: _governance without scope: hub (ADR-0066).
2. Acceptance of interactive commands with bundle: _governance when declaring scope: hub.
3. Acceptance of interactive commands with bundle: _governance when annotated with # ccba:allow-hub-only-command.
4. Acceptance of interactive commands with bundle: _core.
5. Detection and rejection of mismatched declared GPI scores (COND-01).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ccba_harness.skill_validator import SkillValidator

pytestmark = [pytest.mark.fast, pytest.mark.unit]


@pytest.fixture
def validator(tmp_path: Path) -> SkillValidator:
    return SkillValidator(project_root=tmp_path)


def test_command_distribution_rejects_governance_without_scope_hub(
    validator: SkillValidator, tmp_path: Path
) -> None:
    """Verifies that interactive command in _governance without scope: hub is rejected."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        """---
name: ccba-sample-tool
bundle: _governance
tier: kernel
user-invocable: true
command: /ccba-sample-tool
gpi:
  s: 4.0
  k: 3.0
  a: 3.0
  p: 1.0
---
# Sample Tool
Instructions here.
""",
        encoding="utf-8",
    )

    issues = validator.audit_skill(skill_file, enforce_gpi=True)
    categories = [i.category for i in issues]
    assert "INVALID_COMMAND_DISTRIBUTION" in categories
    err = [i for i in issues if i.category == "INVALID_COMMAND_DISTRIBUTION"][0]
    assert "ADR-0066" in err.message
    assert "without 'scope: hub'" in err.message


def test_command_distribution_accepts_governance_with_scope_hub(
    validator: SkillValidator, tmp_path: Path
) -> None:
    """Verifies that interactive command in _governance with scope: hub passes audit."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        """---
name: ccba-sample-tool
bundle: _governance
tier: kernel
scope: hub
user-invocable: true
command: /ccba-sample-tool
gpi:
  s: 4.0
  k: 3.0
  a: 3.0
  p: 1.0
---
# Sample Tool
Instructions here.
""",
        encoding="utf-8",
    )

    issues = validator.audit_skill(skill_file, enforce_gpi=True)
    categories = [i.category for i in issues]
    assert "INVALID_COMMAND_DISTRIBUTION" not in categories


def test_command_distribution_accepts_governance_with_comment_bypass(
    validator: SkillValidator, tmp_path: Path
) -> None:
    """Verifies that interactive command in _governance with bypass annotation passes audit."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        """---
name: ccba-sample-tool
bundle: _governance
tier: kernel
user-invocable: true
command: /ccba-sample-tool
gpi:
  s: 4.0
  k: 3.0
  a: 3.0
  p: 1.0
---
# Sample Tool
# ccba:allow-hub-only-command
Instructions here.
""",
        encoding="utf-8",
    )

    issues = validator.audit_skill(skill_file, enforce_gpi=True)
    categories = [i.category for i in issues]
    assert "INVALID_COMMAND_DISTRIBUTION" not in categories


def test_command_distribution_accepts_core_bundle(
    validator: SkillValidator, tmp_path: Path
) -> None:
    """Verifies that interactive command in bundle: _core passes audit without scope."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        """---
name: ccba-sample-tool
bundle: _core
tier: kernel
user-invocable: true
command: /ccba-sample-tool
gpi:
  s: 4.0
  k: 3.0
  a: 3.0
  p: 1.0
---
# Sample Tool
Instructions here.
""",
        encoding="utf-8",
    )

    issues = validator.audit_skill(skill_file, enforce_gpi=True)
    categories = [i.category for i in issues]
    assert "INVALID_COMMAND_DISTRIBUTION" not in categories


def test_cond_01_mismatched_gpi_score_detected(validator: SkillValidator, tmp_path: Path) -> None:
    """Verifies COND-01: Detects when declared score contradicts the formula."""
    skill_file = tmp_path / "SKILL.md"
    # Formula: 2.5*4.0 + 2.0*3.0 + 2.0*3.0 - 1.5*1.0 = 10 + 6 + 6 - 1.5 = 20.5
    # Declared: 15.0 (mismatched!)
    skill_file.write_text(
        """---
name: ccba-sample-tool
bundle: _core
tier: kernel
user-invocable: true
command: /ccba-sample-tool
gpi:
  s: 4.0
  k: 3.0
  a: 3.0
  p: 1.0
  score: 15.0
---
# Sample Tool
Instructions here.
""",
        encoding="utf-8",
    )

    issues = validator.audit_skill(skill_file, enforce_gpi=True)
    categories = [i.category for i in issues]
    assert "MISMATCHED_GPI_SCORE" in categories
    err = [i for i in issues if i.category == "MISMATCHED_GPI_SCORE"][0]
    assert "COND-01" in err.message
    assert "20.5" in err.message
