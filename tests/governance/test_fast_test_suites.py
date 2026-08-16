"""test_fast_test_suites.py - Automated SLA Governance Verification for Isolated Fast Test Suites.

Verifies that:
1. Every package in `packages/` has a registered fast test suite.
2. Running the fast suite via `run_isolated_test(..., fast_mode=True)` executes and succeeds.
3. The isolated execution finishes within the SLA threshold (< 5.0s process wall clock).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.eval.run_isolated_tests import discover_test_targets, run_isolated_test

pytestmark = [pytest.mark.integration]


def test_discover_test_targets_includes_all_packages() -> None:
    """Verify discover_test_targets finds all core packages."""
    targets = discover_test_targets(PROJECT_ROOT)
    expected_packages = [
        "ccba-ai",
        "ccba-harness",
        "ccba-legal-intel",
        "ccba-maskara",
        "ccba-notebooklm",
        "ccba-ooxml",
        "ccba-pdf-prep",
        "mdconverter",
    ]
    for pkg in expected_packages:
        assert pkg in targets, f"Package {pkg} must have a discoverable test suite"


@pytest.mark.parametrize(
    "pkg_name",
    [
        "ccba-ai",
        "ccba-harness",
        "ccba-legal-intel",
        "ccba-maskara",
        "ccba-notebooklm",
        "ccba-ooxml",
        "ccba-pdf-prep",
        "mdconverter",
    ],
)
def test_isolated_package_fast_suite_sla(pkg_name: str) -> None:
    """Verify that each package's isolated fast test suite passes within SLA limits."""
    targets = discover_test_targets(PROJECT_ROOT)
    assert pkg_name in targets, f"Test directory not found for {pkg_name}"
    target_path = targets[pkg_name]

    success, elapsed = run_isolated_test(
        target_path=target_path,
        project_root=PROJECT_ROOT,
        include_stress=False,
        fast_mode=True,
        timeout_sec=15,
    )

    assert success is True, f"Fast test suite for {pkg_name} failed!"
    # Process wall-clock SLA on Windows is max 5.0s (including python bootstrap), with pure test time < 2.0s
    assert elapsed < 5.0, (
        f"Fast test suite for {pkg_name} took {elapsed:.2f}s, exceeding 5.0s limit"
    )
