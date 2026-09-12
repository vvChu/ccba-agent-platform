---
name: ccba-research
description: Nghiên cứu chuyên sâu một vấn đề kỹ thuật hoặc pháp lý đối chiếu với
  các nguồn tài liệu gốc đáng tin cậy bằng cách khởi chạy subagent chạy ngầm (hỗ trợ
  Dual-Agent Adversarial).
metadata:
  version: "1.2.0"
  author: "CCBA Hub"
user-invocable: true
command: /ccba-research
gpi:
  s: 4.0
  k: 3.0
  a: 1.0
  p: 1.0
keywords:
- research
- nghiên cứu
- tìm hiểu
- tra cứu
- citations
- adversarial
- deep-investigation
disable-model-invocation: true
bundle: _software
tier: kernel
triggers:
- research
- nghiên cứu
- tìm hiểu
- tra cứu
- citations
- ccba-research
- adversarial research
- ccba-sequential-thinking
- sequential-thinking
---

# 📚 Kỹ năng: ccba-research (Nghiên Cứu Chạy Ngầm & Phản Biện Đa Tác Nhân)

Kỹ năng này hướng dẫn Agent cách khởi chạy **background subagents** (`research` subagents) để thực hiện các cuộc điều tra tài liệu, thu thập thông tin facts từ các API, mã nguồn hoặc Văn bản Pháp luật (VBPL) song song dưới nền theo **Kiến trúc Suy luận 3 Pha (Three-Phase Reasoning Hierarchy)**. Điều này giúp Agent chính tiếp tục làm việc mà không bị block và loại bỏ nguy cơ ô nhiễm ngữ cảnh (context bloating).

---

## 📋 Tiêu chí hoàn thành (Completion Criteria)

Kỹ năng chỉ được coi là hoàn thành khi đáp ứng các điều kiện sau:
1. Khởi chạy thành công subagent `research` chạy ngầm qua `invoke_subagent` (chế độ Đơn tác nhân hoặc Phản biện Kép).
2. Subagent tuân thủ **Rào chắn Ngân sách Tìm kiếm (Search Budget Cap)**: Tối đa 5 lượt tra cứu/tìm kiếm (max 5 tool calls) trong 1 phiên.
3. Subagent thu thập thông tin trực tiếp từ **các nguồn sơ cấp đáng tin cậy** (tài liệu chính thức, source code dự án, API gốc, VBPL hiện hành) và áp dụng **Kiểm chứng Nguồn tin Chéo (Cross-Reference Validation)**.
4. Tuân thủ nghiêm ngặt **Two-Layer Sub-Agent Guardrail (ADR 0035)**: Độ sâu `depth_limit = 1`, chỉ cấp quyền công cụ đọc (`view_file`, `grep_search`, `read_resource`), tối đa 2 subagents song song.
5. Kết quả nghiên cứu được xuất ra tệp Markdown theo **Mẫu Báo cáo Kỹ thuật 5 phần chuẩn hóa**, có trích dẫn nguồn (citations) rõ ràng.
6. Tệp báo cáo được lưu trữ linh hoạt tại:
   - Mặc định: `.md/knowledge/research_and_studies/research-[slug].md`
   - Trong ngữ cảnh Wayfinder/Issue: `.md/knowledge/issues/[feature_name]/research-[slug].md`

---

## 🛠️ Quy trình thực hiện (3 Pha Chuẩn Boost)

### Pha 1: Phân Rã Bài Toán & Lựa Chọn Chế Độ (Goal & Strategy Formulation)
Xác định câu hỏi nghiên cứu của người dùng và lựa chọn chế độ thực thi:
- **Chế độ Chuẩn (Standard Single Subagent):** Dành cho tra cứu tài liệu, API specs, tóm tắt thư viện thông thường.
- **Chế độ Phản biện Kép (Dual-Agent Adversarial Pattern):** Kích hoạt khi nghiên cứu quyết định kiến trúc lớn (ADR), tái cấu trúc module phức tạp, hoặc giải quyết xung đột văn bản pháp luật/quy chuẩn.

**Tiêu chí hoàn thành:** Xác định rõ phạm vi câu hỏi và nguồn sơ cấp cần đối chiếu.

---

### Pha 2: Thực Thi Độc Lập Chạy Ngầm (Parallel Multi-Agent Execution)

#### Trường Hợp A — Chế độ Chuẩn (Single Subagent)
Sử dụng `invoke_subagent` khởi chạy 1 subagent `research` với Search Budget Cap (5 tool calls) và Mẫu báo cáo 5 phần.

#### Trường Hợp B — Chế độ Phản Biện Kép (Dual-Agent Adversarial)
Sử dụng `invoke_subagent` khởi chạy đồng thời **2 subagents độc lập**:
1. **Subagent A (`Solution Explorer / Proponent`):**
   - Nhiệm vụ: Khảo sát giải pháp tối ưu, code patterns mẫu, best practices kỹ thuật và các ưu điểm nổi bật.
   - Budget: Max 5 tool calls.
2. **Subagent B (`Risk & Boundary Challenger`):**
   - Nhiệm vụ: Rà soát rủi ro bảo mật (Maskara), vi phạm ranh giới Deep Seams (ADR 0035), breaking changes, và các trường hợp biên (edge cases).
   - Budget: Max 5 tool calls.

---

**Tiêu chí hoàn thành:** Hoàn thành khảo sát độc lập từ các subagent trong ngân sách tìm kiếm.

---

### Pha 3: Hợp Nhất, Phản Biện & Xuất Báo Cáo (Synthesis & Delivery)
Khi các subagents hoàn tất và gửi thông báo hoàn thành (Reactive Wakeup):
- Agent chính đọc báo cáo và tổng hợp ma trận đánh giá: **Giá trị × Độ phức tạp × Rủi ro × KISS**.
- Trình bày tệp Markdown chuẩn 5 phần:

```markdown
# Báo cáo Nghiên cứu: [Tên Chủ Đề]

## 1. Tóm tắt Thực thi (Executive Summary)
[Tóm tắt 2-3 đoạn về phát hiện cốt lõi và các đề xuất hành động chính]

## 2. Kết quả Nghiên cứu Chi tiết (Key Findings)
- **Tổng quan & Xu hướng**: [Mô tả chi tiết kỹ thuật/pháp lý, phiên bản, độ chín]
- **Quy chuẩn Tốt nhất (Best Practices)**: [Các khuyến nghị kỹ thuật/quy trình tốt nhất]
- **Bẫy thường gặp & Rủi ro (Adversarial Risks & Common Pitfalls)**: [Các rủi ro, bẫy thiết kế và phương án khắc phục từ Challenger]
- **Bảo mật & Hiệu năng**: [Đánh giá ranh giới Maskara và Deep Seams]

## 3. Khuyến nghị Triển khai (Implementation Recommendations)
- [Các bước hành động ngắn gọn, khả thi để áp dụng vào hệ thống CCBA]

## 4. Tài liệu Tham chiếu & Citations (References & Citations)
- [Bảng hoặc danh sách chứa liên kết/nguồn trích dẫn sơ cấp rõ ràng]

## 5. Câu hỏi chưa làm rõ (Unresolved Questions)
- [Nêu rõ các câu hỏi, giả định mầm hoặc điểm mù chưa thể xác nhận, nếu có]
```

**Tiêu chí hoàn thành:** Báo cáo Markdown được lưu tại đúng đường dẫn và hiển thị liên kết truy cập trực tiếp cho người dùng.

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*



**Tiêu chí hoàn thành:** Báo cáo nghiên cứu 5 phần được lưu vào tệp markdown theo đúng cấu trúc.


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/sequential_thinking_method.md` | Phương pháp tư duy suy luận tuần tự nhiều bước (Sequential Thinking) |
| `references/sequential_core-patterns.md` | Các mẫu hình cốt lõi và khung giải thuật tư duy logic |
| `references/sequential_advanced-techniques.md` | Kỹ thuật suy luận phản biện nâng cao và phân nhánh giả thuyết |

