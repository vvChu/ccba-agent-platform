import json
import re
from typing import Any

from ccba_ai import ai


class Cleaners:
    """Helper utilities to clean up text and extract JSON from LLM responses."""

    _THINK_PATTERN = re.compile(r"<think>.*?</think>\n*", re.DOTALL | re.IGNORECASE)
    _THINK_UNCLOSED = re.compile(r"<think>.*", re.DOTALL | re.IGNORECASE)
    _ORPHAN_END = re.compile(r"^.*?</think>\n*", re.DOTALL | re.IGNORECASE)

    @classmethod
    def strip_think_tags(cls, text: str) -> str:
        """Strip <think>...</think> tags and their contents from reasoning models."""
        text = cls._THINK_PATTERN.sub("", text)
        text = cls._THINK_UNCLOSED.sub("", text)
        text = cls._ORPHAN_END.sub("", text)
        return text.strip()

    @classmethod
    def extract_json(cls, raw: str) -> Any:
        """Extract JSON dictionary or list from raw text containing Markdown fences."""
        clean = cls.strip_think_tags(raw)
        match = re.search(r"```(?:json)?\s*([\{\[].*?[\}\]])\s*```", clean, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        match = re.search(r"([\{\[].*[\}\]])", clean, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        return None

    @classmethod
    def remove_ocr_artifacts(cls, text: str) -> str:
        """Remove long uppercase lines commonly created by page headers/footers in OCR."""
        return re.sub(r"^[A-ZÀ-Ỹ][A-ZÀ-Ỹ\s_]{14,}\.?\s*$", "", text, flags=re.MULTILINE).strip()


class LegalAnalysisEngine:
    """Module responsible for calling Spark LiteLLM to analyze law texts."""

    def __init__(self, model: str = "gemini-3.1-pro-high") -> None:
        self.model = model

    def analyze_document(self, text: str) -> dict[str, Any]:
        """Extract metadata and summarize key properties of the document."""
        clean_text = Cleaners.remove_ocr_artifacts(text)[:80000]
        prompt = f"""
Analyze the following Vietnamese legal text. Extract metadata and summarize key properties.
Return ONLY a JSON object (inside a markdown json code block) with the following keys:
- title: string (Human-readable official name, e.g. "Luật Xây dựng 2025")
- doc_number: string (Official document number, e.g. "135/2025/QH15")
- issuing_body: string (e.g. "Quốc hội", "Chính phủ")
- signing_date: string (ISO 8601 date YYYY-MM-DD or empty)
- effective_date: string (ISO 8601 date YYYY-MM-DD or empty)
- summary: string (Brief 3-4 sentence summary of scope and main changes)

Law text:
{clean_text}
"""
        reply = ai.chat(prompt, model=self.model, temperature=0.1, max_tokens=8192)
        res = Cleaners.extract_json(reply)
        if not res:
            res = {
                "title": "Unknown Legal Document",
                "doc_number": "Unknown",
                "issuing_body": "Unknown",
                "signing_date": "",
                "effective_date": "",
                "summary": "Could not parse summary from LLM.",
            }
        return res

    def generate_checklist(self, text: str) -> list[dict[str, Any]]:
        """Identify key compliance requirements and build a RACI checklist."""
        clean_text = Cleaners.remove_ocr_artifacts(text)[:60000]
        prompt = f"""
Parse the following construction law/regulation text and extract key compliance requirements.
For each requirement, provide:
- reference: string (e.g., "Điều 45 Khoản 1")
- requirement: string (Vietnamese text of the rule/requirement)
- evidence: string (Evidence needed to verify compliance)
- raci: dict (Role assignments for: Owner, Contractor, Supervisor. Use values: R (Responsible), A (Accountable), C (Consulted), I (Informed), or None)

Return ONLY a JSON list of objects (inside a markdown json code block). Max 10 most critical requirements.

Text:
{clean_text}
"""
        reply = ai.chat(prompt, model=self.model, temperature=0.1, max_tokens=8192)
        res = Cleaners.extract_json(reply)
        if isinstance(res, list):
            return res
        if isinstance(res, dict) and "requirements" in res:
            return res["requirements"]
        return []

    def perform_diff(self, old_text: str, new_text: str) -> dict[str, Any]:
        """Perform semantic diff between old and new law versions."""
        clean_old = Cleaners.remove_ocr_artifacts(old_text)[:40000]
        clean_new = Cleaners.remove_ocr_artifacts(new_text)[:40000]
        prompt = f"""
Compare the older construction law text with the newer version.
Extract the key updates, deleted rules, and added provisions.
Return ONLY a JSON object (inside a markdown json code block) with:
- changes_summary: string (Overview of differences)
- comparison_table: list of dicts (with keys: item, old_provision, new_provision, effect)

Old law sample:
{clean_old}

New law sample:
{clean_new}
"""
        reply = ai.chat(prompt, model=self.model, temperature=0.1, max_tokens=8192)
        res = Cleaners.extract_json(reply)
        if not res:
            res = {"changes_summary": "Failed to extract diff summary.", "comparison_table": []}
        return res
