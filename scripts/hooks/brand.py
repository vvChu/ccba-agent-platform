"""Brand Enforcement Hook for CCBA Lifecycle.

Checks generated markdown and text files for correct brand names and prohibited words.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import yaml

from .base import BaseHook, HookContext, HookResult


class BrandHook(BaseHook):
    """Verifies brand spelling and alerts on prohibited placeholder words."""

    name = "brand_enforcement"
    supported_events = ("post-tool",)

    DEFAULT_BRAND_PATTERNS = [
        (r"\bclaudekit\b", "ClaudeKit"),
        (r"\blitellm\b", "LiteLLM"),
        (r"\bantigravity\b", "Antigravity"),
        (r"\bgemini\b", "Gemini"),
    ]

    DEFAULT_PROHIBITED_WORDS = [
        r"\blorem ipsum\b",
        r"\bplaceholder\b",
    ]

    BRAND_RULES_FILE = Path(".md/knowledge/brand_rules.yaml")

    @classmethod
    def load_brand_rules(cls) -> tuple[list[tuple[str, str]], list[str]]:
        if not cls.BRAND_RULES_FILE.exists():
            return cls.DEFAULT_BRAND_PATTERNS, cls.DEFAULT_PROHIBITED_WORDS

        try:
            with open(cls.BRAND_RULES_FILE, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            patterns = []
            for item in data.get("brand_patterns", []):
                patterns.append((item["pattern"], item["correct"]))

            prohibited = data.get("prohibited_words", [])
            return (patterns or cls.DEFAULT_BRAND_PATTERNS), (
                prohibited or cls.DEFAULT_PROHIBITED_WORDS
            )
        except Exception:
            return cls.DEFAULT_BRAND_PATTERNS, cls.DEFAULT_PROHIBITED_WORDS

    @classmethod
    def check_file(cls, file_path: Path) -> list[str]:
        findings: list[str] = []
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return findings

        brand_patterns, prohibited_words = cls.load_brand_rules()

        for pattern, correct in brand_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for m in matches:
                if m != correct:
                    w = f"[Brand Warning] In file '{file_path}': Found '{m}', expected '{correct}'"
                    print(f"\x1b[33m{w}\x1b[0m")
                    findings.append(w)

        for pattern in prohibited_words:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for m in matches:
                a = f"[Policy Alert] In file '{file_path}': Found prohibited word '{m}'"
                print(f"\x1b[31m{a}\x1b[0m")
                findings.append(a)

        return findings

    def execute(self, context: HookContext) -> HookResult:
        findings = []

        if context.path:
            p = Path(context.path)
            if p.exists() and p.is_file():
                findings.extend(self.check_file(p))
                return HookResult(
                    name=self.name,
                    exit_code=0,
                    message=f"Scanned {p.name}: {len(findings)} notice(s)",
                    details={"findings": findings},
                )

        cwd = Path(context.cwd or Path.cwd())
        exclude_dirs = {".git", "claudekit-engineer", ".agents", "node_modules", "venv", ".venv"}

        for root, dirs, files in os.walk(cwd):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for f in files:
                if f.endswith((".md", ".txt")):
                    file_path = Path(root) / f
                    if "node_modules" in str(file_path):
                        continue
                    findings.extend(self.check_file(file_path))

        return HookResult(
            name=self.name,
            exit_code=0,
            message=f"Brand check completed with {len(findings)} notice(s).",
            details={"findings": findings},
        )
