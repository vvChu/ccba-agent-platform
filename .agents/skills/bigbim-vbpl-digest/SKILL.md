---
name: bigbim-vbpl-digest
description: Tra cứu và tóm lược nội dung văn bản pháp lý BIM Việt Nam kết hợp các
  tiêu chuẩn ISO 19650-1/2/3/5 và quy chuẩn kỹ thuật xây dựng.
applies_to:
- BIM
- Pháp điển
- Thẩm tra thiết kế
bundle: _bim
tier: kernel
command: /bigbim-vbpl-digest
layer: _bim
metadata:
  version: "1.0.0"
  author: "BIGBIM"
gpi:
  s: 3.0
  k: 2.0
  a: 4.0
  p: 1.0
triggers:
- nghị định BIM
- điều khoản BIM
- ISO 19650
- luật xây dựng BIM
- pháp lý BIM
- quy định nộp BIM
- bắt buộc BIM
---
# BIGBIM VBPL Digest Skill

> **Vai trò**: Chuyên gia Pháp lý BIM — tra cứu điều khoản, tóm tắt yêu cầu, giải thích nghĩa vụ theo VBPL hiện hành.
> **Sứ mệnh**: Trả lời câu hỏi "quy định nào yêu cầu X?" và "điều Y của NĐ/ISO nói gì?" một cách chính xác, có căn cứ trích dẫn chuẩn xác.

---

## 🏛️ Platform-Aware Architecture Posture (ADR-0061)

Skill này thuộc thế năng **`compose-existing`**, hợp thành từ các công cụ tra cứu tri thức pháp lý của nền tảng:
* **Tra Cứu & Trích Xuất Pháp Lý:** Sử dụng CLI `python -m ccba_legal query` và `get-clause` (Deep Seam `LegalKnowledgeEngine`). Các chunk tài liệu cũ tại Spoke chỉ đóng vai trò tham khảo kỹ thuật, không có giá trị bảo chứng hiệu lực.
* **SSOT Vòng Đời & Hiệu Lực:** Trạng thái hiệu lực và quan hệ thay thế bắt buộc đối soát theo nguyên tắc kiểm định SSOT tại Mục 5; tuyệt đối không sử dụng văn bản đã hết hiệu lực thi hành.

---

## 📚 Nguồn Dữ Liệu & Công Cụ Tra Cứu

> **Quy định SSOT:** Tra cứu điều khoản quy phạm pháp luật bắt buộc thực thi qua Deep Seam `ccba_legal query` và `get-clause`. Các chunk tiêu chuẩn ISO đóng vai trò tài liệu kỹ thuật phụ trợ:

| Nguồn | Loại | Công cụ / Đường dẫn |
|:------|:------|:-------------------|
| Quy phạm pháp luật BIM | Pháp lý SSOT | CLI `python -m ccba_legal query` và `get-clause` |
| ISO 19650-1 — 15 chunks | Kỹ thuật | `[bigbim_method_path]/.md/chunks/ISO_19650_VN/1-AP01-*/` |
| ISO 19650-2 — 12 chunks | Kỹ thuật | `[bigbim_method_path]/.md/chunks/ISO_19650_VN/2-AP01-*/` |
| ISO 19650-3 — 12 chunks | Kỹ thuật | `[bigbim_method_path]/.md/chunks/ISO_19650_VN/3-AP01-*/` |
| ISO 19650-5 — 15 chunks | Kỹ thuật | `[bigbim_method_path]/.md/chunks/ISO_19650_VN/5-AP01-*/` |
| Chunk Master Index | Kỹ thuật | `[bigbim_method_path]/.md/chunks/INDEX.md` |

**Workflow tra cứu:**
1. Tra cứu VBPL quy phạm: gọi `python -m ccba_legal query --q "..."` và `python -m ccba_legal get-clause ...`
2. Tra cứu tiêu chuẩn kỹ thuật ISO: định vị chunk trong `chunks/ISO_19650_VN/`
3. Trích dẫn nguyên văn điều khoản chính xác kèm trạng thái hiệu lực chuẩn hóa ACTIVE

---

## Hub & Execution Context

*   **Skill Path**: `.agents/skills/bigbim-vbpl-digest/SKILL.md`
*   **Trigger Keywords**: `NĐ 175`, `nghị định BIM`, `Nghị định 175`, `điều khoản BIM`, `ISO 19650`, `điều`, `khoản`, `luật xây dựng BIM`, `pháp lý BIM`, `quy định nộp BIM`, `bắt buộc BIM`, `thời điểm nộp`

---

## 🎯 Quy trình thực thi của AI Agent

### Bước 1 — Phân tích câu hỏi

Xác định:
- **Nguồn**: Quy chuẩn/Nghị định quy phạm hay Tiêu chuẩn kỹ thuật ISO 19650?
- **Loại query**: Tra điều khoản cụ thể (số điều/khoản) hay tìm theo chủ đề?
- **Output format**: Trích dẫn nguyên văn, tóm tắt, hay so sánh?
- **Tiêu chí hoàn thành:** Xác định rõ ràng nguồn văn bản, loại truy vấn và định dạng đầu ra mong muốn.

### Bước 2 — Tra cứu dữ liệu

```bash
# 1. Nếu là văn bản quy phạm pháp luật (VBPL):
python -m ccba_legal query --q "<từ khóa>" --status ACTIVE
python -m ccba_legal get-clause --doc "<doc_id>" --clause "<số điều>"

# 2. Nếu là tiêu chuẩn kỹ thuật ISO 19650:
# Đọc chunks phụ trợ: chunks/ISO_19650_VN/<phần>/00_CHUNK_INDEX.md
```
- **Tiêu chí hoàn thành:** Định vị chính xác điều khoản quy phạm qua Seam hoặc đường dẫn chunk tiêu chuẩn kỹ thuật liên quan.

### Bước 3 — Đọc và tổng hợp

- Đọc điều khoản trích xuất từ Seam hoặc chunk liên quan
- Trích dẫn nguyên văn có số điều/khoản
- Nêu rõ nghĩa vụ áp dụng cho ai, khi nào
- **Tiêu chí hoàn thành:** Đọc hiểu và trích xuất đúng điều khoản nguyên văn kèm đối tượng và phạm vi áp dụng.

### Bước 4 — Output format chuẩn

```markdown
## Câu trả lời

**Nguồn**: [Mã văn bản đã đối soát SSOT], Điều X, Khoản Y
**Nguyên văn**: "..."

**Tóm tắt**: [2-3 câu]

**Áp dụng cho**: [đối tượng]
**Thời điểm**: [khi nào bắt buộc]
```
- **Tiêu chí hoàn thành:** Xuất kết quả giải đáp chuẩn format với đầy đủ nguồn, nguyên văn, tóm tắt và đối tượng áp dụng.

---

## 📋 Mapping Chủ đề → Nguồn

| Chủ đề | Nguồn chính (Seam SSOT) | Chunks kỹ thuật tham khảo |
|:-------|:------------------------|:-------------------------|
| BIM bắt buộc từ khi nào | Tra cứu VBPL qua `python -m ccba_legal query` & `get-clause` | Tài liệu kỹ thuật phụ trợ |
| Yêu cầu nộp mô hình BIM | Tra cứu VBPL qua `python -m ccba_legal query` & `get-clause` | Tài liệu kỹ thuật phụ trợ |
| CDE, EIR, AIR | Tiêu chuẩn ISO 19650-2 Section 4-5 | chunk_04–09 |
| Vận hành AIM | Tiêu chuẩn ISO 19650-3 Section 5 | chunk_06–12 |
| Phân loại bảo mật thông tin | Tiêu chuẩn ISO 19650-5 Section 4-7 | chunk_06–10 |
| Giấy phép xây dựng + BIM | Tra cứu VBPL qua `python -m ccba_legal query` & `get-clause` | Tài liệu kỹ thuật phụ trợ |
| Nghiệm thu, hoàn công + BIM | Tra cứu VBPL qua `python -m ccba_legal query` & `get-clause` | Tài liệu kỹ thuật phụ trợ |

---

## 5. Rào Chắn Điểm Liệt & Cập Nhật Hiệu Lực Văn Bản (Hard Floor Invariant)
* **TUYỆT ĐỐI KHÔNG** trích dẫn các văn bản quy phạm pháp luật đã hết hiệu lực thi hành hoặc bị thay thế.
* Mọi văn bản trích dẫn bắt buộc phải được đối soát qua lệnh SSOT `python -m ccba_legal query` hoặc thư viện `ccba_legal.registry`, đảm bảo đạt trạng thái hiệu lực chuẩn hóa `ACTIVE` (bao gồm `current`/`active` qua hàm `normalize_doc_status`) và không bị thay thế bởi văn bản khác (các trường bị thay thế `superseded_by`, `replaced_by`, `replaced_by_docs` trống và mã văn bản không nằm trong danh sách thay thế của bất kỳ văn bản kế nhiệm nào). Các văn bản kế nhiệm sở hữu quan hệ thay thế (`supersedes`, `replaces`, `replaced_docs`, `relations.*`) đối với văn bản cũ vẫn hoàn toàn hợp lệ để trích dẫn.
* Mọi vi phạm trích dẫn văn bản hết hiệu lực sẽ bị đánh rớt ngay lập tức (Hard Floor Fail-Fast: 0.0%).
