"""Tests for Zero-Bloat Reference Architecture & Windows/OneDrive Hardening (Issue #285)."""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from ccba_legal.cli import build_parser, handle_sync
from ccba_legal.registry import LegalRegistryManager
from ccba_legal.sync import (
    LegalSyncEngine,
    safe_copy2,
    safe_remove,
    safe_rmtree,
    sync_legal_assets,
)


@pytest.fixture
def mock_master_corpus(tmp_path: Path) -> Path:
    """Create a temporary mock master ccba-legal-knowledge repository."""
    corpus = tmp_path / "ccba-legal-knowledge"
    corpus.mkdir(parents=True, exist_ok=True)

    # 1. Bundles in legal_docs/
    bundle_01 = corpus / "legal_docs" / "01_vbpl" / "luat_xay_dung_2025"
    bundle_01.mkdir(parents=True, exist_ok=True)
    (bundle_01 / "luat_xay_dung_2025.md").write_text("# Luật XD 2025", encoding="utf-8")
    (bundle_01 / "metadata.yaml").write_text("id: LXD-2025\n", encoding="utf-8")
    (bundle_01 / "sources").mkdir(exist_ok=True)
    (bundle_01 / "sources" / "scan.pdf").write_bytes(b"%PDF-1.4 dummy large pdf content")

    # 2. Master registry
    reg_dir = corpus / ".md" / "data"
    reg_dir.mkdir(parents=True, exist_ok=True)
    master_reg = {
        "laws": [
            {
                "id": "LXD-2025",
                "document_number": "135/2025/QH15",
                "title": "Luật Xây dựng 2025",
                "status": "ACTIVE",
            }
        ]
    }
    with open(reg_dir / "legal_registry.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(master_reg, f)

    return corpus


def test_pull_latest_okf_bundles_zero_bloat_reference(
    mock_master_corpus: Path, tmp_path: Path
) -> None:
    """Test pull_latest_okf_bundles with pull_assets=False merges registry without copying bundles."""
    spoke_root = tmp_path / "test_spoke"
    spoke_root.mkdir(parents=True, exist_ok=True)

    engine = LegalSyncEngine(project_root=spoke_root)
    res = engine.pull_latest_okf_bundles(
        source_corpus_dir=mock_master_corpus,
        pull_assets=False,
    )

    assert res["status"] == "success"
    assert res["tier"] == "tier_1_local_corpus"
    assert res["bundles_synced"] == []

    # Target legal_docs directory should not be created
    target_legal_docs = spoke_root / ".md" / "legal_docs"
    assert not target_legal_docs.exists()

    # But local registry should be merged
    local_reg = spoke_root / ".md" / "data" / "legal_registry.yaml"
    assert local_reg.exists()
    data = yaml.safe_load(local_reg.read_text(encoding="utf-8"))
    assert any(doc.get("id") == "LXD-2025" for doc in data.get("laws", []))


def test_pull_latest_okf_bundles_full_assets(mock_master_corpus: Path, tmp_path: Path) -> None:
    """Test pull_latest_okf_bundles with pull_assets=True copies OKF bundles and sources."""
    spoke_root = tmp_path / "test_spoke_full"
    spoke_root.mkdir(parents=True, exist_ok=True)

    engine = LegalSyncEngine(project_root=spoke_root)
    res = engine.pull_latest_okf_bundles(
        source_corpus_dir=mock_master_corpus,
        pull_assets=True,
    )

    assert res["status"] == "success"
    assert len(res["bundles_synced"]) == 1
    assert "01_vbpl/luat_xay_dung_2025" in res["bundles_synced"]

    target_legal_docs = spoke_root / ".md" / "legal_docs"
    assert target_legal_docs.exists()
    copied_bundle = target_legal_docs / "01_vbpl" / "luat_xay_dung_2025"
    assert copied_bundle.exists()
    assert (copied_bundle / "sources" / "scan.pdf").exists()


def test_master_legal_corpus_self_copy_guard(mock_master_corpus: Path) -> None:
    """Test that syncing with dest_root pointing directly to Master Legal Corpus legal_docs avoids self-copy."""
    engine = LegalSyncEngine(project_root=mock_master_corpus)

    res = engine.pull_latest_okf_bundles(
        target_dir=mock_master_corpus / "legal_docs",
        source_corpus_dir=mock_master_corpus,
        pull_assets=True,
    )

    assert res["status"] == "success"
    assert res.get("mode") == "master_corpus_preserved"
    assert res["bundles_synced"] == []


def test_safe_copy2_and_safe_remove_readonly(tmp_path: Path) -> None:
    """Test safe_copy2 and safe_remove can overwrite and delete files with Read-Only flag set."""
    src_file = tmp_path / "source.txt"
    src_file.write_text("hello source", encoding="utf-8")

    dst_file = tmp_path / "destination.txt"
    dst_file.write_text("old content", encoding="utf-8")

    # Set Read-Only on destination
    os.chmod(dst_file, stat.S_IREAD)

    # safe_copy2 should overwrite without PermissionError
    res_copy = safe_copy2(src_file, dst_file)
    assert Path(res_copy).read_text(encoding="utf-8") == "hello source"

    # Set Read-Only again and test safe_remove
    os.chmod(dst_file, stat.S_IREAD)
    safe_remove(dst_file)
    assert not dst_file.exists()


def test_safe_remove_directory_with_readonly_files(tmp_path: Path) -> None:
    """Test safe_remove/safe_rmtree on directory containing read-only files and subdirectories."""
    test_dir = tmp_path / "readonly_dir"
    sub_dir = test_dir / "sub"
    sub_dir.mkdir(parents=True, exist_ok=True)

    file1 = test_dir / "file1.txt"
    file1.write_text("file1", encoding="utf-8")
    os.chmod(file1, stat.S_IREAD)

    file2 = sub_dir / "file2.txt"
    file2.write_text("file2", encoding="utf-8")
    os.chmod(file2, stat.S_IREAD)

    safe_rmtree(test_dir)
    assert not test_dir.exists()


def test_legal_registry_manager_save_readonly(tmp_path: Path) -> None:
    """Test LegalRegistryManager.save() can overwrite a read-only registry file."""
    reg_file = tmp_path / "legal_registry.yaml"
    reg_file.write_text("laws: []\n", encoding="utf-8")

    # Lock file as read-only
    os.chmod(reg_file, stat.S_IREAD)

    mgr = LegalRegistryManager(registry_path=reg_file)
    mgr.save({"laws": [{"id": "LXD-2025"}]})

    saved_data = yaml.safe_load(reg_file.read_text(encoding="utf-8"))
    assert saved_data["laws"][0]["id"] == "LXD-2025"


def test_cli_reference_only_flag_and_zero_bloat_exit_0(
    mock_master_corpus: Path, tmp_path: Path
) -> None:
    """Test CLI ccba-legal sync --reference-only parses flag and exits 0 on success."""
    parser = build_parser()
    args = parser.parse_args(
        [
            "sync",
            "--pull-latest",
            "--reference-only",
            "--source-corpus",
            str(mock_master_corpus),
            "-o",
            str(tmp_path / ".md" / "legal_docs"),
        ]
    )

    assert args.reference_only is True
    assert args.pull_latest is True

    with patch.object(Path, "cwd", return_value=tmp_path):
        exit_code = handle_sync(args)
        assert exit_code == 0


def test_sync_legal_assets_helper_pull_assets(mock_master_corpus: Path, tmp_path: Path) -> None:
    """Test sync_legal_assets convenience helper passes pull_assets correctly."""
    spoke_root = tmp_path / "helper_spoke"
    spoke_root.mkdir(parents=True, exist_ok=True)

    res_ref = sync_legal_assets(
        source_corpus_dir=mock_master_corpus,
        project_root=spoke_root,
        pull_assets=False,
    )
    assert res_ref["status"] == "success"
    assert res_ref["bundles_synced"] == []

    res_full = sync_legal_assets(
        source_corpus_dir=mock_master_corpus,
        project_root=spoke_root,
        pull_assets=True,
    )
    assert res_full["status"] == "success"
    assert len(res_full["bundles_synced"]) == 1


def test_safe_copy2_destination_directory_with_readonly_file(tmp_path: Path) -> None:
    """Test safe_copy2 clears Read-Only on target file inside directory when dst is a directory."""
    src_file = tmp_path / "data.txt"
    src_file.write_text("updated content", encoding="utf-8")

    dst_dir = tmp_path / "output_dir"
    dst_dir.mkdir(parents=True, exist_ok=True)

    existing_file = dst_dir / "data.txt"
    existing_file.write_text("initial content", encoding="utf-8")
    os.chmod(existing_file, stat.S_IREAD)

    res = safe_copy2(src_file, dst_dir)
    assert Path(res).read_text(encoding="utf-8") == "updated content"
    assert (dst_dir / "data.txt").read_text(encoding="utf-8") == "updated content"


def test_safe_copy2_self_copy_to_parent_directory(tmp_path: Path) -> None:
    """Test safe_copy2 avoids SameFileError when dst is the parent directory of src."""
    file_path = tmp_path / "sample.txt"
    file_path.write_text("sample data", encoding="utf-8")

    # Copying to its own parent directory should be detected as self-copy
    res = safe_copy2(file_path, tmp_path)
    assert Path(res).exists()
    assert Path(res).read_text(encoding="utf-8") == "sample data"


def test_safe_remove_windows_junction(tmp_path: Path) -> None:
    """Test safe_remove correctly deletes Windows NTFS directory junctions without deleting target contents."""
    if sys.platform != "win32":
        pytest.skip("Windows NTFS directory junction test requires win32")

    try:
        import _winapi

        if not hasattr(_winapi, "CreateJunction"):
            pytest.skip("_winapi.CreateJunction not available on this platform")
    except ImportError:
        pytest.skip("_winapi not available on this platform")

    target_dir = tmp_path / "junction_target"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / "payload.txt"
    target_file.write_text("protected content", encoding="utf-8")

    junction_path = tmp_path / "junction_link"
    _winapi.CreateJunction(str(target_dir), str(junction_path))

    assert junction_path.exists()
    assert (junction_path / "payload.txt").exists()

    safe_remove(junction_path)

    # Junction link should be gone, but target contents preserved
    assert not junction_path.exists()
    assert target_dir.exists()
    assert target_file.exists()
    assert target_file.read_text(encoding="utf-8") == "protected content"


def test_legal_registry_manager_save_lock_retry(tmp_path: Path) -> None:
    """Test LegalRegistryManager.save retries on temporary permission/lock error."""
    reg_file = tmp_path / "legal_registry.yaml"
    reg_file.write_text("laws: []\n", encoding="utf-8")

    mgr = LegalRegistryManager(registry_path=reg_file)

    call_count = 0
    orig_open = open

    def mock_open(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        # Fail first call with PermissionError, succeed on second
        if call_count == 1 and len(args) > 1 and "w" in args[1]:
            raise PermissionError("[WinError 32] File locked by background sync")
        return orig_open(*args, **kwargs)

    with patch("builtins.open", side_effect=mock_open):
        mgr.save({"laws": [{"id": "RETRY-TEST"}]})

    saved_data = yaml.safe_load(reg_file.read_text(encoding="utf-8"))
    assert saved_data["laws"][0]["id"] == "RETRY-TEST"
    assert call_count >= 2


def test_safe_remove_directory_with_nested_junction(tmp_path: Path) -> None:
    """Test safe_remove on directory containing an NTFS junction removes junction without deleting target files."""
    if sys.platform != "win32":
        pytest.skip("Windows NTFS directory junction test requires win32")

    try:
        import _winapi

        if not hasattr(_winapi, "CreateJunction"):
            pytest.skip("_winapi.CreateJunction not available on this platform")
    except ImportError:
        pytest.skip("_winapi not available on this platform")

    parent_dir = tmp_path / "parent_dir"
    parent_dir.mkdir(parents=True, exist_ok=True)
    (parent_dir / "regular_file.txt").write_text("file in parent", encoding="utf-8")

    external_target_dir = tmp_path / "external_target_dir"
    external_target_dir.mkdir(parents=True, exist_ok=True)
    external_file = external_target_dir / "preserve_me.txt"
    external_file.write_text("do not delete", encoding="utf-8")

    nested_junction = parent_dir / "nested_junction"
    _winapi.CreateJunction(str(external_target_dir), str(nested_junction))

    assert (nested_junction / "preserve_me.txt").exists()

    safe_remove(parent_dir)

    assert not parent_dir.exists()
    assert not nested_junction.exists()
    # Ensure external target and its file were NOT deleted!
    assert external_target_dir.exists()
    assert external_file.exists()
    assert external_file.read_text(encoding="utf-8") == "do not delete"


def test_safe_copy2_destination_symlink_does_not_chmod_target(tmp_path: Path) -> None:
    """Test safe_copy2 avoids calling chmod on symlink destination to protect target permissions."""
    src_file = tmp_path / "src.txt"
    src_file.write_text("new content", encoding="utf-8")

    target_file = tmp_path / "target.txt"
    target_file.write_text("old content", encoding="utf-8")

    symlink_file = tmp_path / "symlink.txt"
    try:
        symlink_file.symlink_to(target_file)
    except (OSError, NotImplementedError):
        pytest.skip("Creating symlinks requires privileges or Developer Mode on Windows")

    # Spy on os.chmod to verify it is never invoked on symlink_file
    with patch("os.chmod", wraps=os.chmod) as mock_chmod:
        safe_copy2(src_file, symlink_file)
        for call_args in mock_chmod.call_args_list:
            called_path = Path(call_args[0][0])
            assert not (called_path.is_symlink())
