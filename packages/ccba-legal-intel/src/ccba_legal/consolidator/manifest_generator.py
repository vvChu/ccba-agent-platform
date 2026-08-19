"""LLM-Assisted Patch Manifest Generator via CCBA AI Gateway."""

import json
import re
from pathlib import Path
from typing import Any
import yaml

from .patch_manifest_schema import (
    DefectSeverity,
    DocMode,
    PatchAction,
    PatchItem,
    PatchManifest,
)


class ManifestGenerator:
    """Uses LLM (AI Gateway) to analyze amending text and generate PatchManifest YAML draft."""

    SYSTEM_PROMPT = """Bạn là Chuyên gia Pháp lý AI của CCBA Platform.
Nhiệm vụ của bạn là phân tích Văn bản Gốc và Văn bản Sửa đổi (Thông tư/Nghị định) để trích xuất danh sách các Thao tác Lập quy (Action Tokens).

Các Action Token hỗ trợ:
- REPLACE: Sửa đổi toàn bộ điều khoản/bảng biểu.
- INSERT_AFTER: Bổ sung điều khoản mới vào sau một điều khoản cụ thể.
- INSERT_BEFORE: Bổ sung điều khoản mới vào trước một điều khoản.
- APPEND: Bổ sung nội dung vào cuối điều khoản hiện có.
- INSERT_RANGE_AFTER: Bổ sung một dải nhiều điều khoản con (ví dụ 1.4.31 đến 1.4.34).
- REPEAL: Bãi bỏ điều khoản/bảng biểu.
- SUBSTITUTE_PHRASE: Thay thế cụm từ kỹ thuật cụ thể.

Xuất ra định dạng JSON tuân thủ schema:
{
  "target_doc_id": "string",
  "amending_doc_id": "string",
  "doc_mode": "qcvn | luat | nghi_dinh | thong_tu",
  "title": "string",
  "official_citation": "string",
  "effective_date": "YYYY-MM-DD",
  "default_cong_bao_number": "string",
  "default_jurisdiction": "CQXD | CONG_AN",
  "patches": [
    {
      "action": "REPLACE | INSERT_AFTER | APPEND | INSERT_RANGE_AFTER | REPEAL | SUBSTITUTE_PHRASE",
      "target_anchor": "string (ví dụ: muc-1-1-2 hoặc D5)",
      "new_anchor": "string (nếu có)",
      "new_anchors": ["string"] (nếu là INSERT_RANGE_AFTER),
      "citation": "string (Căn cứ pháp lý)",
      "defect_severity": "CRITICAL_DEFECT | WARNING_NOTICE | INFORMATIVE",
      "jurisdiction": "CQXD | CONG_AN",
      "grace_period_end": "YYYY-MM-DD (nếu có quy định chuyển tiếp)",
      "new_content_inline": "string (nội dung mới đầy đủ)"
    }
  ]
}
Chỉ xuất DUY NHẤT mã JSON hợp lệ, không kèm giải thích."""

    def generate_manifest_from_files(
        self,
        base_md_path: Path | str,
        amending_md_path: Path | str,
        output_yaml_path: Path | str | None = None,
        mock_response: str | None = None,
    ) -> PatchManifest:
        """Analyze base and amendment files to produce a validated PatchManifest draft."""
        base_text = Path(base_md_path).read_text(encoding="utf-8")
        amending_text = Path(amending_md_path).read_text(encoding="utf-8")

        raw_json = ""
        if mock_response:
            raw_json = mock_response.strip()
        else:
            try:
                from ccba_ai import ai

                prompt = f"{self.SYSTEM_PROMPT}\n\n--- VĂN BẢN GỐC ---\n{base_text[:4000]}\n\n--- VĂN BẢN SỬA ĐỔI ---\n{amending_text[:8000]}"
                response = ai.chat(prompt)
                raw_json = response.strip()
            except Exception as exc:
                raise RuntimeError(f"AI Gateway invocation failed: {exc}")

        # Clean JSON markdown blocks
        if raw_json.startswith("```"):
            raw_json = re.sub(r"^```[a-z]*\n?", "", raw_json)
            raw_json = re.sub(r"\n?```$", "", raw_json).strip()

        data = json.loads(raw_json)
        manifest = PatchManifest.from_dict(data)

        if output_yaml_path:
            out_p = Path(output_yaml_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            with open(out_p, "w", encoding="utf-8") as f:
                yaml.dump(manifest.to_dict(), f, allow_unicode=True, sort_keys=False)

        return manifest
