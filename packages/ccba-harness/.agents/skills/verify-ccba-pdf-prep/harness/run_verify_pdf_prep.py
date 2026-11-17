#!/usr/bin/env python3
"""run_verify_pdf_prep.py - Profile B In-Process 5-Block Verification Harness for ccba-pdf-prep.

Implements the 5 core verification blocks in Profile B (in-process library mode, zero HTTP server):
1. Clean-Slate Pre-flight (covered_paths & module existence check)
2. In-Process Sandbox Isolation (TemporaryDirectory, PYTHONPATH, PYMUPDF_MESSAGE=fd:2)
3. Deterministic Seam Import Barrier (clean subprocess import of ccba_pdf_prep public seams)
4. Evidence-Capture Test Suite (Pytest 6-feature contract + 4 live bug_path replays)
5. Guaranteed Workspace Cleanup (finally cleanup of temporary sandbox)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping, Sequence
from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    """Locate the repository root containing pyproject.toml and packages/ccba-pdf-prep."""
    current = (start or Path(__file__).resolve()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "packages" / "ccba-pdf-prep" / "src" / "ccba_pdf_prep" / "__init__.py"
        ).is_file():
            return candidate
    raise RuntimeError(f"Could not locate repository root from {current}")


HARNESS_DIR = Path(__file__).resolve().parent
REPO_ROOT = find_repo_root(HARNESS_DIR)


def _build_sandbox_env(tmp_dir: Path) -> dict[str, str]:
    """Build isolated environment with monorepo package sources and PyMuPDF stderr isolation."""
    env = os.environ.copy()
    paths = [
        str(REPO_ROOT),
        str(REPO_ROOT / "packages" / "ccba-pdf-prep" / "src"),
        str(REPO_ROOT / "packages" / "ccba-harness" / "src"),
    ]
    existing = env.get("PYTHONPATH", "")
    extra = os.pathsep.join(paths)
    env["PYTHONPATH"] = f"{extra}{os.pathsep}{existing}" if existing else extra
    env["PYMUPDF_MESSAGE"] = "fd:2"
    env["CCBA_PDF_PREP_SANDBOX"] = str(tmp_dir)
    return env


def clean_slate_preflight() -> None:
    """Block 1: Verify all covered ccba-pdf-prep files exist on disk."""
    pkg_dir = REPO_ROOT / "packages" / "ccba-pdf-prep" / "src" / "ccba_pdf_prep"
    required = (
        pkg_dir / "__init__.py",
        pkg_dir / "pipeline.py",
        pkg_dir / "core.py",
        pkg_dir / "vision.py",
        pkg_dir / "detector.py",
    )
    for req in required:
        if not req.is_file():
            raise RuntimeError(f"Clean-Slate Pre-flight failed: Missing {req}")


def verify_seam_import_barrier(env: Mapping[str, str]) -> None:
    """Block 3: Deterministically verify ccba_pdf_prep public seam loading in clean interpreter."""
    probe_code = (
        "import ccba_pdf_prep as p; "
        "assert all(hasattr(p, s) for s in ('PDFProcessingPipeline', 'ProcessingResult', "
        "'PDFProcessingError', 'PDFReport', 'PDFCategory', 'render_page_to_image', 'get_pdf_page_count'))"
    )
    proc = subprocess.run(
        [sys.executable, "-c", probe_code],
        cwd=str(REPO_ROOT),
        env=dict(env),
        capture_output=True,
        text=True,
        timeout=15.0,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Seam Import Barrier failed: {proc.stderr.strip()}")


def run_evidence_test_suite(
    harness_dir: Path, env: Mapping[str, str], evidence_out: Path | None = None
) -> int:
    """Block 4: Execute the Pytest contract suite and optionally write JSON evidence."""
    test_file = harness_dir / "test_pdf_prep_suite.py"
    start_ms = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-q", "--tb=short"],
        cwd=str(REPO_ROOT),
        env=dict(env),
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
            "app": "ccba-pdf-prep",
            "profile": "in-process-library",
            "exit_code": proc.returncode,
            "passed": proc.returncode == 0,
            "duration_ms": duration_ms,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
        evidence_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return proc.returncode


def classify_drift_status(
    *,
    env_blocked: bool,
    suite_passed: bool,
    contract_changed: bool,
    intentional_change: bool,
) -> str:
    """Classify maintenance outcome into one of 4 canonical drift states."""
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
    """Verify covered_paths via LF SHA-256 and reachable sync_commit (fail-closed)."""
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
    """Check that every FEAT-PDF-* entry in features/INDEX.md has a matching test."""
    if not features_index.is_file() or not test_suite.is_file():
        return ["MISSING_INDEX_OR_SUITE"]
    index_text = features_index.read_text(encoding="utf-8")
    suite_text = test_suite.read_text(encoding="utf-8").lower()
    declared_ids = set(re.findall(r"FEAT-PDF-\d{3}", index_text))
    expected_ids = {f"FEAT-PDF-00{idx}" for idx in range(1, 7)}
    missing: list[str] = []
    for feat_id in sorted(declared_ids | expected_ids):
        suffix = feat_id.rsplit("-", 1)[-1].lower()
        if feat_id not in index_text or f"test_feat_pdf_{suffix}_" not in suite_text:
            missing.append(feat_id)
    return missing


def execute_verification_harness(evidence_out: Path | None = None) -> int:
    """Orchestrate all 5 Profile-B in-process blocks of verify-ccba-pdf-prep."""
    clean_slate_preflight()
    with tempfile.TemporaryDirectory(prefix="verify_ccba_pdf_prep_") as tmp_dir:
        sandbox_path = Path(tmp_dir)
        env = _build_sandbox_env(sandbox_path)
        verify_seam_import_barrier(env)
        return run_evidence_test_suite(HARNESS_DIR, env, evidence_out=evidence_out)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for verify-ccba-pdf-prep runner."""
    parser = argparse.ArgumentParser(
        description="Run Profile B 5-block verification harness for ccba-pdf-prep."
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
