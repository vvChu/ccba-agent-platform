"""Unit tests for ccba_ooxml spreadsheet calculation and safe macro injection."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from ccba_ooxml import OOXMLWorkspace, recalc_xlsx, setup_libreoffice_macro

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_recalc_xlsx_nonexistent():
    res = recalc_xlsx("nonexistent_file_test.xlsx")
    assert "error" in res
    assert "not exist" in res["error"]


def test_safe_macro_injection_existing_file(tmp_path: Path):
    """Verify that existing macros in Module1.xba are not overwritten or deleted."""
    fake_appdata = tmp_path / "AppData" / "Roaming"
    macro_dir = fake_appdata / "LibreOffice" / "4" / "user" / "basic" / "Standard"
    macro_dir.mkdir(parents=True, exist_ok=True)
    macro_file = macro_dir / "Module1.xba"

    existing_macro_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE script:module PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "module.dtd">
<script:module xmlns:script="http://openoffice.org/2000/script" script:name="Module1" script:language="StarBasic">
    Sub MyCustomUserMacro()
      ' Do some important engineer calculation
    End Sub
</script:module>"""
    macro_file.write_text(existing_macro_content, encoding="utf-8")

    with patch.dict(os.environ, {"APPDATA": str(fake_appdata)}):
        ok = setup_libreoffice_macro()
        assert ok is True

        content_after = macro_file.read_text(encoding="utf-8")
        # Ensure custom user macro is preserved
        assert "MyCustomUserMacro" in content_after
        # Ensure RecalculateAndSave was safely injected
        assert "RecalculateAndSave" in content_after
        assert "</script:module>" in content_after


def test_ooxml_workspace_recalculate_dispatch(tmp_path: Path):
    """Test OOXMLWorkspace.recalculate method validation and dispatch."""
    docx_file = tmp_path / "test.docx"
    docx_file.write_text("dummy", encoding="utf-8")

    ws = OOXMLWorkspace(docx_file, validate=False)
    res = ws.recalculate()
    assert "error" in res
    assert "only supported for .xlsx" in res["error"]
