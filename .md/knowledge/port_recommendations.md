<!-- AUTO-GENERATED-START -->
# 📋 Upstream Porting Recommendations

Báo cáo tự động đánh giá các tính năng mới từ thượng nguồn. Cập nhật ngày: 2026-07-09 04:49:02
---

### 🟢 [RECOMMEND PORT] Skill: `ask-matt` (Score: 85/100)
*   **Kho chứa nguồn**: `mattpocock-skills`
*   **Đánh giá**: AI Gateway SDK missing - simulated approval
*   **Các bước triển khai**:
    *   Verify manually
    *   Port via ccba-kit
---

### 🟢 [RECOMMEND PORT] Skill: `implement` (Score: 85/100)
*   **Kho chứa nguồn**: `mattpocock-skills`
*   **Đánh giá**: AI Gateway SDK missing - simulated approval
*   **Các bước triển khai**:
    *   Verify manually
    *   Port via ccba-kit
---

### 🟢 [RECOMMEND PORT] Skill: `setup-matt-pocock-skills` (Score: 85/100)
*   **Kho chứa nguồn**: `mattpocock-skills`
*   **Đánh giá**: AI Gateway SDK missing - simulated approval
*   **Các bước triển khai**:
    *   Verify manually
    *   Port via ccba-kit
---

### 🔴 [IGNORE (Đã tồn tại)] Skill: `improve-codebase-architecture` (Score: 25/100)
*   **Kho chứa nguồn**: `mattpocock-skills`
*   **Đánh giá**: Kỹ năng 'improve-codebase-architecture' đã tồn tại sẵn trên local và đã có workflow tương ứng 'ccba-improve-codebase-architecture'. Việc port thêm một phiên bản từ upstream sẽ gây xung đột tên gọi, loãng tài nguyên và tạo ra nợ kỹ thuật không cần thiết.
*   **Các bước triển khai**:
    *   Kiểm tra nội dung của tệp 'improve-codebase-architecture' hiện tại trên local để so sánh với logic mới từ upstream.
    *   Nếu upstream có các cải tiến về hiển thị (HTML report/Mermaid) hoặc logic tư duy tốt hơn, hãy thực hiện 'cherry-pick' các đoạn code đó vào phiên bản hiện tại thay vì ghi đè.
    *   Cập nhật tài liệu hướng dẫn sử dụng (nếu có) của workflow 'ccba-improve-codebase-architecture' để đồng bộ với các tiêu chuẩn thiết kế mới từ upstream.
    *   Loại bỏ các tệp tin thừa từ quá trình thử nghiệm port để giữ cho cấu trúc thư mục sạch sẽ.
---

### 🔴 [IGNORE (Đã tồn tại)] Skill: `to-tickets` (Score: 25/100)
*   **Kho chứa nguồn**: `mattpocock-skills`
*   **Đánh giá**: Kỹ năng 'to-tickets' đã tồn tại trên local và hệ thống hiện có workflow 'ccba-to-tickets'. Việc port thêm một bản sao từ upstream sẽ gây xung đột không gian tên (namespace) và làm loãng cấu trúc quản lý kỹ năng hiện tại. Thay vì port, chúng ta nên đánh giá sự khác biệt giữa phiên bản upstream và bản local hiện tại để thực hiện nâng cấp (refactor) nếu cần thiết.
*   **Các bước triển khai**:
    *   Kiểm tra sự khác biệt về logic giữa tệp SKILL.md của upstream và phiên bản 'to-tickets' hiện có trên local.
    *   Nếu phiên bản upstream có các cải tiến về quy trình (như cách xử lý 'wide refactors' hoặc template mới), hãy áp dụng các thay đổi đó vào kỹ năng 'to-tickets' local thay vì tạo mới.
    *   Rà soát lại workflow 'ccba-to-tickets' để đảm bảo nó đang sử dụng phiên bản kỹ năng tối ưu nhất.
    *   Nếu cần, thực hiện cập nhật tài liệu hướng dẫn (nếu có thay đổi đáng kể trong logic xử lý ticket) thay vì ghi đè bằng kỹ năng mới.
---

### 🔴 [IGNORE (Đã tồn tại)] Skill: `wayfinder` (Score: 25/100)
*   **Kho chứa nguồn**: `mattpocock-skills`
*   **Đánh giá**: Kỹ năng 'wayfinder' đã tồn tại sẵn trong danh sách local skills và workflows của hệ thống. Việc port thêm từ thượng nguồn (upstream) sẽ gây xung đột định danh, làm loãng cấu trúc thư mục và gây khó khăn cho việc quản lý phiên bản (version control). Thay vì port mới, cần đánh giá sự khác biệt giữa phiên bản local hiện tại và phiên bản MattPocock để áp dụng các cải tiến (patching) nếu cần thiết.
*   **Các bước triển khai**:
    *   Kiểm tra nội dung tệp 'wayfinder' hiện có trên local để so sánh với tài liệu SKILL.md từ thượng nguồn.
    *   Nếu phiên bản thượng nguồn có các tính năng ưu việt (như logic phân loại fog-of-war tốt hơn), hãy thực hiện merge các cải tiến đó vào bản local thay vì tạo mới.
    *   Chạy lệnh 'ccba-eval-gate' để đánh giá hiệu năng của 'wayfinder' hiện tại với các case thực tế trong hệ thống.
    *   Cập nhật tài liệu hướng dẫn (nếu cần) để đồng bộ với các quy trình mới từ MattPocock mà không làm thay đổi tên định danh kỹ năng.
---

### 🟡 [UPGRADE/INTEGRATE] Skill: `batch-grill-me` (Score: 30/100)
*   **Kho chứa nguồn**: `mattpocock-skills`
*   **Đánh giá**: Kỹ năng 'batch-grill-me' có sự trùng lặp chức năng cốt lõi với kỹ năng 'grilling' và workflow 'ccba-grill-with-docs' hiện có trong hệ thống. Mặc dù cơ chế 'design tree' và 'batching' của nó rất mạnh mẽ, việc port thêm một kỹ năng phỏng vấn/xác định yêu cầu mới sẽ gây phân mảnh quy trình làm việc (workflow fragmentation). Thay vào đó, kiến trúc nên ưu tiên nâng cấp kỹ năng 'grilling' hiện tại để hỗ trợ tư duy theo 'frontier' và 'design tree' thay vì tạo thêm một thực thể mới.
*   **Các bước triển khai**:
    *   Đánh giá lại kỹ năng 'grilling' hiện tại và xác định các thiếu hụt về khả năng quản lý trạng thái theo 'design tree'.
    *   Tích hợp tư duy 'frontier' (phân loại câu hỏi dựa trên dependencies) vào prompt template của 'grilling' thay vì port 'batch-grill-me'.
    *   Nếu cần thiết, cập nhật 'ccba-grill-with-docs' để hỗ trợ việc dispatch sub-agent tìm kiếm thông tin môi trường thay vì hỏi người dùng.
    *   Bỏ qua (IGNORE) việc port 'batch-grill-me' để giữ cho danh mục kỹ năng hiện tại tinh gọn.
---

### 🟢 [RECOMMEND PORT] Skill: `to-questionnaire` (Score: 85/100)
*   **Kho chứa nguồn**: `mattpocock-skills`
*   **Đánh giá**: Kỹ năng 'to-questionnaire' cung cấp một phương pháp luận chuyên biệt về thu thập tri thức (knowledge extraction) mà hệ thống hiện tại chưa có. Mặc dù chúng ta có 'grilling', 'ask', và 'triage', nhưng các kỹ năng đó tập trung vào việc truy vấn trực tiếp hoặc phân loại, trong khi 'to-questionnaire' tập trung vào việc tạo ra một 'artifact' (tài liệu bảng hỏi) có cấu trúc để làm việc bất đồng bộ (async). Nó bổ trợ hoàn hảo cho các workflow hiện có như 'ccba-research' và 'handoff'.
*   **Các bước triển khai**:
    *   Tạo thư mục mới cho kỹ năng trong cấu trúc quản lý kỹ năng của ccba-agent-platform.
    *   Sao chép nội dung SKILL.md và cấu hình metadata tương ứng vào thư mục mới.
    *   Tích hợp với hệ thống 'platform-loader' để đảm bảo kỹ năng được nhận diện trong môi trường runtime.
    *   Kiểm tra tính tương thích với 'markdown-document-processing' để đảm bảo việc tạo tệp .md đầu ra tuân thủ tiêu chuẩn tài liệu của nền tảng.
    *   Thực hiện thử nghiệm (dry-run) bằng cách kết hợp với workflow 'ccba-research' để kiểm chứng khả năng trích xuất thông tin.
---

### 🔴 [IGNORE (Đã tồn tại)] Skill: `grilling` (Score: 20/100)
*   **Kho chứa nguồn**: `mattpocock-skills`
*   **Đánh giá**: Kỹ năng 'grilling' đã tồn tại trong danh sách local cả dưới dạng skill và workflow (ccba-grill-with-docs). Việc port thêm từ thượng nguồn sẽ gây ra xung đột namespace, dư thừa code và khó khăn trong quản lý phiên bản. Hệ thống hiện tại của chúng ta đã có các thành phần tương đương hoặc mạnh mẽ hơn để thực hiện việc stress-test tư duy.
*   **Các bước triển khai**:
    *   Duy trì phiên bản 'grilling' hiện có trên local để tránh xung đột.
    *   Kiểm tra nội dung tệp SKILL.md của nhánh thượng nguồn để so sánh với phiên bản local hiện tại.
    *   Nếu phiên bản thượng nguồn có cải tiến về logic prompt, hãy thực hiện 'cherry-pick' hoặc cập nhật logic đó vào file local thay vì tạo mới.
    *   Đánh giá xem workflow 'ccba-grill-with-docs' có thể được tối ưu hóa để bao hàm các trigger mới từ thượng nguồn hay không.
---

### 🔴 [IGNORE (Đã tồn tại)] Skill: `domain-modeling` (Score: 25/100)
*   **Kho chứa nguồn**: `mattpocock-skills`
*   **Đánh giá**: IGNORE (Đã tồn tại): Kỹ năng 'domain-modeling' đã tồn tại sẵn trên local catalog.
*   **Các bước triển khai**:
    *   So sánh tệp SKILL.md mới với phiên bản local
    *   Cherry-pick cải tiến nếu cần thay vì port mới
---

### 🔴 [IGNORE] Skill: `code-review` (Score: 20/100) — Reject/Duplicate
*   **Kho chứa nguồn**: `mattpocock-skills` (https://github.com/mattpocock/skills)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0040)**: `Reject/Duplicate` (Bundle: `_core`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Đã tồn tại tương đương trên hệ thống.
*   **Lý do**: IGNORE (Đã tồn tại): Kỹ năng 'code-review' đã tồn tại sẵn trên local catalog.
*   **Các bước triển khai**:
    *   So sánh tệp SKILL.md mới với phiên bản local
    *   Cherry-pick cải tiến quy trình nếu cần thay vì port mới
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia https://github.com/mattpocock/skills code-review --compare`
---

### 🔴 [IGNORE] Skill: `codebase-design` (Score: 20/100) — Reject/Duplicate
*   **Kho chứa nguồn**: `mattpocock-skills` (https://github.com/mattpocock/skills)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0040)**: `Reject/Duplicate` (Bundle: `_core`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Đã tồn tại tương đương trên hệ thống.
*   **Lý do**: IGNORE (Đã tồn tại): Kỹ năng 'codebase-design' đã tồn tại sẵn trên local catalog.
*   **Các bước triển khai**:
    *   So sánh tệp SKILL.md mới với phiên bản local
    *   Cherry-pick cải tiến quy trình nếu cần thay vì port mới
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia https://github.com/mattpocock/skills codebase-design --compare`
---

### 🔴 [IGNORE] Skill: `diagnosing-bugs` (Score: 20/100) — Reject/Duplicate
*   **Kho chứa nguồn**: `mattpocock-skills` (https://github.com/mattpocock/skills)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0040)**: `Reject/Duplicate` (Bundle: `_core`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Đã tồn tại tương đương trên hệ thống.
*   **Lý do**: IGNORE (Đã tồn tại): Kỹ năng 'diagnosing-bugs' đã tồn tại sẵn trên local catalog.
*   **Các bước triển khai**:
    *   So sánh tệp SKILL.md mới với phiên bản local
    *   Cherry-pick cải tiến quy trình nếu cần thay vì port mới
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia https://github.com/mattpocock/skills diagnosing-bugs --compare`
---

### 🟢 [RECOMMEND PORT] Skill: `prototype` (Score: 85/100) — Tier 1
*   **Kho chứa nguồn**: `mattpocock-skills` (https://github.com/mattpocock/skills)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0040)**: `Tier 1` (Bundle: `_core`, `disable-model-invocation: false`)
*   **Đánh giá tương thích Python**: High. The logic of the prototype skill relies on process orchestration and file generation, which are native strengths of Python. The existing 'ccba-prototype' can be refactored to align with the 'throwaway' methodology and strict state-surfacing requirements.
*   **Lý do**: Kỹ năng này cung cấp một framework tư duy (framework-agnostic) mạnh mẽ cho việc phát triển nhanh. Việc tích hợp vào _core giúp chuẩn hóa quy trình ra quyết định kỹ thuật cho toàn bộ hệ thống, tránh việc viết code prototype bừa bãi trong codebase chính.
*   **Các bước triển khai**:
    *   Refactor ccba-prototype theo hướng dẫn của ADR-0040: tích hợp quy trình branch logic (LOGIC.md/UI.md) vào prompt template.
    *   Cấu hình script generator để tự động tạo file README.prototype.md nhằm đánh dấu code là 'throwaway'.
    *   Thêm cơ chế 'State Inspector' để tuân thủ quy tắc 'Surface the state' bằng cách dump state object ra log hoặc console.
    *   Tạo template cho các file prototype (HTML/Python) để đảm bảo tính 'Trivial to run' theo yêu cầu của Skill.
    *   Cập nhật tài liệu hướng dẫn cho team về việc dọn dẹp (cleanup) sau khi prototype hoàn thành.
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia https://github.com/mattpocock/skills prototype --port`
---

### 🟢 [RECOMMEND PORT] Skill: `research` (Score: 85/100) — Tier 1
*   **Kho chứa nguồn**: `mattpocock-skills` (https://github.com/mattpocock/skills)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0040)**: `Tier 1` (Bundle: `_core`, `disable-model-invocation: false`)
*   **Đánh giá tương thích Python**: High. The logic relies on agentic orchestration (background tasks, file I/O, and Markdown generation), which maps perfectly to our existing Python-based agent primitives (LangGraph/PydanticAI) in the monorepo.
*   **Lý do**: Kỹ năng 'research' là một công cụ nền tảng (foundational) có giá trị cao trong việc tự động hóa thu thập tri thức. Nó bổ trợ trực tiếp cho các kỹ năng hiện có như 'ccba-legal-intel' và 'docs-validator'. Do yêu cầu logic phức tạp về truy vấn nguồn tin cậy và xử lý tệp tin, nó phù hợp làm Master Skill trong bundle _core.
*   **Các bước triển khai**:
    *   Khởi tạo module mới trong _core/research bằng cách kế thừa base agent class hiện có.
    *   Tích hợp với 'hybrid-rag-search' để đảm bảo truy xuất nguồn tin cậy (primary sources).
    *   Thiết lập cơ chế 'background agent' sử dụng Celery hoặc Python asyncio để đảm bảo không chặn workflow của người dùng.
    *   Cấu hình logic ghi tệp Markdown tuân thủ theo conventions của monorepo.
    *   Triển khai unit test để kiểm chứng khả năng trích dẫn nguồn (citation verification).
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia https://github.com/mattpocock/skills research --port`
---

### 🔴 [IGNORE] Skill: `resolving-merge-conflicts` (Score: 20/100) — Reject/Duplicate
*   **Kho chứa nguồn**: `mattpocock-skills` (https://github.com/mattpocock/skills)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0040)**: `Reject/Duplicate` (Bundle: `_core`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Đã tồn tại tương đương trên hệ thống.
*   **Lý do**: IGNORE (Đã tồn tại): Kỹ năng 'resolving-merge-conflicts' đã tồn tại sẵn trên local catalog.
*   **Các bước triển khai**:
    *   So sánh tệp SKILL.md mới với phiên bản local
    *   Cherry-pick cải tiến quy trình nếu cần thay vì port mới
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia https://github.com/mattpocock/skills resolving-merge-conflicts --compare`
---

### 🔴 [IGNORE] Skill: `tdd` (Score: 20/100) — Reject/Duplicate
*   **Kho chứa nguồn**: `mattpocock-skills` (https://github.com/mattpocock/skills)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0040)**: `Reject/Duplicate` (Bundle: `_core`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Đã tồn tại tương đương trên hệ thống.
*   **Lý do**: IGNORE (Đã tồn tại): Kỹ năng 'tdd' đã tồn tại sẵn trên local catalog.
*   **Các bước triển khai**:
    *   So sánh tệp SKILL.md mới với phiên bản local
    *   Cherry-pick cải tiến quy trình nếu cần thay vì port mới
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia https://github.com/mattpocock/skills tdd --compare`
---

### 🔴 [IGNORE] Skill: `to-spec` (Score: 20/100) — Reject/Duplicate
*   **Kho chứa nguồn**: `mattpocock-skills` (https://github.com/mattpocock/skills)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0040)**: `Reject/Duplicate` (Bundle: `_core`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Đã tồn tại tương đương trên hệ thống.
*   **Lý do**: IGNORE (Đã tồn tại): Kỹ năng 'to-spec' đã tồn tại sẵn trên local catalog.
*   **Các bước triển khai**:
    *   So sánh tệp SKILL.md mới với phiên bản local
    *   Cherry-pick cải tiến quy trình nếu cần thay vì port mới
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia https://github.com/mattpocock/skills to-spec --compare`
---

### 🔴 [IGNORE] Skill: `triage` (Score: 20/100) — Reject/Duplicate
*   **Kho chứa nguồn**: `mattpocock-skills` (https://github.com/mattpocock/skills)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0040)**: `Reject/Duplicate` (Bundle: `_core`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Đã tồn tại tương đương trên hệ thống.
*   **Lý do**: IGNORE (Đã tồn tại): Kỹ năng 'triage' đã tồn tại sẵn trên local catalog.
*   **Các bước triển khai**:
    *   So sánh tệp SKILL.md mới với phiên bản local
    *   Cherry-pick cải tiến quy trình nếu cần thay vì port mới
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia https://github.com/mattpocock/skills triage --compare`
---

### 🔴 [IGNORE] Skill: `wizard` (Score: 20/100) — Reject/Duplicate
*   **Kho chứa nguồn**: `mattpocock-skills` (https://github.com/mattpocock/skills)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0040)**: `Reject/Duplicate` (Bundle: `_core`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Đã tồn tại tương đương trên hệ thống.
*   **Lý do**: IGNORE (Đã tồn tại): Kỹ năng 'wizard' đã tồn tại sẵn trên local catalog.
*   **Các bước triển khai**:
    *   So sánh tệp SKILL.md mới với phiên bản local
    *   Cherry-pick cải tiến quy trình nếu cần thay vì port mới
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia https://github.com/mattpocock/skills wizard --compare`
---

### 🟢 [RECOMMEND PORT] Skill: `claude-handoff` (Score: 85/100) — Tier 3
*   **Kho chứa nguồn**: `mattpocock-skills` (https://github.com/mattpocock/skills)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0040)**: `Tier 3` (Bundle: `_core`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Cao. Kỹ năng này đóng vai trò như một bộ điều phối tiến trình (process orchestrator), có thể dễ dàng triển khai bằng module 'subprocess' của Python để gọi các lệnh CLI hoặc giao tiếp với AI Gateway SDK hiện có.
*   **Lý do**: Kỹ năng 'claude-handoff' cung cấp giải pháp quản lý ngữ cảnh (context management) hiệu quả cho các tác vụ dài hơi. Vì nó yêu cầu disable-model-invocation (theo thiết kế gốc) và tập trung vào luồng làm việc thủ công của người dùng, nó hoàn toàn phù hợp với Tier 3 trong kiến trúc ADR-0040.
*   **Các bước triển khai**:
    *   Tạo thư mục 'claude-handoff' trong _core bundle.
    *   Triển khai logic xử lý tham số đầu vào để tạo tóm tắt ngữ cảnh (handoff summary).
    *   Tích hợp với 'ai-gateway-sdk' để gửi yêu cầu khởi chạy agent nền (background agent) thay vì gọi trực tiếp CLI bên ngoài nếu có thể.
    *   Thiết lập cơ chế kiểm tra tính bảo mật (redaction) để đảm bảo không có thông tin nhạy cảm được đưa vào prompt của agent mới.
    *   Cập nhật tài liệu hướng dẫn sử dụng cho người dùng cuối về cách quản lý các background agents.
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia https://github.com/mattpocock/skills claude-handoff --port`
---

### 🟢 [RECOMMEND PORT] Skill: `implement-spec` (Score: 85/100) — Tier 3
*   **Kho chứa nguồn**: `mattpocock-skills` (https://github.com/mattpocock/skills)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0040)**: `Tier 3` (Bundle: `_software`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: High compatibility. The logic relies on task orchestration and Git CLI operations, which can be seamlessly implemented using Python's subprocess module, GitPython or PyGit2, and standard concurrent.futures for subagent management.
*   **Lý do**: Kỹ năng 'implement-spec' cung cấp một quy trình làm việc (workflow) có cấu trúc cao để xử lý task graph, phù hợp với tiêu chí Tier 3. Nó không yêu cầu suy luận mô hình trực tiếp mà tập trung vào điều phối (orchestration), tương thích tốt với các công cụ quản lý code hiện có trong bundle _software.
*   **Các bước triển khai**:
    *   Tạo mới thư mục skill 'implement-spec' trong _software bundle.
    *   Triển khai logic điều phối task graph bằng Python, sử dụng cấu trúc dữ liệu đồ thị để xác định frontier của các tickets.
    *   Tích hợp với module 'code-review' hiện có để tự động hóa bước kiểm tra PR.
    *   Cấu hình cơ chế quản lý Git worktree cho các subagent để đảm bảo tính cô lập và đồng thời.
    *   Viết tài liệu hướng dẫn cấu trúc tệp tin spec và ticket để người dùng cuối tuân thủ đúng định dạng đầu vào.
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia https://github.com/mattpocock/skills implement-spec --port`
---

### 🔴 [IGNORE] Skill: `loop-me` (Score: 20/100) — Reject/Duplicate
*   **Kho chứa nguồn**: `mattpocock-skills` (https://github.com/mattpocock/skills)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0040)**: `Reject/Duplicate` (Bundle: `_core`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Đã tồn tại tương đương trên hệ thống.
*   **Lý do**: IGNORE (Đã tồn tại): Kỹ năng 'loop-me' đã tồn tại sẵn trên local catalog.
*   **Các bước triển khai**:
    *   So sánh tệp SKILL.md mới với phiên bản local
    *   Cherry-pick cải tiến quy trình nếu cần thay vì port mới
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia https://github.com/mattpocock/skills loop-me --compare`
---

### 🔴 [IGNORE] Skill: `setup-ts-deep-modules` (Score: 20/100) — Reject/Duplicate
*   **Kho chứa nguồn**: `mattpocock-skills` (https://github.com/mattpocock/skills)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0040)**: `Reject/Duplicate` (Bundle: `_core`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Đã tồn tại tương đương trên hệ thống.
*   **Lý do**: IGNORE (Đã tồn tại): Kỹ năng 'setup-ts-deep-modules' đã tồn tại sẵn trên local catalog.
*   **Các bước triển khai**:
    *   So sánh tệp SKILL.md mới với phiên bản local
    *   Cherry-pick cải tiến quy trình nếu cần thay vì port mới
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia https://github.com/mattpocock/skills setup-ts-deep-modules --compare`
---

### 🟢 [RECOMMEND PORT] Skill: `writing-beats` (Score: 85/100) — Tier 3
*   **Kho chứa nguồn**: `mattpocock-skills` (https://github.com/mattpocock/skills)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0040)**: `Tier 3` (Bundle: `_consulting`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Cao. Kỹ năng này chủ yếu xử lý logic luồng (workflow) và thao tác tệp tin (I/O), vốn là thế mạnh của Python. Việc chuyển đổi từ mô tả Markdown sang logic Python class là rất khả thi.
*   **Lý do**: Kỹ năng 'writing-beats' tập trung vào phương pháp luận biên soạn nội dung có cấu trúc (choose-your-own-adventure). Do tính chất tương tác cao, yêu cầu người dùng lựa chọn từng bước và không bắt buộc gọi LLM tự động (đã có cờ disable-model-invocation: true trong tài liệu), nó phù hợp hoàn hảo với Tier 3 (User Workflow). Nó bổ trợ tốt cho gói _consulting hiện có.
*   **Các bước triển khai**:
    *   Tạo thư mục skill tại ccba-agent-platform/skills/writing-beats.
    *   Triển khai logic điều phối (orchestrator) bằng Python để quản lý state 'grounded concepts' và tệp tin markdown.
    *   Xây dựng CLI hoặc giao diện tương tác để người dùng chọn 'beats' theo từng bước.
    *   Tích hợp với file-stability-guard để đảm bảo tính nhất quán của tệp tin đầu ra.
    *   Viết tài liệu hướng dẫn sử dụng theo chuẩn ADR-0040 cho người dùng cuối.
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia https://github.com/mattpocock/skills writing-beats --port`
---

### 🟢 [RECOMMEND PORT] Skill: `retro` (Score: 85/100) — Tier 3
*   **Kho chứa nguồn**: `mattpocock-skills` (https://github.com/mattpocock/skills)
*   **Bản quyền**: `MIT License (Tự do sử dụng)`
*   **Phân tầng đề xuất (ADR-0040)**: `Tier 3` (Bundle: `_core`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Rất cao. Kỹ năng này chủ yếu dựa trên logic phân tích văn bản và workflow điều phối, không phụ thuộc vào thư viện bên thứ ba đặc thù, dễ dàng tích hợp vào hệ thống file-based của Monorepo.
*   **Lý do**: Kỹ năng 'retro' cung cấp khung tư duy (framework) quan trọng cho việc cải tiến quy trình làm việc của agent. Vì nó dựa trên việc phân tích session logs và tư vấn người dùng, việc đặt ở Tier 3 với 'disable-model-invocation: true' là phù hợp nhất để tránh tiêu tốn token không cần thiết khi agent tự chạy retro. Nó bổ trợ tốt cho 'session_retrospective' hiện có bằng cách cung cấp các hạng mục đánh giá cụ thể (Navigation, Tool economy, v.v.).
*   **Các bước triển khai**:
    *   Tạo mới module 'retro' trong thư mục _core/skills/retro.
    *   Chuyển đổi nội dung SKILL.md thành định dạng tài liệu nội bộ của ccba-agent-platform.
    *   Tích hợp với hệ thống log hiện tại của 'session_retrospective' để đảm bảo tính nhất quán về dữ liệu.
    *   Cập nhật README của bundle _core để làm rõ sự khác biệt giữa 'retro' (phân tích quy trình) và 'session_retrospective' (tổng kết nội dung).
    *   Thiết lập cơ chế kiểm tra (sanity check) để đảm bảo không xung đột với các chỉ dẫn trong AGENTS.md hiện tại.
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia https://github.com/mattpocock/skills retro --port`

---

### 🟢 [RECOMMEND PORT] Skill: `ab-test-setup` (Score: 80/100) — Tier 3: Composite Orchestrator
*   **Kho chứa nguồn**: `marketing` (https://github.com/claudekit/claudekit-marketing)
*   **Bản quyền**: `Bản quyền đóng (Không được sao chép)`
*   **Phân tầng đề xuất (ADR-0057)**: `Tier 3: Composite Orchestrator` (Bundle: `_software`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Cần địa hóa sang môi trường Python / Ruff / PyTest.
*   **Lý do**: Kỹ năng mới chưa có trên catalog (PROPRIETARY). Định tuyến: Cổng 1 (Orchestration Gate): Tác vụ có điều phối nhiều tác tử song song, chuyển trạng thái StateGraph checkpoints hoặc cần con người phê duyệt (HITL). Bắt buộc triển khai tại Tầng 3 (Composite Orchestrator).
*   **Các bước triển khai**:
    *   Chạy lệnh `/ccba-xia .md/scratch/repos/claudekit-marketing ab-test-setup --compare` để trinh sát
    *   Định tuyến tới Tầng 3: Composite Orchestrator (.agents/workflows/) theo ADR-0057
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia .md/scratch/repos/claudekit-marketing ab-test-setup --port`

---

### 🟢 [RECOMMEND PORT] Skill: `ai-artist` (Score: 80/100) — Tier 2A: Progressive Reference (GPI: 5.00)
*   **Kho chứa nguồn**: `marketing` (https://github.com/claudekit/claudekit-marketing)
*   **Bản quyền**: `Bản quyền đóng (Không được sao chép)`
*   **Phân tầng đề xuất (ADR-0057)**: `Tier 2A: Progressive Reference` (Bundle: `_software`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Cần địa hóa sang môi trường Python / Ruff / PyTest.
*   **Lý do**: Kỹ năng mới chưa có trên catalog (PROPRIETARY). Định tuyến: Chỉ số GPI (5.00) < 12.0. Phân loại: Tier 2A (Progressive Reference). Cần lưu trữ dưới dạng tài liệu tham chiếu trong references/*.md của Master Skill 'codebase-design'; cảnh báo/từ chối tạo thư mục Skill độc lập.
*   **Các bước triển khai**:
    *   Chạy lệnh `/ccba-xia .md/scratch/repos/claudekit-marketing ai-artist --compare` để trinh sát
    *   Định tuyến tới references/ai-artist.md (của Master Skill 'codebase-design') theo ADR-0057
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia .md/scratch/repos/claudekit-marketing ai-artist --port`

---

### 🟢 [RECOMMEND PORT] Skill: `competitor-alternatives` (Score: 80/100) — Tier 2A: Progressive Reference (GPI: 5.00)
*   **Kho chứa nguồn**: `marketing` (https://github.com/claudekit/claudekit-marketing)
*   **Bản quyền**: `Bản quyền đóng (Không được sao chép)`
*   **Phân tầng đề xuất (ADR-0057)**: `Tier 2A: Progressive Reference` (Bundle: `_software`, `disable-model-invocation: true`)
*   **Đánh giá tương thích Python**: Cần địa hóa sang môi trường Python / Ruff / PyTest.
*   **Lý do**: Kỹ năng mới chưa có trên catalog (PROPRIETARY). Định tuyến: Chỉ số GPI (5.00) < 12.0. Phân loại: Tier 2A (Progressive Reference). Cần lưu trữ dưới dạng tài liệu tham chiếu trong references/*.md của Master Skill 'codebase-design'; cảnh báo/từ chối tạo thư mục Skill độc lập.
*   **Các bước triển khai**:
    *   Chạy lệnh `/ccba-xia .md/scratch/repos/claudekit-marketing competitor-alternatives --compare` để trinh sát
    *   Định tuyến tới references/competitor-alternatives.md (của Master Skill 'codebase-design') theo ADR-0057
> ⚡ **Lệnh kích hoạt Port 1-Click:** `/ccba-xia .md/scratch/repos/claudekit-marketing competitor-alternatives --port`
<!-- AUTO-GENERATED-END -->

<!-- DEVELOPER-NOTES-START -->
## 📝 Ghi chú của Kỹ sư (Developer Notes)
*Kỹ sư có thể tự do ghi chép các phân tích, đánh giá thủ công tại đây. Phần này sẽ được tự động bảo toàn khi đồng bộ thượng nguồn.*
<!-- DEVELOPER-NOTES-END -->