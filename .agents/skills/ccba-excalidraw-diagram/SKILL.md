---
name: ccba-excalidraw-diagram
description: Công cụ tạo sơ đồ Excalidraw JSON (.excalidraw) chuyên nghiệp cho Obsidian
  và excalidraw.com.
disable-model-invocation: true
applies_to:
- Phần mềm
- Thiết kế
- Tác vụ Admin
bundle: _core
user-invocable: true
command: /ccba-excalidraw-diagram
gpi:
  s: 3.0
  k: 4.0
  a: 1.0
  p: 1.0
keywords:
- Diagram
- Excalidraw
- Visualization
- Architecture
- Sơ đồ
- Flowchart
- Obsidian
triggers:
- ccba-show-me
- show-me
---

# Excalidraw Diagram Skill

Skill này tạo ra file Excalidraw JSON **đẹp, chuyên nghiệp và có chiều sâu** — không chỉ là các hộp và mũi tên thông thường.

Nguồn gốc: Dựa trên và mở rộng từ [excalidraw-diagram-skill](https://github.com/coleam00/excalidraw-diagram-skill) của coleam00, được tùy chỉnh cho hệ thống VvC Second Brain và workflow Obsidian.

---

## Triết lý cốt lõi: Diagram phải ARGUE, không chỉ DISPLAY

> Một diagram không phải là text được format lại. Đó là một lập luận thị giác cho thấy mối quan hệ, nhân quả và luồng mà từ ngữ không thể diễn đạt được. Hình dạng phải LÀ ý nghĩa.

**Isomorphism Test**: Nếu bỏ hết text, cấu trúc hình ảnh một mình có truyền đạt được khái niệm không? Nếu không — thiết kế lại.

**Education Test**: Người xem có thể học được điều gì cụ thể từ diagram này không?

---

## Quy trình thực hiện (6 bước)

### Bước 0: Đánh giá độ sâu cần thiết
- **Đề xuất dựng mẫu thử nhanh (ADR 0010):** Khi thiết kế các luồng kiến trúc/giao diện phức tạp dưới dạng Excalidraw, Agent có thể đề xuất người dùng chạy `/ccba-implement` ở nhánh **UI (UI.md)** để sinh nhanh 3 biến thể giao diện thô kèm bộ switcher nổi dưới đáy màn hình, giúp người dùng trực quan hóa sơ đồ trước khi thiết kế chi tiết trên Excalidraw.

**Diagram đơn giản/khái niệm** — dùng khi:
- Giải thích mental model hoặc triết lý
- Khán giả không cần chi tiết kỹ thuật
- Ví dụ: "Vòng lặp phản hồi", "Phân cấp tổ chức"

**Diagram toàn diện/kỹ thuật** — dùng khi:
- Diagramming hệ thống thực, protocol, hoặc kiến trúc
- Dùng để giảng dạy hoặc thuyết trình
- Cần evidence artifacts (code snippets, JSON examples, real data)
- **Tiêu chí hoàn thành:** Xác định rõ đối tượng người xem và mức độ chi tiết (đơn giản hay kỹ thuật toàn diện) của diagram.

### Bước 1: Hiểu sâu nội dung

Với mỗi khái niệm, hỏi:
- Khái niệm này **LÀM gì**? (không chỉ là nó là gì)
- Mối quan hệ giữa các khái niệm là gì?
- Luồng hoặc sự chuyển hóa cốt lõi là gì?
- **Người xem cần THẤY gì để hiểu?**
- **Tiêu chí hoàn thành:** Làm rõ bản chất chức năng, mối quan hệ và luồng chuyển hóa giữa các khái niệm.

### Bước 2: Map khái niệm sang Visual Pattern

| Nếu khái niệm... | Dùng pattern này |
|-------------------|-----------------|
| Tạo ra nhiều output | **Fan-out** (mũi tên tỏa ra từ trung tâm) |
| Kết hợp nhiều input thành một | **Convergence** (phễu, mũi tên hội tụ) |
| Có cấu trúc phân cấp | **Tree** (lines + free-floating text) |
| Là chuỗi các bước | **Timeline** (line + dots + free-floating labels) |
| Lặp hoặc cải tiến liên tục | **Cycle** (mũi tên quay lại điểm bắt đầu) |
| Là trạng thái trừu tượng | **Cloud** (overlapping ellipses) |
| Chuyển đổi input thành output | **Assembly line** (before → process → after) |
| So sánh hai thứ | **Side-by-side** (song song với tương phản) |
- **Tiêu chí hoàn thành:** Lựa chọn visual pattern phù hợp với ngữ nghĩa của từng khái niệm cụ thể.

### Bước 3: Đảm bảo sự đa dạng

Với diagram nhiều khái niệm: **mỗi khái niệm chính phải dùng một visual pattern khác nhau**. Tuyệt đối không dùng lưới hộp đều nhau.
- **Tiêu chí hoàn thành:** Đảm bảo bố cục phong phú, kết hợp đa dạng các pattern khác nhau thay vì lưới hộp đơn điệu.

### Bước 4: Phác thảo luồng

Trước khi viết JSON, hãy trace mentally cách mắt di chuyển qua diagram. Phải có một "visual story" rõ ràng.
- **Tiêu chí hoàn thành:** Luồng dẫn dắt thị giác (visual story) được thiết lập liền mạch từ điểm bắt đầu đến kết thúc.

### Bước 5: Generate JSON (từng section)

**QUAN TRỌNG**: Với diagram lớn và toàn diện, **xây dựng JSON từng section một**. KHÔNG cố generate toàn bộ file trong một lần.
- **Tiêu chí hoàn thành:** Cấu trúc JSON cho từng section được tạo thành công với tọa độ hình học chính xác.

### Bước 6: Tạo file và kiểm tra

Sau khi generate JSON, tạo file `.excalidraw` với cấu trúc chuẩn (xem phần Format bên dưới).
- **Tiêu chí hoàn thành:** File `.excalidraw` hợp lệ được tạo và hiển thị kiểm tra thành công.

---

## Palette màu chuẩn (Brand Colors)

**Áp dụng nhất quán** trong mọi diagram. Màu mã hóa ý nghĩa, không phải trang trí.

### Shape Colors (Semantic)

| Mục đích | Fill | Stroke |
|----------|------|--------|
| Primary/Neutral | `#3b82f6` | `#1e3a5f` |
| Secondary | `#60a5fa` | `#1e3a5f` |
| Tertiary | `#93c5fd` | `#1e3a5f` |
| Start/Trigger | `#fed7aa` | `#c2410c` |
| End/Success | `#a7f3d0` | `#047857` |
| Warning/Reset | `#fee2e2` | `#dc2626` |
| Decision | `#fef3c7` | `#b45309` |
| AI/LLM | `#ddd6fe` | `#6d28d9` |
| Error | `#fecaca` | `#b91c1c` |

**Luôn dùng stroke tối hơn fill để tạo contrast.**

### Text Colors (Hierarchy)

| Level | Color | Dùng cho |
|-------|-------|---------|
| Title | `#1e40af` | Section headings, major labels |
| Subtitle | `#3b82f6` | Subheadings, secondary labels |
| Body/Detail | `#64748b` | Annotations, metadata |
| On light fills | `#374151` | Text bên trong shape sáng màu |
| On dark fills | `#ffffff` | Text bên trong shape tối màu |

### Evidence Artifact Colors

| Artifact | Background | Text |
|----------|-----------|------|
| Code snippet | `#1e293b` | Syntax-colored |
| JSON/data | `#1e293b` | `#22c55e` (green) |

---

## Cấu trúc JSON chuẩn

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [...],
  "appState": {
    "viewBackgroundColor": "#ffffff",
    "gridSize": 20
  },
  "files": {}
}
```

### File format cho Obsidian (`.excalidraw.md`)

```markdown
---
excalidraw-plugin: parsed
tags: [excalidraw]
---
==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠==

# Text Elements
[text elements listed here with ^id anchors]

%%
# Drawing
```json
{...excalidraw json...}
```
%%
```

**QUAN TRỌNG cho Obsidian**: Khối `# Drawing` PHẢI được bọc trong `%%...%%` để Plugin Excalidraw nhận dạng và render đúng.

---

## Element Templates

### Free-Floating Text (không container)
```json
{
  "type": "text",
  "id": "title_1",
  "x": 100, "y": 50,
  "width": 300, "height": 35,
  "text": "Section Title",
  "originalText": "Section Title",
  "fontSize": 24,
  "fontFamily": 3,
  "textAlign": "left",
  "verticalAlign": "top",
  "strokeColor": "#1e40af",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 1,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 11111,
  "version": 1,
  "versionNonce": 22222,
  "isDeleted": false,
  "groupIds": [],
  "boundElements": null,
  "link": null,
  "locked": false,
  "containerId": null,
  "lineHeight": 1.25
}
```

### Rectangle (shape)
```json
{
  "type": "rectangle",
  "id": "rect_1",
  "x": 100, "y": 100,
  "width": 180, "height": 90,
  "strokeColor": "#1e3a5f",
  "backgroundColor": "#93c5fd",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 12345,
  "version": 1,
  "versionNonce": 67890,
  "isDeleted": false,
  "groupIds": [],
  "boundElements": [{"id": "text_1", "type": "text"}],
  "link": null,
  "locked": false,
  "roundness": {"type": 3}
}
```

### Text bên trong Shape (PHẢI là element riêng biệt)

> ⚠️ CRITICAL: Rectangle/Ellipse/Diamond KHÔNG render text từ trường `text` của chính chúng. Phải tạo element `text` riêng với `containerId` trỏ về shape.

```json
{
  "type": "text",
  "id": "text_1",
  "x": 110, "y": 128,
  "width": 160, "height": 24,
  "text": "Label",
  "originalText": "Label",
  "fontSize": 16,
  "fontFamily": 3,
  "textAlign": "center",
  "verticalAlign": "middle",
  "strokeColor": "#374151",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 1,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 11112,
  "version": 1,
  "versionNonce": 22223,
  "isDeleted": false,
  "groupIds": [],
  "boundElements": null,
  "link": null,
  "locked": false,
  "containerId": "rect_1",
  "lineHeight": 1.25
}
```

### Arrow
```json
{
  "type": "arrow",
  "id": "arrow_1",
  "x": 280, "y": 145,
  "width": 120, "height": 0,
  "strokeColor": "#1e3a5f",
  "backgroundColor": "transparent",
  "fillStyle": "solid",
  "strokeWidth": 2,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 33333,
  "version": 1,
  "versionNonce": 44444,
  "isDeleted": false,
  "groupIds": [],
  "boundElements": null,
  "link": null,
  "locked": false,
  "points": [[0, 0], [120, 0]],
  "startBinding": {"elementId": "rect_1", "focus": 0, "gap": 2},
  "endBinding": {"elementId": "rect_2", "focus": 0, "gap": 2},
  "startArrowhead": null,
  "endArrowhead": "arrow"
}
```

### Timeline Marker (Small Dot)
```json
{
  "type": "ellipse",
  "id": "dot_1",
  "x": 94, "y": 94,
  "width": 12, "height": 12,
  "strokeColor": "#1e3a5f",
  "backgroundColor": "#3b82f6",
  "fillStyle": "solid",
  "strokeWidth": 1,
  "strokeStyle": "solid",
  "roughness": 0,
  "opacity": 100,
  "angle": 0,
  "seed": 66666,
  "version": 1,
  "versionNonce": 77777,
  "isDeleted": false,
  "groupIds": [],
  "boundElements": null,
  "link": null,
  "locked": false
}
```

---

## Quy tắc quan trọng (Anti-patterns cần tránh)

### ❌ Sai — Text trong Shape element
```json
{"type": "rectangle", "text": "Label", "fontSize": 16}
```
Rectangle không render trường `text`. Text sẽ không hiển thị.

### ✅ Đúng — Text element riêng biệt
```json
{"type": "rectangle", "id": "r1", "boundElements": [{"id": "t1", "type": "text"}]},
{"type": "text", "id": "t1", "containerId": "r1", "text": "Label"}
```

### Các lỗi thường gặp khác:
- ❌ Không có `appState` trong JSON → Plugin crash
- ❌ Dùng `roughness: 1` cho diagram chuyên nghiệp → Trông như sketch
- ❌ Generate toàn bộ diagram lớn trong một lần → JSON bị cắt, lỗi
- ❌ Uniform card grid → Không truyền đạt quan hệ
- ❌ Không có arrow giữa các element liên quan → Mất thông tin quan hệ

---

## Shape Meaning (Chọn đúng hình)

| Loại khái niệm | Shape | Lý do |
|----------------|-------|-------|
| Labels, descriptions | **none** (free-floating text) | Typography tạo hierarchy |
| Section titles | **none** (free-floating text) | Font size/weight đủ rồi |
| Timeline markers | small `ellipse` (10-20px) | Visual anchor |
| Start, trigger, input | `ellipse` | Mềm mại, origin-like |
| End, output, result | `ellipse` | Điểm đến |
| Decision, condition | `diamond` | Ký hiệu quyết định cổ điển |
| Process, action, step | `rectangle` | Hành động có giới hạn |
| Hierarchy node | lines + text (no boxes) | Cấu trúc qua đường thẳng |

**Mặc định: không có container.** Thêm shape chỉ khi nó mang ý nghĩa. Mục tiêu: <30% text elements nằm trong container.

---

## Aesthetics hiện đại

- `roughness: 0` — Clean, crisp. **Mặc định cho diagram chuyên nghiệp.**
- `roughness: 1` — Hand-drawn. Chỉ dùng cho brainstorming/informal.
- `strokeWidth: 2` — Standard cho shapes
- `strokeWidth: 1` — Thin, elegant cho lines/dividers
- `strokeWidth: 3` — Bold, dùng sparingly cho kết nối chính
- `opacity: 100` — **Luôn dùng 100%**. Dùng color/size để tạo hierarchy.
- `fontFamily: 3` — **Mặc định**. Monospace, professional.
- `fontSize: 16-20` — Recommended range.

---

## Scale và Layout

- **Hero element**: 300×150 — visual anchor, quan trọng nhất
- **Primary**: 180×90
- **Secondary**: 120×60
- **Small**: 60×40
- **Whitespace = Importance**: Element quan trọng nhất có nhiều khoảng trắng nhất (200px+)
- **Flow direction**: left→right hoặc top→bottom cho sequences, radial cho hub-and-spoke

---

## Output Format

Tuỳ theo context, agent tạo ra:

### 1. File `.excalidraw` (cho excalidraw.com / Claude Projects)
Chỉ là file JSON thuần, không cần frontmatter:
```json
{
  "type": "excalidraw",
  "version": 2,
  ...
}
```

### 2. File `.excalidraw.md` (cho Obsidian)
Dùng format Markdown với frontmatter YAML và `%%` wrapper:
```markdown
---
excalidraw-plugin: parsed
tags: [excalidraw]
---
==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠==

# Text Elements
[text content]

%%
# Drawing
```json
{json content}
```
%%
```

---

## Checklist trước khi deliver

### Depth & Evidence
- [ ] Đánh giá đúng level: simple hay comprehensive?
- [ ] (Nếu technical) Đã research actual specs, real event names?
- [ ] (Nếu comprehensive) Có evidence artifacts không?

### Conceptual
- [ ] Isomorphism test: cấu trúc thị giác mirror khái niệm?
- [ ] Variety: mỗi khái niệm chính dùng visual pattern khác nhau?
- [ ] Không có uniform card grid?

### Container Discipline
- [ ] Minimal containers: text nào có thể free-floating?
- [ ] Timeline/tree dùng lines + text thay vì boxes?

### Technical
- [ ] Mọi text trong shape đều là element riêng biệt với `containerId`?
- [ ] `appState` có trong JSON root?
- [ ] `roughness: 0` (trừ khi hand-drawn được yêu cầu)?
- [ ] `opacity: 100` cho mọi element?
- [ ] `fontFamily: 3`?
- [ ] File Obsidian có `%%` wrapper quanh `# Drawing`?

### Structural
- [ ] Mọi relationship có arrow/line?
- [ ] Luồng thị giác rõ ràng?
- [ ] Element quan trọng = lớn hơn/có nhiều whitespace hơn?


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/visual_concepts.md` | Hướng dẫn trực quan hóa giải thuật, sơ đồ dữ liệu qua Excalidraw |

