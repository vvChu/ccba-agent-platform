"""CCBA Platform — Pull Request AI Reviewer Comments & Review Auditor.

Fetches active reviews, review requests, inline review comments, and PR comments
from automated AI reviewers (CodeRabbit and GitHub Copilot), ensuring no unresolved
actionable changes remain before release. Supports explicit --repo targeting, warns on
0 AI reviews (NO_AI_REVIEW) while keeping exit 0 by default (exit 3 with --require-review),
and fails closed on API/CLI errors.
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
_ACTIONABLE_CODERABBIT_RE = re.compile(r"actionable comments posted:\s*[1-9]\d*", re.IGNORECASE)


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


def _parse_cli_tokens(
    argv: Sequence[str] | None,
    *,
    allow_require_review: bool,
) -> tuple[int | None, str | None, bool]:
    """Parse CLI tokens with optional --require-review flag (fail-closed)."""
    args = list(sys.argv[1:] if argv is None else argv)
    pr_number: int | None = None
    repo: str | None = None
    require_review = False
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
        elif arg == "--require-review" and allow_require_review:
            require_review = True
            idx += 1
        elif arg.startswith("-"):
            raise ValueError(f"Unknown option: {arg}")
        else:
            pr_number = _assign_pr_number(pr_number, _parse_positive_int(arg, "PR number"))
            idx += 1
    return pr_number, repo, require_review


def parse_cli_options(argv: Sequence[str] | None = None) -> tuple[int | None, str | None, bool]:
    """Parse --pr / positional PR number, --repo / -R slug, and --require-review flag."""
    return _parse_cli_tokens(argv, allow_require_review=True)


def parse_cli_args(argv: Sequence[str] | None = None) -> tuple[int | None, str | None]:
    """Parse --pr / positional PR number and optional --repo / -R slug from CLI arguments."""
    pr_number, repo, _ = _parse_cli_tokens(argv, allow_require_review=False)
    return pr_number, repo


def get_current_pr_number(repo: str | None = None, pr_number: int | None = None) -> int:
    """Get the active PR number from args/CLI or gh CLI (0 only when no PR exists locally)."""
    if pr_number is not None:
        return pr_number
    pr_num, cli_repo, _ = parse_cli_options()
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


def is_coderabbit_user(user_obj: dict[str, Any] | None) -> bool:
    """Check if user dictionary represents CodeRabbit bot."""
    if not user_obj or not isinstance(user_obj, dict):
        return False
    login = str(user_obj.get("login", "")).lower()
    return "coderabbit" in login


def is_ai_reviewer_user(user_obj: dict[str, Any] | None) -> bool:
    """Check if user dictionary represents any supported AI PR reviewer bot."""
    return is_copilot_user(user_obj) or is_coderabbit_user(user_obj)


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


def _extract_ai_user(entry: dict[str, Any]) -> dict[str, Any] | None:
    """Return author/user dict if it belongs to a supported AI reviewer, else None."""
    for key in ("author", "user"):
        candidate = entry.get(key)
        if isinstance(candidate, dict) and is_ai_reviewer_user(candidate):
            return candidate
    return None


def _has_coderabbit_actionable(body: str, state: str = "") -> bool:
    """Return True if CodeRabbit review/comment body or state signals unresolved items."""
    return state == "CHANGES_REQUESTED" or bool(_ACTIONABLE_CODERABBIT_RE.search(body))


def _is_benign_coderabbit_summary(body: str, state: str = "") -> bool:
    """Return True only for benign CodeRabbit walkthrough, status, or command-ack comments."""
    if _has_coderabbit_actionable(body, state):
        return False
    lowered = body.lower()
    if (
        "auto-generated comment: summarize by coderabbit.ai" in lowered
        or "<!-- walkthrough_start -->" in lowered
        or "auto-generated comment by coderabbit for review status" in lowered
    ):
        return True
    return (
        "auto-generated reply by coderabbit" in lowered
        and "<!-- coderabbit review command invocation:" in lowered
    )


def _review_has_actionable_changes(review: dict[str, Any], user_obj: dict[str, Any] | None) -> bool:
    """Determine whether an AI reviewer top-level review requires action."""
    body = str(review.get("body", ""))
    state = str(review.get("state", ""))
    if is_coderabbit_user(user_obj):
        return _has_coderabbit_actionable(body, state)
    return "changes recommended" in body.lower() or "🟡" in body or state == "CHANGES_REQUESTED"


def _collect_unaddressed_reviews(reviews: Any) -> tuple[list[dict[str, Any]], int]:
    """Collect unresolved AI reviewer top-level review recommendations."""
    if not isinstance(reviews, list):
        return [], 0
    ai_reviews = [r for r in reviews if isinstance(r, dict) and _extract_ai_user(r) is not None]
    latest_by_bot: dict[str, tuple[dict[str, Any], dict[str, Any] | None]] = {}
    for rev in ai_reviews:
        user_obj = _extract_ai_user(rev)
        login_key = str((user_obj or {}).get("login", "")).lower()
        latest_by_bot[login_key] = (rev, user_obj)
    issues: list[dict[str, Any]] = []
    for latest_review, user_obj in latest_by_bot.values():
        if not _review_has_actionable_changes(latest_review, user_obj):
            continue
        body = str(latest_review.get("body", ""))
        state = str(latest_review.get("state", ""))
        review_id = str(latest_review.get("id", ""))
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        summary = "\n".join(lines[:6]) if lines else "Changes recommended by AI reviewer"
        if not check_if_resolved_in_code_or_walkthrough(review_id, summary[:30]):
            issues.append(
                {"review_id": review_id, "state": state, "summary": summary, "body": body}
            )
    return issues, len(ai_reviews)


def _collect_unaddressed_inline_comments(inline_comments: Any) -> tuple[list[dict[str, Any]], int]:
    """Collect unresolved AI reviewer inline review comments."""
    if not isinstance(inline_comments, list):
        return [], 0
    ai_inline = [
        c for c in inline_comments if isinstance(c, dict) and _extract_ai_user(c) is not None
    ]
    issues: list[dict[str, Any]] = []
    for c in ai_inline:
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
    return issues, len(ai_inline)


def _collect_unaddressed_pr_comments(pr_comments: Any) -> tuple[list[dict[str, Any]], int]:
    """Collect unresolved AI reviewer top-level conversation comments."""
    if not isinstance(pr_comments, list):
        return [], 0
    ai_comments = [
        c for c in pr_comments if isinstance(c, dict) and _extract_ai_user(c) is not None
    ]
    issues: list[dict[str, Any]] = []
    for c in ai_comments:
        user_obj = _extract_ai_user(c)
        c_id = str(c.get("id", ""))
        c_body = str(c.get("body", ""))
        if is_coderabbit_user(user_obj) and _is_benign_coderabbit_summary(c_body):
            continue
        if not check_if_resolved_in_code_or_walkthrough(c_id, c_body[:30]):
            issues.append({"id": c_id, "body": c_body})
    return issues, len(ai_comments)


def _fetch_pr_audit_inputs(
    pr_number: int,
    repo: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]] | None]:
    """Fetch PR overview and (unless an AI review request is pending) inline comments."""
    overview = (
        fetch_pr_overview(pr_number) if repo is None else fetch_pr_overview(pr_number, repo=repo)
    )
    review_requests = overview.get("reviewRequests", [])
    if isinstance(review_requests, list) and any(
        is_ai_reviewer_user(r) for r in review_requests if isinstance(r, dict)
    ):
        return overview, None
    inline_comments = (
        fetch_inline_comments(pr_number)
        if repo is None
        else fetch_inline_comments(pr_number, repo=repo)
    )
    return overview, inline_comments


def _build_zero_issue_result(
    pr_number: int,
    rev_cnt: int,
    inl_cnt: int,
    prc_cnt: int,
    require_review: bool,
) -> tuple[int, dict[str, Any]]:
    """Build CLEAN or NO_AI_REVIEW payload when zero unresolved issues remain."""
    if rev_cnt == 0 and inl_cnt == 0 and prc_cnt == 0:
        return (3 if require_review else 0), {
            "status": "NO_AI_REVIEW",
            "message": (
                f"No AI reviewer (CodeRabbit/Copilot) review or comment found on PR #{pr_number} "
                "(0 reviews). Verify CodeRabbit App installation or use Grok code_review if private."
            ),
            "reviews_count": 0,
            "inline_comments_count": 0,
            "pr_comments_count": 0,
        }
    return 0, {
        "status": "CLEAN",
        "message": f"All AI reviewer reviews and comments on PR #{pr_number} are clean or resolved.",
        "reviews_count": rev_cnt,
        "inline_comments_count": inl_cnt,
        "pr_comments_count": prc_cnt,
    }


def audit_pull_request(
    pr_number: int,
    repo: str | None = None,
    *,
    require_review: bool = False,
) -> tuple[int, dict[str, Any]]:
    """Audit AI reviewer reviews and comments for a given PR (fail-closed on fetch errors).

    Returns:
        (exit_code, summary_dict) where 0=CLEAN or advisory NO_AI_REVIEW,
        1=CHANGES_RECOMMENDED/FETCH_ERROR, 2=PENDING, 3=NO_AI_REVIEW with --require-review.
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
            "message": f"AI review is currently requested and pending on PR #{pr_number}. Do not merge yet.",
            "reviewRequests": overview.get("reviewRequests", []),
        }

    review_issues, rev_cnt = _collect_unaddressed_reviews(overview.get("reviews", []))
    inline_issues, inl_cnt = _collect_unaddressed_inline_comments(inline_comments)
    pr_comment_issues, prc_cnt = _collect_unaddressed_pr_comments(overview.get("comments", []))
    if review_issues or inline_issues or pr_comment_issues:
        return 1, {
            "status": "CHANGES_RECOMMENDED",
            "message": f"AI reviewer has recommended changes on PR #{pr_number} that must be resolved.",
            "review_issues": review_issues,
            "inline_issues": inline_issues,
            "pr_comment_issues": pr_comment_issues,
        }
    return _build_zero_issue_result(pr_number, rev_cnt, inl_cnt, prc_cnt, require_review)


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


def _emit_audit_output(exit_code: int, result: dict[str, Any]) -> None:
    """Emit structured status output and exit with the canonical exit code."""
    if result.get("status") == "NO_AI_REVIEW":
        print(f"[WARN] {result['message']}", file=sys.stderr)
        sys.exit(exit_code)
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


def main() -> None:
    """CLI entrypoint for PR AI reviewer comment and review auditing."""
    _configure_windows_utf8_stdio()
    try:
        pr_num, cli_repo, require_review = parse_cli_options()
        pr_number = get_current_pr_number(repo=cli_repo, pr_number=pr_num)
    except (RuntimeError, ValueError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        sys.exit(1)

    if pr_number == 0:
        print("[OK] No active Pull Request detected. Skipping.")
        sys.exit(0)

    exit_code, result = (
        audit_pull_request(pr_number, require_review=require_review)
        if cli_repo is None
        else audit_pull_request(pr_number, repo=cli_repo, require_review=require_review)
    )
    _emit_audit_output(exit_code, result)


if __name__ == "__main__":
    main()
