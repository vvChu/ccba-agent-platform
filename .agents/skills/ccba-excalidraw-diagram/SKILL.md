---
name: ccba-excalidraw-diagram
description: Tạo và tối ưu sơ đồ kiến trúc Excalidraw tất định 16:9 với 8 layout engines và Bảng Đặc Tả Ma Trận Markdown chuẩn công thái học.
disable-model-invocation: true
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Tác vụ Admin
bundle: _core
tier: kernel
user-invocable: true
command: /ccba-excalidraw-diagram
metadata:
  version: "1.0.0"
  author: "CCBA Hub"
gpi:
  s: 4.0
  k: 4.0
  a: 3.0
  p: 3.0
triggers:
- excalidraw
- vẽ sơ đồ
- diagram
- layout engine
- sơ đồ kiến trúc
- vẽ quy trình
- layout router
---

# Excalidraw Diagramming & Layout Engine

Skill hỗ trợ thiết kế, tối ưu bố cục tự động và xuất bản sơ đồ kỹ thuật Excalidraw chuẩn công thái học thị giác 16:9 (Visual Ergonomics Standard v8.15.10) cho toàn bộ mạng lưới dự án CCBA.

---

## 🎯 Khi Nào Sử Dụng

- Khi cần vẽ sơ đồ kiến trúc hệ thống, chuỗi giá trị, luồng dữ liệu, hoặc sơ đồ tổ chức.
- Khi cần tối ưu hoá toạ độ Excalidraw elements tự động để tránh chồng lấn hình khối.
- Khi cần xuất **Bảng Đặc Tả Ma Trận Kiến Trúc Markdown** đi kèm ngay dưới sơ đồ.
- Khi người dùng yêu cầu: "vẽ sơ đồ", "excalidraw diagram", "sơ đồ kiến trúc", "bố cục quy trình".

---

## 🏛️ Bộ 8 Layout Engines & Tiêu Chí Lựa Chọn

Thư viện lõi `ccba-diagram` (`from ccba_diagram import apply_smart_layout`) hỗ trợ 8 layout engines:

| Engine | Mã Hint LLM | Dạng Cấu Trúc Đồ Thị Phù Hợp |
| :--- | :--- | :--- |
| **`sugiyama`** | `#layout:sugiyama` | Phân tầng thứ bậc theo DAG (Directed Acyclic Graph) |
| **`wheel`** | `#layout:wheel` | Trung tâm Hub điều phối với chu trình ngoài xoay chiều kim đồng hồ |
| **`matrix`** | `#layout:matrix` | Ma trận 4 góc phần tư 2x2 hoặc phân tán toạ độ (style `cross` / `axis`) |
| **`tree`** | `#layout:tree` | Cấu trúc cây phân nhánh Top-Down (`#dir:td`) hoặc Left-to-Right (`#dir:lr`) |
| **`radial`** | `#layout:radial` | Toả tròn hình sao 1 Hub kết nối với các Spoke độc lập |
| **`concentric`** | `#layout:concentric` | Các vành đai đồng tâm đa tầng từ lõi ra ngoại vi |
| **`value_chain`** | `#layout:value_chain` | Chuỗi giá trị Porter / pipeline tuần tự ngang và hoạt động bổ trợ |
| **`cycle`** | `#layout:cycle` | Vòng lặp phản hồi khép kín (Closed feedback loop) |

---

## 📐 Quy Chuẩn Công Thái Học Thị Giác 16:9

1. **Khóa Canvas Width:** $1.000\text{px} \le W \le 1.150\text{px}$ để tỷ lệ co giãn nhúng vào tài liệu đạt $\ge 65\%-70\%$.
2. **Cắt Tỉa Mũi Tên:** Tuyệt đối dùng `get_shape_boundary_point` để cắt tỉa theo biên hình khối ellipse/hộp chữ nhật, triệt tiêu đè khối hoặc ngược đầu mũi tên.
3. **Bảng Đặc Tả Markdown:** Luôn gọi `generate_markdown_spec_table(elements)` để xuất bảng đặc tả bên dưới sơ đồ.
   - Bắt buộc escape pipe trong wikilinks: `[[slug\|alias]]`.
   - Phân tầng 2 nhịp: `↳&nbsp;Target Node`.
   - Bắt buộc dùng ngoặc tròn `()`, tuyệt đối không rò rỉ `#40;`/`#41;` ra bảng Markdown.

---

## 💻 Cách Vận Hành Qua Python API & CLI

```python
from ccba_diagram import apply_smart_layout, generate_markdown_spec_table

# 1. Tối ưu hoá toạ độ elements in-place
engine_used = apply_smart_layout(elements)

# 2. Sinh bảng Markdown
spec_table = generate_markdown_spec_table(elements)
```

Hoặc qua dòng lệnh:
```bash
ccba-diagram layout input.json -o output.json --engine auto
ccba-diagram spec-table input.json
```

---

## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ thiết kế và tối ưu sơ đồ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| [`references/visual_concepts.md`](references/visual_concepts.md) | Cẩm nang nguyên lý thị giác, bảng màu Academic Grayscale & Pastel, typography 16:9 và bố cục ma trận |

## Bộc Lộ Dần & Cấu Trúc Tinh Gọn (Progressive Disclosure)
* **Cấu trúc tài liệu Level 3:** Phân tách rõ ràng giữa quy trình cốt lõi và tài liệu hướng dẫn chuyên sâu qua bảng chỉ mục Level 3.
* **Tham chiếu liên kết:** Mọi tài liệu mở rộng đều được dẫn xuất qua liên kết Markdown chuẩn mực: [`references/visual_concepts.md`](references/visual_concepts.md).
* **Chống rác dữ liệu (Anti-Debris Invariant):** Không để lại comment nháp, TODO tạm thời hay các chỉ thị thừa không cần thiết.
