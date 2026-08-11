#!/usr/bin/env python3
"""
Update Checker for claudekit-engineer.
Checks for new commits/skills in the claudekit-engineer repository.
"""

import subprocess
import sys
from pathlib import Path

# Enforce UTF-8 output
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Tracking configuration for both upstream repositories
PLATFORM_ROOT = Path(__file__).resolve().parents[1]
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


def ensure_local_repo(config: dict) -> bool:
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
            # Detect default branch name (usually main or master)
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


def get_local_sha(config: dict) -> str:
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


def get_remote_sha(remote_url: str) -> str:
    """Query git ls-remote for the remote repository head commit."""
    try:
        res = subprocess.run(
            ["git", "ls-remote", remote_url, "refs/heads/main"],
            capture_output=True,
            text=True,
            check=True,
        )
        output = res.stdout.strip()
        if output:
            return output.split()[0]
    except subprocess.SubprocessError:
        pass
    # Fallback to check refs/heads/master if main is not found
    try:
        res = subprocess.run(
            ["git", "ls-remote", remote_url, "refs/heads/master"],
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


def check_and_evaluate(config: dict, check_only: bool = False):
    """Check a single repository and trigger the evaluator if updates found."""
    repo_type = config["type"]
    local_path = config["local_path"]
    remote_url = config["remote_url"]
    sha_file = config["sha_file"]

    print(f"[ClaudeKit Update Check] Checking remote {repo_type} for new updates...")

    remote_sha = get_remote_sha(remote_url)
    if not remote_sha:
        print(f"[ClaudeKit Update Check] Warning: Could not connect to remote {repo_type}.")
        return

    # Ensure local repo is synced
    success = ensure_local_repo(config)
    if not success:
        print(f"[ClaudeKit Update Check] Warning: Failed to sync local repo for {repo_type}.")
        return

    local_sha = get_local_sha(config)

    if not local_sha:
        print(
            f"[ClaudeKit Update Check] Initializing tracker for {repo_type} with remote SHA: {remote_sha}"
        )
        if not check_only:
            sha_file.write_text(remote_sha, encoding="utf-8")
        return

    if local_sha != remote_sha:
        print(f"\n\x1b[33m[UPDATE AVAILABLE]\x1b[0m New updates found in {repo_type}!")
        print(f"  - Local SHA:  {local_sha[:8]}")
        print(f"  - Remote SHA: {remote_sha[:8]}")

        # Get list of changed files
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
            print(f"  - Error retrieving changed files list: {e}")

        if check_only:
            print(
                "  - [Check-Only Mode] Skipping automated evaluator. Please run evaluate command manually.\n"
            )
            return

        print("  - Triggering Automated Porting Evaluator...")
        # Invoke assess_upstream_features.py
        try:
            eval_cmd = [
                sys.executable,
                str(PLATFORM_ROOT / "scripts" / "assess_upstream_features.py"),
                "--repo-path",
                str(local_path),
                "--repo-type",
                repo_type,
                "--base",
                local_sha,
                "--head",
                remote_sha,
            ]
            # Run evaluator
            subprocess.run(eval_cmd, check=True)

            # Save the new SHA
            sha_file.write_text(remote_sha, encoding="utf-8")
            print(f"[ClaudeKit Update Check] Successfully processed updates for {repo_type}.\n")
        except Exception as e:
            print(f"[ClaudeKit Update Check] Error running evaluator: {e}\n")
    else:
        print(f"[ClaudeKit Update Check] {repo_type} is up-to-date.")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Check for ClaudeKit Upstream Updates")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check for updates and list changed files, do not evaluate",
    )
    args = parser.parse_args()

    print("[ClaudeKit Update Check] Running update checks across repositories...\n")
    for config in REPOS_CONFIG:
        check_and_evaluate(config, check_only=args.check_only)
    print("\n[ClaudeKit Update Check] All update checks completed.")


if __name__ == "__main__":
    main()
