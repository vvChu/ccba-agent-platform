# Mẫu Biểu: Phiếu Yêu Cầu Cung Cấp Thông Tin Kỹ Thuật (RFI)

> **Mô tả**: Biểu mẫu Quản lý Kỹ thuật Dự án (Project Technical Management Form) chuẩn hóa theo ISO 19650 và thông lệ tư vấn quốc tế cho các dự án công nghiệp, dân dụng và hạ tầng.  
> **Cấp độ kiến trúc**: Tier 4 Canonical Engineering Template  
> **Áp dụng**: Lệnh `/ccba-xu-ly-van-phong --template rfi-ky-thuat` kết hợp Deep Seam `ccba-ooxml` / `WordFormFiller`.

---

## 🏛️ Quy Chuẩn Danh Xưng & Thương Hiệu (RULE-6.1)

1. **Cơ quan cấp trên**: Viện Khoa học công nghệ xây dựng.
   - Danh xưng viết tắt chuẩn: **`Viện`**, **`Viện KHCN`**, hoặc **`IBST`**.
   - *CẤM TUYỆT ĐỐI:* Dùng `Viện IBST` (lặp từ tautology).
2. **Đơn vị trực thuộc**: Trung tâm Tư vấn và Ứng dụng BIM trong xây dựng.
   - Danh xưng viết tắt chuẩn: **`Trung tâm`**, **`Trung tâm BIM`**, hoặc **`CCBA`**.
   - *CẤM TUYỆT ĐỐI:* Dùng `Trung tâm CCBA` (lặp từ tautology).
3. **Đơn vị gửi (From / Consultant) & Metadata**:
   - Viết chuẩn: **`IBST - CCBA`** hoặc **`IBST - Trung tâm BIM`** (Cơ quan chủ quản trước $\to$ Đơn vị trực thuộc thực hiện sau).
   - *CẤM DÙNG:* `IBST / CCBA` (dấu slash `/` dễ bị đối tác quốc tế hiểu lầm là Liên danh nhà thầu/tư vấn Joint Venture hoặc quan hệ thay thế And/Or).
4. **Khối tư vấn dẫn dắt trong câu văn**:
   - Viết chuẩn: **`💡 Đề xuất của Tư vấn`** (hoặc `Đề xuất của Tư vấn (IBST)`), tạo văn phong tự nhiên, mềm mại, tôn trọng tiếng Việt và giữ vững vị thế tư vấn trực tiếp.
5. **Phân cấp Header**:
   - **Tối đa 2 cấp**: Cấp Viện (dòng 1) và Cấp Trung tâm (dòng 2).
   - **Tuyệt đối KHÔNG đưa "BỘ XÂY DỰNG"** vào Header của biểu mẫu kỹ thuật dự án.
   - **Không chèn đuôi ngoặc đơn `(IBST)` và `(CCBA)`** vào dòng tiếng Việt chính thức. Tên tiếng Anh viết tắt được thể hiện qua Logo hoặc dòng phụ đề song ngữ trang nhã (`Secondary #595959`).

---

## 📐 Thông Số Hình Học Khóa Cứng (Geometry Invariants — COND-01)

- **Khổ giấy**: A4 ($210 \times 297\text{ mm}$ / $11906 \times 16838\text{ DXA}$).
- **Lề trang (Margins)**:
  - Top = $2.0\text{ cm}$ (`1134 DXA`)
  - Bottom = $2.0\text{ cm}$ (`1134 DXA`)
  - Left = $3.0\text{ cm}$ (`1701 DXA`) — *Đóng gáy hồ sơ dự án*
  - Right = $2.0\text{ cm}$ (`1134 DXA`)
- **Chiều rộng nội dung (CONTENT_WIDTH)**:
  $$\mathbf{CONTENT\_WIDTH = 11906 - 1701 - 1134 = 9071\text{ DXA}}$$
- **Động cơ Cân bằng Cột Thích ứng & Bất biến OpenXML Fixed Grid (Adaptive Balancing & Fixed Invariant)**:
  - Bảng RFI phải đảm bảo **Visual Parity 100% giữa Microsoft Word và PDF Engine (LibreOffice)** bằng cách tiêm bắt buộc `<w:tblLayout w:val="fixed"/>` và `<w:tblGrid><w:gridCol w:w="..."/>` trong OpenXML.
  - Phân bổ 4 cột linh hoạt theo mật độ nội dung (Content-Aware Density):
    - Cột 1 (STT / Mã số tham chiếu): **`650 - 750 DXA`** (~7.2 - 8.2%)
    - Cột 2 (Nội dung Yêu cầu & Đề xuất của Tư vấn): **`4121 - 4300 DXA`** (~45.4 - 47.4%) — *Mở rộng +21%...26% diện tích, giúp trải dài khối đề xuất và giảm ~40% số trang in*.
    - Cột 3 (Định dạng & Tiêu chuẩn giao nộp CDE): **`1500 - 1700 DXA`** (~16.5 - 18.7%) — *Tối ưu vừa khít checkbox và nhãn định dạng, khử hoàn toàn khoảng trắng dư thừa*.
    - Cột 4 (Phản hồi của Đối tác / Hồ sơ đính kèm): **`2450 - 2600 DXA`** (~27.0 - 28.7%) — *Gọn gàng, đủ rộng cho checkbox và ghi chú viết tay*.
    - **Tổng cộng bất biến**: $\mathbf{\sum W_i = 9071\text{ DXA}}$ ($100.0\%$).
- **Khối ký 2 ô (Sign-off Block Grid)**:
  - Cột 1 (Đại diện Tư vấn IBST / CCBA): **`4535 DXA`**
  - Cột 2 (Đại diện Khách hàng / Đối tác): **`4536 DXA`**
  - **Tổng cộng**: $\mathbf{4535 + 4536 = 9071\text{ DXA}}$.
- **Đệm ô (Cell Padding)**:
  - Top / Bottom = $0.1\text{ cm}$ (`57 DXA`)
  - Left / Right = $0.15\text{ cm}$ (`85 DXA`)

---

## 🎨 Bảng Màu Nhận Diện Formal Navy (COND-02)

| Vai trò | Mã HEX | Áp dụng trên RFI Form |
| :--- | :---: | :--- |
| **Primary** | `#1F3864` | Nền Header bảng, Heading 2, Viền khung chính |
| **Accent** | `#C00000` | Ngày hạn phản hồi (Due Date), Mức độ Khẩn / Urgent, Heading 1 |
| **Secondary** | `#595959` | Dòng phụ đề tiếng Anh, Chú thích kỹ thuật, Metadata phụ |
| **Body Text** | `#202020` | Văn bản nội dung (đen nhẹ, chống chói mắt) |
| **Zebra Lẻ** | `#F2F2F2` | Nền xen kẽ cho các dòng dữ liệu lẻ |
| **Zebra Chẵn** | `#FFFFFF` | Nền trắng thuần cho các dòng dữ liệu chẵn |
| **Border / Line** | `#BFBFBF` | Đường kẻ mảnh phân cách bảng và viền ô |

---

## ⚙️ Quy Tắc OpenXML & Chống Tách Trang (COND-06)

1. **Bảo toàn dòng bảng**: Toàn bộ thẻ `<w:tr>` trong mọi bảng bắt buộc phải có `<w:cantSplit/>`.
2. **Lặp tiêu đề trang sau**: Thẻ `<w:tr>` đầu tiên của bảng dữ liệu bắt buộc chứa `<w:tblHeader/>`.
3. **Khối ký nguyên tử**: Khối chữ ký được thiết kế thành một bảng 2 ô độc lập có `<w:cantSplit/>`. Nếu không gian cuối trang không đủ cho chiều cao khối ký, renderer tự động chèn ngắt trang (`pageBreakBefore`) để chống hiện tượng mồ côi chữ ký sang trang mới.
4. **Bảo vệ dữ liệu cá nhân (PII)**: Tên, chức danh, số điện thoại, email của nhân sự được định nghĩa dạng slot biến và nạp theo Cascading Vault ADR-0059.

---

## 📋 Cấu Trúc Khung Mẫu (Wireframe Schema)

```text
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ┌──────────────────────────────────────────────────┐                   ┌─────────────────────────────┐ │
│ │ VIỆN KHOA HỌC CÔNG NGHỆ XÂY DỰNG                 │   PHIẾU YÊU CẦU   │ Mã RFI: {{MA_RFI}}          │ │
│ │ Institute for Building Science and Technology    │   CUNG CẤP        │ Ngày lập: {{NGAY_PHAT_HANH}}│ │
│ │                                                  │ THÔNG TIN KỸ THUẬT│ Hạn trả lời: {{HAN_TRA_LOI}}│ │
│ │ TRUNG TÂM TƯ VẤN VÀ ỨNG DỤNG BIM TRONG XÂY DỰNG │    REQUEST FOR    │ Mức độ:   {{MUC_DO_UU_TIEN}} │ │
│ │ Center for Consulting and BIM Application (CCBA) │    INFORMATION    │                             │ │
│ └──────────────────────────────────────────────────┘                   └─────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ THÔNG TIN KIỂM SOÁT DỰ ÁN (PROJECT CONTROL MATRIX) - 9071 DXA                                          │
├───────────────────────────────┬────────────────────────────────┬───────────────────────────────────────┤
│ Dự án: {{TEN_DU_AN}}          │ Gửi đến (To): {{BEN_NHAN}}     │ Đơn vị gửi (From): IBST - CCBA        │
│ Gói thầu: {{TEN_GOI_THAU}}    │ Người nhận: {{NGUOI_NHAN}}     │ Điều phối viên (PIC): {{DIEU_PHOI_VIEN│
├───────────────────────────────┼────────────────────────────────┼───────────────────────────────────────┤
│ Bộ môn: {{BO_MON}}            │ Phân khu / Tầng: {{VI_TRI}}    │ Ảnh hưởng Chi phí:  {{ANH_HUONG_CHI_PH│
│ Mã mô hình / CDE: {{MA_CDE}}  │ Trục lưới: {{TRUC_LUOI}}       │ Ảnh hưởng Tiến độ:  {{ANH_HUONG_TIEN_D│
├───────────────────────────────┴────────────────────────────────┴───────────────────────────────────────┤
│ I. MỤC ĐÍCH & Ý NGHĨA KỸ THUẬT (PURPOSE & STATUTORY OBJECTIVE)                                         │
│    {{MUC_DICH_KY_THUAT}}                                                                              │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ II. DANH MỤC DỮ LIỆU YÊU CẦU & ĐỀ XUẤT CỦA TƯ VẤN (ADAPTIVE 4-COLUMN GRID - 9071 DXA)                  │
├───────┬─────────────────────────────────┬───────────────────────────────┬──────────────────────────────┤
│ STT   │ Nội dung Yêu cầu & Đề xuất Tư vấn│ Định dạng & Giao nộp CDE      │ Phản hồi & Đính kèm Đối tác  │
│ (650) │ (4121 DXA - Mở rộng tối ưu)     │ (1700 DXA - Vừa khít)         │ (2600 DXA - Gọn gàng)        │
├───────┼─────────────────────────────────┼───────────────────────────────┼──────────────────────────────┤
│ 1.1   │ [Tên hạng mục]                  │ [ ] File CAD (.dwg)           │ [ ] Đã đính kèm: ...         │
│       │ • Yêu cầu chi tiết...           │ [ ] File BIM (.rvt / .ifc)    │ [ ] Cung cấp tại buổi họp    │
│       │ • 💡 Đề xuất của Tư vấn:        │ [ ] File PDF ký số            │ [ ] Chưa có / Nhờ tư vấn     │
│       │   (Consultant's Recommendation) │ [ ] Khảo sát thực địa         │     khảo sát đề xuất phương án│
├───────┴─────────────────────────────────┴───────────────────────────────┴──────────────────────────────┤
│ III. XÁC NHẬN & ĐÓNG PHIẾU (SIGN-OFF & PROTOCOL - 2 Ô CHỐNG TÁCH TRANG - 9071 DXA)                    │
├───────────────────────────────────────────────┬────────────────────────────────────────────────────────┤
│          ĐẠI DIỆN TƯ VẤN (IBST - CCBA)        │             ĐẠI DIỆN KHÁCH HÀNG / ĐỐI TÁC              │
│                                               │                                                        │
│ Người lập phiếu (Author / Cấp 1A):            │ Người tiếp nhận & Phản hồi (Recipient):                │
│ {{NGUOI_LAP_PHIEU}}                           │ {{NGUOI_TIEP_NHAN}}                                    │
│                                               │                                                        │
│ Chủ trì / Lãnh đạo Phòng (Lead / Cấp 2-3):    │ Ngày xác nhận: ..... / ..... / 2026                    │
│ {{LANH_DAO_PHONG}}                            │ Trạng thái RFI: [ ] Đóng (Closed)   [ ] Cần làm rõ thêm│
└───────────────────────────────────────────────┴────────────────────────────────────────────────────────┘
```
