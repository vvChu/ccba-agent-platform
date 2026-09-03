# 🏛️ Báo Cáo Nghiên Cứu & Khung Thiết Kế: Phong Cách Trình Chiếu Tối Giản Cao Cấp (Minimalist & Swiss Design) Cho CCBA

> **Mã chuyên đề**: `CCBA-RD-RES-2026-004`  
> **Chủ thể nghiên cứu**: Dual-Agent Adversarial Research (Minimalist Design Specialist $\times$ Usability & Engineering Challenger)  
> **Quy chuẩn đối chiếu**: Swiss International Typographic Style, Dieter Rams "Less but Better", Edward Tufte Data-Dense Design, WCAG 2.1 AAA, ISO 19650, QCVN/TCVN Xây Dựng.  
> **Tài liệu tham chiếu thực tế**: [`.md/seminars/2026/demo_seminar_nd175.md`](file:///d:/GitHubProjects/ccba-agent-platform/.md/seminars/2026/demo_seminar_nd175.md) & [`.md/seminars/2026/demo_seminar_nd175.pptx`](file:///d:/GitHubProjects/ccba-agent-platform/.md/seminars/2026/demo_seminar_nd175.pptx).

---

## 1. TỔNG QUAN & ĐẶT VẤN ĐỀ (EXECUTIVE SUMMARY & PROBLEM STATEMENT)

Trong tư vấn xây dựng và thẩm tra kỹ thuật BIM của CCBA (Viện IBST), một bài thuyết trình slide phục vụ đồng thời 2 nhóm đối tượng có kỳ vọng trái ngược:
1. **Lãnh đạo cấp cao (Chủ đầu tư, Viện trưởng, Giám đốc QLDA)**: Cần nắm bắt thông điệp cốt lõi và số liệu KPI trong vòng **5-10 giây** lướt nhìn.
2. **Hội đồng Thẩm định & Kỹ sư trưởng**: Cần căn cứ pháp lý chính xác (QCVN, TCVN, ISO 19650), vị trí cấu kiện cụ thể (Trục Grid, Tầng, IFC GUID) và số liệu va chạm chi tiết.

### Điểm Nghẽn của Thiết Kế Trình Chiếu Truyền Thống:
- **Visual Clutter (Rác thị giác)**: Lạm dụng các đường viền hộp kín, đổ bóng 3D, nền dải màu gradient dày đặc khiến mắt người xem bị phân tán.
- **Thiếu Phân Cấp Typography Cực Hạn**: Các con số đắt giá (`60%`, `111 va chạm`, `1.5 ngày`, `24 lỗi nghiêm trọng`) bị "chìm" lẫn trong đoạn văn bản hoặc ô bảng.
- **Bố Cục Cứng Nhắc Đối Xứng 50/50**: Tạo cảm giác đơn điệu, không nhấn mạnh được sự vượt trội của phương pháp luận **CCBA WAY**.

### Mục Tiêu Nghiên Cứu:
Xây dựng một hệ thống thiết kế **"Tối giản nhưng Sâu sắc & Chuẩn xác" (Minimalist yet High-Density & Rigorous)**, kết hợp tinh hoa của **Phong cách Thụy Sĩ (Swiss Modernist / Scandinavian / Linear Design)** với **Kỷ luật Dữ liệu Kỹ thuật IBST**.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│               TRIẾT LÝ: TỐI GIẢN KỸ THUẬT (ENGINEERING MINIMALISM) CCBA                │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ "Tối giản trong Báo cáo Kỹ thuật không phải là hiển thị ít thông tin,                 │
│  mà là triệt tiêu tối đa Nhiễu thị giác (Visual Noise / Chartjunk)                    │
│  để dành 100% sự tập trung cho Dữ liệu có cấu trúc cao (Structured High-Density Data)."│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. PHÂN TÍCH ADVERSARIAL: 3 BẪY THIẾT KẾ & HỆ THỐNG RÀO CHẮN (GUARDRAILS)

Cuộc đối thoại phản biện giữa **Chuyên gia Tối giản (Proponent)** và **Chuyên gia Trình chiếu Kỹ thuật (Challenger)** đã xác lập 3 bẫy nguy cơ và các rào chắn cưỡng chế:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                 MA TRẬN NGUY CƠ & RÀO CHẮN BẢO VỆ CHẤT LƯỢNG TRÌNH CHIẾU               │
├───────────────────────┬───────────────────────────────┬────────────────────────────────┤
│ Bẫy Thiết Kế Cực Đoan │ Nguy Cơ Thực Địa              │ Rào Chắn Kỹ Thuật (Guardrail)  │
├───────────────────────┼───────────────────────────────┼────────────────────────────────┤
│ 1. Information        │ Cắt gọt viện dẫn quy chuẩn    │ 🏷 Kiến trúc 3 tầng (3-Tier):   │
│    Starvation         │ để giữ slide "sạch" $\rightarrow$   │ Header Kết luận $\rightarrow$ Bento Data│
│    (Đói thông tin)    │ Báo cáo mất tính pháp lý      │ Matrix $\rightarrow$ Footer Metadata   │
├───────────────────────┼───────────────────────────────┼────────────────────────────────┤
│ 2. Projector Washout  │ Dùng chữ xám nhạt (#5A6872)   │ 🖨️ Chuẩn tương phản WCAG AAA:  │
│    (Lóa máy chiếu)    │ và viền mờ $\rightarrow$ Bị tán xạ  │ Chữ Đen Than (#1E293B) $\ge 10:1$│
│                       │ biến mất trên máy chiếu 2000lm│ Viền thẻ rõ nét 1.0pt (#CBD5E1)│
├───────────────────────┼───────────────────────────────┼────────────────────────────────┤
│ 3. Context Fragment   │ Xé bảng 8 cột thành 6 slides  │ 📊 Bento Box Matrix 1 Slide:   │
│    (Vỡ bối cảnh)      │ $\rightarrow$ Gây "Slide Fatigue", mất│ Phân cụm hàng, Zebra Striping, │
│                       │ tương quan đa bộ môn BIM      │ kèm Companion QR Code Deep Dive│
└───────────────────────┴───────────────────────────────┴────────────────────────────────┘
```

### Chi Tiết Rào Chắn 1: Kiến Trúc 3 Tầng Thị Giác (3-Tier Slide Hierarchy)
- **Tầng 1 - Header Band (5-10 giây)**: Kết luận định lượng đanh thép (ví dụ: `15/18 Cửa Thoát Nạn Tầng Hầm B1 Không Đạt EI 60`).
- **Tầng 2 - Bento Data Matrix (15-30 giây)**: Ma trận số liệu có cấu trúc cao, thẻ phân loại, bảng Swiss Table không viền dọc.
- **Tầng 3 - Traceability Metadata Stamp (Truy vết)**: Dải chân trang cố định ghi nhận căn cứ pháp lý (`Bảng 1 QCVN 06:2022/BXD`), mã định danh mô hình (`IFC GUID: 2xO$r025v89xL12`) và phiên bản tài liệu.

### Chi Tiết Rào Chắn 2: Tiêu Chuẩn Hiển Thị Máy Chiếu Hiện Trường
- **Chữ thân bài (Body Text)**: Cấm dùng xám nhạt; bắt buộc dùng **Đen Than Slate (`#1E293B`)** hoặc **Navy Tối (`#0B1B3D`)** trên nền Trắng `#FFFFFF` / Xám nhạt `#F8FAFC`.
- **Kích thước chữ tối thiểu**: Tiêu đề Display `36-40pt`, Tiêu đề phân đoạn `18-20pt`, Thân bài & bảng biểu `13-15pt Medium` (không dùng font dưới `11pt` trong mọi hoàn cảnh).
- **Mã hóa Đa kênh (Multi-modal Status)**: Luôn kết hợp [Màu sắc + Icon ký tự + Text Badge] (ví dụ: `[FAIL ✗]` nền đỏ, `[PASS ✓]` nền xanh lá) để người mù màu hoặc máy chiếu lệch màu vẫn nhận biết chính xác 100%.

---

## 3. KHUNG THIẾT KẾ TỐI GIẢN CAO CẤP: NGUYÊN TẮC 85-10-5

```
+-------------------------------------------------------------------------------+
|  [TAG/EYEBROW] 11pt Bold (Capsule Nền Mờ Navy / Cyan)                          |
|  TIÊU ĐỀ DISPLAY 38pt SEMIBOLD (Màu Than Chì #0F172A, Tracking Gọn)          |
|  Phụ đề diễn giải 15pt Regular (#475569)                                      |
|                                                                               |
|  +-----------------------------------+  +----------------------------------+  |
|  | CỘT CHÍNH HERO (60% Width)         |  | CỘT THAM CHIẾU (38% Width)       |  |
|  |  ⚡ HERO NUMBER: 60% (56pt Cyan)   |  |  Nền Xám Nhạt #F8FAFC            |  |
|  |  Rút ngắn thời gian thẩm tra       |  |  Viền Mảnh 1.0pt #CBD5E1         |  |
|  +-----------------------------------+  +----------------------------------+  |
|                                                                               |
|  Negative Space (Khoảng thở thanh thoát)                   CCBA Technical 2026|
+-------------------------------------------------------------------------------+
```

### 1. Phân Bổ Không Gian & Màu Sắc Phẫu Thuật (Surgical Color Rule 85-10-5)
- **85% Canvas**: Nền Trắng tinh khiết (`#FFFFFF`) kết hợp các mảng thẻ xám cực nhạt (`#F8FAFC`).
- **10% Neutral Structure**: Chữ than chì tối (`#0F172A`, `#1E293B`) và đường phân cách hairline mỏng `0.75pt` (`#E2E8F0` / `#CBD5E1`).
- **5% Surgical Accents (Chỉ xuất hiện tại điểm kích thích thị giác)**:
  - **CCBA Navy (`#363883`)**: Kicker capsule, Primary Hero Stat, viền mốc quan trọng.
  - **Digital Cyan (`#0093DD`)**: Điểm nhấn AI, tốc độ, nền tảng số, icon dot 6px.
  - **IBST Red (`#DA251C`)**: Điểm nóng rủi ro kỹ thuật, cảnh báo nghiêm trọng `[FAIL ✗]`.

### 2. Số Liệu Điểm Nhấn (KPI Hero Numbers 48-60pt)
Thay vì nhét số liệu vào câu văn dài, các con số đột phá được tách thành các **Hero Number Blocks** kích thước lớn (`48-60pt Bold`), đặt ngay phía trên nhãn giải nghĩa ngắn gọn (`12-13pt`).

### 3. Bố Cục Bento Grid Bất Đối Xứng (Asymmetric 60/40 & 55/42)
- **Tỷ lệ 60/40 (Golden Split)**: Cột giải pháp CCBA WAY chiếm 60% với thẻ nổi bật; cột truyền thống chiếm 40% đóng vai trò đối chiếu.
- **Bento Matrix Hotspots (55/42)**: 1 Thẻ Hero lớn (chiếm 55% bề ngang) đặt cạnh 2 thẻ phụ xếp dọc (chiếm 42% bề ngang) tạo nhịp điệu thị giác hiện đại.

### 4. Bảng Dữ Liệu Kiểu Thụy Sĩ (Swiss Borderless Table)
- **Triệt tiêu 100% đường kẻ dọc** và khung bao quanh.
- **Chỉ giữ đường kẻ ngang phân cách siêu mảnh `0.75pt`** màu `#E2E8F0`.
- **Hàng tổng kết**: Dùng đường line `1.5pt` màu Navy `#363883`, in đậm toàn bộ số liệu tổng hợp.

---

## 4. QUY CHUẨN 5 ARCHETYPES CHO BỘ SLIDE DEMO KỸ THUẬT

Dưới đây là thiết kế kiến trúc chi tiết cho 5 slide mẫu trong [`.md/seminars/2026/demo_seminar_nd175.md`](file:///d:/GitHubProjects/ccba-agent-platform/.md/seminars/2026/demo_seminar_nd175.md):

---

### Archetype 1: Cover Slide (Minimalist Swiss Hero)
*Áp dụng: Slide 1 - Trang Bìa Hội Thảo*

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [TRUNG TÂM TƯ VẤN & ỨNG DỤNG BIM CCBA — VIỆN IBST] (Capsule 11pt Bold)                 │
│                                                                                        │
│ ỨNG DỤNG BIM & NỀN TẢNG SỐ                                                             │
│ TRONG THẨM TRA THIẾT KẾ                                                                │
│ (38pt SemiBold, Màu #0F172A, Dãn dòng 1.15)                                            │
│                                                                                        │
│ Phổ biến Nghị định 175/2024/NĐ-CP & Triển khai Quy trình CCBA WAY                      │
│ (16pt Regular, Màu #475569)                                                            │
│ ──────────────────────── (Thanh Bar 3 Màu 3pt)                                        │
│ 👤 TS. Nguyễn Văn A — Chuyên gia Trưởng BIM            📅 Ngày: 02/09/2026              │
│ [LOGO IBST BIM] (Góc phải dưới, cân đối, sắc nét)                                     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Archetype 2: Policy Roadmap (Asymmetric 60/40 Split)
*Áp dụng: Slide 2 - Lộ trình NĐ 175/2024*

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [PHÁP LÝ] Lộ Trình Áp Dụng BIM Bắt Buộc Theo NĐ 175/2024                               │
│ Căn cứ quy định mới nhất của Chính phủ về quản lý dự án đầu tư xây dựng                │
│                                                                                        │
│ ┌──────────────────────────────────────┐  ┌──────────────────────────────────────────┐ │
│ │ CỘT NỘI DUNG CHÍNH (60% W - Card)    │  │ CỘT KPI TRỌNG TÂM (36% W)                │ │
│ │                                      │  │                                          │ │
│ │ 📌 Giai đoạn 2025 - 2026             │  │ MỐC THỜI HẠN BẮT BUỘC                    │ │
│ │ Bắt buộc công trình Cấp I và Đặc     │  │ 2025 – 2026                              │ │
│ │ biệt sử dụng vốn Đầu tư công         │  │ (Hero Number: 44pt Bold Navy #363883)    │ │
│ │                                      │  │                                          │ │
│ │ 📌 Tiêu chuẩn dữ liệu: IFC4 / IFC4X3 │  │ CHUẨN DỮ LIỆU BÀN GIAO                   │ │
│ │ 📌 Trách nhiệm: Kiểm toán xung đột   │  │ IFC4X3 / CDE (ISO 19650)                 │ │
│ └──────────────────────────────────────┘  └──────────────────────────────────────────┘ │
│ 🏷 Căn cứ: Điều 6 & Phụ lục IX Nghị định 175/2024/NĐ-CP | CCBA Technical System        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Archetype 3: Comparison & Benchmark (Hero Contrast Split)
*Áp dụng: Slide 3 - So Sánh 2D Truyền Thống vs CCBA WAY AI Audit*

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [SO SÁNH] Đột Phá Năng Suất: 2D Truyền Thống vs CCBA WAY AI Audit                     │
│                                                                                        │
│ ┌────────────────────────────────────┐  ┌────────────────────────────────────────────┐ │
│ │ 2D TRUYỀN THỐNG (38% W)            │  │ CCBA WAY & AI AUDIT (58% W - HERO CARD)    │ │
│ │ (Nền Xám #F8FAFC, Viền #CBD5E1)    │  │ (Viền Xanh Cyan 2.5pt, Nền Trắng Nổi Bật)  │ │
│ │                                    │  │                                            │ │
│ │ • Đọc bản vẽ rời rạc từng bộ môn   │  │  ⚡ RÚT NGẮN THỜI GIAN THẨM TRA             │ │
│ │ • Xung đột phát hiện muộn tại CT   │  │  60% (Hero Metric 56pt Bold Cyan #0093DD)  │ │
│ │ • Bóc tách thủ công nhiều tuần     │  │                                            │ │
│ │ • Rủi ro chi phí phát sinh cao     │  │  • Tích hợp mô hình Quad-View Vision       │ │
│ │                                    │  │  • Tự động phát hiện 100% va chạm          │ │
│ │ ⏳ Thời gian xử lý: 7–10 ngày       │  │  • Báo cáo Heatmap tương tác trực quan     │ │
│ └────────────────────────────────────┘  └────────────────────────────────────────────┘ │
│ ────────────────────────────────────────────────────────────────────────────────────── │
│ CCBA Consulting Platform 2026                   Smarter (#363883) Faster (#DA251C) Better (#0093DD)│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Archetype 4: Swiss Clean Table & KPI Dashboard
*Áp dụng: Slide 4 - Thống Kê Xung Đột Mô Hình*

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [BẢNG SỐ LIỆU] Tổng Hợp Kết Quả Thẩm Tra Xung Đột Mô Hình                             │
│                                                                                        │
│ ┌──────────────────────┐  ┌──────────────────────┐  ┌────────────────────────────────┐ │
│ │ TỔNG SỐ XUNG ĐỘT     │  │ VA CHẠM NGHIÊM TRỌNG │  │ THỜI GIAN XỬ LÝ TB             │ │
│ │ 111                  │  │ 24                   │  │ 1.5 Ngày                       │ │
│ │ (44pt Bold Navy)     │  │ (44pt Bold Red)      │  │ (44pt Bold Cyan)               │ │
│ └──────────────────────┘  └──────────────────────┘  └────────────────────────────────┘ │
│                                                                                        │
│ Bộ môn Phối hợp        Tổng Xung đột   Nghiêm trọng (Critical)  Thời gian TB   Trạng thái │
│ ────────────────────────────────────────────────────────────────────────────────────── │
│ Kiến trúc — Kết cấu          18                   4               1.5 ngày    [PASS ✓] │
│ Kết cấu — Cơ điện            64                  12               2.0 ngày    [PASS ✓] │
│ Cơ điện — PCCC               29                   8               1.0 ngày    [PASS ✓] │
│ ══════════════════════════════════════════════════════════════════════════════════════ │
│ TỔNG THỂ DỰ ÁN              111                  24               1.5 ngày    PASS GATE│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Archetype 5: Technical Hotspots Bento Grid (Asymmetric 55/42)
*Áp dụng: Slide 5 - Điểm Nóng Kỹ Thuật Đa Bộ Môn*

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [LƯU Ý KỸ THUẬT] Điểm Nóng Trọng Yếu Cần Kiểm Soát Phối Hợp Đa Bộ Môn                 │
│                                                                                        │
│ ┌─────────────────────────────────────────┐  ┌───────────────────────────────────────┐ │
│ │ 🏛️ KIẾN TRÚC & PCCC [ARC-FP] (55% W)    │  │ 🏗️ PHÂN HỆ KẾT CẤU [STR] (42% W)      │ │
│ │ (Thẻ Lớn Hero - Accent Navy Bar 3px)    │  │ (Accent Red Dot 6px)                  │ │
│ │                                         │  │ • Mở lỗ dầm trong vùng mô men uốn nhỏ │ │
│ │ • Chiều rộng & cao thông thủy thoát nạn │  │ • Cốt thép gia cường lỗ d > 300mm     │ │
│ │   tuân thủ nghiêm ngặt QCVN 06:2022/BXD │  ├───────────────────────────────────────┤ │
│ │ • Cửa chống cháy EI 60 tại buồng thang  │  │ ⚙️ PHÂN HỆ CƠ ĐIỆN [MEP] (42% W)       │ │
│ │ • Hành lang thoát hiểm không vật cản    │  │ (Accent Cyan Dot 6px)                 │ │
│ │                                         │  │ • Van ngăn cháy tự động xuyên tường   │ │
│ │ 🏷 Căn cứ: QCVN 06:2022 / Điều 3.4.2     │  │ • Độ dốc thoát nước 1.5% đến 2.0%     │ │
│ └─────────────────────────────────────────┘  └───────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. KẾ HOẠCH HÀNH ĐỘNG TRIỂN KHAI (ACTION PLAN)

| Bước | Hạng mục công việc | File ảnh hưởng | Kết quả kỳ vọng |
| :---: | :--- | :--- | :--- |
| **1** | **Cập nhật Design Tokens** | `packages/ccba-ooxml/src/ccba_ooxml/pptx/templates.py` | Bổ sung mã màu Scandinavian `#0F172A`, `#F8FAFC`, `#CBD5E1`, `#E2E8F0`, thông số bo góc và typographic scale mới. |
| **2** | **Nâng cấp Layout Renderers** | `packages/ccba-ooxml/src/ccba_ooxml/pptx/deck_builder.py` | Hỗ trợ Bento Asymmetric Split (60/40), Bento Hotspots (55/42), Hero Numbers tự động trích xuất, Swiss Borderless Table kèm 3 KPI Cards. |
| **3** | **Cập nhật Test Cases** | `packages/ccba-ooxml/tests/test_deck_builder.py` | Bổ sung test kiểm tra render Hero Numbers, Swiss table dividers và tỷ lệ Bento grid. |
| **4** | **Tái Sinh Slide Mẫu Demo** | `.md/seminars/2026/demo_seminar_nd175.pptx` | Biên dịch lại bài thuyết trình mẫu với giao diện tối giản Thụy Sĩ đỉnh cao. |

---

*Báo cáo nghiên cứu đã được phê duyệt và sẵn sàng cho giai đoạn nâng cấp mã nguồn.*
