"""test_crawler_vip_verification.py - Unit tests for verify_tvpl_vip_status and timestamp-bounded download guard."""

from __future__ import annotations

from unittest.mock import MagicMock
import pytest

from ccba_legal.session import verify_tvpl_vip_status

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_verify_tvpl_vip_status_active() -> None:
    """Verify verify_tvpl_vip_status returns True when user account is active."""
    cdp_mock = MagicMock()
    cdp_mock.evaluate_js.return_value = "VIP_PRO_ACTIVE"
    assert verify_tvpl_vip_status(cdp_mock) is True


def test_verify_tvpl_vip_status_guest() -> None:
    """Verify verify_tvpl_vip_status returns False when user is guest."""
    cdp_mock = MagicMock()
    cdp_mock.evaluate_js.return_value = "GUEST"
    assert verify_tvpl_vip_status(cdp_mock) is False


def test_verify_tvpl_vip_status_exception_safe() -> None:
    """Verify verify_tvpl_vip_status safely returns False if evaluation raises exception."""
    cdp_mock = MagicMock()
    cdp_mock.evaluate_js.side_effect = RuntimeError("CDP disconnected")
    assert verify_tvpl_vip_status(cdp_mock) is False
