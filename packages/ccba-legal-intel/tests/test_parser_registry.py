import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from ccba_legal.cleaners import Cleaners
from ccba_legal.parser import LegalAnalysisEngine
from ccba_legal.registry import LegalRegistryManager


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


def test_registry_manager_path_resolution(tmp_path: Path, monkeypatch) -> None:
    from ccba_legal.registry import discover_master_registry_path

    # Deterministic test with explicit custom path
    custom_reg = tmp_path / "custom_registry.yaml"
    custom_reg.write_text("metadata: {}", encoding="utf-8")
    custom_manager = LegalRegistryManager(registry_path=custom_reg)
    assert custom_manager.registry_path.resolve() == custom_reg.resolve()

    # Branch 1: When CWD contains .md/data/legal_registry.yaml
    cwd_dir = tmp_path / "workspace"
    local_reg = cwd_dir / ".md" / "data" / "legal_registry.yaml"
    local_reg.parent.mkdir(parents=True)
    local_reg.write_text("metadata: {}", encoding="utf-8")
    monkeypatch.chdir(cwd_dir)
    manager_local = LegalRegistryManager()
    assert manager_local.registry_path.resolve() == local_reg.resolve()

    # Branch 2: When CWD does not contain local registry, fallback to master registry
    empty_cwd = tmp_path / "empty_workspace"
    empty_cwd.mkdir()
    monkeypatch.chdir(empty_cwd)
    manager_master = LegalRegistryManager()
    assert manager_master.registry_path.resolve() == discover_master_registry_path().resolve()


def test_lifecycle_resolution_with_replacement(tmp_path: Path) -> None:
    """Verify get_lifecycle resolves obsolete statute replacement via KNOWN_STATUTORY_REPLACEMENTS."""
    reg_file = tmp_path / "legal_registry.yaml"
    reg_file.write_text(
        """decrees:
  - id: ND-217-2026
    document_number: 217/2026/NĐ-CP
    title: Nghị định về quản lý dự án đầu tư xây dựng
    short_name: Nghị định 217/2026/NĐ-CP
    status: active
""",
        encoding="utf-8",
    )

    mgr = LegalRegistryManager(registry_path=reg_file)
    life = mgr.get_lifecycle("15/2021/NĐ-CP")
    assert str(life["status"]).upper() == "SUPERSEDED"
    assert life["suggested_replacement"]["id"] == "ND-217-2026"
    assert life["suggested_replacement"]["document_number"] == "217/2026/NĐ-CP"
    assert "217/2026/NĐ-CP" in life["warning"]


def test_lifecycle_and_find_doc_nd_cp_equivalence(tmp_path: Path) -> None:
    """Verify ASCII ND-CP and diacritic NĐ-CP are treated as equivalent in find_doc and get_lifecycle."""
    reg_file = tmp_path / "legal_registry.yaml"
    reg_file.write_text(
        """decrees:
  - id: ND-217-2026
    document_number: 217/2026/NĐ-CP
    title: Nghị định về quản lý dự án đầu tư xây dựng
    short_name: Nghị định 217/2026/NĐ-CP
    status: active
""",
        encoding="utf-8",
    )

    mgr = LegalRegistryManager(registry_path=reg_file)

    # 1. find_doc with ASCII ND-CP should find diacritic NĐ-CP doc
    doc_ascii = mgr.find_doc("217/2026/ND-CP")
    assert doc_ascii is not None
    assert doc_ascii["id"] == "ND-217-2026"

    # 2. get_lifecycle with ASCII ND-CP should return ACTIVE (never downgraded to UNVERIFIED)
    life_ascii = mgr.get_lifecycle("217/2026/ND-CP")
    assert str(life_ascii["status"]).lower() == "active"
    assert life_ascii["warning"] is None

    # 3. Obsolete query with ASCII ND-CP should resolve to SUPERSEDED
    life_obs_ascii = mgr.get_lifecycle("15/2021/ND-CP")
    assert str(life_obs_ascii["status"]).upper() == "SUPERSEDED"
    assert life_obs_ascii["suggested_replacement"]["id"] == "ND-217-2026"
