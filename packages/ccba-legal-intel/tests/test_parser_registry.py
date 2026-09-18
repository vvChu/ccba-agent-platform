import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from ccba_legal.cleaners import Cleaners
from ccba_legal.parser import LegalAnalysisEngine
from ccba_legal.registry import LegalRegistryManager, resolve_project_root


def test_cleaners_strip_think_tags():
    raw_text = "<think>Here is some deep thought\nwhich is internal</think>\nActual content here."
    cleaned = Cleaners.strip_think_tags(raw_text)
    assert cleaned == "Actual content here."

    unclosed = "<think>thinking without closing tag... Actual content."
    cleaned_unclosed = Cleaners.strip_think_tags(unclosed)
    assert cleaned_unclosed == ""


def test_cleaners_extract_json():
    raw = 'Some text before.\n```json\n{\n  "key": "value"\n}\n```\nSome text after.'
    data = Cleaners.extract_json(raw)
    assert data == {"key": "value"}

    raw_no_md = '{\n  "numbers": [1, 2, 3]\n}'
    data_no_md = Cleaners.extract_json(raw_no_md)
    assert data_no_md == {"numbers": [1, 2, 3]}


def test_cleaners_remove_ocr_artifacts():
    raw = "BỘ XÂY DỰNG TRƯỜNG ĐẠI HỌC KIẾN TRÚC\nCỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n\nĐiều 1: Quy định chung."
    cleaned = Cleaners.remove_ocr_artifacts(raw)
    # The header line is long and capitalized, so it should be stripped
    assert "Điều 1: Quy định chung." in cleaned
    assert "BỘ XÂY DỰNG" not in cleaned


def test_legal_analysis_engine_seam():
    # Setup mock LLM client
    mock_ai = MagicMock()
    mock_ai.chat.return_value = """
```json
{
  "title": "Luật Xây dựng 2025",
  "doc_number": "135/2025/QH15",
  "issuing_body": "Quốc hội",
  "signing_date": "2025-06-15",
  "effective_date": "2026-01-01",
  "summary": "Tóm tắt thay đổi chính về PCCC và quản lý chất lượng."
}
```
"""
    engine = LegalAnalysisEngine(ai_client=mock_ai)

    text = "Nội dung văn bản luật xây dựng mới..."
    result = engine.analyze_document(text)

    # Assert chat call
    mock_ai.chat.assert_called_once()
    assert result["title"] == "Luật Xây dựng 2025"
    assert result["doc_number"] == "135/2025/QH15"


def test_legal_registry_manager_temp():
    with tempfile.TemporaryDirectory() as temp_dir:
        reg_file = Path(temp_dir) / "registry.yaml"
        manager = LegalRegistryManager(registry_path=reg_file)

        # Test loading empty registry
        data = manager.load()
        assert "laws" in data
        assert len(data["laws"]) == 0

        # Test adding document
        doc_data = {"title": "Nghị định 06/2021/NĐ-CP", "effective_date": "2021-01-26"}
        manager.add_or_update_doc("decrees", "ND_06_2021", doc_data)

        # Reload and verify
        new_data = manager.load()
        assert len(new_data["decrees"]) == 1
        assert new_data["decrees"][0]["id"] == "ND_06_2021"
        assert new_data["decrees"][0]["title"] == "Nghị định 06/2021/NĐ-CP"


def test_registry_manager_path_resolution():
    from ccba_legal.registry import discover_master_registry_path
    manager = LegalRegistryManager()
    cwd_cand = Path.cwd() / ".md" / "data" / "legal_registry.yaml"
    expected_path = cwd_cand.resolve() if cwd_cand.is_file() else discover_master_registry_path()
    assert manager.registry_path.resolve() == expected_path.resolve()
