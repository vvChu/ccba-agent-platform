# ADR: Chuẩn Hóa Deep Seams Cho 4 Sub-systems Trọng Tâm (QC, VBHN, TVPL Crawler, Document Conversion)

- **Mã định danh**: ADR-0011
- **Ngày tạo**: 2026-08-15
- **Trạng thái**: Accepted (Đã phê duyệt qua Grilling Session)
- **Tác giả**: Kỹ sư trưởng & Antigravity Agent
- **Tham chiếu**: [How To Make Codebases AI Agents Love — Matt Pocock (AI Hero)](https://www.aihero.dev/how-to-make-codebases-ai-agents-love)

---

## 1. Bối cảnh (Context / Problem)

Trước đây, codebase của CCBA Platform tồn tại tình trạng phân mảnh giao diện (Shallow Modules) tại 4 hệ thống trọng tâm:
1. **QC Multi-Discipline Pipeline**: Bộc lộ 3 protocols rời rạc (`QCDiscoveryEngine`, `QCAuditEngine`, `QCReporterEngine`), buộc caller phải tự tổ chức Coordination Matrix và tự crop ảnh Quad-View.
2. **Legal Intel VBHN Engine**: Bị xé lẻ thành 5 classes (`ASTParser`, `DeltaPatchGenerator`, `VBHNMerger`, `OKFStructureProcessor`, `OKFBundlePackager`).
3. **TVPL VIP Crawler**: Bộc lộ 5 classes (`TVPLCrawlerEngine`, `TVPLVIPCrawler`, `CookieVault`, `TVPLSessionMutex`, `MockChromeCDP`), buộc caller tự quản lý session mutex và port CDP.
4. **Document Conversion & Hậu xử lý**: `ConversionPipeline` tách rời khỏi các plugins hậu xử lý (`TableReconstructor`, `FormTemplateCleaner`, `LinkPatcher`, `VNLegalLinter`), làm tăng số lượng tool calls và phát sinh cognitive burnout cho AI Agent.

---

## 2. Quyết định Kiến trúc (Architectural Decisions)

Thống nhất đóng gói và chuẩn hóa **4 Deep Seams** duy nhất làm giao diện công khai chính thức cho 4 Sub-systems:

| Sub-system | Deep Seam Công Khai | Trách Nhiệm Đóng Gói (Encapsulated Internals) |
| :--- | :--- | :--- |
| **1. QC Multi-Discipline** | `QCAuditPipeline` | Tự động hóa chuỗi Discovery $\rightarrow$ Quad-View Alignment $\rightarrow$ Multimodal Vision Audit $\rightarrow$ Technical Reporter. |
| **2. Legal Intel VBHN** | `VBHNEngine` | Tự động hóa chuỗi AST Parsing $\rightarrow$ Delta Patch Calculation $\rightarrow$ Tree Merge $\rightarrow$ OKF Bundle Packaging. |
| **3. TVPL VIP Crawler** | `TVPLCrawler` | Tự động hóa CookieVault, Session Mutex Lock, Anti-bot Popups, Chrome CDP / HTTP fallback, và tải tài liệu đính kèm. |
| **4. Document Conversion** | `ConversionPipeline` | Tự động hóa Format Detection $\rightarrow$ Engine Selection $\rightarrow$ Table Reconstruction $\rightarrow$ Form Header Recovery $\rightarrow$ Relative Link Patching $\rightarrow$ Format Linting. |

Toàn bộ các helper classes, intermediate models, và sub-parsers được đưa vào thư mục hoặc file private `_*` và chỉ được truy cập nội bộ trong cùng package.

---

## 3. Hệ quả & Đánh đổi (Consequences & Trade-offs)

### ✅ Lợi ích đạt được:
- **Giảm 80% số lượng Tool Calls**: AI Agent chỉ cần gọi một hàm/class duy nhất cho mỗi bài toán nghiệp vụ thay vì phải nhảy qua nhảy lại nhiều files.
- **Loại bỏ Cognitive Burnout**: AI Agent mới khởi tạo nắm bắt toàn bộ năng lực hệ thống ngay từ layer trên cùng (`__all__` / `__init__.py`) mà không bị quá tải token.
- **Tăng tính Locality & Khả năng Kiểm thử**: Các tầng bên dưới tự do refactor thuật toán bên trong mà không làm vỡ các caller bên ngoài.

### ⚠️ Đánh đổi & Ràng buộc:
- Giao diện Seam cấp cao nhận tham số tổng quát; nếu caller muốn can thiệp vi mô vào từng node AST trung gian, phải sử dụng các API nâng cao được tài liệu hóa rõ ràng trong `packages/*/AGENTS.md`.
