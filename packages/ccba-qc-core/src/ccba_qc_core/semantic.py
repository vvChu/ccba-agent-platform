"""Semantic Audit Engine — Cross-discipline schedule, text tag, and specification conflict checking."""

from __future__ import annotations

import logging

from ccba_ai import AuditFinding, AuditReport, async_ai, parse_llm_json

logger = logging.getLogger(__name__)

_SEMANTIC_AUDIT_PROMPT = """Bạn là một Chuyên gia BIM Coordinator (BIM Manager) dày dạn kinh nghiệm.
Nhiệm vụ của bạn là thực hiện "Semantic Audit" - đối soát logic dữ liệu thiết kế từ các bản vẽ thuộc 4 bộ môn:
1. Kiến trúc (Arch)
2. Kết cấu (KC)
3. Cơ điện (MEP)
4. Phòng cháy chữa cháy (PCCC)

Dưới đây là DỮ LIỆU BÓC TÁCH (Dạng Text) từ các bản vẽ của tầng: {level_label}.
Tọa độ của text có thể không theo thứ tự, bạn cần dựa vào ngữ nghĩa (Semantic) để nhận diện các bảng biểu (Schedules), ghi chú (Notes), và thông tin phòng (Room Tags).

DỮ LIỆU KIẾN TRÚC:
{d_arch}

DỮ LIỆU KẾT CẤU:
{d_kc}

DỮ LIỆU MEP:
{d_mep}

DỮ LIỆU PCCC:
{d_pccc}

--- YÊU CẦU ---
1. Tìm các mâu thuẫn dữ liệu (Data Inconsistency / Conflicts):
   - Tên phòng, công năng phòng có khớp nhau không?
   - Bảng tải trọng (KC) có khớp với công năng phòng (Arch) không?
   - Ghi chú kỹ thuật (Specs/Notes) của MEP và PCCC có đá nhau không?
2. Bỏ qua các đoạn text rác (ví dụ khung tên, tên người ký, tỷ lệ bản vẽ).

--- ĐẦU RA YÊU CẦU ---
Trả về kết quả dưới dạng chuẩn JSON tuân thủ CHÍNH XÁC cấu trúc sau (không bọc trong markdown tick, không thêm text giải thích):
{{
    "summary": "Tóm tắt ngắn gọn tình trạng nhất quán dữ liệu của toàn bộ mặt bằng (dưới 100 chữ).",
    "conflicts": [
        {{
            "severity": "low/medium/high/critical",
            "disciplines": "VD: Arch vs KC",
            "location": "Tên phòng, bảng biểu, hoặc Grid text...",
            "description": "Mô tả chi tiết sự bất đồng dữ liệu (vd: Bản vẽ Arch ghi phòng X nhưng KC ghi phòng Y)",
            "recommendation": "Đề xuất cách giải quyết (vd: Cập nhật lại tên phòng trên bản vẽ KC)"
        }}
    ]
}}
"""


class SemanticAuditEngine:
    """Đối soát dữ liệu phi hình học giữa các bộ môn (Semantic BIM Conflict)."""

    def __init__(self, ai_model: str = "qwen-local-primary", timeout: float = 300.0) -> None:
        self.ai_model = ai_model
        self.timeout = timeout

    async def run_audit(
        self,
        level_label: str,
        arch_text: str,
        kc_text: str,
        mep_text: str,
        pccc_text: str,
    ) -> AuditReport:
        """Run semantic cross-check on 4 discipline texts for a level."""
        prompt = _SEMANTIC_AUDIT_PROMPT.format(
            level_label=level_label,
            d_arch=arch_text,
            d_kc=kc_text,
            d_mep=mep_text,
            d_pccc=pccc_text,
        )

        logger.info("Gửi dữ liệu text (length: %d) tới %s...", len(prompt), self.ai_model)

        try:
            raw_text = await async_ai.chat_multi(
                model=self.ai_model,
                messages=[
                    {"role": "system", "content": "Bạn là chuyên gia trả về JSON hợp lệ."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=8192,
                temperature=0.1,
            )

            data = parse_llm_json(raw_text)
            if not data:
                logger.error("Failed to parse JSON: %s", raw_text)
                return AuditReport(
                    level=level_label,
                    ai_model=self.ai_model,
                    findings=[],
                    summary="Lỗi trích xuất JSON phản hồi từ AI.",
                    raw_response=raw_text,
                )

            findings: list[AuditFinding] = []
            for item in data.get("conflicts", []):
                sev = item.get("severity", "low").lower()
                disciplines_str = item.get("disciplines", "Unknown")
                disciplines = [
                    d.strip()
                    for d in disciplines_str.replace("vs", ",").replace("&", ",").split(",")
                    if d.strip()
                ]

                findings.append(
                    AuditFinding(
                        severity=sev,
                        location=item.get("location", "Unknown"),
                        disciplines=disciplines,
                        description=item.get("description", "No description"),
                        recommendation=item.get("recommendation", "No recommendation"),
                        source="semantic_audit_engine",
                    )
                )

            return AuditReport(
                level=level_label,
                ai_model=self.ai_model,
                findings=findings,
                summary=str(data.get("summary", "")),
                raw_response=raw_text,
            )
        except Exception as e:
            logger.error("Semantic Audit failed: %s", e)
            return AuditReport(
                level=level_label,
                ai_model=self.ai_model,
                findings=[],
                summary=f"Lỗi phân tích: {e}",
            )
