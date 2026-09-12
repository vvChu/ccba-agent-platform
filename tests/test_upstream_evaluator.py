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
    generate_xia_command,
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
    repo_dir.mkdir()
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
