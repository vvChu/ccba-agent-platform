# ADR 0037: Constitution-Driven Traceability Matrix Pattern & Dynamic Knowledge Pointers

## Status
**Accepted** (Ban hành: 2026-08-15)

## Bối cảnh (Context)
Trong các dự án kỹ thuật, tư vấn xây dựng và chuyển đổi số (như `IDOP-CCBA-WAY`), mức độ phức tạp của các quy định pháp lý (QCVN, TCVN, Luật Xây dựng) và quy chế nội bộ (`QCTK 2815`, `QCCTNB 3209`, `CCBA Charter 2026`) là rất cao.
Trước đây, các đặc tả kỹ thuật (Specs) và User Stories thường chỉ trích dẫn văn bản pháp quy một cách lỏng lẻo hoặc phân tán trong văn bản mô tả, dẫn đến:
1. **Mất dấu vết tuân thủ (Compliance Drift):** Khi quy chế hoặc luật thay đổi, rất khó xác định các module hay SharePoint list nào bị ảnh hưởng.
2. **Nguy cơ nhân bản dữ liệu (Data Duplication):** Xu hướng copy các file quy chế toàn văn từ Spoke sang Hub gây ra tình trạng đa nguồn chân lý (Multiple Sources of Truth), làm lệch pha tri thức khi có bản sửa đổi.

## Quyết định Kiến trúc (Architectural Decision)
CCBA Platform chính thức ban hành 2 mẫu hình kiến trúc bắt buộc cho toàn hệ sinh thái Hub-Spoke:

### 1. Ma Trận Truy Vết Thể Chế 2 Chiều (`Constitution-Driven Traceability Matrix`)
Mọi dự án Spoke có độ phức tạp cao về mặt quản trị bắt buộc phải thiết lập tệp tin cấu hình **`.md/cross_references.yaml`**.
Tệp này đóng vai trò là cầu nối số hóa giữa:
- **Tầng Thể chế (`.md/governance_constitution/`):** Từng Điều, Khoản, Phụ lục của các quy chế pháp lý.
- **Tầng Đặc tả Kỹ thuật (`specs/modules/`):** Từng Feature Spec, User Story, Acceptance Criteria.
- **Tầng Thiết kế Hệ thống (`.md/system_blueprint/` hoặc Data Schemas):** SharePoint Lists, Entity Models.

#### Cấu trúc Chuẩn hóa của `cross_references.yaml`:
```yaml
metadata:
  project: <PROJECT_NAME>
  milestone: <MILESTONE>
  total_spec_modules: <COUNT>
  total_mapped_references: <COUNT>
modules:
  - module_id: <DOMAIN_SUBMODULE>
    domain: <DOMAIN>
    spec_file: specs/modules/<path>/spec.md
    spec_title: <TITLE>
    governance_constitution_references:
      - document: <DOC_FILE>
        document_title: <DOC_TITLE>
        article_clause: <ARTICLE_CLAUSE>
        section_context: <CONTEXT>
        topic: <TOPIC>
        excerpt: <EXCERPT>
    system_blueprint_references:
      - document: <BLUEPRINT_FILE>
        section: <SECTION>
```

### 2. Cơ Chế Con Trỏ Tri Thức Động (`Dynamic Knowledge Pointer`)
Hub `ccba-agent-platform` tuyệt đối **không sao chép nội dung văn bản thể chế nội bộ** từ các Spoke về Hub.
Thay vào đó, Hub chỉ duy trì các con trỏ đường dẫn động trong `catalog.yaml`:
```yaml
knowledge:
  - name: ccba_operations_kb
    description: Thể chế Quản lý Dự án (QCTK 2815), Chi tiêu Nội bộ (QCCTNB 3209) & Điều lệ CCBA 2026
    knowledge_path: '[idop_path]/.md/INDEX.md'
    cross_references: '[idop_path]/.md/cross_references.yaml'
    constitution_root: '[idop_path]/.md/governance_constitution/'
    blueprint_root: '[idop_path]/.md/system_blueprint/'
```
* Nguyên tắc: **Spoke là Nguồn Sự Thật Duy Nhất (SSOT) cho thể chế và dữ liệu nội bộ của nó. Hub cung cấp khả năng khám phá (Discovery) và Điều phối (Orchestration).**

## Hệ quả & Lợi ích (Consequences & Benefits)
* **Khả năng kiểm toán 100% (100% Auditability):** Bất kỳ trường dữ liệu hay logic nghiệp vụ nào cũng có thể truy vết ngược về điều khoản quy chế gốc trong < 1 giây.
* **0% Trùng lặp dữ liệu (Zero Duplication):** Cập nhật quy chế tại 1 nơi duy nhất (`D:\idop-ccba-way`), toàn bộ AI Agents trong hệ thống tự động nắm bắt dữ liệu mới nhất.
* **Tái sử dụng cho mọi Spoke:** Mẫu hình này có thể áp dụng cho Spoke Tư vấn Giám sát, Thẩm tra PCCC, BIM Management.
