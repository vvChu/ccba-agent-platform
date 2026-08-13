#!/usr/bin/env python3
"""
Deep Module for Upstream Repository Synchronization and Feature Evaluation.
Handles cloning, fetching, diffing, AI evaluation, and parse-protected reporting.
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

# Enforce UTF-8 output on Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Attempt importing AI Gateway
try:
    from ccba_ai import ai
except ImportError:
    ai = None

PLATFORM_ROOT = Path(__file__).resolve().parents[2]
RECOMMENDATIONS_FILE = PLATFORM_ROOT / ".md" / "knowledge" / "port_recommendations.md"

REPOS_CONFIG = [
    {
        "type": "engineer",
        "local_path": PLATFORM_ROOT / ".md/scratch/repos/claudekit-engineer",
        "remote_url": "https://github.com/claudekit/claudekit-engineer",
        "sha_file": PLATFORM_ROOT / ".md/scratch/claudekit_last_sha.txt",
    },
    {
        "type": "marketing",
        "local_path": PLATFORM_ROOT / ".md/scratch/repos/claudekit-marketing",
        "remote_url": "https://github.com/claudekit/claudekit-marketing",
        "sha_file": PLATFORM_ROOT / ".md/scratch/claudekit_marketing_last_sha.txt",
    },
    {
        "type": "mattpocock-skills",
        "local_path": PLATFORM_ROOT / ".md/scratch/repos/mattpocock-skills",
        "remote_url": "https://github.com/mattpocock/skills",
        "sha_file": PLATFORM_ROOT / ".md/scratch/mattpocock_skills_last_sha.txt",
    },
]


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


def call_ai_evaluation(repo_type: str, skill_name: str, content: str) -> dict:
    """Evaluate a skill using AI Gateway, or Rule-Based Fallback if unavailable."""
    existing_skills, existing_workflows = get_existing_elements()

    is_duplicate = skill_name in existing_skills or skill_name in existing_workflows
    similar_skills = [s for s in existing_skills if skill_name in s or s in skill_name]

    if is_duplicate:
        return {
            "should_port": False,
            "score": 25,
            "reason": f"IGNORE (Đã tồn tại): Kỹ năng '{skill_name}' đã tồn tại sẵn trên local catalog.",
            "actionable_steps": [
                "So sánh tệp SKILL.md mới với phiên bản local",
                "Cherry-pick cải tiến nếu cần thay vì port mới",
            ],
        }

    if ai is not None:
        system_prompt = (
            "Bạn là kiến trúc sư phần mềm trưởng của ccba-agent-platform.\n"
            "Nhiệm vụ của bạn là đánh giá xem có nên port một kỹ năng mới từ thượng nguồn hay không.\n"
            "Phản hồi bằng JSON sạch:\n"
            "{\n"
            '  "should_port": true/false,\n'
            '  "score": 0-100,\n'
            '  "reason": "Tóm tắt lý do bằng tiếng Việt",\n'
            '  "actionable_steps": ["Bước 1...", "Bước 2..."]\n'
            "}"
        )

        user_prompt = f"""
        Kho thượng nguồn: {repo_type}
        Tên kỹ năng đề xuất: {skill_name}
        Kỹ năng tương tự trên local: {similar_skills}
        Danh sách skills hiện có: {existing_skills}
        Nội dung SKILL.md:
        ```markdown
        {content}
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
            return json.loads(clean_reply)
        except Exception as e:
            print(f"[Evaluator] AI Gateway error: {e}. Switching to Rule-Based Fallback.")

    # Rule-Based Fallback when AI Gateway is not available
    return {
        "should_port": True,
        "score": 85,
        "reason": "Kỹ năng mới chưa có trên local catalog (AI Gateway không khả dụng - Cần rà soát thủ công).",
        "actionable_steps": ["Rà soát thủ công tệp SKILL.md", "Port qua ccba-kit"],
    }


def append_recommendation(repo_type: str, skill_name: str, result: dict):
    """Write recommendation to port_recommendations.md using Parse-Protection markers."""
    try:
        if not RECOMMENDATIONS_FILE.parent.exists():
            RECOMMENDATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)

        header = f"# 📋 Upstream Porting Recommendations\n\nBáo cáo tự động đánh giá các tính năng mới từ thượng nguồn. Cập nhật ngày: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        content = ""
        developer_notes = "\n\n<!-- DEVELOPER-NOTES-START -->\n## 📝 Ghi chú của Kỹ sư (Developer Notes)\n*Kỹ sư có thể tự do ghi chép các phân tích, đánh giá thủ công tại đây. Phần này sẽ được tự động bảo toàn khi đồng bộ thượng nguồn.*\n<!-- DEVELOPER-NOTES-END -->"

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

        if is_duplicate:
            status_text = "IGNORE (Đã tồn tại)"
            color = "🔴"
        elif not result.get("should_port", True):
            status_text = "IGNORE"
            color = "🔴"
        else:
            status_text = "RECOMMEND PORT"
            color = "🟢"

        item_md = f"""
---

### {color} [{status_text}] Skill: `{skill_name}` (Score: {result.get("score", 0)}/100)
*   **Kho chứa nguồn**: `{repo_type}`
*   **Đánh giá**: {result.get("reason", "Không có lý do chi tiết từ AI")}
*   **Các bước triển khai**:
"""
        for step in result.get("actionable_steps", []):
            item_md += f"    *   {step}\n"

        if f"`{skill_name}`" not in auto_gen_content:
            auto_gen_content += "\n" + item_md.strip()

        final_content = f"<!-- AUTO-GENERATED-START -->\n{auto_gen_content.strip()}\n<!-- AUTO-GENERATED-END -->{developer_notes}"

        RECOMMENDATIONS_FILE.write_text(final_content, encoding="utf-8")
        print(f"[Evaluator] Wrote recommendation for '{skill_name}' -> {status_text}")
    except Exception as e:
        print(f"[Evaluator] Error writing recommendation: {e}")


class UpstreamEvaluator:
    """Unified engine for upstream repository updates and feature evaluation."""

    def __init__(self, configs: list[dict] = None):
        self.configs = configs or REPOS_CONFIG

    def ensure_local_repo(self, config: dict) -> bool:
        """Ensure the local repository is cloned and updated."""
        local_path = config["local_path"]
        remote_url = config["remote_url"]
        repo_type = config["type"]

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
                default_branch = "main"
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

    def get_local_sha(self, config: dict) -> str:
        """Get the recorded SHA or the current local clone's head commit."""
        sha_file = config["sha_file"]
        if sha_file.exists():
            return sha_file.read_text(encoding="utf-8").strip()

        local_path = config["local_path"]
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

    def evaluate_repo_diff(self, repo_path: Path, base_sha: str, head_sha: str, repo_type: str):
        """Run git diff and evaluate modified or new skills."""
        if not repo_path.exists():
            return

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
                    skill_name = match.group(2) if repo_type == "mattpocock-skills" else match.group(1)
                    print(f"[Evaluator] Found new/modified skill: '{skill_name}' in {repo_type}")

                    show_res = subprocess.run(
                        ["git", "show", f"{head_sha}:{f}"],
                        cwd=str(repo_path),
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    skill_content = show_res.stdout
                    result = call_ai_evaluation(repo_type, skill_name, skill_content)
                    append_recommendation(repo_type, skill_name, result)
        except subprocess.SubprocessError as e:
            print(f"[Evaluator] Git diff error in '{repo_path}': {e}")

    def check_and_evaluate_single(self, config: dict, check_only: bool = False):
        """Check and evaluate a single repository config."""
        repo_type = config["type"]
        local_path = config["local_path"]
        remote_url = config["remote_url"]
        sha_file = config["sha_file"]

        print(f"[Upstream Check] Checking remote {repo_type} for new updates...")

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
            print(f"[Upstream Check] Initializing tracker for {repo_type} with remote SHA: {remote_sha[:8]}")
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

            print("  - Running Automated Feature Evaluator...")
            self.evaluate_repo_diff(local_path, local_sha, remote_sha, repo_type)
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

    parser = argparse.ArgumentParser(description="CCBA Upstream Synchronization & Evaluation Engine")
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
