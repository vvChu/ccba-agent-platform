import sys
from pathlib import Path

# Ensure src is in python path
src_dir = Path(__file__).parents[1] / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import pytest

from ccba_notebooklm._artifacts import get_source_id_by_path
from ccba_notebooklm._client import get_client
from ccba_notebooklm._registry import (
    get_file_sha256,
    normalize_to_relative,
    read_registry,
    update_registry,
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    monkeypatch.delenv("NOTEBOOKLM_SESSION_COOKIE", raising=False)
    monkeypatch.delenv("NOTEBOOKLM_COOKIES_JSON", raising=False)
    test_reg = tmp_path / "sources_registry.yaml"
    monkeypatch.setattr("ccba_notebooklm._registry.REGISTRY_FILE", test_reg)


@pytest.mark.asyncio
async def test_ensure_source_new_file(tmp_path):
    """Xác minh get_source_id_by_path thêm file mới chưa có trong registry."""
    dummy_file = tmp_path / "test_doc.txt"
    dummy_file.write_text("Hello NotebookLM Test Content", encoding="utf-8")

    client = get_client()
    nb_id = "nb-mock-1"

    source_id = await get_source_id_by_path(client, nb_id, str(dummy_file))
    assert source_id == "src-mock-file"

    # Kiểm tra registry được ghi lại đúng
    registry = read_registry()
    norm_path = normalize_to_relative(str(dummy_file))
    assert norm_path in registry
    assert registry[norm_path]["source_id"] == "src-mock-file"
    assert registry[norm_path]["notebook_id"] == nb_id


@pytest.mark.asyncio
async def test_ensure_source_cache_hit(tmp_path):
    """Xác minh get_source_id_by_path trả về source_id trực tiếp khi SHA-256 khớp (Cache HIT)."""
    dummy_file = tmp_path / "cached_doc.txt"
    dummy_file.write_text("Cached content for NotebookLM", encoding="utf-8")
    sha256 = get_file_sha256(str(dummy_file))
    nb_id = "nb-mock-1"

    # Pre-register in registry with an existing mock source ID ("src-mock-1")
    update_registry(str(dummy_file), "src-mock-1", sha256, nb_id)

    client = get_client()

    # Calling get_source_id_by_path should hit cache and return "src-mock-1" without uploading
    source_id = await get_source_id_by_path(client, nb_id, str(dummy_file))
    assert source_id == "src-mock-1"


@pytest.mark.asyncio
async def test_ensure_source_sha256_mismatch(tmp_path):
    """Xác minh get_source_id_by_path tự động xóa source cũ và upload source mới khi SHA-256 thay đổi."""
    dummy_file = tmp_path / "mismatched_doc.txt"
    dummy_file.write_text("Original Version 1", encoding="utf-8")
    nb_id = "nb-mock-1"

    # Registry has old sha256
    update_registry(str(dummy_file), "src-mock-1", "old_fake_sha256_hash", nb_id)

    # Modify file content (Version 2)
    dummy_file.write_text("Modified Version 2 Content", encoding="utf-8")
    new_sha256 = get_file_sha256(str(dummy_file))

    client = get_client()

    source_id = await get_source_id_by_path(client, nb_id, str(dummy_file))
    assert source_id == "src-mock-file"

    # Registry updated with new sha256
    registry = read_registry()
    norm_path = normalize_to_relative(str(dummy_file))
    assert registry[norm_path]["sha256"] == new_sha256
