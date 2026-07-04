---
name: long-form-writer
description: Generates long-form documentation (2000+ words) by actively managing LLM context to bypass output limits. Ideal for regulations, whitepapers, or manuals.
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_core"
---

# Long-Form Writer Skill

This skill allows Antigravity to generate "super-long" content that exceeds standard output token limits. It uses a Python script (`scripts/generate.py`) that implements a "Chain of Continuation" loop, forcing the model to write deeply about specific sections without summarizing.

## When to Use

- You need to draft a **comprehensive regulation**, **legal document**, or **detailed manual** (e.g., > 10 pages).
- The user requests "detailed," "deep analysis," or "no summarization."
- Standard generation cuts off or becomes too brief.

## How to Use

1. **Prepare the Prompt**:
    Create a highly detailed prompt that outlines exactly what the document should cover. Structure it clearly (e.g., "Part 1...", "Part 2...").

2. **Run the Script**:
    Use `run_command` to execute the generation script.

    ```powershell
    python [hub_path]/.agents/skills/long-form-writer/scripts/generate.py --prompt "YOUR_DETAILED_PROMPT" --output "absolute/path/to/output.docx" --cycles 3
    ```

    - `--prompt`: The detailed instructions for the content.
    - `--output`: The absolute path where the .docx file should be saved.
    - `--cycles`: Number of times to force "continue writing" (Default: 3). Increase to 5-10 for extremely long documents.
    - `--model`: (Optional) `gemini-1.5-pro` (default) or others.

3. **Verify Output**:
    Check that the file was created and notify the user.

## Dependencies

- `google-generativeai`
- `python-docx`
