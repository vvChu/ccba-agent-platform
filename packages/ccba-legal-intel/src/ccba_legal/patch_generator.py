"""Delta Patch Generator and Dry-Run Verification Engine via AI Gateway."""

import json
import re

from .ast_parser import ASTNode, ASTParser, DeltaPatch, PatchAction


class DeltaPatchGenerator:
    """Generates and verifies DeltaPatch objects for legal document consolidation."""

    SYSTEM_PROMPT = """You are a Legal Intelligence Assistant. Your task is to analyze two legal texts:
1. The Original Legal Document (or Clause)
2. The Amending Document (or Amending Clause)

Identify what changes are being made (REPLACE, INSERT_AFTER, ABROGATE, SUSPEND) and output a JSON object adhering to this schema:
{
  "target_doc_id": "string",
  "amending_doc_id": "string",
  "patches": [
    {
      "node_id": "string (e.g. D1-K1 or D1-K2-Pa)",
      "action": "REPLACE | INSERT_AFTER | ABROGATE | SUSPEND",
      "old_text_anchor": "exact text snippet from original node to match",
      "new_content": "new text content to insert or replace with",
      "citation": "citation explanation string"
    }
  ]
}
Output ONLY raw JSON with no extra markdown codeblocks or text."""

    def generate_patch_from_text(
        self,
        target_doc_id: str,
        amending_doc_id: str,
        original_text: str,
        amending_text: str,
        mock_llm_response: str | None = None,
    ) -> DeltaPatch:
        """Generate a DeltaPatch from original and amending text using AI Gateway or mock response."""
        if mock_llm_response:
            raw_json = mock_llm_response.strip()
            if raw_json.startswith("```json"):
                raw_json = raw_json.replace("```json", "").replace("```", "").strip()
            data = json.loads(raw_json)
            return DeltaPatch.from_dict(data)

        # Real AI Gateway invocation
        try:
            from ccba_ai import ai

            user_prompt = f"""Original Text:\n{original_text}\n\nAmending Text:\n{amending_text}"""
            response_text = ai.chat(f"{self.SYSTEM_PROMPT}\n\n{user_prompt}")
            clean_json = response_text.strip()
            if clean_json.startswith("```"):
                clean_json = re.sub(r"^```[a-z]*\n?", "", clean_json)
                clean_json = re.sub(r"\n?```$", "", clean_json).strip()

            data = json.loads(clean_json)
            return DeltaPatch.from_dict(data)
        except Exception:
            # Fallback empty patch on error
            return DeltaPatch(
                target_doc_id=target_doc_id,
                amending_doc_id=amending_doc_id,
                patches=[],
            )

    def apply_patch_dry_run(
        self,
        nodes: list[ASTNode],
        patch: DeltaPatch,
    ) -> tuple[bool, list[str]]:
        """Validate all patch items against the AST nodes tree without mutating.

        Returns:
            (is_valid, error_list)
        """
        parser = ASTParser()
        flat_nodes = parser.flatten_ast(nodes)
        errors: list[str] = []

        for item in patch.patches:
            target_node = flat_nodes.get(item.node_id)
            if not target_node:
                errors.append(
                    f"[NODE_NOT_FOUND] Node ID '{item.node_id}' does not exist in AST tree."
                )
                continue

            if item.action in (PatchAction.REPLACE, PatchAction.ABROGATE):
                if item.old_text_anchor and item.old_text_anchor not in target_node.content:
                    errors.append(
                        f"[ANCHOR_MISMATCH] Node '{item.node_id}' content does not contain old_text_anchor: '{item.old_text_anchor}'"
                    )

        return (len(errors) == 0, errors)
