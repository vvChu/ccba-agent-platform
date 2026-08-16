# 📋 Đặc Tả Kỹ Thuật (Spec): Triển Khai Hoàn Thiện Ruột 4 Deep Seams Trên CCBA Platform

- **Mã tài liệu**: `SPEC-2026-08-15-DEEP-SEAMS`
- **Tính năng / Chủ đề**: Triển khai hoàn thiện 4 Deep Seams (`QCAuditPipeline`, `VBHNEngine`, `TVPLCrawler`, `ConversionPipeline`)
- **Tham chiếu Quyết định**: [**ADR-0011**](../adr/adr_20260815_224158_chuan_hoa_deep_seams_cho_4_sub_systems_t.md)
- **Phương pháp luận**: Deep Modules & Grey Box Seams (Matt Pocock — *AI Hero*)
- **Trạng thái**: `ready-for-agent`

---

## 1. Problem Statement (Vấn Đề Cần Giải Quyết)

Trước đây, codebase của CCBA Platform bị phân mảnh thành nhiều classes nhỏ lẻ (Shallow Modules) tại 4 hệ thống trọng tâm:
1. **QC Multi-Discipline Pipeline**: Caller phải tự điều phối `QCDiscoveryEngine`, tự crop ma trận bản vẽ Quad-View, tự gọi `QCAuditEngine`, rồi tự chuyển `AuditReport` vào `QCReporterEngine`.
2. **Legal Intel VBHN Engine**: Quy trình hợp nhất văn bản pháp luật bị xé lẻ thành 5 classes (`ASTParser`, `DeltaPatchGenerator`, `VBHNMerger`, `OKFStructureProcessor`, `OKFBundlePackager`).
3. **TVPL VIP Crawler**: Caller phải tự quản lý `CookieVault`, tự tạo `TVPLSessionMutex`, tự mở port CDP, và tự xử lý popups/retry.
4. **Document Conversion Pipeline**: `ConversionPipeline` tách rời khỏi các post-processors (`TableReconstructor`, `FormTemplateCleaner`, `LinkPatcher`), buộc caller phải viết script nối dài nhiều vòng lặp.

Hậu quả là AI Agent mới khởi tạo (vốn không có bộ nhớ dài hạn) phải thực hiện 15-20 tool calls để tìm kiếm, xâu chuỗi các hàm nhỏ lẻ, dẫn đến **kiệt sức nhận thức (cognitive burnout)** và phát sinh lỗi rò rỉ ranh giới phụ thuộc.

---

## 2. Solution (Giải Pháp)

Hiện thực hóa và đóng gói trọn vẹn ruột (implementation) cho **4 Deep Seams** duy nhất:
1. **`QCAuditPipeline`** (`ccba-ai`): Cung cấp hàm `run_audit()` thực hiện trọn gói chuỗi Discovery $\rightarrow$ Quad-View Alignment $\rightarrow$ Multimodal Vision Audit $\rightarrow$ Technical Reporter.
2. **`VBHNEngine`** (`ccba-legal-intel`): Cung cấp hàm `merge_documents()` thực hiện trọn gói AST Parsing $\rightarrow$ Delta Patch Calculation $\rightarrow$ Tree Merge $\rightarrow$ OKF Bundle Packaging.
3. **`TVPLCrawler`** (`ccba-legal-intel`): Cung cấp Facade `fetch_document()` và `search()` tự động quản lý CookieVault, Session Mutex Lock, Anti-bot Popups, Chrome CDP / HTTP fallback và tải file đính kèm.
4. **`ConversionPipeline`** (`mdconverter`): Cung cấp cơ chế All-in-One tự động phát hiện định dạng $\rightarrow$ Engine Selection $\rightarrow$ Tự sửa bảng biểu $\rightarrow$ Khôi phục tiêu đề biểu mẫu $\rightarrow$ Vá link phụ lục $\rightarrow$ Lint cú pháp.

Mỗi Seam chỉ bộc lộ giao diện bề mặt tối giản (Thin Interface), giấu toàn bộ độ phức tạp bên trong, đảm bảo AI Agent chỉ cần đúng 1 lệnh gọi duy nhất.

---

## 3. User Stories (Câu Chuyện Người Dùng)

### 👥 Nhóm 1: Dành cho AI Agent & Automated Pipelines
1. Là một AI Agent thực hiện thẩm tra thiết kế, tôi muốn gọi duy nhất hàm `QCAuditPipeline.run_audit(project_dir)` để nhận được báo cáo thẩm tra hoàn chỉnh mà không cần phải tự crop bản vẽ hay quản lý Coordination Matrix.
2. Là một AI Agent xử lý văn bản pháp luật, tôi muốn gọi hàm `VBHNEngine.merge_documents(base_doc, amending_doc)` để nhận văn bản hợp nhất chuẩn OKF mà không cần phải tự bóc tách từng Node AST.
3. Là một AI Agent thu thập dữ liệu pháp lý, tôi muốn gọi `TVPLCrawler.fetch_document(url_or_id)` để tự động tải văn bản và file đính kèm mà không cần bận tâm về xung đột session hay mã hóa cookie.
4. Là một AI Agent chuyển đổi tài liệu, tôi muốn gọi `ConversionPipeline.convert(path)` để nhận được file Markdown chuẩn sạch (đã sửa bảng, vá link phụ lục và khôi phục tiêu đề) trong một lần gọi duy nhất.

### 👷 Nhóm 2: Dành cho Kỹ sư Thẩm tra & Chuyên viên Pháp lý CCBA
5. Là một Kỹ sư Thẩm tra PCCC/MEP, tôi muốn hệ thống QC tự động phát hiện sai lệch cao độ và xung đột không gian giữa 4 bộ môn Kiến trúc - Kết cấu - MEP - PCCC thông qua hình ảnh Quad-View căn chỉnh tự động.
6. Là một Chuyên viên Pháp lý Xây dựng, tôi muốn xem được bảng thống kê chi tiết các điều/khoản được Sửa đổi, Bổ sung, Bãi bỏ kèm theo văn bản hợp nhất do `VBHNEngine` sinh ra.
7. Là một Kỹ sư Quản trị Dữ liệu, tôi muốn nhiều tiến trình cào dữ liệu cùng lúc không làm khóa tài khoản VIP Thư Viện Pháp Luật nhờ cơ chế Session Mutex tự động trong `TVPLCrawler`.
8. Là một Kỹ sư Soạn thảo Hồ sơ, tôi muốn bảng biểu phức tạp có ô gộp (merged cells) trong tài liệu kỹ thuật Word/PDF được tự động dựng lại thành bảng Markdown phẳng chuẩn xác.

---

## 4. Implementation Decisions (Quyết Định Triển Khai)

### 🏗️ Quyết định 1: Cấu trúc Seam `QCAuditPipeline` (`packages/ccba-ai`)
- Đặt tại `packages/ccba-ai/src/ccba_ai/pipeline.py` và re-export tại `ccba_ai/__init__.py`.
- Interface công khai:
  ```python
  class QCAuditPipeline:
      def __init__(self, ai_client: AIClient | None = None) -> None: ...
      async def run_audit(
          self,
          project_dir: Path | str,
          output_dir: Path | str | None = None,
          disciplines: list[str] | None = None,
      ) -> AuditReportSummary: ...
      def run_audit_sync(
          self,
          project_dir: Path | str,
          output_dir: Path | str | None = None,
          disciplines: list[str] | None = None,
      ) -> AuditReportSummary: ...
  ```

### 📜 Quyết định 2: Cấu trúc Seam `VBHNEngine` (`packages/ccba-legal-intel`)
- Đặt tại `packages/ccba-legal-intel/src/ccba_legal/vbhn_engine.py` và re-export tại `ccba_legal/__init__.py`.
- Interface công khai:
  ```python
  class VBHNEngine:
      def merge_documents(
          self,
          base_doc: str | Path,
          amending_doc: str | Path,
          doc_meta: dict[str, Any] | None = None,
          output_path: Path | None = None,
      ) -> MergedLegalDocument: ...
  ```

### 🕷️ Quyết định 3: Cấu trúc Seam `TVPLCrawler` (`packages/ccba-legal-intel`)
- Đặt tại `packages/ccba-legal-intel/src/ccba_legal/crawler_facade.py` và re-export tại `ccba_legal/__init__.py`.
- Interface công khai:
  ```python
  class TVPLCrawler:
      def __init__(
          self,
          cookie_vault: CookieVault | None = None,
          session_mutex: TVPLSessionMutex | None = None,
      ) -> None: ...
      def fetch_document(
          self,
          doc_url_or_id: str,
          download_attachments: bool = True,
          output_dir: Path | None = None,
      ) -> CrawledLegalDocument: ...
      def search(self, query: str, max_results: int = 10) -> list[dict[str, Any]]: ...
  ```

### 🔄 Quyết định 4: Cấu trúc All-in-One `ConversionPipeline` (`packages/mdconverter`)
- Nâng cấp `packages/mdconverter/src/mdconverter/core/pipeline.py`.
- Tự động kích hoạt `TableReconstructor`, `VNLegalPostProcessor`, `LinkPatcherPostProcessor` và `FormTemplateCleaner` trong chuỗi xử lý mặc định.

---

## 5. Testing Decisions (Quyết Định Kiểm Thử)

1. **Tuân thủ Tiêu chuẩn Kiểm thử Siêu Tốc (Fast SLA < 2s)**:
   - Mọi unit test cho 4 Deep Seams đều được gắn nhãn `pytestmark = [pytest.mark.fast, pytest.mark.unit]`.
   - Sử dụng Mock Objects cho I/O nặng (Mock AIClient, Mock HTTP Provider, Mock Chrome CDP) để đảm bảo thời gian chạy dưới 1 giây.
2. **Kiểm thử Giao diện Bề mặt (External Behavior Only)**:
   - Test suites chỉ gọi qua Public Seams của package (`from ccba_ai import QCAuditPipeline`, `from ccba_legal import VBHNEngine, TVPLCrawler`, `from mdconverter import ConversionPipeline`).
   - Nghiêm cấm test suites gọi trực tiếp vào các file private `_*`.
3. **Danh mục Test Suites Cần Tạo**:
   - `packages/ccba-ai/tests/test_qc_pipeline.py`
   - `packages/ccba-legal-intel/tests/test_vbhn_engine.py`
   - `packages/ccba-legal-intel/tests/test_tvpl_crawler_facade.py`
   - `packages/mdconverter/tests/test_pipeline_all_in_one.py`

---

## 6. Out of Scope (Ngoài Phạm Vi)

- Thay đổi thuật toán tính toán kết cấu hay quy chuẩn kỹ thuật xây dựng (QCVN 06:2022/BXD).
- Triển khai hạ tầng server live hoặc thay đổi hệ thống database backend.
- Thay đổi các dependency bên ngoài (giữ nguyên stack hiện hữu).

---

## 7. Further Notes (Ghi Chú Bổ Sung)

- Đảm bảo toàn bộ mã nguồn mới phải vượt qua rào chắn tĩnh `ruff check` (0 errors), `mypy` strict, và `check_dependency_contracts.py` (5/5 contracts KEPT).
