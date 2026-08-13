import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ccba_legal.crawler import (
    HeadlessEnvironmentError,
    TVPLSessionMutex,
    download_three_tier,
)
from ccba_legal.registry import (
    DEFAULT_RELATION_SYNONYMS,
    load_relation_synonyms,
)


def test_mutex_acquire_and_release(tmp_path: Path) -> None:
    lock_file = tmp_path / "tvpl_vip_session.lock"
    # Acquire
    with TVPLSessionMutex(lock_path=lock_file, timeout=0.3, retry_interval=0.03):
        assert lock_file.exists()
        content = lock_file.read_text(encoding="utf-8")
        data = json.loads(content)
        assert data["pid"] == os.getpid()

    # Release
    assert not lock_file.exists()


def test_mutex_held_timeout(tmp_path: Path) -> None:
    lock_file = tmp_path / "tvpl_vip_session.lock"

    # Create an active lock by current process (guaranteed active)
    lock_data = {"pid": os.getpid(), "timestamp": time.time()}
    lock_file.write_text(json.dumps(lock_data), encoding="utf-8")

    with pytest.raises(TimeoutError):
        with TVPLSessionMutex(lock_path=lock_file, timeout=0.3, retry_interval=0.03):
            pass


def test_mutex_expired_override(tmp_path: Path) -> None:
    lock_file = tmp_path / "tvpl_vip_session.lock"

    # Create an expired lock (6 minutes ago)
    lock_data = {"pid": 99999, "timestamp": time.time() - 360}
    lock_file.write_text(json.dumps(lock_data), encoding="utf-8")

    with TVPLSessionMutex(lock_path=lock_file, timeout=0.3, retry_interval=0.03):
        assert lock_file.exists()
        content = lock_file.read_text(encoding="utf-8")
        data = json.loads(content)
        assert data["pid"] == os.getpid()


def test_mutex_corrupted_override(tmp_path: Path) -> None:
    lock_file = tmp_path / "tvpl_vip_session.lock"

    # Create a corrupted lock file
    lock_file.write_text("corrupted content", encoding="utf-8")

    with TVPLSessionMutex(lock_path=lock_file, timeout=0.3, retry_interval=0.03):
        assert lock_file.exists()
        content = lock_file.read_text(encoding="utf-8")
        data = json.loads(content)
        assert data["pid"] == os.getpid()


def test_load_relation_synonyms_no_file() -> None:
    with patch("ccba_legal.crawler.resolve_project_root") as mock_resolve:
        # Resolve to a non-existent directory
        mock_resolve.return_value = Path("/nonexistent/dir")
        mapping = load_relation_synonyms()
        assert mapping == DEFAULT_RELATION_SYNONYMS


def test_load_relation_synonyms_valid_file(tmp_path: Path) -> None:
    resources_dir = tmp_path / ".agents" / "skills" / "ccba-legal-intel" / "resources"
    resources_dir.mkdir(parents=True, exist_ok=True)
    yaml_file = resources_dir / "relation_synonyms.yaml"

    yaml_content = """
relation_synonyms:
  amends_docs:
    - 'Văn bản bị sửa đổi bổ sung'
    - 'Văn bản bị sửa đổi, bổ sung'
  replaced_docs:
    - 'Văn bản bị thay thế'
"""
    yaml_file.write_text(yaml_content, encoding="utf-8")

    with patch("ccba_legal.crawler.resolve_project_root", return_value=tmp_path):
        mapping = load_relation_synonyms()
        assert mapping["Văn bản bị sửa đổi bổ sung"] == "amends_docs"
        assert mapping["Văn bản bị sửa đổi, bổ sung"] == "amends_docs"
        assert mapping["Văn bản bị thay thế"] == "replaced_docs"


def test_download_three_tier_target_exists(tmp_path: Path) -> None:
    download_dir = tmp_path / "download"
    download_dir.mkdir()
    target_file = download_dir / "test_doc.docx"
    target_file.write_bytes(
        b"dummy content"
    )  # must be non-empty: _check_tier_1 requires st_size > 0

    cdp_mock = MagicMock()
    # Should succeed immediately without checking other tiers
    assert download_three_tier(cdp_mock, download_dir, "test_doc") is True


def test_download_three_tier_cache_exists(tmp_path: Path) -> None:
    download_dir = tmp_path / "download"
    download_dir.mkdir()

    # Set up mock project root
    cache_dir = tmp_path / ".md" / "data" / "cache"
    cache_dir.mkdir(parents=True)
    cache_file = cache_dir / "test_doc.pdf"
    cache_file.write_text("dummy pdf content", encoding="utf-8")

    cdp_mock = MagicMock()
    with patch("ccba_legal.crawler.resolve_project_root", return_value=tmp_path):
        assert download_three_tier(cdp_mock, download_dir, "test_doc") is True

    expected_target = download_dir / "test_doc.pdf"
    assert expected_target.exists()
    assert expected_target.read_text(encoding="utf-8") == "dummy pdf content"


def test_download_three_tier_shared_drive_exists(tmp_path: Path) -> None:
    download_dir = tmp_path / "download"
    download_dir.mkdir()

    # Set up mock shared drive
    shared_dir = tmp_path / "shared_drive"
    shared_dir.mkdir()
    shared_file = shared_dir / "test_doc.doc"
    shared_file.write_text("dummy doc content", encoding="utf-8")

    cdp_mock = MagicMock()
    with (
        patch.dict(os.environ, {"SHARED_DRIVE_DIR": str(shared_dir)}),
        patch("ccba_legal.crawler.resolve_project_root", return_value=tmp_path),
    ):
        assert download_three_tier(cdp_mock, download_dir, "test_doc") is True

    expected_target = download_dir / "test_doc.doc"
    assert expected_target.exists()
    assert expected_target.read_text(encoding="utf-8") == "dummy doc content"


def test_download_three_tier_google_drive(tmp_path: Path) -> None:
    download_dir = tmp_path / "download"
    download_dir.mkdir()

    # Mock google-api-python-client
    mock_service = MagicMock()
    mock_list = mock_service.files().list
    mock_list.return_value.execute.return_value = {
        "files": [{"id": "drive_file_id_123", "name": "test_doc.docx"}]
    }

    # Mock MediaIoBaseDownload to write dummy content
    class MockDownloader:
        def __init__(self, fd: Any, request: Any) -> None:
            self.fd = fd

        def next_chunk(self) -> Any:
            self.fd.write(b"drive docx content")
            return None, True

    # Inject mock scripts.legal_sync module into sys.modules
    import types

    mock_sync = types.ModuleType("scripts.legal_sync")
    mock_sync.GOOGLE_API_AVAILABLE = True  # type: ignore[attr-defined]
    mock_sync.get_drive_service = MagicMock(return_value=mock_service)  # type: ignore[attr-defined]
    sys.modules["scripts.legal_sync"] = mock_sync

    mock_gapi = types.ModuleType("googleapiclient")
    sys.modules["googleapiclient"] = mock_gapi
    mock_gapi_http = types.ModuleType("googleapiclient.http")
    mock_gapi_http.MediaIoBaseDownload = MockDownloader  # type: ignore[attr-defined]
    sys.modules["googleapiclient.http"] = mock_gapi_http

    cdp_mock = MagicMock()
    try:
        with (
            patch.dict(os.environ, {"DRIVE_FOLDER_ID": "mock_folder_id"}),
            patch("ccba_legal.crawler.resolve_project_root", return_value=tmp_path),
        ):
            assert download_three_tier(cdp_mock, download_dir, "test_doc") is True
    finally:
        sys.modules.pop("scripts.legal_sync", None)
        sys.modules.pop("googleapiclient", None)
        sys.modules.pop("googleapiclient.http", None)

    expected_target = download_dir / "test_doc.docx"
    assert expected_target.exists()
    assert expected_target.read_bytes() == b"drive docx content"


def test_download_three_tier_s3(tmp_path: Path) -> None:
    download_dir = tmp_path / "download"
    download_dir.mkdir()

    # Mock boto3 s3 client
    mock_s3_client = MagicMock()

    # When calling download_file, create a dummy file
    def mock_download_file(bucket: Any, key: Any, filename: str) -> None:
        with open(filename, "wb") as f:
            f.write(b"s3 content")

    mock_s3_client.download_file.side_effect = mock_download_file

    # Inject mock boto3 and botocore into sys.modules
    import types

    mock_boto3 = types.ModuleType("boto3")
    mock_boto3.client = MagicMock(return_value=mock_s3_client)  # type: ignore[attr-defined]
    sys.modules["boto3"] = mock_boto3

    mock_botocore = types.ModuleType("botocore")
    sys.modules["botocore"] = mock_botocore
    mock_botocore_exc = types.ModuleType("botocore.exceptions")

    class MockClientError(Exception):
        pass

    mock_botocore_exc.ClientError = MockClientError  # type: ignore[attr-defined]
    sys.modules["botocore.exceptions"] = mock_botocore_exc

    cdp_mock = MagicMock()
    try:
        with (
            patch.dict(os.environ, {"AWS_BUCKET_NAME": "mock-bucket"}),
            patch("ccba_legal.crawler.resolve_project_root", return_value=tmp_path),
        ):
            assert download_three_tier(cdp_mock, download_dir, "test_doc") is True
    finally:
        sys.modules.pop("boto3", None)
        sys.modules.pop("botocore", None)
        sys.modules.pop("botocore.exceptions", None)

    expected_target = download_dir / "test_doc.docx"
    assert expected_target.exists()
    assert expected_target.read_bytes() == b"s3 content"


def test_download_three_tier_headless_guard(tmp_path: Path) -> None:
    download_dir = tmp_path / "download"
    download_dir.mkdir()

    cdp_mock = MagicMock()
    # In headless, it should raise HeadlessEnvironmentError
    with (
        patch.dict(os.environ, {"CI": "true"}),
        patch("ccba_legal.crawler.resolve_project_root", return_value=tmp_path),
        pytest.raises(HeadlessEnvironmentError),
    ):
        download_three_tier(cdp_mock, download_dir, "test_doc")


@pytest.mark.slow
def test_download_three_tier_direct_crawl(tmp_path: Path) -> None:
    download_dir = tmp_path / "download"
    download_dir.mkdir()

    # Mock trigger_download to succeed and create the file
    def mock_trigger(cdp: Any, d_dir: Path, slug: str) -> bool:
        f = d_dir / f"{slug}.docx"
        f.write_text("crawled docx", encoding="utf-8")
        return True

    cdp_mock = MagicMock()
    with (
        patch("ccba_legal.crawler.trigger_download", side_effect=mock_trigger),
        patch("ccba_legal.crawler.resolve_project_root", return_value=tmp_path),
        patch("ccba_legal.crawler._check_shared_drive", return_value=False),
        patch("ccba_legal.crawler._check_google_drive", return_value=False),
        patch("ccba_legal.crawler._check_aws_s3", return_value=False),
    ):
        assert download_three_tier(cdp_mock, download_dir, "test_doc") is True

    # Check that file exists in target dir
    expected_target = download_dir / "test_doc.docx"
    assert expected_target.exists()
    assert expected_target.read_text(encoding="utf-8") == "crawled docx"

    # Check that file was cached
    expected_cache = tmp_path / ".md" / "data" / "cache" / "test_doc.docx"
    assert expected_cache.exists()
    assert expected_cache.read_text(encoding="utf-8") == "crawled docx"
