import shutil
from pathlib import Path

import pytest

from ccba_notebooklm import (
    check_auth,
    get_client,
    handle_artifact_flow,
)


# Đảm bảo tắt môi trường auth thực tế trong test cases này
@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("NOTEBOOKLM_SESSION_COOKIE", raising=False)
    monkeypatch.delenv("NOTEBOOKLM_COOKIES_JSON", raising=False)


@pytest.mark.asyncio
async def test_mock_auth():
    """Xác minh mock client auth luôn trả về 0 (thành công)."""
    code = await check_auth()
    assert code == 0


@pytest.mark.asyncio
async def test_mock_client_creation():
    """Xác minh client được tạo ra là mock client."""
    client = get_client()
    assert client.use_mock is True


@pytest.mark.asyncio
async def test_mock_artifact_flow():
    """Xác minh handle_artifact_flow chạy thành công với Mock client."""
    test_src = "packages/ccba-notebooklm/tests/test_notebooklm_basic.py"
    out_dir = "packages/ccba-notebooklm/tests/test_out"

    # Tạo fake source file để test
    src_path = Path(test_src)
    assert src_path.exists()

    try:
        # Test quiz generation
        code = await handle_artifact_flow(
            task_type="quiz",
            source_path=test_src,
            output_dir=out_dir,
            output_filename_pattern="quiz_{source_id}.json",
            output_format="json",
            quantity="standard",
            difficulty="medium",
        )
        assert code == 0

        # Kiểm tra file sinh ra
        out_file = Path(out_dir) / "quiz_src-mock-file.json"
        assert out_file.exists()
        assert b"Mock Question" in out_file.read_bytes()

    finally:
        # Cleanup
        if Path(out_dir).exists():
            shutil.rmtree(out_dir)


@pytest.mark.asyncio
async def test_flat_client_methods():
    """Xác minh các phương thức phẳng mới của CCBANotebookLMClient."""
    client = get_client()
    async with client as client_ctx:
        # Kiểm tra context manager trả về chính client
        assert client_ctx is client

        # Liệt kê notebook
        notebooks = await client.list_notebooks()
        assert len(notebooks) >= 2
        nb_id = notebooks[0].id
        assert nb_id == "nb-mock-1"

        # Liệt kê source
        sources = await client.list_sources(nb_id)
        assert len(sources) >= 2
        src_id = sources[0].id

        # Tạo và xóa notebook
        new_nb = await client.create_notebook("New Temp Notebook")
        assert new_nb.id.startswith("nb-mock-")
        await client.delete_notebook(new_nb.id)

        # Đăng ký và xóa source
        new_src = await client.add_file_source(
            nb_id, "packages/ccba-notebooklm/tests/test_mock_client.py"
        )
        assert new_src.id == "src-mock-file"
        await client.delete_source(nb_id, new_src.id)

        # Hỏi chat
        chat_res = await client.ask_chat(nb_id, "Hello Test", [src_id])
        assert chat_res.answer is not None

        # Sinh và tải artifact
        artifact = await client.generate_artifact(
            "quiz", nb_id, [src_id], quantity="standard", difficulty="medium"
        )
        assert artifact.task_id == "task-quiz-1"
