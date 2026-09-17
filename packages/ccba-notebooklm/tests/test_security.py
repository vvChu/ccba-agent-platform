"""Test cases for security and Maskara sanitization in ccba-notebooklm."""

import sys
from pathlib import Path

# Ensure src is in python path
src_dir = Path(__file__).parents[1] / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import pytest

from ccba_notebooklm._artifacts import query_rag
from ccba_notebooklm._security import sanitize_prompt_for_query

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_sanitize_prompt_clean():
    """Prompt thông thường không bị thay đổi."""
    prompt = "Quy định về chiều cao công trình theo QCVN 06:2022 là gì?"
    assert sanitize_prompt_for_query(prompt) == prompt


def test_sanitize_prompt_blocks_critical_keys():
    """Prompt chứa OpenAI / Google / GitHub key bị chặn với ValueError."""
    fake_openai = "sk-" + "a" * 30
    with pytest.raises(ValueError, match="CHẶN"):
        sanitize_prompt_for_query(f"Hãy dùng key {fake_openai} để tra cứu.")

    fake_google = "AIza" + "a" * 35
    with pytest.raises(ValueError, match="CHẶN"):
        sanitize_prompt_for_query(f"Key của tôi là {fake_google}")


def test_sanitize_prompt_redacts_other_secrets():
    """Prompt chứa token khác (ví dụ AWS key) được redact an toàn."""
    fake_aws = "AKIA" + "B" * 16
    prompt = f"Server dùng key {fake_aws} để truy xuất dữ liệu."
    redacted = sanitize_prompt_for_query(prompt)
    assert fake_aws not in redacted
    assert "[MASKARA_REDACTED:aws-access-key]" in redacted


@pytest.mark.asyncio
async def test_query_rag_blocks_critical_secrets(capsys):
    """query_rag chặn ngay từ đầu và trả về exit code 3 khi prompt chứa API key."""
    fake_openai = "sk-" + "c" * 30
    code = await query_rag("dummy_path.txt", f"Tra cứu với key {fake_openai}")
    assert code == 3
    captured = capsys.readouterr()
    assert "CHẶN" in captured.err
