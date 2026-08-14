"""Unit tests for ccba-pdf-prep document skills (PDF forms) and domain boundary purity."""

import ccba_pdf_prep
from ccba_pdf_prep import fill_pdf_fields, get_field_info


def test_pdf_form_skills_exports():
    """Verify PDF form skills are properly exposed in public API."""
    assert get_field_info is not None
    assert fill_pdf_fields is not None


def test_domain_purity_no_xlsx_recalc_export():
    """Verify that recalc_xlsx is not exported in ccba_pdf_prep (ADR-012/ADR-013)."""
    assert "recalc_xlsx" not in ccba_pdf_prep.__all__
    assert not hasattr(ccba_pdf_prep, "recalc_xlsx")
