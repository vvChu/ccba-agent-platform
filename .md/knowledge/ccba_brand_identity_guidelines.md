# 🎨 CCBA Brand Identity Guidelines (Quy Chuẩn Nhận Diện Thương Hiệu CCBA - ver 3.4)

> **Tổ chức**: Trung tâm Tư vấn & Ứng dụng BIM trong Xây dựng (CCBA) — Viện Khoa học Công nghệ Xây dựng (IBST)  
> **Sứ mệnh**: *"Thúc đẩy cách mạng số và ứng dụng BIM để nâng tầm ngành xây dựng Việt Nam."*  
> **Tầm nhìn**: *"Thúc đẩy các dự án xây dựng đạt chất lượng vượt trội và hiệu suất tối ưu thông qua giải pháp BIM và nền tảng số tích hợp, xây dựng một hệ sinh thái hợp tác vì hiệu quả và bền vững trong ngành."*  
> **Slogan**: **`Smarter Faster Better`** (*"Thông minh hơn - Nhanh hơn - Tốt hơn"*)  
> **Quy trình chuẩn**: **`CCBA WAY`** (Giai đoạn 1: Sales/BD $\rightarrow$ Giai đoạn 2: Delivery $\rightarrow$ Giai đoạn 3: Closure/Review)

---

## 1. Hệ Thống Màu Sắc & Thông Số Kỹ Thuật (Color Matrix & Guardrails)

### 1.1. Màu sắc Cốt lõi (Core Brand Colors)

| Tên màu | HEX (Digital) | RGB (Screen) | CMYK (In ấn Offset/Laser) | Pantone Spot | Ý nghĩa & Gắn kết CCBA WAY |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Đỏ IBST** (*IBST Red*) | `#DA251C` | `(218, 37, 28)` | `C:0 / M:98 / Y:100 / K:5` | **Pantone 485 C** | Năng lượng, Tiên phong. Giai đoạn 1 (BD/Sales). Tinh thần **TỐI ƯU & ĐỔI MỚI**. Kết cấu (`STR`). |
| **Xanh Đậm CCBA** (*Dark Blue*) | `#363883` | `(54, 56, 131)` | `C:95 / M:90 / Y:20 / K:10` | **Pantone 2745 C**| Tin cậy, Chuyên nghiệp. Giai đoạn 2 (Delivery). Tinh thần **CHUYÊN NGHIỆP & TIN CẬY**. Kiến trúc (`ARC`). |
| **Xanh Dương Sáng** (*BIM Bright Blue*) | `#0093DD` | `(0, 147, 221)` | `C:80 / M:30 / Y:0 / K:0` | **Pantone 299 C** | Công nghệ BIM, Hợp tác. Giai đoạn 3 (Closure/Review). Tinh thần **ĐỔI MỚI & TRÁCH NHIỆM**. Cơ điện (`MEP`). |
| **Xanh Dương TT** (*Primary UI Blue*) | `#005A9C` | `(0, 90, 156)` | `C:98 / M:65 / Y:15 / K:2` | **Pantone 7686 C**| Cân bằng, công nghệ. Tiêu đề phụ, đường viền bảng. |

### 1.2. Rào chắn Tương phản Bắt buộc (WCAG 2.1 AA/AAA Enforced Text-Background Matrix)

Để chống lỗi "chữ vô hình" hoặc chữ mờ nhạt gây nhức mắt:

| Màu Nền (Background) | Mã HEX | Màu Chữ Bắt Buộc (Enforced Text Color) | Contrast Ratio | Chuẩn WCAG |
| :--- | :--- | :--- | :--- | :--- |
| **Xanh Đậm CCBA** | `#363883` | **Trắng Tuyệt đối (`#FFFFFF`)** | `10.24 : 1` | **AAA Pass** |
| **Xanh Dương Sáng** | `#0093DD` | **Xanh Đen / Navy Tối (`#0B1B3D` hoặc `#002B49`)** | `5.85 : 1` | **AA Pass** |
| **Đỏ IBST** | `#DA251C` | **Trắng Tuyệt đối (`#FFFFFF`) (Weight $\ge 500$)** | `4.95 : 1` | **AA Pass** |
| **Vàng Chú Ý** | `#F2C811` | **Đen Than (`#1A202C`) hoặc Slate Dark (`#2C3E50`)** | `6.86 : 1` | **AAA Pass** |
| **Nền Thẻ / Sáng** | `#F8FAFC` | **Slate Dark (`#2C3E50`)** | `11.80 : 1` | **AAA Pass** |

> 🚫 **CẤM TUYỆT ĐỐI**:
> - Không bao giờ đặt chữ `#2C3E50` lên nền `#363883` (tương phản 1.08:1 - chữ vô hình).
> - Không bao giờ đặt chữ Trắng `#FFFFFF` lên nền Vàng `#F2C811` (tương phản 1.61:1 - trượt chuẩn).
> - Không dùng chữ Trắng nhỏ cho nền `#0093DD` (chỉ đạt 3.38:1 - không đủ độ tương phản cho body text).

### 1.3. Cơ chế Tiếp cận Thị giác Đa kênh (Multi-modal Accessibility Encoding)
- **Quy chuẩn Chống Mù màu (CVD)**: Không bao giờ dùng màu sắc đơn độc để chỉ thị trạng thái hoặc bộ môn.
- **Trạng thái QA/QC**: Bắt buộc kết hợp **[Icon] + [Text Badge] + [Color]**:
  - `[PASS]` / `✓` trên nền Xanh lá `#28A745` (chữ trắng)
  - `[FAIL]` / `✗` trên nền Đỏ IBST `#DA251C` (chữ trắng)
  - `[WARN]` / `⚠` trên nền Vàng `#F2C811` (chữ đen `#1A202C`)
- **Phân hệ Bộ môn BIM**: Bổ sung ký hiệu viết tắt:
  - `[ARC]` Kiến trúc (`#363883`)
  - `[STR]` Kết cấu (`#DA251C`)
  - `[MEP]` Cơ điện (`#0093DD`)

---

## 2. Hệ Thống Typography & Chiến Lược Phân Tầng 2 Lớp

### 2.1. Phân tầng Môi trường Thực thi (Digital vs Universal Office)

1. **Lớp 1 — Môi trường Web, Dashboard & PDF Xuất bản (Digital Native)**:
   - **Primary Font**: **Inter** (Google Fonts — Regular 400, Medium 500, SemiBold 600, Bold 700).
   - **Cover / Event Heading**: **Montserrat** (Bold 700 / ExtraBold 800).
   - **Formal / Trích dẫn**: **Lora** (Italic 400i).

2. **Lớp 2 — Môi trường Tài liệu Office Giao nộp (PowerPoint `.pptx`, Word `.docx`)**:
   - Để ngăn ngừa 100% rủi ro lệch khung chữ (Metric Incompatibility) và tràn slide khi mở trên máy tính đối tác chưa cài font Inter:
     - **Tiêu đề (Headings)**: **`Segoe UI Semibold` / `Segoe UI Bold`**
     - **Thân bài (Body Text)**: **`Segoe UI Regular`**
     - **Trích dẫn**: **`Georgia Italic`**
   - *Lưu ý*: Khi bắt buộc dùng `Inter` trong file `.pptx`, cấu hình tùy chọn **Embed TrueType Fonts** trong file PowerPoint trước khi phát hành.

---

## 3. Hệ Thống Logo Thích Ứng 3 Cấp Độ (Responsive Logo Family)

1. **Master Logo ($\ge 128\text{px}$)**:
   - Biểu tượng Tòa nhà IBST (Đỏ) + Quỹ đạo elip (Xanh Đậm) + Chữ BIM (Xanh Đậm / Xanh Dương).
   - Ứng dụng: Bìa báo cáo in ấn, Backdrop hội thảo, Slide Cover mở đầu.
2. **Compact Header Mark ($48\text{px} - 120\text{px}$)**:
   - Khối tòa nhà IBST nét đậm + Chữ BIM (loại bỏ các nét elip mảnh và chữ IBST li ti).
   - Ứng dụng: Header slide nội dung, Navbar web, App Header.
3. **Micro Favicon ($16\text{px} - 32\text{px}$)**:
   - Khối lập phương 3D Isometric đơn khối mang 3 màu cốt lõi với chữ **C** trung tâm, nét tối thiểu 2px chống nhòe sub-pixel.
   - Ứng dụng: Favicon trình duyệt, App Avatar, Breadcrumb icon.

---

## 4. Slogan Chuẩn & Phối Màu 3 Từ

- **Khẩu hiệu**: **`Smarter Faster Better`** (*"Thông minh hơn - Nhanh hơn - Tốt hơn"*).
- **Quy tắc phối màu từng từ**:
  - `Smarter` $\rightarrow$ **`#363883`** (Xanh Đậm CCBA — Tri thức, giải pháp thông minh, AI)
  - `Faster` $\rightarrow$ **`#DA251C`** (Đỏ IBST — Tốc độ, quy trình tinh gọn, tự động hóa)
  - `Better` $\rightarrow$ **`#0093DD`** (Xanh Dương Sáng — Chất lượng vượt trội, đổi mới bền vững)
- **Vị trí**: Chân trang slide thuyết trình (footer), bìa báo cáo kỹ thuật, chữ ký email.
