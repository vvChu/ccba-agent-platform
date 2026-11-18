"""Validator for PowerPoint presentation XML files against XSD schemas."""

from __future__ import annotations

import posixpath
import re
from pathlib import Path

import lxml.etree

from ._parsed_package import ValidationDiagnostic, extract_error_line, make_diagnostic
from .base import BaseSchemaValidator

_UUID_RE = re.compile(
    r"^[\{\(]?[0-9A-Fa-f]{8}-?[0-9A-Fa-f]{4}-?[0-9A-Fa-f]{4}-?[0-9A-Fa-f]{4}-?[0-9A-Fa-f]{12}[\}\)]?$"
)


def _parse_exception_diag(rel_path: str, exc: BaseException) -> ValidationDiagnostic:
    """Build a structured diagnostic from an XML parse or traversal exception."""
    return make_diagnostic(
        f"Error: {exc}",
        rel_path,
        extract_error_line(exc),
        f"  {rel_path}: Error: {exc}",
    )


def _canonicalize_rels_target(rels_rel_path: str, target: str) -> str | None:
    """Resolve an OOXML relationship ``Target`` to a canonical POSIX part path."""
    clean = target.strip().replace("\\", "/")
    if not clean or clean.lower().startswith(("http://", "https://", "mailto:")):
        return None
    if clean.startswith("/"):
        return posixpath.normpath(clean.lstrip("/"))

    rels_dir = posixpath.dirname(rels_rel_path)
    source_dir = (
        posixpath.dirname(rels_dir) if posixpath.basename(rels_dir) == "_rels" else rels_dir
    )
    joined = f"{source_dir}/{clean}" if source_dir else clean
    return posixpath.normpath(joined)


class PPTXSchemaValidator(BaseSchemaValidator):
    """Validator for PowerPoint presentation XML files against XSD schemas."""

    PRESENTATIONML_NAMESPACE = "http://schemas.openxmlformats.org/presentationml/2006/main"

    ELEMENT_RELATIONSHIP_TYPES = {
        "sldid": "slide",
        "sldmasterid": "slidemaster",
        "notesmasterid": "notesmaster",
        "sldlayoutid": "slidelayout",
        "themeid": "theme",
        "tablestyleid": "tablestyles",
    }

    def validate(self) -> bool:
        """Run all validation checks and return True if all pass."""
        self.reset_diagnostics()
        if not self.validate_xml():
            return False

        checks = (
            self.validate_namespaces,
            self.validate_unique_ids,
            self.validate_uuid_ids,
            self.validate_file_references,
            self.validate_slide_layout_ids,
            self.validate_content_types,
            self.validate_against_xsd,
            self.validate_notes_slide_references,
            self.validate_all_relationship_ids,
            self.validate_no_duplicate_slide_layouts,
        )
        all_valid = True
        for check in checks:
            if not check():
                all_valid = False
        return all_valid

    def _slide_master_files(self) -> list[Path]:
        """Return slide master XML paths in deterministic POSIX order."""
        masters_dir = self.unpacked_dir / "ppt" / "slideMasters"
        return [p for p in self.xml_files if p.parent == masters_dir and p.suffix == ".xml"]

    def _slide_rels_files(self) -> list[Path]:
        """Return slide relationship paths in deterministic POSIX order."""
        slides_rels_dir = self.unpacked_dir / "ppt" / "slides" / "_rels"
        return [
            p
            for p in self.parsed_package.rels_files
            if p.parent == slides_rels_dir and p.name.endswith(".xml.rels")
        ]

    def _check_file_uuid_ids(self, xml_file: Path) -> list[ValidationDiagnostic]:
        """Collect invalid UUID-like ID diagnostics for a single XML file."""
        rel_path = self.parsed_package.rel_path_str(xml_file)
        diagnostics: list[ValidationDiagnostic] = []
        try:
            root = self.parsed_package.get_root(xml_file)
            for elem in root.iter():
                for attr, value in elem.attrib.items():
                    attr_name = str(attr).split("}")[-1].lower()
                    if (attr_name == "id" or attr_name.endswith("id")) and self._looks_like_uuid(
                        str(value)
                    ):
                        if not _UUID_RE.match(str(value)):
                            msg = (
                                f"ID '{value}' appears to be a UUID but contains "
                                "invalid hex characters"
                            )
                            diagnostics.append(make_diagnostic(msg, rel_path, elem.sourceline))
        except (lxml.etree.XMLSyntaxError, Exception) as exc:
            diagnostics.append(_parse_exception_diag(rel_path, exc))
        return diagnostics

    def validate_uuid_ids(self) -> bool:
        """Validate that ID attributes that look like UUIDs contain only hex values."""
        diagnostics: list[ValidationDiagnostic] = []
        for xml_file in self.xml_files:
            diagnostics.extend(self._check_file_uuid_ids(xml_file))
        return self._emit_result(
            diagnostics,
            f"FAILED - Found {len(diagnostics)} UUID ID validation errors:",
            "PASSED - All UUID-like IDs contain valid hex values",
        )

    def _looks_like_uuid(self, value: str) -> bool:
        """Check if a value has the general structure of a UUID."""
        clean_value = value.strip("{}()").replace("-", "")
        return len(clean_value) == 32 and all(c.isalnum() for c in clean_value)

    def _check_single_slide_master(self, slide_master: Path) -> list[ValidationDiagnostic]:
        """Validate ``sldLayoutId`` relationship references for one slide master."""
        rel_master = self.parsed_package.rel_path_str(slide_master)
        rels_file = slide_master.parent / "_rels" / f"{slide_master.name}.rels"
        rel_rels = self.parsed_package.rel_path_str(rels_file)
        if not rels_file.exists():
            msg = f"Missing relationships file: {rel_rels}"
            return [make_diagnostic(msg, rel_master, None, f"  {rel_master}: {msg}")]

        diagnostics: list[ValidationDiagnostic] = []
        current_rel = rel_master
        try:
            root = self.parsed_package.get_root(slide_master)
            current_rel = rel_rels
            rels_root = self.parsed_package.get_root(rels_file)
            rel_tag = f".//{{{self.PACKAGE_RELATIONSHIPS_NAMESPACE}}}Relationship"
            valid_rids = {
                rel.get("Id")
                for rel in rels_root.findall(rel_tag)
                if "slideLayout" in rel.get("Type", "")
            }
            layout_tag = f".//{{{self.PRESENTATIONML_NAMESPACE}}}sldLayoutId"
            r_id_attr = f"{{{self.OFFICE_RELATIONSHIPS_NAMESPACE}}}id"
            for sld_layout_id in root.findall(layout_tag):
                r_id = sld_layout_id.get(r_id_attr)
                if r_id and r_id not in valid_rids:
                    layout_id = sld_layout_id.get("id")
                    msg = (
                        f"sldLayoutId with id='{layout_id}' references r:id='{r_id}' "
                        "which is not found in slide layout relationships"
                    )
                    diagnostics.append(make_diagnostic(msg, rel_master, sld_layout_id.sourceline))
        except (lxml.etree.XMLSyntaxError, Exception) as exc:
            diagnostics.append(_parse_exception_diag(current_rel, exc))
        return diagnostics

    def validate_slide_layout_ids(self) -> bool:
        """Validate that sldLayoutId elements in slide masters reference valid slide layouts."""
        slide_masters = self._slide_master_files()
        if not slide_masters:
            self.last_diagnostics = []
            if self.verbose:
                print("PASSED - No slide masters found")
            return True

        diagnostics: list[ValidationDiagnostic] = []
        for slide_master in slide_masters:
            diagnostics.extend(self._check_single_slide_master(slide_master))
        return self._emit_result(
            diagnostics,
            f"FAILED - Found {len(diagnostics)} slide layout ID validation errors:",
            "PASSED - All slide layout IDs reference valid slide layouts",
            extra_footer=(
                "Remove invalid references or add missing slide layouts to the relationships file."
            ),
        )

    def validate_no_duplicate_slide_layouts(self) -> bool:
        """Validate that each slide has exactly one slideLayout reference."""
        diagnostics: list[ValidationDiagnostic] = []
        rel_tag = f".//{{{self.PACKAGE_RELATIONSHIPS_NAMESPACE}}}Relationship"
        for rels_file in self._slide_rels_files():
            rel_path = self.parsed_package.rel_path_str(rels_file)
            try:
                root = self.parsed_package.get_root(rels_file)
                layout_rels = [
                    rel for rel in root.findall(rel_tag) if "slideLayout" in rel.get("Type", "")
                ]
                if len(layout_rels) > 1:
                    msg = f"has {len(layout_rels)} slideLayout references"
                    diagnostics.append(
                        make_diagnostic(
                            msg, rel_path, layout_rels[1].sourceline, f"  {rel_path}: {msg}"
                        )
                    )
            except Exception as exc:
                diagnostics.append(_parse_exception_diag(rel_path, exc))
        return self._emit_result(
            diagnostics,
            "FAILED - Found slides with duplicate slideLayout references:",
            "PASSED - All slides have exactly one slideLayout reference",
        )

    def _collect_notes_slide_refs(
        self, slide_rels_files: list[Path]
    ) -> tuple[dict[str, list[tuple[str, str, int | None]]], list[ValidationDiagnostic]]:
        """Collect canonical notesSlide targets mapped to ``(slide_name, rel_path, line)``."""
        references: dict[str, list[tuple[str, str, int | None]]] = {}
        parse_diags: list[ValidationDiagnostic] = []
        rel_tag = f".//{{{self.PACKAGE_RELATIONSHIPS_NAMESPACE}}}Relationship"

        for rels_file in slide_rels_files:
            rel_path = self.parsed_package.rel_path_str(rels_file)
            try:
                root = self.parsed_package.get_root(rels_file)
                slide_name = rels_file.stem.replace(".xml", "")
                for rel in root.findall(rel_tag):
                    if "notesSlide" not in rel.get("Type", ""):
                        continue
                    canon_target = _canonicalize_rels_target(rel_path, rel.get("Target", ""))
                    if canon_target is not None:
                        references.setdefault(canon_target, []).append(
                            (slide_name, rel_path, rel.sourceline)
                        )
            except (lxml.etree.XMLSyntaxError, Exception) as exc:
                parse_diags.append(_parse_exception_diag(rel_path, exc))
        return references, parse_diags

    def validate_notes_slide_references(self) -> bool:
        """Validate that each notesSlide file is referenced by only one slide."""
        slide_rels_files = self._slide_rels_files()
        if not slide_rels_files:
            self.last_diagnostics = []
            if self.verbose:
                print("PASSED - No slide relationship files found")
            return True

        notes_refs, diagnostics = self._collect_notes_slide_refs(slide_rels_files)
        for target, references in notes_refs.items():
            if len(references) <= 1:
                continue
            slide_names = [ref[0] for ref in references]
            msg = (
                f"Notes slide '{target}' is referenced by multiple slides: {', '.join(slide_names)}"
            )
            legacy_lines = [f"  {msg}", *(f"    - {rel_p}" for _, rel_p, _ in references)]
            diagnostics.append(
                make_diagnostic(msg, references[1][1], references[1][2], "\n".join(legacy_lines))
            )

        return self._emit_result(
            diagnostics,
            f"FAILED - Found {len(diagnostics)} notes slide reference validation errors:",
            "PASSED - All notes slide references are unique",
            extra_footer="Each slide may optionally have its own slide file.",
        )


if __name__ == "__main__":
    raise RuntimeError("This module should not be run directly.")
