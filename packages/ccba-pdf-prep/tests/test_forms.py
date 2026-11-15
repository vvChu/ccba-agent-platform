"""Unit tests verifying PDF AcroForm field extraction and filling helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    DictionaryObject,
    NameObject,
    NumberObject,
    TextStringObject,
)

from ccba_pdf_prep.forms import (
    fill_pdf_fields,
    get_field_info,
    get_full_annotation_field_id,
    make_field_dict,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _build_acroform_pdf(path: Path) -> Path:
    """Create a 1-page PDF containing a single AcroForm text widget."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=400, height=400)

    widget = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Widget"),
            NameObject("/FT"): NameObject("/Tx"),
            NameObject("/T"): TextStringObject("full_name"),
            NameObject("/Rect"): ArrayObject(
                [NumberObject(50), NumberObject(300), NumberObject(200), NumberObject(320)]
            ),
            NameObject("/P"): page.indirect_reference,
        }
    )
    widget_ref = writer._add_object(widget)
    page[NameObject("/Annots")] = ArrayObject([widget_ref])
    writer._root_object[NameObject("/AcroForm")] = DictionaryObject(
        {NameObject("/Fields"): ArrayObject([widget_ref])}
    )

    with open(path, "wb") as f:
        writer.write(f)
    return path


def test_get_full_annotation_field_id_nested() -> None:
    """Nested widget annotations resolve to parent.child identifiers."""
    parent: dict[str, Any] = {"/T": "applicant"}
    child: dict[str, Any] = {"/T": "email", "/Parent": parent}
    assert get_full_annotation_field_id(child) == "applicant.email"
    assert get_full_annotation_field_id({}) is None


def test_make_field_dict_variants() -> None:
    """Verify text, checkbox, choice, and unknown AcroForm field descriptors."""
    assert make_field_dict({"/FT": "/Tx"}, "name") == {"field_id": "name", "type": "text"}
    assert make_field_dict({"/FT": "/Btn", "/_States_": ["/Yes", "/Off"]}, "agree") == {
        "field_id": "agree",
        "type": "checkbox",
        "checked_value": "/Yes",
        "unchecked_value": "/Off",
    }
    assert make_field_dict(
        {"/FT": "/Ch", "/_States_": [("a", "Alpha"), ("b", "Beta")]}, "tier"
    ) == {
        "field_id": "tier",
        "type": "choice",
        "choice_options": [
            {"value": "a", "text": "Alpha"},
            {"value": "b", "text": "Beta"},
        ],
    }
    assert make_field_dict({"/FT": "/Sig"}, "sig") == {
        "field_id": "sig",
        "type": "unknown (/Sig)",
    }


def test_get_field_info_and_fill_pdf_fields_roundtrip(tmp_path: Path) -> None:
    """AcroForm widget inspection and filling persist updated field values."""
    src_pdf = _build_acroform_pdf(tmp_path / "form.pdf")
    out_pdf = tmp_path / "filled.pdf"

    info = get_field_info(PdfReader(str(src_pdf)))
    assert len(info) == 1
    assert info[0]["field_id"] == "full_name"
    assert info[0]["type"] == "text"
    assert info[0]["page"] == 1

    fill_pdf_fields(
        src_pdf,
        [{"field_id": "full_name", "page": 1, "value": "CCBA Tester"}],
        out_pdf,
    )
    filled_fields = PdfReader(str(out_pdf)).get_fields()
    assert filled_fields is not None
    assert filled_fields["full_name"].get("/V") == "CCBA Tester"
