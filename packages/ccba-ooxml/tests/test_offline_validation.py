"""Unit tests for offline XML schema validation in ccba-ooxml (Issue #260)."""

from __future__ import annotations

from pathlib import Path

import lxml.etree
import pytest

from ccba_ooxml.validation.base import BaseSchemaValidator, OfflineSchemaResolver


@pytest.mark.fast
def test_offline_schema_resolver_resolves_dublincore() -> None:
    """Verify OfflineSchemaResolver intercepts Dublin Core and xml.xsd URLs."""
    schemas_dir = Path(__file__).parent.parent / "src" / "ccba_ooxml" / "schemas"
    resolver = OfflineSchemaResolver(schemas_dir)

    urls = [
        "http://dublincore.org/schemas/xmls/qdc/2003/04/02/dc.xsd",
        "http://dublincore.org/schemas/xmls/qdc/2003/04/02/dcterms.xsd",
        "http://dublincore.org/schemas/xmls/qdc/2003/04/02/dcmitype.xsd",
        "dc.xsd",
        "dcterms.xsd",
        "dcmitype.xsd",
        "http://www.w3.org/2001/03/xml.xsd",
    ]

    for url in urls:
        resolved = resolver.resolve(url, None, None)
        assert resolved is not None, f"Failed to resolve URL offline: {url}"


@pytest.mark.fast
def test_compiled_schema_cache() -> None:
    """Verify BaseSchemaValidator caches compiled schemas."""
    schemas_dir = Path(__file__).parent.parent / "src" / "ccba_ooxml" / "schemas"
    schema_path = schemas_dir / "ecma" / "fouth-edition" / "opc-coreProperties.xsd"

    schema1 = BaseSchemaValidator.get_compiled_schema(schema_path, schemas_dir)
    schema2 = BaseSchemaValidator.get_compiled_schema(schema_path, schemas_dir)

    assert schema1 is schema2


@pytest.mark.fast
def test_core_properties_validation_offline() -> None:
    """Verify that core.xml validates successfully 100% offline without network calls."""
    schemas_dir = Path(__file__).parent.parent / "src" / "ccba_ooxml" / "schemas"
    schema_path = schemas_dir / "ecma" / "fouth-edition" / "opc-coreProperties.xsd"
    schema = BaseSchemaValidator.get_compiled_schema(schema_path, schemas_dir)

    valid_core_xml = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        b'<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        b'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
        b'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
        b"  <dc:title>Test Document</dc:title>\n"
        b"  <dc:creator>Test Author</dc:creator>\n"
        b'  <dcterms:created xsi:type="dcterms:W3CDTF">2026-09-11T12:00:00Z</dcterms:created>\n'
        b'  <dcterms:modified xsi:type="dcterms:W3CDTF">2026-09-11T12:00:00Z</dcterms:modified>\n'
        b"</cp:coreProperties>"
    )

    doc = lxml.etree.fromstring(valid_core_xml)
    assert schema.validate(doc) is True


@pytest.mark.fast
def test_invalid_core_properties_detected_offline() -> None:
    """Verify that invalid core.xml elements are correctly flagged without network errors."""
    schemas_dir = Path(__file__).parent.parent / "src" / "ccba_ooxml" / "schemas"
    schema_path = schemas_dir / "ecma" / "fouth-edition" / "opc-coreProperties.xsd"
    schema = BaseSchemaValidator.get_compiled_schema(schema_path, schemas_dir)

    invalid_core_xml = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        b'<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties">\n'
        b"  <cp:nonExistentElement>Invalid</cp:nonExistentElement>\n"
        b"</cp:coreProperties>"
    )

    doc = lxml.etree.fromstring(invalid_core_xml)
    assert schema.validate(doc) is False
    assert len(schema.error_log) > 0
