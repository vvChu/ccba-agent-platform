#!/usr/bin/env python3
"""run_verify_wayfinder.py - 5-Block Deterministic Verification Harness for /ccba-wayfinder.

Implements the 5 core verification blocks per ADR-0009, ADR-0044, ADR-0057, and ADR-0058:
1. Clean-Slate Pre-flight (Port collision check & ccba-wayfinder target files readiness)
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
    """Locates the repository root containing .agents/skills and pyproject.toml.

    Args:
        start: Starting directory path.

    Returns:
        Path: Resolved repository root path.
    """
    current = (start or Path(__file__).resolve()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").is_file() and (
            candidate / ".agents" / "skills" / "ccba-wayfinder" / "SKILL.md"
        ).is_file():
            return candidate
    raise RuntimeError(f"Could not locate repository root from {current}")


HARNESS_DIR = Path(__file__).resolve().parent
REPO_ROOT = find_repo_root(HARNESS_DIR)


def find_free_port() -> int:
    """Finds an available local TCP port on 127.0.0.1.

    Returns:
        int: Available ephemeral TCP port number.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def is_port_in_use(port: int) -> bool:
    """Checks whether a local TCP port is currently occupied.

    Args:
        port: Local TCP port number to probe.

    Returns:
        bool: True if a process is listening on 127.0.0.1:port, False otherwise.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def clean_slate_preflight(port: int) -> None:
    """Block 1: Verifies that the target port is free and ccba-wayfinder covered_paths exist.

    Args:
        port: Target TCP port for the readiness probe server.

    Raises:
        RuntimeError: If the target port is occupied or required files are missing.
    """
    if is_port_in_use(port):
        raise RuntimeError(f"Clean-Slate Pre-flight failed: TCP port {port} is already in use.")

    required_files = (
        REPO_ROOT / ".agents" / "skills" / "ccba-wayfinder" / "SKILL.md",
        REPO_ROOT
        / "packages"
        / "ccba-harness"
        / "src"
        / "ccba_harness"
        / "evals"
        / "simulators"
        / "platform_tooling.py",
        REPO_ROOT
        / "packages"
        / "ccba-harness"
        / "src"
        / "ccba_harness"
        / "evals"
        / "archetypes_catalog.yaml",
        REPO_ROOT / "scripts" / "spoke" / "sync" / "coordinator.py",
    )
    for req in required_files:
        if not req.is_file():
            raise RuntimeError(f"Clean-Slate Pre-flight failed: Missing covered file {req}")


def start_probe_server(port: int, workdir: Path) -> subprocess.Popen[bytes]:
    """Block 2: Starts an isolated readiness probe HTTP server in its own Process Group.

    Args:
        port: Local TCP port to bind.
        workdir: Temporary directory to store the ephemeral server script.

    Returns:
        subprocess.Popen[bytes]: Handle to the spawned server process group.
    """
    server_script = workdir / "_wayfinder_probe_server.py"
    server_script.write_text(
        f"""import http.server
class ProbeHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{{"status":"ok","skill":"ccba-wayfinder"}}')
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
    """Block 3: Deterministically polls the readiness probe URL until HTTP 200 or timeout.

    Args:
        url: HTTP readiness endpoint URL.
        timeout_seconds: Maximum bounded wait duration in seconds.
        interval: Poll interval in seconds.

    Returns:
        bool: True if the endpoint returned HTTP 200 within timeout, False otherwise.
    """
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
    """Block 4: Executes the Pytest contract suite for ccba-wayfinder and captures JSON evidence.

    Args:
        harness_dir: Directory containing test_wayfinder_suite.py.
        evidence_out: Optional path to write JSON execution evidence.

    Returns:
        int: Process exit code from the test suite (0 if all tests pass).
    """
    test_file = harness_dir / "test_wayfinder_suite.py"
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
            "app": "ccba-wayfinder",
            "exit_code": proc.returncode,
            "passed": proc.returncode == 0,
            "duration_ms": duration_ms,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
        evidence_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return proc.returncode


def cleanup_process_group(proc: subprocess.Popen[bytes]) -> None:
    """Block 5: Terminates the entire server process group safely inside a finally block.

    Args:
        proc: Subprocess handle for the probe server.
    """
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
    """Classifies maintenance outcome into one of 4 canonical drift states (COND-01).

    Args:
        env_blocked: True if environment or infrastructure prevented execution.
        suite_passed: True if the verification harness exited with code 0.
        contract_changed: True if covered_paths changed since sync_commit.
        intentional_change: True if contract change is backed by ADR/PR/commit intent.

    Returns:
        str: One of 'in_sync', 'updated', 'bug', or 'blocked'.
    """
    if env_blocked:
        return "blocked"
    if not contract_changed and suite_passed:
        return "in_sync"
    if contract_changed and intentional_change and suite_passed:
        return "updated"
    return "bug"


def validate_wayfinder_map_sections(map_markdown: str) -> list[str]:
    """Validates that a Wayfinding Map contains all 5 mandatory structural sections.

    Args:
        map_markdown: Markdown text of a Wayfinding Map.

    Returns:
        list[str]: Missing canonical section names (empty list if valid).
    """
    required_sections = (
        "Destination",
        "Notes",
        "Decisions",
        "Not Yet Specified",
        "Out of Scope",
    )
    lower_text = map_markdown.lower()
    missing: list[str] = []
    for sec in required_sections:
        if sec.lower() not in lower_text:
            missing.append(sec)
    return missing


def classify_fog_or_ticket(*, has_sharp_question: bool, is_blocked: bool = False) -> str:
    """Applies the Fog vs. Ticket Test from /ccba-wayfinder.

    Args:
        has_sharp_question: True if the question can be stated sharply and precisely.
        is_blocked: True if the question depends on another open ticket.

    Returns:
        str: 'CREATE_TICKET' if sharp question exists (even if blocked), else 'NOT_YET_SPECIFIED'.
    """
    if has_sharp_question:
        return "CREATE_TICKET_BLOCKED" if is_blocked else "CREATE_TICKET_FRONTIER"
    return "NOT_YET_SPECIFIED"


def validate_ticket_execution_transition(
    *,
    has_fog: bool,
    assignee_claimed: bool,
    tickets_in_session: int,
) -> tuple[bool, str]:
    """Validates Wayfinder workflow state transitions and detects bug-path violations.

    Args:
        has_fog: True if the problem has unresolved fog requiring a Wayfinding Map.
        assignee_claimed: True if the agent claimed Assignee on the ticket before working.
        tickets_in_session: Number of tickets worked in the current session.

    Returns:
        tuple[bool, str]: (is_valid_transition, target_state_or_reason).
    """
    if not has_fog:
        return (
            False,
            "DirectExecutionHandoff: zero_fog_detected -> use /ccba-implement or /ccba-tdd",
        )
    if not assignee_claimed:
        return False, "RaceConditionCollision: worked_without_assignee_claim"
    if tickets_in_session > 1:
        return False, "SessionOverload: exceeded 1 ticket per ~100K token session"
    return True, "TicketResolved"


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
    """Checks that every FEAT-WF-* entry in features/INDEX.md has a matching test in test_wayfinder_suite.py.

    Args:
        features_index: Path to features/INDEX.md.
        test_suite: Path to test_wayfinder_suite.py.

    Returns:
        list[str]: Missing feature IDs not covered by the test suite.
    """
    if not features_index.is_file() or not test_suite.is_file():
        return ["MISSING_INDEX_OR_SUITE"]
    index_text = features_index.read_text(encoding="utf-8")
    suite_text = test_suite.read_text(encoding="utf-8").lower()
    missing: list[str] = []
    for idx in range(1, 8):
        feat_id = f"FEAT-WF-00{idx}"
        test_prefix = f"test_feat_wf_00{idx}_"
        if feat_id not in index_text or test_prefix not in suite_text:
            missing.append(feat_id)
    return missing


def execute_verification_harness(evidence_out: Path | None = None) -> int:
    """Orchestrates all 5 blocks of the verify-ccba-wayfinder lifecycle.

    Args:
        evidence_out: Optional path to write structured JSON evidence.

    Returns:
        int: 0 if all 5 blocks succeed, non-zero otherwise.
    """
    port = find_free_port()
    clean_slate_preflight(port)

    with tempfile.TemporaryDirectory(prefix="verify_ccba_wayfinder_") as tmp_dir:
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
    """CLI entrypoint for verify-ccba-wayfinder runner.

    Args:
        argv: Optional sequence of command-line arguments.

    Returns:
        int: Exit code (0 on pass, non-zero on failure).
    """
    parser = argparse.ArgumentParser(
        description="Run 5-block verification harness for /ccba-wayfinder."
    )
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
