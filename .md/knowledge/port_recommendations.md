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
<!-- AUTO-GENERATED-END -->

<!-- DEVELOPER-NOTES-START -->
## 📝 Ghi chú của Kỹ sư (Developer Notes)
*Kỹ sư có thể tự do ghi chép các phân tích, đánh giá thủ công tại đây. Phần này sẽ được tự động bảo toàn khi đồng bộ thượng nguồn.*
<!-- DEVELOPER-NOTES-END -->