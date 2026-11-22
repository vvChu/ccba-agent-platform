# CCBA Brand Identity v3.4 — Bộ màu DOCX Báo cáo Đánh giá Kỹ thuật

Dùng mặc định cho các Báo cáo Đánh giá Kỹ thuật DOCX phát hành dưới danh nghĩa `IBST - CCBA` (tích hợp trực tiếp trong Deep Seam `ccba_ooxml:CCBADocxTheme` và `TechnicalReportBuilder`, font thống nhất `Segoe UI`).

---

## 1. Bảng màu chính (CCBA Brand v3.4)

| Vai trò | Mã HEX | Mô tả & Phạm vi áp dụng |
| :--- | :---: | :--- |
| Dark Blue Primary | `#363883` | Tiêu đề bìa, Heading 1, Header bảng, tiêu đề ô ký, Slogan *Smarter* |
| IBST Red | `#DA251C` | Đường gạch Header trang bìa, Category badge, KPI/Callout cảnh báo, Slogan *Faster* |
| BIM Bright Blue | `#0093DD` | **Chỉ dùng** cho đường viền nhấn trên (`top border`) thẻ KPI và chữ *Better* trong slogan 3 màu |
| Primary UI Blue | `#005A9C` | Heading 2, chữ số liệu KPI trên nền sáng (`#F8FAFC`/`#FFFFFF`), dấu bullet, Callout thông tin |
| Body Text Dark | `#1A202C` | Văn bản nội dung chính (độ tương phản cao, dịu mắt hơn đen thuần `#000000`) |
| Secondary / Muted | `#595959` | Phụ đề tiếng Anh nghiêng, chạy trang Header/Footer, chú thích `(Ký, ghi rõ họ tên)` |
| Light Surface | `#F8FAFC` | Nền cột nhãn Document Control Matrix, nền thẻ KPI |
| Info Callout Tint | `#F0F6FC` | Nền khối Callout thông tin / Đề xuất của Tư vấn |
| Section Tint | `#E8EAF6` | Nền tím xanh nhẹ (tùy chọn cho banner nhóm lớn) |
| Zebra Row Alt | `#F9FAFB` | Nền hàng lẻ trong bảng dữ liệu (hàng chẵn `#FFFFFF`) |
| Grid Border Light | `#CBD5E1` | Đường kẻ mảnh đồng bộ bảng dữ liệu, ma trận kiểm soát và thẻ KPI |

---

## 2. Quy tắc Tương phản WCAG 2.1 AA/AAA (Bắt buộc)

Màu xanh sáng thương hiệu **`#0093DD`** trên nền trắng `#FFFFFF` hoặc `#F8FAFC` chỉ đạt tỷ lệ tương phản khoảng **3.4:1** (không đạt chuẩn **WCAG 2.1 AA** tối thiểu `4.5:1` cho văn bản thường và số liệu). Do đó:

| Ngữ cảnh sử dụng | Mã HEX cho phép | Tỷ lệ tương phản xấp xỉ | Quy tắc áp dụng |
| :--- | :---: | :---: | :--- |
| Chữ body, tiêu đề phụ, chỉ số KPI trên `#FFFFFF` / `#F8FAFC` | `#005A9C` | `~6.8:1` / `~6.4:1` (Đạt AA/AAA) | **Bắt buộc thay thế** `#0093DD` cho mọi chữ số liệu / nội dung trên nền sáng |
| Văn bản chính trên nền trắng / xám rất nhạt | `#1A202C` | `~16.0:1` (Đạt AAA) | Dùng mặc định cho style `Normal` và ô dữ liệu bảng |
| Chữ trắng trên nền `#363883` (Header bảng) | `#FFFFFF` | `~9.9:1` (Đạt AAA) | Dùng cho tiêu đề cột bảng (`<w:tblHeader/>`) |
| Viền nhấn trên thẻ KPI & chữ slogan *Better* (`Bold`) | `#0093DD` | Điểm nhấn đồ họa | Không dùng `#0093DD` cho chữ body hoặc số liệu metric |

> **Cưỡng chế trong mã nguồn:** `CCBADocxTheme` và `wcag_safe_text_hex()` tại `ccba_ooxml.docx._report_theme` tự động ánh xạ màu chữ metric `#0093DD` $\to$ `#005A9C` trong khi vẫn giữ `#0093DD` ở đường viền trên (`sz="18"`).

---

## 3. Áp dụng cho Heading & Slogan Footer

| Thành phần | Mã HEX | Quy chuẩn trình bày |
| :--- | :---: | :--- |
| **Trang bìa — Tiêu đề chính** | `#363883` | `Segoe UI`, Bold `19pt`, căn giữa, kèm `title_en` nghiêng `12pt` `#595959` |
| **Heading 1 (Mục chính)** | `#363883` | `Segoe UI`, Bold `12.5pt`, `keep_with_next = True` |
| **Heading 2 (Tiểu mục)** | `#005A9C` | `Segoe UI`, Bold `10.5pt`, `keep_with_next = True` |
| **Slogan Footer 3 màu** | `#363883` · `#DA251C` · `#0093DD` | `Smarter` (`#363883`) `Faster` (`#DA251C`) `Better` (`#0093DD`) kèm `IBST - CCBA` và `Trang PAGE / NUMPAGES` |

---

## 4. Áp dụng cho Bảng & Callout / Traffic Light

| Thành phần | Viền / Accent | Nền Fill | Màu chữ tiêu đề / nội dung |
| :--- | :---: | :---: | :--- |
| **Header bảng dữ liệu** | `#CBD5E1` | `#363883` | `#FFFFFF` (Bold `9pt`, `<w:tblHeader/>`) |
| **Zebra bảng dữ liệu** | `#CBD5E1` | `#F9FAFB` (lẻ) / `#FFFFFF` (chẵn) | `#1A202C` (`9pt`, `<w:cantSplit/>`) |
| **Callout Info / Recommendation** | `#005A9C` / `#363883` (`sz="24"`) | `#F0F6FC` | Tiêu đề `#005A9C`/`#363883`, nội dung `#1A202C` |
| **Callout Cảnh báo (`warn`)** | `#B45309` (`sz="24"`) | `#FEF9E7` | Tiêu đề `#B45309`, nội dung `#1A202C` |
| **Callout Nguy hiểm (`danger`)** | `#DA251C` (`sz="24"`) | `#FEF2F2` | Tiêu đề `#DA251C`, nội dung `#1A202C` |
| **Callout Đạt chuẩn (`ok`)** | `#15803D` (`sz="24"`) | `#ECFDF5` | Tiêu đề `#15803D`, nội dung `#1A202C` |
