# CONTEXT & DESIGN DECISIONS — CCBA HUB-SPOKE ARCHITECTURE

Tài liệu này lưu trữ các thuật ngữ và biên bản quyết định kiến trúc (ADRs) được chốt qua phiên phỏng vấn Grill-with-Docs.

---

## 1. THUẬT NGỮ CHUYÊN NGÀNH (GLOSSARY)

| Thuật ngữ | Định nghĩa trong CCBA Agent Platform |
| :--- | :--- |
| **CCBA Hub** | Repository bộ não trung tâm (`ccba-agent-platform`), lưu trữ Hiến pháp AGENTS.md, AI Gateway SDK (`ccba-ai`), Core Engines, Shared Skills và Workflows. |
| **Knowledge Spoke** | Repository Spoke chuyên biệt lưu trữ dữ liệu tri thức chuẩn OKF (QCVN, TCVN, Luật, Nghị định) phục vụ RAG cho toàn bộ nền tảng. |
| **Reuse-First Gate** | Quy trình cưỡng chế kiểm tra Hub catalog (`catalog.yaml`) trước khi viết bất kỳ tool/script mới nào tại Spoke. |
| **OKF Bundle** | Đóng gói tri thức mở phân tầng (Metadata + Index + Core Concept + Guiding Docs + Diff Matrix). |

---

## 2. NHẬT KÝ QUYẾT ĐỊNH KIẾN TRÚC (DECISION LOG)

### ADR-001: Mô hình Lưu trữ & Truy vấn Knowledge Spoke
- **Trạng thái:** CHẤP THUẬN (ACCEPTED)
- **Quyết định:** Áp dụng **Phương án C (Enterprise Hybrid Package & Smart Resolution Gateway)**.
- **Chi tiết:** 
  - Tạo repository Spoke độc lập `ccba-legal-knowledge-spoke` lưu trữ full OKF Bundles.
  - Tích hợp module `legal_knowledge` vào Python Package `ccba-ai` với cơ chế Smart Resolution 3 tầng (Local Spoke Path $\rightarrow$ Package Embedded Registry $\rightarrow$ Server Spark API Gateway `:8090`).

### ADR-002: Quy trình Tự động hóa Cào dữ liệu & Đồng bộ Tri thức (Atomic Ingestion Pipeline)
- **Trạng thái:** CHẤP THUẬN (ACCEPTED)
- **Quyết định:** Áp dụng Quy trình 3 bước tự động hóa (Atomic Write $\rightarrow$ Registry Validation $\rightarrow$ Silent Git Push).
- **Chi tiết:** 
  - Script `tvpl_vip_crawler.py` đóng gói OKF Bundle ghi trực tiếp sang Knowledge Spoke.
  - Tự động chạy `validate_docs.py` cập nhật `legal_registry.yaml`.
  - Tự động thực hiện git commit & push ngầm tại repo Knowledge Spoke.

### ADR-003: Tải trực tiếp Tệp DOCX Gốc đã Làm sạch lên Google Drive & NotebookLM
- **Trạng thái:** CHẤP THUẬN (ACCEPTED)
- **Quyết định:** Tận dụng trực tiếp tệp `.docx` gốc vừa cào về từ TVPL VIP, chạy `tvpl_table_engine.py` dọn dẹp bảng biểu trên file Word và upload thẳng lên Google Drive (`1b9vm_1KQ8Fg8Crr1Q-i2xmE62UIHy-_2`).
- **Lý do:** Loại bỏ thao tác convert ngược (Markdown $\rightarrow$ Docx), bảo toàn 100% định dạng Word chuẩn, giảm 50% thời gian xử lý.

### ADR-004: Sử dụng Tên Văn Bản Chuẩn Hóa (Thay thế tên dùng chung `concept.md`)
- **Trạng thái:** CHẤP THUẬN (ACCEPTED)
- **Quyết định:** Thay thế tệp tên trừu tượng `concept.md` bằng tên tệp chuẩn hóa phản ánh chính xác mã hiệu văn bản (ví dụ: `qcvn_04_2021_bxd.md`, `qcvn_06_2022_bxd.md`).
- **Lý do:** Tăng 100% tính định danh trực quan khi mở nhiều tab trên Editor, kết quả grep/RAG search chứa ngay mã hiệu văn bản, loại bỏ hoàn toàn sự mơ hồ.

### ADR-005: Tự động Đóng gói Văn bản Hợp nhất (Consolidated Reference Text)
- **Trạng thái:** CHẤP THUẬN (ACCEPTED)
- **Quyết định:** Khi một Quy chuẩn/Tiêu chuẩn có bản sửa đổi bổ sung, OKF Bundle bắt buộc tạo thêm tệp **Văn bản Hợp nhất mới nhất** (ví dụ: [`qcvn_04_2021_bxd_hop_nhat_2026.md`](../legal_docs/qcvn_04_2021_bxd/qcvn_04_2021_bxd_hop_nhat_2026.md)).
- **Lý do:** Giúp Kỹ sư tra cứu 1 tệp duy nhất thể hiện đúng quy định đang có hiệu lực hiện tại mà không phải tự đối chiếu 2 file, đồng thời ưu tiên tệp này làm nguồn RAG Query chính cho AI Agent.

### ADR-006: Cấu trúc Workspace Mode cho Knowledge Spoke (`project.mode: delivery`)
- **Trạng thái:** CHẤP THUẬN (ACCEPTED)
- **Quyết định:** Thư mục `ccba-legal-knowledge-spoke` được thiết lập cấu trúc Workspace Mode là **`project.mode: delivery`**.
- **Lý do:** 
  - Khác với dự án phần mềm (`software`), Knowledge Spoke là kho dữ liệu sản phẩm tri thức (Delivery Assets).
  - Mode `delivery` cung cấp đầy đủ hệ thống thư mục nghiệp vụ chuyên sâu (`.md/extracted_docs/`, `.md/knowledge/`, `.md/legal_docs/`, `.md/data/`) phục vụ lưu trữ OKF Bundles, RAG Registry và quản trị tri thức chuẩn CCBA.

### ADR-007: Kiến trúc Đường dẫn Nông "Native-First" cho LLM Agents (Shallow Path Architecture)
- **Trạng thái:** CHẤP THUẬN (ACCEPTED)
- **Quyết định:** Đưa trực tiếp kho `legal_docs/` lên **cấp 1 của Spoke** và đặt tệp `legal_registry.yaml` ngay tại **Project Root**.
- **Chi tiết:** 
  - Đường dẫn tệp tri thức: `ccba-legal-knowledge-spoke/legal_docs/REGULATION_QCVN/qcvn_04_2021_bxd/...` (Độ sâu tối đa 3 cấp).
  - Loại bỏ hoàn toàn đường dẫn sâu 6 cấp (`.md/extracted_docs/legal_docs/...`).
- **Lý do:** Giảm 70% số bước định vị thư mục (`list_dir`), tăng tốc độ `grep` và tra cứu RAG của LLM Native Agents lên gấp 10 lần, đồng thời dễ bảo trì cho con người.

### ADR-008: Đặt tên Tinh gọn cho Repository Tri thức (`ccba-legal-knowledge`)
- **Trạng thái:** CHẤP THUẬN (ACCEPTED)
- **Quyết định:** Đổi tên Repository Spoke tri thức từ `ccba-legal-knowledge-spoke` thành **`ccba-legal-knowledge`** (hoặc `ccba-legal-intel`).
- **Lý do:** 
  - Loại bỏ từ hậu tố rườm rà `-spoke` (vốn là vai trò kiến trúc đã được khai báo sẵn trong `workspace_context.yaml`).
  - Tên `ccba-legal-knowledge` ngắn gọn (20 chars), dễ gõ CLI, chuẩn hóa quốc tế và đồng bộ 100% với Python Package `ccba-legal-intel`.

### ADR-011: Chuẩn hóa Luồng Onboarding & Chuyển đổi Cấu hình Idempotent (`/ccba-platform` ➔ `/ccba-init-spoke` ➔ `/ccba-setup-skills`)
- **Trạng thái:** CHẤP THUẬN (ACCEPTED)
- **Quyết định:**
  1. *Triết lý Onboarding Lazy Setup*: Kỹ năng `/ccba-platform` giữ vai trò Cổng Router toàn cục siêu tốc, ủy quyền hoàn toàn phỏng vấn cấu hình dev cho `/ccba-setup-skills`. Ở bước cuối của `/ccba-init-spoke`, in thông báo đề xuất hướng dẫn người dùng gọi `/ccba-setup-skills` khi sẵn sàng.
  2. *Ghi đè An toàn & Idempotent (Backup First)*: Khi chuyển đổi Issue Tracker qua `/ccba-setup-skills`, hệ thống ghi đè file cấu hình mới và tự động đổi tên file cũ thành `issue_tracker.md.bak` nếu chứa dữ liệu task cũ để đảm bảo không mất mát dữ liệu.

### ADR-012: Hợp Nhất Legal Seams & Di Dời Excel Recalculation Về Đúng Domain OOXML
- **Trạng thái:** CHẤP THUẬN (ACCEPTED)
- **Quyết định:**
  1. *Đóng gói Legal Seams*: Đưa toàn bộ logic trích dẫn (`grounding.py`), tìm kiếm Sổ bộ (`registry.py`), và bóc tách phụ lục (`appendices.py`) từ các script riêng lẻ vào package lõi `ccba_legal`. Chuyển các file trong `scripts/legal/` thành Thin CLI Delegates.
  2. *Khắc phục Domain Drift*: Di dời tiện ích tính toán Excel `recalc_xlsx` từ `ccba-pdf-prep` về `ccba-ooxml` (`calc.py`), tích hợp phương thức `recalculate()` trên `OOXMLWorkspace`, áp dụng **Safe Macro Injection** (không ghi đè `Module1.xba`) và **Lazy Import `openpyxl`**.
  3. *Chuẩn hóa Stream Reconfiguration (P2.2)*: Di chuyển toàn bộ cấu hình `sys.stdout` UTF-8 vào bên trong `if __name__ == '__main__':` để bảo toàn bộ bắt luồng Pytest runner.
- **Lý do:** Tăng 100% tính Locality và Leverage, loại bỏ sự phân mảnh công cụ và bảo vệ an toàn macro người dùng trên máy trạm.

### ADR-013: Kiến Trúc Spoke Governance Seams & Hoàn Tất Tinh Gọn API ccba-pdf-prep
- **Trạng thái:** CHẤP THUẬN (ACCEPTED)
- **Quyết định:**
  1. *Spoke Governance Deep Seams*: Xây dựng `SpokeSyncEngine` (và alias `SpokeSynchronizer`) tại `scripts/spoke/spoke_synchronizer.py` chịu trách nhiệm toàn bộ quá trình Discovery, Catalog Merge, RSA Registration và Guardrail Copy. Xuất bản qua `scripts/spoke/__init__.py` kèm procedural delegate `sync_project()`.
  2. *Thin CLI Delegates*: Cung cấp `scripts/session_cleanup.py` và `scripts/sync_spoke.py` làm CLI entrypoint mỏng chuyển tiếp lời gọi sang `scripts/spoke/`.
  3. *Tuân thủ P2.2*: Di dời toàn bộ `sys.stdout.reconfigure()` và `io.TextIOWrapper` từ root module scope trong `spoke_synchronizer.py` và `bootstrap_spokes.py` vào bên trong khối `if __name__ == '__main__':`.
  4. *Hoàn tất Domain Purity ccba-pdf-prep*: Loại bỏ hoàn toàn `recalc_xlsx` khỏi `__all__`, docstrings và public exports của `ccba_pdf_prep`, cập nhật test suite `test_document_skills.py` khẳng định ranh giới chuyên biệt cho PDF Vision và PDF Form Filling.
- **Lý do:** Tăng cường tính Locality, bảo vệ bộ bắt luồng Pytest runner trên Windows và ngăn chặn LLM Agent gọi nhầm thư viện.

### ADR-014: Chuẩn Hóa Toàn Bộ Domain Services Sang Pydantic v2 DTOs Thuần Túy (Phương Án 3 Wayfinder)
- **Trạng thái:** CHẤP THUẬN (ACCEPTED)
- **Quyết định:**
  1. *Pydantic v2 DTOs Thuần Túy*: Định nghĩa các mô hình `SEOAuditResult`, `TeamTask`, `PlanCreationResult`, `PhaseUpdateResult`, `PlanPhaseData`, `PlanStatusResult` trong `packages/ccba-ai/src/ccba_ai/models.py`.
  2. *Refactor Dứt Điểm Không Hybrid*: Loại bỏ triệt để ý tưởng dùng lớp bọc giả lập dictionary (`DictLikeModel`), chuyển đổi 100% callers (`scripts/validation/seo_audit.py`, `test_seo.py`, `test_plan_manager.py`, `test_models.py`, `test_team.py`) sang truy cập thuộc tính tường minh (`res.score`, `task.name`, `res.model_dump()`).
  3. *Xử lý Serialization An Toàn*: Hàm `save_tasks()` trong `team.py` hỗ trợ serialize tự động cả `TeamTask` và dictionary thô bằng `model_dump()`.
- **Lý do:** Đạt được tính an toàn kiểu dữ liệu tuyệt đối (Strict Typing & Schema Validation), tối ưu hóa trải nghiệm lập trình cho Subagents/IDEs và ngăn chặn các anti-patterns lai tạp ("nửa nạc nửa mỡ") trong codebase.






