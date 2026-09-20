"""Unit tests for CCBA Diagram CLI."""

from __future__ import annotations

import json
from pathlib import Path

from ccba_diagram.cli import main
from helpers import make_arrow, make_shape


def test_cli_layout_command(tmp_path: Path):
    """Test 'ccba-diagram layout' command."""
    s1 = make_shape("A", text="Start")
    s2 = make_shape("B", text="End")
    arr = make_arrow("a1", "A", "B")

    input_file = tmp_path / "diagram.json"
    output_file = tmp_path / "layout_out.json"

    input_file.write_text(json.dumps([s1, s2, arr]), encoding="utf-8")

    code = main(["layout", str(input_file), "-o", str(output_file), "--engine", "sugiyama"])
    assert code == 0
    assert output_file.exists()

    result_elements = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(result_elements) == 3


def test_cli_spec_table_command(tmp_path: Path, capsys):
    """Test 'ccba-diagram spec-table' command."""
    s1 = make_shape("A", text="Architecture Core")
    input_file = tmp_path / "diagram.json"
    input_file.write_text(json.dumps([s1]), encoding="utf-8")

    code = main(["spec-table", str(input_file), "-t", "Kiến Trúc CLI"])
    assert code == 0

    captured = capsys.readouterr()
    assert "### 📋 Kiến Trúc CLI" in captured.out
    assert "Architecture Core" in captured.out


def test_cli_missing_file():
    """Test CLI error handling on missing input file."""
    code = main(["layout", "non_existent_file.json"])
    assert code == 1
