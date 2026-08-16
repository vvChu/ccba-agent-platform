"""test_wiki_health_linter.py - Scoped Fast Unit Tests for WikiHealthLinter.

Tests LLM-Wiki index catalog verification, append-only log schema validation,
orphan knowledge note detection, and broken link resolution.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.governance.wiki_health_linter import WikiHealthLinter

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_wiki_health_linter_real_workspace():
    """Verify that current repository LLM-Wiki passes 100% with zero hard issues."""
    linter = WikiHealthLinter()
    issues = linter.audit()
    assert len(issues) == 0


def test_wiki_health_linter_missing_index(tmp_path: Path):
    """Verify detection when index.md is missing."""
    kb = tmp_path / ".md" / "knowledge"
    kb.mkdir(parents=True)
    (kb / "log.md").write_text("## [2026-08-16] [ingest] | Title\n- Note\n", encoding="utf-8")

    linter = WikiHealthLinter(project_root=tmp_path)
    issues = linter.check_index_integrity()
    assert len(issues) == 1
    assert issues[0].subject == "Missing LLM-Wiki Index"


def test_wiki_health_linter_invalid_log_header(tmp_path: Path):
    """Verify detection when log.md header does not match schema."""
    kb = tmp_path / ".md" / "knowledge"
    kb.mkdir(parents=True)
    (kb / "index.md").write_text("# Index\n- [Test](test.md)\n" * 10, encoding="utf-8")
    (kb / "log.md").write_text("## Invalid Header Format\n- Note\n", encoding="utf-8")

    linter = WikiHealthLinter(project_root=tmp_path)
    issues = linter.check_log_schema()
    assert len(issues) == 1
    assert issues[0].subject == "Invalid Wiki Log Header"


def test_wiki_health_linter_orphan_note_detection(tmp_path: Path):
    """Verify detection of orphan notes that are not cataloged in index.md."""
    kb = tmp_path / ".md" / "knowledge"
    kb.mkdir(parents=True)
    (kb / "index.md").write_text("# Index\n- [Cataloged](cataloged.md)\n" * 5, encoding="utf-8")
    (kb / "log.md").write_text("## [2026-08-16] [ingest] | Title\n", encoding="utf-8")
    (kb / "cataloged.md").write_text("# Cataloged\n", encoding="utf-8")
    (kb / "orphan_note.md").write_text("# Orphan\n", encoding="utf-8")

    linter = WikiHealthLinter(project_root=tmp_path)
    issues = linter.check_orphan_knowledge_files()
    assert len(issues) == 1
    assert issues[0].subject == "Orphan Knowledge Note"
    assert "orphan_note.md" in issues[0].message


def test_wiki_health_linter_broken_link_detection(tmp_path: Path):
    """Verify detection of broken links in active knowledge documents."""
    kb = tmp_path / ".md" / "knowledge"
    kb.mkdir(parents=True)
    (kb / "index.md").write_text("# Index\n- [Broken](non_existent_target.md)\n", encoding="utf-8")
    (kb / "log.md").write_text("## [2026-08-16] [ingest] | Title\n", encoding="utf-8")

    linter = WikiHealthLinter(project_root=tmp_path)
    issues = linter.check_broken_knowledge_links()
    assert len(issues) == 1
    assert issues[0].subject == "Broken Knowledge Link"
    assert "non_existent_target.md" in issues[0].message
