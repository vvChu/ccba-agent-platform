#!/usr/bin/env python3
"""Deterministic Remote Repository Protection CLI Tool.

Applies GitHub branch rulesets, Dependabot security fixes, vulnerability alerts,
and secret scanning/push protection to remote GitHub repositories via GitHub CLI (gh).
Complies with CCBA-SOP-SEC-001, ADR-0057, and ADR-0058.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def check_gh_cli() -> bool:
    """Checks if the GitHub CLI (gh) is installed on PATH."""
    return shutil.which("gh") is not None


def check_gh_auth() -> bool:
    """Checks if the user is authenticated with GitHub CLI."""
    try:
        res = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            check=False,
        )
        return res.returncode == 0
    except Exception:
        return False


def resolve_target_repo(repo_arg: str | None = None, cwd: Path | None = None) -> str | None:
    """Resolves target repository in 'owner/repo' format from arg or git remote origin."""
    if repo_arg and repo_arg.strip():
        clean = repo_arg.strip()
        if "/" in clean and not clean.startswith("http") and not clean.startswith("git@"):
            return clean

    # Detect from local git origin remote
    try:
        res = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=str(cwd or Path.cwd()),
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            url = res.stdout.strip()
            # Match git@github.com:owner/repo.git or https://github.com/owner/repo(.git)
            match = re.search(
                r"(?:git@github\.com:|https?://github\.com/)([\w.-]+)/([\w.-]+?)(?:\.git)?$", url
            )
            if match:
                return f"{match.group(1)}/{match.group(2)}"
    except Exception:
        pass

    return None


def check_admin_permission(repo: str) -> bool:
    """Checks whether the authenticated user has admin rights on the repository."""
    try:
        res = subprocess.run(
            ["gh", "api", f"repos/{repo}", "--jq", ".permissions.admin"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            return res.stdout.strip().lower() == "true"
    except Exception:
        pass
    return False


def get_default_branch(repo: str) -> str:
    """Fetches default branch of repository via GitHub API, falling back to 'main'."""
    try:
        res = subprocess.run(
            ["gh", "api", f"repos/{repo}", "--jq", ".default_branch"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return "main"


def enable_vulnerability_alerts(repo: str, dry_run: bool = False) -> bool:
    """Enables Dependabot alerts and automated security fixes."""
    if dry_run:
        print(f"[Dependabot] [DRY-RUN] Would enable vulnerability alerts on {repo}")
        print(f"[Dependabot] [DRY-RUN] Would enable automated security fixes on {repo}")
        return True

    print(f"[Dependabot] Enabling vulnerability alerts on {repo}...")
    res1 = subprocess.run(
        ["gh", "api", "-X", "PUT", f"repos/{repo}/vulnerability-alerts"],
        capture_output=True,
        text=True,
        check=False,
    )

    print(f"[Dependabot] Enabling automated security fixes on {repo}...")
    res2 = subprocess.run(
        ["gh", "api", "-X", "PUT", f"repos/{repo}/automated-security-fixes"],
        capture_output=True,
        text=True,
        check=False,
    )

    success = (res1.returncode == 0) and (res2.returncode == 0)
    if success:
        print("  - Vulnerability alerts & Dependabot fixes: ✅ Enabled")
    else:
        print(
            f"  - Vulnerability alerts warning: {res1.stderr.strip() or res2.stderr.strip()}",
            file=sys.stderr,
        )
    return success


def enable_secret_scanning(repo: str, dry_run: bool = False) -> bool:
    """Enables secret scanning and push protection with graceful GHAS fallback."""
    payload = {
        "security_and_analysis": {
            "secret_scanning": {"status": "enabled"},
            "secret_scanning_push_protection": {"status": "enabled"},
        }
    }

    if dry_run:
        print(f"[Secret Scanning] [DRY-RUN] Would enable secret scanning on {repo}:")
        print(json.dumps(payload, indent=2))
        return True

    print(f"[Secret Scanning] Configuring secret scanning and push protection on {repo}...")
    res = subprocess.run(
        ["gh", "api", "-X", "PATCH", f"repos/{repo}", "--input", "-"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )

    if res.returncode == 0:
        print("  - Secret scanning & Push protection: ✅ Enabled")
        return True

    # Graceful fallback: Private repos without GHAS license return 422 or 403
    print(
        f"  - ⚠️ [WARNING] Secret scanning could not be enabled ({res.stderr.strip()}).\n"
        "    Note: Private repositories require GitHub Advanced Security (GHAS). Skipping.",
        file=sys.stderr,
    )
    return False


def get_ruleset_id_by_name(repo: str, ruleset_name: str) -> int | None:
    """Finds an existing ruleset ID by its exact display name."""
    try:
        res = subprocess.run(
            ["gh", "api", f"repos/{repo}/rulesets"],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            rulesets = json.loads(res.stdout)
            if isinstance(rulesets, list):
                for r in rulesets:
                    if r.get("name") == ruleset_name:
                        return int(r["id"])
    except Exception:
        pass
    return None


def build_ruleset_payload(
    branch: str,
    checks: list[str] | None = None,
    approvals: int = 0,
    ruleset_name: str = "Protect Main Branch",
) -> dict[str, Any]:
    """Builds a complete, valid GitHub Ruleset API payload.

    Omits 'required_status_checks' when checks list is empty to prevent HTTP 422 Unprocessable Entity.
    """
    rules: list[dict[str, Any]] = [
        {"type": "deletion"},
        {"type": "non_fast_forward"},
        {
            "type": "pull_request",
            "parameters": {
                "required_approving_review_count": approvals,
                "dismiss_stale_reviews_on_push": False,
                "require_code_owner_review": False,
                "require_last_push_approval": False,
                "required_review_thread_resolution": False,
            },
        },
    ]

    # Only include required_status_checks rule if checks list is non-empty
    if checks and len(checks) > 0:
        rules.append(
            {
                "type": "required_status_checks",
                "parameters": {
                    "strict_required_status_checks_policy": True,
                    "required_status_checks": [{"context": c} for c in checks],
                },
            }
        )

    return {
        "name": ruleset_name,
        "target": "branch",
        "enforcement": "active",
        "conditions": {
            "ref_name": {
                "include": [f"refs/heads/{branch}"],
                "exclude": [],
            }
        },
        "rules": rules,
        "bypass_actors": [
            {
                "actor_id": 5,
                "actor_type": "RepositoryRole",
                "bypass_mode": "always",
            }
        ],
    }


def apply_branch_ruleset(
    repo: str,
    branch: str,
    checks: list[str] | None = None,
    approvals: int = 0,
    ruleset_name: str = "Protect Main Branch",
    dry_run: bool = False,
) -> bool:
    """Idempotently creates or updates a branch protection ruleset."""
    payload = build_ruleset_payload(
        branch=branch,
        checks=checks,
        approvals=approvals,
        ruleset_name=ruleset_name,
    )

    if dry_run:
        print(f"[Ruleset] [DRY-RUN] Target Repository: {repo}")
        print(f"[Ruleset] [DRY-RUN] Target Branch    : {branch}")
        print(f"[Ruleset] [DRY-RUN] Ruleset Name     : {ruleset_name}")
        print("[Ruleset] [DRY-RUN] Generated Ruleset Payload:")
        print(json.dumps(payload, indent=2))
        return True

    existing_id = get_ruleset_id_by_name(repo, ruleset_name)
    if existing_id is not None:
        print(
            f"[Ruleset] Updating existing ruleset ID {existing_id} ('{ruleset_name}') on {repo}..."
        )
        endpoint = f"repos/{repo}/rulesets/{existing_id}"
        method = "PUT"
    else:
        print(f"[Ruleset] Creating new ruleset ('{ruleset_name}') on {repo}...")
        endpoint = f"repos/{repo}/rulesets"
        method = "POST"

    res = subprocess.run(
        ["gh", "api", "-X", method, endpoint, "--input", "-"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )

    if res.returncode == 0:
        action = "Updated" if existing_id else "Created"
        print(f"  - Branch Ruleset: ✅ {action} successfully for '{branch}'.")
        return True

    print(f"❌ [Ruleset Error] Failed to {method} ruleset: {res.stderr.strip()}", file=sys.stderr)
    return False


def protect_repository(
    repo: str | None = None,
    branch: str | None = None,
    checks: list[str] | None = None,
    approvals: int = 0,
    no_dependabot: bool = False,
    ruleset_name: str = "Protect Main Branch",
    dry_run: bool = False,
) -> int:
    """Executes the full automated repository protection workflow."""
    print("\n=== CCBA Remote Repository Protection ===")

    # 1. Pre-flight binary check
    if not check_gh_cli():
        print(
            "❌ [ERROR] GitHub CLI ('gh') is not installed or not found on PATH.", file=sys.stderr
        )
        print("   Install gh via https://cli.github.com/ or your package manager.", file=sys.stderr)
        return 1

    # 2. Pre-flight auth check
    if not check_gh_auth():
        print(
            "❌ [ERROR] GitHub CLI is not authenticated. Please run 'gh auth login'.",
            file=sys.stderr,
        )
        return 1

    # 3. Resolve target repository
    target_repo = resolve_target_repo(repo)
    if not target_repo:
        print("❌ [ERROR] Could not determine target repository.", file=sys.stderr)
        print(
            "   Please provide '--repo owner/repo' or run inside a GitHub git clone.",
            file=sys.stderr,
        )
        return 1

    print(f"Target Repo  : {target_repo}")

    # 4. Check admin permissions
    if not dry_run:
        is_admin = check_admin_permission(target_repo)
        if not is_admin:
            print(
                f"❌ [ERROR] Authenticated user lacks Admin rights on '{target_repo}'.\n"
                "   Configuring rulesets and repository security requires repository administrator role.",
                file=sys.stderr,
            )
            return 1
        print("Permissions  : ✅ Repository Admin confirmed")
    else:
        print("Permissions  : [DRY-RUN] Permission check skipped")

    # 5. Resolve target branch
    target_branch = branch or get_default_branch(target_repo)
    print(f"Target Branch: {target_branch}")

    # 6. Apply Ruleset
    ruleset_ok = apply_branch_ruleset(
        repo=target_repo,
        branch=target_branch,
        checks=checks,
        approvals=approvals,
        ruleset_name=ruleset_name,
        dry_run=dry_run,
    )
    if not ruleset_ok and not dry_run:
        return 1

    # 7. Configure Dependabot & Vulnerability Alerts
    if not no_dependabot:
        enable_vulnerability_alerts(target_repo, dry_run=dry_run)
    else:
        print("[Dependabot] Skipped (--no-dependabot specified).")

    # 8. Configure Secret Scanning & Push Protection
    enable_secret_scanning(target_repo, dry_run=dry_run)

    print("\n========================================================")
    status_label = (
        "[DRY-RUN] Simulation Complete" if dry_run else "Protection Deployed Successfully"
    )
    print(f"🚀 {status_label} for '{target_repo}'!")
    print("========================================================\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Builds CLI argument parser for protect_repo."""
    parser = argparse.ArgumentParser(
        description="Automated GitHub repository protection (rulesets, Dependabot, secret scanning)."
    )
    parser.add_argument(
        "--repo",
        "-r",
        default=None,
        help="Target repository in 'owner/repo' format (auto-detected from origin if omitted)",
    )
    parser.add_argument(
        "--branch",
        "-b",
        default=None,
        help="Branch to protect (default: detected default branch, usually 'main')",
    )
    parser.add_argument(
        "--checks",
        "-c",
        nargs="*",
        default=None,
        help="List of required CI status check context names",
    )
    parser.add_argument(
        "--approvals",
        "-a",
        type=int,
        default=0,
        help="Required PR approving reviews count (default: 0)",
    )
    parser.add_argument(
        "--ruleset-name",
        default="Protect Main Branch",
        help="Display name for the GitHub Ruleset (default: 'Protect Main Branch')",
    )
    parser.add_argument(
        "--no-dependabot",
        action="store_true",
        help="Skip enabling Dependabot security fixes and vulnerability alerts",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview planned API calls and ruleset payloads without modifying remote repo",
    )
    return parser


def main() -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args()
    return protect_repository(
        repo=args.repo,
        branch=args.branch,
        checks=args.checks,
        approvals=args.approvals,
        no_dependabot=args.no_dependabot,
        ruleset_name=args.ruleset_name,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
