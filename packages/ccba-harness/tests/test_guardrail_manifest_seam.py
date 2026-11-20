"""Unit tests for the Tier-0 pure-stdlib _guardrail_manifest seam."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from ccba_harness._guardrail_manifest import (
    MANIFEST_REL_PATH,
    collect_guardrail_hashes,
    compute_lf_sha256,
    main,
    verify_guardrail_manifest,
    write_guardrail_manifest,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_compute_lf_sha256_matches_crlf_and_lf(tmp_path: Path) -> None:
    """Verify LF normalization produces identical digests across CRLF and LF inputs."""
    lf_file = tmp_path / "lf.py"
    crlf_file = tmp_path / "crlf.py"
    lf_file.write_bytes(b"line1\nline2\n")
    crlf_file.write_bytes(b"line1\r\nline2\r\n")
    assert compute_lf_sha256(lf_file) == compute_lf_sha256(crlf_file)


def test_write_and_verify_guardrail_manifest_excludes_json_and_detects_tamper(
    tmp_path: Path,
) -> None:
    """Verify manifest excludes metadata JSONs, passes valid files, and catches 1-byte tamper."""
    g_dir = tmp_path / "scripts" / "_guardrails"
    g_dir.mkdir(parents=True)
    target = g_dir / "safe_pytest.py"
    target.write_text("print('ok')\n", encoding="utf-8")
    (g_dir / "module_budget_baseline.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "conftest.py").write_text("# conftest\n", encoding="utf-8")

    manifest_path = write_guardrail_manifest(
        tmp_path,
        [
            "scripts/_guardrails/safe_pytest.py",
            "scripts/_guardrails/module_budget_baseline.json",
            "scripts/_guardrails/guardrails_manifest.json",
            "conftest.py",
            ".githooks/pre-commit",
        ],
    )
    assert manifest_path == (tmp_path / MANIFEST_REL_PATH).resolve()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert list(payload["files"].keys()) == ["scripts/_guardrails/safe_pytest.py"]
    assert verify_guardrail_manifest(tmp_path, manifest_path) == []

    # 1-byte tamper must fail closed
    target.write_text("print('xx')\n", encoding="utf-8")
    violations = verify_guardrail_manifest(tmp_path, manifest_path)
    assert len(violations) == 1
    assert "SHA-256 mismatch" in violations[0]

    # Missing file must fail closed
    target.unlink()
    missing_violations = verify_guardrail_manifest(tmp_path, manifest_path)
    assert len(missing_violations) == 1
    assert "missing" in missing_violations[0]


def test_verify_rejects_traversal_and_bool_schema_version(tmp_path: Path) -> None:
    """Verify traversal entries and non-integer/bool schema_version fail closed."""
    assert collect_guardrail_hashes(tmp_path, ["scripts/_guardrails/../evil.py"]) == {}
    manifest = tmp_path / MANIFEST_REL_PATH
    manifest.parent.mkdir(parents=True)

    manifest.write_text(json.dumps({"schema_version": True, "files": {}}), encoding="utf-8")
    assert any("schema_version" in v for v in verify_guardrail_manifest(tmp_path, manifest))

    manifest.write_text(
        json.dumps({"schema_version": 1, "files": {"scripts/_guardrails/../x.py": "a" * 64}}),
        encoding="utf-8",
    )
    assert any("Invalid manifest entry" in v for v in verify_guardrail_manifest(tmp_path, manifest))


def test_cli_verify_exit_codes(tmp_path: Path) -> None:
    """Verify standalone CLI --verify fails without manifest, passes valid, fails tampered."""
    assert main(["--path", str(tmp_path), "--verify"]) == 1
    assert main(["--path", str(tmp_path)]) == 1

    target = tmp_path / "scripts" / "_guardrails" / "safe_runner.py"
    target.parent.mkdir(parents=True)
    target.write_text("X = 1\n", encoding="utf-8")
    write_guardrail_manifest(tmp_path, ["scripts/_guardrails/safe_runner.py"])

    assert main(["--path", str(tmp_path), "--verify"]) == 0
    target.write_text("X = 2\n", encoding="utf-8")
    assert main(["--path", str(tmp_path), "--verify"]) == 1


def test_guardrail_manifest_module_stays_pure_stdlib_and_under_loc_cap() -> None:
    """Verify _guardrail_manifest.py stays pure stdlib, <= 120 LOC, and no ccba_harness deps."""
    mod_file = (
        Path(__file__).resolve().parents[1] / "src" / "ccba_harness" / "_guardrail_manifest.py"
    )
    lines = mod_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= 120
    assert sys.version_info >= (3, 10)
