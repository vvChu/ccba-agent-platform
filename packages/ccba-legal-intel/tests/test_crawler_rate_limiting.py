"""test_crawler_rate_limiting.py - Unit tests for TVPL rate limiter, jitter, and credentials security."""

from __future__ import annotations

import os
import time
from unittest.mock import patch

import pytest

from ccba_legal import (
    TVPLCrawlFailedException,
    TVPLRateLimiter,
    get_tvpl_credentials,
    sleep_with_jitter,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_get_tvpl_credentials_raises_when_missing() -> None:
    """Verify get_tvpl_credentials strictly raises EnvironmentError when no env vars/files exist."""
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("TVPL_USERNAME", None)
        os.environ.pop("TVPL_PASSWORD", None)

        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(EnvironmentError, match="TVPL VIP credentials not configured"):
                get_tvpl_credentials()


def test_get_tvpl_credentials_success_from_env() -> None:
    """Verify get_tvpl_credentials retrieves credentials from environment variables."""
    with patch.dict(os.environ, {"TVPL_USERNAME": "test_user", "TVPL_PASSWORD": "test_password"}):
        user, pwd = get_tvpl_credentials()
        assert user == "test_user"
        assert pwd == "test_password"


def test_sleep_with_jitter_bounds() -> None:
    """Verify sleep_with_jitter sleeps within base_sec + [jitter_min, jitter_max]."""
    start = time.time()
    slept = sleep_with_jitter(base_sec=0.05, jitter_min=0.01, jitter_max=0.03)
    elapsed = time.time() - start

    assert 0.06 <= slept <= 0.08 + 0.02
    assert elapsed >= 0.05


def test_rate_limiter_throttling_interval() -> None:
    """Verify TVPLRateLimiter throttles requests when called too quickly."""
    limiter = TVPLRateLimiter(max_requests_per_session=5, min_request_interval_sec=0.1)

    limiter.check_and_throttle()
    assert limiter.session_request_count == 1

    start = time.time()
    limiter.check_and_throttle()
    elapsed = time.time() - start

    assert limiter.session_request_count == 2
    # Second request should have been throttled to respect min_request_interval_sec
    assert elapsed >= 0.08


def test_rate_limiter_session_cap_reached() -> None:
    """Verify TVPLRateLimiter raises TVPLCrawlFailedException when max requests cap is reached."""
    limiter = TVPLRateLimiter(max_requests_per_session=2, min_request_interval_sec=0.0)

    limiter.check_and_throttle()
    limiter.check_and_throttle()

    assert limiter.session_request_count == 2

    with pytest.raises(TVPLCrawlFailedException, match="Session request cap"):
        limiter.check_and_throttle()

    # Reset session should allow new requests
    limiter.reset_session()
    assert limiter.session_request_count == 0
    limiter.check_and_throttle()
    assert limiter.session_request_count == 1
