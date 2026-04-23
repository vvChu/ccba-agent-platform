import asyncio
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
from pydantic import BaseModel
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("SemanticAudit")

class DataConflict(BaseModel):
    severity: str  # e.g., low, medium, high, critical
    disciplines: str # e.g., Arch vs KC
    location: str # e.g., Tên phòng, Grid C-4
    description: str
    recommendation: str

class SemanticAuditResult(BaseModel):
    level: str
    ai_model: str
    conflicts: List[DataConflict]
    summary: str
    high_severity_count: int
    conflict_count: int

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
    def __init__(self, ai_model: str = "qwen-local-primary", timeout: float = 300.0):
        self.ai_model = ai_model
        load_dotenv(Path(__file__).parent.parent.parent.parent.parent / ".env.ai-gateway")
        base_url = os.environ.get("AI_GATEWAY_URL", "http://100.83.192.30:8090/v1")
        api_key = os.environ.get("AI_GATEWAY_KEY", "ccba-internal-key")
        
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout
        )

    async def run_audit(
        self, 
        level_label: str, 
        arch_text: str, 
        kc_text: str, 
        mep_text: str, 
        pccc_text: str
    ) -> SemanticAuditResult:
        
        prompt = _SEMANTIC_AUDIT_PROMPT.format(
            level_label=level_label,
            d_arch=arch_text,
            d_kc=kc_text,
            d_mep=mep_text,
            d_pccc=pccc_text
        )

        logger.info(f"Đang gửi dữ liệu text (length: {len(prompt)}) tới {self.ai_model}...")

        try:
            response = await self.client.chat.completions.create(
                model=self.ai_model,
                messages=[
                    {"role": "system", "content": "Bạn là chuyên gia trả về JSON hợp lệ."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=8192,
                temperature=0.1
            )
            
            raw_text = response.choices[0].message.content
            
            import re
            raw_text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
            
            # First, try to extract from a markdown json block
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, flags=re.DOTALL)
            if match:
                cleaned_text = match.group(1)
            else:
                # Fallback: try to find the first { and match brackets (simplified by just taking the whole string and letting json_repair or loads try)
                start_idx = raw_text.find('{')
                if start_idx != -1:
                    # Very naive fallback: just take from first { to the end, and we'll rfind }
                    end_idx = raw_text.rfind('}')
                    cleaned_text = raw_text[start_idx:end_idx+1]
                else:
                    cleaned_text = raw_text
            
            # Clean any trailing garbage if it has multiple root objects by just taking the first one
            import json
            try:
                # Sometimes json.loads works directly if the string is perfect
                data = json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                # If there's Extra data, we can truncate at the error position!
                if "Extra data" in str(e):
                    # For example: Extra data: line 27 column 5 (char 1552)
                    import re
                    err_match = re.search(r"\(char (\d+)\)", str(e))
                    if err_match:
                        char_pos = int(err_match.group(1))
                        cleaned_text = cleaned_text[:char_pos].strip()
                        data = json.loads(cleaned_text)
                    else:
                        raise e
                else:
                    raise e
            except Exception as e:
                logger.error(f"Failed to parse JSON. Cleaned text was:\n{cleaned_text}")
                raise e
            
            conflicts = []
            high_sev_count = 0
            for item in data.get("conflicts", []):
                sev = item.get("severity", "low").lower()
                if sev in ["high", "critical"]:
                    high_sev_count += 1
                
                conflicts.append(DataConflict(
                    severity=sev,
                    disciplines=item.get("disciplines", "Unknown"),
                    location=item.get("location", "Unknown"),
                    description=item.get("description", "No description"),
                    recommendation=item.get("recommendation", "No recommendation")
                ))

            return SemanticAuditResult(
                level=level_label,
                ai_model=self.ai_model,
                conflicts=conflicts,
                summary=data.get("summary", ""),
                high_severity_count=high_sev_count,
                conflict_count=len(conflicts)
            )

        except Exception as e:
            logger.error(f"Semantic Audit failed: {e}")
            raise
