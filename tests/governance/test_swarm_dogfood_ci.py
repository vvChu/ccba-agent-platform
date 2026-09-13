"""test_swarm_dogfood_ci.py - Fast CI Dogfood Stress Test for 3-Worker Swarm & Single-Writer Protocol.

Implements Wayfinder Ticket 3 / ADR-0053:
1. Simulates 3 concurrent Workers (Legal, MEP Water, Architecture/Alarm) writing to .system_generated/scratch/worker_{N}/.
2. Validates Single-Writer Protocol (ADR-0053) patch aggregation, dry-run, and collision detection.
3. Tests instant atomic rollback upon verification test failure.
4. Guaranteed execution time < 5.0 seconds for CI compatibility.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest
from scripts.governance.apply_worker_patch import (
    PatchBlock,
    execute_swarm_patches,
    load_patches_from_directory,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_3_worker_swarm_concurrent_clean_merge(tmp_path: Path) -> None:
    """Scenario 1: 3 workers (Legal, MEP, Arch) submit independent patches simultaneously.

    Verifies:
    - Patches in .system_generated/scratch/worker_{1,2,3}/ are aggregated.
    - 0 collisions detected.
    - Dry-run passes cleanly.
    - All 3 sections in report_registry.md are updated atomically.
    - Verification test passes.
    - Total execution time < 2.0s.
    """
    scratch_root = tmp_path / ".system_generated" / "scratch"
    w1_dir = scratch_root / "worker_1"
    w2_dir = scratch_root / "worker_2"
    w3_dir = scratch_root / "worker_3"
    w1_dir.mkdir(parents=True)
    w2_dir.mkdir(parents=True)
    w3_dir.mkdir(parents=True)

    # Base report file with 3 distinct placeholder seams
    registry_file = tmp_path / "report_registry.md"
    initial_registry_content = (
        "# BÁO CÁO THẨM TRA THIẾT KẾ ĐA BỘ MÔN (PCCC / MEP / KIẾN TRÚC)\n\n"
        "## PHẦN 1: PHÁP LÝ & QUY CHUẨN\n"
        "<!-- WORKER_1_FINDINGS -->\n\n"
        "## PHẦN 2: HỆ THỐNG CẤP NƯỚC CHỮA CHÁY & MEP\n"
        "<!-- WORKER_2_FINDINGS -->\n\n"
        "## PHẦN 3: BÁO CHÁY & THOÁT NẠN KIẾN TRÚC\n"
        "<!-- WORKER_3_FINDINGS -->\n"
    )
    registry_file.write_text(initial_registry_content, encoding="utf-8")

    # Worker 1: Legal & Specifications patch (Search-Replace format)
    patch_w1 = (
        "FILE: report_registry.md\n"
        "<<<<<<< SEARCH\n"
        "<!-- WORKER_1_FINDINGS -->\n"
        "=======\n"
        "- [CRITICAL] Thuyết minh thiếu căn cứ Luật Xây dựng 2025 và Nghị định 207/2026/NĐ-CP.\n"
        "- [HIGH] Bậc chịu lửa nhà xưởng F5 chưa đối soát theo Bảng H.3 QCVN 06:2022/BXD.\n"
        ">>>>>>> REPLACE\n"
    )
    (w1_dir / "worker_1_legal.patch").write_text(patch_w1, encoding="utf-8")

    # Worker 2: MEP Water patch (Search-Replace format)
    patch_w2 = (
        "FILE: report_registry.md\n"
        "<<<<<<< SEARCH\n"
        "<!-- WORKER_2_FINDINGS -->\n"
        "=======\n"
        "- [CRITICAL] Dung tích bể nước ngầm B2 bản vẽ ghi 420 m3, thiếu 30 m3 so với Thuyết minh 450 m3.\n"
        "- [HIGH] Cột áp bơm chữa cháy chính EP-01 chênh lệch: Thuyết minh H=95m, bản vẽ ghi H=90m.\n"
        ">>>>>>> REPLACE\n"
    )
    (w2_dir / "worker_2_mep.diff").write_text(patch_w2, encoding="utf-8")

    # Worker 3: Architecture & Alarm patch (JSON manifest format)
    patch_w3_manifest = [
        {
            "file": "report_registry.md",
            "search": "<!-- WORKER_3_FINDINGS -->",
            "replace": (
                "- [CRITICAL] Tường bao gian lánh nạn tầng 10 ghi EI 90 thay vì REI 150 theo Mục A.3.2 QCVN 06.\n"
                "- [HIGH] Đầu báo khói FA-SD-0312 cách miệng gió hồi điều hòa 400mm, vi phạm TCVN 5738:2021."
            ),
        }
    ]
    (w3_dir / "worker_3_arch.json").write_text(json.dumps(patch_w3_manifest), encoding="utf-8")

    # Single-Writer loads patches from entire scratch tree
    patches = load_patches_from_directory(scratch_root)
    assert len(patches) == 3

    verify_cmd = f'"{sys.executable}" -c "print(\'Swarm QC Dogfood Verification Passed\')"'

    t0 = time.perf_counter()
    report = execute_swarm_patches(
        patches=patches,
        base_dir=tmp_path,
        apply=True,
        verify=True,
        verify_commands=[verify_cmd],
    )
    duration = time.perf_counter() - t0

    # Assertions
    assert report.success is True
    assert report.patches_count == 3
    assert len(report.collisions) == 0
    assert len(report.dry_run_errors) == 0
    assert set(report.applied_files) == {"report_registry.md"}
    assert report.semantic_conflict is False
    assert report.rollback_performed is False
    assert duration < 5.0  # Must be fast in CI

    # Check that disk content has all 3 findings seamlessly merged
    updated_content = registry_file.read_text(encoding="utf-8")
    assert "Luật Xây dựng 2025" in updated_content
    assert "Dung tích bể nước ngầm B2" in updated_content
    assert "REI 150 theo Mục A.3.2" in updated_content
    assert "<!-- WORKER_1_FINDINGS -->" not in updated_content
    assert "<!-- WORKER_2_FINDINGS -->" not in updated_content
    assert "<!-- WORKER_3_FINDINGS -->" not in updated_content


def test_3_worker_swarm_syntactic_collision_rejection(tmp_path: Path) -> None:
    """Scenario 2: Worker 1 and Worker 2 collide on the same line; Worker 3 touches independent seam.

    Verifies:
    - Collision is detected before any disk write.
    - Report fails with collisions listed.
    - Zero files on disk are modified.
    """
    code_file = tmp_path / "qc_pipeline.py"
    initial_code = (
        "def audit_fire_rating():\n"
        "    rating = 'REI 60'\n"
        "    return rating\n"
    )
    code_file.write_text(initial_code, encoding="utf-8")

    doc_file = tmp_path / "notes.md"
    doc_file.write_text("TODO: Audit notes\n", encoding="utf-8")

    # Worker 1 wants to upgrade rating to REI 120
    p_w1 = PatchBlock(
        file_path="qc_pipeline.py",
        search_content="    rating = 'REI 60'",
        replace_content="    rating = 'REI 120'",
        source_patch="worker_1_legal",
    )
    # Worker 2 wants to upgrade rating to REI 150 (direct collision with Worker 1!)
    p_w2 = PatchBlock(
        file_path="qc_pipeline.py",
        search_content="    rating = 'REI 60'",
        replace_content="    rating = 'REI 150'",
        source_patch="worker_2_mep",
    )
    # Worker 3 touches independent file notes.md
    p_w3 = PatchBlock(
        file_path="notes.md",
        search_content="TODO: Audit notes",
        replace_content="DONE: Audit notes completed",
        source_patch="worker_3_arch",
    )

    report = execute_swarm_patches(
        patches=[p_w1, p_w2, p_w3],
        base_dir=tmp_path,
        apply=True,
        verify=False,
    )

    assert report.success is False
    assert len(report.collisions) >= 1
    assert "worker_1_legal" in report.collisions[0]
    assert "worker_2_mep" in report.collisions[0]
    assert report.rollback_performed is False

    # Disk files must remain completely untouched
    assert code_file.read_text(encoding="utf-8") == initial_code
    assert doc_file.read_text(encoding="utf-8") == "TODO: Audit notes\n"


def test_3_worker_swarm_semantic_conflict_atomic_rollback(tmp_path: Path) -> None:
    """Scenario 3: 3 workers modify 3 different files cleanly, but Worker 2 introduces a runtime error.

    Verifies:
    - Dry-run succeeds and files are written to disk.
    - Verification gate command fails (exit code != 0).
    - Single-Writer detects semantic conflict and executes full snapshot rollback.
    - All 3 files are 100% restored to their pre-patch states.
    """
    f_config = tmp_path / "config.py"
    f_config.write_text("MAX_RETRIES = 3\n", encoding="utf-8")

    f_service = tmp_path / "service.py"
    f_service.write_text("def run():\n    return 'OK'\n", encoding="utf-8")

    f_doc = tmp_path / "README.md"
    f_doc.write_text("# Project Docs\n", encoding="utf-8")

    # Worker 1: updates config cleanly
    p_w1 = PatchBlock(
        file_path="config.py",
        search_content="MAX_RETRIES = 3",
        replace_content="MAX_RETRIES = 5",
        source_patch="worker_1",
    )
    # Worker 2: inserts broken runtime logic
    p_w2 = PatchBlock(
        file_path="service.py",
        search_content="return 'OK'",
        replace_content="raise RuntimeError('PCCC Pipeline Assertion Failed!')",
        source_patch="worker_2",
    )
    # Worker 3: updates README cleanly
    p_w3 = PatchBlock(
        file_path="README.md",
        search_content="# Project Docs",
        replace_content="# Project Docs (Audited v2)",
        source_patch="worker_3",
    )

    # Verification command that attempts to execute service.py
    verify_cmd = f'"{sys.executable}" -c "import service; service.run()"'

    report = execute_swarm_patches(
        patches=[p_w1, p_w2, p_w3],
        base_dir=tmp_path,
        apply=True,
        verify=True,
        verify_commands=[verify_cmd],
    )

    assert report.success is False
    assert report.semantic_conflict is True
    assert report.rollback_performed is True
    assert len(report.verification_errors) >= 1
    assert any("RuntimeError" in err or "PCCC Pipeline Assertion Failed" in err or "exit" in err for err in report.verification_errors)

    # Verify 100% restoration to initial contents
    assert f_config.read_text(encoding="utf-8") == "MAX_RETRIES = 3\n"
    assert f_service.read_text(encoding="utf-8") == "def run():\n    return 'OK'\n"
    assert f_doc.read_text(encoding="utf-8") == "# Project Docs\n"


def test_load_patches_from_multi_worker_scratch(tmp_path: Path) -> None:
    """Verify recursive scanning and loading from 3 separate worker directories."""
    scratch = tmp_path / ".system_generated" / "scratch"
    for i in (1, 2, 3):
        wdir = scratch / f"worker_{i}"
        wdir.mkdir(parents=True)
        patch_content = (
            f"FILE: module_{i}.py\n"
            f"<<<<<<< SEARCH\n"
            f"val = {i}\n"
            f"=======\n"
            f"val = {i * 10}\n"
            f">>>>>>> REPLACE\n"
        )
        (wdir / f"patch_{i}.patch").write_text(patch_content, encoding="utf-8")

    patches = load_patches_from_directory(scratch)
    assert len(patches) == 3
    sources = {p.source_patch for p in patches}
    assert sources == {"patch_1.patch", "patch_2.patch", "patch_3.patch"}
    target_files = {p.file_path for p in patches}
    assert target_files == {"module_1.py", "module_2.py", "module_3.py"}
