#!/usr/bin/env python3
"""
Update Checker for claudekit-engineer.
Checks for new commits/skills in the claudekit-engineer repository.
"""

import sys
import os
import subprocess
from pathlib import Path

# Enforce UTF-8 output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Tracking configuration for both upstream repositories
REPOS_CONFIG = [
    {
        "type": "engineer",
        "local_path": Path("claudekit-engineer"),
        "remote_url": "https://github.com/claudekit/claudekit-engineer",
        "sha_file": Path(".md/scratch/claudekit_last_sha.txt")
    },
    {
        "type": "marketing",
        "local_path": Path(".agents/claudekit-marketing"),
        "remote_url": "https://github.com/claudekit/claudekit-marketing",
        "sha_file": Path(".md/scratch/claudekit_marketing_last_sha.txt")
    }
]


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
                check=True
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
            check=True
        )
        output = res.stdout.strip()
        if output:
            return output.split()[0]
    except subprocess.SubprocessError:
        pass
    return ""


def check_and_evaluate(config: dict):
    """Check a single repository and trigger the evaluator if updates found."""
    repo_type = config["type"]
    local_path = config["local_path"]
    remote_url = config["remote_url"]
    sha_file = config["sha_file"]
    
    print(f"[ClaudeKit Update Check] Checking remote claudekit-{repo_type} for new updates...")
    
    local_sha = get_local_sha(config)
    remote_sha = get_remote_sha(remote_url)
    
    if not remote_sha:
        print(f"[ClaudeKit Update Check] Warning: Could not connect to remote claudekit-{repo_type}.")
        return
        
    if not local_sha:
        print(f"[ClaudeKit Update Check] Initializing tracker for {repo_type} with remote SHA: {remote_sha}")
        sha_file.write_text(remote_sha, encoding="utf-8")
        return
        
    if local_sha != remote_sha:
        print(f"\n\x1b[33m[UPDATE AVAILABLE]\x1b[0m New updates found in claudekit-{repo_type}!")
        print(f"  - Local SHA:  {local_sha[:8]}")
        print(f"  - Remote SHA: {remote_sha[:8]}")
        print(f"  - Triggering Automated Porting Evaluator...")
        
        # Invoke assess_upstream_features.py
        try:
            eval_cmd = [
                sys.executable,
                "scripts/assess_upstream_features.py",
                "--repo-path", str(local_path),
                "--repo-type", repo_type,
                "--base", local_sha,
                "--head", remote_sha
            ]
            # Run evaluator
            subprocess.run(eval_cmd, check=True)
            
            # Save the new SHA
            sha_file.write_text(remote_sha, encoding="utf-8")
            print(f"[ClaudeKit Update Check] Successfully processed updates for claudekit-{repo_type}.\n")
        except Exception as e:
            print(f"[ClaudeKit Update Check] Error running evaluator: {e}\n")
    else:
        print(f"[ClaudeKit Update Check] claudekit-{repo_type} is up-to-date.")


def main():
    print("[ClaudeKit Update Check] Running update checks across repositories...\n")
    for config in REPOS_CONFIG:
        check_and_evaluate(config)
    print("\n[ClaudeKit Update Check] All update checks completed.")


if __name__ == "__main__":
    main()
