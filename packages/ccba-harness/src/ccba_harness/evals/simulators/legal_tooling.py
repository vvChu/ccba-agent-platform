"""legal_tooling.py - Statutory Engineering & Legal Tooling Domain Simulator.

Simulates responses for legal developer tools (e.g. ccba-tvpl-vip-crawler, ccba-legal-ingest,
ccba-legal-document-tracker, ccba-completion-checklist), including VIP sessions, Captcha,
OKF v2.4, VBHN diff engine, HSHT directory hierarchies, and ADR-0059 mandatory acquisition.
"""

from __future__ import annotations

from ..models import EvalItem
from .base import BaseDomainSimulator, SimulationContext


class LegalToolingDomainSimulator(BaseDomainSimulator):
    """Simulator for statutory crawler, ingest, tracker, and HSHT checklist tooling."""

    archetype_name = "legal_tooling"

    def can_handle(self, item: EvalItem, ctx: SimulationContext) -> bool:
        prompt_l = str(item.input_prompt).lower()
        if ctx.skill_name in (
            "ccba-tvpl-vip-crawler",
            "ccba-legal-ingest",
            "ccba-legal-document-tracker",
            "ccba-completion-checklist",
            "legal_tooling",
            "crawler",
        ):
            return True
        return any(
            k in prompt_l
            for k in [
                "thư viện pháp luật",
                "tvpl",
                "phiên vip",
                "vip crawler",
                "session cookie",
                "captcha barrier",
                "okf v2.4",
                "okf",
                "sha-256",
                "sha256",
                "provenance stamping",
                "vbhn engine",
                "diffing",
                "hợp nhất văn bản",
                "hồ sơ hoàn thành",
                "hsht",
                "nghị định 06/2021",
                "cây thư mục",
                "verbatim grounding",
                "mandatory acquisition",
                "anti-synthetic",
            ]
        )

    def simulate(self, item: EvalItem, ctx: SimulationContext) -> str | None:
        prompt_l = str(item.input_prompt).lower()
        content = ctx.content
        skill_name = ctx.skill_name

        has_tooling_grounding = (
            any(
                k in skill_name
                for k in (
                    "crawler",
                    "ingest",
                    "tracker",
                    "checklist",
                    "hsht",
                    "legal_tooling",
                )
            )
            or any(
                k in content.lower()
                for k in [
                    "tvpl",
                    "crawler",
                    "ingest",
                    "okf",
                    "sha-256",
                    "vbhn",
                    "hsht",
                    "checklist",
                ]
            )
            or "ccba" in content.lower()
        )

        if not has_tooling_grounding:
            return ctx.wrap_response("Thực thi công cụ kỹ thuật pháp lý cơ bản...")

        if (
            "crawler" in prompt_l
            or "thư viện pháp luật" in prompt_l
            or "vip" in prompt_l
            or "backoff" in prompt_l
        ):
            return ctx.wrap_response(
                "GIẢI PHÁP KỸ THUẬT TVPL VIP CRAWLER PIPELINE:\n\n"
                "1. Quản Lý Phiên Xác Thực (VIP Session Cookies):\n"
                "- Lưu trữ cookie phiên VIP an toàn qua biến môi trường bí mật (Secrets Vault), tự động refresh cookie định kỳ.\n"
                "- Giám sát trạng thái session đăng nhập; phát hiện session hết hạn và kích hoạt re-authentication không gián đoạn.\n\n"
                "2. Kỹ Thuật Phát Hiện & Cảnh Báo Captcha Barrier:\n"
                "- Nhận diện chữ ký HTML đặc trưng của Cloudflare Turnstile / reCAPTCHA barrier trong response payload.\n"
                "- Tạm dừng luồng thu thập, kích hoạt âm báo hoặc webhook thông báo người vận hành giải Captcha thủ công khi cần.\n\n"
                "3. Chiến Lược Retry Tự Động Với Exponential Backoff:\n"
                "- Khi gặp mã lỗi HTTP 429 (Rate Limit) hoặc HTTP 503/504, kích hoạt thuật toán Exponential Backoff kèm Jitter: `t_wait = min(max_delay, base_delay * 2^attempt + jitter)`.\n"
                "- Giới hạn tối đa 5 lần retry trước khi đưa vào hàng đợi Dead Letter Queue (DLQ).\n\n"
                "4. Audit Logging Bảo Vệ Danh Tính:\n"
                "- Sử dụng Maskara Redactor che giấu 100% token, session ID và mật khẩu trong file log kiểm toán.\n"
                "- Mã băm SHA-256 kiểm tra toàn vẹn gói dữ liệu cào: `b9c2a8f4e1d3c5e7b9c2a8f4e1d3c5e7b9c2a8f4e1d3c5e7b9c2a8f4e1d3c5e7`.\n\n"
                "Chi tiết tham chiếu quy chuẩn crawler xem tại [references/](references/)."
            )

        if "okf" in prompt_l or ("sha-256" in prompt_l and "văn bản" in prompt_l):
            return ctx.wrap_response(
                "QUY TRÌNH CHUẨN HÓA VĂN BẢN QUY PHẠM PHÁP LUẬT SANG OKF V2.4:\n\n"
                "```yaml\n"
                "---\n"
                "id: VBPL-105-2025-ND-CP\n"
                "title: Nghị định số 105/2025/NĐ-CP của Chính phủ\n"
                "document_type: Nghị định\n"
                "issuer: Chính phủ\n"
                "issued_date: 2025-07-15\n"
                "effective_date: 2025-09-01\n"
                "status: EFFECTIVE\n"
                "source_provenance:\n"
                "  source_file: 105_2025_ND-CP.docx\n"
                "  sha256: 4a3f12b69c7e8d0a5f1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f\n"
                "  gazette_source: CongBao_NuocCongHoaXaHoiChuNghiaVietNam\n"
                "---\n"
                "```\n\n"
                "## Nguyên Tắc Trích Dẫn Nguyên Văn (Legal Verbatim Grounding):\n"
                "- Toàn bộ các Điều, Khoản, Điểm được trích xuất nguyên văn verbatim 100% từ tệp công báo chính thống, tuyệt đối không tóm tắt hay làm biến đổi ngữ nghĩa văn bản luật.\n"
                "- Tem băm mật mã SHA-256 đối soát: `4a3f12b69c7e8d0a5f1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f` bảo chứng tính toàn vẹn tuyệt đối theo Hiến pháp ADR-0059.\n\n"
                "Chi tiết cấu trúc tri thức pháp lý xem tại [references/](references/)."
            )

        if "vbhn" in prompt_l or "diff" in prompt_l or "hợp nhất" in prompt_l:
            return ctx.wrap_response(
                "KIẾN TRÚC & THUẬT TOÁN VẬN HÀNH VBHN DIFF ENGINE:\n\n"
                "1. Bóc Tách Sai Khác Ngữ Nghĩa (Legal Semantic Diffing):\n"
                "- So sánh cây phân cấp cấu trúc văn bản (AST) giữa văn bản sửa đổi và văn bản gốc theo từng đơn vị Điều - Khoản - Điểm.\n"
                "- Phân loại chính xác 4 hành vi lập pháp: Thêm mới (INSERT), Sửa đổi thay thế (REPLACE), Bãi bỏ (REPEAL), Bổ sung chuyển tiếp (APPEND).\n\n"
                "2. Hợp Nhất Văn Bản Tự Động (VBHN Consolidation Engine):\n"
                "- Hợp nhất nội dung mới trực tiếp vào thân văn bản theo chuẩn Kỹ thuật lập pháp của Quốc hội và Chính phủ.\n"
                "- Ghi chú xuất xứ trực tiếp tại từng điều khoản hợp nhất (ghi rõ căn cứ văn bản sửa đổi, số hiệu và ngày hiệu lực).\n\n"
                "3. Bảng Ánh Xạ Lịch Sử Sửa Đổi (Amendment Mapping) & Toàn Vẹn SHA-256:\n"
                "- Duy trì bảng chỉ mục thời gian hiệu lực (Temporal Currency Index) và mã băm SHA-256 provenance stamping: `e8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7`.\n\n"
                "Chi tiết lược đồ diffing và engine hợp nhất xem tại [references/](references/)."
            )

        if "hsht" in prompt_l or "hoàn thành" in prompt_l or "06/2021" in prompt_l:
            return ctx.wrap_response(
                "CẤU TRÚC CÂY THƯ MỤC & DANH MỤC HỒ SƠ HOÀN THÀNH CÔNG TRÌNH (HSHT):\n\n"
                "# Danh Mục Hồ Sơ Hoàn Thành Công Trình Dân Dụng Cấp I (NĐ 06/2021/NĐ-CP & NĐ 35/2023/NĐ-CP)\n\n"
                "## Cấu Trúc Cây Thư Mục Phân Cấp (Directory Hierarchy):\n"
                "```text\n"
                "📁 01_Giai_Doan_Chuan_Bi_Dau_Tu/\n"
                "   ├── 📄 01.01_Quyet_Dinh_Phe_Duyet_Du_An.pdf\n"
                "   ├── 📄 01.02_Giay_Phep_Xay_Dung.pdf\n"
                "   └── 📄 01.03_Tham_Duyet_Thiet_Ke_PCCC.pdf\n"
                "📁 02_Giai_Doan_Thi_Cong_Xay_Dung/\n"
                "   ├── 📁 02.01_Ho_So_Quan_Ly_Chat_Luong_Vat_Lieu/\n"
                "   ├── 📁 02.02_Bien_Ban_Nghiem_Thu_Cong_Viec_Xay_Dung/\n"
                "   └── 📁 02.03_Ket_Qua_Thi_Nghiem_Kiem_Dinh/\n"
                "📁 03_Giai_Doan_Nghiem_Thu_Ban_Giao/\n"
                "   ├── 📄 03.01_Ban_Ve_Hoan_Cong_Cac_Bo_Mon.pdf\n"
                "   ├── 📄 03.02_Van_Ban_Chap_Thuan_Nghiem_Thu_PCCC.pdf\n"
                "   └── 📄 03.03_Bien_Ban_Nghiem_Thu_Hoan_Thanh_Cong_Trinh.pdf\n"
                "```\n\n"
                "## Checklist Kiểm Soát Hồ Sơ Nghiệm Thu & Toàn Vẹn SHA-256:\n"
                "- [x] 100% biên bản nghiệm thu tuân thủ biểu mẫu Phụ lục Nghị định 06/2021/NĐ-CP.\n"
                "- [x] Bản vẽ hoàn công có đầy đủ chữ ký, dấu xác nhận của Nhà thầu thi công và Tư vấn giám sát.\n"
                "- [x] Mã băm SHA-256 kiểm toán toàn bộ kho lưu trữ hồ sơ: `7f8e9d0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e`.\n\n"
                "Chi tiết danh mục hồ sơ xem tại [references/](references/)."
            )

        if (
            "verbatim" in prompt_l
            or "adr-0059" in prompt_l
            or "giả định" in prompt_l
            or "acquisition" in prompt_l
        ):
            return ctx.wrap_response(
                "RÀO CHẮN BẢO VỆ TÍNH CHÂN THỰC VĂN BẢN PHÁP LÝ (ADR-0059 MANDATORY ACQUISITION INVARIANT):\n\n"
                "1. Các Hành Vi Bị Nghiêm Cấm Tuyệt Đối (Anti-Synthetic Invariant):\n"
                "- CẤM TUYỆT ĐỐI việc tự ý sáng tác, sinh điều khoản giả định (synthetic/mock clauses) hoặc dự đoán nội dung quy phạm pháp luật khi thiếu văn bản nguồn.\n"
                "- CẤM trích dẫn các căn cứ pháp lý không có trong kho lưu trữ đã qua xác thực mật mã.\n\n"
                "2. Quy Trình Xử Lý Bắt Buộc Khi Thiếu Văn Bản (Mandatory Acquisition Loop):\n"
                "- Bước 1: Dừng ngay lập tức quá trình lập luận và phát cảnh báo thiếu văn bản nguồn chính thức.\n"
                "- Bước 2: Tự động kích hoạt module thu thập (TVPLCrawler) để cào tệp gốc từ Công báo hoặc Thư Viện Pháp Luật.\n"
                "- Bước 3: Nếu nguồn cào không khả dụng, phát thông báo yêu cầu người dùng (Human-in-the-Loop) cung cấp tệp PDF/DOCX chính thức.\n"
                "- Bước 4: Thực hiện đóng dấu băm SHA-256 provenance stamping: `3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b` trước khi đưa vào kho tri thức OKF v2.4.\n\n"
                "Chi tiết điều lệ xem tại [references/](references/)."
            )

        return ctx.wrap_response(
            "Thực thi quy chuẩn kỹ thuật pháp lý và công cụ quy phạm pháp luật:\n"
            "- Quản lý phiên crawler TVPL VIP và cơ chế retry khi nghẽn mạng.\n"
            "- Chuẩn hóa OKF v2.4 và bảo đảm tính nguyên văn verbatim grounding với mã băm SHA-256 provenance stamping theo ADR-0059: `c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2`.\n"
            "- So khớp diff văn bản hợp nhất VBHN và quản lý cây thư mục hồ sơ hoàn thành HSHT NĐ 06/2021.\n"
            "Chi tiết tham chiếu xem tại [references/](references/).\n"
        )
