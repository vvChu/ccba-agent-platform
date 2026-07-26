"""Module generating legal advisory documents compliant with Decree 30/2020/NĐ-CP formatting."""

from datetime import datetime
from typing import Dict, Any, List
from scripts.legal_grounding_gate import format_grounded_response

SUPPORTED_DOC_TYPES = ["compliance_report", "inquiry_letter", "contract_risk_advisory"]

ND30_HEADER = """
TRUNG TÂM TƯ VẤN VÀ ỨNG DỤNG BIM    CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
        TRONG XÂY DỰNG (CCBA)                 Độc lập - Tự do - Hạnh phúc
     -----------------------                      -----------------------
"""


def generate_legal_document(doc_type: str, data: Dict[str, Any]) -> str:
    """Generate standardized legal document formatted per NĐ 30/2020/NĐ-CP."""
    if doc_type not in SUPPORTED_DOC_TYPES:
        raise ValueError(f"Unsupported document type '{doc_type}'. Must be one of: {SUPPORTED_DOC_TYPES}")

    today_str = datetime.now().strftime("ngày %d tháng %m năm %Y")
    author = data.get("author", "Hệ thống AI Agent CCBA")
    subject = data.get("subject", "Tư vấn Pháp luật Xây dựng")
    raw_content = data.get("advisory_content", "")
    retrieved_docs = data.get("retrieved_docs", [])

    # Format content with grounding verifier & disclaimer
    grounded_content = format_grounded_response(raw_content, retrieved_docs)

    if doc_type == "compliance_report":
        project = data.get("project_name", "Dự án Xây dựng")
        doc_body = f"""{ND30_HEADER.strip()}
                            Hà Nội, {today_str}

                  BÁO CÁO TƯ VẤN TUÂN THỦ PHÁP LÝ
               Về việc: {subject}
               Dự án: {project}

I. THÔNG TIN DỰ ÁN & PHẠM VI RÀ SOÁT
- Tên dự án: {project}
- Nội dung rà soát: {subject}
- Đơn vị thực hiện: Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng (CCBA)

II. NỘI DUNG TƯ VẤN CHI TIẾT & ĐÁNH GIÁ TUÂN THỦ
{grounded_content}

III. NƠI NHẬN & CHỮ KÝ
- Chủ đầu tư / Ban QLDA;
- Lưu: VT, HS Dự án.

                     ĐẠI DIỆN ĐỘI NGŨ THẨM ĐỊNH CCBA
                                {author}
"""

    elif doc_type == "inquiry_letter":
        recipient = data.get("recipient", "Cơ quan Quản lý Nhà nước về Xây dựng")
        doc_body = f"""{ND30_HEADER.strip()}
Số: .../CV-CCBA                               Hà Nội, {today_str}
V/v: {subject}

                   CÔNG VĂN HỎI Ý KIẾN CHUYÊN MÔN

Kính gửi: {recipient}

Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng (CCBA) trân trọng gửi công văn tới {recipient} để xin ý kiến hướng dẫn nghiệp vụ đối với nội dung sau:

1. Nội dung thắc mắc & Căn cứ thực tiễn:
{grounded_content}

2. Kiến nghị & Đề xuất:
Kính đề nghị {recipient} xem xét, cho ý kiến hướng dẫn chính thức để CCBA và các đơn vị liên quan có căn cứ triển khai công việc đúng quy định pháp luật.

Trân trọng cảm ơn./.

Nơi nhận:
- Như trên;
- Ban Giám đốc CCBA;
- Lưu: VT.
                                  GIÁM ĐỐC / TRƯỞNG ĐOÀN
                                       {author}
"""

    else:  # contract_risk_advisory
        doc_body = f"""{ND30_HEADER.strip()}
                            Hà Nội, {today_str}

                 THƯ PHẢN HỒI RỦI RO HỢP ĐỒNG XÂY DỰNG
               Về việc: {subject}

{grounded_content}

                     ĐỘI NGŨ PHÁP LÝ & HỢP ĐỒNG CCBA
                                {author}
"""

    return doc_body.strip()
