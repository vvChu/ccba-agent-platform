"""Automated Unit Tests for Catalog CLI Seam & Skill Queries (ADR-0047, ADR-0032).

Covers CLI search across package seams and agent skills, filtering behaviors,
empty query validation, in-memory isolation, ANSI color handling, and entrypoint signatures.
"""

from __future__ import annotations

from typing import Any

import pytest
from scripts.ccba_platform_cli import main as platform_main
from scripts.governance.compile_catalog import HUB_ROOT, query_catalog
from scripts.governance.compile_catalog import main as compile_catalog_main
from scripts.spoke.find_skills import main as find_skills_main

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_query_catalog_empty_keyword(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify query_catalog rejects empty or whitespace-only search terms."""
    rc1 = query_catalog(HUB_ROOT, "")
    assert rc1 == 1
    captured1 = capsys.readouterr()
    assert "[ERROR] Please provide a non-empty search keyword." in captured1.err

    rc2 = query_catalog(HUB_ROOT, "   ")
    assert rc2 == 1
    captured2 = capsys.readouterr()
    assert "[ERROR] Please provide a non-empty search keyword." in captured2.err


def test_compile_catalog_cli_empty_query(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify compile_catalog CLI handles --query '' by returning exit code 1."""
    rc = compile_catalog_main(["--query", ""])
    assert rc == 1
    captured = capsys.readouterr()
    assert "[ERROR] Please provide a non-empty search keyword." in captured.err


def test_query_catalog_no_match(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify query_catalog graceful message when no seams or skills match."""
    rc = query_catalog(HUB_ROOT, "xyz_nonexistent_12345")
    assert rc == 0
    captured = capsys.readouterr()
    assert "No seams or skills found matching 'xyz_nonexistent_12345'" in captured.out
    assert "Tip: Check spelling or try a broader keyword" in captured.out


def test_query_catalog_match_seams_only(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify keyword matching only package seams prints Tier 1 and omits Tier 2/3."""
    rc = query_catalog(HUB_ROOT, "ccba-qc-core")
    assert rc == 0
    captured = capsys.readouterr()
    assert "📦 [Tier 1: Monorepo Package Deep Seams]" in captured.out
    assert "ccba-qc-core" in captured.out
    assert "⚡ [Tier 2/3: Agent Skills & Workflows]" not in captured.out


def test_query_catalog_match_skills_only(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify keyword matching only agent skills prints Tier 2/3 and omits Tier 1."""
    rc = query_catalog(HUB_ROOT, "ccba-new-feature")
    assert rc == 0
    captured = capsys.readouterr()
    assert "⚡ [Tier 2/3: Agent Skills & Workflows]" in captured.out
    assert "ccba-new-feature" in captured.out
    assert "📦 [Tier 1: Monorepo Package Deep Seams]" not in captured.out


def test_query_catalog_match_both_seams_and_skills(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify keyword matching both package seams and skills displays both tiers."""
    rc = query_catalog(HUB_ROOT, "ccba-harness")
    assert rc == 0
    captured = capsys.readouterr()
    assert "📦 [Tier 1: Monorepo Package Deep Seams]" in captured.out
    assert "⚡ [Tier 2/3: Agent Skills & Workflows]" in captured.out
    assert "ccba-harness" in captured.out


def test_query_catalog_in_memory_isolation(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify fast in-memory execution using monkeypatched catalog dict."""
    fake_catalog: dict[str, Any] = {
        "seams": [
            {
                "package": "mock-pkg",
                "path": "packages/mock-pkg",
                "description": "Mock package for fast unit testing",
                "public_seams": ["from mock_pkg import MockSeam"],
                "contracts": "Mock contract invariant",
                "tests": "pytest packages/mock-pkg/tests",
            }
        ],
        "skills": [
            {
                "name": "mock-skill",
                "version": "1.0",
                "description": "Mock skill description",
                "role": "Mock Tester",
                "path": ".agents/skills/mock-skill",
                "triggers": ["test-mock"],
            }
        ],
    }
    monkeypatch.setattr(
        "scripts.governance.compile_catalog.compile_catalog_dict",
        lambda _hub_root: fake_catalog,
    )
    rc = query_catalog(HUB_ROOT, "mock")
    assert rc == 0
    captured = capsys.readouterr()
    assert "mock-pkg" in captured.out
    assert "mock-skill" in captured.out


def test_find_skills_cli_flags_and_ansi_output(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify find_skills CLI flags (--seam, --seams, -s) and ANSI formatted skill results."""
    # Test seam flags exit cleanly
    with pytest.raises(SystemExit) as exc_info_s:
        find_skills_main(["-s", "harness"])
    assert exc_info_s.value.code == 0

    with pytest.raises(SystemExit) as exc_info_seam:
        find_skills_main(["--seam", "harness"])
    assert exc_info_seam.value.code == 0

    with pytest.raises(SystemExit) as exc_info_seams:
        find_skills_main(["--seams", "harness"])
    assert exc_info_seams.value.code == 0

    # Test standard skill query with ANSI green formatting
    find_skills_main(["new-feature"])
    captured = capsys.readouterr()
    assert "\x1b[32m" in captured.out
    assert "\x1b[0m" in captured.out
    assert "ccba-new-feature" in captured.out


def test_ccba_platform_cli_find_seam(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify ccba-platform find-seam invocation via main entrypoint."""
    rc = platform_main(["find-seam", "harness"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "🔍 CCBA Platform Catalog Query: 'harness'" in captured.out
    assert "📦 [Tier 1: Monorepo Package Deep Seams]" in captured.out
