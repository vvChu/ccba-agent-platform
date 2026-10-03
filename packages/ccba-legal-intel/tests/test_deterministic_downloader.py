"""Unit tests for deterministic downloader, lock cleanup, and resilience hardening."""

import shutil
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from ccba_legal.cdp import MockChromeCDP, cleanup_zombie_locks
from ccba_legal.crawler.tier_downloader import _wait_for_download, trigger_download


def test_cleanup_zombie_locks_removes_dead_locks(tmp_path: Path) -> None:
    """Verify cleanup_zombie_locks cleanly unlinks orphaned/dead lock files."""
    user_data = tmp_path / "chrome_vip"
    user_data.mkdir(parents=True, exist_ok=True)

    # 1. Dead symlink lock pointing to an impossible PID
    dead_lock = user_data / "SingletonLock"
    dead_target = "testhost-9999999"
    try:
        dead_lock.symlink_to(dead_target)
    except OSError:
        dead_lock.write_text("testhost-9999999")

    # 2. Orphaned SingletonCookie and SingletonSocket
    cookie_lock = user_data / "SingletonCookie"
    cookie_lock.write_text("mock_cookie_lock")
    socket_lock = user_data / "SingletonSocket"
    socket_lock.write_text("mock_socket_lock")

    assert dead_lock.exists() or dead_lock.is_symlink()
    assert cookie_lock.exists()
    assert socket_lock.exists()

    cleanup_zombie_locks(user_data)

    assert not dead_lock.exists()
    assert not cookie_lock.exists()
    assert not socket_lock.exists()


def test_cleanup_zombie_locks_noop_on_missing_dir(tmp_path: Path) -> None:
    """Verify cleanup_zombie_locks handles non-existent paths gracefully."""
    missing_dir = tmp_path / "does_not_exist"
    cleanup_zombie_locks(missing_dir)


def test_cdp_file_stability_guard(tmp_path: Path) -> None:
    """Verify MockChromeCDP and _check_file_stability identify completed downloads."""
    cdp = MockChromeCDP()
    watch_dir = tmp_path / "downloads"
    watch_dir.mkdir(parents=True, exist_ok=True)

    # In-progress file (.crdownload) should be ignored
    temp_file = watch_dir / "document.docx.crdownload"
    temp_file.write_bytes(b"downloading...")

    found = cdp._check_file_stability(
        [watch_dir], [".docx"], start_time=time.time(), existing_files=set()
    )
    assert found is None

    # Completed file with stable size
    completed_file = watch_dir / "document.docx"
    completed_file.write_bytes(b"PK\x03\x04final docx content")

    found = cdp._check_file_stability(
        [watch_dir], [".docx"], start_time=time.time() - 1.0, existing_files=set()
    )
    assert found is not None
    assert found.name == "document.docx"


def test_wait_for_download_delegates_to_cdp(tmp_path: Path) -> None:
    """Verify _wait_for_download invokes CDP completion handler."""
    watch_dir = tmp_path / "downloads"
    watch_dir.mkdir(parents=True, exist_ok=True)

    mock_cdp = MagicMock()
    fake_found = watch_dir / "sample.pdf"
    fake_found.write_bytes(b"%PDF-1.4 content")
    mock_cdp.wait_for_download_completion.return_value = fake_found

    result = _wait_for_download(
        [watch_dir],
        set(),
        [".pdf"],
        timeout=5.0,
        start_time=time.time(),
        cdp=mock_cdp,
    )

    assert result == fake_found
    mock_cdp.wait_for_download_completion.assert_called_once()


def test_trigger_download_enforces_rate_limiter(tmp_path: Path) -> None:
    """Verify trigger_download invokes TVPLRateLimiter.check_and_throttle before requests."""
    cdp = MockChromeCDP()
    cdp.connected = True
    download_dir = tmp_path / "downloads"
    download_dir.mkdir(parents=True, exist_ok=True)

    # Mock preflight inspection returning DOCX and PDF available
    preflight_mock = {
        "has_docx": True,
        "has_pdf": True,
        "pdf_tier": 1,
    }
    cdp.set_mock_js_response("document.readyState", "complete")

    with (
        patch.object(cdp, "evaluate_js", return_value=preflight_mock),
        patch(
            "ccba_legal.crawler.tier_downloader.TVPLRateLimiter.check_and_throttle"
        ) as mock_throttle,
        patch("ccba_legal.crawler.tier_downloader._wait_for_download") as mock_wait,
    ):
        mock_file = download_dir / "test.docx"
        mock_file.write_bytes(b"PK\x03\x04")
        mock_wait.return_value = mock_file

        res = trigger_download(
            cdp=cdp,
            download_dir=download_dir,
            slug_name="test_slug",
            format_type="docx",
            download_attachments=False,
            doc_url="https://thuvienphapluat.vn/van-ban/Xay-dung-Do-thi/test.aspx",
        )

        assert mock_throttle.call_count >= 1
        assert res.get("success") is True


def test_permission_error_retry_on_file_move(tmp_path: Path) -> None:
    """Verify trigger_download resiliently retries when shutil.move encounters Windows Defender lock."""
    cdp = MockChromeCDP()
    cdp.connected = True
    download_dir = tmp_path / "dest"
    download_dir.mkdir(parents=True, exist_ok=True)

    watch_dir = tmp_path / "watch"
    watch_dir.mkdir(parents=True, exist_ok=True)
    temp_docx = watch_dir / "downloaded.docx"
    temp_docx.write_bytes(b"PK\x03\x04docx content")

    preflight_mock = {
        "has_docx": True,
        "has_pdf": False,
        "pdf_tier": None,
    }

    # Simulate PermissionError on first move attempt, success on second
    attempt_count = 0
    orig_move = shutil.move

    def fake_move(src, dst):
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count == 1:
            raise PermissionError(
                "[WinError 32] The process cannot access the file because it is being used by another process"
            )
        return orig_move(src, dst)

    with (
        patch.object(cdp, "evaluate_js", return_value=preflight_mock),
        patch("ccba_legal.crawler.tier_downloader.TVPLRateLimiter.check_and_throttle"),
        patch("ccba_legal.crawler.tier_downloader._wait_for_download", return_value=temp_docx),
        patch("shutil.move", side_effect=fake_move),
        patch("time.sleep"),  # Skip backoff sleep in tests
    ):
        res = trigger_download(
            cdp=cdp,
            download_dir=download_dir,
            slug_name="slug_win_retry",
            format_type="docx",
            download_attachments=False,
        )

        assert res.get("success") is True
        assert attempt_count == 2
