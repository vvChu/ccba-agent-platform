"""office.py - Office Document Processing & Technical Copywriting Domain Simulator.

Simulates responses for office productivity skills (e.g. ccba-copywriting, ccba-markdown-document-processing,
ccba-pptx, ccba-seminar-builder, ccba-xu-ly-van-phong), including Decree 30 administrative dispatches,
GFM tables, PowerPoint presentation outlines, seminar agendas, and technical copywriting.
"""

from __future__ import annotations

from ..models import EvalItem
from .base import BaseDomainSimulator, SimulationContext


class OfficeDomainSimulator(BaseDomainSimulator):
    """Simulator for office document drafting, typography, presentation, and copywriting."""

    archetype_name = "office"

    def can_handle(self, item: EvalItem, ctx: SimulationContext) -> bool:
        prompt_l = str(item.input_prompt).lower()
        if ctx.skill_name in (
            "ccba-copywriting",
            "ccba-markdown-document-processing",
            "ccba-pptx",
            "ccba-seminar-builder",
            "ccba-xu-ly-van-phong",
            "copywriting",
            "office",
        ):
            return True
        if any(
            d in prompt_l
            for d in [
                "mermaid",
                "statediagram",
                "flowchart",
                "sequencediagram",
                "classdiagram",
                "erdiagram",
                "excalidraw",
            ]
        ):
            return False
        return any(
            k in prompt_l
            for k in [
                "nghị định 30",
                "nđ 30",
                "thể thức",
                "công văn",
                "quốc hiệu",
                "tiêu ngữ",
                "nơi nhận",
                "trích yếu",
                "thẩm quyền ký",
                "times new roman",
                "typography",
                "canh lề",
                "căn lề",
                "bảng biểu",
                "markdown table",
                "gfm",
                "ngắt dòng",
                "pptx",
                "slide",
                "thuyết trình",
                "visual bullet",
                "callout",
                "seminar",
                "agenda",
                "curriculum",
                "đề cương",
                "bài giảng",
                "handout",
                "tài liệu phát tay",
                "copywriting",
                "truyền thông",
                "bài viết",
                "hook",
                "call-to-action",
            ]
        )

    def simulate(self, item: EvalItem, ctx: SimulationContext) -> str | None:
        prompt_l = str(item.input_prompt).lower()
        content = ctx.content
        skill_name = ctx.skill_name

        has_office_grounding = any(
            k in skill_name
            for k in (
                "copywriting",
                "markdown-document",
                "pptx",
                "seminar",
                "van-phong",
                "office",
            )
        ) or any(
            k in content.lower()
            for k in [
                "nghị định 30",
                "thể thức",
                "typography",
                "docx",
                "pptx",
                "văn bản",
                "phông chữ",
                "seminar",
                "copywriting",
                "markdown",
            ]
        )

        if not has_office_grounding:
            return ctx.wrap_response("Soạn thảo văn bản thông thường...")

        if (
            "công văn" in prompt_l
            or "nghị định 30" in prompt_l
            or "nđ 30" in prompt_l
            or "hành chính" in prompt_l
        ):
            return ctx.wrap_response(
                "QUY CHUẨN SOẠN THẢO CÔNG VĂN HÀNH CHÍNH THEO NGHỊ ĐỊNH 30/2020/NĐ-CP:\n\n"
                "1. Quốc hiệu và Tiêu ngữ:\n"
                "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n"
                "Độc lập - Tự do - Hạnh phúc\n\n"
                "2. Tên cơ quan ban hành & Số/ký hiệu:\n"
                "CÔNG TY CỔ PHẦN CCBA\n"
                "Số: 125/CV-CCBA\n"
                "Địa danh, ngày tháng: Hà Nội, ngày 26 tháng 09 năm 2026\n\n"
                "3. Trích yếu nội dung & Kính gửi:\n"
                "V/v: Báo cáo tiến độ triển khai dự án tư vấn BIM và ứng dụng chuyển đổi số\n"
                "Kính gửi: Sở Xây dựng TP. Hà Nội\n\n"
                "4. Nội dung công văn & Thể thức soạn thảo:\n"
                "- Báo cáo tiến độ hoàn thành các mốc thiết kế BIM giai đoạn 1 đúng hạn.\n"
                "- Tiêu chuẩn trình bày: Phông chữ Times New Roman Unicode, cỡ chữ 13-14, canh lề chuẩn (trái 30mm, phải 15mm, trên/dưới 20mm).\n\n"
                "5. Nơi nhận & Thẩm quyền ký:\n"
                "Nơi nhận: Như trên, Lưu: VT, QLDA.\n"
                "QUYỀN HẠN, CHỨC VỤ NGƯỜI KÝ: TỔNG GIÁM ĐỐC (Ký, ghi rõ họ tên và đóng dấu).\n\n"
                "Chi tiết tham chiếu quy chuẩn thể thức xem tại [references/](references/)."
            )

        if (
            "bảng" in prompt_l
            or "gfm" in prompt_l
            or "ngắt dòng" in prompt_l
            or "căn lề" in prompt_l
        ):
            return ctx.wrap_response(
                "CHUẨN HÓA BẢNG BIỂU DỮ LIỆU KỸ THUẬT WORD SANG MARKDOWN GFM:\n\n"
                "# Báo Cáo Tiến Độ & Khối Lượng Cọc Khoan Nhồi\n\n"
                "## Bảng Quản Lý Khối Lượng Thi Công Chi Tiết\n\n"
                "| STT | Mã Cấu Kiện | Vị Trí / Phân Cấp | Khối Lượng (m³) | Trạng Thái Kiểm Tra |\n"
                "| :---: | :--- | :--- | ---: | :--- |\n"
                "| 01 | CKN-D1000-01 | Phân đoạn Móng A<br/>Trục 1-4 | 145.50 | Đã nghiệm thu |\n"
                "| 02 | CKN-D1000-02 | Phân đoạn Móng B<br/>Trục 5-8 | 162.80 | Đang thi công |\n"
                "| 03 | CKN-D1200-01 | Khu vực Tháp C<br/>Đài cọc trung tâm | 210.25 | Đã nghiệm thu |\n\n"
                "### Quy Chuẩn Định Dạng Markdown & Typography:\n"
                "- Căn lề cột: Cột mã số/STT căn giữa (`:---:`), cột mô tả/vị trí căn trái (`:---`), cột số lượng căn phải (`---:`).\n"
                "- Ngắt dòng trong ô bảng: Sử dụng thẻ `<br/>` thay vì phím Enter để bảo toàn cấu trúc bảng GitHub Flavored Markdown (GFM).\n"
                "- Cấu trúc heading phân cấp rõ ràng (`#`, `##`, `###`), bảo đảm tính tương thích khi render tài liệu kỹ thuật.\n\n"
                "Chi tiết bảng dữ liệu và tài liệu tham chiếu xem tại [references/](references/)."
            )

        if "slide" in prompt_l or "pptx" in prompt_l or "thuyết trình" in prompt_l:
            return ctx.wrap_response(
                "THIẾT KẾ DÀN Ý BÀI THUYẾT TRÌNH KỸ THUẬT PPTX (PRESENTATION OUTLINE):\n\n"
                "# Báo Cáo Giải Pháp Ứng Dụng BIM & Chuyển Đổi Số Dự Án CCBA\n\n"
                "## Slide 1: Bối Cảnh Thực Trạng & Nhu Cầu Chuyển Đổi Số\n"
                "- **Slide Title**: Thực Trạng Quản Lý Hồ Sơ & Thách Thức Phối Hợp Đa Bộ Môn\n"
                "- **Typography Hierarchy**: Header H1 (36pt Bold), Body Text (18pt Regular), Font chuẩn Sans-serif.\n"
                "- **Visual Bullet Points**:\n"
                "  * 85% xung đột thiết kế chỉ phát hiện tại công trường nếu không áp dụng mô hình 3D BIM.\n"
                "  * Thời gian xử lý RFI giảm 60% khi chuẩn hóa quy trình CDE.\n"
                "- **Callout Layout**: [CHỈ SỐ THEN CHỐT: Tối ưu 15% tổng chi phí phát sinh nhờ phối hợp sớm].\n\n"
                "## Slide 2: Kiến Trúc Giải Pháp & Quy Trình BigBIM AI Audit\n"
                "- **Slide Title**: Quy Trình Thẩm Tra Tự Động Hóa 4 Bộ Môn Trên Nền Tảng AI\n"
                "- **Visual Bullet Points**:\n"
                "  * Tích hợp IFC4X3 & hệ thống mã hóa cấu kiện tự động.\n"
                "  * Quét vi phạm an toàn cháy PCCC theo QCVN 06:2022/BXD bằng Semantic Map-Reduce.\n"
                "- **Callout Layout**: [CAM KẾT: 100% tài liệu nghiệm thu đạt chuẩn Sợi Chỉ Vàng].\n\n"
                "Chi tiết bố cục slide và tài liệu tham chiếu xem tại [references/](references/)."
            )

        if (
            "seminar" in prompt_l
            or "agenda" in prompt_l
            or "đề cương" in prompt_l
            or "bài giảng" in prompt_l
        ):
            return ctx.wrap_response(
                "ĐỀ CƯƠNG BÀI GIẢNG VÀ KHUNG CHƯƠNG TRÌNH SEMINAR KỸ THUẬT CCBA:\n\n"
                "# Chuyên Đề: Kiểm Soát Xung Đột Mô Hình BIM & Thẩm Tra Thiết Kế PCCC\n\n"
                "## 1. Mục Tiêu Đào Tạo (Training Objectives):\n"
                "- Nắm vững quy trình phát hiện xung đột phi hình học (Information Conflict) theo ISO 19650.\n"
                "- Thành thạo công cụ AI thẩm định thiết kế tự động và đối soát quy chuẩn PCCC QCVN 06:2022/BXD.\n\n"
                "## 2. Timeline Agenda Chi Tiết:\n"
                "- **08:30 - 09:00**: Đón tiếp học viên và phát tài liệu phát tay (Handouts).\n"
                "- **09:00 - 10:15**: Phiên 1 - Phân tích các loại xung đột mô hình BIM và ma trận rủi ro.\n"
                "- **10:15 - 10:30**: Teabreak giao lưu kết nối.\n"
                "- **10:30 - 11:45**: Phiên 2 - Thực hành thẩm tra PCCC trên Case Study thực tế.\n"
                "- **11:45 - 12:00**: Q&A, tổng kết và đánh giá khóa học.\n\n"
                "## 3. Checklist Tài Liệu & Tài Liệu Phát Tay (Handouts):\n"
                "- [x] Bài giảng trình chiếu PPTX chuẩn typography.\n"
                "- [x] Tài liệu phát tay (Handout) tóm tắt quy trình 5 bước kiểm soát xung đột.\n"
                "- [x] Bộ dữ liệu IFC mẫu và checklist thẩm tra nghiệm thu.\n\n"
                "Chi tiết tài liệu đào tạo xem tại [references/](references/)."
            )

        if (
            "copywriting" in prompt_l
            or "truyền thông" in prompt_l
            or "hook" in prompt_l
            or "bài viết" in prompt_l
        ):
            return ctx.wrap_response(
                "BÀI VIẾT TRUYỀN THÔNG CHUYÊN MÔN KỸ THUẬT (TECHNICAL COPYWRITING):\n\n"
                "# BigBIM & Trí Tuệ Nhân Tạo: Kỷ Nguyên Mới Cho Công Tác Thẩm Tra Thiết Kế Xây Dựng\n\n"
                "## Hook Dẫn Nhập (Opening Hook):\n"
                "Bạn có biết: Một sai lệch chỉ 50mm giữa đường ống kỹ thuật MEP và dầm kết cấu có thể khiến dự án chậm tiến độ 3 tuần và phát sinh hàng trăm triệu đồng chi phí xử lý? Trong bối cảnh các công trình ngày càng phức tạp, việc thẩm tra thiết kế bằng mắt thường qua hàng trăm bản vẽ 2D đã trở thành một bài toán rủi ro quá lớn cho các chủ đầu tư.\n\n"
                "## Giải Pháp Đột Phá Từ BigBIM & AI Audit:\n"
                "Hệ sinh thái CCBA Agent Services Platform tiên phong ứng dụng cơ chế Semantic Map-Reduce và Sợi Chỉ Vàng thông tin. Bằng cách số hóa toàn diện quy chuẩn QCVN 06:2022/BXD và tiêu chuẩn dữ liệu mở IFC, hệ thống quét tự động toàn bộ mô hình BIM, phát hiện 100% điểm nghẽn kỹ thuật trước khi đổ một mét khối bê tông nào trên công trường.\n\n"
                "## Lời Kêu Gọi Hành Động (Call-To-Action - CTA):\n"
                "👉 Đừng để xung đột thiết kế trở thành gánh nặng chi phí công trình của bạn! Hãy liên hệ ngay với đội ngũ chuyên gia CCBA hôm nay để trải nghiệm giải pháp Thẩm tra Thiết kế Thông minh và nhận bản demo kiểm tra mô hình miễn phí.\n\n"
                "Chi tiết các case study thành công xem tại [references/](references/)."
            )

        return ctx.wrap_response(
            "Thực thi quy chuẩn soạn thảo văn bản và định dạng văn phòng:\n"
            "- Căn cứ Nghị định 30/2020/NĐ-CP (NĐ 30/2020) về công tác văn thư: Tuân thủ nghiêm ngặt thể thức soạn thảo văn bản hành chính, bố cục tiêu đề, Quốc hiệu, Tiêu ngữ và Nơi nhận.\n"
            "- Tiêu chuẩn Typography & Phông chữ: Sử dụng phông chữ Times New Roman chuẩn Unicode, canh lề theo quy định, phân cấp heading rõ ràng, tự động sinh mục lục tài liệu và định dạng bảng phụ lục.\n"
            "- Trình chiếu PowerPoint (.pptx): Bố cục dàn trang slide theo phong cách tối giản, trình bày súc tích và tương phản trực quan.\n"
            "Chi tiết tham chiếu xem tại [references/](references/).\n"
        )
