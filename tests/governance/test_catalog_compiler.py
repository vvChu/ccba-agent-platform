"""test_catalog_compiler.py - Unit and regression tests for compile_catalog.py seam validator.

Validates:
1. All public deep seams in actual monorepo packages match their exported symbols.
2. Phantom seam symbols are deterministically caught and reported.
3. Foreign package spoofing across boundaries is blocked.
4. Non-existent submodules are caught and reported.
5. Top-level AST symbol fallback logic operates correctly without explicit __all__.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from scripts.governance.compile_catalog import (
    HUB_ROOT,
    _extract_module_exported_symbols,
    check_catalog_in_sync,
    validate_seam_exports,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_real_codebase_seams_validation() -> None:
    """Verify that all Public Deep Seams declared in packages/*/AGENTS.md exist and export cleanly."""
    errors = validate_seam_exports(HUB_ROOT)
    assert not errors, (
        f"Found {len(errors)} seam export validation error(s) in actual codebase:\n"
        + "\n".join(f"  ❌ {err}" for err in errors)
    )


def test_isolated_phantom_seam_detection(tmp_path: Path) -> None:
    """Verify that validate_seam_exports detects symbols not declared in module __all__."""
    pkg_dir = tmp_path / "packages" / "ccba-pdf-prep"
    src_dir = pkg_dir / "src" / "ccba_pdf_prep"
    src_dir.mkdir(parents=True)

    init_file = src_dir / "__init__.py"
    init_file.write_text(
        '__all__ = ["PDFProcessingPipeline", "ProcessingResult"]\n\n'
        "class PDFProcessingPipeline: pass\n"
        "class ProcessingResult: pass\n",
        encoding="utf-8",
    )

    agents_md = pkg_dir / "AGENTS.md"
    agents_md.write_text(
        "# ccba-pdf-prep Package Guidance\n\n"
        "- **Public Deep Seams**: `from ccba_pdf_prep import PDFProcessingPipeline, PhantomSymbol`.\n",
        encoding="utf-8",
    )

    errors = validate_seam_exports(tmp_path)
    assert len(errors) == 1
    assert "declares seam symbol 'PhantomSymbol' from 'ccba_pdf_prep'" in errors[0]
    assert "is not exported by" in errors[0]


def test_isolated_foreign_package_spoofing(tmp_path: Path) -> None:
    """Verify that validate_seam_exports prevents package declaring seam for foreign module."""
    pkg_dir = tmp_path / "packages" / "ccba-pdf-prep"
    src_dir = pkg_dir / "src" / "ccba_pdf_prep"
    src_dir.mkdir(parents=True)

    (src_dir / "__init__.py").write_text('__all__ = ["PDFPipeline"]\n', encoding="utf-8")

    agents_md = pkg_dir / "AGENTS.md"
    agents_md.write_text(
        "# ccba-pdf-prep Package Guidance\n\n"
        "- **Public Deep Seams**: `from ccba_ooxml import pack_document`.\n",
        encoding="utf-8",
    )

    errors = validate_seam_exports(tmp_path)
    assert len(errors) == 1
    assert "declares seam for foreign module 'ccba_ooxml'" in errors[0]
    assert "Expected root package 'ccba_pdf_prep'" in errors[0]


def test_isolated_missing_module_detection(tmp_path: Path) -> None:
    """Verify that validate_seam_exports detects non-existent submodules."""
    pkg_dir = tmp_path / "packages" / "ccba-pdf-prep"
    src_dir = pkg_dir / "src" / "ccba_pdf_prep"
    src_dir.mkdir(parents=True)

    (src_dir / "__init__.py").write_text('__all__ = ["PDFPipeline"]\n', encoding="utf-8")

    agents_md = pkg_dir / "AGENTS.md"
    agents_md.write_text(
        "# ccba-pdf-prep Package Guidance\n\n"
        "- **Public Deep Seams**: `from ccba_pdf_prep.nonexistent_submod import SomeSymbol`.\n",
        encoding="utf-8",
    )

    errors = validate_seam_exports(tmp_path)
    assert len(errors) == 1
    assert (
        "declares seam module 'ccba_pdf_prep.nonexistent_submod' which does not exist" in errors[0]
    )


def test_extract_module_exported_symbols_without_all(tmp_path: Path) -> None:
    """Verify that _extract_module_exported_symbols falls back to top-level public definitions."""
    module_file = tmp_path / "sample_mod.py"
    module_file.write_text(
        "def public_func(): pass\n"
        "def _private_func(): pass\n"
        "class PublicClass: pass\n"
        "class _PrivateClass: pass\n"
        "CONSTANT_VAL = 42\n"
        "_PRIVATE_VAL = 100\n"
        "from math import sqrt, sin as my_sin\n"
        "from os import _exit\n",
        encoding="utf-8",
    )

    symbols = _extract_module_exported_symbols(module_file)
    assert symbols is not None
    assert "public_func" in symbols
    assert "PublicClass" in symbols
    assert "CONSTANT_VAL" in symbols
    assert "sqrt" in symbols
    assert "my_sin" in symbols

    assert "_private_func" not in symbols
    assert "_PrivateClass" not in symbols
    assert "_PRIVATE_VAL" not in symbols
    assert "_exit" not in symbols


def test_check_catalog_in_sync_catches_seam_errors(tmp_path: Path) -> None:
    """Verify that check_catalog_in_sync flags static seam export errors."""
    catalog_path = tmp_path / ".agents" / "skills" / "platform-loader" / "catalog.yaml"
    catalog_path.parent.mkdir(parents=True)
    catalog_path.write_text("skills: []\nworkflows: []\nseams: []\n", encoding="utf-8")

    with patch(
        "scripts.governance.compile_catalog.validate_seam_exports",
        return_value=["Mock phantom seam error"],
    ):
        in_sync, msg = check_catalog_in_sync(tmp_path)
        assert in_sync is False
        assert "Static Seam Export Error: Mock phantom seam error" in msg


def test_extract_module_exported_symbols_with_aug_assign(tmp_path: Path) -> None:
    """Verify that _extract_module_exported_symbols supports __all__ += [...] AugAssign pattern."""
    module_file = tmp_path / "aug_mod.py"
    module_file.write_text(
        '__all__ = ["foo"]\n__all__ += ["bar", "baz"]\n\nfoo = 1\nbar = 2\nbaz = 3\n',
        encoding="utf-8",
    )

    symbols = _extract_module_exported_symbols(module_file)
    assert symbols == {"foo", "bar", "baz"}


def test_validate_seam_exports_handles_trailing_punctuation(tmp_path: Path) -> None:
    """Verify that validate_seam_exports immunizes symbol names against trailing punctuation."""
    pkg_dir = tmp_path / "packages" / "ccba-pdf-prep"
    src_dir = pkg_dir / "src" / "ccba_pdf_prep"
    src_dir.mkdir(parents=True)

    (src_dir / "__init__.py").write_text(
        '__all__ = ["PDFProcessingPipeline"]\nclass PDFProcessingPipeline: pass\n',
        encoding="utf-8",
    )

    agents_md = pkg_dir / "AGENTS.md"
    agents_md.write_text(
        "# ccba-pdf-prep Package Guidance\n\n"
        "- **Public Deep Seams**: `from ccba_pdf_prep import PDFProcessingPipeline.`.\n",
        encoding="utf-8",
    )

    errors = validate_seam_exports(tmp_path)
    assert errors == []
