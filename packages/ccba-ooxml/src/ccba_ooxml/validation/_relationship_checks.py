"""OOXML ID uniqueness, file references, and relationship ID validation checks."""

from __future__ import annotations

from pathlib import Path

import lxml.etree

from ._parsed_package import (
    CONTENT_TYPES_NAMESPACE,
    ParsedOOXMLPackage,
    ParsedXMLFile,
    ValidationDiagnostic,
    make_diagnostic,
)

UNIQUE_ID_REQUIREMENTS: dict[str, tuple[str, str]] = {
    "comment": ("id", "file"),
    "commentrangestart": ("id", "file"),
    "commentrangeend": ("id", "file"),
    "bookmarkstart": ("id", "file"),
    "bookmarkend": ("id", "file"),
    "sldid": ("id", "file"),
    "sldmasterid": ("id", "global"),
    "sldlayoutid": ("id", "global"),
    "cm": ("authorid", "file"),
    "sheet": ("sheetid", "file"),
    "definedname": ("id", "file"),
    "cxnsp": ("id", "file"),
    "sp": ("id", "file"),
    "pic": ("id", "file"),
    "grpsp": ("id", "file"),
}

MC_NAMESPACE = "http://schemas.openxmlformats.org/markup-compatibility/2006"
XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace"
PACKAGE_RELATIONSHIPS_NAMESPACE = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFICE_RELATIONSHIPS_NAMESPACE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
)


def _extract_attr_value(elem: lxml.etree._Element, target_attr: str) -> str | None:
    """Return value of case-insensitive local attribute name on ``elem``."""
    for attr, value in elem.attrib.items():
        attr_str = str(attr)
        attr_local = attr_str.split("}")[-1].lower() if "}" in attr_str else attr_str.lower()
        if attr_local == target_attr:
            return str(value)
    return None


def _record_id_occurrence(
    rel_path: str,
    line_num: int | None,
    tag: str,
    attr_name: str,
    scope: str,
    id_value: str,
    global_ids: dict[str, tuple[str, int | None, str]],
    file_ids: dict[tuple[str, str], dict[str, int | None]],
    diagnostics: list[ValidationDiagnostic],
) -> None:
    """Track an ID attribute and append a diagnostic when duplicated."""
    if scope == "global":
        if id_value in global_ids:
            prev_file, prev_line, prev_tag = global_ids[id_value]
            msg = f"Global ID '{id_value}' in <{tag}> already used in {prev_file} at line {prev_line} in <{prev_tag}>"
            diagnostics.append(make_diagnostic(msg, rel_path, line_num))
        else:
            global_ids[id_value] = (rel_path, line_num, tag)
        return

    seen = file_ids.setdefault((tag, attr_name), {})
    if id_value in seen:
        msg = f"Duplicate {attr_name}='{id_value}' in <{tag}> (first occurrence at line {seen[id_value]})"
        diagnostics.append(make_diagnostic(msg, rel_path, line_num))
    else:
        seen[id_value] = line_num


def _check_entry_unique_ids(
    entry: ParsedXMLFile,
    mc_ns: str,
    unique_reqs: dict[str, tuple[str, str]],
    global_ids: dict[str, tuple[str, int | None, str]],
) -> list[ValidationDiagnostic]:
    """Validate global and file-scoped ID uniqueness on a cloned XML root."""
    diagnostics: list[ValidationDiagnostic] = []
    cloned_root = entry.clone_root()
    if cloned_root is None:
        return diagnostics

    mc_nodes = cloned_root.xpath(".//mc:AlternateContent", namespaces={"mc": mc_ns})
    if isinstance(mc_nodes, list):
        for elem in mc_nodes:
            parent = elem.getparent() if hasattr(elem, "getparent") else None
            if parent is not None:
                parent.remove(elem)

    file_ids: dict[tuple[str, str], dict[str, int | None]] = {}
    for elem in cloned_root.iter():
        tag_str = str(elem.tag)
        tag = tag_str.split("}")[-1].lower() if "}" in tag_str else tag_str.lower()
        if tag not in unique_reqs:
            continue
        attr_name, scope = unique_reqs[tag]
        id_value = _extract_attr_value(elem, attr_name)
        if id_value is not None:
            _record_id_occurrence(
                entry.rel_path,
                elem.sourceline,
                tag,
                attr_name,
                scope,
                id_value,
                global_ids,
                file_ids,
                diagnostics,
            )
    return diagnostics


def check_unique_ids(
    package: ParsedOOXMLPackage, mc_ns: str, unique_reqs: dict[str, tuple[str, str]]
) -> list[ValidationDiagnostic]:
    """Validate global and file-level unique IDs across all XML files."""
    diagnostics: list[ValidationDiagnostic] = []
    global_ids: dict[str, tuple[str, int | None, str]] = {}
    for xml_file in package.xml_files:
        entry = package.get_entry(xml_file)
        if entry.parse_error is not None:
            err_msg, line_num = entry.parse_error
            diagnostics.append(
                make_diagnostic(
                    err_msg, entry.rel_path, line_num, f"  {entry.rel_path}: Error: {err_msg}"
                )
            )
            continue
        diagnostics.extend(_check_entry_unique_ids(entry, mc_ns, unique_reqs, global_ids))
    return diagnostics


def expected_relationship_type(element_name: str, explicit_map: dict[str, str]) -> str | None:
    """Resolve expected relationship type for an element name."""
    elem_lower = element_name.lower()
    if elem_lower in explicit_map:
        return explicit_map[elem_lower]
    if elem_lower.endswith("id") and len(elem_lower) > 2:
        prefix = elem_lower[:-2]
        return "slide" if prefix == "sld" else prefix.lower()
    if elem_lower.endswith("reference") and len(elem_lower) > 9:
        return elem_lower[:-9].lower()
    return None


def _check_single_rels_targets(
    package: ParsedOOXMLPackage, rels_file: Path, pkg_rel_ns: str
) -> tuple[set[Path], list[ValidationDiagnostic]]:
    """Inspect one ``.rels`` file and return resolved target paths plus errors."""
    entry = package.get_entry(rels_file)
    if entry.root is None:
        err_msg, line_num = entry.parse_error or ("Parse failed", None)
        return set(), [
            make_diagnostic(
                err_msg, entry.rel_path, line_num, f"  Error parsing {entry.rel_path}: {err_msg}"
            )
        ]

    referenced: set[Path] = set()
    diagnostics: list[ValidationDiagnostic] = []
    base_dir = package.unpacked_dir if rels_file.name == ".rels" else rels_file.parent.parent
    for rel in entry.root.findall(".//ns:Relationship", namespaces={"ns": pkg_rel_ns}):
        target = rel.get("Target")
        if not target or target.startswith(("http", "mailto:")):
            continue
        try:
            target_path = (base_dir / target).resolve()
            if target_path.exists() and target_path.is_file():
                referenced.add(target_path)
                continue
        except (OSError, ValueError):
            pass
        diagnostics.append(
            make_diagnostic(f"Broken reference to {target}", entry.rel_path, rel.sourceline)
        )
    return referenced, diagnostics


def check_file_references(
    package: ParsedOOXMLPackage, pkg_rel_ns: str
) -> tuple[bool, list[ValidationDiagnostic]]:
    """Validate bidirectional consistency between ``.rels`` targets and unpacked files."""
    if not package.rels_files:
        return False, []
    all_targets = [
        f.resolve()
        for f in package.all_files
        if f.name != "[Content_Types].xml" and not f.name.endswith(".rels")
    ]
    all_referenced: set[Path] = set()
    diagnostics: list[ValidationDiagnostic] = []
    for rels_file in package.rels_files:
        refs, rel_diags = _check_single_rels_targets(package, rels_file, pkg_rel_ns)
        all_referenced.update(refs)
        diagnostics.extend(rel_diags)

    for unref in sorted(set(all_targets) - all_referenced):
        rel_str = unref.relative_to(package.unpacked_dir).as_posix()
        msg = f"Unreferenced file: {rel_str}"
        diagnostics.append(make_diagnostic(msg, rel_str, None, f"  {msg}"))
    return True, diagnostics


def _collect_rid_types(
    package: ParsedOOXMLPackage, rels_file: Path, pkg_rel_ns: str
) -> tuple[dict[str, str], list[ValidationDiagnostic]]:
    """Load relationship ID -> type mapping and report duplicate rIds."""
    entry = package.get_entry(rels_file)
    if entry.root is None:
        err_msg, line_num = entry.parse_error or ("Parse failed", None)
        return {}, [
            make_diagnostic(
                err_msg, entry.rel_path, line_num, f"  Error processing {entry.rel_path}: {err_msg}"
            )
        ]

    rid_to_type: dict[str, str] = {}
    diagnostics: list[ValidationDiagnostic] = []
    for rel in entry.root.findall(f".//{{{pkg_rel_ns}}}Relationship"):
        rid = rel.get("Id")
        if not rid:
            continue
        if rid in rid_to_type:
            diagnostics.append(
                make_diagnostic(
                    f"Duplicate relationship ID '{rid}' (IDs must be unique)",
                    entry.rel_path,
                    rel.sourceline,
                )
            )
        rel_type = rel.get("Type", "")
        rid_to_type[rid] = rel_type.split("/")[-1] if "/" in rel_type else rel_type
    return rid_to_type, diagnostics


def _check_xml_rid_attrs(
    entry: ParsedXMLFile,
    rid_to_type: dict[str, str],
    office_rel_ns: str,
    explicit_map: dict[str, str],
    diagnostics: list[ValidationDiagnostic],
) -> None:
    """Validate every ``r:id`` attribute on elements in ``entry.root``."""
    assert entry.root is not None
    attr_key = f"{{{office_rel_ns}}}id"
    for elem in entry.root.iter():
        rid_attr = elem.get(attr_key)
        if not rid_attr:
            continue
        tag_str = str(elem.tag)
        elem_name = tag_str.split("}")[-1] if "}" in tag_str else tag_str
        if rid_attr not in rid_to_type:
            preview = ", ".join(sorted(rid_to_type.keys())[:5])
            suffix = "..." if len(rid_to_type) > 5 else ""
            msg = f"<{elem_name}> references non-existent relationship '{rid_attr}' (valid IDs: {preview}{suffix})"
            diagnostics.append(make_diagnostic(msg, entry.rel_path, elem.sourceline))
        elif explicit_map:
            expected_type = expected_relationship_type(elem_name, explicit_map)
            if expected_type and expected_type not in rid_to_type[rid_attr].lower():
                msg = f"<{elem_name}> references '{rid_attr}' which points to '{rid_to_type[rid_attr]}' but should point to a '{expected_type}' relationship"
                diagnostics.append(make_diagnostic(msg, entry.rel_path, elem.sourceline))


def check_all_relationship_ids(
    package: ParsedOOXMLPackage,
    pkg_rel_ns: str,
    office_rel_ns: str,
    explicit_map: dict[str, str],
) -> list[ValidationDiagnostic]:
    """Validate that ``r:id`` attributes reference existing relationship entries and types."""
    diagnostics: list[ValidationDiagnostic] = []
    for xml_file in package.xml_files:
        if xml_file.name.endswith(".rels"):
            continue
        rels_file = xml_file.parent / "_rels" / f"{xml_file.name}.rels"
        if not rels_file.exists():
            continue
        rid_to_type, rel_diags = _collect_rid_types(package, rels_file, pkg_rel_ns)
        diagnostics.extend(rel_diags)
        entry = package.get_entry(xml_file)
        if entry.root is None:
            if entry.parse_error:
                err_msg, line_num = entry.parse_error
                diagnostics.append(
                    make_diagnostic(
                        err_msg,
                        entry.rel_path,
                        line_num,
                        f"  Error processing {entry.rel_path}: {err_msg}",
                    )
                )
            continue
        _check_xml_rid_attrs(entry, rid_to_type, office_rel_ns, explicit_map, diagnostics)
    return diagnostics


__all__ = [
    "CONTENT_TYPES_NAMESPACE",
    "MC_NAMESPACE",
    "OFFICE_RELATIONSHIPS_NAMESPACE",
    "PACKAGE_RELATIONSHIPS_NAMESPACE",
    "UNIQUE_ID_REQUIREMENTS",
    "XML_NAMESPACE",
    "check_all_relationship_ids",
    "check_file_references",
    "check_unique_ids",
    "expected_relationship_type",
]
