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
            {
                "name": "empty-url-repo",
                "type": "empty",
                "remote_url": "   ",
                "branch": "main",
                "enabled": True,
                "description": "Empty URL repo",
            },
            {
                "name": "claudekit-engineer",
                "type": "engineer",
                "remote_url": "https://github.com/claudekit/claudekit-engineer",
                "branch": "main",
                "enabled": True,
                "description": "Default repo mapping",
            },
        ],
    }
    config_file.write_text(yaml.safe_dump(data), encoding="utf-8")

    sources = load_upstream_sources(config_file)
    assert len(sources) == 2
    assert sources[0]["name"] == "custom-repo-1"
    assert sources[0]["remote_url"] == "https://github.com/custom/repo1"
    assert sources[0]["branch"] == "main"
    assert sources[0]["sha_file"].name == "custom-repo-1_last_sha.txt"

    # Legacy SHA file mapping test
    assert sources[1]["name"] == "claudekit-engineer"
    assert sources[1]["sha_file"].name == "claudekit_last_sha.txt"


def test_load_upstream_sources_fallback_on_missing_file(tmp_path: Path) -> None:
    """Verify load_upstream_sources falls back to defaults when file does not exist."""
    missing_file = tmp_path / "non_existent.yaml"
    sources = load_upstream_sources(missing_file)
    assert len(sources) >= 3
    assert any(s["name"] == "claudekit-engineer" for s in sources)


def test_check_repo_license(tmp_path: Path) -> None:
    """Verify license detection correctly classifies MIT, GPL, Unknown, and Custom."""
    # 1. MIT License
    mit_dir = tmp_path / "mit_repo"
    mit_dir.mkdir()
    (mit_dir / "LICENSE").write_text(
        "MIT License\nPermission is hereby granted...", encoding="utf-8"
    )
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

    # 3. Custom License -> Classified as UNKNOWN per 4-value contract
    custom_dir = tmp_path / "custom_repo"
    custom_dir.mkdir()
    (custom_dir / "LICENSE").write_text("Custom Special License Terms", encoding="utf-8")
    lic_type_custom, lic_desc_custom = check_repo_license(custom_dir)
    assert lic_type_custom == "UNKNOWN"
    assert "Custom license" in lic_desc_custom

    # 4. Unknown/Empty License
    empty_dir = tmp_path / "empty_repo"
    empty_dir.mkdir()
    lic_type_empty, _ = check_repo_license(empty_dir)
    assert lic_type_empty == "UNKNOWN"


def test_generate_xia_command() -> None:
    """Verify 1-click command generation produces valid CLI invocation string."""
    cmd_compare = generate_xia_command(
        "https://github.com/mattpocock/skills", "grill-me", "--compare"
    )
    assert cmd_compare == "/ccba-xia https://github.com/mattpocock/skills grill-me --compare"

    cmd_port = generate_xia_command(
        "https://github.com/claudekit/claudekit-engineer", "new-tool", "--port"
    )
    assert cmd_port == "/ccba-xia https://github.com/claudekit/claudekit-engineer new-tool --port"


def test_call_ai_evaluation_duplicate_rejection() -> None:
    """Verify duplicate skills in catalog are rejected without calling LLM."""
    with patch(
        "scripts.spoke.upstream_evaluator.get_existing_elements",
        return_value=(["my-existing-skill"], []),
    ):
        res = call_ai_evaluation(
            "engineer", "my-existing-skill", "content", "https://github.com/test/repo"
        )
        assert res["should_port"] is False
        assert "IGNORE" in res["reason"]
        assert res["recommended_tier"] == "Reject/Duplicate"
        assert "--compare" in res["xia_command"]


def test_call_ai_evaluation_rule_based_fallback() -> None:
    """Verify rule-based fallback produces ADR-0040 tiering and xia_command."""
    with patch("scripts.spoke.upstream_evaluator.ai", None):
        with patch("scripts.spoke.upstream_evaluator.get_existing_elements", return_value=([], [])):
            res = call_ai_evaluation(
                "engineer", "brand-new-workflow", "content", "https://github.com/test/repo"
            )
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
        append_recommendation(
            "test-repo", "test-skill", sample_result, "https://github.com/test/repo", "MIT License"
        )

        # 2. Engineer manually adds a note
        content = recs_file.read_text(encoding="utf-8")
        custom_note = "\n- [x] Đã thảo luận cùng team kỹ thuật ngày 2026-08-16."
        content_with_notes = content.replace(
            "<!-- DEVELOPER-NOTES-END -->", f"{custom_note}\n<!-- DEVELOPER-NOTES-END -->"
        )
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
        append_recommendation(
            "test-repo", "dup-skill", second_result, "https://github.com/test/repo", "MIT License"
        )

        # 4. Verify developer note is preserved and both skills are present
        updated_content = recs_file.read_text(encoding="utf-8")
        assert custom_note in updated_content
        assert "`test-skill`" in updated_content
        assert "`dup-skill`" in updated_content
        assert "⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia" in updated_content


def test_get_remote_sha_with_custom_branch() -> None:
    """Verify get_remote_sha prioritizes querying custom branch before falling back."""
    from unittest.mock import MagicMock

    from scripts.spoke.upstream_evaluator import UpstreamEvaluator

    evaluator = UpstreamEvaluator()
    calls = []

    def mock_subprocess_run(cmd, **kwargs):
        calls.append(cmd)
        mock_res = MagicMock()
        if "refs/heads/feature-xyz" in cmd:
            mock_res.stdout = "abc1234567890\trefs/heads/feature-xyz\n"
            return mock_res
        mock_res.stdout = ""
        return mock_res

    with patch("subprocess.run", side_effect=mock_subprocess_run):
        sha = evaluator.get_remote_sha("https://github.com/test/repo", branch="feature-xyz")
        assert sha == "abc1234567890"
        assert any("refs/heads/feature-xyz" in c for c in calls)


def test_call_ai_evaluation_ai_gateway_adr0057_flow() -> None:
    """Verify AI Gateway response with ADR-0057 fields is evaluated by two-stage framework."""
    import json
    from unittest.mock import MagicMock

    mock_ai = MagicMock()
    mock_ai.chat.return_value = json.dumps({
        "should_port": True,
        "score": 92,
        "is_deterministic": False,
        "is_orchestrated": False,
        "gpi_scores": {"s": 4.0, "k": 3.0, "a": 2.0, "p": 1.0},
        "target_bundle": "_software",
        "disable_model_invocation": False,
        "parent_master_skill": None,
        "python_compatibility_assessment": "High",
        "reason": "Cognitive core skill",
        "actionable_steps": ["Step 1", "Step 2"],
    })

    with patch("scripts.spoke.upstream_evaluator.ai", mock_ai):
        with patch("scripts.spoke.upstream_evaluator.get_existing_elements", return_value=([], [])):
            res = call_ai_evaluation(
                "engineer", "cognitive-analyzer", "# Skill\n...", "https://github.com/test/repo"
            )
            assert res["should_port"] is True
            # s=4, k=3, a=2, p=1 -> 4*2.5 + 3*2 + 2*2 - 1*1.5 = 10 + 6 + 4 - 1.5 = 18.5 >= 12.0 -> Tier 2B
            assert "Tier 2B: Standalone Kernel Skill" in res["recommended_tier"]
            assert res["decision_result"]["gpi_score"] == 18.5
            assert res["decision_result"]["allow_standalone_skill"] is True


def test_call_ai_evaluation_rule_based_fallback_deterministic() -> None:
    """Verify deterministic skill name routes to Tier 1 under ADR-0057."""
    with patch("scripts.spoke.upstream_evaluator.ai", None):
        with patch("scripts.spoke.upstream_evaluator.get_existing_elements", return_value=([], [])):
            res = call_ai_evaluation(
                "engineer", "ast-parse-cleaner", "content", "https://github.com/test/repo"
            )
            assert res["should_port"] is True
            assert "Tier 1: Package Function / Deep Seam" in res["recommended_tier"]
            assert res["decision_result"]["allow_standalone_skill"] is False


def test_call_ai_evaluation_rule_based_fallback_cognitive_tier2a() -> None:
    """Verify cognitive sub-threshold skill name routes to Tier 2A under ADR-0057."""
    with patch("scripts.spoke.upstream_evaluator.ai", None):
        with patch("scripts.spoke.upstream_evaluator.get_existing_elements", return_value=([], [])):
            res = call_ai_evaluation(
                "engineer", "helper-assistant", "content", "https://github.com/test/repo"
            )
            assert res["should_port"] is True
            assert "Tier 2A: Progressive Reference" in res["recommended_tier"]
            assert res["decision_result"]["gpi_score"] == 5.0
            assert res["decision_result"]["allow_standalone_skill"] is False


def test_call_ai_evaluation_robust_json_parsing_with_preamble() -> None:
    """Verify AI Gateway response wrapped in markdown block and text preamble parses correctly."""
    import json
    from unittest.mock import MagicMock

    raw_data = {
        "should_port": True,
        "score": 88,
        "is_deterministic": False,
        "is_orchestrated": False,
        "gpi_scores": {"s": 3.0, "k": 2.0, "a": 2.0, "p": 2.0},
        "target_bundle": "_core",
        "disable_model_invocation": True,
        "parent_master_skill": None,
        "python_compatibility_assessment": "Good",
        "reason": "Review ritual",
        "actionable_steps": ["Step 1"],
    }
    mock_response = f"Chào bạn, dưới đây là kết quả:\n```json\n{json.dumps(raw_data, indent=2)}\n```\nHy vọng hữu ích!"

    mock_ai = MagicMock()
    mock_ai.chat.return_value = mock_response

    with patch("scripts.spoke.upstream_evaluator.ai", mock_ai):
        with patch("scripts.spoke.upstream_evaluator.get_existing_elements", return_value=([], [])):
            res = call_ai_evaluation(
                "engineer", "review-tool", "# Skill\n...", "https://github.com/test/repo"
            )
            assert res["should_port"] is True
            assert "Tier 2B: Standalone Kernel Skill" in res["recommended_tier"]
            assert res["decision_result"]["gpi_score"] == 12.5

