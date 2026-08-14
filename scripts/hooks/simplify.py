"""Simplify Gate Hook for checking git diff complexity before shipping/committing.

Warns or blocks when user attempts to ship, PR, or commit code carrying
a large, unsimplified git diff.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

from .base import BaseHook, HookContext, HookResult


class SimplifyGateHook(BaseHook):
    """Monitors prompt submission for commit/ship intent and blocks overly complex diffs."""

    name = "simplify_gate"
    supported_events = ("user-prompt-submit", "pre-tool")

    LOC_DELTA_THRESHOLD = 400
    FILE_COUNT_THRESHOLD = 8
    SINGLE_FILE_LOC_THRESHOLD = 200

    HARD_VERBS = ["ship", "merge", "pr", "deploy", "publish"]
    SOFT_VERBS = ["commit", "finalize", "release"]

    @classmethod
    def build_verb_pattern(cls, verbs: list[str]) -> re.Pattern[str]:
        verb_list = "|".join(re.escape(v) for v in verbs)
        action_prefix = "|".join(
            [r"please", r"can\s+you", r"go\s+ahead\s+and", r"let'?s", r"ready\s+to", r"time\s+to"]
        )
        action_object = "|".join(
            [
                r"it",
                r"this",
                r"that",
                r"these",
                r"the",
                r"my",
                r"our",
                r"changes?",
                r"branch",
                r"pr",
                r"pull\s+request",
                r"release",
                r"package",
                r"prod(?:uction)?",
                r"staging",
                r"now",
                r"please",
                r"to",
            ]
        )
        return re.compile(
            r"/(?:ck:)?(?P<v1>" + verb_list + r")\b|"
            r"\b(?:" + action_prefix + r")\s+(?P<v2>" + verb_list + r")\b|"
            r"\b(?:" + action_object + r")\s+(?P<v3>" + verb_list + r")\b|"
            r"\b(?P<v4>" + verb_list + r")\b\s+(?:" + action_object + r")\b",
            re.IGNORECASE,
        )

    @classmethod
    def matched_severity(cls, prompt: str) -> tuple[str, str]:
        if not prompt:
            return "", ""

        negated_pattern = (
            r"\b(?:don'?t|do not|never|not)\s+(?:\w+\s+){0,2}?(?:"
            + "|".join(cls.HARD_VERBS + cls.SOFT_VERBS)
            + r")\b"
        )
        if re.search(negated_pattern, prompt, re.IGNORECASE) or "ship on" in prompt.lower():
            return "", ""

        hard_re = cls.build_verb_pattern(cls.HARD_VERBS)
        soft_re = cls.build_verb_pattern(cls.SOFT_VERBS)

        if match := hard_re.search(prompt):
            matched_v = (
                match.group("v1")
                or match.group("v2")
                or match.group("v3")
                or match.group("v4")
                or ""
            )
            return "hard", matched_v
        if match := soft_re.search(prompt):
            matched_v = (
                match.group("v1")
                or match.group("v2")
                or match.group("v3")
                or match.group("v4")
                or ""
            )
            return "soft", matched_v

        return "", ""

    @staticmethod
    def count_lines(file_path: Path) -> int:
        if not file_path.is_file():
            return 0
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    @classmethod
    def get_git_diff_signals(cls, cwd: str) -> dict[str, Any]:
        total_loc = 0
        max_file_loc = 0
        files: set[str] = set()

        # 1. Run git diff HEAD --numstat
        try:
            diff_res = subprocess.run(
                ["git", "diff", "HEAD", "--numstat", "--ignore-all-space"],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception:
            diff_res = None

        if diff_res and diff_res.returncode == 0 and diff_res.stdout:
            for line in diff_res.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 3:
                    added = int(parts[0]) if parts[0].isdigit() else 0
                    removed = int(parts[1]) if parts[1].isdigit() else 0
                    file_path = parts[2]

                    total_loc += added + removed
                    if added > max_file_loc:
                        max_file_loc = added
                    files.add(file_path)

        # 2. Add untracked new files
        try:
            ls_res = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception:
            ls_res = None

        if ls_res and ls_res.returncode == 0 and ls_res.stdout:
            for file_path in ls_res.stdout.splitlines():
                file_path = file_path.strip()
                if not file_path:
                    continue

                full_path = Path(cwd) / file_path
                loc = cls.count_lines(full_path)
                total_loc += loc
                if loc > max_file_loc:
                    max_file_loc = loc
                files.add(file_path)

        return {
            "total_loc": total_loc,
            "file_count": len(files),
            "max_file_loc": max_file_loc,
            "files": list(files),
        }

    def execute(self, context: HookContext) -> HookResult:
        if os.environ.get("CK_SIMPLIFY_DISABLED") == "1" or context.is_approved:
            return HookResult(name=self.name, exit_code=0, message="Simplify gate bypassed.")

        prompt = context.args or context.status or ""
        if not prompt:
            return HookResult(
                name=self.name, exit_code=0, message="No prompt payload for simplify gate."
            )

        severity, verb = self.matched_severity(prompt)
        if not severity:
            return HookResult(name=self.name, exit_code=0, message="No shipping/commit verb found.")

        cwd = context.cwd or os.getcwd()
        metrics = self.get_git_diff_signals(cwd)

        breaches = []
        if metrics["total_loc"] > self.LOC_DELTA_THRESHOLD:
            breaches.append(f"{metrics['total_loc']} LOC")
        if metrics["file_count"] > self.FILE_COUNT_THRESHOLD:
            breaches.append(f"{metrics['file_count']} files")
        if metrics["max_file_loc"] > self.SINGLE_FILE_LOC_THRESHOLD:
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
                return HookResult(
                    name=self.name,
                    exit_code=2,
                    message=f"Hard block: Git diff exceeded thresholds ({', '.join(breaches)})",
                    details={"metrics": metrics, "breaches": breaches, "verb": verb},
                )
            else:
                print(error_msg.replace("[SIMPLIFY GATE]", "\x1b[33m[SIMPLIFY WARNING]\x1b[0m"))
                return HookResult(
                    name=self.name,
                    exit_code=0,  # Soft warning allows continuation
                    message=f"Soft warning: Git diff exceeded thresholds ({', '.join(breaches)})",
                    details={"metrics": metrics, "breaches": breaches, "verb": verb},
                )

        return HookResult(
            name=self.name,
            exit_code=0,
            message="Diff complexity within allowable thresholds.",
            details={"metrics": metrics},
        )
