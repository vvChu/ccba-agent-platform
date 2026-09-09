"""test_tier3_orchestrator.py - Unit tests for Tier 3 Composite Orchestrator validation.

Verifies:
1. Orchestrators declaring 'tier: orchestrator' bypass Stage 2 GPI metrics under --enforce-gpi.
2. Multi-agent orchestrators without Single-Writer Protocol (ADR-0053) are flagged.
3. Undeclared orchestration ('is-orchestrated: true' without 'tier: orchestrator') triggers Gate 1 violation.
4. evaluate_skill_file and CLI recognize Tier 3 Orchestrators seamlessly.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ccba_harness.cli import run_evaluate_gpi_cli
from ccba_harness.gpi import ArchitectureTier
from ccba_harness.skill_validator import SkillValidator


@pytest.fixture
def temp_skill_dir(tmp_path: Path) -> Path:
    """Fixture creating a temporary directory for skill testing."""
    skill_dir = tmp_path / "skills"
    skill_dir.mkdir(parents=True, exist_ok=True)
    return skill_dir


def test_valid_tier3_orchestrator_passes_enforce_gpi(temp_skill_dir: Path) -> None:
    """Verify that a valid Tier 3 Orchestrator passes audit with --enforce-gpi without needing 'gpi:'."""
    skill_file = temp_skill_dir / "ccba-test-orchestrator" / "SKILL.md"
    skill_file.parent.mkdir(parents=True, exist_ok=True)
    skill_file.write_text(
        """---
name: ccba-test-orchestrator
description: Test multi-agent orchestrator workflow.
tier: orchestrator
is-orchestrated: true
disable-model-invocation: true
bundle: _core
command: /ccba-test-orchestrator
triggers:
- test-orchestrator
---
# Test Orchestrator

Điều phối các worker subagents thực hiện nhiệm vụ.

## Single-Writer Protocol (ADR 0053)
Duy nhất Orchestrator có quyền ghi codebase và commit Git. Các worker chỉ hoạt động trong scratch read-only.

## Các bước thực hiện

### Bước 1: Khởi tạo kế hoạch
Lập team sheet và phân công worker.
- **Tiêu chí hoàn thành:** Kế hoạch sẵn sàng.

### Bước 2: Điều phối thực thi
Phân đợt worker chạy song song.
- **Tiêu chí hoàn thành:** Toàn bộ worker hoàn tất xuất báo cáo scratch.
""",
        encoding="utf-8",
    )

    validator = SkillValidator()
    issues = validator.audit_skill(skill_file, enforce_gpi=True)
    assert not issues, (
        f"Expected 0 issues for valid orchestrator, got: {[i.message for i in issues]}"
    )


def test_multi_agent_orchestrator_missing_single_writer_flagged(temp_skill_dir: Path) -> None:
    """Verify that multi-agent orchestrator lacking Single-Writer Protocol is flagged."""
    skill_file = temp_skill_dir / "ccba-bad-orchestrator" / "SKILL.md"
    skill_file.parent.mkdir(parents=True, exist_ok=True)
    skill_file.write_text(
        """---
name: ccba-bad-orchestrator
description: Bad orchestrator coordinating workers.
tier: orchestrator
is-orchestrated: true
disable-model-invocation: true
bundle: _core
command: /ccba-bad-orchestrator
triggers:
- bad-orchestrator
---
# Bad Orchestrator

Điều phối và dispatch worker subagents tự do sửa code mà không có rào chắn.

## Các bước thực hiện

### Bước 1: Khởi tạo
Chạy các subagents.
- **Tiêu chí hoàn thành:** Bước 1 xong.

### Bước 2: Hoàn tất
Chạy các workers.
- **Tiêu chí hoàn thành:** Bước 2 xong.
""",
        encoding="utf-8",
    )

    validator = SkillValidator()
    issues = validator.audit_skill(skill_file, enforce_gpi=True)
    categories = [i.category for i in issues]
    assert "SINGLE_WRITER_PROTOCOL_VIOLATION" in categories


def test_is_orchestrated_without_tier_flags_orchestration_gate_violation(
    temp_skill_dir: Path,
) -> None:
    """Verify that is-orchestrated: true without tier: orchestrator triggers ORCHESTRATION_GATE_VIOLATION."""
    skill_file = temp_skill_dir / "ccba-undeclared-orchestrator" / "SKILL.md"
    skill_file.parent.mkdir(parents=True, exist_ok=True)
    skill_file.write_text(
        """---
name: ccba-undeclared-orchestrator
description: Undeclared orchestration attempt.
is-orchestrated: true
bundle: _core
triggers:
- undeclared
---
# Undeclared Orchestrator

### Bước 1: Chạy
- **Tiêu chí hoàn thành:** Xong.
""",
        encoding="utf-8",
    )

    validator = SkillValidator()
    issues = validator.audit_skill(skill_file, enforce_gpi=True)
    categories = [i.category for i in issues]
    assert "ORCHESTRATION_GATE_VIOLATION" in categories


def test_evaluate_skill_file_recognizes_tier_orchestrator(temp_skill_dir: Path) -> None:
    """Verify that evaluate_skill_file automatically detects tier: orchestrator."""
    skill_file = temp_skill_dir / "ccba-auto-tier3" / "SKILL.md"
    skill_file.parent.mkdir(parents=True, exist_ok=True)
    skill_file.write_text(
        """---
name: ccba-auto-tier3
description: Auto detected Tier 3.
tier: orchestrator
bundle: _core
---
# Auto Tier 3
""",
        encoding="utf-8",
    )

    validator = SkillValidator()
    result = validator.evaluate_skill_file(skill_file)
    assert result.tier == ArchitectureTier.TIER_3_ORCHESTRATOR
    assert result.passed_gate_0 is True
    assert result.passed_gate_1 is False
    assert result.gpi_score is None


def test_cli_evaluate_gpi_orchestrated_override(
    temp_skill_dir: Path, capsys: pytest.CaptureFixture
) -> None:
    """Verify that CLI evaluate-gpi with --orchestrated returns 0 and prints Tier 3 result."""
    skill_file = temp_skill_dir / "ccba-cli-eval" / "SKILL.md"
    skill_file.parent.mkdir(parents=True, exist_ok=True)
    skill_file.write_text(
        """---
name: ccba-cli-eval
description: CLI eval test.
bundle: _core
---
# CLI Eval
""",
        encoding="utf-8",
    )

    exit_code = run_evaluate_gpi_cli(["--file", str(skill_file), "--orchestrated"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Tier 3: Composite Orchestrator" in captured.out
