#!/usr/bin/env python3
"""run_verify_ai.py - 5-Block Deterministic Verification Harness for package ccba-ai.

Implements the 5 core verification blocks per ADR-0009, ADR-0044, and ADR-0058:
1. Clean-Slate Pre-flight (Port collision check, covered_paths & ccba_ai import readiness)
2. Dual-Mode Server Lifecycle (Process group isolation: setsid / CREATE_NEW_PROCESS_GROUP)
3. Deterministic Health Barrier (HTTP readiness probe polling without arbitrary sleep)
4. Evidence-Capture Test Suite (Pytest 6-feature contract + Statechart bug_path replay)
5. Guaranteed Graceful Cleanup (Process group termination in finally block)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from urllib.request import urlopen


def find_repo_root(start: Path | None = None) -> Path:
    """Locates the repository root containing pyproject.toml and packages/ccba-ai."""
    current = (start or Path(__file__).resolve()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "packages" / "ccba-ai" / "src" / "ccba_ai" / "__init__.py"
        ).is_file():
            return candidate
    raise RuntimeError(f"Could not locate repository root from {current}")


HARNESS_DIR = Path(__file__).resolve().parent
REPO_ROOT = find_repo_root(HARNESS_DIR)


def find_free_port() -> int:
    """Finds an available local TCP port on 127.0.0.1."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def is_port_in_use(port: int) -> bool:
    """Checks whether a local TCP port is currently occupied."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def _build_pythonpath_env() -> dict[str, str]:
    """Builds environment with REPO_ROOT, ccba-ai/src, and ccba-harness/src on PYTHONPATH."""
    env = os.environ.copy()
    paths = [
        str(REPO_ROOT),
        str(REPO_ROOT / "packages" / "ccba-ai" / "src"),
        str(REPO_ROOT / "packages" / "ccba-harness" / "src"),
    ]
    existing = env.get("PYTHONPATH", "")
    extra = os.pathsep.join(paths)
    env["PYTHONPATH"] = f"{extra}{os.pathsep}{existing}" if existing else extra
    return env


def clean_slate_preflight(port: int) -> None:
    """Block 1: Verifies port availability, covered files, and ccba_ai clean import."""
    if is_port_in_use(port):
        raise RuntimeError(f"Clean-Slate Pre-flight failed: TCP port {port} is already in use.")

    required_files = (
        REPO_ROOT / "packages" / "ccba-ai" / "src" / "ccba_ai" / "__init__.py",
        REPO_ROOT / "packages" / "ccba-ai" / "src" / "ccba_ai" / "circuit_breaker.py",
        REPO_ROOT / "packages" / "ccba-ai" / "src" / "ccba_ai" / "fallback.py",
        REPO_ROOT / "packages" / "ccba-ai" / "src" / "ccba_ai" / "routing.py",
        REPO_ROOT / "packages" / "ccba-ai" / "src" / "ccba_ai" / "client.py",
        REPO_ROOT / ".agents" / "skills" / "ccba-ai-gateway-sdk" / "SKILL.md",
    )
    for req in required_files:
        if not req.is_file():
            raise RuntimeError(f"Clean-Slate Pre-flight failed: Missing covered file {req}")

    ping = subprocess.run(
        [sys.executable, "-c", "import ccba_ai; assert ccba_ai.CircuitBreaker is not None"],
        cwd=str(REPO_ROOT),
        env=_build_pythonpath_env(),
        capture_output=True,
        text=True,
        timeout=15.0,
    )
    if ping.returncode != 0:
        raise RuntimeError(f"ccba_ai pre-flight import failed: {ping.stderr}")


def start_probe_server(port: int, workdir: Path) -> subprocess.Popen[bytes]:
    """Block 2: Starts an isolated readiness probe HTTP server in its own Process Group."""
    server_script = workdir / "_ai_probe_server.py"
    server_script.write_text(
        f"""import http.server
class ProbeHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{{"status":"ok","package":"ccba-ai"}}')
    def log_message(self, *args):
        pass
http.server.HTTPServer(("127.0.0.1", {port}), ProbeHandler).serve_forever()
""",
        encoding="utf-8",
    )

    if sys.platform == "win32":
        flags = int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200))
        return subprocess.Popen(
            [sys.executable, str(server_script)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags,
        )
    return subprocess.Popen(
        [sys.executable, str(server_script)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid,
    )


def poll_readiness(url: str, timeout_seconds: float = 10.0, interval: float = 0.05) -> bool:
    """Block 3: Deterministically polls the readiness probe URL until HTTP 200 or timeout."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=0.5) as response:
                if response.status == 200:
                    return True
        except OSError:
            pass
        time.sleep(interval)
    return False


def run_evidence_test_suite(harness_dir: Path, evidence_out: Path | None = None) -> int:
    """Block 4: Executes the Pytest contract suite for ccba-ai and captures JSON evidence."""
    test_file = harness_dir / "test_ai_suite.py"
    start_ms = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-q", "--tb=short"],
        cwd=str(REPO_ROOT),
        env=_build_pythonpath_env(),
        capture_output=True,
        text=True,
        timeout=60.0,
    )
    duration_ms = round((time.perf_counter() - start_ms) * 1000.0, 2)

    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)

    if evidence_out is not None:
        evidence_out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "app": "ccba-ai",
            "exit_code": proc.returncode,
            "passed": proc.returncode == 0,
            "duration_ms": duration_ms,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
        evidence_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return proc.returncode


def cleanup_process_group(proc: subprocess.Popen[bytes]) -> None:
    """Block 5: Terminates the entire server process group safely inside a finally block."""
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            capture_output=True,
            check=False,
        )
    else:
        try:
            pgid = os.getpgid(proc.pid)
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    try:
        proc.wait(timeout=3.0)
    except subprocess.TimeoutExpired:
        proc.kill()


def classify_drift_status(
    *,
    env_blocked: bool,
    suite_passed: bool,
    contract_changed: bool,
    intentional_change: bool,
) -> str:
    """Classifies maintenance outcome into one of 4 canonical drift states."""
    if env_blocked:
        return "blocked"
    if not contract_changed and suite_passed:
        return "in_sync"
    if contract_changed and intentional_change and suite_passed:
        return "updated"
    return "bug"


def check_git_provenance(
    sync_commit: str,
    covered_paths: Sequence[str],
    expected_sha256: Mapping[str, str] | None = None,
) -> list[str]:
    """Verifies covered_paths via LF SHA-256 and reachable sync_commit (fail-closed)."""
    src_dir = str(REPO_ROOT / "packages" / "ccba-harness" / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    from ccba_harness.verifier import check_harness_git_provenance

    return check_harness_git_provenance(
        REPO_ROOT,
        sync_commit,
        covered_paths,
        expected_sha256=expected_sha256,
    )


def verify_surface_diff(features_index: Path, test_suite: Path) -> list[str]:
    """Checks that every FEAT-AI-* entry in features/INDEX.md has a matching test."""
    if not features_index.is_file() or not test_suite.is_file():
        return ["MISSING_INDEX_OR_SUITE"]
    index_text = features_index.read_text(encoding="utf-8")
    suite_text = test_suite.read_text(encoding="utf-8").lower()
    declared_ids = set(re.findall(r"FEAT-AI-\d{3}", index_text))
    expected_ids = {f"FEAT-AI-00{idx}" for idx in range(1, 7)}
    missing: list[str] = []
    for feat_id in sorted(declared_ids | expected_ids):
        suffix = feat_id.rsplit("-", 1)[-1].lower()
        if feat_id not in index_text or f"test_feat_ai_{suffix}_" not in suite_text:
            missing.append(feat_id)
    return missing


def execute_verification_harness(evidence_out: Path | None = None) -> int:
    """Orchestrates all 5 blocks of the verify-ccba-ai lifecycle."""
    port = find_free_port()
    clean_slate_preflight(port)

    with tempfile.TemporaryDirectory(prefix="verify_ccba_ai_") as tmp_dir:
        proc = start_probe_server(port, Path(tmp_dir))
        try:
            url = f"http://127.0.0.1:{port}/healthz"
            if not poll_readiness(url, timeout_seconds=10.0):
                print("ERROR: Deterministic Health Barrier timed out.", file=sys.stderr)
                return 1
            return run_evidence_test_suite(HARNESS_DIR, evidence_out=evidence_out)
        finally:
            cleanup_process_group(proc)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for verify-ccba-ai runner."""
    parser = argparse.ArgumentParser(description="Run 5-block verification harness for ccba-ai.")
    parser.add_argument(
        "--evidence-out",
        type=Path,
        default=None,
        help="Optional file path to write JSON verification evidence.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    return execute_verification_harness(evidence_out=args.evidence_out)


if __name__ == "__main__":
    sys.exit(main())
