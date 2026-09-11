"""PCCC Map-Reduce Engine — Specialized regulatory compliance audit for QCVN 06:2022/BXD and TCVN 3890:2023."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from ccba_ai import async_ai, parse_llm_json

logger = logging.getLogger(__name__)

CHAR_LIMIT = 45000


class PcccMapReduceEngine:
    """Semantic PCCC Audit Engine chia 4 gói Map-Reduce."""

    def __init__(self, ai_model: str = "qwen-local-primary", timeout: float = 600.0) -> None:
        self.ai_model = ai_model
        self.timeout = timeout

    async def _query_llm(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        logger.info("Sending request (length: %d) to %s...", len(user_prompt), self.ai_model)
        raw_text = await async_ai.chat_multi(
            model=self.ai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=8192,
            temperature=0.1,
        )

        data = parse_llm_json(raw_text)
        if isinstance(data, dict):
            res: dict[str, Any] = dict(data)
            return res
        return {"error": "Failed to parse JSON", "raw": raw_text}

    async def run_package_1_legal(self, thuyet_minh: str, gop_y: str = "") -> dict[str, Any]:
        """Gói 1: Pháp lý & Thuyết minh."""
        system_prompt = "Bạn là chuyên gia PCCC (QCVN 06:2022/BXD, TCVN 3890:2023). Trả về JSON."
        prompt = f"""[GÓI 1: PHÁP LÝ & THUYẾT MINH]
THUYẾT MINH: {thuyet_minh}
GÓP Ý PC07 (Nếu có): {gop_y}

YÊU CẦU:
1. Đánh giá tính tuân thủ của Thuyết minh đối với QCVN 06:2022/BXD và TCVN 3890:2023.
2. Kiểm tra xem Thuyết minh có liệt kê các Phụ lục tính toán (Âm thanh, Ắc quy, Thủy lực bơm 150%, Bình dự trữ 10%) hay không. Nếu không, báo lỗi.
3. Bắt buộc kiểm tra nội dung kết nối mạng truyền tin báo cháy GTEL (QĐ 8390/QĐ-BCA) và PCCC cho lán trại tạm thời giai đoạn thi công.
4. Kiểm tra xem Thuyết minh đã cập nhật đầy đủ các góp ý của PC07 chưa.
Trích xuất lỗi vào JSON:
{{
    "findings": [
        {{"severity": "high/medium/low", "issue": "...", "recommendation": "..."}}
    ]
}}"""
        return await self._query_llm(system_prompt, prompt)

    async def run_package_2_mep_water(self, mep_pccc: str, thuyet_minh: str) -> dict[str, Any]:
        """Gói 2: MEP Nước & Bơm vs Thuyết minh."""
        system_prompt = "Bạn là kỹ sư MEP PCCC. Trả về JSON."
        prompt = f"""[GÓI 2: MEP NƯỚC & BƠM VS THUYẾT MINH]
THUYẾT MINH (Tóm tắt): {thuyet_minh}
BẢN VẼ MEP PCCC (Nước/Bơm/Bể): {mep_pccc}

YÊU CẦU:
1. So sánh thông số thiết bị (Dung tích bể, Lưu lượng bơm, Cột áp, Đầu phun Sprinkler) giữa Bản vẽ và Thuyết minh.
2. Kiểm tra điểm làm việc của bơm: Đối chiếu thông số Bơm phải thỏa mãn QCVN 02:2020 (Ở 150% Lưu lượng thiết kế thì Cột áp không nhỏ hơn 65%).
Trích xuất lỗi vào JSON:
{{
    "findings": [
        {{"severity": "high/medium/low", "issue": "...", "recommendation": "..."}}
    ]
}}"""
        return await self._query_llm(system_prompt, prompt)

    async def run_package_3_mep_alarm(self, mep_pccc: str, arch_pccc: str) -> dict[str, Any]:
        """Gói 3: MEP Báo cháy vs Kiến trúc."""
        system_prompt = "Bạn là kỹ sư PCCC (Báo cháy & Kiến trúc). Trả về JSON."
        prompt = f"""[GÓI 3: MEP BÁO CHÁY VS KIẾN TRÚC]
BẢN VẼ KIẾN TRÚC PCCC: {arch_pccc}
BẢN VẼ MEP PCCC (Báo cháy/Thoát nạn): {mep_pccc}

YÊU CẦU:
1. Kiểm tra vị trí đầu báo, nút ấn, đèn Exit trên bản vẽ Kiến trúc có đồng bộ với sơ đồ Báo cháy MEP không?
2. Quét các ghi chú (Note/Text) trên bản vẽ Kiến trúc để tìm kiếm các quy định của CQXD: biển báo 'LỐI VÀO TỪ TRÊN CAO', 'GIAN LÁNH NẠN', và sơn kẻ vạch phản quang bãi đỗ xe chữa cháy. Báo lỗi nếu thiếu.
3. Tuân thủ TCVN 5738:2021 về khoảng cách đầu báo và vị trí báo cháy.
Trích xuất lỗi vào JSON:
{{
    "findings": [
        {{"severity": "high/medium/low", "issue": "...", "recommendation": "..."}}
    ]
}}"""
        return await self._query_llm(system_prompt, prompt)

    async def run_package_4_reducer(self, findings: list[dict[str, Any]]) -> dict[str, Any]:
        """Gói 4: Tổng hợp (Reducer)."""
        system_prompt = "Bạn là Trưởng phòng QA PCCC. Trả về JSON."
        prompt = f"""[GÓI 4: TỔNG HỢP (REDUCER)]
Dưới đây là các lỗi (findings) được phát hiện từ 3 gói kiểm tra riêng biệt:
{json.dumps(findings, ensure_ascii=False, indent=2)}

YÊU CẦU:
Tổng hợp lại, loại bỏ các lỗi trùng lặp, chấm điểm hồ sơ (0-100) và xuất ra JSON:
{{
    "overall_quality_score": 85,
    "summary": "Tóm tắt...",
    "qcvn_compliance_status": "PASS/FAIL/NEEDS_REVIEW",
    "final_findings": [
        {{"severity": "critical/high/medium/low", "category": "...", "issue": "...", "recommendation": "..."}}
    ]
}}"""
        return await self._query_llm(system_prompt, prompt)

    async def execute_full_audit(
        self,
        thuyet_minh: str,
        arch_pccc: str,
        mep_pccc: str,
        gop_y: str = "",
        output_file: Path | None = None,
    ) -> dict[str, Any]:
        """Execute full 4-stage map reduce pipeline and optionally save markdown report."""
        all_findings: list[dict[str, Any]] = []

        res1 = await self.run_package_1_legal(thuyet_minh[:CHAR_LIMIT], gop_y)
        if "findings" in res1 and isinstance(res1["findings"], list):
            for f in res1["findings"]:
                f["source"] = "Package 1: Legal & Specs"
            all_findings.extend(res1["findings"])

        mep_water_part = mep_pccc[: len(mep_pccc) // 2] if mep_pccc else ""
        res2 = await self.run_package_2_mep_water(
            mep_water_part[:CHAR_LIMIT], thuyet_minh[:CHAR_LIMIT]
        )
        if "findings" in res2 and isinstance(res2["findings"], list):
            for f in res2["findings"]:
                f["source"] = "Package 2: MEP Water vs Specs"
            all_findings.extend(res2["findings"])

        mep_alarm_part = mep_pccc[len(mep_pccc) // 2 :] if mep_pccc else ""
        res3 = await self.run_package_3_mep_alarm(
            mep_alarm_part[:CHAR_LIMIT], arch_pccc[:CHAR_LIMIT]
        )
        if "findings" in res3 and isinstance(res3["findings"], list):
            for f in res3["findings"]:
                f["source"] = "Package 3: MEP Alarm vs Arch"
            all_findings.extend(res3["findings"])

        res4 = await self.run_package_4_reducer(all_findings)

        if output_file:
            report_md = [
                "# Báo cáo Đánh giá Chất lượng Hồ sơ PCCC",
                f"> **Model sử dụng:** {self.ai_model}",
                "",
                f"- **Điểm chất lượng:** {res4.get('overall_quality_score', 'N/A')}",
                f"- **Tình trạng tuân thủ QCVN:** {res4.get('qcvn_compliance_status', 'N/A')}",
                "## Tóm tắt",
                str(res4.get("summary", "")),
                "## Các Vấn đề Tồn tại (Final Findings)",
            ]
            for i, finding in enumerate(res4.get("final_findings", []), 1):
                report_md.append(
                    f"### {i}. [{str(finding.get('severity', '')).upper()}] - {finding.get('category', 'General')}"
                )
                report_md.append(f"**Vấn đề:** {finding.get('issue', '')}")
                report_md.append(f"**Đề xuất:** {finding.get('recommendation', '')}\n")

            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text("\n".join(report_md), encoding="utf-8")

        return res4


# Backward compatibility alias
MapReduceEngine = PcccMapReduceEngine
