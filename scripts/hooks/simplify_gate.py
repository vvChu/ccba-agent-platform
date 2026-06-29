"""Hook script for UserPromptSubmit events to check diff complexity.

Warns or blocks when user attempts to ship, PR, or commit code carrying
a large, unsimplified git diff.
"""

import os
import re
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set

# Configuration Thresholds
LOC_DELTA_THRESHOLD = 400
FILE_COUNT_THRESHOLD = 8
SINGLE_FILE_LOC_THRESHOLD = 200

# Verb Matching Regex Patterns
HARD_VERBS = ["ship", "merge", "pr", "deploy", "publish"]
SOFT_VERBS = ["commit", "finalize", "release"]


def build_verb_pattern(verbs: List[str]) -> re.Pattern:
    """Build a regex pattern to match dynamic action verbs in user prompts."""
    verb_list = "|".join(re.escape(v) for v in verbs)
    action_prefix = "|".join([
        r"please",
        r"can\s+you",
        r"go\s+ahead\s+and",
        r"let'?s",
        r"ready\s+to",
        r"time\s+to"
    ])
    action_object = "|".join([
        r"it", r"this", r"that", r"these", r"the", r"my", r"our",
        r"changes?", r"branch", r"pr", r"pull\s+request", r"release",
        r"package", r"prod(?:uction)?", r"staging", r"now", r"please", r"to"
    ])
    
    return re.compile(
        r"/(?:ck:)?(?P<v1>" + verb_list + r")\b|"
        r"\b(?:" + action_prefix + r")\s+(?P<v2>" + verb_list + r")\b|"
        r"\b(?P<v3>" + verb_list + r")\b\s+(?:" + action_object + r")\b",
        re.IGNORECASE
    )


def matched_severity(prompt: str) -> Tuple[str, str]:
    """Check user prompt for commit or ship intent and return severity level.

    Args:
        prompt: User input string.

    Returns:
        Tuple of (severity, matched_verb) where severity is "hard", "soft", or "".
    """
    # Reject false positives: negated phrases
    negated_pattern = r"\b(?:don'?t|do not|never|not)\s+(?:\w+\s+){0,2}?(?:" + "|".join(HARD_VERBS + SOFT_VERBS) + r")\b"
    if re.search(negated_pattern, prompt, re.IGNORECASE) or "ship on" in prompt.lower():
        return "", ""

    hard_re = build_verb_pattern(HARD_VERBS)
    soft_re = build_verb_pattern(SOFT_VERBS)
    
    if match := hard_re.search(prompt):
        matched_v = match.group("v1") or match.group("v2") or match.group("v3") or ""
        return "hard", matched_v
    if match := soft_re.search(prompt):
        matched_v = match.group("v1") or match.group("v2") or match.group("v3") or ""
        return "soft", matched_v
        
    return "", ""


def count_lines(filepath: Path) -> int:
    """Helper to count lines in a text file.

    Args:
        filepath: Path to the target file.

    Returns:
        Number of lines in the file.
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def get_git_diff_signals(cwd: str) -> Dict[str, Any]:
    """Gather git diff metrics (LOC additions/deletions and untracked files).

    Args:
        cwd: Repository working directory.

    Returns:
        Dict of diff metrics (total_loc, file_count, max_file_loc).
    """
    metrics = {
        "total_loc": 0,
        "file_count": 0,
        "max_file_loc": 0,
        "files": []
    }
    
    # 1. Run git diff HEAD --numstat
    try:
        diff_res = subprocess.run(
            ["git", "diff", "HEAD", "--numstat", "--ignore-all-space"],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
    except Exception:
        return metrics
        
    files = set()
    if diff_res.returncode == 0 and diff_res.stdout:
        for line in diff_res.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 3:
                added = int(parts[0]) if parts[0].isdigit() else 0
                removed = int(parts[1]) if parts[1].isdigit() else 0
                file_path = parts[2]
                
                metrics["total_loc"] += added + removed
                if added > metrics["max_file_loc"]:
                    metrics["max_file_loc"] = added
                files.add(file_path)
                
    # 2. Add untracked new files
    try:
        ls_res = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
    except Exception:
        ls_res = None
        
    if ls_res and ls_res.returncode == 0 and ls_res.stdout:
        for file_path in ls_res.stdout.splitlines():
            file_path = file_path.strip()
            if not file_path:
                continue
            
            full_path = Path(cwd) / file_path
            loc = count_lines(full_path)
            metrics["total_loc"] += loc
            if loc > metrics["max_file_loc"]:
                metrics["max_file_loc"] = loc
            files.add(file_path)
            
    metrics["file_count"] = len(files)
    metrics["files"] = list(files)
    return metrics


def main(event: str, payload: Dict[str, Any]) -> int:
    """Evaluate if working tree has too complex diff before shipping/committing.

    Args:
        event: Lifecycle event name.
        payload: Event arguments and environment state.

    Returns:
        Exit code: 0 to allow, 2 to block.
    """
    # Bypass check
    if os.environ.get("CK_SIMPLIFY_DISABLED") == "1":
        return 0
        
    prompt = payload.get("args") or payload.get("status") or ""
    if not prompt:
        return 0
        
    # Check if prompt bypass is approved
    if "APPROVED:" in prompt:
        return 0
        
    # Check matched verbs and severity
    severity, verb = matched_severity(prompt)
    if not severity:
        return 0
        
    cwd = payload.get("cwd") or os.getcwd()
    metrics = get_git_diff_signals(cwd)
    
    # Evaluate breaches
    breaches = []
    if metrics["total_loc"] > LOC_DELTA_THRESHOLD:
        breaches.append(f"{metrics['total_loc']} LOC")
    if metrics["file_count"] > FILE_COUNT_THRESHOLD:
        breaches.append(f"{metrics['file_count']} files")
    if metrics["max_file_loc"] > SINGLE_FILE_LOC_THRESHOLD:
        breaches.append(f"single file +{metrics['max_file_loc']} LOC")
        
    if breaches:
        verb_noun = "shipping/PR" if severity == "hard" else "committing"
        error_msg = f"""
\x1b[31m[SIMPLIFY GATE]\x1b[0m: Unsimplified git diff detected ({", ".join(breaches)})!
  
  Matched Verb: \x1b[33m'{verb}'\x1b[0m ({verb_noun} intent detected)
  
  The current changes are too large and complex.
  Please simplify your code or refactor before proceeding.
  
  To fix this:
  - Run code simplifier subagent to reduce diff size.
  - Or manually clean up redundant/commented code.
  
  To bypass:
  - Add "APPROVED:" prefix to your request.
  - Or set environment variable `CK_SIMPLIFY_DISABLED=1`.
"""
        if severity == "hard":
            print(error_msg)
            return 2  # Hard Block
        else:
            # Soft Warning
            print(error_msg.replace("[SIMPLIFY GATE]", "\x1b[33m[SIMPLIFY WARNING]\x1b[0m"))
            return 0  # Allow but warn
            
    return 0
