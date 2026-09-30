"""test_quarantine_linter.py - Unit and regression tests for AST Seam Linter & Quarantine Adapter.

Validates (PR-B1 Issue #439):
1. Parsing and validation of `# ccba:quarantine seam_id=<id> reason=<reason> until=<YYYY-MM-DD> issue=<url>`.
2. Rejection of invalid reasons, malformed URLs, and non-existent seam IDs.
3. Accurate expiration detection comparing against runner UTC date.
4. Enforcement of forbidden substitute import alignment (card must govern the imported module).
5. Prevention of path traversal in seam_id.
6. Quarantine path containment under adapters/quarantine/.
7. Strict quarantine mode rejecting legacy bypasses vs default grace period.
8. Dry-run quarantine audit reporting.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from scripts.governance.check_dependency_contracts import (
    DependencyASTVisitor,
    SeamCardRestriction,
)
from scripts.governance.check_dependency_contracts import (
    main as linter_main,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]

MOCK_CARD_MAP = {
    "pdf_preprocessor.v1": {
        "seam_id": "pdf_preprocessor.v1",
        "implementation_packages": ["ccba_pdf_prep"],
        "forbidden_substitute_imports": ["fitz", "pymupdf"],
        "import_path": "ccba_pdf_prep:PDFProcessingPipeline",
    },
    "legal_markdown.v1": {
        "seam_id": "legal_markdown.v1",
        "implementation_packages": ["mdconverter"],
        "forbidden_substitute_imports": ["fpdf"],
        "import_path": "mdconverter:ConversionPipeline",
    },
    "ooxml_processor.v1": {
        "seam_id": "ooxml_processor.v1",
        "implementation_packages": ["ccba_ooxml"],
        "forbidden_substitute_imports": ["docx", "openpyxl"],
        "import_path": "ccba_ooxml:DocxDocument",
    },
}

MOCK_RESTRICTIONS = {
    "fitz": SeamCardRestriction(
        seam_id="pdf_preprocessor.v1",
        allowed_packages={"ccba_pdf_prep"},
        seam_replacement="ccba_pdf_prep",
        forbidden_imports=["fitz", "pymupdf"],
    ),
    "pymupdf": SeamCardRestriction(
        seam_id="pdf_preprocessor.v1",
        allowed_packages={"ccba_pdf_prep"},
        seam_replacement="ccba_pdf_prep",
        forbidden_imports=["fitz", "pymupdf"],
    ),
    "docx": SeamCardRestriction(
        seam_id="ooxml_processor.v1",
        allowed_packages={"ccba_ooxml"},
        seam_replacement="ccba_ooxml",
        forbidden_imports=["docx", "openpyxl"],
    ),
    "fpdf": SeamCardRestriction(
        seam_id="legal_markdown.v1",
        allowed_packages={"mdconverter"},
        seam_replacement="mdconverter",
        forbidden_imports=["fpdf"],
    ),
}


def test_quarantine_valid_marker_exemption() -> None:
    """Verify that a valid quarantine marker permits import and records active quarantine."""
    code = """
import fitz  # ccba:quarantine seam_id=pdf_preprocessor.v1 reason=hardware_mismatch until=2026-12-31 issue=https://github.com/vvChu/ccba-agent-platform/issues/439
"""
    tree = ast.parse(code)
    visitor = DependencyASTVisitor(
        current_package="ccba_qc_core",
        current_file=Path("packages/ccba-qc-core/src/ccba_qc_core/audit.py"),
        raw_lines=code.splitlines(),
        bypass_restrictions=MOCK_RESTRICTIONS,
        card_map=MOCK_CARD_MAP,
    )
    visitor.visit(tree)

    assert len(visitor.violations) == 0
    assert len(visitor.active_quarantines) == 1
    assert visitor.active_quarantines[0][2] == "fitz"
    assert visitor.active_quarantines[0][3] == "pdf_preprocessor.v1"


def test_quarantine_missing_required_fields() -> None:
    """Verify that missing any required quarantine parameter triggers QuarantineMarkerViolation."""
    code = """
import fitz  # ccba:quarantine seam_id=pdf_preprocessor.v1 reason=hardware_mismatch
"""
    tree = ast.parse(code)
    visitor = DependencyASTVisitor(
        current_package="ccba_qc_core",
        current_file=Path("packages/ccba-qc-core/src/ccba_qc_core/audit.py"),
        raw_lines=code.splitlines(),
        bypass_restrictions=MOCK_RESTRICTIONS,
        card_map=MOCK_CARD_MAP,
    )
    visitor.visit(tree)

    assert len(visitor.violations) == 1
    v = visitor.violations[0]
    assert v.rule_name == "QuarantineMarkerViolation"
    assert "missing required field(s)" in v.message
    assert "until" in v.message
    assert "issue" in v.message


def test_quarantine_invalid_reason() -> None:
    """Verify that unsupported reason triggers QuarantineMarkerViolation."""
    code = """
import fitz  # ccba:quarantine seam_id=pdf_preprocessor.v1 reason=too_lazy_to_refactor until=2026-12-31 issue=https://github.com/vvChu/ccba-agent-platform/issues/439
"""
    tree = ast.parse(code)
    visitor = DependencyASTVisitor(
        current_package="ccba_qc_core",
        current_file=Path("packages/ccba-qc-core/src/ccba_qc_core/audit.py"),
        raw_lines=code.splitlines(),
        bypass_restrictions=MOCK_RESTRICTIONS,
        card_map=MOCK_CARD_MAP,
    )
    visitor.visit(tree)

    assert len(visitor.violations) == 1
    assert visitor.violations[0].rule_name == "QuarantineMarkerViolation"
    assert "Invalid quarantine reason 'too_lazy_to_refactor'" in visitor.violations[0].message


def test_quarantine_invalid_issue_format() -> None:
    """Verify that non-GitHub issue URLs trigger QuarantineMarkerViolation."""
    code = """
import fitz  # ccba:quarantine seam_id=pdf_preprocessor.v1 reason=hardware_mismatch until=2026-12-31 issue=https://gitlab.com/issue/123
"""
    tree = ast.parse(code)
    visitor = DependencyASTVisitor(
        current_package="ccba_qc_core",
        current_file=Path("packages/ccba-qc-core/src/ccba_qc_core/audit.py"),
        raw_lines=code.splitlines(),
        bypass_restrictions=MOCK_RESTRICTIONS,
        card_map=MOCK_CARD_MAP,
    )
    visitor.visit(tree)

    assert len(visitor.violations) == 1
    assert visitor.violations[0].rule_name == "QuarantineMarkerViolation"
    assert "Invalid issue URL" in visitor.violations[0].message


def test_quarantine_expired_date() -> None:
    """Verify that an expired quarantine date triggers QuarantineExpiredViolation."""
    code = """
import fitz  # ccba:quarantine seam_id=pdf_preprocessor.v1 reason=hardware_mismatch until=2024-01-01 issue=https://github.com/vvChu/ccba-agent-platform/issues/439
"""
    tree = ast.parse(code)
    visitor = DependencyASTVisitor(
        current_package="ccba_qc_core",
        current_file=Path("packages/ccba-qc-core/src/ccba_qc_core/audit.py"),
        raw_lines=code.splitlines(),
        bypass_restrictions=MOCK_RESTRICTIONS,
        card_map=MOCK_CARD_MAP,
    )
    visitor.visit(tree)

    assert len(visitor.violations) == 1
    v = visitor.violations[0]
    assert v.rule_name == "QuarantineExpiredViolation"
    assert "expired on 2024-01-01" in v.message


def test_quarantine_mismatched_seam_forbidden_imports() -> None:
    """Verify that a quarantine marker for one card cannot be used to import forbidden modules of another."""
    # Attempting to use legal_markdown.v1 to exempt fitz
    code = """
import fitz  # ccba:quarantine seam_id=legal_markdown.v1 reason=hardware_mismatch until=2026-12-31 issue=https://github.com/vvChu/ccba-agent-platform/issues/439
"""
    tree = ast.parse(code)
    visitor = DependencyASTVisitor(
        current_package="ccba_qc_core",
        current_file=Path("packages/ccba-qc-core/src/ccba_qc_core/audit.py"),
        raw_lines=code.splitlines(),
        bypass_restrictions=MOCK_RESTRICTIONS,
        card_map=MOCK_CARD_MAP,
    )
    visitor.visit(tree)

    assert len(visitor.violations) == 1
    assert visitor.violations[0].rule_name == "QuarantineMarkerViolation"
    assert "does not govern forbidden module 'fitz'" in visitor.violations[0].message


def test_quarantine_path_traversal_in_seam_id() -> None:
    """Verify that directory traversal in seam_id is rejected."""
    code = """
import fitz  # ccba:quarantine seam_id=../../malicious reason=hardware_mismatch until=2026-12-31 issue=https://github.com/vvChu/ccba-agent-platform/issues/439
"""
    tree = ast.parse(code)
    visitor = DependencyASTVisitor(
        current_package="ccba_qc_core",
        current_file=Path("packages/ccba-qc-core/src/ccba_qc_core/audit.py"),
        raw_lines=code.splitlines(),
        bypass_restrictions=MOCK_RESTRICTIONS,
        card_map=MOCK_CARD_MAP,
    )
    visitor.visit(tree)

    assert len(visitor.violations) == 1
    assert visitor.violations[0].rule_name == "QuarantineMarkerViolation"
    assert "contains invalid path characters" in visitor.violations[0].message


def test_quarantine_strict_mode_rejects_legacy_bypass() -> None:
    """Verify that strict_quarantine=True rejects legacy # ccba:allow-raw-bypass."""
    code = """
import docx  # ccba:allow-raw-bypass (legacy comment)
"""
    tree = ast.parse(code)
    visitor = DependencyASTVisitor(
        current_package="ccba_ai",
        current_file=Path("packages/ccba-ai/src/ccba_ai/doc.py"),
        raw_lines=code.splitlines(),
        bypass_restrictions=MOCK_RESTRICTIONS,
        card_map=MOCK_CARD_MAP,
        strict_quarantine=True,
    )
    visitor.visit(tree)

    assert len(visitor.violations) == 1
    assert visitor.violations[0].rule_name == "LegacyBypassDeprecatedViolation"
    assert "uses legacy bypass" in visitor.violations[0].message


def test_quarantine_path_enforcement() -> None:
    """Verify that enforce_quarantine_path=True requires file to be in adapters/quarantine/."""
    code = """
import fitz  # ccba:quarantine seam_id=pdf_preprocessor.v1 reason=hardware_mismatch until=2026-12-31 issue=https://github.com/vvChu/ccba-agent-platform/issues/439
"""
    tree = ast.parse(code)

    # 1. Non-quarantine location
    bad_visitor = DependencyASTVisitor(
        current_package=None,
        current_file=Path("scripts/some_script.py"),
        raw_lines=code.splitlines(),
        bypass_restrictions=MOCK_RESTRICTIONS,
        card_map=MOCK_CARD_MAP,
        enforce_quarantine_path=True,
    )
    bad_visitor.visit(tree)
    assert len(bad_visitor.violations) == 1
    assert bad_visitor.violations[0].rule_name == "QuarantinePathViolation"

    # 2. Valid quarantine location
    good_visitor = DependencyASTVisitor(
        current_package=None,
        current_file=Path("adapters/quarantine/pdf_preprocessor.v1.py"),
        raw_lines=code.splitlines(),
        bypass_restrictions=MOCK_RESTRICTIONS,
        card_map=MOCK_CARD_MAP,
        enforce_quarantine_path=True,
    )
    good_visitor.visit(tree)
    assert len(good_visitor.violations) == 0


def test_dry_run_quarantine_cli(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that check_dependency_contracts --dry-run-quarantine outputs audit report."""
    rc = linter_main(["--dry-run-quarantine"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "QUARANTINE DRY-RUN AUDIT REPORT" in captured.out
    assert "Legacy Raw Bypasses" in captured.out
