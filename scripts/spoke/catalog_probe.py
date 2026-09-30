"""catalog_probe.py - Non-blocking Subprocess Network Probe (ADR-0060 Mục 6).

Implements background probe with hard 1.5s SIGKILL timeout, reaping zombie processes,
and protecting Linter/CLI from kernel-level blocking getaddrinfo/DNS socket hangs.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

__all__ = ["CatalogProbeRunner"]

_DEBOUNCE_SECONDS = 900.0  # 15 minutes


class CatalogProbeRunner:
    """Manages non-blocking subprocess probe execution and state persistence."""

    def __init__(self, spoke_root: Path) -> None:
        self.spoke_root = spoke_root.resolve()
        self.cache_dir = self.spoke_root / ".agents" / "cache" / "hub-catalog"
        self.state_file = self.cache_dir / "probe-state.json"

    def get_persisted_state(self) -> dict[str, Any]:
        """Read persisted probe state safely."""
        if not self.state_file.is_file():
            return {}
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def save_persisted_state(self, state: dict[str, Any]) -> None:
        """Persist probe state atomically."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        temp_f = self.cache_dir / f".state.{os.getpid()}_{time.time_ns()}.tmp"
        try:
            temp_f.write_text(json.dumps(state, indent=2), encoding="utf-8")
            os.replace(temp_f, self.state_file)
        except Exception:
            if temp_f.is_file():
                try:
                    temp_f.unlink(missing_ok=True)
                except Exception:
                    pass

    def evaluate_freshness(
        self,
        current_seam_sha: str,
        catalog_url: str | None = None,
        timeout_sec: float = 1.5,
    ) -> str:
        """Evaluate catalog freshness via subprocess probe with hard timeout.

        Returns:
            "fresh" | "stale" | "unverified"
        """
        target_url = catalog_url or os.environ.get("CCBA_CATALOG_URL")
        if not target_url or not target_url.strip():
            # No control plane URL configured; do not open socket
            return "unverified"

        target_url = target_url.strip()
        state = self.get_persisted_state()
        now = time.time()
        last_probe_time = state.get("last_probe_timestamp_epoch", 0.0)
        last_url = state.get("url")

        # Monotonic Debounce check (15 minutes)
        if last_url == target_url and (now - last_probe_time) < _DEBOUNCE_SECONDS:
            cached_status = state.get("last_freshness", "unverified")
            cached_remote_sha = state.get("remote_seam_sha256")
            if cached_remote_sha:
                return "fresh" if cached_remote_sha == current_seam_sha else "stale"
            return cached_status

        # Spawn subprocess probe with hard timeout
        remote_sha = self._spawn_subprocess_probe(target_url, timeout_sec=timeout_sec)

        if remote_sha:
            freshness = "fresh" if remote_sha == current_seam_sha else "stale"
            self.save_persisted_state(
                {
                    "url": target_url,
                    "last_probe_timestamp_epoch": now,
                    "last_freshness": freshness,
                    "remote_seam_sha256": remote_sha,
                }
            )
            return freshness

        # Timed out or network error -> mark unverified and update debounce timestamp
        self.save_persisted_state(
            {
                "url": target_url,
                "last_probe_timestamp_epoch": now,
                "last_freshness": "unverified",
                "remote_seam_sha256": None,
            }
        )
        return "unverified"

    def check_mcp_health(self, url: str, timeout_sec: float = 1.5) -> bool:
        """Check health of remote MCP endpoint within timeout budget."""
        if not url or not url.strip():
            return False

        worker_code = (
            "import urllib.request, sys; "
            "url = sys.argv[1]; "
            "req = urllib.request.Request(url, headers={'User-Agent': 'CCBA-MCP-Probe/1.0'}); "
            "resp = urllib.request.urlopen(req, timeout=1.2); "
            "sys.stdout.write('OK' if resp.status < 500 else 'ERR'); "
            "sys.stdout.flush()"
        )

        cmd = [sys.executable, "-c", worker_code, url.strip()]
        kwargs: dict[str, Any] = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "shell": False,
        }
        if os.name != "nt":
            kwargs["start_new_session"] = True

        try:
            proc = subprocess.Popen(cmd, **kwargs)
        except Exception:
            return False

        try:
            stdout, _ = proc.communicate(timeout=timeout_sec)
            return proc.returncode == 0 and "OK" in stdout
        except subprocess.TimeoutExpired:
            self._reap_process_hard(proc)
            return False
        except Exception:
            self._reap_process_hard(proc)
            return False

    def _spawn_subprocess_probe(self, url: str, timeout_sec: float = 1.5) -> str | None:
        """Run probe worker in isolated process group and enforce hard SIGKILL on timeout."""
        worker_code = (
            "import urllib.request, hashlib, sys; "
            "url = sys.argv[1]; "
            "req = urllib.request.Request(url, headers={'User-Agent': 'CCBA-Spoke-Probe/1.0'}); "
            "resp = urllib.request.urlopen(req, timeout=1.2); "
            "data = resp.read(); "
            "sha = hashlib.sha256(data).hexdigest(); "
            "sys.stdout.write(sha); "
            "sys.stdout.flush()"
        )

        cmd = [sys.executable, "-c", worker_code, url]

        # Use start_new_session=True to create a new process group on POSIX
        kwargs: dict[str, Any] = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "shell": False,
        }
        if os.name != "nt":
            kwargs["start_new_session"] = True

        try:
            proc = subprocess.Popen(cmd, **kwargs)
        except Exception:
            return None

        try:
            stdout, _ = proc.communicate(timeout=timeout_sec)
            if proc.returncode == 0 and stdout:
                res_sha = stdout.strip()
                if len(res_sha) == 64 and all(c in "0123456789abcdef" for c in res_sha):
                    return res_sha
            return None
        except subprocess.TimeoutExpired:
            # Process exceeded wall clock budget -> hard kill process group
            self._reap_process_hard(proc)
            return None
        except Exception:
            self._reap_process_hard(proc)
            return None

    def _reap_process_hard(self, proc: subprocess.Popen[str]) -> None:
        """Hard kill process and its process group, then reap zombie with wait()."""
        try:
            if os.name != "nt":
                pgid = os.getpgid(proc.pid)
                os.killpg(pgid, signal.SIGKILL)
            else:
                proc.kill()
        except ProcessLookupError:
            pass
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        try:
            # Crucial: Reap zombie exit status from kernel table
            proc.wait(timeout=0.5)
        except Exception:
            pass
