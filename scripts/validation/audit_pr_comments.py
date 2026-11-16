"""CCBA Platform — Pull Request Copilot Comments & Review Auditor.

Fetches active reviews, review requests, inline review comments, and PR comments
from GitHub Copilot, ensuring that Copilot has finished reviewing and that no
'Changes recommended' remain unaddressed before release. Supports explicit --repo
targeting for cross-repository invocation and fails closed on API/CLI errors.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

_REPO_PATTERN = re.compile(r"^[\w.-]+/[\w.-]+$")


def run_command(cmd: list[str]) -> str:
    """Run a system command and return its stdout, raising RuntimeError on failure."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Command {' '.join(cmd)} failed: {exc}") from exc
    if res.returncode != 0:
        raise RuntimeError(f"Command {' '.join(cmd)} failed: {res.stderr.strip()}")
    return res.stdout.strip()


def _parse_positive_int(raw: str, flag_name: str) -> int:
    """Parse a strictly positive integer CLI value or raise ValueError."""
    if not raw.isdigit() or int(raw) <= 0:
        raise ValueError(f"Invalid {flag_name} value {raw!r}: expected a positive integer.")
    return int(raw)


def _validate_repo_slug(raw: str) -> str:
    """Validate GitHub owner/repo slug syntax or raise ValueError."""
    cleaned = raw.strip()
    if not cleaned or cleaned.startswith("-") or not _REPO_PATTERN.fullmatch(cleaned):
        raise ValueError(f"Invalid --repo value {raw!r}: expected 'owner/repo'.")
    return cleaned


def _assign_pr_number(current: int | None, candidate: int) -> int:
    """Assign PR number ensuring no conflicting values are passed on the CLI."""
    if current is not None and current != candidate:
        raise ValueError(f"Conflicting PR numbers supplied: {current} vs {candidate}.")
    return candidate


def _extract_flag_value(args: Sequence[str], idx: int, arg: str, flag: str) -> tuple[str, int]:
    """Extract flag value from '--flag=val' or '--flag val' forms."""
    if arg.startswith(f"{flag}="):
        return arg.split("=", 1)[1], idx + 1
    if idx + 1 >= len(args):
        raise ValueError(f"Option {flag} requires a value.")
    return args[idx + 1], idx + 2


def parse_cli_args(argv: Sequence[str] | None = None) -> tuple[int | None, str | None]:
    """Parse --pr / positional PR number and optional --repo / -R slug from CLI arguments."""
    args = list(sys.argv[1:] if argv is None else argv)
    pr_number: int | None = None
    repo: str | None = None
    idx = 0
    while idx < len(args):
        arg = args[idx]
        if arg == "--pr" or arg.startswith("--pr="):
            val, idx = _extract_flag_value(args, idx, arg, "--pr")
            pr_number = _assign_pr_number(pr_number, _parse_positive_int(val, "--pr"))
        elif arg in ("--repo", "-R") or arg.startswith(("--repo=", "-R=")):
            flag = "--repo" if arg.startswith("--repo") else "-R"
            val, idx = _extract_flag_value(args, idx, arg, flag)
            repo = _validate_repo_slug(val)
        elif arg.startswith("-"):
            raise ValueError(f"Unknown option: {arg}")
        else:
            pr_number = _assign_pr_number(pr_number, _parse_positive_int(arg, "PR number"))
            idx += 1
    return pr_number, repo


def get_current_pr_number(repo: str | None = None) -> int:
    """Get the active PR number from CLI args or gh CLI (0 only when no PR exists locally)."""
    pr_num, cli_repo = parse_cli_args()
    effective_repo = repo if repo is not None else cli_repo
    if pr_num is not None:
        return pr_num

    cmd = ["gh", "pr", "view"]
    if effective_repo:
        cmd.extend(["--repo", effective_repo])
    cmd.extend(["--json", "number", "-q", ".number"])
    try:
        out = run_command(cmd)
    except RuntimeError as exc:
        if not effective_repo and "no pull requests found" in str(exc).lower():
            return 0
        raise
    if out.isdigit() and int(out) > 0:
        return int(out)
    raise RuntimeError(f"Unexpected gh pr view output: {out!r}")


def is_copilot_user(user_obj: dict[str, Any] | None) -> bool:
    """Check if user dictionary represents GitHub Copilot bot."""
    if not user_obj or not isinstance(user_obj, dict):
        return False
    login = str(user_obj.get("login", "")).lower()
    return "copilot" in login


def _decode_paginated_json_array(raw: str) -> list[dict[str, Any]]:
    """Decode a single JSON array or concatenated gh --paginate JSON arrays."""
    text = raw.strip()
    if not text:
        raise RuntimeError("Empty JSON response from gh api")
    decoder = json.JSONDecoder()
    items: list[dict[str, Any]] = []
    idx = 0
    while idx < len(text):
        try:
            page, next_idx = decoder.raw_decode(text, idx)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON from gh api: {exc}") from exc
        if not isinstance(page, list) or not all(isinstance(entry, dict) for entry in page):
            raise RuntimeError("Unexpected non-list or malformed entry in gh api response")
        items.extend(page)
        idx = next_idx
        while idx < len(text) and text[idx].isspace():
            idx += 1
    return items


def fetch_pr_overview(pr_number: int, repo: str | None = None) -> dict[str, Any]:
    """Fetch PR review requests, reviews, and top-level comments (fail-closed)."""
    cmd = ["gh", "pr", "view", str(pr_number)]
    if repo:
        cmd.extend(["--repo", repo])
    cmd.extend(["--json", "reviewRequests,reviews,comments,state,title,number"])
    raw = run_command(cmd)
    if not raw:
        raise RuntimeError("Empty JSON response from gh pr view")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON from gh pr view: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("Unexpected non-object JSON from gh pr view")
    return data


def fetch_inline_comments(pr_number: int, repo: str | None = None) -> list[dict[str, Any]]:
    """Fetch inline review comments for a Pull Request via GitHub API with pagination."""
    endpoint = (
        f"repos/{repo}/pulls/{pr_number}/comments"
        if repo
        else f"repos/:owner/:repo/pulls/{pr_number}/comments"
    )
    raw = run_command(["gh", "api", "--paginate", endpoint])
    return _decode_paginated_json_array(raw)


def check_if_resolved_in_code_or_walkthrough(identifier: str, snippet: str) -> bool:
    """Check if the comment or issue has already been documented in walkthrough.md."""
    possible_paths = [
        Path.cwd() / "walkthrough.md",
        Path.cwd() / ".md" / "walkthrough.md",
        Path.cwd() / ".md" / "knowledge" / "reports" / "walkthrough.md",
    ]
    for path in possible_paths:
        if path.exists():
            try:
                content = path.read_text(encoding="utf-8")
                if identifier and str(identifier) in content:
                    return True
                if snippet and len(snippet) >= 15 and snippet in content:
                    return True
            except OSError:
                pass
    return False


def _collect_unaddressed_reviews(reviews: Any) -> tuple[list[dict[str, Any]], int]:
    """Collect unresolved Copilot top-level review recommendations."""
    if not isinstance(reviews, list):
        return [], 0
    copilot_reviews = [
        r
        for r in reviews
        if isinstance(r, dict)
        and (is_copilot_user(r.get("author")) or is_copilot_user(r.get("user")))
    ]
    issues: list[dict[str, Any]] = []
    if copilot_reviews:
        latest_review = copilot_reviews[-1]
        body = str(latest_review.get("body", ""))
        state = str(latest_review.get("state", ""))
        review_id = str(latest_review.get("id", ""))
        has_rec = (
            "changes recommended" in body.lower() or "🟡" in body or state == "CHANGES_REQUESTED"
        )
        if has_rec:
            lines = [line.strip() for line in body.splitlines() if line.strip()]
            summary = "\n".join(lines[:6]) if lines else "Changes recommended by Copilot"
            if not check_if_resolved_in_code_or_walkthrough(review_id, summary[:30]):
                issues.append(
                    {"review_id": review_id, "state": state, "summary": summary, "body": body}
                )
    return issues, len(copilot_reviews)


def _collect_unaddressed_inline_comments(inline_comments: Any) -> tuple[list[dict[str, Any]], int]:
    """Collect unresolved Copilot inline review comments."""
    if not isinstance(inline_comments, list):
        return [], 0
    copilot_inline = [
        c
        for c in inline_comments
        if isinstance(c, dict)
        and (is_copilot_user(c.get("user")) or is_copilot_user(c.get("author")))
    ]
    issues: list[dict[str, Any]] = []
    for c in copilot_inline:
        c_id = str(c.get("id", ""))
        c_body = str(c.get("body", ""))
        if not check_if_resolved_in_code_or_walkthrough(c_id, c_body[:30]):
            issues.append(
                {
                    "id": c_id,
                    "path": str(c.get("path", "")),
                    "line": c.get("line"),
                    "body": c_body,
                }
            )
    return issues, len(copilot_inline)


def _collect_unaddressed_pr_comments(pr_comments: Any) -> tuple[list[dict[str, Any]], int]:
    """Collect unresolved Copilot top-level conversation comments."""
    if not isinstance(pr_comments, list):
        return [], 0
    copilot_comments = [
        c
        for c in pr_comments
        if isinstance(c, dict)
        and (is_copilot_user(c.get("author")) or is_copilot_user(c.get("user")))
    ]
    issues: list[dict[str, Any]] = []
    for c in copilot_comments:
        c_id = str(c.get("id", ""))
        c_body = str(c.get("body", ""))
        if not check_if_resolved_in_code_or_walkthrough(c_id, c_body[:30]):
            issues.append({"id": c_id, "body": c_body})
    return issues, len(copilot_comments)


def _fetch_pr_audit_inputs(
    pr_number: int,
    repo: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]] | None]:
    """Fetch PR overview and (unless Copilot review is pending) inline comments."""
    overview = (
        fetch_pr_overview(pr_number) if repo is None else fetch_pr_overview(pr_number, repo=repo)
    )
    review_requests = overview.get("reviewRequests", [])
    if isinstance(review_requests, list) and any(
        "copilot" in str(r.get("login", "")).lower() for r in review_requests if isinstance(r, dict)
    ):
        return overview, None
    inline_comments = (
        fetch_inline_comments(pr_number)
        if repo is None
        else fetch_inline_comments(pr_number, repo=repo)
    )
    return overview, inline_comments


def audit_pull_request(
    pr_number: int,
    repo: str | None = None,
) -> tuple[int, dict[str, Any]]:
    """Audit Copilot reviews and comments for a given PR (fail-closed on fetch errors).

    Returns:
        (exit_code, summary_dict) where 0=CLEAN, 1=CHANGES_RECOMMENDED/FETCH_ERROR, 2=PENDING.
    """
    if pr_number <= 0:
        return 1, {"status": "FETCH_ERROR", "message": f"Invalid PR number: {pr_number}"}
    try:
        overview, inline_comments = _fetch_pr_audit_inputs(pr_number, repo=repo)
    except (RuntimeError, ValueError) as exc:
        return 1, {"status": "FETCH_ERROR", "message": str(exc)}

    if inline_comments is None:
        return 2, {
            "status": "PENDING",
            "message": f"Copilot review is currently requested and pending on PR #{pr_number}. Do not merge yet.",
            "reviewRequests": overview.get("reviewRequests", []),
        }

    review_issues, rev_cnt = _collect_unaddressed_reviews(overview.get("reviews", []))
    inline_issues, inl_cnt = _collect_unaddressed_inline_comments(inline_comments)
    pr_comment_issues, prc_cnt = _collect_unaddressed_pr_comments(overview.get("comments", []))
    if review_issues or inline_issues or pr_comment_issues:
        return 1, {
            "status": "CHANGES_RECOMMENDED",
            "message": f"Copilot has recommended changes on PR #{pr_number} that must be resolved.",
            "review_issues": review_issues,
            "inline_issues": inline_issues,
            "pr_comment_issues": pr_comment_issues,
        }
    return 0, {
        "status": "CLEAN",
        "message": f"All Copilot reviews and comments on PR #{pr_number} are clean or resolved.",
        "reviews_count": rev_cnt,
        "inline_comments_count": inl_cnt,
        "pr_comments_count": prc_cnt,
    }


def _configure_windows_utf8_stdio() -> None:
    """Reconfigure stdout/stderr streams to UTF-8 on Windows hosts."""
    if not sys.platform.startswith("win"):
        return
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8")
            except OSError:
                pass


def main() -> None:
    """CLI entrypoint for PR Copilot comment and review auditing."""
    _configure_windows_utf8_stdio()
    try:
        _, cli_repo = parse_cli_args()
        pr_number = get_current_pr_number(repo=cli_repo)
    except (RuntimeError, ValueError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        sys.exit(1)

    if pr_number == 0:
        print("[OK] No active Pull Request detected. Skipping.")
        sys.exit(0)

    exit_code, result = (
        audit_pull_request(pr_number)
        if cli_repo is None
        else audit_pull_request(pr_number, repo=cli_repo)
    )
    if exit_code == 0:
        print(f"[OK] {result['message']}")
        sys.exit(0)
    if exit_code == 2:
        print(f"[PENDING] {result['message']}")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(2)
    print(f"[FAIL] {result['message']}", file=sys.stderr)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(1)


if __name__ == "__main__":
    main()
