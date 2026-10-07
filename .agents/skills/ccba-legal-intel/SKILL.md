---
name: ccba-legal-intel
description: Autonomous legal intelligence agent to crawl, diff, and generate compliance
  checklists from Vietnamese legal documents.
bundle: _consulting
tier: kernel
command: /ccba-legal-intel
layer: _consulting
package_path: packages/ccba-legal-intel
metadata:
  version: "1.0.0"
  author: "CCBA Hub"
gpi:
  s: 4.0
  k: 4.0
  a: 4.0
  p: 1.0
triggers:
- ccba-legal-intel
- crawl law
- diff law
- legal checklist
- thuvienphapluat
- TVPL
conforms_to:
- "ADR-0021"
- "ADR-0031"
- "ADR-0034"
- "ADR-0035"
- "ADR-0036"
- "ADR-0037"
- "ADR-0038"
- "ADR-0039"
- "ADR-0040"
- "ADR-0041"
- "ADR-0042"
- "ADR-0050"
---
# Skill: CCBA Legal Intelligence Engine (`ccba-legal-intel`)

Kỹ năng này hướng dẫn Agent phân tích đồ thị quan hệ pháp luật qua Deep Seam **`LegalKnowledgeEngine`** ([`packages/ccba-legal-intel`](../../../packages/ccba-legal-intel)), tra cứu điều khoản, bóc tách bảng ma trận số liệu, thiết lập checklist tuân thủ và xuất bản tài liệu trình chiếu.

---

## 🏛️ Platform-Aware Architecture Posture (ADR-0061)

Skill này thuộc thế năng **`compose-existing`**, tập trung vào phân tích đồ thị quan hệ pháp luật, tra cứu điều khoản và trích xuất tri thức:
* **Thu Thập & Ingestion:** Ủy quyền 100% việc nạp văn bản mới cho Skill Seam [`/ccba-legal-ingest`](../ccba-legal-ingest/SKILL.md) (`legal_ingest.v1`). Tuyệt đối không duy trì sổ tay thu thập trùng lặp.
* **Tra Cứu & Trích Xuất Tri Thức:** Khai thác các Seam hiện có của `ccba_legal` (`LegalKnowledgeEngine`, `get-clause`, `get-table`).

---

## 1. Quy chuẩn & Rào cản Kỹ thuật (Technical Guardrails)

### 1.1. Cấu Trúc Gói Tri Thức Hợp Nhất OKF Bundle v2.4 Universal (ADR 0021, ADR 0034, ADR 0036, ADR 0037, ADR 0041, ADR 0042)
Mỗi văn bản quy phạm pháp luật khi được bóc tách và tra cứu bắt buộc phải đọc từ cấu trúc bundle độc lập với 4 ngăn kéo và Universal `sources/`:
```text
legal_docs/<category_prefix>/<document_slug>/
├── metadata.yaml               # Metadata độc lập (SSOT cấp bundle, lưu pdf_sha256 và source_assets)
├── <document_slug>.md          # Nội dung Markdown thuần sạch 100% nguyên văn (ADR 0037)
├── clauses.json                # Cây điều khoản AST & severity rating
├── index.md                    # Mục lục điều hướng nội bộ 2D
├── sources/                    # Universal sources invariant: chứa bản gốc .docx và .pdf
│   ├── <document_slug>.docx
│   └── <document_slug>.pdf
├── templates/                  # Thư mục biểu mẫu nguyên tử (Atomic Form Templates)
│   └── phu_luc_xx/mau_yy_...md
├── tables/                     # Thư mục chứa bảng dữ liệu tra cứu 2D
│   ├── json/                   # JSON ma trận 2D
│   └── csv/                    # CSV UTF-8 with BOM
├── figures/                    # Thẻ thị giác tính toán tham số hóa (cards/)
└── annexes/                    # Phụ lục kỹ thuật quy phạm (Technical Normative Annexes)
```
* **Quy chuẩn `metadata.yaml`:** Chứa `id`, `document_number`, `type`, `issued_date`, `effective_date`, `pdf_sha256`, `pdf_status: verified`, khối `source_assets`.
* **Cơ chế Khớp nối Hub-Spoke:** Tương thích 100% hai chiều giữa Hub (`packages/ccba-legal-intel`) và Spoke (`legal_registry.yaml`).

### 1.2. Rào Cản Bảo Mật & Giới Hạn Đường Dẫn
*   **Bảo vệ hai tầng chống Path Traversal (CWE-22)**: Khi truy xuất điều khoản hoặc bảng biểu qua CLI/API, hệ thống luôn xác thực đường dẫn tài liệu nằm trong thư mục gốc được phép.
*   **Giới hạn độ dài Slug (Windows MAX_PATH Prevention)**: Độ dài định danh slug tối đa 60 ký tự để bảo đảm an toàn khi đồng bộ liên hệ điều hành.

---


## 2. Ánh xạ Đồ thị Quan hệ Lược đồ (11 nhóm quan hệ)

Khi cào trang Lược đồ (`Tab=LuocDo`), so khớp các tiêu đề mối quan hệ của TVPL:
- `amends_docs`: Văn bản bị sửa đổi bổ sung
- `replaced_docs`: Văn bản bị thay thế
- `referenced_docs`: Văn bản được dẫn chiếu
- `basis_docs`: Văn bản được căn cứ
- `guided_docs`: Văn bản được hướng dẫn
- `consolidated_docs`: Văn bản được hợp nhất
- `guiding_docs`: Văn bản hướng dẫn
- `consolidations`: Văn bản hợp nhất (VBHN)
- `amended_by_docs`: Văn bản sửa đổi bổ sung
- `replaced_by_docs`: Văn bản thay thế
- `related_docs`: Văn bản liên quan cùng nội dung

---

## 3. Hướng dẫn Khai Thác & Ứng Dụng Tri Thức Pháp Lý

> [!NOTE]
> **Phân định ranh giới trách nhiệm (ADR-0059, ADR-0061)**: Toàn bộ quy trình nạp gốc văn bản mới gồm đăng nhập TVPL VIP (`login`), thu thập văn bản (`fetch`), chuyển đổi Word sang OKF v2.4 Bundle (`convert`), hợp nhất VBHN (`consolidate`) và kiểm định 15 Cổng Master CI được quản trị tập trung tại [`/ccba-legal-ingest`](../ccba-legal-ingest/SKILL.md). Kỹ năng `ccba-legal-intel` tập trung vào khai thác đồ thị quan hệ, tra cứu điều khoản/bảng biểu (`query`, `get-clause`, `get-table`), đồng bộ Spoke (`sync`), thiết lập checklist tuân thủ và xuất bản tài liệu trình chiếu.

### 1. Đồng Bộ Dữ Liệu Pháp Lý Về Spoke (1-Click Legal Sync - ADR 0050)
```bash
python -m ccba_legal sync --pull-latest [-o legal_docs] [--doc <doc_id>]
```
Tự động kéo các OKF v2.4 bundles đạt chuẩn từ kho tri thức gốc `ccba-legal-knowledge` (hoặc Cloud Legal Vault) và thực hiện Non-Destructive Additive Merge cho `legal_registry.yaml` tại Spoke.
* **Tiêu chí hoàn thành:** Toàn bộ gói văn bản OKF v2.4 chuẩn được sao chép về Spoke và `legal_registry.yaml` được cập nhật bảo toàn.

### 2. Tra Cứu & Trích Xuất Tri Thức Pháp Lý (LegalKnowledgeEngine CLI & API — ADR 0035, ADR 0050)
* **Tra cứu văn bản và cảnh báo vòng đời:**
  ```bash
  python -m ccba_legal query "Luật Xây dựng"
  ```
* **Trích xuất nguyên vẹn Điều/Khoản với Tier-Aware Semantic Slicing & Alias Parser:**
  ```bash
  python -m ccba_legal get-clause --doc Luat-Xay-dung-2025-135-2025-QH15 --clause d1
  python -m ccba_legal get-clause --doc Luat-Xay-dung-2025-135-2025-QH15 --clause d15k2
  ```
* **Trích xuất bảng ma trận số liệu chuẩn Markdown/CSV:**
  ```bash
  python -m ccba_legal get-table --doc qcvn_06_2022_bxd --table bang_01 --format markdown
  ```
* **Lập trình Python Facade qua `LegalKnowledgeEngine`:**
  ```python
  from ccba_legal import LegalKnowledgeEngine, query
  engine = LegalKnowledgeEngine()
  docs = engine.search("nghị định 105")
  clause = engine.get_clause("Luat-Xay-dung-2025-135-2025-QH15", "d1")
  table = engine.get_table("qcvn_06_2022_bxd", "bang_01", format="markdown")
  ```
* **Tiêu chí hoàn thành:** Truy xuất thành công dữ liệu điều khoản/bảng biểu kèm cảnh báo pháp lý và bảo vệ hai tầng chống CWE-22 Path Traversal.

### 3. Phân Tích Đồ Thị Lược Đồ Quan Hệ & Kiểm Soát Vòng Đời (Graph Intelligence)
Khai thác 11 mối quan hệ lược đồ tại Mục 2 để xây dựng ma trận căn cứ pháp lý:
* Nhận diện văn bản bị thay thế (`replaced_by_docs`) để cảnh báo rủi ro điểm liệt (Hard Floor Invariant).
* Lập bản đồ văn bản hướng dẫn (`guiding_docs`) từ Luật gốc xuống Nghị định và Thông tư thi hành.
* Đối chiếu văn bản hợp nhất (`consolidations`) để bảo đảm tính đồng bộ quy phạm.

### 4. Thiết Lập Checklist Tuân Thủ Dự Án (Compliance Checklist)
* Bóc tách các yêu cầu bắt buộc (mandates) từ các điều khoản đã trích xuất.
* Gắn mã định danh quy phạm (`doc_id` + `clause_id`) vào từng đầu mục kiểm tra.
* Cập nhật trạng thái tuân thủ dự án và liên kết trực tiếp tới file nguồn OKF v2.4 trên Spoke.

### 5. Xuất Bản Trình Chiếu PowerPoint 1-Chạm (Legal-to-PPTX Thin Seam — ADR 0044)
```bash
python -m ccba_legal pptx <input_markdown> -o <output_pptx>
```
Chuyển đổi trực tiếp tài liệu tóm tắt pháp lý (`summary.md` / `concept.md`) sang file trình chiếu PowerPoint `.pptx` chuẩn nhận diện thương hiệu CCBA (Swiss Modernist Design ver 3.4) qua dynamic import `ccba_ooxml`.
* **Tiêu chí hoàn thành:** File presentation `.pptx` được tạo thành công với layout chuẩn thương hiệu CCBA và kích thước hợp lệ.

