# 📐 Diagramming & Technical Visuals Hygiene

Quy chuẩn bất biến khi tạo hoặc cập nhật sơ đồ minh họa (Excalidraw, Mermaid, D2, Image Art) cho tài liệu kiến thức và bài viết học thuật.

---

## 1. Obsidian Excalidraw 2.x Wrapper Invariant
Mọi tệp `.excalidraw.md` **BẮT BUỘC** tuân thủ cấu trúc 3 tầng chuẩn của Obsidian Excalidraw Plugin (phiên bản 2.x):
```markdown
# Excalidraw Data

## Text Elements
...

%%
## Drawing
```json
...
```
%%
```
- **Quy tắc**: Tuyệt đối không dùng H1 `# Drawing` hoặc bỏ qua `# Excalidraw Data`.
- **Hệ quả nếu vi phạm**: Plugin Obsidian sẽ tự động nhân bản header `# Text Elements` và làm rò rỉ thẻ neo `^txt_...` vào thân văn bản ghi chú.

---

## 2. Mermaid Syntax & Theme Hygiene
Khi tạo hoặc nhúng sơ đồ Mermaid:
- **Subgraph Styling**: TUYỆT ĐỐI KHÔNG dùng `classDef` hay lệnh gán `class <id>` cho `subgraph`. Subgraph trong Mermaid là phần tử SVG group `<g class="cluster">`, không phải leaf node. Luôn dùng cú pháp:
  ```mermaid
  style <subgraphId> fill:#f8fafc,stroke:#334155,stroke-width:1px;
  ```
- **Non-Flowchart Diagrams**: Tuyệt đối không tiêm `classDef` vào các loại sơ đồ chuyên biệt (`pie`, `timeline`, `mindmap`, `sequenceDiagram`, `stateDiagram`). Trình phân tích cú pháp của Mermaid sẽ vỡ ngay lập tức. Tùy biến màu sắc qua khối directive khởi tạo:
  ```mermaid
  %%{init: {'theme': 'base', 'themeVariables': {'primaryColor': '#0f172a', ...}}}%%
  ```
- **Nhãn An Toàn (Label Escaping & Wrapping)**:
  - Luôn bọc nhãn node trong dấu ngoặc vuông kèm ngoặc kép: `id["Nhãn văn bản"]`.
  - Ngắt dòng bằng `<br/>` (không dùng `\n` thô).
  - Escape ký tự xung đột bằng mã thực thể HTML:
    - Ngoặc đơn `(` / `)` $\rightarrow$ `#40;` / `#41;`
    - Dấu gạch đứng `|` $\rightarrow$ `#124;`
    - Ngoặc kép `"` $\rightarrow$ `#quot;`

---

## 3. Diagrams-as-Code (D2 & Vector Graphics)
- Ưu tiên D2 cho các sơ đồ kiến trúc hệ thống sâu, hạ tầng đám mây và luồng dữ liệu phức tạp.
- Biên dịch ra vector SVG qua local `d2` CLI hoặc Kroki REST API (`https://kroki.io/d2/svg`, 0 dependency, timeout 15s).
- Lưu cả tệp `.svg` và `.d2` (mã nguồn) vào thư mục đính kèm (`attachments/`).

---

## 4. Kiến Trúc Minh Họa Đa Tầng (4-Layer Hierarchy)
Mỗi bài viết chuyên sâu hoặc tổng hợp kiến trúc nên kết hợp linh hoạt 4 tầng thị giác:
- **Tầng 1 (Hero Art)**: Ảnh bìa ẩn dụ tỉ lệ 16:9 ở đầu bài viết (ngay dưới H1 title), sinh qua multimodal diffusion (`![[ten_bai_viet_hero.jpg|100%]]`).
- **Tầng 2 (Interactive Canvas)**: Sơ đồ Excalidraw tổng quan tương tác trên Desktop Obsidian (`![[ten_bai_viet.excalidraw.md|100%]]`).
- **Tầng 3 (Inline Native)**: Sơ đồ Mermaid nội dòng ngay dưới các mục phân tích cụ thể, tối ưu cho Mobile và GitHub (` ```mermaid `).
- **Tầng 4 (High-res Vector)**: Tệp SVG kiến trúc D2 cho nhu cầu xuất bản PDF/Web chất lượng cao (`![[ten_bai_viet.d2.svg|100%]]`).

---

## 5. Windows CRLF-Safe Markdown Manipulation
- Môi trường Windows sử dụng ký tự xuống dòng `\r\n`. Khi xử lý YAML frontmatter hoặc chèn ảnh dưới H1 bằng regex, luôn sử dụng mẫu regex an toàn `\r?\n` hoặc module `core.frontmatter` (`parse_frontmatter`, `extract_body`) để bảo vệ dữ liệu không bị hỏng.
