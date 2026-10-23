---
proposal_id: "2026-10-23_standardize_rfi_template"
type: "skills"
name: "standardize-rfi-template"
status: "proposed"
priority: "Cao"
proposed_by_project: "ccba-legal-knowledge"
proposed_by_archetype: "knowledge_corpus"
proposed_date: "2026-10-23"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Tất cả Spokes"
graduated_to: ""
supersedes_spoke_docs: []
---

# RFC Proposal: Chuẩn Hóa Biểu Mẫu Phiếu Yêu Cầu Cung Cấp Thông Tin Kỹ Thuật (RFI) Cho IBST / CCBA

- **Tác giả đề xuất:** Antigravity (Pair Architect & Builder) & Kỹ sư Vũ Văn Chủ (Giám đốc Trung tâm CCBA)
- **Ngày lập:** 2026-10-23
- **Trạng thái:** Đang đề xuất (Proposed)
- **Phán quyết Thẩm định:** **`APPROVE`** từ Grok 4.7 (`req-spoke-standardize-rfi-template-002`, 0 blocking conditions)
- **Căn cứ pháp lý nền tảng:** [ADR-0045](../../docs/adr/0045-hub-proposal-ingestion-governance.md), [ADR-0061](../../docs/adr/0061-platform-aware-kiss-seam-contracts.md), Tiêu chuẩn ISO 19650, Hợp đồng Mẫu FIDIC, Thể chế Thương hiệu CCBA.

---

### 1. Bối cảnh & Động lực Thực tế tại Spoke (Context & Real-world Motivation)

Trong quá trình triển khai các dự án tư vấn BIM và PCCC công nghiệp quy mô lớn (điển hình như Dự án Mở rộng Nhà máy Panasonic - PAPVN và Nhà máy Thiết bị Y tế Terumo Bến Cát), Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng (CCBA) thuộc Viện Khoa học Công nghệ Xây dựng (IBST) liên tục phải phát hành các Phiếu Yêu cầu Cung cấp Thông tin Kỹ thuật (RFI / Technical Request for Information).

1. **Nỗi đau thực tế (Pain Point):**
   - Sự nhập nhằng giữa văn bản hành chính nhà nước (Nghị định 30/2020/NĐ-CP) và biểu mẫu quản lý kỹ thuật dự án quốc tế (ISO 19650 / FIDIC). Việc chèn Quốc hiệu - Tiêu ngữ và dòng cơ quan chủ quản 3 tầng nấc ("BỘ XÂY DỰNG") khiến form giao tiếp dự án trở nên nặng tính quan liêu hành chính, không phù hợp với thông lệ làm việc cùng các Chủ đầu tư, Tổng thầu FDI (Nhật Bản, Châu Âu).
   - Sai số hình học OpenXML: Các bảng dữ liệu bị tràn lề, co giãn tùy tiện do thiếu định mức Content Width ($9071\text{ DXA}$), ô bảng gãy ngang dòng giữa 2 trang (thiếu `cantSplit`), bảng dài mất tiêu đề trang sau (thiếu `tblHeader`), khối chữ ký bị mồ côi (orphaned signature) đẩy sang trang trắng.
   - Trùng lặp danh xưng ngữ nghĩa (Tautology): Các cách viết lỗi thời như "Viện IBST" hoặc "Trung tâm CCBA" làm giảm tính chuyên nghiệp của một Viện nghiên cứu đầu ngành.

2. **Quá trình ươm tạo & Kiểm định tại Spoke:**
   - Hoàn thiện bộ đặc tả Tier 4 Canonical Template (`docx-ky-thuat-rfi.md`) và Mô hình dữ liệu trung gian chuẩn hóa YAML IR (`rfi_template_schema.yaml`).
   - Xuất bản thành công bản mẫu DOCX (OpenXML strict) và PDF thực tế cho dự án Panasonic.
   - Hoàn thành chu trình thẩm định Level-2 Peer Exchange (ADR-0063/ADR-0064) với **Grok 4.7 xhigh**, đạt kết quả phán quyết **`APPROVE` tuyệt đối** (0 blocking conditions, rủi ro tối thiểu).

3. **Giá trị khi phổ biến lên Hub:**
   - Chuẩn hóa năng lực phát hành biểu mẫu trao đổi kỹ thuật cho toàn bộ mạng lưới Spoke của CCBA Agent Platform.
   - Bất kỳ kỹ sư hoặc Agent nào trong hệ sinh thái đều có thể sinh ngay file RFI đẹp mắt, chính xác về hình học, chuẩn nhận diện thương hiệu Formal Navy chỉ bằng một lệnh đơn giản.

---

### 2. Đánh Giá Giá Trị × Rủi Ro × KISS (Evaluation Matrix)

| Tiêu Chí | Đánh Giá Cụ Thể | Ghi Chú / Bằng Chứng |
| :--- | :--- | :--- |
| **Giá trị Nghiệp vụ (Value)** | **Rất cao** | Chuẩn hóa thể thức giao tiếp kỹ thuật chuẩn ISO 19650 cho toàn bộ các dự án FDI của CCBA |
| **Độ Phức tạp (Complexity)** | **Thấp (KISS)** | Tách bạch 100% dữ liệu (YAML IR) khỏi giao diện (OpenXML). Không tạo thêm daemon hay engine mới |
| **Rủi ro Rò rỉ (Risk)** | **0%** | Dữ liệu nhân sự PII được che chắn qua slot biến theo ADR-0059. Đã kiểm tra qua `check_spoke_leakage.py` |
| **Bảo tồn Kiến trúc (Charter)** | **Tuyệt đối** | Đạt 6 điều kiện phong tỏa COND-01 đến COND-06 của Grok. Giữ nguyên 15 cổng CI quy chuẩn của Spoke |

---

### 3. Thiết Kế Chi Tiết & Tích Hợp Vào Hub (Technical Specification)

1. **Vị trí tích hợp tại Hub Monorepo:**
   - Đặc tả mẫu Tier 4: `.agents/skills/ccba-xu-ly-van-phong/templates/docx-ky-thuat-rfi.md`
   - Mô hình dữ liệu YAML IR: `.agents/skills/ccba-xu-ly-van-phong/templates/rfi_template_schema.yaml`
   - Cập nhật Master Skill: `.agents/skills/ccba-xu-ly-van-phong/SKILL.md` (bổ sung tra cứu Composable Table và quy tắc thương hiệu `RULE-6.1`)

2. **Các Bất Biến Kỹ Thuật Được Thiết Lập:**
   - **Hình học nền tảng khóa cứng & Động cơ Cân bằng Thích ứng (COND-01 & COND-06):** Khổ A4, lề trái $3.0\text{ cm}$ (`1701 DXA`), lề phải/trên/dưới $2.0\text{ cm}$ (`1134 DXA`). Vùng nội dung bất biến $\mathbf{CONTENT\_WIDTH = 9071\text{ DXA}}$. Lưới 4 cột cân bằng thích ứng (Adaptive Content-Aware Balancing) kết hợp cưỡng chế khóa cứng OpenXML (`tblLayout="fixed"` và `tblGrid`) để bảo đảm 100% Visual Parity giữa Microsoft Word và PDF Engine (LibreOffice): Cột 1 ($650 - 750\text{ DXA}$), Cột 2 ($4121 - 4300\text{ DXA}$ — mở rộng tối đa diện tích cho đề xuất tư vấn), Cột 3 ($1500 - 1700\text{ DXA}$), Cột 4 ($2450 - 2600\text{ DXA}$). Khối ký 2 ô: $4535 + 4536 = 9071\text{ DXA}$. Đệm ô: $57\text{ DXA}$ dọc, $85\text{ DXA}$ ngang.
   - **Bảng màu Formal Navy (COND-02):** Header `#1F3864`, Text `#FFFFFF`, Zebra `#F2F2F2` / `#FFFFFF`, Accent `#C00000`, Secondary `#595959`, Body `#202020`.
   - **Bảo toàn OpenXML (COND-06):** $100\%$ thẻ `<w:cantSplit/>` cho từng dòng, thẻ `<w:tblHeader/>` cho dòng tiêu đề.
   - **Quy chuẩn danh xưng bất biến (RULE-6.1):** Viện (`Viện`, `Viện KHCN`, `IBST`), Trung tâm (`Trung tâm`, `Trung tâm BIM`, `CCBA`). Đơn vị gửi: `IBST - CCBA` (CẤM dùng slash `IBST / CCBA` để tránh hiểu lầm liên danh). Bỏ Quốc hiệu NĐ 30 và "Bộ Xây dựng" khỏi Header kỹ thuật.
   - **Khối tư vấn dẫn dắt:** Bắt buộc có mục "💡 Đề xuất của Tư vấn (Consultant's Recommendation)" dưới mỗi câu hỏi.
