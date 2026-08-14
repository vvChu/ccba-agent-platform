"""Parser module for analyzing Vietnamese legal texts.

Uses LLM capabilities from ccba_ai and cleaner utility to extract key
information, RACI checklists, and perform semantic differences between texts.
"""

from typing import Any

from ccba_ai import ai

from .cleaners import Cleaners


class LegalAnalysisEngine:
    """Module responsible for calling Spark LiteLLM to analyze law texts."""

    def __init__(self, model: str = "gemini-3.7-flash-high", ai_client: Any = None) -> None:
        """Initialize the engine with an LLM model and optional adapter client (seam)."""
        self.model = model
        self.ai_client = ai_client or ai

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
        reply = self.ai_client.chat(prompt, model=self.model, temperature=0.1, max_tokens=8192)
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
        reply = self.ai_client.chat(prompt, model=self.model, temperature=0.1, max_tokens=8192)
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
        reply = self.ai_client.chat(prompt, model=self.model, temperature=0.1, max_tokens=8192)
        res = Cleaners.extract_json(reply)
        if not res:
            res = {"changes_summary": "Failed to extract diff summary.", "comparison_table": []}
        return res

    def standardize_formulas(self, text: str) -> str:
        """Detect construction cost formulas in the text and standardize them using the LLM.

        Args:
            text: The legal text containing possible formulas.

        Returns:
            The text with standardized LaTeX equations, explanation tables, and Python executable blocks.
        """
        keywords = ["công thức", "tính toán", "chi phí", "phương pháp tính"]
        if not any(k in text.lower() for k in keywords):
            return text

        paragraphs = text.split("\n\n")
        updated_paras = []
        for para in paragraphs:
            has_formula = False
            lower_para = para.lower()
            if "công thức" in lower_para or "tính theo" in lower_para or "tính bằng" in lower_para:
                has_formula = True
            elif "=" in lower_para and any(op in lower_para for op in ["+", "-", "*", "/", " x "]):
                has_formula = True

            if has_formula:
                prompt = f"""
Analyze this text paragraph. If it contains a formula for calculating construction costs, values or quantities:
1. Convert the formula into a LaTeX equation block wrapped in double dollar signs ($$...$$).
2. Generate a parameter explanation table (Markdown table with columns: Ký hiệu, Ý nghĩa).
3. Append an executable Python code block (```python ... ```) with a function that calculates it.
4. Keep the surrounding text in the paragraph unchanged.

If there is no formula, return the paragraph exactly as is.

Paragraph:
{para}
"""
                reply = self.ai_client.chat(prompt, model=self.model, temperature=0.1)
                reply = Cleaners.strip_think_tags(reply)
                updated_paras.append(reply)
            else:
                updated_paras.append(para)

        return "\n\n".join(updated_paras)

    def extract_amendments(self, text: str, source_doc_path: str = "") -> list[dict[str, Any]]:
        """Extract clause-level changes/amendments from the document text.

        Args:
            text: The text content of the amending document.
            source_doc_path: Path of the source document making the amendment.

        Returns:
            A list of dicts with target_doc_id, target_anchor, amendment_source, source_doc_path.
        """
        # Try parsing as JSON first (useful for testing or relation schema)
        try:
            parsed = Cleaners.extract_json(text)
            if isinstance(parsed, list):
                for item in parsed:
                    if "source_doc_path" not in item or not item["source_doc_path"]:
                        item["source_doc_path"] = source_doc_path
                return parsed
        except Exception:
            pass

        # Call LLM to extract clause-level changes
        clean_text = Cleaners.remove_ocr_artifacts(text)[:40000]
        prompt = f"""
Analyze the following Vietnamese legal text to extract clause-level amendments or modifications it makes to other documents.
Identify:
1. The target document ID that is being amended (e.g., "nd_06_2021" for Nghị định 06/2021/NĐ-CP).
2. The specific clause/article being amended, converted to an anchor ID (e.g. "d15k2" for Clause 2 Article 15 - Điều 15 Khoản 2, or "d12" for Article 12 - Điều 12).
3. The specific clause in this source document making the amendment (e.g., "Điều 1 Thông tư B" or similar).

Return ONLY a JSON list of objects (inside a markdown json code block) with the following structure:
[
  {{
    "target_doc_id": "target document ID (e.g., 'nd_06_2021')",
    "target_anchor": "HTML anchor of target clause (e.g., 'd15k2')",
    "amendment_source": "Source clause making the amendment (e.g., 'Điều 1 Thông tư B')",
    "source_doc_path": "{source_doc_path}"
  }}
]

If no amendments to other documents are found, return an empty list: [].

Text:
{clean_text}
"""
        reply = self.ai_client.chat(prompt, model=self.model, temperature=0.1, max_tokens=8192)
        res = Cleaners.extract_json(reply)
        if isinstance(res, list):
            for item in res:
                if "source_doc_path" not in item or not item["source_doc_path"]:
                    item["source_doc_path"] = source_doc_path
            return res
        return []
