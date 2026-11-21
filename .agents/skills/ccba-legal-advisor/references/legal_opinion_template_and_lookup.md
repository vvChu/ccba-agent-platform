# Legal Advisor — Tri-Surface 1812/QĐ-BXD Lookup & Opinion Template Reference

Tài liệu tham chiếu Level 3 cho `ccba-legal-advisor`, lưu trữ đầy đủ bộ từ điển Quyết định `1812/QĐ-BXD`, 4 Khung Mẫu Tương Tác Động và mẫu chuẩn "Phiếu Giải Đáp Pháp Lý CCBA" 4 phần.

## 1. Bốn Khung Mẫu Tương Tác Động (Dynamic Interaction Archetypes)

1. **Mẫu 1 — Thẩm định tham số:** Kiểm tra thông số kỹ thuật cụ thể của công trình (Bậc chịu lửa, số thang, tải trọng...).
2. **Mẫu 2 — Đối chiếu chuyển tiếp:** So sánh quy định cũ và mới để bảo vệ quyền lợi không hồi tố.
3. **Mẫu 3 — Bảng Ma trận Checklist:** Xuất bảng đối soát đa cột phục vụ báo cáo thẩm tra kỹ thuật.
4. **Mẫu 4 — Bóc tách Biểu mẫu & Thủ tục:** Hướng dẫn hồ sơ cấp phép xây dựng hoặc nghiệm thu hoàn công.

## 2. Giao Thức Ngôn Ngữ Chung Ba Bề Mặt (Tri-Surface Ubiquitous Language — QĐ 1812/QĐ-BXD)

- **Bề mặt Giao tiếp Người dùng (Human / Statutory Surface):** Khi đặt câu hỏi làm rõ (`A/B/C`), sử dụng nguyên văn danh mục chuẩn hóa của Bộ Xây dựng (`1812/QĐ-BXD`):
  - **5 nguồn vốn:** `VONDAUTUCONG - Vốn đầu tư công`, `VONNHANUOC - Vốn nhà nước ngoài đầu tư công`, `PPP - Dự án PPP`, `KHAC - Vốn khác`, `HONHOP - Vốn hỗn hợp`.
  - **4 kịch bản thủ tục công trình:**
    - `II.A`: Dự án đầu tư xây dựng.
    - `II.B`: Công trình xây dựng yêu cầu thẩm định thiết kế xây dựng triển khai sau thiết kế cơ sở tại cơ quan chuyên môn về xây dựng.
    - `II.C`: Công trình xây dựng không yêu cầu thẩm định thiết kế xây dựng triển khai sau thiết kế cơ sở tại cơ quan chuyên môn về xây dựng, chỉ yêu cầu cấp giấy phép xây dựng.
    - `II.D`: Công trình xây dựng không yêu cầu lập dự án đầu tư xây dựng, chỉ yêu cầu cấp giấy phép xây dựng.
  - **5 cấp công trình:** `DACBIET - Cấp đặc biệt`, `I - Cấp I`, `II - Cấp II`, `III - Cấp III`, `IV - Cấp IV`.
  - **Địa giới hành chính 2 cấp:** Tỉnh/Thành phố + Phường/Xã/Đặc khu theo Quyết định `19/2025/QĐ-TTg`.
- **Bề mặt Quản trị Nội bộ (CCBA WAY / ADR-0046 Surface):** Phân định 3 tầng trách nhiệm trong Phiếu Giao Việc (QCTK 2815):
  - **Chủ trì Hợp đồng** (`CHU_TRI_HOP_DONG_PM` — cấp hợp đồng).
  - **Chủ nhiệm theo hoạt động xây dựng** (`vaiTroChuTri` mã `1..9` theo Mục II.C.11 QĐ 1812/QĐ-BXD: `1- Chủ nhiệm lập quy hoạch`, `3- Chủ nhiệm khảo sát xây dựng`, `4- Chủ nhiệm thiết kế`, `6- Chủ nhiệm thẩm tra thiết kế`, `8- Giám sát trưởng của đơn vị giám sát`, `9- Chỉ huy trưởng của nhà thầu thi công xây dựng công trình`).
  - **Chủ trì Bộ môn** (`CHU_TRI_BO_MON` — cấp bộ môn chuyên ngành: `2- Chủ trì bộ môn thiết kế`, `5- Chủ trì bộ môn thiết kế (thiết kế xây dựng)`, `7- Chủ trì thẩm tra các bộ môn thiết kế`).
- **Bề mặt Nội bộ Agent (Agent Internal State):** Ghi nhận song song các khóa `camelCase` (`nguonVonDauTu`, `nhomDuAn`, `loaiDuAn`, `capCongTrinh`, `section_namespace`, `maTinh`, `maXa`, `vaiTroChuTri`) trong Mục 1 của Phiếu Giải Đáp Pháp Lý để liên thông CSDL Quốc gia và `IDOPBridge`.

## 3. Cấu Trúc 4 Phần "Phiếu Giải Đáp Pháp Lý CCBA"

```markdown
# 🏛️ PHIẾU GIẢI ĐÁP PHÁP LÝ & QUY CHUẨN XÂY DỰNG (CCBA LEGAL OPINION)

## 1. 📌 Tóm Tắt Bối Cảnh & Vấn Đề Pháp Lý
- Loại công trình & Nhóm công năng: [Ví dụ: Khách sạn 12 tầng, F1.2]
- Thông số kỹ thuật cốt lõi: [Chiều cao PCCC, diện tích sàn, cấp công trình...]
- Yêu cầu pháp lý cần giải quyết: [Câu hỏi trọng tâm]

## 2. ⚡ Kết Luận Pháp Lý Trọng Tâm (Executive Summary)
- [Khẳng định dứt khoát: BẮT BUỘC / ĐƯỢC MIỄN / ĐẠT CHUẨN / CẦN ĐIỀU CHỈNH]
- Thẩm quyền giải quyết (Sở Xây dựng / Cảnh sát PCCC / Chủ đầu tư tự duyệt).

## 3. 🔍 Căn Cứ Pháp Lý & Ma Trận Đối Chiếu Chi Tiết
| STT | Phân Hệ / Tiêu Chí | Quy Định Pháp Luật Bắt Buộc | Điều Khoản / Bảng Trích Dẫn | Vết Xác Thực Nguồn Gốc (Provenance) | Đánh Giá Áp Dụng |
| :---: | :--- | :--- | :--- | :--- | :---: |
| 1 | ... | ... | [Điều ... Luật Xây dựng 2025](...) | `pdf_sha256: [hash]` (nguon: `legal_docs/.../metadata.yaml`) | 🟢 Đạt / 🔴 Chưa đạt |
| 2 | ... | ... | [Bảng ... QCVN 06:2022](...) | `pdf_sha256: [hash]` (nguon: `legal_docs/.../clauses.json`) | ... |

## 4. ⚠️ Khuyến Nghị Kỹ Thuật & Cảnh Báo Rủi Ro (Actionable Advice)
- **Hồ sơ / Biểu mẫu cần chuẩn bị:** [Đính kèm biểu mẫu từ templates/]
- **Rủi ro cần phòng tránh:** [Lưu ý về PCCC, điều khoản chuyển tiếp, chế tài phạt...]
```
