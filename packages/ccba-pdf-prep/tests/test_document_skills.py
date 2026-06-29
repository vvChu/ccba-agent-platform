from ccba_pdf_prep import fill_pdf_fields, get_field_info, recalc_xlsx


def test_imports():
    assert get_field_info is not None
    assert fill_pdf_fields is not None
    assert recalc_xlsx is not None


def test_recalc_xlsx_nonexistent():
    res = recalc_xlsx("nonexistent.xlsx")
    assert "error" in res
    assert "exist" in res["error"]
