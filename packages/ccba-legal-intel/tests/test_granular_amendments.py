import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import yaml
from ccba_legal.packager import inject_warning_block
from ccba_legal.parser import LegalAnalysisEngine
from ccba_legal.registry import LegalRegistryManager
from ccba_legal.coordinator import LegalProcessor


def test_extract_amendments():
    # 1. Test using direct JSON schema input (relation schema parsing)
    engine = LegalAnalysisEngine(ai_client=MagicMock())
    schema_text = """
    ```json
    [
      {
        "target_doc_id": "nd_06_2021",
        "target_anchor": "d15k2",
        "amendment_source": "Điều 1 Thông tư B",
        "source_doc_path": "../thong_tu_b/thong_tu_b.md"
      }
    ]
    ```
    """
    amendments = engine.extract_amendments(
        schema_text, source_doc_path="../thong_tu_b/thong_tu_b.md"
    )
    assert len(amendments) == 1
    assert amendments[0]["target_doc_id"] == "nd_06_2021"
    assert amendments[0]["target_anchor"] == "d15k2"
    assert amendments[0]["amendment_source"] == "Điều 1 Thông tư B"
    assert amendments[0]["source_doc_path"] == "../thong_tu_b/thong_tu_b.md"

    # 2. Test using LLM call (ai_client.chat)
    mock_ai = MagicMock()
    mock_ai.chat.return_value = """
    ```json
    [
      {
        "target_doc_id": "nd_06_2021",
        "target_anchor": "d15k2",
        "amendment_source": "Điều 1 Thông tư B",
        "source_doc_path": "../thong_tu_b/thong_tu_b.md"
      }
    ]
    ```
    """
    engine_llm = LegalAnalysisEngine(ai_client=mock_ai)
    amendments_llm = engine_llm.extract_amendments(
        "This is amending text that will trigger LLM.",
        source_doc_path="../thong_tu_b/thong_tu_b.md",
    )
    mock_ai.chat.assert_called_once()
    assert len(amendments_llm) == 1
    assert amendments_llm[0]["target_doc_id"] == "nd_06_2021"


def test_inject_warning_block():
    markdown_content = """# Test Document
<a id="d15k1"></a>1. Khoản 1 quy định...
<a id="d15k2"></a>2. Khoản 2 quy định...
3. Khoản 3 quy định...
"""
    updated = inject_warning_block(
        markdown_content=markdown_content,
        target_anchor="d15k2",
        amendment_source="Điều 1 Thông tư B",
        source_doc_path="../thong_tu_b/thong_tu_b.md",
    )

    # Verify warning block is injected right after the anchor line
    lines = updated.splitlines()
    assert lines[2] == '<a id="d15k2"></a>2. Khoản 2 quy định...'
    assert (
        lines[3]
        == "> [!WARNING] Khoản này đã bị sửa đổi/bổ sung bởi Điều 1 Thông tư B. Xem nội dung mới tại [Thông tư B](../thong_tu_b/thong_tu_b.md)."
    )
    assert lines[4] == "3. Khoản 3 quy định..."

    # Verify duplicate warning block is not injected
    re_updated = inject_warning_block(
        markdown_content=updated,
        target_anchor="d15k2",
        amendment_source="Điều 1 Thông tư B",
        source_doc_path="../thong_tu_b/thong_tu_b.md",
    )
    assert re_updated == updated


def test_update_clause_status_in_registry():
    with tempfile.TemporaryDirectory() as temp_dir:
        reg_file = Path(temp_dir) / "legal_registry.yaml"
        # Seed registry with a target document
        initial_data = {
            "decrees": [
                {"id": "ND-06-2021", "title": "Nghị định 06/2021/NĐ-CP", "status": "current"}
            ]
        }
        with open(reg_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(initial_data, f)

        manager = LegalRegistryManager(registry_path=reg_file)
        manager.update_clause_status(
            target_doc_id="ND-06-2021",
            clause_anchor="d15k2",
            status="amended",
            amended_by="Điều 1 Thông tư B",
            source_doc_path="../thong_tu_b/thong_tu_b.md",
        )

        # Reload and check
        data = manager.load()
        doc = data["decrees"][0]
        assert "clauses" in doc
        assert "d15k2" in doc["clauses"]
        clause = doc["clauses"]["d15k2"]
        assert clause["status"] == "amended"
        assert clause["amended_by"] == "Điều 1 Thông tư B"
        assert clause["source_doc_path"] == "../thong_tu_b/thong_tu_b.md"


def test_process_amendments_integration():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        reg_file = temp_path / "legal_registry.yaml"

        # Create folder structure mimicking the OKF bundles
        target_doc_dir = temp_path / ".md" / "legal_docs" / "nd_06_2021"
        target_doc_dir.mkdir(parents=True, exist_ok=True)
        target_markdown_file = target_doc_dir / "full_text.md"

        target_markdown_file.write_text(
            """# Nghị định 06/2021
<a id="d15k2"></a>Khoản 2 Điều 15...
""",
            encoding="utf-8",
        )

        # Seed registry
        initial_data = {
            "decrees": [
                {
                    "id": "ND-06-2021",
                    "title": "Nghị định 06/2021/NĐ-CP",
                    "file_path": ".md/legal_docs/nd_06_2021/full_text.md",
                }
            ]
        }
        with open(reg_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(initial_data, f)

        # Initialize coordinator
        processor = LegalProcessor(registry_path=reg_file)

        # Mock resolve_project_root to return our temp directory so it can find the target markdown file
        import ccba_legal.registry

        original_resolve = ccba_legal.registry.resolve_project_root
        ccba_legal.registry.resolve_project_root = lambda: temp_path

        try:
            # Source amending document schema
            source_content = """
            ```json
            [
              {
                "target_doc_id": "ND-06-2021",
                "target_anchor": "d15k2",
                "amendment_source": "Điều 1 Thông tư B",
                "source_doc_path": "../thong_tu_b/thong_tu_b.md"
              }
            ]
            ```
            """

            # Process amendments
            mods = processor.process_amendments_from_document(
                source_doc_id="thong_tu_b",
                source_doc_content=source_content,
                source_doc_path="../thong_tu_b/thong_tu_b.md",
            )

            assert len(mods) == 1

            # Verify warning was injected in the file
            updated_text = target_markdown_file.read_text(encoding="utf-8")
            assert (
                "> [!WARNING] Khoản này đã bị sửa đổi/bổ sung bởi Điều 1 Thông tư B. Xem nội dung mới tại [Thông tư B](../thong_tu_b/thong_tu_b.md)."
                in updated_text
            )

            # Verify registry was updated
            registry_data = processor.registry_mgr.load()
            assert registry_data["decrees"][0]["clauses"]["d15k2"]["status"] == "amended"

        finally:
            ccba_legal.registry.resolve_project_root = original_resolve
