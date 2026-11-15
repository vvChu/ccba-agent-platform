from __future__ import annotations

from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter


def get_full_annotation_field_id(annotation: Any) -> str | None:
    """Resolve the hierarchical dotted field identifier for a PDF widget annotation."""
    components: list[str] = []
    while annotation:
        field_name = annotation.get("/T")
        if field_name:
            components.append(field_name)
        annotation = annotation.get("/Parent")
    return ".".join(reversed(components)) if components else None


def make_field_dict(field: Any, field_id: str) -> dict[str, Any]:
    """Build a normalized field descriptor dictionary from a pypdf field object."""
    field_dict: dict[str, Any] = {"field_id": field_id}
    ft = field.get("/FT")
    if ft == "/Tx":
        field_dict["type"] = "text"
    elif ft == "/Btn":
        field_dict["type"] = "checkbox"
        states = field.get("/_States_", [])
        if len(states) == 2:
            if "/Off" in states:
                field_dict["checked_value"] = states[0] if states[0] != "/Off" else states[1]
                field_dict["unchecked_value"] = "/Off"
            else:
                field_dict["checked_value"] = states[0]
                field_dict["unchecked_value"] = states[1]
    elif ft == "/Ch":
        field_dict["type"] = "choice"
        states = field.get("/_States_", [])
        field_dict["choice_options"] = [{"value": state[0], "text": state[1]} for state in states]
    else:
        field_dict["type"] = f"unknown ({ft})"
    return field_dict


def _collect_radio_and_page_positions(
    reader: PdfReader,
    field_info_by_id: dict[str, dict[str, Any]],
    possible_radio_names: set[str],
) -> dict[str, dict[str, Any]]:
    """Populate page coordinates on known fields and extract radio group options."""
    radio_fields_by_id: dict[str, dict[str, Any]] = {}
    for page_index, page in enumerate(reader.pages):
        annotations = page.get("/Annots", [])
        for ann in annotations:
            ann_resolved = ann.get_object() if hasattr(ann, "get_object") else ann
            field_id = get_full_annotation_field_id(ann_resolved)
            if field_id in field_info_by_id:
                field_info_by_id[field_id]["page"] = page_index + 1
                field_info_by_id[field_id]["rect"] = ann_resolved.get("/Rect")
            elif field_id in possible_radio_names:
                on_values: list[str] = []
                try:
                    ap = ann_resolved.get("/AP")
                    if ap:
                        n = ap.get("/N")
                        on_values = [v for v in n if v != "/Off"] if n else []
                except (KeyError, TypeError):
                    continue
                if len(on_values) == 1:
                    rect = ann_resolved.get("/Rect")
                    if field_id not in radio_fields_by_id:
                        radio_fields_by_id[field_id] = {
                            "field_id": field_id,
                            "type": "radio_group",
                            "page": page_index + 1,
                            "radio_options": [],
                        }
                    radio_fields_by_id[field_id]["radio_options"].append(
                        {"value": on_values[0], "rect": rect}
                    )
    return radio_fields_by_id


def get_field_info(reader: PdfReader) -> list[dict[str, Any]]:
    """Extract form field metadata, page numbers, and widget bounding boxes from a PDF."""
    fields = reader.get_fields()
    if not fields:
        return []

    field_info_by_id: dict[str, dict[str, Any]] = {}
    possible_radio_names: set[str] = set()

    for field_id, field in fields.items():
        if field.get("/Kids"):
            if field.get("/FT") == "/Btn":
                possible_radio_names.add(field_id)
            continue
        field_info_by_id[field_id] = make_field_dict(field, field_id)

    radio_fields_by_id = _collect_radio_and_page_positions(
        reader, field_info_by_id, possible_radio_names
    )
    for r_field in radio_fields_by_id.values():
        field_info_by_id[r_field["field_id"]] = r_field

    return list(field_info_by_id.values())


def fill_pdf_fields(
    input_pdf_path: str | Path,
    fields_data: list[dict[str, Any]],
    output_pdf_path: str | Path,
) -> None:
    """Fill PDF AcroForm fields from structured per-page field entries and write output PDF."""
    fields_by_page: dict[int, dict[str, Any]] = {}
    for field in fields_data:
        if "value" in field:
            field_id = field["field_id"]
            page = int(field["page"])
            if page not in fields_by_page:
                fields_by_page[page] = {}
            fields_by_page[page][field_id] = field["value"]

    reader = PdfReader(str(input_pdf_path))
    writer = PdfWriter(clone_from=reader)

    for page, field_values in fields_by_page.items():
        writer.update_page_form_field_values(
            writer.pages[page - 1], field_values, auto_regenerate=False
        )

    writer.set_need_appearances_writer(True)
    with open(output_pdf_path, "wb") as f:
        writer.write(f)
