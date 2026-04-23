import asyncio
import json
import logging
from pathlib import Path
from pydantic import BaseModel
from openai import AsyncOpenAI
import os
import argparse
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("PcccMapReduce")

# Limit characters per chunk (approx 10k-15k tokens)
CHAR_LIMIT = 45000

class MapReduceEngine:
    def __init__(self, ai_model: str = "qwen-local-primary", timeout: float = 600.0):
        self.ai_model = ai_model
        load_dotenv(Path(r"d:\GitHubProjects\ccba-agent-platform\.env.ai-gateway"))
        base_url = os.environ.get("AI_GATEWAY_URL", "http://100.83.192.30:8090/v1")
        api_key = os.environ.get("AI_GATEWAY_KEY", "ccba-internal-key")
        
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout
        )

    async def _query_llm(self, system_prompt: str, user_prompt: str) -> dict:
        logger.info(f"Đang gửi request (length: {len(user_prompt)}) tới {self.ai_model}...")
        response = await self.client.chat.completions.create(
            model=self.ai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=8192,
            temperature=0.1
        )
        
        raw_text = response.choices[0].message.content
        import re
        raw_text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
        
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, flags=re.DOTALL)
        if match:
            cleaned_text = match.group(1)
        else:
            start_idx = raw_text.find('{')
            end_idx = raw_text.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                cleaned_text = raw_text[start_idx:end_idx+1]
            else:
                cleaned_text = raw_text
                
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON. Raw text was:\n{cleaned_text}")
            return {"error": "Failed to parse JSON", "raw": cleaned_text}

    async def run_package_1_legal(self, thuyet_minh: str, gop_y: str) -> dict:
        system_prompt = "Bạn là chuyên gia PCCC (QCVN 06:2022/BXD, TCVN 3890:2023). Trả về JSON."
        prompt = f"""[GÓI 1: PHÁP LÝ & THUYẾT MINH]
THUYẾT MINH: {thuyet_minh}
GÓP Ý PC07 (Nếu có): {gop_y}

YÊU CẦU:
1. Đánh giá tính tuân thủ của Thuyết minh đối với QCVN 06:2022/BXD và TCVN 3890:2023 (bậc chịu lửa, khoảng cách an toàn, trang bị ban đầu).
2. Kiểm tra xem Thuyết minh đã cập nhật các góp ý của PC07 chưa.
Trích xuất lỗi vào JSON:
{{
    "findings": [
        {{"severity": "high/medium/low", "issue": "...", "recommendation": "..."}}
    ]
}}"""
        return await self._query_llm(system_prompt, prompt)

    async def run_package_2_mep_water(self, mep_pccc: str, thuyet_minh: str) -> dict:
        system_prompt = "Bạn là kỹ sư MEP PCCC. Trả về JSON."
        prompt = f"""[GÓI 2: MEP NƯỚC & BƠM VS THUYẾT MINH]
THUYẾT MINH (Tóm tắt): {thuyet_minh}
BẢN VẼ MEP PCCC (Nước/Bơm/Bể): {mep_pccc}

YÊU CẦU:
So sánh thông số thiết bị (Dung tích bể, Lưu lượng bơm, Cột áp, Đầu phun Sprinkler) giữa Bản vẽ và Thuyết minh.
Trích xuất lỗi vào JSON:
{{
    "findings": [
        {{"severity": "high/medium/low", "issue": "...", "recommendation": "..."}}
    ]
}}"""
        return await self._query_llm(system_prompt, prompt)

    async def run_package_3_mep_alarm(self, mep_pccc: str, arch_pccc: str) -> dict:
        system_prompt = "Bạn là kỹ sư PCCC (Báo cháy & Kiến trúc). Trả về JSON."
        prompt = f"""[GÓI 3: MEP BÁO CHÁY VS KIẾN TRÚC]
BẢN VẼ KIẾN TRÚC PCCC: {arch_pccc}
BẢN VẼ MEP PCCC (Báo cháy/Thoát nạn): {mep_pccc}

YÊU CẦU:
1. Kiểm tra vị trí đầu báo, nút ấn, đèn Exit trên bản vẽ Kiến trúc có đồng bộ với sơ đồ Báo cháy MEP không?
2. Tuân thủ TCVN 5738:2021 về khoảng cách đầu báo và vị trí báo cháy.
Trích xuất lỗi vào JSON:
{{
    "findings": [
        {{"severity": "high/medium/low", "issue": "...", "recommendation": "..."}}
    ]
}}"""
        return await self._query_llm(system_prompt, prompt)

    async def run_package_4_reducer(self, findings: list) -> dict:
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

async def main():
    parser = argparse.ArgumentParser(description="CCBA Semantic PCCC Audit Engine")
    parser.add_argument("--tm", type=str, required=True, help="Đường dẫn đến file Markdown Thuyết minh PCCC")
    parser.add_argument("--arch", type=str, required=True, help="Đường dẫn đến file Markdown Kiến trúc PCCC")
    parser.add_argument("--mep", type=str, required=True, help="Đường dẫn đến file Markdown MEP PCCC")
    parser.add_argument("--gopy", type=str, required=False, default="", help="Đường dẫn đến file Markdown Góp ý PC07 (tuỳ chọn)")
    parser.add_argument("--model", type=str, default="qwen-local-primary", help="Tên model LLM (mặc định: qwen-local-primary)")
    parser.add_argument("--out", type=str, default="PCCC_MapReduce_Report.md", help="Đường dẫn file báo cáo đầu ra")

    args = parser.parse_args()

    tm_path = Path(args.tm)
    arch_path = Path(args.arch)
    mep_path = Path(args.mep)
    pc07_path = Path(args.gopy) if args.gopy else None
    
    thuyet_minh = tm_path.read_text(encoding="utf-8") if tm_path.exists() else ""
    arch_pccc = arch_path.read_text(encoding="utf-8") if arch_path.exists() else ""
    mep_pccc = mep_path.read_text(encoding="utf-8") if mep_path.exists() else ""
    gop_y = pc07_path.read_text(encoding="utf-8") if (pc07_path and pc07_path.exists()) else ""
    
    if not thuyet_minh:
        logger.warning(f"Không tìm thấy file Thuyết minh hoặc file trống: {args.tm}")
    if not arch_pccc:
        logger.warning(f"Không tìm thấy file Kiến trúc hoặc file trống: {args.arch}")
    if not mep_pccc:
        logger.warning(f"Không tìm thấy file MEP hoặc file trống: {args.mep}")
    
    engine = MapReduceEngine(ai_model=args.model)
    
    all_findings = []
    
    # PACKAGE 1
    logger.info("=== BẮT ĐẦU GÓI 1: PHÁP LÝ & THUYẾT MINH ===")
    res1 = await engine.run_package_1_legal(thuyet_minh[:CHAR_LIMIT], gop_y)
    if "findings" in res1:
        for f in res1["findings"]: f["source"] = "Package 1: Legal & Specs"
        all_findings.extend(res1["findings"])
        
    # PACKAGE 2
    logger.info("=== BẮT ĐẦU GÓI 2: MEP NƯỚC VS THUYẾT MINH ===")
    mep_water_part = mep_pccc[:len(mep_pccc)//2] if mep_pccc else ""
    res2 = await engine.run_package_2_mep_water(mep_water_part[:CHAR_LIMIT], thuyet_minh[:CHAR_LIMIT])
    if "findings" in res2:
        for f in res2["findings"]: f["source"] = "Package 2: MEP Water vs Specs"
        all_findings.extend(res2["findings"])
        
    # PACKAGE 3
    logger.info("=== BẮT ĐẦU GÓI 3: MEP BÁO CHÁY VS KIẾN TRÚC ===")
    mep_alarm_part = mep_pccc[len(mep_pccc)//2:] if mep_pccc else ""
    res3 = await engine.run_package_3_mep_alarm(mep_alarm_part[:CHAR_LIMIT], arch_pccc[:CHAR_LIMIT])
    if "findings" in res3:
        for f in res3["findings"]: f["source"] = "Package 3: MEP Alarm vs Arch"
        all_findings.extend(res3["findings"])
        
    # PACKAGE 4
    logger.info("=== BẮT ĐẦU GÓI 4: REDUCER (TỔNG HỢP) ===")
    res4 = await engine.run_package_4_reducer(all_findings)
    
    # OUTPUT REPORT
    report_md = [
        f"# Báo cáo Đánh giá Chất lượng Hồ sơ PCCC",
        f"> **Model sử dụng:** {args.model}",
        "",
        f"- **Điểm chất lượng:** {res4.get('overall_quality_score', 'N/A')}",
        f"- **Tình trạng tuân thủ QCVN:** {res4.get('qcvn_compliance_status', 'N/A')}",
        "## Tóm tắt",
        res4.get('summary', ''),
        "## Các Vấn đề Tồn tại (Final Findings)"
    ]
    
    for i, finding in enumerate(res4.get('final_findings', []), 1):
        report_md.append(f"### {i}. [{finding.get('severity', '').upper()}] - {finding.get('category', 'General')}")
        report_md.append(f"**Vấn đề:** {finding.get('issue', '')}")
        report_md.append(f"**Đề xuất:** {finding.get('recommendation', '')}\n")
        
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(report_md), encoding="utf-8")
    logger.info(f"✅ Đã hoàn thành toàn bộ Map-Reduce Audit và lưu vào {args.out}")

if __name__ == "__main__":
    asyncio.run(main())
