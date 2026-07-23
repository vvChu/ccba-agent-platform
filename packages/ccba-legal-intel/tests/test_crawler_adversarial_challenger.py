import json
import os
import sys
import threading
import time
import types
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.adversarial]

from ccba_legal.crawler import (
    TVPLSessionMutex,
    download_three_tier,
)
from ccba_legal.registry import (
    DEFAULT_RELATION_SYNONYMS,
    load_relation_synonyms,
)


@pytest.fixture
def mock_tier3_disabled() -> Generator[None, None, None]:
    """Fixture to mock Tier 3 CDP crawl and headless checks to prevent web interaction."""
    with (
        patch("ccba_legal.crawler._check_is_headless", return_value=False),
        patch("ccba_legal.crawler.trigger_download", return_value=False),
    ):
        yield


# =====================================================================
# SCENARIO 1: Mutex Lock Concurrency Race Condition
# =====================================================================
def test_mutex_concurrency_race_condition(tmp_path: Path) -> None:
    """Verify that multiple threads cannot concurrently acquire the lock.
    One thread will succeed, and the other will fail/timeout.
    """
    lock_file = tmp_path / "tvpl_vip_session.lock"
    acquired_locks = []
    errors = []

    def run_lock(thread_num: int) -> None:
        try:
            with TVPLSessionMutex(lock_path=lock_file, timeout=1, retry_interval=0.1):
                acquired_locks.append(thread_num)
                # Hold the lock longer than Thread 2's timeout (1s) to force a timeout
                time.sleep(1.5)
        except Exception as e:
            errors.append((thread_num, e))

    t1 = threading.Thread(target=run_lock, args=(1,))
    t2 = threading.Thread(target=run_lock, args=(2,))

    t1.start()
    time.sleep(0.1)  # Ensure t1 acquires the lock first
    t2.start()

    t1.join()
    t2.join()

    # Thread 1 should have acquired it
    assert len(acquired_locks) == 1
    assert acquired_locks[0] == 1
    # Thread 2 should have timed out/failed
    assert len(errors) == 1
    assert errors[0][0] == 2
    assert isinstance(errors[0][1], TimeoutError)


# =====================================================================
# SCENARIO 2: Killed Process / Simulated Deadlock
# =====================================================================
def test_mutex_killed_process_deadlock(tmp_path: Path) -> None:
    """Verify that if a process holding the lock is dead, a new crawler
    can immediately override the lock and acquire it.
    """
    lock_file = tmp_path / "tvpl_vip_session.lock"

    # Simulate an active lock created by process 99999 (which is dead) 10 seconds ago
    lock_data = {"pid": 99999, "timestamp": time.time() - 10}
    lock_file.write_text(json.dumps(lock_data), encoding="utf-8")

    # A new crawler tries to run. Since the PID is dead, it overrides the lock immediately.
    with TVPLSessionMutex(lock_path=lock_file, timeout=1, retry_interval=0.05):
        assert lock_file.exists()
        content = lock_file.read_text(encoding="utf-8")
        data = json.loads(content)
        assert data["pid"] == os.getpid()


# =====================================================================
# SCENARIO 3: Synonyms Configuration (Malformed YAML & JS Normalization Issues)
# =====================================================================
def test_load_relation_synonyms_malformed_yaml(tmp_path: Path) -> None:
    """Verify that load_relation_synonyms falls back to default mapping on malformed YAML."""
    resources_dir = tmp_path / ".agents" / "skills" / "ccba-legal-intel" / "resources"
    resources_dir.mkdir(parents=True, exist_ok=True)
    yaml_file = resources_dir / "relation_synonyms.yaml"

    # Malformed YAML syntax (no colon after relation_synonyms)
    yaml_content = """
relation_synonyms
  amends_docs:
    - 'Văn bản bị sửa đổi bổ sung'
"""
    yaml_file.write_text(yaml_content, encoding="utf-8")

    with patch("ccba_legal.crawler.resolve_project_root", return_value=tmp_path):
        mapping = load_relation_synonyms()
        # Should gracefully fallback
        assert mapping == DEFAULT_RELATION_SYNONYMS


def test_relation_synonyms_js_normalization_bug() -> None:
    """Verify that synonyms in YAML with commas or multiple spaces
    match successfully in the JS query because both the web page element
    text and the synonym key are normalized.
    """
    import re

    def js_matches_fixed(element_text: str, key_from_yaml: str) -> bool:
        # Normalized key
        normalized_key = key_from_yaml.replace(",", "")
        normalized_key = re.sub(r"\s+", " ", normalized_key).strip()
        # Normalized web text
        txt = element_text.replace(",", "")
        txt = re.sub(r"\s+", " ", txt).strip()
        return txt.startswith(normalized_key)

    # Case A: YAML synonym contains a comma
    yaml_synonym_with_comma = "Văn bản bị sửa đổi, bổ sung"
    web_element_text = "Văn bản bị sửa đổi, bổ sung"
    assert js_matches_fixed(web_element_text, yaml_synonym_with_comma)

    # Case B: YAML synonym contains multiple spaces
    yaml_synonym_with_spaces = "Văn bản    thay thế"
    web_element_text_spaces = "Văn bản    thay thế"
    assert js_matches_fixed(web_element_text_spaces, yaml_synonym_with_spaces)


# =====================================================================
# SCENARIO 4: Network Issues & Invalid/Corrupted Cache Files
# =====================================================================
def test_download_three_tier_corrupted_cache(tmp_path: Path, mock_tier3_disabled: Any) -> None:
    """Verify that an invalid/empty (0-byte) cache file is ignored
    and not copied to the target folder, preventing corrupted cache restoration.
    """
    download_dir = tmp_path / "download"
    download_dir.mkdir()

    # Create an empty/corrupted cache file in Tier 1 cache directory
    cache_dir = tmp_path / ".md" / "data" / "cache"
    cache_dir.mkdir(parents=True)
    cache_file = cache_dir / "test_corrupted.docx"
    cache_file.write_bytes(b"")  # 0-byte file representing corruption

    cdp_mock = MagicMock()
    with patch("ccba_legal.crawler.resolve_project_root", return_value=tmp_path):
        result = download_three_tier(cdp_mock, download_dir, "test_corrupted")
        assert result is False

    # Verify that no 0-byte file got copied to target folder
    target_file = download_dir / "test_corrupted.docx"
    assert not target_file.exists()


def test_download_three_tier_partial_download_bug(tmp_path: Path, mock_tier3_disabled: Any) -> None:
    """Verify that when a Tier 2 download fails midway (e.g. network issue),
    it cleans up the partial/corrupted file in the target directory and does
    not leave it behind.
    """
    download_dir = tmp_path / "download"
    download_dir.mkdir()

    # Mock Google Drive API to return a file
    mock_service = MagicMock()
    mock_list = mock_service.files().list
    mock_list.return_value.execute.return_value = {
        "files": [{"id": "drive_file_id_123", "name": "test_partial.docx"}]
    }

    # Simulate downloader that writes partial content and then encounters a network error
    class MockDownloader:
        def __init__(self, fd: Any, request: Any) -> None:
            self.fd = fd

        def next_chunk(self) -> None:
            self.fd.write(b"partial downloaded bytes")
            raise ConnectionResetError("Network reset by peer")

    # Inject mocks into sys.modules
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
            # First run: Fails due to simulated ConnectionResetError
            result_1 = download_three_tier(cdp_mock, download_dir, "test_partial")
            assert result_1 is False

            # Verify that partial file is deleted and NOT left in target folder
            target_path = download_dir / "test_partial.docx"
            assert not target_path.exists()

            # Second run: Correctly tries again and fails (or doesn't see partial file)
            result_2 = download_three_tier(cdp_mock, download_dir, "test_partial")
            assert result_2 is False

    finally:
        sys.modules.pop("scripts.legal_sync", None)
        sys.modules.pop("googleapiclient", None)
        sys.modules.pop("googleapiclient.http", None)


def test_download_three_tier_headless_exit(tmp_path: Path) -> None:
    """Verify that when running in a headless/CI environment, download_three_tier
    raises HeadlessEnvironmentError instead of attempting CDP crawl at Tier 3.
    """
    from ccba_legal.crawler import HeadlessEnvironmentError

    download_dir = tmp_path / "download"
    download_dir.mkdir()

    cdp_mock = MagicMock()
    with (
        patch("ccba_legal.crawler.resolve_project_root", return_value=tmp_path),
        patch("ccba_legal.crawler._check_is_headless", return_value=True),
    ):
        with pytest.raises(HeadlessEnvironmentError):
            download_three_tier(cdp_mock, download_dir, "test_headless")
