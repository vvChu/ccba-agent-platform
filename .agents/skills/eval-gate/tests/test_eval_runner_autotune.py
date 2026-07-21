"""test_eval_runner_autotune.py - Unit tests cho CCBA Skill Auto-Tuner (SkillOpt integration)."""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Thêm đường dẫn module eval_runner vào sys.path
eval_runner_dir = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(eval_runner_dir))

from eval_runner import (
    preserve_yaml_frontmatter,
    optimizer_edit_prompt,
    auto_tune_skill,
)


def test_preserve_yaml_frontmatter_keeps_original_header():
    """Đảm bảo giữ nguyên YAML Frontmatter gốc khi thay đổi phần nội dung prompt."""
    original_prompt = (
        "---\n"
        "name: copywriting\n"
        "description: Standard Copywriting Skill\n"
        "bundle: _core\n"
        "---\n\n"
        "# Old Body\nOriginal instructions here."
    )
    
    edited_body_only = "# New Body\nOptimized instructions with stronger constraints."
    
    result = preserve_yaml_frontmatter(original_prompt, edited_body_only)
    
    assert result.startswith("---\nname: copywriting\n")
    assert "bundle: _core" in result
    assert "# New Body" in result
    assert "Optimized instructions with stronger constraints." in result
    assert "Original instructions here." not in result


def test_preserve_yaml_frontmatter_handles_edited_with_frontmatter():
    """Đảm bảo xử lý đúng khi LLM Optimizer tự ý bọc lại frontmatter trong câu trả lời."""
    original_prompt = (
        "---\n"
        "name: test_skill\n"
        "bundle: _software\n"
        "---\n\n"
        "# Original Content"
    )
    
    edited_with_frontmatter = (
        "---\n"
        "name: test_skill_modified\n"
        "bundle: hacked\n"
        "---\n\n"
        "# Modified Content"
    )
    
    result = preserve_yaml_frontmatter(original_prompt, edited_with_frontmatter)
    
    # Bắt buộc bảo vệ frontmatter GỐC (name: test_skill, bundle: _software)
    assert "name: test_skill\n" in result
    assert "bundle: _software" in result
    assert "# Modified Content" in result
    assert "name: test_skill_modified" not in result


@patch("ccba_ai.ai.chat")
def test_optimizer_edit_prompt_calls_llm(mock_ai_chat):
    """Kiểm tra optimizer_edit_prompt gọi AI Gateway đúng tham số."""
    mock_ai_chat.return_value = "# Refined Prompt Content"
    
    original_prompt = "---\nname: demo\n---\n\n# Original Prompt"
    failure_details = [{"case_id": "c1", "failure_reason": "Missing section heading"}]
    
    result = optimizer_edit_prompt(original_prompt, failure_details, model_id="gemini-3.1-pro-high")
    
    assert mock_ai_chat.called
    assert "Missing section heading" in mock_ai_chat.call_args[0][0]
    assert "name: demo" in result
    assert "# Refined Prompt Content" in result
