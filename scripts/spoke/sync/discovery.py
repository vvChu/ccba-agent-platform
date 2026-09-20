"""discovery.py - Smart Discovery Engine to locate CCBA Hub directory.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from .base import HubNotFoundError

__all__ = ["HubDiscoverer", "HubNotFoundError", "resolve_cross_platform_path"]

_WIN_DRIVE_PATTERN = re.compile(r"^[A-Za-z]:[\\/]")


def resolve_cross_platform_path(raw_path: str, base_dir: Path | None = None) -> Path | None:
    """Safely parse and resolve a path string across Windows and POSIX/Linux/WSL.

    Handles:
    - Windows drive paths ('D:\\...') running on POSIX: attempts wslpath if inside WSL,
      otherwise avoids treating it as a relative path under base_dir.
    - Relative paths ('../ccba-agent-platform') relative to base_dir.
    - Standard absolute paths.
    """
    path_str = raw_path.strip().strip("'\"")
    if not path_str:
        return None

    # Check if this is a Windows-style drive path (e.g. D:\... or D:/...)
    is_win_drive = bool(_WIN_DRIVE_PATTERN.match(path_str))

    if os.name != "nt" and is_win_drive:
        # Running on POSIX/Linux
        # 1. If inside WSL and wslpath exists, try converting
        if shutil.which("wslpath"):
            try:
                res = subprocess.run(
                    ["wslpath", "-u", path_str],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if res.returncode == 0 and res.stdout.strip():
                    wsl_p = Path(res.stdout.strip())
                    if wsl_p.exists():
                        return wsl_p.resolve()
            except Exception:
                pass
        # 2. Native Linux cannot directly resolve Windows drive letters
        return None

    cand = Path(path_str)
    if not cand.is_absolute():
        if base_dir:
            cand = (base_dir / cand).resolve()
        else:
            cand = cand.resolve()
    return cand


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
        """Locate Hub using 5-step smart discovery with multi-OS and env priority."""
        hub_root: Path | None = None

        # Step 1: Check CCBA_HUB_PATH / HUB_PATH environment variables (Top Priority)
        for env_key in ("CCBA_HUB_PATH", "HUB_PATH"):
            env_val = os.environ.get(env_key)
            if env_val:
                env_hub = resolve_cross_platform_path(env_val, self.spoke_root)
                if env_hub and self._is_valid_hub(env_hub):
                    hub_root = env_hub
                    break

        # Step 2: Check workspace_context.yaml
        if not hub_root:
            hub_path_val = self.context.get("hub_path")
            if not hub_path_val:
                proj_info = self.context.get("project")
                if isinstance(proj_info, dict):
                    hub_path_val = proj_info.get("hub_path")

            raw_str: str | None = None
            if isinstance(hub_path_val, dict):
                # Multi-OS mapping: {"windows": "D:\\...", "linux": "/home/..."}
                os_key = "windows" if os.name == "nt" else "linux"
                raw_str = str(hub_path_val.get(os_key) or hub_path_val.get("posix") or "")
            elif isinstance(hub_path_val, str):
                raw_str = hub_path_val

            if raw_str:
                candidate = resolve_cross_platform_path(raw_str, self.spoke_root)
                if candidate and self._is_valid_hub(candidate):
                    hub_root = candidate

        # Step 3: Check Sibling directory (ccba-agent-platform)
        if not hub_root:
            sibling_hub = (self.spoke_root.parent / "ccba-agent-platform").resolve()
            if self._is_valid_hub(sibling_hub):
                hub_root = sibling_hub

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

        # Auto-save ONLY if workspace_context.yaml was missing hub_path and relative path is feasible
        # Do not overwrite with machine-specific absolute path if resolved via env or already configured
        if self.context_file and self.context_file.exists():
            current_conf = self.context.get("hub_path")
            if not current_conf:
                try:
                    rel_to_spoke = os.path.relpath(hub_root, self.spoke_root)
                    save_path = rel_to_spoke if not rel_to_spoke.startswith("..") else str(hub_root)
                except ValueError:
                    save_path = str(hub_root)
                self.context["hub_path"] = save_path
                try:
                    with open(self.context_file, "w", encoding="utf-8") as f:
                        yaml.dump(self.context, f, allow_unicode=True)
                    print(f"[Sync] Auto-saved discovered Hub path: {save_path}")
                except Exception as e:
                    print(
                        f"[Sync] Warning: Could not save Hub path to context: {e}", file=sys.stderr
                    )

        return hub_root
