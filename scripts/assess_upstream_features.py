#!/usr/bin/env python3
"""
Automated Upstream Porting Evaluator for ccba-agent-platform.
Checks differences in claudekit-engineer and claudekit-marketing repositories,
identifies new skills, and evaluates them using AI Gateway.
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Enforce UTF-8 output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Attempt importing AI Gateway
try:
    from ccba_ai import ai
except ImportError:
    # Fail-safe local mock class if package not found
    class MockAI:
        def chat(self, prompt, model=None, system=None, format=None):
            return json.dumps({
                "should_port": True,
                "score": 85,
                "reason": "AI Gateway SDK missing - simulated approval",
                "actionable_steps": ["Verify manually", "Port via ccba-kit"]
            })
    ai = MockAI()

import yaml

PLATFORM_ROOT = Path(__file__).resolve().parents[1]
RECOMMENDATIONS_FILE = PLATFORM_ROOT / ".md" / "knowledge" / "port_recommendations.md"


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
    """Send skill details to AI Gateway for suitability review."""
    existing_skills, existing_workflows = get_existing_elements()

    # Check for direct duplicates first
    is_duplicate = skill_name in existing_skills or skill_name in existing_workflows
    similar_skills = [s for s in existing_skills if skill_name in s or s in skill_name]

    system_prompt = (
        "Bạn là kiến trúc sư phần mềm trưởng của ccba-agent-platform.\n"
        "Nhiệm vụ của bạn là đánh giá xem có nên port một kỹ năng mới từ ClaudeKit hoặc MattPocock thượng nguồn (upstream) sang nền tảng của mình hay không.\n"
        "Hãy phản hồi bằng định dạng JSON sạch có cấu trúc sau:\n"
        "{\n"
        "  \"should_port\": true/false,\n"
        "  \"score\": 0-100,\n"
        "  \"reason\": \"Tóm tắt lý do bằng tiếng Việt\",\n"
        "  \"actionable_steps\": [\"Bước 1...\", \"Bước 2...\"]\n"
        "}"
    )

    duplicate_context = ""
    if is_duplicate:
        duplicate_context = f"\nCẢNH BÁO: Kỹ năng này trùng tên với một thành phần ĐÃ TỒN TẠI trên local: '{skill_name}'."
    elif similar_skills:
        duplicate_context = f"\nCẢNH BÁO: Kỹ năng này có thể tương tự/trùng lặp với các thành phần ĐÃ TỒN TẠI trên local: {similar_skills}."

    user_prompt = f"""
    Nhánh thượng nguồn: {repo_type}
    Tên kỹ năng đề xuất: {skill_name}
    {duplicate_context}

    Danh sách các kỹ năng hiện có trên local: {existing_skills}
    Danh sách các workflows hiện có trên local: {existing_workflows}

    Nội dung tệp SKILL.md:
    ```markdown
    {content}
    ```

    Hãy phân tích theo ma trận: Giá trị nghiệp vụ x Độ phức tạp x Rủi ro trùng lặp (Reuse-First Gate).
    ĐẶC BIỆT LƯU Ý:
    1. Nếu kỹ năng đã tồn tại trên local hoặc trùng lặp chức năng cốt lõi với kỹ năng sẵn có, bạn nên đặt should_port = false, score thấp (ví dụ < 35) và đề xuất IGNORE hoặc chỉ rõ phương án NÂNG CẤP/TÍCH HỢP thay vì đề xuất port mới hoàn toàn.
    2. Chỉ port (should_port = true) nếu nó thực sự mang lại giá trị mới và chưa hề có trên local.
    """

    try:
        reply = ai.chat(user_prompt, system=system_prompt)

        # Strip potential markdown code fences from JSON response
        clean_reply = reply.strip()
        if clean_reply.startswith("```json"):
            clean_reply = clean_reply[7:]
        if clean_reply.endswith("```"):
            clean_reply = clean_reply[:-3]
        clean_reply = clean_reply.strip()

        return json.loads(clean_reply)
    except Exception as e:
        return {
            "should_port": True,
            "score": 75,
            "reason": f"Lỗi gọi AI Gateway: {e}. Đề xuất rà soát thủ công.",
            "actionable_steps": ["Rà soát thủ công tệp tin SKILL.md", "Port nếu cần thiết"]
        }


def append_recommendation(repo_type: str, skill_name: str, result: dict):
    """Write recommendation item to .md/port_recommendations.md."""
    try:
        if not RECOMMENDATIONS_FILE.parent.exists():
            RECOMMENDATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)

        header = f"# 📋 Upstream Porting Recommendations\n\nBáo cáo tự động đánh giá các tính năng mới từ thượng nguồn. Cập nhật ngày: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Read existing file content or start new
        content = ""
        if RECOMMENDATIONS_FILE.exists():
            content = RECOMMENDATIONS_FILE.read_text(encoding="utf-8")

        if not content.startswith("# 📋 Upstream"):
            content = header + content

        # Check existing list for dynamic status override
        existing_skills, existing_workflows = get_existing_elements()
        is_duplicate = skill_name in existing_skills or skill_name in existing_workflows

        if is_duplicate:
            status_text = "IGNORE (Đã tồn tại)"
            color = "🔴"
        elif not result.get("should_port", True):
            reason_lower = result.get("reason", "").lower()
            if "nâng cấp" in reason_lower or "tích hợp" in reason_lower or "cải tiến" in reason_lower:
                status_text = "UPGRADE/INTEGRATE"
                color = "🟡"
            else:
                status_text = "IGNORE"
                color = "🔴"
        else:
            status_text = "RECOMMEND PORT"
            color = "🟢"

        item_md = f"""
---

### {color} [{status_text}] Skill: `{skill_name}` (Score: {result.get('score', 0)}/100)
*   **Kho chứa nguồn**: `{repo_type}`
*   **Đánh giá**: {result.get('reason', 'Không có lý do chi tiết từ AI')}
*   **Các bước triển khai**:
"""
        for step in result.get("actionable_steps", []):
            item_md += f"    *   {step}\n"

        content += item_md
        RECOMMENDATIONS_FILE.write_text(content, encoding="utf-8")
        print(f"[Evaluator] Wrote suitability report for '{skill_name}' -> {status_text}")
    except Exception as e:
        print(f"[Evaluator] Error writing recommendation: {e}")


def run_mock_mode():
    """Simulate finding and evaluating mock skills for testing."""
    print("[Evaluator] Running in TEST MOCK mode...")

    mock_engineer_skill = (
        "name: ck:mock-debugger\n"
        "description: Automated breakpoint injector and step-by-step trace analyzer for debugging Python stack traces.\n"
        "category: debugging\n"
    )

    mock_marketing_skill = (
        "name: ckm:mock-funnel-optimizer\n"
        "description: Generates micro-copy variations for A/B testing on e-commerce landing pages.\n"
        "category: conversion\n"
    )

    mock_mattpocock_skill = (
        "name: /grill-with-docs\n"
        "description: Interviewing skill that helps define domain models and project context by grilling the project docs.\n"
        "category: productivity\n"
    )

    print("[Evaluator] Simulating review for 'mock-debugger' (Engineer)...")
    res1 = call_ai_evaluation("engineer", "mock-debugger", mock_engineer_skill)
    append_recommendation("engineer", "mock-debugger", res1)

    print("[Evaluator] Simulating review for 'mock-funnel-optimizer' (Marketing)...")
    res2 = call_ai_evaluation("marketing", "mock-funnel-optimizer", mock_marketing_skill)
    append_recommendation("marketing", "mock-funnel-optimizer", res2)

    print("[Evaluator] Simulating review for 'grill-with-docs' (MattPocock)...")
    res3 = call_ai_evaluation("mattpocock-skills", "grill-with-docs", mock_mattpocock_skill)
    append_recommendation("mattpocock-skills", "grill-with-docs", res3)

    print(f"\n[Evaluator] Success! Please view results in {RECOMMENDATIONS_FILE}")


def check_git_diffs(repo_path: Path, base_sha: str, head_sha: str, repo_type: str):
    """Run git diff in the specified repo to find new skills."""
    if not repo_path.exists():
        print(f"[Evaluator] Warning: Repository path '{repo_path}' not found. Skipping.")
        return

    try:
        # Run git diff
        cmd = ["git", "diff", "--name-only", base_sha, head_sha]
        res = subprocess.run(cmd, cwd=str(repo_path), capture_output=True, text=True, check=True)
        files = res.stdout.strip().splitlines()

        if repo_type == "mattpocock-skills":
            skill_pattern = re.compile(r"skills/([^/]+)/([^/]+)/SKILL\.md$")
        else:
            skill_pattern = re.compile(r"claude/skills/([^/]+)/SKILL\.md$")

        for f in files:
            match = skill_pattern.search(f)
            if match:
                if repo_type == "mattpocock-skills":
                    match.group(1)
                    skill_name = match.group(2)
                else:
                    skill_name = match.group(1)

                print(f"[Evaluator] Found modified/new skill: '{skill_name}' in upstream {repo_type}")

                # Retrieve the file contents from head SHA
                show_cmd = ["git", "show", f"{head_sha}:{f}"]
                show_res = subprocess.run(show_cmd, cwd=str(repo_path), capture_output=True, text=True, check=True)
                skill_content = show_res.stdout

                result = call_ai_evaluation(repo_type, skill_name, skill_content)
                append_recommendation(repo_type, skill_name, result)
    except subprocess.SubprocessError as e:
        print(f"[Evaluator] Git execution error in '{repo_path}': {e}")


def main():
    parser = argparse.ArgumentParser(description="CCBA Upstream Feature Porting Evaluator")
    parser.add_argument("--test-mock", action="store_true", help="Simulate a new skill check using mock data")
    parser.add_argument("--repo-path", help="Path to local upstream repo directory")
    parser.add_argument("--repo-type", choices=["engineer", "marketing", "mattpocock-skills"], help="Repository type to evaluate")
    parser.add_argument("--base", help="Base commit SHA for git diff")
    parser.add_argument("--head", help="Head commit SHA for git diff")

    args = parser.parse_args()

    if args.test_mock:
        run_mock_mode()
        sys.exit(0)

    if not args.repo_path or not args.repo_type or not args.base or not args.head:
        print("[Evaluator] Error: Missing required git diff arguments (--repo-path, --repo-type, --base, --head).")
        sys.exit(1)

    check_git_diffs(Path(args.repo_path), args.base, args.head, args.repo_type)


if __name__ == "__main__":
    main()
