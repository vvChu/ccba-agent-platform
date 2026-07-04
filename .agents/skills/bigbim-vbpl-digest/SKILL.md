---
name: bigbim-vbpl-digest
description: Tra cứu và tóm lược nội dung văn bản pháp lý BIM Việt Nam — NĐ 175/2024, ISO 19650-1/2/3/5, QCVN liên quan.
applies_to:
  - "Quản lý thông tin"
  - "Tư vấn pháp luật xây dựng"
  - "BIM Execution"
bundle: "_core"
---

# BIGBIM VBPL Digest Skill

> **Vai trò**: Chuyên gia Pháp lý BIM — tra cứu điều khoản, tóm tắt yêu cầu, giải thích nghĩa vụ theo VBPL hiện hành.
> **Sứ mệnh**: Trả lời câu hỏi "quy định nào yêu cầu X?" và "điều Y của NĐ/ISO nói gì?" một cách chính xác, có trích dẫn.

---

## 📚 BIGBIM Method KB — Nguồn dữ liệu

> Skill này **TRA CỨU TRỰC TIẾP** từ chunks của tài liệu gốc:

| Nguồn | Layer | Path |
|:------|:------|:-----|
| NĐ 175/2024 — 111 chunks | Layer 2 | `[bigbim_method_path]/.md/chunks/VBPL_BIM_VN/175_2024_ND-CP_*/` |
| ISO 19650-1 — 15 chunks | Layer 2 | `[bigbim_method_path]/.md/chunks/ISO_19650_VN/1-AP01-*/` |
| ISO 19650-2 — 12 chunks | Layer 2 | `[bigbim_method_path]/.md/chunks/ISO_19650_VN/2-AP01-*/` |
| ISO 19650-3 — 12 chunks | Layer 2 | `[bigbim_method_path]/.md/chunks/ISO_19650_VN/3-AP01-*/` |
| ISO 19650-5 — 15 chunks | Layer 2 | `[bigbim_method_path]/.md/chunks/ISO_19650_VN/5-AP01-*/` |
| Chunk Master Index | Layer 2 | `[bigbim_method_path]/.md/chunks/INDEX.md` |

**Workflow tra cứu:**
1. Đọc `chunks/INDEX.md` để xác định nguồn phù hợp
2. Đọc `00_CHUNK_INDEX.md` trong folder nguồn để locate chunk
3. Đọc chunk cụ thể → trích dẫn điều khoản chính xác
4. Cross-reference với KB articles Layer 3 nếu cần synthesis

---

## Hub & Execution Context

*   **Skill Path**: `.agents/skills/bigbim-vbpl-digest/SKILL.md`
*   **Trigger Keywords**: `NĐ 175`, `nghị định BIM`, `Nghị định 175`, `điều khoản BIM`, `ISO 19650`, `điều`, `khoản`, `luật xây dựng BIM`, `pháp lý BIM`, `quy định nộp BIM`, `bắt buộc BIM`, `thời điểm nộp`

---

## 🎯 Quy trình thực thi của AI Agent

### Bước 1 — Phân tích câu hỏi

Xác định:
- **Nguồn**: NĐ 175 hay ISO 19650-1/2/3/5?
- **Loại query**: Tra điều khoản cụ thể (số điều/khoản) hay tìm theo chủ đề?
- **Output format**: Trích dẫn nguyên văn, tóm tắt, hay so sánh?

### Bước 2 — Locate chunk

```
Nếu NĐ 175:
  → chunks/VBPL_BIM_VN/175_2024_ND-CP_.../00_CHUNK_INDEX.md
  → Tìm chunk theo keyword trong heading column

Nếu ISO 19650:
  → chunks/ISO_19650_VN/<phần>/00_CHUNK_INDEX.md
  → Tìm theo section number (VD: "5.6 Tiến trình")
```

### Bước 3 — Đọc và tổng hợp

- Đọc chunk liên quan (1-3 chunks tối đa)
- Trích dẫn nguyên văn có số điều/khoản
- Nêu rõ nghĩa vụ áp dụng cho ai, khi nào

### Bước 4 — Output format chuẩn

```markdown
## Câu trả lời

**Nguồn**: NĐ 175/2024-NĐ-CP, Điều X, Khoản Y
**Nguyên văn**: "..."

**Tóm tắt**: [2-3 câu]

**Áp dụng cho**: [đối tượng]
**Thời điểm**: [khi nào bắt buộc]
```

---

## 📋 Mapping Chủ đề → Nguồn

| Chủ đề | Nguồn chính | Chunks tham khảo |
|:-------|:-----------|:----------------|
| BIM bắt buộc từ khi nào | NĐ 175 Điều 8 | chunk_01–05 |
| Yêu cầu nộp mô hình BIM | NĐ 175 Chương III | chunk_20–35 |
| CDE, EIR, AIR | ISO 19650-2 Section 4-5 | chunk_04–09 |
| Vận hành AIM | ISO 19650-3 Section 5 | chunk_06–12 |
| Phân loại bảo mật thông tin | ISO 19650-5 Section 4-7 | chunk_06–10 |
| Giấy phép xây dựng + BIM | NĐ 175 Chương VI | chunk_50–65 |
| Nghiệm thu, hoàn công + BIM | NĐ 175 Chương VIII | chunk_80–95 |
