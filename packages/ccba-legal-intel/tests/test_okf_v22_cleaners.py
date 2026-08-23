"""Tests for OKF v2.2 Cleaners and Scoped Noise Strippers on Hub."""

import pytest
from ccba_legal.cleaners import Cleaners


def test_strip_administrative_noise():
    raw_text = """
### Điều 1. Phạm vi điều chỉnh
Quy định về hoạt động xây dựng.

Nơi nhận:
- Như Điều 1;
- Lưu: VT.

__CHỦ TỊCH QUỐC HỘI
Vương Đình Huệ__
"""
    cleaned = Cleaners.strip_administrative_noise(raw_text)
    assert "Điều 1. Phạm vi điều chỉnh" in cleaned
    assert "Nơi nhận" not in cleaned
    assert "CHỦ TỊCH QUỐC HỘI" not in cleaned


def test_strip_web_artifacts():
    raw_html = """
### Điều 2. Đối tượng áp dụng
Áp dụng cho mọi tổ chức cá nhân.
<script type="text/javascript">var track = 1;</script>
<form action="/share" method="post"><input type="submit" value="Share Facebook"/></form>
"""
    cleaned = Cleaners.strip_web_artifacts(raw_html)
    assert "Điều 2. Đối tượng áp dụng" in cleaned
    assert "<script" not in cleaned
    assert "<form" not in cleaned
    assert "<input" not in cleaned
