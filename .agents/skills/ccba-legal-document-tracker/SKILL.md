---
name: ccba-legal-document-tracker
description: Theo dõi, so sánh và phân tích các VBPL xây dựng Việt Nam với VBHNEngine
  và Registry.
applies_to:
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _consulting
tier: kernel
user-invocable: true
command: /ccba-legal-document-tracker
metadata:
  version: "1.0.0"
  author: "CCBA Hub"
gpi:
  s: 4.0
  k: 3.0
  a: 4.0
  p: 1.0
triggers:
- VBPL
- pháp luật
- legal
- registry
- nghị định
- thông tư
- văn bản pháp luật
- luật xây dựng
- ccba-update-legal-registry
- update-legal-registry
---

# Legal Document Tracker

Skill hỗ trợ theo dõi, phân tích và so sánh các Văn bản Pháp luật (VBPL) liên quan đến quản lý chất lượng công trình xây dựng tại Việt Nam kết hợp Deep Seam **`VBHNEngine`** ([`packages/ccba-legal-intel`](../../../packages/ccba-legal-intel)).

---

## 🏛️ Platform-Aware Architecture Posture (ADR-0061)

Skill này thuộc thế năng **`compose-existing`**, hợp thành từ các Seam và engine quản trị văn bản đã có trong nền tảng:
* **Hạ Tầng Hợp Nhất Văn Bản:** Sử dụng `LegislativeConsolidator` hoặc `VBHNEngine.merge_documents` của gói `ccba-legal-intel` (CLI `python -m ccba_legal consolidate`). Tuyệt đối không tự viết logic merge văn bản ad-hoc.
* **SSOT Vòng Đời & Hiệu Lực:** Trạng thái hiệu lực chuẩn hóa và quan hệ thay thế đối soát qua lệnh `python -m ccba_legal query` hoặc thư viện `ccba_legal.registry` (công nhận status chuẩn hóa `ACTIVE`, cùng các trường thay thế `supersedes`, `replaces`, `replaced_docs`, `relations.*`); tuyệt đối không dán cứng danh sách văn bản thay thế vào thân skill.

---

## When to Use

- Cần **cập nhật danh mục VBPL** đang theo dõi (thêm mới, thay đổi trạng thái)
- Cần **so sánh VBPL cũ ↔ mới** (VD: NĐ 06/2021 vs dự thảo NĐ QLCL 2026) qua AST diff tự động
- Cần **hợp nhất văn bản pháp luật** (Luật gốc + các Nghị định sửa đổi bổ sung)
- Cần **đánh giá tác động** của VBPL mới lên quy trình CCBA
- Cần **hướng dẫn NotebookLM** để đọc nhanh VBPL hoặc soạn thảo công văn

---

## Key Files

| File | Mô tả |
|------|--------|
| `legal_registry.yaml` | **Root SSOT**: Danh mục 34+ VBPL/QCVN/TCVN đang theo dõi kèm metadata chuẩn OKF v2.4 |
| `resources/comparison_table.md` | Template bảng so sánh VBPL cũ ↔ mới |
| `resources/impact_report.md` | Template báo cáo tác động thay đổi lên CCBA |
| `resources/notebooklm_prompts.md` | Prompt mẫu cho NotebookLM theo use case |

---

## How to Use

### 1. Cập nhật Registry VBPL (`legal_registry.yaml`)

Đọc file `legal_registry.yaml` tại Root Spoke để nắm danh mục hiện tại. Khi cần cập nhật:
1. **Thêm VBPL/QCVN/TCVN mới**: Thêm entry mới vào nhóm tương ứng (`laws:`, `standards:`) với đầy đủ `bundle_path`, `pdf_path`, `pdf_sha256`, `pdf_status: verified` và khối `source_assets`.
2. **Thay đổi trạng thái**: Cập nhật `status` (`DRAFT` $\rightarrow$ `PENDING_EFFECTIVE` $\rightarrow$ `ACTIVE` $\rightarrow$ `SUPERSEDED` / `PARTIALLY_AMENDED` theo enum `LegalDocStatus`).
3. **Đánh dấu thay thế / hướng dẫn**: Khai báo rõ ràng trong `relations:` (`replaces:`, `guided_by:`).

### 2. Tạo Bảng So Sánh & Hợp Nhất VBPL (`VBHNEngine` CLI & API)

Khi có văn bản sửa đổi bổ sung:

1. Thực thi lệnh hợp nhất AST và sinh ma trận so sánh đồng vị `bang_so_sanh_thay_doi.md` (ADR 0036):
   ```bash
   python -m ccba_legal consolidate \
     --manifest "legal_docs/<category>/<doc_slug>/patch_manifest.yaml" \
     --base "legal_docs/<category>/<doc_slug>/sources/<doc_slug>_goc.md" \
     --output "legal_docs/<category>/<doc_slug>"
   ```
   * **Hoặc sử dụng Python API qua Deep Seam `LegislativeConsolidator` / `VBHNEngine`:**
   ```python
   from ccba_legal import LegislativeConsolidator, VBHNEngine

   # Khởi tạo qua patch manifest đã được biên tập
   consolidator = LegislativeConsolidator.from_manifest_file("patch_manifest.yaml")
   res = consolidator.consolidate("base.md", "output_dir")

   # Hoặc sử dụng VBHNEngine để hợp nhất tài liệu
   engine = VBHNEngine()
   vbhn_doc = engine.merge_documents(base_doc="base.md", amending_doc="patch1.md")
   ```
2. Đọc kết quả diff được chuẩn hóa theo từng chương/điều/khoản (tự động so khớp `D1` $\leftrightarrow$ `dieu-1`).
3. Điền các đánh giá chuyên môn vào template `resources/comparison_table.md`.
4. Xuất file vào thư mục tài liệu đích của dự án.

### 3. Tạo Impact Report

Khi cần đánh giá tác động:
1. Đọc template `resources/impact_report.md`.
2. Xác định các quy trình CCBA bị ảnh hưởng.
3. Phân loại tác động: Cao / Trung bình / Thấp.
4. Đề xuất hành động cần thiết (cập nhật quy trình, đào tạo).
5. Xuất file Markdown và Word (.docx).

### 4. Hướng dẫn NotebookLM

Đọc `resources/notebooklm_prompts.md` để lấy prompt mẫu cho các use case:
- Đọc nhanh VBPL $\rightarrow$ trích xuất điểm chính
- Soạn thảo công văn dựa trên VBPL
- So sánh 2 văn bản trong cùng notebook

---

## ⚠️ Disclaimer

Skill này tạo **tài liệu phân tích VBPL**, KHÔNG phải tư vấn pháp lý. Luôn cần chuyên gia pháp lý xác nhận trước khi áp dụng vào dự án thực.


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/registry_sync_guide.md` | Quy trình đồng bộ định kỳ legal registry và cập nhật cơ sở dữ liệu văn bản pháp lý |

## 5. Rào Chắn Điểm Liệt & Cập Nhật Hiệu Lực Văn Bản (Hard Floor Invariant)
* **TUYỆT ĐỐI KHÔNG** trích dẫn các văn bản quy phạm pháp luật đã hết hiệu lực thi hành hoặc bị thay thế.
* Mọi văn bản trích dẫn bắt buộc phải được đối soát qua lệnh SSOT `python -m ccba_legal query` hoặc thư viện `ccba_legal.registry`, đảm bảo đạt trạng thái hiệu lực chuẩn hóa `ACTIVE` (bao gồm `current`/`active` qua hàm `normalize_doc_status`) và không bị thay thế bởi văn bản khác (các trường bị thay thế `superseded_by`, `replaced_by`, `replaced_by_docs` trống và mã văn bản không nằm trong danh sách thay thế của bất kỳ văn bản kế nhiệm nào). Các văn bản kế nhiệm sở hữu quan hệ thay thế (`supersedes`, `replaces`, `replaced_docs`, `relations.*`) đối với văn bản cũ vẫn hoàn toàn hợp lệ để trích dẫn.
* Mọi vi phạm trích dẫn văn bản hết hiệu lực sẽ bị đánh rớt ngay lập tức (Hard Floor Fail-Fast: 0.0%).
