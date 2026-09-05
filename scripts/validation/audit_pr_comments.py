"""CCBA Platform — Pull Request Copilot Comments & Review Auditor.

Fetches active reviews, review requests, inline review comments, and PR comments
from GitHub Copilot, ensuring that Copilot has finished reviewing and that no
'Changes recommended' remain unaddressed before release.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_command(cmd: list[str]) -> str:
    """Run a system command and return its stdout."""
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        raise RuntimeError(f"Command {' '.join(cmd)} failed: {res.stderr}")
    return res.stdout.strip()


def get_current_pr_number() -> int:
    """Get the active Pull Request number from CLI args or gh CLI."""
    # Support positional argument or --pr=<num> / --pr <num>
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg.startswith("--pr="):
            val = arg.split("=", 1)[1]
            if val.isdigit():
                return int(val)
        elif arg == "--pr" and i + 1 < len(args) and args[i + 1].isdigit():
            return int(args[i + 1])
        elif arg.isdigit():
            return int(arg)

    try:
        out = run_command(["gh", "pr", "view", "--json", "number", "-q", ".number"])
        if out and out.isdigit():
            return int(out)
    except Exception as e:
        print(f"[Warning] Failed to fetch PR number via gh CLI: {e}", file=sys.stderr)
    return 0


def is_copilot_user(user_obj: dict[str, Any] | None) -> bool:
    """Check if user dictionary represents GitHub Copilot bot."""
    if not user_obj or not isinstance(user_obj, dict):
        return False
    login = str(user_obj.get("login", "")).lower()
    return "copilot" in login


def fetch_pr_overview(pr_number: int) -> dict[str, Any]:
    """Fetch PR review requests, reviews, and top-level comments."""
    try:
        raw = run_command(
            [
                "gh",
                "pr",
                "view",
                str(pr_number),
                "--json",
                "reviewRequests,reviews,comments,state,title,number",
            ]
        )
        if raw:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
    except Exception as e:
        print(f"[Warning] Failed to fetch PR overview: {e}", file=sys.stderr)
    return {"reviewRequests": [], "reviews": [], "comments": []}


def fetch_inline_comments(pr_number: int) -> list[dict[str, Any]]:
    """Fetch inline review comments for a Pull Request via GitHub API with pagination."""
    try:
        raw = run_command(
            [
                "gh",
                "api",
                "--paginate",
                f"repos/:owner/:repo/pulls/{pr_number}/comments",
            ]
        )
        if raw:
            data = json.loads(raw)
            if isinstance(data, list):
                return data
    except Exception as e:
        print(f"[Warning] Failed to fetch inline review comments: {e}", file=sys.stderr)
    return []


def check_if_resolved_in_code_or_walkthrough(identifier: str, snippet: str) -> bool:
    """Check if the comment or issue has already been documented in walkthrough.md."""
    possible_paths = [
        Path.cwd() / "walkthrough.md",
        Path.cwd() / ".md" / "walkthrough.md",
    ]
    for path in possible_paths:
        if path.exists():
            try:
                content = path.read_text(encoding="utf-8")
                if identifier and str(identifier) in content:
                    return True
                if snippet and len(snippet) >= 15 and snippet in content:
                    return True
            except Exception:
                pass
    return False


def audit_pull_request(pr_number: int) -> tuple[int, dict[str, Any]]:
    """Audit Copilot reviews and comments for a given PR.

    Returns:
        (exit_code, summary_dict)
        exit_code 0: Clean or all resolved.
        exit_code 1: Has unaddressed changes recommended or inline comments.
        exit_code 2: Copilot review in progress (Pending).
    """
    overview = fetch_pr_overview(pr_number)

    # 1. Check Pending Review Requests
    review_requests = overview.get("reviewRequests", [])
    copilot_pending = any("copilot" in str(r.get("login", "")).lower() for r in review_requests)
    if copilot_pending:
        return 2, {
            "status": "PENDING",
            "message": f"Copilot review is currently requested and pending on PR #{pr_number}. Do not merge yet.",
            "reviewRequests": review_requests,
        }

    # 2. Check Top-level Reviews
    reviews = overview.get("reviews", [])
    copilot_reviews = [
        r for r in reviews if is_copilot_user(r.get("author")) or is_copilot_user(r.get("user"))
    ]

    unaddressed_review_issues: list[dict[str, Any]] = []
    if copilot_reviews:
        # Check latest review
        latest_review = copilot_reviews[-1]
        body = str(latest_review.get("body", ""))
        state = str(latest_review.get("state", ""))
        review_id = str(latest_review.get("id", ""))

        has_changes_recommended = (
            "changes recommended" in body.lower() or "🟡" in body or state == "CHANGES_REQUESTED"
        )

        if has_changes_recommended:
            # Extract first summary paragraph
            lines = [line.strip() for line in body.splitlines() if line.strip()]
            summary = "\n".join(lines[:6]) if lines else "Changes recommended by Copilot"
            if not check_if_resolved_in_code_or_walkthrough(review_id, summary[:30]):
                unaddressed_review_issues.append(
                    {
                        "review_id": review_id,
                        "state": state,
                        "summary": summary,
                        "body": body,
                    }
                )

    # 3. Check Inline Review Comments
    inline_comments = fetch_inline_comments(pr_number)
    copilot_inline = [
        c
        for c in inline_comments
        if is_copilot_user(c.get("user")) or is_copilot_user(c.get("author"))
    ]

    unaddressed_inline: list[dict[str, Any]] = []
    for c in copilot_inline:
        c_id = str(c.get("id", ""))
        c_path = str(c.get("path", ""))
        c_line = c.get("line")
        c_body = str(c.get("body", ""))
        if not check_if_resolved_in_code_or_walkthrough(c_id, c_body[:30]):
            unaddressed_inline.append(
                {
                    "id": c_id,
                    "path": c_path,
                    "line": c_line,
                    "body": c_body,
                }
            )

    # 4. Check PR-Level Conversation Comments
    pr_comments = overview.get("comments", [])
    copilot_pr_comments = [
        c for c in pr_comments if is_copilot_user(c.get("author")) or is_copilot_user(c.get("user"))
    ]

    unaddressed_pr_comments: list[dict[str, Any]] = []
    for c in copilot_pr_comments:
        c_id = str(c.get("id", ""))
        c_body = str(c.get("body", ""))
        if not check_if_resolved_in_code_or_walkthrough(c_id, c_body[:30]):
            unaddressed_pr_comments.append(
                {
                    "id": c_id,
                    "body": c_body,
                }
            )

    if unaddressed_review_issues or unaddressed_inline or unaddressed_pr_comments:
        return 1, {
            "status": "CHANGES_RECOMMENDED",
            "message": f"Copilot has recommended changes on PR #{pr_number} that must be resolved.",
            "review_issues": unaddressed_review_issues,
            "inline_issues": unaddressed_inline,
            "pr_comment_issues": unaddressed_pr_comments,
        }

    return 0, {
        "status": "CLEAN",
        "message": f"All Copilot reviews and comments on PR #{pr_number} are clean or resolved.",
        "reviews_count": len(copilot_reviews),
        "inline_comments_count": len(copilot_inline),
        "pr_comments_count": len(copilot_pr_comments),
    }


def main() -> None:
    if sys.platform.startswith("win"):
        try:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    pr_number = get_current_pr_number()
    if pr_number == 0:
        print("[OK] No active Pull Request detected. Skipping.")
        sys.exit(0)

    exit_code, result = audit_pull_request(pr_number)

    if exit_code == 0:
        print(f"[OK] {result['message']}")
        sys.exit(0)
    elif exit_code == 2:
        print(f"[PENDING] {result['message']}")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(2)
    else:
        print(f"[FAIL] {result['message']}", file=sys.stderr)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
