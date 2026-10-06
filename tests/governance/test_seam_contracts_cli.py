"""test_seam_contracts_cli.py - Unit and regression tests for seam capability contracts and CLI.

Validates:
1. Static AST validation of seam-contracts.yaml (schema, symbol export, skill paths, traversal safety).
2. Capability matching logic (--in, --out, --hardware) with inclusion semantics.
3. Machine-readable JSON output and deterministic raw SHA-256 computation.
4. Correct exit codes (0 for MATCH, 2 for NO_MATCH, 1 for syntax/input error).
5. Keyword search distinction (KEYWORD_HINT instead of contract receipt).
6. Integration with ccba-platform find-seam and compile_catalog CLI entrypoints.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from scripts.ccba_platform_cli import main as platform_main
from scripts.governance.compile_catalog import (
    HUB_ROOT,
    load_seam_contracts,
    match_seam_cards,
    query_seam_contracts,
    validate_seam_contracts,
)
from scripts.governance.compile_catalog import (
    main as compile_catalog_main,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_real_seam_contracts_validation() -> None:
    """Verify that all cards in real seam-contracts.yaml pass static AST validation."""
    errors = validate_seam_contracts(HUB_ROOT)
    assert not errors, (
        f"Found {len(errors)} seam contract error(s) in actual codebase:\n"
        + "\n".join(f"  ❌ {err}" for err in errors)
    )


def test_seam_contracts_validation_traversal_and_schema(tmp_path: Path) -> None:
    """Verify that validate_seam_contracts catches invalid seam_id and schema issues."""
    contracts_file = tmp_path / "seam-contracts.yaml"

    # Test 1: Empty seam_id
    bad_data: dict[str, object] = {
        "cards": [
            {
                "seam_id": "",
                "kind": "package",
                "import_path": "mdconverter:ConversionPipeline",
                "capability": {"in": ["pdf"], "out": ["markdown"]},
            }
        ]
    }
    contracts_file.write_text(yaml.safe_dump(bad_data), encoding="utf-8")
    errors = validate_seam_contracts(tmp_path)
    assert any("missing required 'seam_id'" in err for err in errors)

    # Test 2: Directory traversal in seam_id
    bad_data["cards"] = [
        {
            "seam_id": "../malicious.v1",
            "kind": "package",
            "import_path": "mdconverter:ConversionPipeline",
            "capability": {"in": ["pdf"], "out": ["markdown"]},
        }
    ]
    contracts_file.write_text(yaml.safe_dump(bad_data), encoding="utf-8")
    errors = validate_seam_contracts(tmp_path)
    assert any("contains invalid path characters" in err for err in errors)

    # Test 3: Duplicate seam_id
    bad_data["cards"] = [
        {
            "seam_id": "duplicate.v1",
            "kind": "package",
            "import_path": "mdconverter:ConversionPipeline",
            "capability": {"in": ["pdf"], "out": ["markdown"]},
        },
        {
            "seam_id": "duplicate.v1",
            "kind": "package",
            "import_path": "mdconverter:ConversionPipeline",
            "capability": {"in": ["pdf"], "out": ["markdown"]},
        },
    ]
    contracts_file.write_text(yaml.safe_dump(bad_data), encoding="utf-8")
    errors = validate_seam_contracts(tmp_path)
    assert any("Duplicate seam_id 'duplicate.v1'" in err for err in errors)

    # Test 4: Invalid kind
    bad_data["cards"] = [
        {
            "seam_id": "invalid_kind.v1",
            "kind": "unknown_type",
            "capability": {"in": ["pdf"], "out": ["markdown"]},
        }
    ]
    contracts_file.write_text(yaml.safe_dump(bad_data), encoding="utf-8")
    errors = validate_seam_contracts(tmp_path)
    assert any("has invalid kind 'unknown_type'" in err for err in errors)


def test_seam_contracts_validation_ast_symbols(tmp_path: Path) -> None:
    """Verify validate_seam_contracts verifies module existence and symbol exports."""
    # Setup mock package
    pkg_dir = tmp_path / "packages" / "ccba-pdf-prep"
    src_dir = pkg_dir / "src" / "ccba_pdf_prep"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text(
        '__all__ = ["ValidClass"]\nclass ValidClass: pass\n', encoding="utf-8"
    )

    contracts_file = tmp_path / "seam-contracts.yaml"

    # Symbol not exported
    contracts_file.write_text(
        yaml.safe_dump(
            {
                "cards": [
                    {
                        "seam_id": "phantom.v1",
                        "kind": "package",
                        "import_path": "ccba_pdf_prep:NonExistentSymbol",
                        "capability": {"in": ["pdf"], "out": ["markdown"]},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    errors = validate_seam_contracts(tmp_path)
    assert any("is not exported by '__init__.py'" in err for err in errors)

    # Unknown root package
    contracts_file.write_text(
        yaml.safe_dump(
            {
                "cards": [
                    {
                        "seam_id": "unknown_pkg.v1",
                        "kind": "package",
                        "import_path": "non_registered_pkg:SomeSymbol",
                        "capability": {"in": ["pdf"], "out": ["markdown"]},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    errors = validate_seam_contracts(tmp_path)
    assert any("references unknown root package 'non_registered_pkg'" in err for err in errors)


def test_seam_contracts_validation_skill_cards(tmp_path: Path) -> None:
    """Verify validate_seam_contracts checks skill path existence and leading slash."""
    contracts_file = tmp_path / "seam-contracts.yaml"

    # Missing skill path on disk
    contracts_file.write_text(
        yaml.safe_dump(
            {
                "cards": [
                    {
                        "seam_id": "missing_skill.v1",
                        "kind": "skill",
                        "command": "/ccba-nonexistent",
                        "skill_path": ".agents/skills/ccba-nonexistent/SKILL.md",
                        "capability": {"in": ["query"], "out": ["answer"]},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    errors = validate_seam_contracts(tmp_path)
    assert any(
        "skill_path '.agents/skills/ccba-nonexistent/SKILL.md' does not exist" in err
        for err in errors
    )

    # Command missing leading slash
    skill_file = tmp_path / ".agents" / "skills" / "ccba-test" / "SKILL.md"
    skill_file.parent.mkdir(parents=True)
    skill_file.write_text("---\nname: ccba-test\n---\n# Test\n", encoding="utf-8")

    contracts_file.write_text(
        yaml.safe_dump(
            {
                "cards": [
                    {
                        "seam_id": "bad_cmd.v1",
                        "kind": "skill",
                        "command": "ccba-test",  # Missing leading slash
                        "skill_path": ".agents/skills/ccba-test/SKILL.md",
                        "capability": {"in": ["query"], "out": ["answer"]},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    errors = validate_seam_contracts(tmp_path)
    assert any("command 'ccba-test' must start with '/'" in err for err in errors)


def test_seam_matching_inclusion_semantics() -> None:
    """Verify match_seam_cards allows card inputs to be a superset of query inputs."""
    cards = [
        {
            "seam_id": "multi_in.v1",
            "capability": {"in": ["pdf", "docx", "pptx"], "out": ["markdown"]},
            "hardware": ["any"],
        },
        {
            "seam_id": "exact_in.v1",
            "capability": {"in": ["pdf"], "out": ["markdown"]},
            "hardware": ["any"],
        },
    ]

    # Query asking for just pdf -> both match because both can take pdf
    matches = match_seam_cards(cards, in_types=["pdf"], out_types=["markdown"])
    matched_ids = [m["seam_id"] for m in matches]
    assert "exact_in.v1" in matched_ids
    assert "multi_in.v1" in matched_ids

    # Query asking for pptx -> only multi_in.v1 matches
    matches_pptx = match_seam_cards(cards, in_types=["pptx"], out_types=["markdown"])
    assert len(matches_pptx) == 1
    assert matches_pptx[0]["seam_id"] == "multi_in.v1"


def test_seam_matching_hardware_filter() -> None:
    """Verify match_seam_cards hardware filtering rules."""
    cards = [
        {
            "seam_id": "general_cpu.v1",
            "capability": {"in": ["pdf"], "out": ["markdown"]},
            "hardware": ["any"],
        },
        {
            "seam_id": "spark_exclusive.v1",
            "capability": {"in": ["pdf"], "out": ["markdown"]},
            "hardware": ["dgx_spark", "cuda"],
        },
    ]

    # Query with hardware=dgx_spark -> both match (one has any, one has dgx_spark)
    matches_spark = match_seam_cards(cards, in_types=["pdf"], hardware="dgx_spark")
    assert len(matches_spark) == 2

    # Query with hardware=mac_m3 -> only general_cpu.v1 matches (hardware: [any])
    matches_mac = match_seam_cards(cards, in_types=["pdf"], hardware="mac_m3")
    assert len(matches_mac) == 1
    assert matches_mac[0]["seam_id"] == "general_cpu.v1"


def test_query_seam_contracts_match_and_json_structure() -> None:
    """Verify query_seam_contracts returns status MATCH, exit code 0, and correct JSON structure."""
    code, payload = query_seam_contracts(
        hub_root=HUB_ROOT,
        in_types=["pdf"],
        out_types=["markdown"],
        as_json=True,
    )
    assert code == 0
    assert payload["status"] == "MATCH"
    assert payload["count"] >= 1
    assert len(payload["index_sha256"]) == 64
    assert any(c["seam_id"] == "legal_markdown.v1" for c in payload["cards"])


def test_query_seam_contracts_no_match() -> None:
    """Verify query_seam_contracts returns exit code 2 and status NO_MATCH with index_sha256."""
    code, payload = query_seam_contracts(
        hub_root=HUB_ROOT,
        in_types=["audio"],
        out_types=["3d_model"],
        as_json=True,
    )
    assert code == 2
    assert payload["status"] == "NO_MATCH"
    assert payload["count"] == 0
    assert len(payload["index_sha256"]) == 64
    assert payload["cards"] == []


def test_query_seam_contracts_missing_inputs() -> None:
    """Verify query_seam_contracts returns exit code 1 when no query parameters are provided."""
    code, payload = query_seam_contracts(hub_root=HUB_ROOT, as_json=True)
    assert code == 1
    assert payload["status"] == "ERROR"


def test_query_seam_contracts_keyword_is_hint_not_contract(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify keyword search outputs KEYWORD_HINT and explicitly notes it is not a contract receipt."""
    code, payload = query_seam_contracts(hub_root=HUB_ROOT, keyword="pdf", as_json=False)
    assert code == 0
    captured = capsys.readouterr()
    assert "KEYWORD_HINT - NOT A CONTRACT RECEIPT" in captured.out
    assert payload["status"] == "KEYWORD_HINT"


def test_raw_byte_sha256_integrity() -> None:
    """Verify that index_sha256 matches hashlib.sha256 of raw bytes from disk."""
    import hashlib

    contracts_file = HUB_ROOT / "seam-contracts.yaml"
    expected_sha256 = hashlib.sha256(contracts_file.read_bytes()).hexdigest()

    data, actual_sha256 = load_seam_contracts(HUB_ROOT)
    assert actual_sha256 == expected_sha256
    assert isinstance(data, dict)
    assert "cards" in data


def test_cli_find_seam_check_flag(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify ccba-platform find-seam --check exits cleanly on valid contracts."""
    rc = platform_main(["find-seam", "--check"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "seam-contracts.yaml is valid" in captured.out


def test_cli_find_seam_capability_match(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify ccba-platform find-seam --in pdf --out markdown --json produces valid JSON receipt."""
    rc = platform_main(["find-seam", "--in", "pdf", "--out", "markdown", "--json"])
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "MATCH"
    assert data["count"] >= 1
    assert any(c["seam_id"] == "legal_markdown.v1" for c in data["cards"])


def test_cli_find_seam_capability_no_match(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify ccba-platform find-seam exit code 2 on capability mismatch."""
    rc = platform_main(["find-seam", "--in", "audio", "--out", "hologram", "--json"])
    assert rc == 2
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "NO_MATCH"
    assert data["count"] == 0
    assert len(data["index_sha256"]) == 64


def test_compile_catalog_cli_capability_flags(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify compile_catalog.py supports --in, --out, and --json directly."""
    rc = compile_catalog_main(["--in", "pdf", "--out", "markdown", "--json"])
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == "MATCH"


def test_seam_contracts_no_forbidden_import_collisions() -> None:
    """Verify that forbidden_substitute_imports across all seam cards have zero collisions.

    If two cards declare the same forbidden import, check_dependency_contracts.py's
    dictionary lookup would overwrite restrictions and silently bypass linter enforcement.
    """
    data, _ = load_seam_contracts(HUB_ROOT)
    cards = data.get("cards", [])

    seen_imports: dict[str, str] = {}
    collisions: list[str] = []

    for card in cards:
        seam_id = card.get("seam_id", "unknown")
        forbidden_list = card.get("forbidden_substitute_imports", [])
        for mod in forbidden_list:
            if mod in seen_imports:
                collisions.append(
                    f"Forbidden import '{mod}' in '{seam_id}' collides with prior declaration in '{seen_imports[mod]}'."
                )
            else:
                seen_imports[mod] = seam_id

    assert not collisions, "Collision(s) detected in forbidden_substitute_imports:\n" + "\n".join(
        f"  ❌ {c}" for c in collisions
    )

