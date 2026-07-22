import json
import os
import sys
import time
from unittest.mock import MagicMock, patch

import pytest
from ccba_legal.crawler import (
    TVPLSessionMutex,
    download_three_tier,
)
from ccba_legal.registry import (
    DEFAULT_RELATION_SYNONYMS,
    load_relation_synonyms,
)


def test_mutex_simultaneous_acquisition(tmp_path):
    """Test that two concurrent processes cannot acquire the lock simultaneously."""
    lock_file = tmp_path / "simultaneous.lock"

    # Instance 1 and Instance 2
    mutex1 = TVPLSessionMutex(lock_path=lock_file, timeout=0.2, retry_interval=0.05)
    mutex2 = TVPLSessionMutex(lock_path=lock_file, timeout=0.2, retry_interval=0.05)

    # First instance acquires the lock successfully
    m1 = mutex1.__enter__()
    assert m1 is mutex1

    # Second instance must fail to acquire the lock and raise TimeoutError
    with pytest.raises(TimeoutError):
        mutex2.__enter__()

    # Clean up
    mutex1.__exit__(None, None, None)


def test_mutex_killed_process_deadlock(tmp_path):
    """Test that if a process holding the lock is dead, the lock is overridden and acquisition succeeds."""
    lock_file = tmp_path / "killed_process.lock"

    # Create lock file with an inactive/non-existent PID (e.g. 99999)
    # and a recent timestamp (e.g. 10 seconds ago).
    lock_data = {"pid": 99999, "timestamp": time.time() - 10}
    lock_file.write_text(json.dumps(lock_data), encoding="utf-8")

    mutex = TVPLSessionMutex(lock_path=lock_file, timeout=0.5, retry_interval=0.1)

    # It should succeed because it overrides the dead process lock
    with mutex:
        assert lock_file.exists()
        content = lock_file.read_text(encoding="utf-8")
        data = json.loads(content)
        assert data["pid"] == os.getpid()


def test_load_relation_synonyms_malformed_yaml(tmp_path):
    """Test that malformed YAML configuration fallback works correctly."""
    resources_dir = tmp_path / ".agents" / "skills" / "ccba-legal-intel" / "resources"
    resources_dir.mkdir(parents=True, exist_ok=True)
    yaml_file = resources_dir / "relation_synonyms.yaml"

    # Write malformed YAML (invalid indentation and list structure)
    yaml_file.write_text(
        "relation_synonyms:\n  amends_docs\n    - 'Văn bản bị sửa đổi'\n  -", encoding="utf-8"
    )

    # Should print warning and return the DEFAULT_RELATION_SYNONYMS mapping
    mapping = load_relation_synonyms(project_root=tmp_path)
    assert mapping == DEFAULT_RELATION_SYNONYMS


def test_js_matching_logic_mismatch(tmp_path):
    """Test that key names with commas or multiple spaces match successfully after normalization."""
    resources_dir = tmp_path / ".agents" / "skills" / "ccba-legal-intel" / "resources"
    resources_dir.mkdir(parents=True, exist_ok=True)
    yaml_file = resources_dir / "relation_synonyms.yaml"

    yaml_content = """
relation_synonyms:
  amends_docs:
    - 'Văn bản bị sửa đổi, bổ sung'
  replaced_docs:
    - 'Văn bản  bị  thay thế'
"""
    yaml_file.write_text(yaml_content, encoding="utf-8")

    mapping = load_relation_synonyms(project_root=tmp_path)

    # Verify that load_relation_synonyms correctly loads the keys
    assert "Văn bản bị sửa đổi, bổ sung" in mapping
    assert "Văn bản  bị  thay thế" in mapping

    # Simulate JavaScript logic on the page elements with key normalization:
    import re

    def js_matches_fixed(element_text: str, key_from_yaml: str) -> bool:
        normalized_key = key_from_yaml.replace(",", "")
        normalized_key = re.sub(r"\s+", " ", normalized_key).strip()
        txt = element_text.replace(",", "").strip()
        txt = re.sub(r"\s+", " ", txt).strip()
        return txt.startswith(normalized_key)

    # Key 1: "Văn bản bị sửa đổi, bổ sung" (contains a comma)
    assert js_matches_fixed("Văn bản bị sửa đổi, bổ sung", "Văn bản bị sửa đổi, bổ sung")

    # Key 2: "Văn bản  bị  thay thế" (contains multiple spaces)
    assert js_matches_fixed("Văn bản  bị  thay thế", "Văn bản  bị  thay thế")


def test_download_three_tier_empty_cache_file(tmp_path):
    """Test that download_three_tier ignores 0-byte/corrupted cache files and does not copy them."""
    download_dir = tmp_path / "download"
    download_dir.mkdir()

    # Create a 0-byte cache file (simulating a corrupted cache)
    cache_dir = tmp_path / ".md" / "data" / "cache"
    cache_dir.mkdir(parents=True)
    cache_file = cache_dir / "test_doc.docx"
    cache_file.touch()

    cdp_mock = MagicMock()
    with (
        patch("ccba_legal.crawler.resolve_project_root", return_value=tmp_path),
        patch("ccba_legal.crawler._check_is_headless", return_value=False),
        patch("ccba_legal.crawler.trigger_download", return_value=False),
    ):
        # Bypasses 0-byte cache and falls back to Tier 3, which returns False
        assert download_three_tier(cdp_mock, download_dir, "test_doc") is False

    expected_target = download_dir / "test_doc.docx"
    assert not expected_target.exists()


def test_download_three_tier_s3_network_error(tmp_path):
    """Test that download_three_tier handles S3 network errors and falls back to Tier 3."""
    download_dir = tmp_path / "download"
    download_dir.mkdir()

    mock_s3_client = MagicMock()

    # Inject mock boto3 and botocore modules
    import types

    mock_boto3 = types.ModuleType("boto3")
    mock_boto3.client = MagicMock(return_value=mock_s3_client)
    sys.modules["boto3"] = mock_boto3

    mock_botocore = types.ModuleType("botocore")
    sys.modules["botocore"] = mock_botocore
    mock_botocore_exc = types.ModuleType("botocore.exceptions")

    class MockClientError(Exception):
        def __init__(self, response, operation_name):
            self.response = response
            self.operation_name = operation_name

    mock_botocore_exc.ClientError = MockClientError
    sys.modules["botocore.exceptions"] = mock_botocore_exc

    # Simulate a 500 Internal Server Error (network/connection issue)
    error_response = {"Error": {"Code": "500", "Message": "Internal Server Error"}}
    mock_s3_client.download_file.side_effect = MockClientError(error_response, "download_file")

    cdp_mock = MagicMock()

    # Mock trigger_download (Tier 3 fallback)
    def mock_trigger(cdp, d_dir, slug):
        f = d_dir / f"{slug}.docx"
        f.write_text("direct crawl docx", encoding="utf-8")
        return True

    try:
        with (
            patch.dict(os.environ, {"AWS_BUCKET_NAME": "mock-bucket"}),
            patch("ccba_legal.crawler.trigger_download", side_effect=mock_trigger),
            patch("ccba_legal.crawler._check_is_headless", return_value=False),
            patch("ccba_legal.crawler.resolve_project_root", return_value=tmp_path),
        ):
            # Bypasses S3 error and falls back to Tier 3 successfully
            assert download_three_tier(cdp_mock, download_dir, "test_doc") is True
    finally:
        sys.modules.pop("boto3", None)
        sys.modules.pop("botocore", None)
        sys.modules.pop("botocore.exceptions", None)

    expected_target = download_dir / "test_doc.docx"
    assert expected_target.exists()
    assert expected_target.read_text(encoding="utf-8") == "direct crawl docx"
