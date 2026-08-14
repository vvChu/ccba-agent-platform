"""Agent profile specifications and log directory locator."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

# Standard agent profiles and paths configuration
AGENT_SPECS: dict[str, dict[str, str]] = {
    "claude": {"dot_dir": ".claude/projects", "app_name": "Claude", "xdg_name": "claude"},
    "codex": {"dot_dir": ".codex/sessions", "app_name": "Codex", "xdg_name": "codex"},
    "cursor": {"dot_dir": ".cursor", "app_name": "Cursor", "xdg_name": "cursor"},
    "opencode": {"dot_dir": ".opencode", "app_name": "opencode", "xdg_name": "opencode"},
    "antigravity": {
        "dot_dir": ".antigravity",
        "app_name": "Antigravity",
        "xdg_name": "antigravity",
    },
    "kimi": {"dot_dir": ".kimi", "app_name": "Kimi", "xdg_name": "kimi"},
    "droid": {"dot_dir": ".droid", "app_name": "Droid", "xdg_name": "droid"},
    "gemini": {"dot_dir": ".gemini", "app_name": "Gemini", "xdg_name": "gemini"},
    "github-copilot": {
        "dot_dir": ".github-copilot",
        "app_name": "GitHub Copilot",
        "xdg_name": "github-copilot",
    },
    "hermes": {"dot_dir": ".hermes", "app_name": "Hermes Agent", "xdg_name": "hermes"},
    "openclaw": {"dot_dir": ".openclaw", "app_name": "OpenClaw", "xdg_name": "openclaw"},
    "kilo": {"dot_dir": ".kilo-code", "app_name": "Kilo Code", "xdg_name": "kilo-code"},
    "kiro": {"dot_dir": ".kiro", "app_name": "Kiro", "xdg_name": "kiro"},
    "pi": {"dot_dir": ".pi", "app_name": "Pi", "xdg_name": "pi"},
    "qoder": {"dot_dir": ".qoder", "app_name": "Qoder", "xdg_name": "qoder"},
    "qwen": {"dot_dir": ".qwen", "app_name": "Qwen Code", "xdg_name": "qwen-code"},
    "trae": {"dot_dir": ".trae", "app_name": "Trae", "xdg_name": "trae"},
}

AGENT_ALIASES: dict[str, str] = {
    "claude-code": "claude",
    "claudecode": "claude",
    "open-code": "opencode",
    "antigravity-cli": "antigravity",
    "antigravity-code": "antigravity",
    "kimi-code": "kimi",
    "kimi-code-cli": "kimi",
    "kimi-cli": "kimi",
    "gemini-cli": "gemini",
    "github-copilot-cli": "github-copilot",
    "copilot": "github-copilot",
    "hermes-agent": "hermes",
    "open-claw": "openclaw",
    "openclaw-cli": "openclaw",
    "kilo-code": "kilo",
    "kiro-cli": "kiro",
    "pi-cli": "pi",
    "qwen-code": "qwen",
    "qoder-cli": "qoder",
    "trae-cli": "trae",
}


def normalize_agent_name(name: str) -> str:
    """Normalize agent name to canonical key."""
    clean = name.lower().strip().replace("_", "-").replace(" ", "-")
    return AGENT_ALIASES.get(clean, clean)


def get_default_roots(dot_dir: str, app_name: str, xdg_name: str) -> list[Path]:
    """Retrieve system-specific default log paths."""
    home = Path.home()
    roots = [home / dot_dir]
    if sys.platform == "win32":
        for env_var in ["APPDATA", "LOCALAPPDATA"]:
            if val := os.getenv(env_var):
                roots.append(Path(val) / app_name)
    elif sys.platform == "darwin":
        roots.append(home / "Library" / "Application Support" / app_name)
    else:
        roots.append(home / ".config" / xdg_name)
        roots.append(home / ".local" / "share" / xdg_name)
    return list(dict.fromkeys(roots))


def resolve_targets(agent_name: str, custom_root: str | None = None) -> list[dict[str, Any]]:
    """Resolve which target directories/agents to scan."""
    norm = normalize_agent_name(agent_name)
    if custom_root:
        return [
            {"agent": norm if norm != "auto" else "custom", "root": Path(custom_root).resolve()}
        ]

    home = Path.home()
    agents_list = list(AGENT_SPECS.keys())

    if norm == "auto":
        existing = []
        for agent in agents_list:
            spec = AGENT_SPECS[agent]
            for path in get_default_roots(spec["dot_dir"], spec["app_name"], spec["xdg_name"]):
                if path.is_dir():
                    existing.append({"agent": agent, "root": path.resolve()})
        return (
            existing
            if existing
            else [{"agent": "claude", "root": (home / ".claude" / "projects").resolve()}]
        )

    if norm == "all":
        all_targets = []
        for agent in agents_list:
            spec = AGENT_SPECS[agent]
            for path in get_default_roots(spec["dot_dir"], spec["app_name"], spec["xdg_name"]):
                all_targets.append({"agent": agent, "root": path.resolve()})
        return all_targets

    if norm not in AGENT_SPECS:
        raise ValueError(f"Unsupported agent: {agent_name}")

    spec = AGENT_SPECS[norm]
    return [
        {"agent": norm, "root": path.resolve()}
        for path in get_default_roots(spec["dot_dir"], spec["app_name"], spec["xdg_name"])
    ]
