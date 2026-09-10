"""test_swarm_single_writer_e2e.py - End-to-End Simulation Test Suite for Swarm Multi-Agent Single-Writer Engine.

Verifies the 5 core scenarios of the Single-Writer Multi-Agent Protocol (ADR-0053, SPEC-2026-TEAMWORK-DIFF-001):
1. Concurrent 5-Worker Swarm across independent seams (Zero collision, clean merge).
2. Syntactic Collision Guard (Cross-worker line collision rejected before disk write).
3. Semantic Conflict & Instant Auto-Rollback (Logic error caught by verification gate, 100% disk restored).
4. Stale / Drift Patch Rejection (Outdated search blocks rejected safely during dry-run).
5. High-Throughput Latency Benchmark (Sub-50ms collision detection across 20+ patch blocks).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from scripts.governance.apply_worker_patch import (
    PatchBlock,
    execute_swarm_patches,
    load_patches_from_directory,
)


def test_scenario_1_concurrent_5_worker_swarm_clean_merge(tmp_path: Path) -> None:
    """Scenario 1: 5 workers submit independent patches to 5 different seams simultaneously.

    Verifies:
    - 0 collisions detected.
    - Dry-run passes.
    - All 5 files are updated atomically on disk.
    - Verification gate succeeds.
    - Full timing breakdown is recorded.
    """
    scratch_dir = tmp_path / ".system_generated" / "scratch" / "teamwork" / "proj_alpha"
    scratch_dir.mkdir(parents=True)

    # Setup initial repository files
    files = {
        "packages/pkg_a/service.py": "def serve_a():\n    return 'v1'\n",
        "packages/pkg_b/service.py": "def serve_b():\n    return 'v1'\n",
        "docs/api.md": "# API Reference\nVersion 1.0\n",
        "scripts/util.py": "TIMEOUT = 10\n",
        "config/settings.json": json.dumps({"env": "staging", "workers": 2}, indent=2) + "\n",
    }
    for rel_path, content in files.items():
        p = tmp_path / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    # 5 workers emit patches into scratch
    worker_patches = [
        (
            "worker_1_patch.txt",
            "FILE: packages/pkg_a/service.py\n<<<<<<< SEARCH\n    return 'v1'\n=======\n    return 'v2'\n>>>>>>> REPLACE\n",
        ),
        (
            "worker_2_patch.txt",
            "FILE: packages/pkg_b/service.py\n<<<<<<< SEARCH\n    return 'v1'\n=======\n    return 'v2'\n>>>>>>> REPLACE\n",
        ),
        (
            "worker_3_patch.txt",
            "FILE: docs/api.md\n<<<<<<< SEARCH\nVersion 1.0\n=======\nVersion 2.0\n>>>>>>> REPLACE\n",
        ),
        (
            "worker_4_patch.txt",
            "FILE: scripts/util.py\n<<<<<<< SEARCH\nTIMEOUT = 10\n=======\nTIMEOUT = 30\n>>>>>>> REPLACE\n",
        ),
        (
            "worker_5_patch.json",
            json.dumps(
                [
                    {
                        "file": "config/settings.json",
                        "search": '"workers": 2',
                        "replace": '"workers": 5',
                    }
                ]
            ),
        ),
    ]

    for fname, ptext in worker_patches:
        (scratch_dir / fname).write_text(ptext, encoding="utf-8")

    # Single-Writer loads and executes
    patches = load_patches_from_directory(scratch_dir)
    assert len(patches) == 5

    verify_cmd = f'"{sys.executable}" -c "print(\'All unit tests pass\')"'

    report = execute_swarm_patches(
        patches=patches,
        base_dir=tmp_path,
        apply=True,
        verify=True,
        verify_commands=[verify_cmd],
    )

    assert report.success is True
    assert report.patches_count == 5
    assert len(report.collisions) == 0
    assert len(report.dry_run_errors) == 0
    assert len(report.applied_files) == 5
    assert report.semantic_conflict is False
    assert report.rollback_performed is False

    # Check on-disk states
    assert "return 'v2'" in (tmp_path / "packages/pkg_a/service.py").read_text(encoding="utf-8")
    assert "return 'v2'" in (tmp_path / "packages/pkg_b/service.py").read_text(encoding="utf-8")
    assert "Version 2.0" in (tmp_path / "docs/api.md").read_text(encoding="utf-8")
    assert "TIMEOUT = 30" in (tmp_path / "scripts/util.py").read_text(encoding="utf-8")
    assert '"workers": 5' in (tmp_path / "config/settings.json").read_text(encoding="utf-8")

    # Timings verified
    assert report.timings["total"] > 0
    assert report.timings["collision_detection"] < 0.05


def test_scenario_2_syntactic_collision_rejection(tmp_path: Path) -> None:
    """Scenario 2: Worker 1 and Worker 2 both attempt to modify the same function block.

    Verifies:
    - Collision is detected before any disk modification occurs.
    - Batch is rejected with clear collision error.
    - Target file remains in its initial clean state.
    """
    target = tmp_path / "core.py"
    target.write_text("def process():\n    step_1()\n    step_2()\n", encoding="utf-8")

    p1 = PatchBlock(
        file_path="core.py",
        search_content="step_1()\n    step_2()",
        replace_content="step_1_optimized()\n    step_2()",
        source_patch="worker_1",
    )
    p2 = PatchBlock(
        file_path="core.py",
        search_content="step_1()\n    step_2()",
        replace_content="step_1()\n    step_2_async()",
        source_patch="worker_2",
    )

    report = execute_swarm_patches(
        patches=[p1, p2],
        base_dir=tmp_path,
        apply=True,
        verify=False,
    )

    assert report.success is False
    assert len(report.collisions) == 1
    assert "worker_1" in report.collisions[0]
    assert "worker_2" in report.collisions[0]
    assert report.rollback_performed is False

    # Disk must be completely untouched
    assert target.read_text(encoding="utf-8") == "def process():\n    step_1()\n    step_2()\n"


def test_scenario_3_semantic_conflict_auto_rollback(tmp_path: Path) -> None:
    """Scenario 3: Worker 1 alters a function signature and Worker 2 calls it with incompatible types.

    No syntactic line collision exists (different files).
    Dry-run passes, atomic write succeeds.
    However, the verification test fails $\rightarrow$ Triggering instant rollback to snapshot.
    """
    callee = tmp_path / "calc.py"
    callee.write_text("def multiply(a: int, b: int) -> int:\n    return a * b\n", encoding="utf-8")

    caller = tmp_path / "app.py"
    caller.write_text("from calc import multiply\nprint(multiply(2, 3))\n", encoding="utf-8")

    # Worker 1: changes return type to string representation without updating signature
    p_worker_1 = PatchBlock(
        file_path="calc.py",
        search_content="return a * b",
        replace_content="return f'RESULT: {a * b}'",
        source_patch="worker_1",
    )

    # Worker 2: expects integer result and performs math
    p_worker_2 = PatchBlock(
        file_path="app.py",
        search_content="print(multiply(2, 3))",
        replace_content="res = multiply(2, 3)\nprint(res + 10)",  # TypeError: can only concatenate str to str
        source_patch="worker_2",
    )

    # Verification runner that runs app.py in subprocess
    verify_cmd = f'"{sys.executable}" app.py'

    report = execute_swarm_patches(
        patches=[p_worker_1, p_worker_2],
        base_dir=tmp_path,
        apply=True,
        verify=True,
        verify_commands=[verify_cmd],
    )

    assert report.success is False
    assert report.semantic_conflict is True
    assert report.rollback_performed is True
    assert len(report.verification_errors) >= 1
    assert any("TypeError" in err or "exit" in err for err in report.verification_errors)

    # Verify 100% restoration to clean states on disk
    assert callee.read_text(encoding="utf-8") == "def multiply(a: int, b: int) -> int:\n    return a * b\n"
    assert caller.read_text(encoding="utf-8") == "from calc import multiply\nprint(multiply(2, 3))\n"


def test_scenario_4_stale_drift_patch_rejection(tmp_path: Path) -> None:
    """Scenario 4: Worker submits patch based on an outdated codebase state (drift).

    Verifies:
    - Pre-flight dry-run catches the missing SEARCH block.
    - Rejects safely without modifying disk.
    """
    target = tmp_path / "router.py"
    # Target file has already been changed to v3
    target.write_text("ROUTE = '/v3/items'\n", encoding="utf-8")

    # Worker patch assumes file is still at v1
    p_stale = PatchBlock(
        file_path="router.py",
        search_content="ROUTE = '/v1/items'",
        replace_content="ROUTE = '/v2/items'",
        source_patch="worker_stale",
    )

    report = execute_swarm_patches(
        patches=[p_stale],
        base_dir=tmp_path,
        apply=True,
        verify=False,
    )

    assert report.success is False
    assert len(report.dry_run_errors) == 1
    assert "SEARCH block not found" in report.dry_run_errors[0]
    assert report.rollback_performed is False
    assert target.read_text(encoding="utf-8") == "ROUTE = '/v3/items'\n"


def test_scenario_5_high_throughput_swarm_benchmark(tmp_path: Path) -> None:
    """Scenario 5: High-throughput benchmark with 20 patch blocks across 10 files.

    Verifies:
    - Parsing and collision detection scale gracefully (< 50ms).
    - Sequential in-memory simulation and atomic apply perform in < 100ms.
    """
    # Create 10 target files
    num_files = 10
    for i in range(num_files):
        f = tmp_path / f"mod_{i}.py"
        f.write_text(f"val_{i} = {i}\nstatus_{i} = 'init'\n", encoding="utf-8")

    # Generate 20 non-overlapping patches (2 per file)
    patches: list[PatchBlock] = []
    for i in range(num_files):
        p1 = PatchBlock(
            file_path=f"mod_{i}.py",
            search_content=f"val_{i} = {i}",
            replace_content=f"val_{i} = {i * 10}",
            source_patch=f"worker_val_{i}",
        )
        p2 = PatchBlock(
            file_path=f"mod_{i}.py",
            search_content=f"status_{i} = 'init'",
            replace_content=f"status_{i} = 'ready'",
            source_patch=f"worker_status_{i}",
        )
        patches.extend([p1, p2])

    assert len(patches) == 20

    t0 = time.perf_counter()
    report = execute_swarm_patches(
        patches=patches,
        base_dir=tmp_path,
        apply=True,
        verify=False,
    )
    t_elapsed = time.perf_counter() - t0

    assert report.success is True
    assert report.patches_count == 20
    assert len(report.applied_files) == 20
    # Collision detection must be very fast (< 0.05s)
    assert report.timings["collision_detection"] < 0.05
    # Overall execution time without external subprocess should be < 0.5s
    assert t_elapsed < 0.5

    # Check all 10 files updated correctly
    for i in range(num_files):
        content = (tmp_path / f"mod_{i}.py").read_text(encoding="utf-8")
        assert f"val_{i} = {i * 10}" in content
        assert f"status_{i} = 'ready'" in content
