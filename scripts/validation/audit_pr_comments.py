"""CCBA Platform — Pull Request Copilot Comments Fetcher.

Fetches active inline review comments and PR comments from Copilot
and prints them for the Agent to evaluate and resolve natively.
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
    walkthrough_path = Path.cwd() / "walkthrough.md"
    if walkthrough_path.exists():
        try:
            content = walkthrough_path.read_text(encoding="utf-8")
            body_snippet = comment["body"][:30]
            if body_snippet in content or str(comment["id"]) in content:
                return True
        except Exception:
            pass
    return False


def main():
    pr_number = get_current_pr_number()
    if pr_number == 0:
        print("[OK] No active Pull Request detected. Skipping.")
        sys.exit(0)

    comments = fetch_pr_comments(pr_number)
    if not comments:
        print("[OK] No comments detected.")
        sys.exit(0)

    copilot_comments = [
        c for c in comments if "copilot" in c["user"].lower() or c["user"] == "Copilot"
    ]
    if not copilot_comments:
        print("[OK] 0 comments from Copilot.")
        sys.exit(0)

    pending_comments = []
    for c in copilot_comments:
        if not check_if_resolved_in_code_or_walkthrough(c):
            pending_comments.append(c)

    if not pending_comments:
        print("[OK] All Copilot comments resolved or documented.")
        sys.exit(0)

    # Output pending comments as clean JSON for the Agent to parse natively
    print(json.dumps(pending_comments, indent=2, ensure_ascii=False))
    # Exit with code 1 to indicate there are pending comments that the Agent must evaluate and address
    sys.exit(1)


if __name__ == "__main__":
    main()
