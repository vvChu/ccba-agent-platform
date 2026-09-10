"""test_apply_worker_patch.py - Unit test suite for Single-Writer Atomic Patch Application Engine.

Verifies:
1. Search-Replace and JSON manifest parsing.
2. Cross-worker collision detection.
3. Pre-flight dry-run matching and ambiguity detection.
4. Atomic application and auto-rollback mechanics.
5. CLI entrypoint operations.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from scripts.governance.apply_worker_patch import (
    PatchBlock,
    apply_atomic,
    detect_collisions,
    dry_run,
    load_patches_from_directory,
    main,
    parse_patch_content,
    rollback,
)


def test_parse_search_replace_blocks() -> None:
    """Verify standard SEARCH/REPLACE blocks with FILE headers are parsed correctly."""
    raw_patch = """
FILE: src/foo.py
<<<<<<< SEARCH
def old_foo():
    return 1
=======
def new_foo():
    return 2
>>>>>>> REPLACE

FILE: src/bar.py
<<<<<<< SEARCH
bar = 10
=======
bar = 20
>>>>>>> REPLACE
"""
    blocks = parse_patch_content(raw_patch, source_name="worker_a.patch")
    assert len(blocks) == 2

    assert blocks[0].file_path == "src/foo.py"
    assert "def old_foo():" in blocks[0].search_content
    assert "def new_foo():" in blocks[0].replace_content
    assert blocks[0].source_patch == "worker_a.patch"

    assert blocks[1].file_path == "src/bar.py"
    assert "bar = 10" in blocks[1].search_content
    assert "bar = 20" in blocks[1].replace_content


def test_parse_json_manifest() -> None:
    """Verify JSON structured patch manifest parsing."""
    manifest = [
        {
            "file": "config.yaml",
            "search": "debug: false",
            "replace": "debug: true",
        },
        {
            "file": "utils.py",
            "search": "MAX = 10",
            "replace": "MAX = 100",
        },
    ]
    raw_json = json.dumps(manifest)
    blocks = parse_patch_content(raw_json, source_name="manifest.json")
    assert len(blocks) == 2
    assert blocks[0].file_path == "config.yaml"
    assert blocks[0].search_content == "debug: false"
    assert blocks[0].replace_content == "debug: true"
    assert blocks[1].file_path == "utils.py"


def test_detect_collisions_no_conflict() -> None:
    """Verify no collisions reported when patches target distinct files or distinct code."""
    p1 = PatchBlock(
        file_path="app.py",
        search_content="def func_a():\n    pass",
        replace_content="def func_a():\n    return 1",
        source_patch="worker_1",
    )
    p2 = PatchBlock(
        file_path="app.py",
        search_content="def func_b():\n    pass",
        replace_content="def func_b():\n    return 2",
        source_patch="worker_2",
    )
    p3 = PatchBlock(
        file_path="other.py",
        search_content="x = 1",
        replace_content="x = 2",
        source_patch="worker_3",
    )

    conflicts = detect_collisions([p1, p2, p3])
    assert conflicts == []


def test_detect_collisions_detected() -> None:
    """Verify collision is detected when two distinct workers target overlapping code."""
    p1 = PatchBlock(
        file_path="app.py",
        search_content="def handler():\n    validate()\n    process()",
        replace_content="def handler():\n    validate_v2()\n    process()",
        source_patch="worker_1",
    )
    p2 = PatchBlock(
        file_path="app.py",
        search_content="validate()\n    process()",
        replace_content="validate()\n    process_async()",
        source_patch="worker_2",
    )

    conflicts = detect_collisions([p1, p2])
    assert len(conflicts) == 1
    assert "Collision in 'app.py'" in conflicts[0]
    assert "worker_1" in conflicts[0]
    assert "worker_2" in conflicts[0]


def test_dry_run_success_and_sequential_chaining(tmp_path: Path) -> None:
    """Verify dry_run succeeds and correctly handles sequential mutations on the same file."""
    test_file = tmp_path / "module.py"
    test_file.write_text("a = 1\nb = 2\nc = 3\n", encoding="utf-8")

    p1 = PatchBlock(
        file_path="module.py",
        search_content="a = 1",
        replace_content="a = 10",
        source_patch="w1",
    )
    # p2 relies on p1 having changed a to 10 in virtual memory
    p2 = PatchBlock(
        file_path="module.py",
        search_content="a = 10\nb = 2",
        replace_content="a = 100\nb = 200",
        source_patch="w1",
    )

    valid, errors = dry_run([p1, p2], tmp_path)
    assert valid is True
    assert errors == []

    # File on disk should remain untouched
    assert test_file.read_text(encoding="utf-8") == "a = 1\nb = 2\nc = 3\n"


def test_dry_run_failures(tmp_path: Path) -> None:
    """Verify dry_run detects missing files, missing search blocks, and ambiguous matches."""
    existing_file = tmp_path / "target.py"
    existing_file.write_text("item = 1\nitem = 1\nitem = 2\n", encoding="utf-8")

    # 1. Missing target file
    p_missing = PatchBlock(
        file_path="non_existent.py",
        search_content="test",
        replace_content="test2",
    )
    valid, errors = dry_run([p_missing], tmp_path)
    assert valid is False
    assert any("Target file does not exist" in e for e in errors)

    # 2. Search block not found
    p_not_found = PatchBlock(
        file_path="target.py",
        search_content="unknown_string",
        replace_content="replacement",
    )
    valid, errors = dry_run([p_not_found], tmp_path)
    assert valid is False
    assert any("SEARCH block not found" in e for e in errors)

    # 3. Ambiguous match (count > 1)
    p_ambiguous = PatchBlock(
        file_path="target.py",
        search_content="item = 1",
        replace_content="item = 99",
    )
    valid, errors = dry_run([p_ambiguous], tmp_path)
    assert valid is False
    assert any("Ambiguous SEARCH block" in e for e in errors)


def test_apply_atomic_success(tmp_path: Path) -> None:
    """Verify atomic apply correctly mutates files on disk and creates restore snapshot."""
    f1 = tmp_path / "file1.txt"
    f2 = tmp_path / "file2.txt"
    f1.write_text("original 1", encoding="utf-8")
    f2.write_text("original 2", encoding="utf-8")

    patches = [
        PatchBlock(file_path="file1.txt", search_content="original 1", replace_content="updated 1"),
        PatchBlock(file_path="file2.txt", search_content="original 2", replace_content="updated 2"),
    ]

    success, snapshot, logs = apply_atomic(patches, tmp_path)
    assert success is True
    assert f1.resolve() in snapshot
    assert f2.resolve() in snapshot
    assert f1.read_text(encoding="utf-8") == "updated 1"
    assert f2.read_text(encoding="utf-8") == "updated 2"


def test_rollback_restores_original_state(tmp_path: Path) -> None:
    """Verify rollback restores all files to exact initial snapshot contents."""
    f1 = tmp_path / "f1.txt"
    f1.write_text("clean state", encoding="utf-8")

    snapshot = {f1.resolve(): "clean state"}

    # Corrupt or modify file
    f1.write_text("corrupted partial state", encoding="utf-8")
    assert f1.read_text(encoding="utf-8") == "corrupted partial state"

    # Trigger rollback
    rollback(snapshot)
    assert f1.read_text(encoding="utf-8") == "clean state"


def test_load_patches_from_directory(tmp_path: Path) -> None:
    """Verify loading and aggregating multiple patch files from a directory."""
    patch_dir = tmp_path / "patches"
    patch_dir.mkdir()

    p1_file = patch_dir / "patch1.diff"
    p1_file.write_text("FILE: a.py\n<<<<<<< SEARCH\nold_a\n=======\nnew_a\n>>>>>>> REPLACE\n", encoding="utf-8")

    p2_file = patch_dir / "patch2.json"
    p2_file.write_text(json.dumps([{"file": "b.py", "search": "old_b", "replace": "new_b"}]), encoding="utf-8")

    loaded = load_patches_from_directory(patch_dir)
    assert len(loaded) == 2
    paths = {p.file_path for p in loaded}
    assert paths == {"a.py", "b.py"}


def test_cli_execution_dry_run_and_apply(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify CLI flags operate cleanly via main entrypoint."""
    target = tmp_path / "code.py"
    target.write_text("VERSION = 1\n", encoding="utf-8")

    patch_file = tmp_path / "bump.patch"
    patch_file.write_text(
        "FILE: code.py\n<<<<<<< SEARCH\nVERSION = 1\n=======\nVERSION = 2\n>>>>>>> REPLACE\n",
        encoding="utf-8",
    )

    # 1. Test check-conflicts flag
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "apply_worker_patch.py",
            "--patch",
            str(patch_file),
            "--base-dir",
            str(tmp_path),
            "--check-conflicts",
        ],
    )
    assert main() == 0

    # 2. Test dry-run flag (no disk changes)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "apply_worker_patch.py",
            "--patch",
            str(patch_file),
            "--base-dir",
            str(tmp_path),
            "--dry-run",
        ],
    )
    assert main() == 0
    assert target.read_text(encoding="utf-8") == "VERSION = 1\n"

    # 3. Test apply flag (disk updated)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "apply_worker_patch.py",
            "--patch",
            str(patch_file),
            "--base-dir",
            str(tmp_path),
            "--apply",
        ],
    )
    assert main() == 0
    assert target.read_text(encoding="utf-8") == "VERSION = 2\n"
