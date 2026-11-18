"""Offline XSD schema compilation, namespace sanitization, and dual-path validation."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import lxml.etree

from ._parsed_package import ParsedOOXMLPackage, clone_element_tree, make_secure_xml_parser
from ._relationship_checks import MC_NAMESPACE

_TEMPLATE_TAG_RE = re.compile(r"\{\{[^}]*\}\}")

SCHEMA_MAPPINGS: dict[str, str] = {
    "word": "ISO-IEC29500-4_2016/wml.xsd",
    "ppt": "ISO-IEC29500-4_2016/pml.xsd",
    "xl": "ISO-IEC29500-4_2016/sml.xsd",
    "[Content_Types].xml": "ecma/fouth-edition/opc-contentTypes.xsd",
    "app.xml": "ISO-IEC29500-4_2016/shared-documentPropertiesExtended.xsd",
    "core.xml": "ecma/fouth-edition/opc-coreProperties.xsd",
    "custom.xml": "ISO-IEC29500-4_2016/shared-documentPropertiesCustom.xsd",
    ".rels": "ecma/fouth-edition/opc-relationships.xsd",
    "people.xml": "microsoft/wml-2012.xsd",
    "commentsIds.xml": "microsoft/wml-cid-2016.xsd",
    "commentsExtensible.xml": "microsoft/wml-cex-2018.xsd",
    "commentsExtended.xml": "microsoft/wml-2012.xsd",
    "chart": "ISO-IEC29500-4_2016/dml-chart.xsd",
    "theme": "ISO-IEC29500-4_2016/dml-main.xsd",
    "drawing": "ISO-IEC29500-4_2016/dml-main.xsd",
}

MAIN_CONTENT_FOLDERS: set[str] = {"word", "ppt", "xl"}

OOXML_NAMESPACES: set[str] = {
    "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "http://schemas.openxmlformats.org/schemaLibrary/2006/main",
    "http://schemas.openxmlformats.org/drawingml/2006/main",
    "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "http://schemas.openxmlformats.org/drawingml/2006/chartDrawing",
    "http://schemas.openxmlformats.org/drawingml/2006/diagram",
    "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
    "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "http://schemas.openxmlformats.org/presentationml/2006/main",
    "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "http://schemas.openxmlformats.org/officeDocument/2006/sharedTypes",
    "http://www.w3.org/XML/1998/namespace",
}

COMPILED_SCHEMA_CACHE: dict[Path, lxml.etree.XMLSchema] = {}


class OfflineSchemaResolver(lxml.etree.Resolver):
    """Custom XML resolver to intercept external schema URLs and route to local files."""

    def __init__(self, schemas_dir: Path) -> None:
        super().__init__()
        self.schemas_dir = schemas_dir
        self.dublincore_dir = schemas_dir / "dublincore"
        self.xml_xsd_path = schemas_dir / "ISO-IEC29500-4_2016" / "xml.xsd"

    def resolve(self, url: str, pubid: str | None, context: Any) -> Any:
        """Resolve known external schema imports to local files inside ``schemas_dir``."""
        url_lower = url.lower()
        target_map = (
            ("dcterms.xsd", self.dublincore_dir / "dcterms.xsd"),
            ("dcmitype.xsd", self.dublincore_dir / "dcmitype.xsd"),
            ("dc.xsd", self.dublincore_dir / "dc.xsd"),
            ("xml.xsd", self.xml_xsd_path),
        )
        for marker, candidate in target_map:
            if marker in url_lower and candidate.exists():
                return self.resolve_filename(str(candidate), context)
        return None


def get_compiled_schema(
    schema_path: Path,
    schemas_dir: Path,
    cache: dict[Path, lxml.etree.XMLSchema] | None = None,
) -> lxml.etree.XMLSchema:
    """Load and compile an XMLSchema with offline resolution and caching."""
    target_cache = COMPILED_SCHEMA_CACHE if cache is None else cache
    resolved_path = schema_path.resolve()
    if resolved_path in target_cache:
        return target_cache[resolved_path]

    parser = make_secure_xml_parser()
    parser.resolvers.add(OfflineSchemaResolver(schemas_dir))

    with open(resolved_path, "rb") as xsd_file:
        xsd_doc = lxml.etree.parse(xsd_file, parser=parser, base_url=str(resolved_path))
        schema = lxml.etree.XMLSchema(xsd_doc)

    target_cache[resolved_path] = schema
    return schema


def resolve_schema_path(
    xml_file: Path,
    schemas_dir: Path,
    schema_mappings: dict[str, str],
    main_content_folders: set[str],
) -> Path | None:
    """Determine the local XSD schema path corresponding to ``xml_file``."""
    if xml_file.name in schema_mappings:
        return schemas_dir / schema_mappings[xml_file.name]
    if xml_file.name.endswith(".rels"):
        return schemas_dir / schema_mappings[".rels"]
    if "charts/" in str(xml_file) and xml_file.name.startswith("chart"):
        return schemas_dir / schema_mappings["chart"]
    if "theme/" in str(xml_file) and xml_file.name.startswith("theme"):
        return schemas_dir / schema_mappings["theme"]
    if xml_file.parent.name in main_content_folders:
        return schemas_dir / schema_mappings[xml_file.parent.name]
    return None


def remove_ignorable_elements(root: Any, allowed_namespaces: set[str]) -> None:
    """Recursively remove child elements outside allowed OOXML namespaces."""
    elements_to_remove = []
    for elem in list(root):
        if not hasattr(elem, "tag") or callable(elem.tag):
            continue
        tag_str = str(elem.tag)
        if tag_str.startswith("{"):
            ns = tag_str.split("}")[0][1:]
            if ns not in allowed_namespaces:
                elements_to_remove.append(elem)
                continue
        remove_ignorable_elements(elem, allowed_namespaces)

    for elem in elements_to_remove:
        root.remove(elem)


def clean_ignorable_namespaces(xml_doc: Any, allowed_namespaces: set[str]) -> Any:
    """Clone ``xml_doc`` and strip non-OOXML attributes and child elements."""
    cloned_tree = clone_element_tree(xml_doc)
    xml_copy = cloned_tree.getroot()
    for elem in xml_copy.iter():
        attrs_to_remove = [
            attr
            for attr in elem.attrib
            if "{" in attr and str(attr).split("}")[0][1:] not in allowed_namespaces
        ]
        for attr in attrs_to_remove:
            del elem.attrib[attr]
    remove_ignorable_elements(xml_copy, allowed_namespaces)
    return cloned_tree


def preprocess_mc_ignorable(xml_doc: Any, mc_ns: str = MC_NAMESPACE) -> Any:
    """Strip ``mc:Ignorable`` from cloned root without mutating cached DOM."""
    root = xml_doc.getroot()
    attr_key = f"{{{mc_ns}}}Ignorable"
    if attr_key in root.attrib:
        del root.attrib[attr_key]
    return xml_doc


def remove_template_tags_from_text_nodes(xml_doc: Any) -> tuple[Any, list[str]]:
    """Strip ``{{ ... }}`` template tags from non-``w:t`` text nodes on a clone."""
    warnings: list[str] = []
    cloned_tree = clone_element_tree(xml_doc)
    xml_copy = cloned_tree.getroot()

    def _strip(text: str | None, kind: str) -> str | None:
        if not text:
            return text
        matches = list(_TEMPLATE_TAG_RE.finditer(text))
        if not matches:
            return text
        for match in matches:
            warnings.append(f"Found template tag in {kind}: {match.group()}")
        return _TEMPLATE_TAG_RE.sub("", text)

    for elem in xml_copy.iter():
        if not hasattr(elem, "tag") or callable(elem.tag):
            continue
        tag_str = str(elem.tag)
        if tag_str.endswith("}t") or tag_str == "t":
            continue
        elem.text = _strip(elem.text, "text content")
        elem.tail = _strip(elem.tail, "tail content")
    return cloned_tree, warnings


def _load_xml_doc_for_xsd(
    xml_file: Path,
    base_path: Path,
    parsed_package: ParsedOOXMLPackage | None,
) -> tuple[lxml.etree._ElementTree | None, str | None]:
    """Load XML via ``parsed_package`` for unpacked files or fresh parser for originals."""
    resolved_base = Path(base_path).resolve()
    if parsed_package is not None and resolved_base == parsed_package.unpacked_dir:
        entry = parsed_package.get_entry(xml_file)
        if entry.parse_error is not None or entry.root is None:
            return None, entry.parse_error[0] if entry.parse_error else "Failed to parse XML"
        return lxml.etree.ElementTree(entry.clone_root()), None

    with open(xml_file, "rb") as handle:
        doc = lxml.etree.parse(handle, parser=make_secure_xml_parser())
    return doc, None


def validate_single_file_xsd(
    xml_file: Path,
    base_path: Path,
    schema: lxml.etree.XMLSchema,
    parsed_package: ParsedOOXMLPackage | None,
    allowed_namespaces: set[str],
    main_content_folders: set[str],
    mc_ns: str = MC_NAMESPACE,
) -> tuple[bool, set[str]]:
    """Run XSD validation on an independent cloned DOM for unpacked or original XML."""
    try:
        xml_doc, parse_err = _load_xml_doc_for_xsd(xml_file, base_path, parsed_package)
        if parse_err is not None or xml_doc is None:
            return False, {parse_err or "Failed to parse XML"}

        xml_doc, _ = remove_template_tags_from_text_nodes(xml_doc)
        xml_doc = preprocess_mc_ignorable(xml_doc, mc_ns=mc_ns)
        relative_path = xml_file.relative_to(base_path)
        if relative_path.parts and relative_path.parts[0] in main_content_folders:
            xml_doc = clean_ignorable_namespaces(xml_doc, allowed_namespaces)

        if schema.validate(xml_doc):
            return True, set()
        return False, {error.message for error in schema.error_log}
    except Exception as exc:
        return False, {str(exc)}


__all__ = [
    "COMPILED_SCHEMA_CACHE",
    "MAIN_CONTENT_FOLDERS",
    "OOXML_NAMESPACES",
    "OfflineSchemaResolver",
    "SCHEMA_MAPPINGS",
    "clean_ignorable_namespaces",
    "get_compiled_schema",
    "preprocess_mc_ignorable",
    "remove_ignorable_elements",
    "remove_template_tags_from_text_nodes",
    "resolve_schema_path",
    "validate_single_file_xsd",
]
