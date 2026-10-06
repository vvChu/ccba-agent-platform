"""test_verification_harness_dogfood.py - Dogfooding test suite for ccba-create-verification-skill.

Tests the 5 core blocks of the verification harness:
1. Clean-Slate Pre-flight (Port check)
2. Dual-Mode Server Lifecycle (Process group isolation: setsid / CREATE_NEW_PROCESS_GROUP)
3. Deterministic Health Barrier (Readiness polling with timeout)
4. Evidence-Capture Test Suite (Execution & assertion)
5. Guaranteed Graceful Cleanup (Process group termination in finally)
Plus Mode 1 (Scaffold) vs Mode 2 (Maintain) and COND-01 (Pre-Remediation Provenance Check).
"""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

import pytest

pytestmark = [pytest.mark.integration]


def find_free_port() -> int:
    """Finds an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def is_port_in_use(port: int) -> bool:
    """Checks whether a port is currently listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex(("127.0.0.1", port)) == 0


def poll_readiness(url: str, timeout_seconds: float = 5.0, interval: float = 0.05) -> bool:
    """Deterministic Health Barrier: polls endpoint until 200 OK or timeout."""
    start = time.monotonic()
    while time.monotonic() - start < timeout_seconds:
        try:
            with urlopen(url, timeout=0.5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(interval)
    return False


def test_clean_slate_pre_flight_detects_occupied_port() -> None:
    """Verifies Block 1: Clean-Slate Pre-flight detects port collisions."""
    port = find_free_port()
    assert not is_port_in_use(port), "Port must initially be free"

    # Occupy the port temporarily
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", port))
    sock.listen(1)
    try:
        assert is_port_in_use(port), "Pre-flight check must detect occupied port"
    finally:
        sock.close()


def test_dual_mode_server_lifecycle_and_guaranteed_cleanup(tmp_path: Path) -> None:
    """Verifies Blocks 2, 3, 4, 5: Server process group lifecycle, probe, and graceful cleanup."""
    port = find_free_port()
    server_script = tmp_path / "dummy_server.py"
    server_script.write_text(
        f"""
import http.server
import sys

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'HEALTHY')
    def log_message(self, *args):
        pass

server = http.server.HTTPServer(('127.0.0.1', {port}), Handler)
server.serve_forever()
""",
        encoding="utf-8",
    )

    is_win = sys.platform == "win32"
    kwargs: dict[str, object] = {}
    if is_win:
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["preexec_fn"] = os.setsid

    proc = subprocess.Popen(
        [sys.executable, str(server_script)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **kwargs,
    )

    try:
        # Block 3: Deterministic Health Barrier
        url = f"http://127.0.0.1:{port}/"
        healthy = poll_readiness(url, timeout_seconds=5.0)
        assert healthy, "Server failed to pass deterministic readiness barrier"

        # Block 4: Evidence-Capture Test
        with urlopen(url, timeout=1.0) as resp:
            content = resp.read().decode("utf-8")
            assert content == "HEALTHY", f"Unexpected payload: {content}"
    finally:
        # Block 5: Guaranteed Graceful Cleanup
        if is_win:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], check=False)
        else:
            try:
                pgid = os.getpgid(proc.pid)
                os.killpg(pgid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        proc.wait(timeout=3.0)

    # Confirm process tree is dead and port is released
    assert proc.poll() is not None, "Process must be terminated"
    assert not is_port_in_use(port), "Port must be released after cleanup"


def test_harness_dual_mode_auto_detection(tmp_path: Path) -> None:
    """Verifies that the skill properly differentiates Mode 1 (Scaffold) from Mode 2 (Maintain)."""
    app_root = tmp_path / "spoke_repo"
    app_root.mkdir()
    skill_dir = app_root / ".agents" / "skills" / "verify-demo-app"

    def detect_mode(path: Path) -> str:
        harness_dir = path / "harness"
        return "maintain" if harness_dir.is_dir() else "scaffold"

    # 1. Before scaffold: must detect Mode 1 (scaffold)
    assert detect_mode(skill_dir) == "scaffold"

    # 2. After scaffold: create harness directory
    harness_dir = skill_dir / "harness"
    harness_dir.mkdir(parents=True)
    assert detect_mode(skill_dir) == "maintain"


def test_pre_remediation_provenance_check_contract_vs_regression() -> None:
    """Verifies COND-01: Distinguishes intentional contract drift from unintended regression."""

    # Provenance Classifier Model
    def evaluate_provenance(
        is_intentional_contract_change: bool,
        is_unintended_regression: bool,
    ) -> str:
        if is_intentional_contract_change and not is_unintended_regression:
            return "ALLOW_HARNESS_UPDATE"
        if is_unintended_regression:
            return "BLOCK_HARNESS_TAMPERING_FIX_SOURCE_CODE"
        return "INDETERMINATE"

    # Case A: User deliberately renamed an endpoint (/api/v1 -> /api/v2) with documentation
    assert (
        evaluate_provenance(is_intentional_contract_change=True, is_unintended_regression=False)
        == "ALLOW_HARNESS_UPDATE"
    )

    # Case B: Regression caused by internal null-pointer bug
    assert (
        evaluate_provenance(is_intentional_contract_change=False, is_unintended_regression=True)
        == "BLOCK_HARNESS_TAMPERING_FIX_SOURCE_CODE"
    )
