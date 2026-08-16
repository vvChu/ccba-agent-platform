#!/usr/bin/env python3
"""Deep Module for Upstream Repository Synchronization and Feature Evaluation.

Handles dynamic repo configuration, cloning, fetching, diffing, ADR-0040 informed
AI evaluation, license auditing, and parse-protected 1-click reporting for ccba-xia.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

# Attempt importing AI Gateway
try:
    from ccba_ai import ai
except ImportError:
    ai = None


PLATFORM_ROOT = Path(__file__).resolve().parents[2]
SOURCES_CONFIG_FILE = PLATFORM_ROOT / ".md" / "knowledge" / "upstream_sources.yaml"
RECOMMENDATIONS_FILE = PLATFORM_ROOT / ".md" / "knowledge" / "port_recommendations.md"

DEFAULT_REPOS_CONFIG = [
    {
        "name": "claudekit-engineer",
        "type": "engineer",
        "local_path": PLATFORM_ROOT / ".md/scratch/repos/claudekit-engineer",
        "remote_url": "https://github.com/claudekit/claudekit-engineer",
        "branch": "main",
        "sha_file": PLATFORM_ROOT / ".md/scratch/claudekit_last_sha.txt",
        "description": "ClaudeKit Engineering Skills",
    },
    {
        "name": "claudekit-marketing",
        "type": "marketing",
        "local_path": PLATFORM_ROOT / ".md/scratch/repos/claudekit-marketing",
        "remote_url": "https://github.com/claudekit/claudekit-marketing",
        "branch": "main",
        "sha_file": PLATFORM_ROOT / ".md/scratch/claudekit_marketing_last_sha.txt",
        "description": "ClaudeKit Marketing Skills",
    },
    {
        "name": "mattpocock-skills",
        "type": "mattpocock-skills",
        "local_path": PLATFORM_ROOT / ".md/scratch/repos/mattpocock-skills",
        "remote_url": "https://github.com/mattpocock/skills",
        "branch": "main",
        "sha_file": PLATFORM_ROOT / ".md/scratch/mattpocock_skills_last_sha.txt",
        "description": "Matt Pocock Skills Repository",
    },
]


def load_upstream_sources(config_file: Path | None = None) -> list[dict[str, Any]]:
    """Load upstream repositories configuration from YAML with fallback to defaults."""
    target_file = config_file or SOURCES_CONFIG_FILE
    if not target_file.exists():
        return DEFAULT_REPOS_CONFIG

    try:
        content = target_file.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        if not isinstance(data, dict) or "sources" not in data:
            return DEFAULT_REPOS_CONFIG

        sources: list[dict[str, Any]] = []
        for s in data.get("sources", []):
            if not isinstance(s, dict) or not s.get("enabled", True):
                continue
            name = str(s.get("name", s.get("type", "unknown")))
            repo_type = str(s.get("type", name))
            remote_url = str(s.get("remote_url", ""))
            branch = str(s.get("branch", "main"))
            description = str(s.get("description", ""))

            sources.append(
                {
                    "name": name,
                    "type": repo_type,
                    "local_path": PLATFORM_ROOT / ".md" / "scratch" / "repos" / name,
                    "remote_url": remote_url,
                    "branch": branch,
                    "sha_file": PLATFORM_ROOT / ".md" / "scratch" / f"{name}_last_sha.txt",
                    "description": description,
                }
            )
        return sources if sources else DEFAULT_REPOS_CONFIG
    except Exception as e:
        print(f"[Evaluator] Warning: Could not parse {target_file}: {e}. Using defaults.")
        return DEFAULT_REPOS_CONFIG


def check_repo_license(repo_path: Path) -> tuple[str, str]:
    """Audit license file in repository and classify type (PERMISSIVE, COPYLEFT, PROPRIETARY, UNKNOWN)."""
    if not repo_path.exists():
        return "UNKNOWN", "Thư mục không tồn tại"

    license_names = [
        "LICENSE",
        "LICENSE.md",
        "LICENSE.txt",
        "COPYING",
        "LICENSE-MIT",
        "LICENSE-APACHE",
    ]
    for name in license_names:
        lic_file = repo_path / name
        if lic_file.exists():
            try:
                text = lic_file.read_text(encoding="utf-8", errors="ignore").lower()
                if (
                    "gnu general public" in text
                    or "gpl" in text
                    or "agpl" in text
                    or "lgpl" in text
                ):
                    return "COPYLEFT", "GPL/AGPL/LGPL (Rủi ro sao chép mã nguồn)"
                if "mit license" in text or "permission is hereby granted" in text:
                    return "PERMISSIVE", "MIT License (Tự do sử dụng)"
                if "apache license" in text:
                    return "PERMISSIVE", "Apache 2.0 License (Tự do sử dụng)"
                if "bsd" in text:
                    return "PERMISSIVE", "BSD License (Tự do sử dụng)"
                if "all rights reserved" in text or "proprietary" in text:
                    return "PROPRIETARY", "Bản quyền đóng (Không được sao chép)"
                return "CUSTOM", "Giấy phép riêng biệt"
            except Exception:
                pass

    return "UNKNOWN", "Không phát hiện tệp LICENSE rõ ràng"


def get_existing_elements() -> tuple[list[str], list[str]]:
    """Load existing skills and workflows from catalog.yaml."""
    catalog_path = PLATFORM_ROOT / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
    if not catalog_path.exists():
        return [], []
    try:
        with open(catalog_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            skills = [s["name"] for s in data.get("skills", []) if "name" in s]
            workflows = [w["name"] for w in data.get("workflows", []) if "name" in w]
            return skills, workflows
    except Exception as e:
        print(f"[Evaluator] Warning: Could not parse catalog.yaml: {e}")
        return [], []


def generate_xia_command(remote_url: str, skill_name: str, mode: str = "--compare") -> str:
    """Generate 1-click CLI command for ccba-xia."""
    if remote_url:
        return f"/ccba-xia {remote_url} {skill_name} {mode}"
    return f"/ccba-xia <repo-url> {skill_name} {mode}"


def call_ai_evaluation(
    repo_type: str,
    skill_name: str,
    content: str,
    remote_url: str = "",
    license_type: str = "PERMISSIVE",
) -> dict[str, Any]:
    """Evaluate a skill using AI Gateway under ADR-0040 (3-Tier Skill Hierarchy), with Rule-Based Fallback."""
    existing_skills, existing_workflows = get_existing_elements()

    is_duplicate = skill_name in existing_skills or skill_name in existing_workflows
    similar_skills = [s for s in existing_skills if skill_name in s or s in skill_name]

    if is_duplicate:
        return {
            "should_port": False,
            "score": 20,
            "recommended_tier": "Reject/Duplicate",
            "target_bundle": "_core",
            "disable_model_invocation": True,
            "parent_master_skill": None,
            "python_compatibility_assessment": "Đã tồn tại tương đương trên hệ thống.",
            "reason": f"IGNORE (Đã tồn tại): Kỹ năng '{skill_name}' đã tồn tại sẵn trên local catalog.",
            "actionable_steps": [
                "So sánh tệp SKILL.md mới với phiên bản local",
                "Cherry-pick cải tiến quy trình nếu cần thay vì port mới",
            ],
            "xia_command": generate_xia_command(remote_url, skill_name, "--compare"),
        }

    if ai is not None:
        system_prompt = (
            "Bạn là Kiến trúc sư trưởng của ccba-agent-platform (Python Monorepo).\n"
            "Nhiệm vụ: Đánh giá kỹ năng mới từ kho thượng nguồn theo thể chế ADR-0040 (Kim tự tháp 3 Tầng):\n"
            "- Tier 1 (Master Deep Skill): model-invoked, logic dày, <= 10 skill/bundle.\n"
            "- Tier 2 (Progressive Reference): tài liệu tham chiếu sâu nằm trong references/ của một Master Skill.\n"
            "- Tier 3 (User Workflow): workflow thủ công của người dùng với 'disable-model-invocation: true'.\n\n"
            "Hãy phân tích và trả về JSON thuần túy (không markdown block):\n"
            "{\n"
            '  "should_port": true/false,\n'
            '  "score": 0-100,\n'
            '  "recommended_tier": "Tier 1" | "Tier 2" | "Tier 3" | "Reject",\n'
            '  "target_bundle": "_core" | "_software" | "_consulting" | "_qc" | "_bim",\n'
            '  "disable_model_invocation": true/false,\n'
            '  "parent_master_skill": "tên master skill nếu là Tier 2 hoặc null",\n'
            '  "python_compatibility_assessment": "Đánh giá mức độ phù hợp khi chuyển sang Python Monorepo",\n'
            '  "reason": "Tóm tắt lý do bằng tiếng Việt",\n'
            '  "actionable_steps": ["Bước 1...", "Bước 2..."]\n'
            "}"
        )

        user_prompt = f"""
        Kho thượng nguồn: {repo_type} ({remote_url})
        Giấy phép repo: {license_type}
        Tên kỹ năng đề xuất: {skill_name}
        Kỹ năng tương tự trên local: {similar_skills}
        Danh sách skills hiện có ({len(existing_skills)} skills): {existing_skills[:30]}...
        Nội dung SKILL.md:
        ```markdown
        {content[:4000]}
        ```
        """
        try:
            reply = ai.chat(user_prompt, system=system_prompt)
            clean_reply = reply.strip()
            if clean_reply.startswith("```json"):
                clean_reply = clean_reply[7:]
            if clean_reply.endswith("```"):
                clean_reply = clean_reply[:-3]
            clean_reply = clean_reply.strip()
            result = json.loads(clean_reply)
            result["xia_command"] = generate_xia_command(
                remote_url, skill_name, "--port" if result.get("should_port") else "--compare"
            )
            return result
        except Exception as e:
            print(f"[Evaluator] AI Gateway error: {e}. Switching to Rule-Based Fallback.")

    # Rule-Based Fallback when AI Gateway is not available
    is_workflow_like = any(
        kw in skill_name for kw in ["workflow", "setup", "sync", "run", "to-", "create"]
    )
    recommended_tier = (
        "Tier 3 (User Workflow)" if is_workflow_like else "Tier 2 (Progressive Reference)"
    )
    return {
        "should_port": True,
        "score": 80,
        "recommended_tier": recommended_tier,
        "target_bundle": "_software",
        "disable_model_invocation": True,
        "parent_master_skill": "codebase-design" if not is_workflow_like else None,
        "python_compatibility_assessment": "Cần địa hóa sang môi trường Python / Ruff / PyTest.",
        "reason": f"Kỹ năng mới chưa có trên catalog ({license_type}). Đề xuất đánh giá qua /ccba-xia.",
        "actionable_steps": [
            f"Chạy lệnh `{generate_xia_command(remote_url, skill_name, '--compare')}` để trinh sát",
            "Xem xét bóc tách thành Progressive Reference theo ADR-0040",
        ],
        "xia_command": generate_xia_command(remote_url, skill_name, "--compare"),
    }


def append_recommendation(
    repo_type: str,
    skill_name: str,
    result: dict[str, Any],
    remote_url: str = "",
    license_desc: str = "MIT License",
):
    """Write recommendation to port_recommendations.md using Parse-Protection markers."""
    try:
        if not RECOMMENDATIONS_FILE.parent.exists():
            RECOMMENDATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)

        header = (
            "# 📋 Upstream Porting Recommendations (ADR-0040 Radar)\n\n"
            f"Báo cáo tự động đánh giá các tính năng mới từ thượng nguồn. Cập nhật ngày: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

        content = ""
        developer_notes = (
            "\n\n<!-- DEVELOPER-NOTES-START -->\n"
            "## 📝 Ghi chú của Kỹ sư (Developer Notes)\n"
            "*Kỹ sư có thể tự do ghi chép các phân tích, đánh giá thủ công tại đây. Phần này sẽ được tự động bảo toàn khi đồng bộ thượng nguồn.*\n"
            "<!-- DEVELOPER-NOTES-END -->"
        )

        if RECOMMENDATIONS_FILE.exists():
            content = RECOMMENDATIONS_FILE.read_text(encoding="utf-8")

        notes_match = re.search(
            r"(<!-- DEVELOPER-NOTES-START -->.*?<!-- DEVELOPER-NOTES-END -->)", content, re.DOTALL
        )
        if notes_match:
            developer_notes = "\n\n" + notes_match.group(1)

        auto_gen_content = ""
        auto_match = re.search(
            r"<!-- AUTO-GENERATED-START -->(.*?)<!-- AUTO-GENERATED-END -->", content, re.DOTALL
        )
        if auto_match:
            auto_gen_content = auto_match.group(1).strip()
        else:
            if content.strip().startswith("# 📋 Upstream"):
                clean_content = content
                if notes_match:
                    clean_content = clean_content.replace(notes_match.group(1), "")
                auto_gen_content = clean_content.strip()
            else:
                auto_gen_content = header.strip()

        existing_skills, existing_workflows = get_existing_elements()
        is_duplicate = skill_name in existing_skills or skill_name in existing_workflows

        tier = result.get("recommended_tier", "Tier 3")
        bundle = result.get("target_bundle", "_software")
        disable_inv = result.get("disable_model_invocation", True)
        py_compat = result.get("python_compatibility_assessment", "Chưa có đánh giá")
        xia_cmd = result.get("xia_command", generate_xia_command(remote_url, skill_name))

        if is_duplicate or not result.get("should_port", True):
            status_text = "IGNORE"
            color = "🔴"
        else:
            status_text = "RECOMMEND PORT"
            color = "🟢"

        item_md = f"""
---

### {color} [{status_text}] Skill: `{skill_name}` (Score: {result.get("score", 0)}/100) — {tier}
*   **Kho chứa nguồn**: `{repo_type}` ({remote_url})
*   **Bản quyền**: `{license_desc}`
*   **Phân tầng đề xuất (ADR-0040)**: `{tier}` (Bundle: `{bundle}`, `disable-model-invocation: {str(disable_inv).lower()}`)
*   **Đánh giá tương thích Python**: {py_compat}
*   **Lý do**: {result.get("reason", "Không có lý do chi tiết từ AI")}
*   **Các bước triển khai**:
"""
        for step in result.get("actionable_steps", []):
            item_md += f"    *   {step}\n"

        item_md += f"> ⚡ **Lệnh kích hoạt Port 1-Click:** `{xia_cmd}`\n"

        if f"`{skill_name}`" not in auto_gen_content:
            auto_gen_content += "\n" + item_md.strip()

        final_content = f"<!-- AUTO-GENERATED-START -->\n{auto_gen_content.strip()}\n<!-- AUTO-GENERATED-END -->{developer_notes}"

        RECOMMENDATIONS_FILE.write_text(final_content, encoding="utf-8")
        print(f"[Evaluator] Wrote recommendation for '{skill_name}' -> {status_text} ({tier})")
    except Exception as e:
        print(f"[Evaluator] Error writing recommendation: {e}")


class UpstreamEvaluator:
    """Unified engine for upstream repository updates and feature evaluation."""

    def __init__(self, configs: list[dict[str, Any]] | None = None):
        self.configs = configs or load_upstream_sources()

    def ensure_local_repo(self, config: dict[str, Any]) -> bool:
        """Ensure the local repository is cloned and updated."""
        local_path: Path = config["local_path"]
        remote_url: str = config["remote_url"]
        repo_type: str = config["type"]

        if not local_path.exists():
            print(f"[Repo Update] Cloning {repo_type} from {remote_url}...")
            local_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                subprocess.run(
                    ["git", "clone", remote_url, str(local_path)], check=True, capture_output=True
                )
                print(f"[Repo Update] Successfully cloned {repo_type}.")
                return True
            except subprocess.SubprocessError as e:
                print(f"[Repo Update] Error cloning {repo_type}: {e}")
                return False
        else:
            try:
                print(f"[Repo Update] Fetching updates for {repo_type}...")
                subprocess.run(
                    ["git", "fetch", "origin"], cwd=str(local_path), check=True, capture_output=True
                )
                res = subprocess.run(
                    ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
                    cwd=str(local_path),
                    capture_output=True,
                    text=True,
                )
                default_branch = config.get("branch", "main")
                if res.returncode == 0:
                    default_branch = res.stdout.strip().split("/")[-1]

                subprocess.run(
                    ["git", "reset", "--hard", f"origin/{default_branch}"],
                    cwd=str(local_path),
                    check=True,
                    capture_output=True,
                )
                print(f"[Repo Update] Successfully updated {repo_type}.")
                return True
            except subprocess.SubprocessError as e:
                print(f"[Repo Update] Error updating {repo_type}: {e}")
                return False

    def get_local_sha(self, config: dict[str, Any]) -> str:
        """Get the recorded SHA or the current local clone's head commit."""
        sha_file: Path = config["sha_file"]
        if sha_file.exists():
            return sha_file.read_text(encoding="utf-8").strip()

        local_path: Path = config["local_path"]
        if local_path.exists() and (local_path / ".git").exists():
            try:
                res = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=str(local_path),
                    capture_output=True,
                    text=True,
                    check=True,
                )
                sha = res.stdout.strip()
                sha_file.write_text(sha, encoding="utf-8")
                return sha
            except subprocess.SubprocessError:
                pass
        return ""

    def get_remote_sha(self, remote_url: str) -> str:
        """Query git ls-remote for the remote repository head commit."""
        for ref in ["refs/heads/main", "refs/heads/master"]:
            try:
                res = subprocess.run(
                    ["git", "ls-remote", remote_url, ref],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                output = res.stdout.strip()
                if output:
                    return output.split()[0]
            except subprocess.SubprocessError:
                pass
        return ""

    def evaluate_repo_diff(
        self, repo_path: Path, base_sha: str, head_sha: str, repo_type: str, remote_url: str
    ):
        """Run git diff and evaluate modified or new skills under ADR-0040."""
        if not repo_path.exists():
            return

        license_type, license_desc = check_repo_license(repo_path)

        try:
            res = subprocess.run(
                ["git", "diff", "--name-only", base_sha, head_sha],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                check=True,
            )
            files = res.stdout.strip().splitlines()

            if repo_type == "mattpocock-skills":
                skill_pattern = re.compile(r"skills/([^/]+)/([^/]+)/SKILL\.md$")
            else:
                skill_pattern = re.compile(r"claude/skills/([^/]+)/SKILL\.md$")

            for f in files:
                match = skill_pattern.search(f)
                if match:
                    skill_name = (
                        match.group(2) if repo_type == "mattpocock-skills" else match.group(1)
                    )
                    print(f"[Evaluator] Found new/modified skill: '{skill_name}' in {repo_type}")

                    show_res = subprocess.run(
                        ["git", "show", f"{head_sha}:{f}"],
                        cwd=str(repo_path),
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    skill_content = show_res.stdout
                    result = call_ai_evaluation(
                        repo_type=repo_type,
                        skill_name=skill_name,
                        content=skill_content,
                        remote_url=remote_url,
                        license_type=license_type,
                    )
                    append_recommendation(
                        repo_type=repo_type,
                        skill_name=skill_name,
                        result=result,
                        remote_url=remote_url,
                        license_desc=license_desc,
                    )
        except subprocess.SubprocessError as e:
            print(f"[Evaluator] Git diff error in '{repo_path}': {e}")

    def check_and_evaluate_single(self, config: dict[str, Any], check_only: bool = False):
        """Check and evaluate a single repository config."""
        repo_type = config["type"]
        local_path: Path = config["local_path"]
        remote_url: str = config["remote_url"]
        sha_file: Path = config["sha_file"]

        print(f"[Upstream Check] Checking remote {repo_type} ({remote_url}) for new updates...")

        remote_sha = self.get_remote_sha(remote_url)
        if not remote_sha:
            print(f"[Upstream Check] Warning: Could not connect to remote {repo_type}.")
            return

        success = self.ensure_local_repo(config)
        if not success:
            print(f"[Upstream Check] Warning: Failed to sync local repo for {repo_type}.")
            return

        local_sha = self.get_local_sha(config)

        if not local_sha:
            print(
                f"[Upstream Check] Initializing tracker for {repo_type} with remote SHA: {remote_sha[:8]}"
            )
            if not check_only:
                sha_file.write_text(remote_sha, encoding="utf-8")
            return

        if local_sha != remote_sha:
            print(f"\n\x1b[33m[UPDATE AVAILABLE]\x1b[0m New updates found in {repo_type}!")
            print(f"  - Local SHA:  {local_sha[:8]}")
            print(f"  - Remote SHA: {remote_sha[:8]}")

            try:
                diff_res = subprocess.run(
                    ["git", "diff", "--name-only", local_sha, remote_sha],
                    cwd=str(local_path),
                    capture_output=True,
                    text=True,
                    check=True,
                )
                changed_files = diff_res.stdout.strip().splitlines()
                if changed_files:
                    print("  - Changed files:")
                    for f in changed_files:
                        print(f"    * {f}")
            except Exception as e:
                print(f"  - Error retrieving changed files: {e}")

            if check_only:
                print("  - [Check-Only Mode] Skipping automated evaluator.\n")
                return

            print("  - Running Automated ADR-0040 Feature Evaluator...")
            self.evaluate_repo_diff(local_path, local_sha, remote_sha, repo_type, remote_url)
            sha_file.write_text(remote_sha, encoding="utf-8")
            print(f"[Upstream Check] Successfully processed updates for {repo_type}.\n")
        else:
            print(f"[Upstream Check] {repo_type} is up-to-date.")

    def sync_and_evaluate(self, check_only: bool = False):
        """Run update checks across all configured repositories."""
        print("[Upstream Check] Running update checks across repositories...\n")
        for config in self.configs:
            self.check_and_evaluate_single(config, check_only=check_only)
        print("\n[Upstream Check] All update checks completed.")


def main():
    import argparse

    if sys.platform == "win32":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="CCBA Upstream Synchronization & Evaluation Engine (ADR-0040 Radar)"
    )

    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check for updates and list changed files without evaluating",
    )
    args = parser.parse_args()

    evaluator = UpstreamEvaluator()
    evaluator.sync_and_evaluate(check_only=args.check_only)


if __name__ == "__main__":
    main()
