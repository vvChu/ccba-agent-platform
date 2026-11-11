#!/usr/bin/env python3
"""run_verify_tdd.py - 5-Block Deterministic Verification Harness for /ccba-tdd.

Implements the 5 core verification blocks per ADR-0009, ADR-0044, ADR-0057, and ADR-0058:
1. Clean-Slate Pre-flight (Port collision check & ccba-tdd target files readiness)
2. Dual-Mode Server Lifecycle (Process group isolation: setsid / CREATE_NEW_PROCESS_GROUP)
3. Deterministic Health Barrier (HTTP readiness probe polling without arbitrary sleep)
4. Evidence-Capture Test Suite (Pytest 7-feature contract suite & JSON evidence capture)
5. Guaranteed Graceful Cleanup (Process group termination in finally block)
"""

from __future__ import annotations

import argparse
import json
import os
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
    """Locates the repository root containing .agents/skills and pyproject.toml."""
    current = (start or Path(__file__).resolve()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").is_file() and (
            candidate / ".agents" / "skills" / "ccba-tdd" / "SKILL.md"
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


def clean_slate_preflight(port: int) -> None:
    """Block 1: Verifies that the target port is free and ccba-tdd covered_paths exist."""
    if is_port_in_use(port):
        raise RuntimeError(f"Clean-Slate Pre-flight failed: TCP port {port} is already in use.")

    required_files = (
        REPO_ROOT / ".agents" / "skills" / "ccba-tdd" / "SKILL.md",
        REPO_ROOT / ".agents" / "skills" / "ccba-tdd" / "references" / "tests.md",
        REPO_ROOT / ".agents" / "skills" / "ccba-tdd" / "references" / "mocking.md",
        REPO_ROOT / "scripts" / "spoke" / "sync" / "coordinator.py",
    )
    for req in required_files:
        if not req.is_file():
            raise RuntimeError(f"Clean-Slate Pre-flight failed: Missing covered file {req}")


def start_probe_server(port: int, workdir: Path) -> subprocess.Popen[bytes]:
    """Block 2: Starts an isolated readiness probe HTTP server in its own Process Group."""
    server_script = workdir / "_tdd_probe_server.py"
    server_script.write_text(
        f"""import http.server
class ProbeHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{{"status":"ok","skill":"ccba-tdd"}}')
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
    """Block 4: Executes the Pytest contract suite for ccba-tdd and captures JSON evidence."""
    test_file = harness_dir / "test_tdd_suite.py"
    env = os.environ.copy()
    extra_paths = f"{REPO_ROOT}{os.pathsep}{REPO_ROOT / 'packages' / 'ccba-harness' / 'src'}"
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{extra_paths}{os.pathsep}{existing}" if existing else extra_paths

    start_ms = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-q", "--tb=short"],
        cwd=str(REPO_ROOT),
        env=env,
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
            "app": "ccba-tdd",
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


def validate_tdd_cycle_transition(
    *,
    is_public_seam: bool,
    has_catches_and_misses_note: bool,
    cycle_count: int = 1,
    verify_patch_exit_code: int = 0,
) -> tuple[bool, str]:
    """Validates Seam Selection -> Red -> Green -> Refactor transitions for /ccba-tdd."""
    if not is_public_seam or not has_catches_and_misses_note:
        return (
            False,
            "PrivateInternalTestError: Must test at public seam with catches/misses tradeoff note",
        )
    if cycle_count > 5:
        return False, "LoopBudgetExhausted: Exceeded 5 Red-Green-Refactor cycles; commit WIP & halt"
    if verify_patch_exit_code != 0:
        return False, "HardLockBlocked: verify-patch --preset code exited non-zero"
    return True, "RefactorVerifiedGreen"


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
    """Checks that every FEAT-TDD-* entry in features/INDEX.md has a matching test in test_tdd_suite.py."""
    if not features_index.is_file() or not test_suite.is_file():
        return ["MISSING_INDEX_OR_SUITE"]
    index_text = features_index.read_text(encoding="utf-8")
    suite_text = test_suite.read_text(encoding="utf-8").lower()
    missing: list[str] = []
    for idx in range(1, 8):
        feat_id = f"FEAT-TDD-00{idx}"
        test_prefix = f"test_feat_tdd_00{idx}_"
        if feat_id not in index_text or test_prefix not in suite_text:
            missing.append(feat_id)
    return missing


def execute_verification_harness(evidence_out: Path | None = None) -> int:
    """Orchestrates all 5 blocks of the verify-ccba-tdd lifecycle."""
    port = find_free_port()
    clean_slate_preflight(port)

    with tempfile.TemporaryDirectory(prefix="verify_ccba_tdd_") as tmp_dir:
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
    """CLI entrypoint for verify-ccba-tdd runner."""
    parser = argparse.ArgumentParser(description="Run 5-block verification harness for /ccba-tdd.")
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
