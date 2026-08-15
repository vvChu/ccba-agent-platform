# ADR 0038: Chuẩn Hóa Cấu Trúc Gói Tri Thức Hợp Nhất OKF Bundle v2.0 (Unified OKF v2.0 Bundle Specification)

## Bối cảnh (Context)
Trong hệ sinh thái Hub-Spoke của CCBA Platform:
- Hub (`ccba-agent-platform`) trước đây sử dụng `OKFBundlePackager` ghi YAML frontmatter trực tiếp ở đầu tệp Markdown, đồng thời yêu cầu cây AST phả hệ để phục vụ thuật toán hợp nhất văn bản sửa đổi (VBHN Delta Patching).
- Spoke (`ccba-legal-knowledge`) vận hành kho tri thức thực tế (21 văn bản, 3,981 điều khoản) với tệp `.md` thuần sạch, tệp `clauses.json` dạng danh sách phẳng và `qa_benchmark.json` phục vụ đối chuẩn.
- Sự sai khác giữa hai cách tiếp cận làm giảm khả năng phối hợp tự động giữa Hub (Crawler, Conflict Engine, Grounding Gate) và Spoke (Ingestion, Corpus Storage).

Phiên phỏng vấn Socrates dồn dập (`/ccba-grill-with-docs`) ngày 2026-08-15 đã đối soát và hội tụ toàn bộ các quyết định kiến trúc để chuẩn hóa một đặc tả duy nhất: **OKF Bundle v2.0**.

---

## Quyết định Kiến trúc (Decisions)

### 1. Cấu Trúc Thư Mục Chuẩn của OKF Bundle v2.0
Mỗi văn bản quy phạm pháp luật hoặc quy chuẩn kỹ thuật được đóng gói thành một thư mục bundle độc lập:
```text
legal_docs/<category_prefix>/<document_slug>/
├── metadata.yaml               # Metadata chính quy (SSOT cấp bundle)
├── <document_slug>.md          # Nội dung Markdown thuần sạch 100%
├── clauses.json                # Danh mục AST phẳng có thuộc tính phân cấp
├── qa_benchmark.json           # Tập dữ liệu đối chuẩn Ground-Truth QA (5 trường)
├── index.md                    # Mục lục điều hướng nội bộ
└── tables/                     # Thư mục chứa bảng dữ liệu trích xuất
    ├── json/                   # JSON ma trận 2D
    └── csv/                    # CSV UTF-8 with BOM
```

### 2. Đặc Tả Từng Thành Phần Cốt Lõi

#### 2.1. Tệp `metadata.yaml` (Độc lập & SSOT)
Tách biệt hoàn toàn metadata ra tệp YAML độc lập, loại bỏ 100% YAML frontmatter khỏi tệp `.md` để bảo vệ định dạng khi hiển thị và xuất bản:
```yaml
doc_id: "nghi_dinh_217_2026_nd_cp"
doc_number: "217/2026/NĐ-CP"
title: "Nghị định quy định chi tiết một số điều của Luật Xây dựng về quản lý hoạt động xây dựng"
type: "vbpl"
category: "Nghị định"
issuer: "Chính phủ"
issued_date: "2026-06-19"
effective_date: "2026-07-01"
status: "effective"
source_url: "https://thuvienphapluat.vn/..."
sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
```

#### 2.2. Tệp `clauses.json` (Flat Index with Hierarchical Coordinates)
Duy trì dạng danh sách phẳng để tra cứu $O(1)$, bổ sung `node_type` và `parent_id` để tái dựng cây AST trong 1 vòng lặp:
```json
[
  {
    "clause_id": "chuong-1",
    "anchor": "chuong-1",
    "node_type": "chapter",
    "parent_id": null,
    "title": "Chương I: Quy định chung",
    "line_start": 28,
    "line_end": 32
  },
  {
    "clause_id": "dieu-1",
    "anchor": "dieu-1",
    "node_type": "article",
    "parent_id": "chuong-1",
    "title": "Điều 1. Phạm vi điều chỉnh",
    "line_start": 33,
    "line_end": 37
  },
  {
    "clause_id": "dieu-1-khoan-1",
    "anchor": "dieu-1-khoan-1",
    "node_type": "clause",
    "parent_id": "dieu-1",
    "title": "1. Khoản 19 Điều 3 về cơ quan chuyên môn...",
    "line_start": 38,
    "line_end": 40
  }
]
```

#### 2.3. Tệp `qa_benchmark.json` (5 Trường Hỗ Trợ AI Grounding Gate)
Mở rộng tập Ground-Truth QA để phục vụ đối soát ảo giác và kiểm thử RAG tự động:
```json
[
  {
    "question": "Cơ quan nào có thẩm quyền thẩm định Báo cáo nghiên cứu khả thi dự án nhóm A?",
    "answer": "Cơ quan chuyên môn về xây dựng thuộc Bộ quản lý công trình xây dựng chuyên ngành.",
    "anchor": "dieu-14-khoan-2",
    "citation": "Khoản 2 Điều 14 Nghị định 217/2026/NĐ-CP",
    "ground_truth_context": "2. Đối với dự án nhóm A do Thủ tướng Chính phủ quyết định chủ trương đầu tư..."
  }
]
```

---

## Hệ Quả & Đánh Đổi (Consequences)

### Tích cực (Positive)
1. **Khớp nối hoàn hảo 2 chiều:** Hub và Spoke dùng chung 1 hợp đồng dữ liệu duy nhất. Hub `OKFBundlePackager` và Spoke `gold_standard_processor.py` đọc/ghi tương thích 100%.
2. **Hỗ trợ tối đa cho AI Grounding:** Bổ sung `citation` và `ground_truth_context` giúp `LegalGroundingGate` trên Hub kiểm tra tính xác thực của câu trả lời AI một cách tự động và chuẩn xác.
3. **Bảo tồn tính toàn vẹn hiển thị:** Loại bỏ frontmatter giúp file `.md` hiển thị sạch sẽ, chuyên nghiệp trên mọi trình đọc và chuyển đổi sang Word/PDF.

### Thách thức & Kế hoạch Chuyển đổi (Migration Plan)
- Nâng cấp `OKFBundlePackager` trên Hub (`ccba_legal.packager`) và `gold_standard_processor.py` trên Spoke để áp dụng đặc tả v2.0.
- Cập nhật `validate_legal_spoke.py` để bổ sung kiểm tra các trường mới của OKF v2.0.

---
*Ghi nhận bởi CCBA Platform Architecture Board — 2026-08-15*
