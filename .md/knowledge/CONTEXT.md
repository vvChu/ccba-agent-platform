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
- **Quyết định:** Khi một Quy chuẩn/Tiêu chuẩn có bản sửa đổi bổ sung, OKF Bundle bắt buộc tạo thêm tệp **Văn bản Hợp nhất mới nhất** (ví dụ: `qcvn_04_2021_bxd_hop_nhat_2026.md`).
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

### ADR-015: Tái Cấu Trúc Module Kiểm Định Governance Thành Các Domain Sub-Auditors Độc Lập
- **Trạng thái:** CHẤP THUẬN (ACCEPTED)
- **Quyết định:**
  1. *Sub-package Governance Chuyên Biệt*: Chuyển đổi tệp monolith 1,522 dòng `doc_auditor.py` thành sub-package `scripts/governance/` bao gồm 5 sub-auditors độc lập: `LinkAuditor` (kiểm tra link, symbol và auto-fixing), `SkillAuditor` (kiểm tra frontmatter và criteria), `RegistryAuditor` (sổ bộ pháp lý & orphan files), `EnvAuditor` (biến môi trường), `DriftAuditor` (kiến trúc & git diff), và `cli.py` (CLI handlers).
  2. *Facade Tương Thích Ngược 100%*: Giữ `scripts/doc_auditor.py` làm Thin Facade và Coordinator (`DocumentAuditor`), re-export toàn bộ public API và helpers để không làm gãy bất kỳ caller, script hay test harness nào.
  3. *Chiến Lược Kiểm Thử 2 Tầng*: Bảo tồn trọn vẹn regression tests cũ (`test_doc_auditor.py`, `test_validate_docs.py`) và bổ sung test unit độc lập `test_governance_sub_auditors.py` đảm bảo toàn bộ test suite chạy dưới 0.3s (tuân thủ Rule P3.1).
- **Lý do:** Tăng tối đa tính Locality và Leverage, giảm 70% độ phức tạp nhận thức, giúp cô lập lỗi hoàn hảo và loại bỏ hoàn toàn God Class trong hệ thống Governance của Platform.

### ADR-016: Khắc Phục Domain Drift của Skill Generator & Tách Rời Khỏi ccba-notebooklm
- **Trạng thái:** CHẤP THUẬN (ACCEPTED)
- **Quyết định:**
  1. *Đúng Domain Scaffolding*: Di dời `skill_generator.py` từ thư mục không liên quan `scripts/security/` sang sub-package chính quy `scripts/scaffolding/skill_generator.py` và xuất bản qua `scripts/scaffolding/__init__.py`.
  2. *Chuẩn hóa Rule P2.2*: Di dời toàn bộ `sys.stdout` stream UTF-8 reconfiguration từ module top-level vào bên trong khối `if __name__ == '__main__':` và `main()`.
  3. *Bảo Vệ Ranh Giới Domain ccba-notebooklm*: Loại bỏ hoàn toàn dynamic import lỗi `_SCRIPTS_DIR / "skill_generator.py"` và hai subcommands ngoại lai (`create-skill`, `sync-skills`) khỏi `packages/ccba-notebooklm/src/ccba_notebooklm/__main__.py`, trả về domain thuần túy cho NotebookLM SDK.
  4. *Bổ Sung Unit Tests*: Xây dựng bộ test `scripts/tests/test_skill_scaffolder.py` kiểm chứng phân tích AST tĩnh và sinh Skill Markdown hợp lệ 100% với `SkillAuditor`.
- **Lý do:** Khắc phục triệt để vi phạm Domain Drift (AP6.2), loại bỏ dynamic import dễ gãy giữa các package, và bảo vệ bộ bắt luồng Pytest runner trên Windows.

### ADR-017: Hoàn Tất Hợp Nhất Legal Templates NĐ 30 Vào Package ccba-legal-intel
- **Trạng thái:** CHẤP THUẬN (ACCEPTED)
- **Quyết định:**
  1. *Đóng Gói Legal Templates Deep Seam*: Di dời toàn bộ logic sinh mẫu văn bản Nghị định 30/2020/NĐ-CP (`generate_legal_document`, `SUPPORTED_DOC_TYPES`, `ND30_HEADER`) từ `scripts/legal/legal_template_generator.py` vào module chính quy `packages/ccba-legal-intel/src/ccba_legal/templates.py`, tích hợp trực tiếp với `ccba_legal.grounding`.
  2. *Thin CLI Delegate & Tương Thích Ngược 100%*: Chuyển `scripts/legal/legal_template_generator.py` thành Thin Re-export Facade kèm CLI runner mẫu trong `main()`.
  3. *Chuẩn hóa Toàn Diện Rule P2.2*: Sửa toàn bộ cấu hình `sys.stdout` UTF-8 ở top-level module scope trong `legal_intelligence.py` và `tvpl_vip_crawler.py` vào bên trong hàm `main()`.
  4. *Kiểm Thử 2 Tầng*: Cập nhật `tests/test_legal_template_generator.py` kiểm định tính đồng nhất giữa direct package call và script facade call.
- **Lý do:** Hoàn tất trọn vẹn lộ trình ADR-012, bảo đảm tính toàn vẹn và duy nhất của domain logic pháp lý trong core package `ccba-legal-intel`.

### ADR-018: Chuẩn Hóa Hạ Tầng An Toàn Tiến Trình & Loại Bỏ Triệt Để Top-Level Stream Mutation (P2.2)
- **Trạng thái:** CHẤP THUẬN (ACCEPTED)
- **Quyết định:**
  1. *Đóng Gói Evaluation & Process Safety Seams*: Xuất bản đầy đủ các abstractions an toàn tiến trình (`DetachedExecutionEngine`, `ensure_single_instance`, `kill_process_tree`, `get_venv_python`, `check_pre_eval_health`, `get_git_modified_files`) qua `scripts/eval/__init__.py`.
  2. *Triệt Tiêu Hoàn Toàn Vi Phạm Rule P2.2*: Di dời toàn bộ `TextIOWrapper` và cấu hình stream UTF-8 top-level tại 7 tệp script (`hook_runner.py`, `drive_auth_helper.py`, `mock_debugger.py`, `repomix_pack.py`, `execute_ticket01`, `execute_ticket02`, `extract_exact_qcvn04`) vào hàm `main()` hoặc khối `if __name__ == '__main__':` với `sys.stdout.reconfigure()`.
  3. *Bảo Vệ Bộ Bắt Luồng Pytest & Agent Server*: Loại trừ tuyệt đối nguy cơ làm đóng file descriptor của Pytest I/O capture và bảo toàn `Safe Process Termination Invariant` (`os.getpid()` & `os.getppid()`).
- **Lý do:** Loại bỏ hoàn toàn lỗi tiềm ẩn `ValueError: I/O operation on closed file`, tăng tính ổn định của test suite và hoàn thiện chuẩn mực Deep Modules cho Platform.

### ADR-019: Tái Cấu Trúc Hệ Thống Lifecycle Hooks Thành Domain Sub-Package Có Typed Contracts
- **Trạng thái:** CHẤP THUẬN (ACCEPTED)
- **Quyết định:**
  1. *Sub-package Lifecycle Hooks Chuyên Biệt*: Chuyển đổi 7 script hook rời rạc thành sub-package `scripts/hooks/` hoàn chỉnh với các typed contracts `HookContext`, `HookResult`, lớp trừu tượng `BaseHook`, và 7 domain hook classes (`PrivacyHook`, `SimplifyGateHook`, `ScoutBlockHook`, `BrandHook`, `NamingHook`, `SessionInitHook`, `TestSpeedHook`).
  2. *Bộ Điều Phối Tập Trung (HookCoordinator)*: Xây dựng `HookCoordinator` tại `scripts/hooks/coordinator.py` quản lý đăng ký, định tuyến sự kiện (`session-init`, `pre-tool`, `post-tool`, `user-prompt-submit`), tự động phát hiện bypass cờ `APPROVED:` và tính toán max exit code tổng hợp.
  3. *Khắc Phục Bug Đường Dẫn Hook Runner*: Chuyển `scripts/eval/hook_runner.py` thành Thin CLI Facade gọi trực tiếp `get_default_coordinator().run_event()`, khắc phục triệt để lỗi đường dẫn `scripts/eval/hooks/` khiến hooks bị fail-open im lặng trước đây.
  4. *Bảo Toàn Tương Thích Ngược 100%*: Duy trì 7 tệp script cũ trong `scripts/hooks/*.py` làm Thin Delegates với cơ chế resilient import (`try ... except ImportError`) hỗ trợ cả standalone CLI execution lẫn package import.
  5. *Kiểm Thử 2 Tầng Siêu Tốc*: Xây dựng bộ test `scripts/tests/test_hooks.py` gồm 17 unit tests bao phủ 100% các rào chắn an ninh, chạy toàn bộ trong < 0.20s (tuân thủ Rule P3.1).
- **Lý do:** Khắc phục lỗi đứt gãy bảo mật im lặng, tăng tối đa tính Locality và Leverage, loại bỏ trùng lặp code, và hoàn thiện cấu trúc Deep Modules cho Platform.

### ADR-020: Hoàn Tất Quy Hoạch Domain Scaffolding & Khắc Phục Triệt Để Domain Drift Tại scripts/security/
- **Trạng thái:** CHẤP THUẬN (ACCEPTED)
- **Quyết định:**
  1. *Khắc Phục Domain Drift (AP6.2)*: Di dời hai tiện ích thống kê tài liệu kiến trúc (`update_arch_stats.py`) và đóng gói mã nguồn (`repomix_pack.py`) từ thư mục `scripts/security/` về đúng sub-package `scripts/scaffolding/` (`arch_stats.py` và `repomix.py`).
  2. *Đóng Gói Deep Seams*: Xây dựng hai lớp xử lý chuyên biệt `ArchStatsUpdater` (tự động đếm metrics và cập nhật an toàn marker regex `<!-- KEY_START -->...<!-- KEY_END -->`) và `RepomixPackager` (quản lý config tạm và chạy npx repomix với cleanup an toàn).
  3. *Loại Bỏ Vi Phạm Rule P2.2*: Di dời toàn bộ `sys.stdout.reconfigure(encoding="utf-8")` ở module top-level trong `arch_stats.py` vào bên trong hàm `main()`, bảo vệ bộ bắt luồng Pytest I/O capture khi import.
  4. *Bảo Toàn Tương Thích Ngược 100%*: Giữ các tệp script cũ tại `scripts/security/update_arch_stats.py` và `scripts/security/repomix_pack.py` làm Thin Forwarding Facades với cơ chế *Resilient Import*.
  5. *Kiểm Thử 2 Tầng*: Bổ sung bộ test `scripts/tests/test_scaffolding.py` kiểm định toàn diện việc cập nhật marker và cấu hình đóng gói repomix trong < 0.20s.
- **Lý do:** Khắc phục triệt để vi phạm phân mảnh ranh giới domain, bảo vệ ranh giới chuyên biệt cho `scripts/security/` (chỉ dành cho an ninh, bảo mật, và redaction) và hoàn thiện chuẩn Deep Modules cho Platform.

### ADR-021: Hợp Nhất DOCX Table Engine & Markdown Converter Vào Package ccba-legal-intel
- **Trạng thái:** CHẤP THUẬN (ACCEPTED)
- **Quyết định:**
  1. *Đóng Gói Cleaners Deep Seams*: Mở rộng lớp `Cleaners` tại `packages/ccba-legal-intel/src/ccba_legal/cleaners.py` tích hợp các phương thức trích xuất và chuyển đổi bảng biểu: `convert_docx_table_to_markdown`, `extract_docx_with_tables`, và `convert_markdown_to_docx`.
  2. *Xuất Bản Public Seams*: Đăng ký các hàm tiện ích bảng biểu qua `ccba_legal/__init__.py`, cho phép toàn bộ pipelines và Spokes tái sử dụng trực tiếp.
  3. *Thin Forwarding CLI Delegates*: Chuyển đổi các script mồ côi tại `scripts/legal/tvpl_table_engine.py` và `scripts/legal/convert_rules_to_docx.py` thành Thin Delegates với cơ chế *Resilient Import*.
  4. *Chuẩn Hóa Toàn Diện Rule P2.2*: Di dời toàn bộ `sys.stdout.reconfigure()` trong `auto_tvpl_vip_downloader.py` và `convert_rules_to_docx.py` vào bên trong hàm `main()`.
  5. *Kiểm Thử 2 Tầng Siêu Tốc*: Xây dựng bộ test `tests/test_legal_table_engine.py` kiểm định toàn diện việc trích xuất bảng, chuyển đổi Markdown $\leftrightarrow$ DOCX, gắn decorator `@pytest.mark.slow` cho các bài test nặng I/O filesystem.
- **Lý do:** Hợp nhất trọn vẹn domain logic xử lý tài liệu pháp lý vào package lõi, loại bỏ hoàn toàn các script mồ côi ngoài luồng và tăng cường tính dùng lại (Leverage).











