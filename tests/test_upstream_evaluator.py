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
    UpstreamEvaluator,
    append_recommendation,
    call_ai_evaluation,
    check_is_duplicate,
    check_repo_license,
    format_vitality_badge,
    generate_xia_command,
    get_repo_vitality_metrics,
    load_eval_cache,
    load_upstream_sources,
    resolve_upstream_resources,
    save_eval_cache,
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
    mock_ai.chat.return_value = json.dumps(
        {
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
        }
    )

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


def test_ensure_local_repo_stale_index_lock_cleanup(tmp_path: Path) -> None:
    """Verify ensure_local_repo detects and cleans up stale .git/index.lock before git operations."""
    repo_dir = tmp_path / "mock_repo"
    git_dir = repo_dir / ".git"
    git_dir.mkdir(parents=True)
    index_lock = git_dir / "index.lock"
    index_lock.write_text("lock", encoding="utf-8")

    config = {
        "name": "mock_repo",
        "type": "mock",
        "local_path": repo_dir,
        "remote_url": "https://github.com/mock/repo",
        "branch": "main",
        "sha_file": tmp_path / "mock_sha.txt",
    }

    evaluator = UpstreamEvaluator()
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        success = evaluator.ensure_local_repo(config)
        assert success is True
        assert not index_lock.exists()


def test_ensure_local_repo_clean_clone_fallback(tmp_path: Path) -> None:
    """Verify ensure_local_repo cleans up corrupted repo and triggers clean clone fallback."""
    repo_dir = tmp_path / "broken_repo"
    (repo_dir / ".git").mkdir(parents=True)
    (repo_dir / "corrupted_file.txt").write_text("broken", encoding="utf-8")

    config = {
        "name": "broken_repo",
        "type": "broken",
        "local_path": repo_dir,
        "remote_url": "https://github.com/broken/repo",
        "branch": "main",
        "sha_file": tmp_path / "broken_sha.txt",
    }

    evaluator = UpstreamEvaluator()
    calls = []

    def mock_subprocess_run(cmd, **kwargs):
        calls.append(cmd)
        if "fetch" in cmd:
            import subprocess

            raise subprocess.SubprocessError("Corrupted packfile")
        from unittest.mock import MagicMock

        res = MagicMock()
        res.returncode = 0
        return res

    with patch("subprocess.run", side_effect=mock_subprocess_run):
        success = evaluator.ensure_local_repo(config)
        assert success is True
        # Verify clone command was executed as fallback
        assert any("clone" in c for c in calls)


def test_resolve_upstream_resources(tmp_path: Path) -> None:
    """Verify resolve_upstream_resources resolves nested skills, workflows, and governance rules."""
    # 1. Nested skill
    nested_skill_dir = tmp_path / "claude" / "skills" / "document-skills" / "docx"
    nested_skill_dir.mkdir(parents=True)
    (nested_skill_dir / "SKILL.md").write_text("# Docx Skill", encoding="utf-8")

    # 2. Standard skill
    standard_skill_dir = tmp_path / "claude" / "skills" / "banner-design"
    standard_skill_dir.mkdir(parents=True)
    (standard_skill_dir / "SKILL.md").write_text("# Banner Skill", encoding="utf-8")

    # 3. Domain workflow
    wf_dir = tmp_path / "claude" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "campaign-workflow.md").write_text("# Campaign Workflow", encoding="utf-8")

    # 4. Governance rule
    (wf_dir / "development-rules.md").write_text("# Dev Rules", encoding="utf-8")

    resources = resolve_upstream_resources(tmp_path)
    res_map = {r["name"]: r for r in resources}

    assert "document-skills/docx" in res_map
    assert res_map["document-skills/docx"]["type"] == "skill"

    assert "banner-design" in res_map
    assert res_map["banner-design"]["type"] == "skill"

    assert "campaign-workflow" in res_map
    assert res_map["campaign-workflow"]["type"] == "workflow"

    assert "development-rules" in res_map
    assert res_map["development-rules"]["type"] == "governance_rule"


def test_check_is_duplicate_fuzzy_and_aliases() -> None:
    """Verify fuzzy deduplication detects prefixes (ck-, ccba-), aliases, and nested leaves."""
    existing_skills = ["ccba-git-guardrails", "ccba-xu-ly-van-phong", "ccba-ask"]
    existing_workflows = ["ccba-run-qc-pipeline"]

    # ck-git -> git -> alias ccba-git-guardrails
    is_dup, match = check_is_duplicate("ck-git", existing_skills, existing_workflows)
    assert is_dup is True
    assert match == "ccba-git-guardrails"

    # nested skill docx -> alias ccba-xu-ly-van-phong
    is_dup, match = check_is_duplicate("document-skills/docx", existing_skills, existing_workflows)
    assert is_dup is True
    assert match == "ccba-xu-ly-van-phong"

    # leaf pptx with no existing skill
    is_dup, match = check_is_duplicate("document-skills/pptx", existing_skills, existing_workflows)
    assert is_dup is False

    # completely new skill
    is_dup, match = check_is_duplicate("brand-new-evaluator", existing_skills, existing_workflows)
    assert is_dup is False


def test_eval_cache_load_save_and_hit(tmp_path: Path) -> None:
    """Verify evaluation cache loads, saves, and avoids re-evaluation on cache hit."""
    cache_file = tmp_path / "upstream_eval_cache.json"

    with patch("scripts.spoke.upstream_evaluator.CACHE_FILE", cache_file):
        test_cache = {
            "mock:my-cached-skill:abc1234567890123": {
                "should_port": True,
                "score": 95,
                "recommended_tier": "Tier 2B",
                "reason": "Cached result",
            }
        }
        save_eval_cache(test_cache)
        loaded = load_eval_cache()
        assert "mock:my-cached-skill:abc1234567890123" in loaded

        with patch("scripts.spoke.upstream_evaluator.get_existing_elements", return_value=([], [])):
            with patch("hashlib.sha256") as mock_hash:
                mock_hash.return_value.hexdigest.return_value = "abc1234567890123"
                res = call_ai_evaluation(
                    repo_type="mock",
                    skill_name="my-cached-skill",
                    content="content",
                    local_path=".md/scratch/repos/mock",
                    use_cache=True,
                )
                assert res["reason"] == "Cached result"
                assert (
                    "/ccba-xia .md/scratch/repos/mock my-cached-skill --port" in res["xia_command"]
                )


def test_1click_xia_command_local_path() -> None:
    """Verify 1-click porting command targets local repo path."""
    cmd = generate_xia_command(
        ".md/scratch/repos/claudekit-marketing", "document-skills/docx", "--port"
    )
    assert cmd == "/ccba-xia .md/scratch/repos/claudekit-marketing document-skills/docx --port"


def test_upstream_sync_mutex_lock(tmp_path: Path) -> None:
    """Verify mutex lock upstream_sync.lock prevents concurrent synchronization runs."""
    lock_file = tmp_path / "upstream_sync.lock"

    with patch("scripts.spoke.upstream_evaluator.LOCK_FILE", lock_file):
        # 1. Active lock prevents execution
        lock_file.write_text("pid: 99999", encoding="utf-8")
        evaluator = UpstreamEvaluator(configs=[])
        evaluator.sync_and_evaluate()
        # Still has content, wasn't unlinked by another run
        assert lock_file.exists()

        # 2. Stale lock (> 300s) is cleared
        import os
        import time

        old_time = time.time() - 400
        os.utime(lock_file, (old_time, old_time))
        evaluator.sync_and_evaluate()
        # After execution completes, lock file should be unlinked
        assert not lock_file.exists()


def test_zero_scan_init_trap_resolution(tmp_path: Path) -> None:
    """Verify missing local_sha triggers initial full scan rather than returning early."""
    repo_dir = tmp_path / "init_repo"
    repo_dir.mkdir()
    skill_dir = repo_dir / "claude" / "skills" / "init-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Init Skill", encoding="utf-8")

    sha_file = tmp_path / "init_sha.txt"
    config = {
        "name": "init_repo",
        "type": "init",
        "local_path": repo_dir,
        "remote_url": "https://github.com/init/repo",
        "branch": "main",
        "sha_file": sha_file,
    }

    evaluator = UpstreamEvaluator(configs=[config])
    with patch.object(evaluator, "get_remote_sha", return_value="deadbeef12345678"):
        with patch.object(evaluator, "ensure_local_repo", return_value=True):
            with patch.object(evaluator, "scan_and_evaluate_repo") as mock_scan:
                evaluator.check_and_evaluate_single(config, check_only=True)
                mock_scan.assert_called_once_with(
                    config, "deadbeef12345678", check_only=True, limit=None, fast=False
                )


def test_zero_scan_init_trap_with_existing_git_repo(tmp_path: Path) -> None:
    """Verify missing sha_file triggers initial scan even when local clone already has .git folder."""
    repo_dir = tmp_path / "cloned_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()

    sha_file = tmp_path / "cloned_sha.txt"
    config = {
        "name": "cloned_repo",
        "type": "cloned",
        "local_path": repo_dir,
        "remote_url": "https://github.com/cloned/repo",
        "branch": "main",
        "sha_file": sha_file,
    }

    evaluator = UpstreamEvaluator(configs=[config])
    assert evaluator.get_local_sha(config) == ""

    with patch.object(evaluator, "get_remote_sha", return_value="aabbccddeeff1122"):
        with patch.object(evaluator, "ensure_local_repo", return_value=True):
            with patch.object(evaluator, "scan_and_evaluate_repo") as mock_scan:
                evaluator.check_and_evaluate_single(config, check_only=False)
                mock_scan.assert_called_once_with(
                    config, "aabbccddeeff1122", check_only=False, limit=None, fast=False
                )
                assert sha_file.exists()
                assert sha_file.read_text(encoding="utf-8").strip() == "aabbccddeeff1122"


def test_check_is_duplicate_claudekit_prefixes_and_colons() -> None:
    """Verify fuzzy deduplication detects ckm-, ckm:, cke-, ck: prefixes."""
    existing_skills = ["ccba-xu-ly-van-phong", "ccba-ask", "ccba-code-review"]
    existing_workflows = ["ccba-run-qc-pipeline"]

    is_dup, match = check_is_duplicate("ckm:docx", existing_skills, existing_workflows)
    assert is_dup is True
    assert match == "ccba-xu-ly-van-phong"

    is_dup, match = check_is_duplicate("ckm-ask", existing_skills, existing_workflows)
    assert is_dup is True
    assert match == "ccba-ask"

    is_dup, match = check_is_duplicate("cke:review", existing_skills, existing_workflows)
    assert is_dup is True
    assert match == "ccba-code-review"


def test_append_recommendation_updates_existing_skill_in_place(tmp_path: Path) -> None:
    """Verify append_recommendation updates existing skill entry in-place instead of ignoring it."""
    recs_file = tmp_path / "port_recommendations.md"
    with patch("scripts.spoke.upstream_evaluator.RECOMMENDATIONS_FILE", recs_file):
        initial_result = {
            "should_port": False,
            "score": 30,
            "recommended_tier": "Reject",
            "target_bundle": "_core",
            "disable_model_invocation": True,
            "reason": "Old evaluation: reject",
            "actionable_steps": ["Ignore"],
            "xia_command": "/ccba-xia .md/scratch/repos/mock test-skill --compare",
        }
        append_recommendation("mock", "test-skill", initial_result)
        content_1 = recs_file.read_text(encoding="utf-8")
        assert "Old evaluation: reject" in content_1

        updated_result = {
            "should_port": True,
            "score": 90,
            "recommended_tier": "Tier 2B: Standalone Kernel Skill",
            "target_bundle": "_software",
            "disable_model_invocation": False,
            "reason": "New evaluation: approved",
            "actionable_steps": ["Run port"],
            "xia_command": "/ccba-xia .md/scratch/repos/mock test-skill --port",
        }
        append_recommendation("mock", "test-skill", updated_result)
        content_2 = recs_file.read_text(encoding="utf-8")
        assert "New evaluation: approved" in content_2
        assert "Old evaluation: reject" not in content_2
        # Ensure it didn't duplicate the entry
        assert content_2.count("`test-skill`") == 1


def test_evaluate_repo_diff_handles_deleted_file_gracefully(tmp_path: Path) -> None:
    """Verify evaluate_repo_diff skips deleted files without raising FileNotFoundError."""
    repo_dir = tmp_path / "diff_repo"
    repo_dir.mkdir()

    evaluator = UpstreamEvaluator()

    def mock_subprocess_run(cmd, **kwargs):
        from unittest.mock import MagicMock

        res = MagicMock()
        if "diff" in cmd:
            res.returncode = 0
            res.stdout = "claude/skills/deleted-skill/SKILL.md\n"
            return res
        elif "show" in cmd:
            res.returncode = 128
            res.stdout = ""
            return res
        res.returncode = 0
        return res

    with patch("subprocess.run", side_effect=mock_subprocess_run):
        # Deleted file does not exist on disk, should skip gracefully and not raise
        evaluator.evaluate_repo_diff(
            repo_path=repo_dir,
            base_sha="11111111",
            head_sha="22222222",
            repo_type="diff_repo",
            remote_url="https://github.com/diff/repo",
        )


def test_get_repo_vitality_metrics_full_and_stale(tmp_path: Path) -> None:
    """Verify full clone vitality uses origin/<branch>, counts commits, and flags stale >= 120d."""
    from datetime import datetime, timezone
    from unittest.mock import MagicMock

    repo_dir = tmp_path / "stale_repo"
    (repo_dir / ".git").mkdir(parents=True)
    stale_epoch = str(int(datetime.now(timezone.utc).timestamp()) - (141 * 86400))

    def mock_run(cmd: list[str], **kwargs: object) -> MagicMock:
        res = MagicMock(returncode=0, stdout="")
        if "--verify" in cmd and "origin/main" in cmd:
            res.stdout = "abc1234\n"
        elif "--format=%ct" in cmd:
            assert "origin/main" in cmd
            res.stdout = f"{stale_epoch}\n"
        elif "--is-shallow-repository" in cmd:
            res.stdout = "false\n"
        elif "--count" in cmd:
            res.stdout = "2451\n"
        return res

    with patch("subprocess.run", side_effect=mock_run):
        metrics = get_repo_vitality_metrics(repo_dir, branch="main", stale_days=120)
        assert metrics["stale"] is True
        assert metrics["age_days"] == 141
        assert metrics["commits_count"] == 2451
        assert metrics["ref"] == "origin/main"
        badge = format_vitality_badge(metrics, local_only=True)
        assert "STALE_UPSTREAM" in badge
        assert "2451 commits" in badge
        assert "local ref origin/main" in badge


def test_get_repo_vitality_metrics_shallow_and_future_skew(tmp_path: Path) -> None:
    """Verify shallow clone sets commits_count=None and future timestamp clamps age_days to 0."""
    from datetime import datetime, timezone
    from unittest.mock import MagicMock

    repo_dir = tmp_path / "shallow_repo"
    (repo_dir / ".git").mkdir(parents=True)
    future_epoch = str(int(datetime.now(timezone.utc).timestamp()) + 7200)

    def mock_run(cmd: list[str], **kwargs: object) -> MagicMock:
        res = MagicMock(returncode=0, stdout="")
        if "--verify" in cmd:
            raise OSError("missing origin ref")
        if "--format=%ct" in cmd:
            res.stdout = f"{future_epoch}\n"
        elif "--is-shallow-repository" in cmd:
            res.stdout = "true\n"
        return res

    with patch("subprocess.run", side_effect=mock_run):
        metrics = get_repo_vitality_metrics(repo_dir, branch="main", stale_days=120)
        assert metrics["stale"] is False
        assert metrics["age_days"] == 0
        assert metrics["commits_count"] is None
        assert metrics["ref"] == "HEAD"
        assert "shallow clone" in format_vitality_badge(metrics)


def test_get_repo_vitality_metrics_missing_or_empty_repo(tmp_path: Path) -> None:
    """Verify missing .git or empty repository returns stale=False with error sentinel."""
    no_git_dir = tmp_path / "no_git"
    no_git_dir.mkdir()
    m1 = get_repo_vitality_metrics(no_git_dir)
    assert m1["stale"] is False
    assert m1["error"] == "no_git_history"
    assert "VITALITY_UNKNOWN" in format_vitality_badge(m1)


def test_check_and_evaluate_single_emits_vitality_on_up_to_date_and_offline(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify COND-01: vitality badge prints on up-to-date branch and when remote fails."""
    repo_dir = tmp_path / "repo"
    (repo_dir / ".git").mkdir(parents=True)
    sha_file = tmp_path / "sha.txt"
    sha_file.write_text("deadbeef12345678", encoding="utf-8")
    cfg = {
        "name": "test-repo",
        "type": "engineer",
        "local_path": repo_dir,
        "remote_url": "https://github.com/test/repo",
        "branch": "main",
        "sha_file": sha_file,
        "stale_upstream_days": 120,
    }
    fake_metrics = {
        "commits_count": 2451,
        "last_commit_date": "2026-06-18",
        "age_days": 141,
        "stale": True,
        "ref": "origin/main",
        "error": None,
    }
    evaluator = UpstreamEvaluator(configs=[cfg])
    with (
        patch.object(evaluator, "get_remote_sha", return_value="deadbeef12345678"),
        patch.object(evaluator, "ensure_local_repo", return_value=True),
        patch(
            "scripts.spoke.upstream_evaluator.get_repo_vitality_metrics",
            return_value=fake_metrics,
        ),
    ):
        evaluator.check_and_evaluate_single(cfg, check_only=True)
    out = capsys.readouterr().out
    assert "is up-to-date" in out
    assert "STALE_UPSTREAM" in out

    with (
        patch.object(evaluator, "get_remote_sha", return_value=""),
        patch(
            "scripts.spoke.upstream_evaluator.get_repo_vitality_metrics",
            return_value=fake_metrics,
        ),
    ):
        evaluator.check_and_evaluate_single(cfg, check_only=True)
    out_offline = capsys.readouterr().out
    assert "Local Vitality:" in out_offline
    assert "STALE_UPSTREAM" in out_offline


def test_ui_and_web_quality_upstream_aliases_route_to_ccba_design() -> None:
    """Verify UI/UX and Web Quality upstream sub-skills map to ccba-design to preserve the 76-skill cap."""
    existing_skills = ["ccba-design", "ccba-web-testing", "ccba-sharepoint-iac"]
    for upstream_skill in (
        "frontend-design",
        "web-design-guidelines",
        "polish",
        "critique",
        "distill",
        "accessibility",
        "core-web-vitals",
    ):
        is_dup, matched = check_is_duplicate(upstream_skill, existing_skills, [])
        assert is_dup is True
        assert matched == "ccba-design"

    for m365_skill in (
        "canvas-app",
        "create-code-app",
        "build-flow",
        "pcf",
        "list-formatting",
        "add-sharepoint",
    ):
        is_dup, matched = check_is_duplicate(m365_skill, existing_skills, [])
        assert is_dup is True
        assert matched == "ccba-sharepoint-iac"


def test_license_classification_matrix_and_post_cache_clamp(tmp_path: Path) -> None:
    """Verify 6-tier license classifier matrix and post-cache/fallback --compare clamping."""
    cases = (
        ("ISC License\nPermission to use, copy, modify, and/or distribute...", "PERMISSIVE"),
        ("Zero-Clause BSD (0BSD)\nPermission to use, copy, modify...", "PERMISSIVE"),
        ("This is free and unencumbered software released into the public domain.", "PERMISSIVE"),
        ("Mozilla Public License Version 2.0 (MPL-2.0)", "COPYLEFT"),
        ("Licensed under either of Apache-2.0 or MIT license at your option.", "PERMISSIVE"),
        ("Dual licensed under the MIT OR GPL-2.0 license.", "COPYLEFT"),
        ("Copyright 2026 Corp. All Rights Reserved.", "PROPRIETARY"),
        ("Bespoke internal evaluation terms v1.", "UNKNOWN"),
    )
    lic_dir = tmp_path / "lic"
    lic_dir.mkdir()
    for body, expected in cases:
        (lic_dir / "LICENSE").write_text(body, encoding="utf-8")
        assert check_repo_license(lic_dir)[0] == expected

    cf, rf = tmp_path / "cache.json", tmp_path / "recs.md"
    kw: dict[str, object] = {
        "CACHE_FILE": cf,
        "RECOMMENDATIONS_FILE": rf,
        "get_existing_elements": lambda: ([], []),
    }
    with patch.multiple("scripts.spoke.upstream_evaluator", **kw), patch("hashlib.sha256") as mh:
        mh.return_value.hexdigest.return_value = "deadbeef12345678"
        save_eval_cache({"mock:dual-skill:deadbeef12345678": {"should_port": True, "score": 90}})
        res = call_ai_evaluation("mock", "dual-skill", "# D", "https://g.co/r", "COPYLEFT")
        assert res["should_port"] is False and res["xia_command"].endswith(" --compare")
        append_recommendation("mock", "dual-skill", res, "https://g.co/r", "Dual MIT/GPL")
        rendered = rf.read_text(encoding="utf-8")
        assert "🟠 [COMPARE ONLY — LICENSE RESTRICTED]" in rendered and "--compare" in rendered


def test_governance_config_prune_sha_and_blobless_clone(tmp_path: Path) -> None:
    """Verify YAML source_kind/aliases, --prune-stale isolation, SHA fallback, and blobless clone teardown."""
    import subprocess

    import scripts.spoke._upstream_helpers as uh

    pnp = {s["name"]: s for s in load_upstream_sources()}["pnp-list-formatting"]
    assert pnp["source_kind"] == "reference_corpus"
    assert pnp["default_target"] == "ccba-sharepoint-iac"
    cfg_y = tmp_path / "sources.yaml"
    cfg_y.write_text("aliases:\n  polish: wrong\n  new-alias: ccba-ask\n", encoding="utf-8")
    amap = {"polish": "ccba-design"}
    uh.load_governance_config(cfg_y, amap)
    assert amap == {"polish": "ccba-design", "new-alias": "ccba-ask"}

    ev = UpstreamEvaluator()
    (tmp_path / "mattpocock_skills_last_sha.txt").write_text("legacysha999\n", encoding="utf-8")
    assert ev.get_local_sha({"sha_file": tmp_path / "mattpocock_last_sha.txt"}) == "legacysha999"

    dest, seen, cmds = tmp_path / "corrupt_clone", [], []
    (dest / ".git").mkdir(parents=True)

    def fake_run(cmd: list[str], **kw: object) -> object:
        seen.append(dest.exists())
        cmds.append(cmd)
        if "--filter=blob:none" in cmd:
            (dest / ".git").mkdir(parents=True, exist_ok=True)
            raise subprocess.SubprocessError("blobless unsupported")
        return object()

    with patch("subprocess.run", side_effect=fake_run):
        assert ev._clone_repo(dest, "https://github.com/org/repo", "mock") is True
    assert seen == [False, False] and "--filter=blob:none" in cmds[0]

    rec_md = tmp_path / "recs.md"
    rec_md.write_text(
        "<!-- AUTO-GENERATED-START -->\n# Header\n\n---\n\n"
        "### 🟢 [RECOMMEND PORT] Skill: `old` (Score: 85/100)\n* simulated approval\n\n---\n\n"
        "### 🟢 [RECOMMEND PORT] Skill: `prop` (Score: 80/100)\n* **Bản quyền**: `Bản quyền đóng`\n"
        "> ⚡ `/ccba-xia repo prop --port`\n<!-- AUTO-GENERATED-END -->\n\n"
        "<!-- DEVELOPER-NOTES-START -->\nKeep ADR-0040 history here\n<!-- DEVELOPER-NOTES-END -->",
        encoding="utf-8",
    )
    assert uh.prune_stale_recommendations(rec_md) == 1
    out = rec_md.read_text(encoding="utf-8")
    assert "simulated approval" not in out and "🟠 [COMPARE ONLY — LICENSE RESTRICTED]" in out
    assert "Keep ADR-0040 history here" in out


def test_upstream_delta_collapsing_acmr_guard_and_repo_upsert(tmp_path: Path) -> None:
    """Verify subfile collapsing, UPSTREAM DELTA routing/clamping, ACMR SHA guard, and (repo, skill) upsert."""
    from unittest.mock import MagicMock

    repo = tmp_path / "impeccable"
    (repo / ".git").mkdir(parents=True)
    (repo / "LICENSE").write_text("MIT License\nPermission is hereby granted...", encoding="utf-8")
    (repo / "skills" / "polish").mkdir(parents=True)
    (repo / "skills" / "polish" / "SKILL.md").write_text("# Polish", encoding="utf-8")
    recs, sha_f = tmp_path / "recs.md", tmp_path / "sha.txt"
    sha_f.write_text("1111222233334444", encoding="utf-8")

    def ok_git(cmd: list[str], **kw: object) -> MagicMock:
        r = MagicMock(returncode=0, stdout="")
        if "diff" in cmd:
            r.stdout = "M\tskills/polish/references/a.md\nM\tskills/polish/scripts/b.py\n"
        elif "show" in cmd:
            r.stdout = "# Changed content"
        return r

    ev = UpstreamEvaluator()
    with (
        patch("scripts.spoke.upstream_evaluator.RECOMMENDATIONS_FILE", recs),
        patch(
            "scripts.spoke.upstream_evaluator.get_existing_elements",
            return_value=(["ccba-design"], []),
        ),
        patch("subprocess.run", side_effect=ok_git),
    ):
        assert (
            ev.evaluate_repo_diff(
                repo,
                "1111222233334444",
                "99998888",
                "impeccable",
                "https://g.co/i",
                ".md/scratch/repos/impeccable",
            )
            is True
        )
        append_recommendation(
            "web-quality-skills",
            "polish",
            {"should_port": True, "score": 80, "reason": "Other repo"},
            "https://g.co/w",
        )
    txt = recs.read_text(encoding="utf-8")
    assert "🔵 [UPSTREAM DELTA]" in txt and "--improve --since 11112222 --target ccba-design" in txt
    assert txt.count("Skill: `polish`") == 2

    cfg = {
        "name": "impeccable",
        "type": "impeccable",
        "local_path": repo,
        "remote_url": "https://github.com/pbakaus/impeccable",
        "branch": "main",
        "sha_file": sha_f,
    }

    def broken_blob(cmd: list[str], **kw: object) -> MagicMock:
        if "diff" in cmd:
            return MagicMock(returncode=0, stdout="M\tskills/missing/SKILL.md\n")
        return MagicMock(returncode=128, stdout="")

    with (
        patch.object(ev, "get_remote_sha", return_value="9999888877776666"),
        patch.object(ev, "ensure_local_repo", return_value=True),
        patch("subprocess.run", side_effect=broken_blob),
    ):
        ev.check_and_evaluate_single(cfg)
    assert sha_f.read_text(encoding="utf-8") == "1111222233334444"


def test_seam_routing_parse_fallback_and_github_archived_badge() -> None:
    """Verify choose_model('audit') + max_tokens=2048 + parse_llm_json fallback and ARCHIVED badge."""
    from unittest.mock import MagicMock

    import scripts.spoke._upstream_helpers as uh

    mock_ai = MagicMock()
    mock_ai.chat.return_value = "<think>reasoning</think>\nNot valid JSON at all!"
    with (
        patch("scripts.spoke.upstream_evaluator.ai", mock_ai),
        patch("scripts.spoke.upstream_evaluator.get_existing_elements", return_value=([], [])),
    ):
        res = call_ai_evaluation(
            "engineer", "novel-skill", "# Skill", "https://github.com/o/r", use_cache=False
        )
    call_kw = mock_ai.chat.call_args.kwargs
    assert call_kw["max_tokens"] == 2048 and call_kw.get("model") is not None
    assert res["should_port"] is True

    with (
        patch("shutil.which", return_value="/usr/bin/gh"),
        patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="true\n")),
    ):
        assert (
            uh.check_github_archived(
                "https://github.com/org/archived-repo.git", _allow_in_pytest=True
            )
            is True
        )
    badge = format_vitality_badge(
        {
            "commits_count": 10,
            "last_commit_date": "2025-01-01",
            "age_days": 200,
            "stale": True,
            "archived": True,
            "ref": "HEAD",
            "error": None,
        }
    )
    assert "⚠️ STALE_UPSTREAM" in badge and "🏛️ ARCHIVED" in badge
    assert (
        generate_xia_command(
            ".md/r", "sk", "--improve", since_sha="abcd1234", target_skill="ccba-x"
        )
        == "/ccba-xia .md/r sk --improve --since abcd1234 --target ccba-x"
    )


def test_corpus_digest_cap_and_shared_triage_ledger(tmp_path: Path) -> None:
    """Verify <=30-line corpus digest and shared triage_ledger (SKIP, DELTA_UNKNOWN, DEFERRED cache)."""
    from unittest.mock import MagicMock

    import scripts.spoke._upstream_helpers as uh

    corpus = tmp_path / "pnp-list-formatting"
    (corpus / ".git").mkdir(parents=True)
    (corpus / "LICENSE").write_text(
        "MIT License\nPermission is hereby granted...", encoding="utf-8"
    )
    for idx in range(40):
        sub = corpus / f"sample-{idx:02d}" / "nested"
        sub.mkdir(parents=True)
        (sub / "view.json").write_text("{}", encoding="utf-8")
    digest = uh.build_corpus_digest(corpus)
    assert len(digest.splitlines()) <= 30 and "sample-00/" in digest

    recs, cache_f = tmp_path / "recs.md", tmp_path / "cache.json"
    cfg = {
        "name": "pnp-list-formatting",
        "type": "pnp-list-formatting",
        "source_kind": "reference_corpus",
        "default_target": "ccba-sharepoint-iac",
        "local_path": corpus,
        "remote_url": "https://github.com/pnp/List-Formatting",
    }
    ev = UpstreamEvaluator(configs=[cfg])
    gov_skip = {
        "triage_ledger": [
            {
                "source": "pnp-list-formatting",
                "upstream_path": ".",
                "target": "ccba-sharepoint-iac",
                "status": "ADOPTED",
                "reviewed_sha": "abc1234",
            }
        ]
    }
    with (
        patch("scripts.spoke.upstream_evaluator.RECOMMENDATIONS_FILE", recs),
        patch("scripts.spoke.upstream_evaluator.CACHE_FILE", cache_f),
        patch(
            "scripts.spoke.upstream_evaluator.load_upstream_governance_config",
            return_value=gov_skip,
        ),
        patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="")),
    ):
        ev.scan_and_evaluate_repo(cfg, "def5678")
    assert not recs.exists()

    with (
        patch("scripts.spoke.upstream_evaluator.RECOMMENDATIONS_FILE", recs),
        patch(
            "scripts.spoke.upstream_evaluator.load_upstream_governance_config",
            return_value=gov_skip,
        ),
        patch("subprocess.run", return_value=MagicMock(returncode=128, stdout="")),
    ):
        ev.scan_and_evaluate_repo(cfg, "def5678")
    assert "🟠 [DELTA UNKNOWN]" in recs.read_text(encoding="utf-8")

    gov_def = {
        "triage_ledger": [
            {
                "source": "pnp-list-formatting",
                "upstream_path": ".",
                "target": "ccba-sharepoint-iac",
                "status": "DEFERRED",
                "reviewed_sha": "abc1234",
            }
        ]
    }
    with (
        patch("scripts.spoke.upstream_evaluator.RECOMMENDATIONS_FILE", recs),
        patch("scripts.spoke.upstream_evaluator.CACHE_FILE", cache_f),
        patch(
            "scripts.spoke.upstream_evaluator.load_upstream_governance_config", return_value=gov_def
        ),
        patch(
            "scripts.spoke.upstream_evaluator.call_ai_evaluation", wraps=call_ai_evaluation
        ) as spy_eval,
        patch("scripts.spoke.upstream_evaluator.ai", None),
    ):
        ev.scan_and_evaluate_repo(cfg, "def5678")
        ev.scan_and_evaluate_repo(cfg, "def5678")
        assert spy_eval.call_count == 1


def test_surgical_triage_ledger_yaml_preserves_comments(tmp_path: Path) -> None:
    """Verify record_triage_decision updates/inserts ledger entries under MutexLock while keeping comments."""
    from scripts.spoke.upstream_evaluator import record_triage_decision

    yml = tmp_path / "upstream_sources.yaml"
    lock_f = tmp_path / "sync.lock"
    yml.write_text(
        "# Top header comment\nversion: '1.1'\n# Ledger section comment\ntriage_ledger:\n"
        '  - source: "mattpocock-skills"\n    upstream_path: "retro"\n'
        '    target: "ccba-session-retrospective"\n    status: "DECLINED"\n'
        '    reviewed_sha: "4ae2317"\n    reason: "Old"\n',
        encoding="utf-8",
    )
    with patch("scripts.spoke.upstream_evaluator.LOCK_FILE", lock_f):
        assert record_triage_decision(
            "mattpocock-skills",
            "retro",
            "ccba-session-retrospective",
            "ADOPTED",
            "9988776",
            "Updated",
            yml,
        )
        assert record_triage_decision(
            "pnp-list-formatting",
            ".",
            "ccba-sharepoint-iac",
            "DEFERRED",
            "1122334",
            "Corpus deferred",
            yml,
        )
    raw = yml.read_text(encoding="utf-8")
    assert "# Top header comment" in raw and "# Ledger section comment" in raw
    parsed = yaml.safe_load(raw)["triage_ledger"]
    assert (
        len(parsed) == 2
        and parsed[0]["status"] == "ADOPTED"
        and parsed[0]["reviewed_sha"] == "9988776"
    )
    assert parsed[1]["source"] == "pnp-list-formatting" and parsed[1]["status"] == "DEFERRED"


def test_dogfood_corpus_digest_under_md_scratch_and_ledger_prune(tmp_path: Path) -> None:
    """Verify corpus digest counts files inside .md/scratch/repos, skips tests/, and prunes closed ledger items."""
    import scripts.spoke._upstream_helpers as uh

    nested_corpus = tmp_path / ".md" / "scratch" / "repos" / "pnp-list-formatting"
    (nested_corpus / "column-samples" / "approval").mkdir(parents=True)
    (nested_corpus / "column-samples" / "approval" / "format.json").write_text(
        "{}", encoding="utf-8"
    )
    digest = uh.build_corpus_digest(nested_corpus)
    assert "column-samples/ (1 files; .json:1)" in digest

    repo_with_test_fixture = tmp_path / "impeccable"
    (repo_with_test_fixture / ".agent" / "skills" / "impeccable").mkdir(parents=True)
    (repo_with_test_fixture / ".agent" / "skills" / "impeccable" / "SKILL.md").write_text(
        "# Real", encoding="utf-8"
    )
    (repo_with_test_fixture / "tests" / "oracle" / "skills" / "audit").mkdir(parents=True)
    (repo_with_test_fixture / "tests" / "oracle" / "skills" / "audit" / "SKILL.md").write_text(
        "# Fixture", encoding="utf-8"
    )
    found = resolve_upstream_resources(repo_with_test_fixture, "impeccable")
    assert [r["name"] for r in found] == ["impeccable"]

    cfg_yml = tmp_path / "gov.yaml"
    cfg_yml.write_text(
        "triage_ledger:\n"
        "  - source: 'mattpocock-skills'\n"
        "    upstream_path: 'to-questionnaire'\n"
        "    target: 'ccba-grilling'\n"
        "    status: 'ADOPTED'\n"
        "    reviewed_sha: '4ae2317d'\n",
        encoding="utf-8",
    )
    rec = tmp_path / "recs.md"
    rec.write_text(
        "<!-- AUTO-GENERATED-START -->\n"
        "### 🟢 [RECOMMEND PORT] Skill: `to-questionnaire` (Score: 85/100)\n"
        "*   **Kho chứa nguồn**: `mattpocock-skills`\n"
        "\n---\n\n"
        "### 🟢 [RECOMMEND PORT] Skill: `chief-of-staff` (Score: 80/100)\n"
        "*   **Kho chứa nguồn**: `mattpocock-skills`\n"
        "<!-- AUTO-GENERATED-END -->\n",
        encoding="utf-8",
    )
    pruned = uh.prune_stale_recommendations(rec, cfg_yml)
    out = rec.read_text(encoding="utf-8")
    assert pruned == 1 and "to-questionnaire" not in out and "chief-of-staff" in out


def test_commercial_licensed_policy_preclamp_cache_and_bidirectional_prune(
    tmp_path: Path,
) -> None:
    """Verify COND-01..03 & COND-09: affirmative vs negated license, COMMERCIAL_LICENSED, v2 cache, and prune."""
    from unittest.mock import patch

    import scripts.spoke._upstream_helpers as uh
    from scripts.spoke.upstream_evaluator import (
        call_ai_evaluation,
        check_repo_license,
        load_eval_cache,
        save_eval_cache,
    )

    ms_mit = (
        "MIT License\nCopyright (c) Microsoft Corporation. All rights reserved.\n"
        "Permission is hereby granted, free of charge, to any person obtaining a copy..."
    )
    neg_prop = "Copyright (c) 2025 Vendor. All Rights Reserved. Not under MIT License or BSD."
    assert uh.classify_license_text(ms_mit)[0] == "PERMISSIVE"
    assert uh.classify_license_text(neg_prop)[0] == "PROPRIETARY"

    repo_prop = tmp_path / "prop_repo"
    repo_prop.mkdir()
    (repo_prop / "LICENSE").write_text(neg_prop, encoding="utf-8")
    assert check_repo_license(repo_prop, licensed_use=False)[0] == "PROPRIETARY"
    assert check_repo_license(repo_prop, licensed_use=True)[0] == "COMMERCIAL_LICENSED"

    repo_gpl = tmp_path / "gpl_repo"
    repo_gpl.mkdir()
    (repo_gpl / "LICENSE").write_text("GNU General Public License v3.0", encoding="utf-8")
    assert check_repo_license(repo_gpl, licensed_use=True)[0] == "COPYLEFT"

    repo_ms = tmp_path / "ms_repo"
    repo_ms.mkdir()
    (repo_ms / "LICENSE").write_text(ms_mit, encoding="utf-8")
    assert check_repo_license(repo_ms, licensed_use=False)[0] == "PERMISSIVE"

    clamped_comm = uh.clamp_license_policy(
        {
            "should_port": True,
            "xia_command": "/ccba-xia r s --copy-raw",
            "actionable_steps": [
                "Run `/ccba-xia r s --copy-raw`",
                "Keep `/ccba-xia r s --improve`",
            ],
        },
        "COMMERCIAL_LICENSED",
        "/ccba-xia r s --compare",
    )
    assert clamped_comm["should_port"] is True
    assert clamped_comm["xia_command"] == "/ccba-xia r s --port"
    assert "--port" in clamped_comm["actionable_steps"][0]
    assert "--improve" in clamped_comm["actionable_steps"][1]

    cf = tmp_path / "eval_cache.json"
    kw: dict[str, object] = {"CACHE_FILE": cf, "get_existing_elements": lambda: ([], [])}
    with patch.multiple("scripts.spoke.upstream_evaluator", **kw):
        save_eval_cache(
            {
                "marketing:ab-test:PROPRIETARY:aaa": {
                    "should_port": False,
                    "status_override": "COMPARE ONLY — LICENSE RESTRICTED",
                }
            }
        )
        assert load_eval_cache() == {}
        r1 = call_ai_evaluation(
            "marketing", "ab-test", "# AB", "https://g.co/m", "PROPRIETARY", fast=True
        )
        assert (
            r1["should_port"] is False
            and r1["status_override"] == "COMPARE ONLY — LICENSE RESTRICTED"
        )
        r2 = call_ai_evaluation(
            "marketing", "ab-test", "# AB", "https://g.co/m", "COMMERCIAL_LICENSED", fast=True
        )
        assert r2["should_port"] is True and "status_override" not in r2

    cfg_yml = tmp_path / "sources.yaml"
    cfg_yml.write_text(
        "sources:\n"
        "  - name: 'claudekit-marketing'\n"
        "    type: 'marketing'\n"
        "    remote_url: 'https://g.co/m'\n"
        "  - name: 'pnp-list-formatting'\n"
        "    type: 'pnp-list-formatting'\n"
        "    source_kind: 'reference_corpus'\n"
        "    remote_url: 'https://g.co/p'\n"
        "triage_ledger:\n"
        "  - source: 'claudekit-marketing'\n"
        "    upstream_path: 'ab-test-setup'\n"
        "    target: 'ccba-copywriting'\n"
        "    status: 'ADOPTED'\n"
        "    reviewed_sha: '11c5eb05'\n"
        "  - source: 'pnp-list-formatting'\n"
        "    upstream_path: '.'\n"
        "    target: 'ccba-sharepoint-iac'\n"
        "    status: 'ADOPTED'\n"
        "    reviewed_sha: '24a2a4ea'\n",
        encoding="utf-8",
    )
    rec = tmp_path / "port_recs.md"
    rec.write_text(
        "<!-- AUTO-GENERATED-START -->\n"
        "### 🟠 [COMPARE ONLY — LICENSE RESTRICTED] Skill: `ab-test-setup` (Score: 85/100)\n"
        "*   **Kho chứa nguồn**: `marketing`\n"
        "*   **Giấy phép (License)**: Bản quyền đóng\n"
        "\n---\n\n"
        "### 🟢 [RECOMMEND PORT] Skill: `pnp-list-formatting (corpus)` (Score: 80/100)\n"
        "*   **Kho chứa nguồn**: `pnp-list-formatting`\n"
        "<!-- AUTO-GENERATED-END -->\n",
        encoding="utf-8",
    )
    assert uh.prune_stale_recommendations(rec, cfg_yml) == 2
    assert "### " not in rec.read_text(encoding="utf-8")


def test_pstack_registered_with_baseline_ledger_and_aliases() -> None:
    """Verify backnotprop/pstack is registered in upstream_sources.yaml with v0.15.36 baseline."""
    import scripts.spoke._upstream_helpers as uh
    from scripts.spoke.upstream_evaluator import get_existing_elements

    sources = {s["name"]: s for s in load_upstream_sources()}
    assert "pstack" in sources
    pstack = sources["pstack"]
    assert pstack["source_kind"] == "skills"
    assert pstack["remote_url"] == "https://github.com/backnotprop/pstack"

    gov = uh.load_governance_config(uh._CANONICAL_YAML)
    aliases = gov["aliases"]
    assert aliases["interrogate"] == "ccba-code-review"
    assert aliases["statechart"] == "ccba-mermaid-diagram"
    assert aliases["ketchup"] == "ccba-handoff"
    assert aliases["unslop"] == "ccba-code-review"

    pstack_entries = [e for e in gov["triage_ledger"] if e.get("source") == "pstack"]
    assert len(pstack_entries) == 61
    assert all(e.get("reviewed_sha") == "97de40dc" for e in pstack_entries)
    existing_skills, existing_workflows = get_existing_elements()
    dup, matched = check_is_duplicate("interrogate", existing_skills, existing_workflows)
    assert dup is True and matched == "ccba-code-review"
