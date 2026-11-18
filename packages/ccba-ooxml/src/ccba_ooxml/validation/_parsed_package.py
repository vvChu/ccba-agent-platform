"""Immutable single-parse XML cache, core structural checks, and secure parser factory."""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import lxml.etree

_LINE_RE = re.compile(r"\bline\s+(\d+)\b", re.IGNORECASE)
CONTENT_TYPES_NAMESPACE = "http://schemas.openxmlformats.org/package/2006/content-types"

DECLARABLE_ROOTS = {
    "sld",
    "sldLayout",
    "sldMaster",
    "presentation",
    "document",
    "workbook",
    "worksheet",
    "theme",
}

MEDIA_EXTENSIONS = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "bmp": "image/bmp",
    "tiff": "image/tiff",
    "wmf": "image/x-wmf",
    "emf": "image/x-emf",
}


def make_secure_xml_parser() -> lxml.etree.XMLParser:
    """Create a fresh offline-hardened XMLParser for a single parse operation.

    Returning a new parser per parse prevents cross-thread contention and stale
    ``error_log`` accumulation inside lxml.
    """
    return lxml.etree.XMLParser(resolve_entities=False, no_network=True)


_make_secure_xml_parser = make_secure_xml_parser


def extract_error_line(exc: BaseException) -> int | None:
    """Extract a 1-based line number from an lxml exception when available."""
    lineno = getattr(exc, "lineno", None)
    if isinstance(lineno, int) and lineno > 0:
        return lineno
    position = getattr(exc, "position", None)
    if isinstance(position, tuple) and position and isinstance(position[0], int):
        if position[0] > 0:
            return position[0]
    match = _LINE_RE.search(str(exc))
    return int(match.group(1)) if match else None


@dataclass(frozen=True)
class ValidationDiagnostic:
    """Structured diagnostic emitted by modular validation helpers."""

    message: str
    severity: str = "ERROR"
    file_path: str | None = None
    line_number: int | None = None
    legacy_line: str = ""


def make_diagnostic(
    message: str,
    file_path: str | None = None,
    line_number: int | None = None,
    legacy_line: str | None = None,
) -> ValidationDiagnostic:
    """Create a normalized ``ValidationDiagnostic`` with consistent legacy formatting."""
    if legacy_line is None:
        if file_path and line_number is not None:
            legacy_line = f"  {file_path}: Line {line_number}: {message}"
        elif file_path:
            legacy_line = f"  {file_path}: {message}"
        else:
            legacy_line = f"  {message}"
    return ValidationDiagnostic(
        message=message, file_path=file_path, line_number=line_number, legacy_line=legacy_line
    )


@dataclass(frozen=True)
class ParsedXMLFile:
    """Cached parse record for one XML or .rels file inside an unpacked package."""

    rel_path: str
    path: Path
    tree: lxml.etree._ElementTree | None
    root: lxml.etree._Element | None
    parse_error: tuple[str, int | None] | None = None

    def clone_root(self) -> lxml.etree._Element | None:
        """Return an independent deep copy of the parsed XML root element."""
        return copy.deepcopy(self.root) if self.root is not None else None


class ParsedOOXMLPackage:
    """Single-parse DOM cache with deterministic sorted file discovery."""

    def __init__(self, unpacked_dir: str | Path) -> None:
        """Index XML/.rels files in ``unpacked_dir`` sorted deterministically."""
        self.unpacked_dir: Path = Path(unpacked_dir).resolve()
        raw_xml = [*self.unpacked_dir.rglob("*.xml"), *self.unpacked_dir.rglob("*.rels")]
        self.xml_files: list[Path] = sorted(
            raw_xml, key=lambda p: p.relative_to(self.unpacked_dir).as_posix()
        )
        self.rels_files: list[Path] = [p for p in self.xml_files if p.name.endswith(".rels")]
        self._all_files: list[Path] | None = None
        self._entries: dict[str, ParsedXMLFile] = {}

    @property
    def all_files(self) -> list[Path]:
        """Return all regular files in ``unpacked_dir`` sorted by POSIX rel path."""
        if self._all_files is None:
            self._all_files = sorted(
                (p for p in self.unpacked_dir.rglob("*") if p.is_file()),
                key=lambda p: p.relative_to(self.unpacked_dir).as_posix(),
            )
        return self._all_files

    def _resolve_target(self, path_or_rel: str | Path) -> tuple[str, Path]:
        """Resolve an arbitrary path or relative string inside ``unpacked_dir``."""
        candidate = Path(path_or_rel)
        if not candidate.is_absolute():
            candidate = self.unpacked_dir / candidate
        resolved = candidate.resolve()
        try:
            rel_key = resolved.relative_to(self.unpacked_dir).as_posix()
        except ValueError:
            rel_key = candidate.as_posix()
        return rel_key, resolved

    def rel_path_str(self, path_or_rel: str | Path) -> str:
        """Normalize a path inside ``unpacked_dir`` to POSIX relative string."""
        rel_key, _ = self._resolve_target(path_or_rel)
        return rel_key

    def get_entry(self, path_or_rel: str | Path) -> ParsedXMLFile:
        """Return cached ``ParsedXMLFile``, parsing at most once per relative path."""
        rel_key, resolved = self._resolve_target(path_or_rel)
        if rel_key in self._entries:
            return self._entries[rel_key]
        try:
            tree = lxml.etree.parse(str(resolved), parser=make_secure_xml_parser())
            entry = ParsedXMLFile(rel_key, resolved, tree, tree.getroot(), None)
        except (lxml.etree.XMLSyntaxError, OSError) as exc:
            entry = ParsedXMLFile(
                rel_key, resolved, None, None, (str(exc), extract_error_line(exc))
            )
        self._entries[rel_key] = entry
        return entry

    def get_root(self, path_or_rel: str | Path) -> lxml.etree._Element:
        """Return read-only cached XML root element, raising if parsing failed."""
        entry = self.get_entry(path_or_rel)
        if entry.parse_error is not None or entry.root is None:
            msg, line = entry.parse_error or ("Failed to parse XML", None)
            raise lxml.etree.XMLSyntaxError(msg, None, line or 0, 0)
        return entry.root

    def clone_root(self, path_or_rel: str | Path) -> lxml.etree._Element:
        """Return mutable deep-cloned root element while keeping cache immutable."""
        return copy.deepcopy(self.get_root(path_or_rel))

    def invalidate(self, path_or_rel: str | Path | None = None) -> None:
        """Clear cached parse entry (or whole cache when ``None``)."""
        if path_or_rel is None:
            self._entries.clear()
            return
        rel_key, _ = self._resolve_target(path_or_rel)
        self._entries.pop(rel_key, None)


def clone_element_tree(xml_doc: Any) -> lxml.etree._ElementTree:
    """Deep-copy an Element or ElementTree into an independent ElementTree."""
    root = xml_doc.getroot() if hasattr(xml_doc, "getroot") else xml_doc
    return lxml.etree.ElementTree(copy.deepcopy(root))


def check_xml_wellformed(package: ParsedOOXMLPackage) -> list[ValidationDiagnostic]:
    """Validate that all XML and .rels files inside ``package`` parse cleanly."""
    diagnostics: list[ValidationDiagnostic] = []
    for xml_file in package.xml_files:
        entry = package.get_entry(xml_file)
        if entry.parse_error is None:
            continue
        err_msg, line_num = entry.parse_error
        prefix = f"Line {line_num}: " if line_num is not None else "Unexpected error: "
        diagnostics.append(
            make_diagnostic(
                err_msg, entry.rel_path, line_num, f"  {entry.rel_path}: {prefix}{err_msg}"
            )
        )
    return diagnostics


def check_namespaces(package: ParsedOOXMLPackage) -> list[ValidationDiagnostic]:
    """Check that prefixes listed in Ignorable attributes are declared on root."""
    diagnostics: list[ValidationDiagnostic] = []
    for xml_file in package.xml_files:
        entry = package.get_entry(xml_file)
        if entry.root is None:
            continue
        declared = {k for k in entry.root.nsmap if k is not None}
        for attr_name, attr_val in entry.root.attrib.items():
            if not str(attr_name).endswith("Ignorable"):
                continue
            for ns in sorted(set(str(attr_val).split()) - declared):
                msg = f"Namespace '{ns}' in Ignorable but not declared"
                diagnostics.append(
                    make_diagnostic(
                        msg, entry.rel_path, entry.root.sourceline, f"  {entry.rel_path}: {msg}"
                    )
                )
    return diagnostics


def check_content_types(
    package: ParsedOOXMLPackage, ct_ns: str = CONTENT_TYPES_NAMESPACE
) -> tuple[bool, list[ValidationDiagnostic]]:
    """Validate XML Override and media Default entries against [Content_Types].xml."""
    ct_file = package.unpacked_dir / "[Content_Types].xml"
    if not ct_file.exists():
        return False, []
    entry = package.get_entry(ct_file)
    if entry.root is None:
        err_msg, line_num = entry.parse_error or ("Invalid XML", None)
        return True, [
            make_diagnostic(
                err_msg,
                "[Content_Types].xml",
                line_num,
                f"  Error parsing [Content_Types].xml: {err_msg}",
            )
        ]

    parts = {
        str(ov.get("PartName", "")).lstrip("/")
        for ov in entry.root.findall(f".//{{{ct_ns}}}Override")
        if ov.get("PartName") is not None
    }
    exts = {
        str(df.get("Extension", "")).lower()
        for df in entry.root.findall(f".//{{{ct_ns}}}Default")
        if df.get("Extension") is not None
    }
    diagnostics: list[ValidationDiagnostic] = []
    for xml_file in package.xml_files:
        rel_str = package.rel_path_str(xml_file)
        if any(s in rel_str for s in (".rels", "[Content_Types]", "docProps/", "_rels/")):
            continue
        xml_entry = package.get_entry(xml_file)
        if xml_entry.root is None:
            continue
        root_tag = str(xml_entry.root.tag)
        root_name = root_tag.split("}")[-1] if "}" in root_tag else root_tag
        if root_name in DECLARABLE_ROOTS and rel_str not in parts:
            msg = f"File with <{root_name}> root not declared in [Content_Types].xml"
            diagnostics.append(
                make_diagnostic(msg, rel_str, xml_entry.root.sourceline, f"  {rel_str}: {msg}")
            )
    _check_media_extensions(package, exts, diagnostics)
    return True, diagnostics


def _check_media_extensions(
    package: ParsedOOXMLPackage,
    declared_extensions: set[str],
    diagnostics: list[ValidationDiagnostic],
) -> None:
    """Verify non-XML media files declare their extension in [Content_Types].xml."""
    for file_path in package.all_files:
        if (
            file_path.suffix.lower() == ".xml"
            or file_path.name.lower().endswith(".rels")
            or file_path.name == "[Content_Types].xml"
        ):
            continue
        if "_rels" in file_path.parts or "docProps" in file_path.parts:
            continue
        ext = file_path.suffix.lstrip(".").lower()
        if ext and ext not in declared_extensions and ext in MEDIA_EXTENSIONS:
            rel_str = package.rel_path_str(file_path)
            msg = f'File with extension \'{ext}\' not declared in [Content_Types].xml - should add: <Default Extension="{ext}" ContentType="{MEDIA_EXTENSIONS[ext]}"/>'
            diagnostics.append(make_diagnostic(msg, rel_str, None, f"  {rel_str}: {msg}"))
