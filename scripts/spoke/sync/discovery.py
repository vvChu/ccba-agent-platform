"""discovery.py - Smart Discovery Engine to locate CCBA Hub directory.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import yaml

from .base import HubNotFoundError

__all__ = ["HubDiscoverer", "HubNotFoundError"]


class HubDiscoverer:
    """Smart Discovery Engine to locate the CCBA Hub directory."""

    def __init__(
        self,
        spoke_root: Path,
        context: dict[str, Any],
        context_file: Path | None = None,
    ) -> None:
        self.spoke_root = spoke_root
        self.context = context
        self.context_file = context_file

    def _is_valid_hub(self, candidate: Path) -> bool:
        catalog = candidate / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
        return catalog.exists()

    def discover(self) -> Path:
        """Locate Hub using 4-step smart discovery and auto-save if path changed."""
        hub_path_val = self.context.get("hub_path")
        if not hub_path_val:
            proj_info = self.context.get("project")
            if isinstance(proj_info, dict):
                hub_path_val = proj_info.get("hub_path")
        hub_path_str = str(hub_path_val or "").strip()

        hub_root: Path | None = None

        # Step 1: Check workspace_context.yaml
        if hub_path_str:
            candidate = Path(hub_path_str)
            if not candidate.is_absolute():
                candidate = (self.spoke_root / candidate).resolve()
            if self._is_valid_hub(candidate):
                hub_root = candidate

        # Step 2: Check Sibling directory (ccba-agent-platform)
        if not hub_root:
            sibling_hub = (self.spoke_root.parent / "ccba-agent-platform").resolve()
            if self._is_valid_hub(sibling_hub):
                hub_root = sibling_hub

        # Step 3: Check CCBA_HUB_PATH environment variable
        if not hub_root and "CCBA_HUB_PATH" in os.environ:
            env_hub = Path(os.environ["CCBA_HUB_PATH"]).resolve()
            if self._is_valid_hub(env_hub):
                hub_root = env_hub

        # Step 4: Fallback to CWD if running inside Hub
        if not hub_root:
            cwd_hub = Path.cwd().resolve()
            if self._is_valid_hub(cwd_hub):
                hub_root = cwd_hub

        if not hub_root:
            raise HubNotFoundError(
                f"[Sync] Error: Could not locate Hub directory from {self.spoke_root}.\n"
                "Please set CCBA_HUB_PATH environment variable or specify hub_path in workspace_context.yaml."
            )

        # Auto-save discovered Hub path if changed
        if hub_path_str != str(hub_root) and self.context_file and self.context_file.exists():
            self.context["hub_path"] = str(hub_root)
            try:
                with open(self.context_file, "w", encoding="utf-8") as f:
                    yaml.dump(self.context, f, allow_unicode=True)
                print(f"[Sync] Auto-saved discovered Hub path: {hub_root}")
            except Exception as e:
                print(f"[Sync] Warning: Could not save Hub path to context: {e}", file=sys.stderr)

        return hub_root
