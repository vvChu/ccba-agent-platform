"""Unit tests for AIVisionFormulaHarvester (ADR 0031 / ADR 0038)."""

from pathlib import Path
from ccba_legal.formula_harvester import (
    _clean_and_extract_katex,
    _compute_sha256,
    _read_cache,
    _validate_katex,
    _write_cache,
    extract_latex_from_image,
    is_formula_image,
)


def test_is_formula_image_classification() -> None:
    # 1. Inline math symbol
    assert is_formula_image(20.0, 50.0, "biến dạng tương ứng") is True

    # 2. Compact single-line formula
    assert is_formula_image(45.0, 200.0, "xác định theo biểu thức") is True

    # 3. Diagram with caption should be rejected
    assert is_formula_image(150.0, 300.0, "Sơ đồ bố trí", forward_text="Hình 1 - Sơ đồ mặt bằng") is False

    # 4. Diagram with CHÚ DẪN should be rejected
    assert is_formula_image(120.0, 250.0, "Mặt cắt", forward_text="CHÚ DẪN:\n1 - Cột") is False


def test_validate_and_clean_katex() -> None:
    valid_raw = "Kết quả là: $$q_1 = 10 \\cdot K \\cdot \\sqrt{P} \\tag{1}$$ xin cảm ơn"
    cleaned = _clean_and_extract_katex(valid_raw)
    assert cleaned == "$$q_1 = 10 \\cdot K \\cdot \\sqrt{P} \\tag{1}$$"
    assert _validate_katex(cleaned) is True

    # Unbalanced braces
    assert _validate_katex("$$a = \\frac{b}{c$$") is False

    # Unbalanced environments
    assert _validate_katex("$$\\begin{aligned} a = b$$") is False


def test_sha256_cache(tmp_path: Path) -> None:
    data = b"fake_png_data_123"
    sha = _compute_sha256(data)
    assert len(sha) == 64

    # Write cache
    _write_cache(tmp_path, sha, "$$a + b = c$$")

    # Read cache
    cached = _read_cache(tmp_path, sha)
    assert cached == "$$a + b = c$$"


def test_extract_latex_skip_vision(tmp_path: Path) -> None:
    data = b"sample_math_png"
    res = extract_latex_from_image(data, cache_dir=tmp_path, skip_vision=True)
    assert "FORMULA_PLACEHOLDER" in res
