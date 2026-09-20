"""Unit tests for Sharded Legal Registry Compiler and CI synchronization checks."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from ccba_legal.cli import build_parser, handle_compile_registry
from ccba_legal.compiler import (
    compile_sharded_registry,
    infer_category,
    normalize_metadata_to_doc_entry,
)
from ccba_legal.validator import validate_registry_sync


class TestShardedRegistryCompiler(unittest.TestCase):
    """Test suite for sharded legal registry compiler."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.docs_dir = self.root / "legal_docs"
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.root / ".md" / "data" / "legal_registry.yaml"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_infer_category_various_types(self) -> None:
        """Verify inference of category across Vietnamese and English legal types."""
        self.assertEqual(infer_category("Luật"), "laws")
        self.assertEqual(infer_category("Bộ luật hình sự"), "laws")
        self.assertEqual(infer_category("Nghị định"), "decrees")
        self.assertEqual(infer_category("Decree of Government"), "decrees")
        self.assertEqual(infer_category("Thông tư"), "circulars")
        self.assertEqual(infer_category("Quyết định"), "decisions")
        self.assertEqual(infer_category("Nghị quyết"), "resolutions")
        self.assertEqual(infer_category("Quy chuẩn kỹ thuật quốc gia"), "standards")
        self.assertEqual(infer_category("Tiêu chuẩn TCVN"), "standards")
        # Explicit category takes precedence
        self.assertEqual(infer_category("Văn bản khác", raw_category="circulars"), "circulars")
        self.assertEqual(infer_category("Văn bản khác", raw_category="decision"), "decisions")

    def test_normalize_metadata_to_doc_entry(self) -> None:
        """Verify metadata normalization including field aliases and relative paths."""
        bundle = self.docs_dir / "01_vbpl" / "nghi_dinh_207_2026_nd_cp"
        bundle.mkdir(parents=True, exist_ok=True)
        (bundle / "nghi_dinh_207_2026_nd_cp.md").write_text("# Content", encoding="utf-8")
        (bundle / "sample.docx").write_text("dummy", encoding="utf-8")

        raw_meta = {
            "doc_id": "ND-207-2026",
            "doc_number": "207/2026/NĐ-CP",
            "title": "Nghị định 207/2026/NĐ-CP",
            "type": "Nghị định",
            "issuer": "Chính phủ",
            "signer": "Phạm Minh Chính",
            "issued_date": "2026-06-15",
            "effective_date": "2026-07-01",
            "replaces": ["06/2021/NĐ-CP"],
            "topics": ["quality_management"],
            "source_assets": {
                "pdf_sha256": "abcdef1234567890",
            },
        }

        cat, entry = normalize_metadata_to_doc_entry(
            metadata=raw_meta,
            bundle_dir=bundle,
            project_root=self.root,
        )

        self.assertEqual(cat, "decrees")
        self.assertEqual(entry["id"], "ND-207-2026")
        self.assertEqual(entry["document_number"], "207/2026/NĐ-CP")
        self.assertEqual(entry["issued_by"], "Chính phủ")
        self.assertEqual(entry["relations"]["replaces"], ["06/2021/NĐ-CP"])
        self.assertEqual(entry["sha256"], "abcdef1234567890")
        self.assertIn("nghi_dinh_207_2026_nd_cp.md", entry["markdown_path"])
        self.assertIn("sample.docx", entry["file_path"])

    def test_compile_sharded_registry_lifecycle_and_sorting(self) -> None:
        """Verify multi-document discovery, categorisation, and deterministic sorting."""
        # 1. Create multiple sharded bundles out-of-order
        # Doc B: Decree
        b_dir = self.docs_dir / "decrees" / "doc_b"
        b_dir.mkdir(parents=True)
        (b_dir / "metadata.yaml").write_text(
            yaml.safe_dump(
                {
                    "id": "ND-02-2026",
                    "type": "Nghị định",
                    "title": "Nghị định số 02",
                    "issued_date": "2026-02-01",
                }
            ),
            encoding="utf-8",
        )

        # Doc A: Decree (should be sorted before Doc B)
        a_dir = self.docs_dir / "decrees" / "doc_a"
        a_dir.mkdir(parents=True)
        (a_dir / "metadata.yaml").write_text(
            yaml.safe_dump(
                {
                    "id": "ND-01-2026",
                    "type": "Nghị định",
                    "title": "Nghị định số 01",
                    "issued_date": "2026-01-01",
                }
            ),
            encoding="utf-8",
        )

        # Doc C: Law
        c_dir = self.docs_dir / "laws" / "doc_c"
        c_dir.mkdir(parents=True)
        (c_dir / "metadata.yaml").write_text(
            yaml.safe_dump(
                {
                    "id": "L-135-2025",
                    "type": "Luật",
                    "title": "Luật Xây dựng 2025",
                    "issued_date": "2025-11-20",
                }
            ),
            encoding="utf-8",
        )

        # 2. Compile
        compiled, is_in_sync, issues = compile_sharded_registry(
            docs_dir=self.docs_dir,
            output_file=self.registry_file,
            project_root=self.root,
        )

        self.assertTrue(self.registry_file.exists())
        self.assertEqual(len(compiled["laws"]), 1)
        self.assertEqual(len(compiled["decrees"]), 2)

        # Deterministic sort check: ND-01-2026 before ND-02-2026
        self.assertEqual(compiled["decrees"][0]["id"], "ND-01-2026")
        self.assertEqual(compiled["decrees"][1]["id"], "ND-02-2026")

        # Check that file matches compiled dict
        loaded = yaml.safe_load(self.registry_file.read_text(encoding="utf-8"))
        self.assertEqual(loaded["decrees"][0]["id"], "ND-01-2026")

    def test_preserves_non_document_sections(self) -> None:
        """Verify that existing non-category sections (metadata, monitoring, seminars) are preserved."""
        # Create an existing base registry with custom metadata and monitoring
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        existing_data = {
            "metadata": {"maintained_by": "Custom Team", "version": "1.0"},
            "monitoring": [{"expected": "2026-12", "source": "moc.gov.vn"}],
            "seminars": [{"id": "SEM-001", "title": "BIM Seminar"}],
            "laws": [],
            "decrees": [],
        }
        self.registry_file.write_text(yaml.safe_dump(existing_data), encoding="utf-8")

        # Create one sharded doc
        doc_dir = self.docs_dir / "01_laws" / "law_1"
        doc_dir.mkdir(parents=True)
        (doc_dir / "metadata.yaml").write_text(
            yaml.safe_dump({"id": "L-01", "type": "Luật", "title": "Luật Mẫu"}),
            encoding="utf-8",
        )

        # Compile
        compiled, _, _ = compile_sharded_registry(
            docs_dir=self.docs_dir,
            output_file=self.registry_file,
            base_registry_path=self.registry_file,
            project_root=self.root,
        )

        self.assertEqual(compiled["metadata"]["maintained_by"], "Custom Team")
        self.assertEqual(len(compiled["monitoring"]), 1)
        self.assertEqual(len(compiled["seminars"]), 1)
        self.assertEqual(len(compiled["laws"]), 1)

    def test_check_mode_sync_and_drift_detection(self) -> None:
        """Verify check_only mode detects parity and drift accurately."""
        # Bundle 1
        d1 = self.docs_dir / "decrees" / "d1"
        d1.mkdir(parents=True)
        (d1 / "metadata.yaml").write_text(
            yaml.safe_dump({"id": "ND-01", "type": "Nghị định"}),
            encoding="utf-8",
        )

        # 1. Compile initially to sync file
        compile_sharded_registry(
            docs_dir=self.docs_dir,
            output_file=self.registry_file,
            check_only=False,
            project_root=self.root,
        )

        # 2. Check parity -> should be in sync
        _, in_sync, issues = compile_sharded_registry(
            docs_dir=self.docs_dir,
            output_file=self.registry_file,
            check_only=True,
            project_root=self.root,
        )
        self.assertTrue(in_sync)
        self.assertEqual(len(issues), 0)

        # 3. Introduce drift by adding a new sharded bundle without re-compiling
        d2 = self.docs_dir / "decrees" / "d2"
        d2.mkdir(parents=True)
        (d2 / "metadata.yaml").write_text(
            yaml.safe_dump({"id": "ND-02", "type": "Nghị định"}),
            encoding="utf-8",
        )

        # Check parity -> should detect drift
        _, in_sync, issues = compile_sharded_registry(
            docs_dir=self.docs_dir,
            output_file=self.registry_file,
            check_only=True,
            project_root=self.root,
        )
        self.assertFalse(in_sync)
        self.assertGreater(len(issues), 0)
        self.assertTrue(any("ND-02" in iss for iss in issues))

    def test_validate_registry_sync_integration(self) -> None:
        """Verify validate_registry_sync function exported from validator module."""
        # When docs exist and registry matches
        d1 = self.docs_dir / "laws" / "l1"
        d1.mkdir(parents=True)
        (d1 / "metadata.yaml").write_text(
            yaml.safe_dump({"id": "L-01", "type": "Luật"}),
            encoding="utf-8",
        )
        compile_sharded_registry(
            docs_dir=self.docs_dir,
            output_file=self.registry_file,
            check_only=False,
            project_root=self.root,
        )

        errors, warnings = validate_registry_sync(
            spoke_root=self.root,
            registry_path=self.registry_file,
            docs_dir=self.docs_dir,
        )
        self.assertEqual(len(errors), 0)

        # Break synchronization
        self.registry_file.unlink()
        errors, warnings = validate_registry_sync(
            spoke_root=self.root,
            registry_path=self.registry_file,
            docs_dir=self.docs_dir,
        )
        self.assertGreater(len(errors), 0)

    def test_cli_compile_registry_execution(self) -> None:
        """Verify execution via CLI argument parser and handle_compile_registry."""
        d1 = self.docs_dir / "decrees" / "d1"
        d1.mkdir(parents=True)
        (d1 / "metadata.yaml").write_text(
            yaml.safe_dump({"id": "ND-01", "type": "Nghị định", "title": "Decree 1"}),
            encoding="utf-8",
        )

        parser = build_parser()

        # Execute compilation
        args_compile = parser.parse_args(
            [
                "compile-registry",
                "--docs-dir",
                str(self.docs_dir),
                "--output",
                str(self.registry_file),
            ]
        )
        exit_code = handle_compile_registry(args_compile)
        self.assertEqual(exit_code, 0)
        self.assertTrue(self.registry_file.exists())

        # Execute check mode
        args_check = parser.parse_args(
            [
                "compile-registry",
                "--docs-dir",
                str(self.docs_dir),
                "--output",
                str(self.registry_file),
                "--check",
            ]
        )
        exit_code_check = handle_compile_registry(args_check)
        self.assertEqual(exit_code_check, 0)
