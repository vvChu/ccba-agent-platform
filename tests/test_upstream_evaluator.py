"""test_upstream_evaluator.py - Unit and Integration tests for Upstream Radar & Handshake Pipeline.

Verifies:
1. Dynamic loading of upstream_sources.yaml and default fallback.
2. License audit detection (MIT, GPL, Unknown).
3. 1-Click command generation for ccba-xia.
4. AI Evaluation schema compliance (ADR-0040 tiering and rule-based fallback).
5. Parse-Protection in port_recommendations.md.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from scripts.spoke.upstream_evaluator import (
    append_recommendation,
    call_ai_evaluation,
    check_repo_license,
    generate_xia_command,
    load_upstream_sources,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_load_upstream_sources_from_custom_yaml(tmp_path: Path) -> None:
    """Verify load_upstream_sources correctly reads and filters enabled sources from YAML."""
    config_file = tmp_path / "test_sources.yaml"
    data = {
        "version": "1.0",
        "sources": [
            {
                "name": "custom-repo-1",
                "type": "engineer",
                "remote_url": "https://github.com/custom/repo1",
                "branch": "main",
                "enabled": True,
                "description": "Enabled repo",
            },
            {
                "name": "custom-repo-2",
                "type": "marketing",
                "remote_url": "https://github.com/custom/repo2",
                "branch": "develop",
                "enabled": False,
                "description": "Disabled repo",
            },
        ],
    }
    config_file.write_text(yaml.safe_dump(data), encoding="utf-8")

    sources = load_upstream_sources(config_file)
    assert len(sources) == 1
    assert sources[0]["name"] == "custom-repo-1"
    assert sources[0]["remote_url"] == "https://github.com/custom/repo1"
    assert sources[0]["branch"] == "main"


def test_load_upstream_sources_fallback_on_missing_file(tmp_path: Path) -> None:
    """Verify load_upstream_sources falls back to defaults when file does not exist."""
    missing_file = tmp_path / "non_existent.yaml"
    sources = load_upstream_sources(missing_file)
    assert len(sources) >= 3
    assert any(s["name"] == "claudekit-engineer" for s in sources)


def test_check_repo_license(tmp_path: Path) -> None:
    """Verify license detection correctly classifies MIT, GPL, and Unknown."""
    # 1. MIT License
    mit_dir = tmp_path / "mit_repo"
    mit_dir.mkdir()
    (mit_dir / "LICENSE").write_text("MIT License\nPermission is hereby granted...", encoding="utf-8")
    lic_type, lic_desc = check_repo_license(mit_dir)
    assert lic_type == "PERMISSIVE"
    assert "MIT" in lic_desc

    # 2. GPL License
    gpl_dir = tmp_path / "gpl_repo"
    gpl_dir.mkdir()
    (gpl_dir / "LICENSE.md").write_text("GNU GENERAL PUBLIC LICENSE Version 3", encoding="utf-8")
    lic_type_gpl, lic_desc_gpl = check_repo_license(gpl_dir)
    assert lic_type_gpl == "COPYLEFT"
    assert "GPL" in lic_desc_gpl

    # 3. Unknown License
    empty_dir = tmp_path / "empty_repo"
    empty_dir.mkdir()
    lic_type_empty, _ = check_repo_license(empty_dir)
    assert lic_type_empty == "UNKNOWN"


def test_generate_xia_command() -> None:
    """Verify 1-click command generation produces valid CLI invocation string."""
    cmd_compare = generate_xia_command("https://github.com/mattpocock/skills", "grill-me", "--compare")
    assert cmd_compare == "/ccba-xia https://github.com/mattpocock/skills grill-me --compare"

    cmd_port = generate_xia_command("https://github.com/claudekit/claudekit-engineer", "new-tool", "--port")
    assert cmd_port == "/ccba-xia https://github.com/claudekit/claudekit-engineer new-tool --port"


def test_call_ai_evaluation_duplicate_rejection() -> None:
    """Verify duplicate skills in catalog are rejected without calling LLM."""
    with patch("scripts.spoke.upstream_evaluator.get_existing_elements", return_value=(["my-existing-skill"], [])):
        res = call_ai_evaluation("engineer", "my-existing-skill", "content", "https://github.com/test/repo")
        assert res["should_port"] is False
        assert "IGNORE" in res["reason"]
        assert res["recommended_tier"] == "Reject/Duplicate"
        assert "--compare" in res["xia_command"]


def test_call_ai_evaluation_rule_based_fallback() -> None:
    """Verify rule-based fallback produces ADR-0040 tiering and xia_command."""
    with patch("scripts.spoke.upstream_evaluator.ai", None):
        with patch("scripts.spoke.upstream_evaluator.get_existing_elements", return_value=([], [])):
            res = call_ai_evaluation("engineer", "brand-new-workflow", "content", "https://github.com/test/repo")
            assert res["should_port"] is True
            assert res["score"] >= 70
            assert "Tier 3" in res["recommended_tier"]
            assert "/ccba-xia https://github.com/test/repo brand-new-workflow" in res["xia_command"]


def test_append_recommendation_preserves_developer_notes(tmp_path: Path) -> None:
    """Verify append_recommendation preserves manual engineer notes across runs."""
    recs_file = tmp_path / "port_recommendations.md"
    with patch("scripts.spoke.upstream_evaluator.RECOMMENDATIONS_FILE", recs_file):
        # 1. First run: creates file
        sample_result = {
            "should_port": True,
            "score": 85,
            "recommended_tier": "Tier 3 (User Workflow)",
            "target_bundle": "_software",
            "disable_model_invocation": True,
            "python_compatibility_assessment": "100% tương thích Python Monorepo.",
            "reason": "Kỹ năng hữu ích.",
            "actionable_steps": ["Chạy lệnh /ccba-xia"],
            "xia_command": "/ccba-xia https://github.com/test/repo test-skill --compare",
        }
        append_recommendation("test-repo", "test-skill", sample_result, "https://github.com/test/repo", "MIT License")

        # 2. Engineer manually adds a note
        content = recs_file.read_text(encoding="utf-8")
        custom_note = "\n- [x] Đã thảo luận cùng team kỹ thuật ngày 2026-08-16."
        content_with_notes = content.replace("<!-- DEVELOPER-NOTES-END -->", f"{custom_note}\n<!-- DEVELOPER-NOTES-END -->")
        recs_file.write_text(content_with_notes, encoding="utf-8")

        # 3. Second run: adds another recommendation
        second_result = {
            "should_port": False,
            "score": 30,
            "recommended_tier": "Reject",
            "target_bundle": "_core",
            "disable_model_invocation": True,
            "python_compatibility_assessment": "Trùng lặp.",
            "reason": "Trùng lặp với skill hiện tại.",
            "actionable_steps": ["Bỏ qua"],
            "xia_command": "/ccba-xia https://github.com/test/repo dup-skill --compare",
        }
        append_recommendation("test-repo", "dup-skill", second_result, "https://github.com/test/repo", "MIT License")

        # 4. Verify developer note is preserved and both skills are present
        updated_content = recs_file.read_text(encoding="utf-8")
        assert custom_note in updated_content
        assert "`test-skill`" in updated_content
        assert "`dup-skill`" in updated_content
        assert "⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia" in updated_content
