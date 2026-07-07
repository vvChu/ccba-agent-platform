"""CCBA Platform — Pull Request Copilot Comments Auditor.

Automatically fetches PR inline and review comments, classifies them using ccba-ai,
and blocks merges if there are pending valid comments that need fixes.
"""

import json
import subprocess
import sys
from pathlib import Path

# Setup console encoding for Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def run_command(cmd: list[str]) -> str:
    """Run a system command and return its stdout."""
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        raise RuntimeError(f"Command {' '.join(cmd)} failed: {res.stderr}")
    return res.stdout.strip()


def get_current_pr_number() -> int:
    """Get the active Pull Request number for the current branch using gh CLI."""
    try:
        out = run_command(["gh", "pr", "view", "--json", "number", "-q", ".number"])
        if out and out.isdigit():
            return int(out)
    except Exception as e:
        print(f"[Warning] Failed to fetch PR number via gh CLI: {e}")
    return 0


def fetch_pr_comments(pr_number: int) -> list[dict]:
    """Fetch inline review comments for a Pull Request."""
    try:
        raw = run_command(
            [
                "gh",
                "api",
                f"repos/vvChu/ccba-agent-platform/pulls/{pr_number}/comments",
                "--jq",
                ".[] | {id: .id, path: .path, line: .line, body: .body, user: .user.login}",
            ]
        )
        if not raw:
            return []
        # gh api output with jq is JSON lines
        comments = []
        for line in raw.splitlines():
            if line.strip():
                comments.append(json.loads(line))
        return comments
    except Exception as e:
        print(f"[Error] Failed to fetch comments: {e}")
        return []


def check_if_resolved_in_code_or_walkthrough(comment: dict) -> bool:
    """Check if the comment has already been resolved or documented in walkthrough.md."""
    # Read walkthrough.md
    walkthrough_path = Path.cwd() / "walkthrough.md"
    if walkthrough_path.exists():
        try:
            content = walkthrough_path.read_text(encoding="utf-8")
            # If the comment ID or key words from the body are in walkthrough.md, consider it documented/resolved
            body_snippet = comment["body"][:30]
            if body_snippet in content or str(comment["id"]) in content:
                return True
        except Exception:
            pass
    return False


def main():
    print("=== CCBA PR COPILOT COMMENTS AUDITOR ===")

    pr_number = get_current_pr_number()
    if pr_number == 0:
        print("[OK] No active Pull Request detected for this branch. Skipping audit.")
        sys.exit(0)

    print(f"Auditing PR #{pr_number}...")
    comments = fetch_pr_comments(pr_number)

    if not comments:
        print("[OK] No Copilot or reviewer comments detected. All clear to merge!")
        sys.exit(0)

    copilot_comments = [
        c for c in comments if "copilot" in c["user"].lower() or c["user"] == "Copilot"
    ]
    if not copilot_comments:
        print(
            f"[OK] Found {len(comments)} comments from human reviewers, but 0 from Copilot. All clear."
        )
        sys.exit(0)

    print(f"Found {len(copilot_comments)} comment(s) from Copilot:")

    pending_valid = []
    resolved_or_bypassed = []

    # Import ccba-ai SDK to run classification
    try:
        from ccba_ai import ai
    except ImportError:
        print("[Warning] ccba-ai SDK not installed. Skipping automatic LLM evaluation.")
        ai = None

    for idx, c in enumerate(copilot_comments, 1):
        print(f"\n[{idx}] File: {c['path']} (Line {c['line']})")
        print(f"    Comment: {c['body']}")

        # Step 1: Check if already resolved/documented locally
        if check_if_resolved_in_code_or_walkthrough(c):
            print("    -> [RESOLVED/BYPASSED] Already documented in walkthrough.md.")
            resolved_or_bypassed.append(c)
            continue

        if ai:
            # Step 2: Use LLM to classify if comment is Valid (reasonable) or Invalid (unreasonable)
            prompt = (
                "Bạn là một Senior Code Reviewer. Hãy đánh giá góp ý (review comment) dưới đây của Copilot "
                "đối với một tệp tin nguồn trong dự án. Hãy xác định góp ý này là hợp lý (VALID) hay không hợp lý (INVALID).\n\n"
                f"TỆP TIN: {c['path']} (Dòng {c['line']})\n"
                f"GÓP Ý CỦA COPILOT: {c['body']}\n\n"
                "QUY TẮC PHÂN LOẠI:\n"
                "- Chọn VALID nếu góp ý chỉ ra lỗi logic, rò rỉ bộ nhớ, thiếu check file exists, lỗi chính tả, hoặc vấn đề bảo mật rõ ràng.\n"
                "- Chọn INVALID nếu góp ý khuyên dùng các thư viện/phương thức không tương thích với phiên bản hiện tại trong dự án, "
                "hoặc đề xuất các thay đổi đi ngược lại yêu cầu thiết kế gốc.\n\n"
                "BẮT BUỘC TRẢ VỀ JSON dạng:\n"
                "{\n"
                '  "classification": "VALID" hoặc "INVALID",\n'
                '  "reason": "Giải thích ngắn gọn bằng tiếng Việt lý do hợp lý hay không"\n'
                "}\n"
                "Chỉ xuất chuỗi JSON sạch, không giải thích thêm, không bọc codeblock."
            )
            try:
                res = ai.chat(prompt, model="gemini-2.5-flash", temperature=0.1)
                data = json.loads(res.strip())
                classification = data.get("classification", "VALID")
                reason = data.get("reason", "")
                print(f"    -> [LLM Judgement]: {classification} - {reason}")

                if classification == "VALID":
                    pending_valid.append(c)
                else:
                    resolved_or_bypassed.append(c)
            except Exception as eval_err:
                print(f"    -> [LLM Error]: Failed to evaluate ({eval_err}). Default to VALID.")
                pending_valid.append(c)
        else:
            # Default to valid if SDK is missing
            pending_valid.append(c)

    print("\n=== AUDIT SUMMARY ===")
    print(f"- Resolved/Bypassed: {len(resolved_or_bypassed)}")
    print(f"- Pending Valid: {len(pending_valid)}")

    if pending_valid:
        print("\n[BLOCKED] There are pending valid comments from Copilot that need to be resolved.")
        print(
            "Please fix the code or document the bypassed comments in walkthrough.md, then run again."
        )
        sys.exit(1)
    else:
        print("\n[OK] All Copilot comments have been evaluated and resolved/bypassed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
