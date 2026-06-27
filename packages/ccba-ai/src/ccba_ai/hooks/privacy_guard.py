import os
import re
import yaml
from pathlib import Path

class PrivacyGuardHook:
    """Security hook to scan content and prevent leakage of sensitive API Keys (Gemini, OpenAI, Groq, LlamaCloud)."""

    DEFAULT_BLOCK_PATTERNS = [
        r"AIzaSy[A-Za-z0-9-_]{30,40}",   # Gemini API Key
        r"sk-[A-Za-z0-9]{30,50}",        # OpenAI API Key
        r"sk-proj-[A-Za-z0-9_]{30,}",    # New OpenAI API Key
        r"sk-[a-zA-Z0-9]{32,}",          # LlamaCloud / Groq / General API Key
    ]

    def __init__(self, config_path: str | None = None):
        self.enabled = True
        self.block_patterns = self.DEFAULT_BLOCK_PATTERNS.copy()
        
        # Load hooks.yaml if it exists
        path = Path(config_path or Path.cwd() / "hooks.yaml")
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}
                hook_config = config.get("hooks", {}).get("privacy_guard", {})
                self.enabled = hook_config.get("enabled", True)
                custom_patterns = hook_config.get("block_patterns", [])
                if custom_patterns:
                    self.block_patterns = custom_patterns
            except Exception as e:
                # Silent fail to avoid disrupting client
                pass

    def check_content(self, content: str) -> None:
        """Scan content against blocked patterns. Raises ValueError if a match is found."""
        if not self.enabled or not content:
            return

        for pattern in self.block_patterns:
            matches = re.findall(pattern, content)
            if matches:
                # Obfuscate key in error message for safety
                key_sample = matches[0]
                obfuscated = key_sample[:6] + "..." + key_sample[-4:] if len(key_sample) > 10 else "..."
                raise ValueError(
                    f"[PrivacyGuard] Security Violation: Detected sensitive API Key leak ({obfuscated}). "
                    "Writing or returning raw API keys is strictly blocked."
                )
