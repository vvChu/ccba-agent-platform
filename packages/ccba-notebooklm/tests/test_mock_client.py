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
            generate_fn=lambda c, nb, src: c.artifacts.generate_quiz(
                nb, source_ids=[src], quantity="standard", difficulty="medium"
            ),
            download_fn=lambda c, nb, out, tid, fmt: c.artifacts.download_quiz(
                nb, out, output_format=fmt
            ),
            output_format="json",
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
