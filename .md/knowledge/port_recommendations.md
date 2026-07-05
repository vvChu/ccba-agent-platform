# 📋 Upstream Porting Recommendations

Báo cáo tự động đánh giá các tính năng mới từ thượng nguồn. Cập nhật ngày: 2026-07-04 09:03:48

## 📋 Báo Cáo Nghiên Cứu và Đánh Giá Chuyển Dịch (Upstream Porting Recommendations)

*Tài liệu nghiên cứu so sánh và đánh giá toàn diện việc chuyển dịch (porting) các kỹ năng từ kho chứa `mattpocock/skills` vào hệ thống CCBA Agent Platform.*

---

## 1. Tổng Quan Nghiên Cứu (Recon Summary)

Kho chứa `mattpocock/skills` cung cấp các kỹ năng (Skills) và quy trình (Workflows) mẫu được thiết kế tối ưu cho AI Agent (đặc biệt là Claude Code). Triết lý cốt lõi của các kỹ năng này là **"A Philosophy of Software Design"** (John Ousterhout), tập trung vào việc hướng dẫn Agent thiết kế các module sâu (deep modules), giảm thiểu phình to ngữ cảnh (context bloating), và tương tác chặt chẽ với người dùng qua cơ chế phỏng vấn liên tục (grilling).

Qua trinh sát cấu trúc dự án nguồn, chúng tôi phân loại thành các nhóm kỹ năng chính phù hợp với CCBA Agent Platform và tiến hành đánh giá toàn diện để chuẩn bị sẵn sàng cho việc bổ sung trong tương lai.

---

## 2. Đánh Giá Toàn Diện Các Nhóm Kỹ Năng (Comprehensive Skills Evaluation)

### Lớp 1: Engineering Skills (Kỹ năng Lập trình & Kiến trúc)
Tập trung vào phát triển, kiểm thử, rà soát và cấu trúc codebase.

| Tên Kỹ Năng | Mô Tả & Mục Tiêu | Đánh Giá Độ Hữu Dụng Với CCBA | Đề Xuất Porting |
| :--- | :--- | :--- | :---: |
| `improve-codebase-architecture` | Quét codebase tìm "module nông", xuất báo cáo HTML visual (Mermaid + Tailwind) và thảo luận cải tiến với user. | **Cực kỳ hữu ích (P0).** Hỗ trợ đắc lực cho Agent khi refactor platform hoặc các ứng dụng Spoke của khách hàng. | **PORT (Pha 1)** |
| `codebase-design` | Hướng dẫn Agent thiết kế các module sâu, xác định seam (mối nối), adapter và đảm bảo locality. | **Hữu ích (P1).** Làm cẩm nang kiến trúc phần mềm cho Agent khi thiết kế chức năng mới. | **PORT (Pha 2)** |
| `diagnosing-bugs` | Vòng lặp chẩn đoán lỗi sâu và regression cho các bug khó. | **Hữu ích (P1).** Có thể tích hợp trực tiếp để nâng cấp hệ thống `mock_debugger.py` hiện có. | **PORT (Pha 2)** |
| `domain-modeling` | Xây dựng và duy trì Domain Model và Ubiquitous Language trong `CONTEXT.md` và ADRs. | **Hữu ích (P2).** Giúp Agent bám sát ngôn ngữ nghiệp vụ của dự án xây dựng/BIM. | **PORT (Pha 3)** |
| `resolving-merge-conflicts` | Hướng dẫn Agent giải quyết xung đột Git merge/rebase một cách an toàn. | **Hữu ích (P2).** Rất cần thiết cho các Agent daemon tự động chạy CI/CD hoặc đồng bộ code. | **RESERVE** |
| `tdd` | Quy trình Test-Driven Development (Red-Green-Refactor). | **Trung bình (P2).** Thích hợp khi Agent viết các tính năng/scripts phức tạp cần bảo đảm kiểm thử. | **RESERVE** |
| `to-issues` / `to-prd` | Chuyển đổi cuộc hội thoại thành Issue/PRD trên Issue Tracker. | **Thấp (P3).** Quy trình lập kế hoạch (`implementation_plan.md`) hiện tại của CCBA đã làm tốt việc này. | **IGNORE** |
| `triage` | Điều phối Issues/PRs qua bộ lọc phân loại và viết brief cho Agent. | **Thấp (P3).** Phù hợp với các dự án mã nguồn mở quy mô lớn, chưa cần cho CCBA. | **IGNORE** |
| `ask-matt` | Router điều hướng người dùng đến skill phù hợp trong repo. | **Không cần thiết.** CCBA đã có `platform-loader` tự động điều phối các workflow. | **IGNORE** |

---

### Lớp 2: Productivity Skills (Kỹ năng Giao tiếp & Hiệu suất)
Tập trung tối ưu hóa giao tiếp Agent-User và quản lý trạng thái phiên làm việc.

| Tên Kỹ Năng | Mô Tả & Mục Tiêu | Đánh Giá Độ Hữu Dụng Với CCBA | Đề Xuất Porting |
| :--- | :--- | :--- | :---: |
| `handoff` | Đóng gói phiên làm việc thành tài liệu handoff nhỏ gọn để chuyển tiếp cho Agent tiếp theo. | **Cực kỳ hữu ích (P1).** Giúp tiết kiệm token và tăng tốc độ xử lý khi chuyển giao context. | **PORT (Pha 2)** |
| `grill-me` / `grilling` | Phỏng vấn người dùng một cách dồn dập (từng câu một) để stress-test kế hoạch thiết kế. | **Hữu ích (P2).** Tăng chất lượng alignment giữa Agent và Kỹ sư trước khi viết code lớn. | **PORT (Pha 3)** |
| `teach` | Hướng dẫn người dùng học một khái niệm hoặc kỹ năng mới trong workspace. | **Thấp (P3).** Ít ứng dụng thực tế trong môi trường sản xuất của CCBA. | **IGNORE** |
| `writing-great-skills` | Cẩm nang viết các file `SKILL.md` hiệu quả và dễ đoán. | **Hữu ích (P2).** Làm tài liệu tham khảo cho kỹ sư khi muốn đóng gói Skill mới lên Hub. | **RESERVE** |

---

### Lớp 3: In-Progress & Misc Skills (Kỹ năng Đang Phát triển & Tiện ích Khác)

| Tên Kỹ Năng | Mô Tả & Mục Tiêu | Đánh Giá Độ Hữu Dụng Với CCBA | Đề Xuất Porting |
| :--- | :--- | :--- | :---: |
| `wayfinder` | Vạch đường qua các bài toán mù mờ, chia nhỏ thành các điều tra con và giải quyết dần. | **Rất triển vọng (P1).** Giúp Agent giải quyết các yêu cầu nghiên cứu lớn/mơ hồ của người dùng. | **PORT (Pha 3)** |
| `wizard` | Tạo script wizard tương tác chạy bash để dẫn dắt con người thiết lập môi trường, điền `.env`... | **Hữu ích (P2).** Cực tốt cho việc viết script bootstrap dự án Spoke hoặc bàn giao cài đặt. | **PORT (Pha 3)** |
| `git-guardrails-claude-code` | Cài đặt hooks chặn các lệnh git nguy hiểm (push, reset --hard, clean) trước khi chạy. | **Hữu ích (P2).** Giúp bảo vệ an toàn cho Agent khi chạy lệnh git tự động trong workspace của user. | **RESERVE** |
| `writing-beats` / `writing-shape` | Kỹ năng viết bài báo, cấu trúc đoạn văn, bài luận theo hành trình. | **Thấp (P3).** CCBA đã có skill `long-form-writer` mạnh mẽ cho tài liệu kỹ thuật/VBPL. | **IGNORE** |
| `migrate-to-shoehorn` | Tool di chuyển test file sang TypeScript shoehorn. | **Không áp dụng.** Chỉ dùng cho stack TypeScript chuyên biệt của tác giả Matt Pocock. | **IGNORE** |
| `scaffold-exercises` | Tạo cấu trúc bài tập cho các khóa học của Total TypeScript. | **Không áp dụng.** Chỉ phục vụ mục đích dạy học của tác giả. | **IGNORE** |
| `setup-pre-commit` | Cài đặt Husky pre-commit hooks + linting trong repo. | **EXISTS.** CCBA đã có sẵn cấu hình pre-commit chuẩn trong repo gốc. | **IGNORE** |

---

### Lớp 4: Deprecated & Personal Skills (Kỹ năng Đã lỗi thời & Cá nhân)

*   `design-an-interface` (Deprecated): Thay thế bởi `codebase-design`. (**IGNORE**)
*   `ubiquitous-language` (Deprecated): Thay thế bởi `domain-modeling`. (**IGNORE**)
*   `qa` & `request-refactor-plan` (Deprecated): Thay thế bởi các quy trình triage/implement mới. (**IGNORE**)
*   `obsidian-vault`: Quản lý ghi chú cá nhân bằng Obsidian. Không thuộc phạm vi CCBA Platform. (**IGNORE**)
*   `edit-article`: Chỉnh sửa bài viết cá nhân. (**IGNORE**)

---

## 3. Câu Hỏi Phản Biện Cốt Lõi Khi Tích Hợp Hệ Thống (Challenge Framework)

Để đảm bảo việc chuyển dịch không gây rủi ro phá vỡ hệ thống hiện tại, chúng tôi thiết lập 5 câu hỏi phản biện dưới đây:

### Q1: Việc xuất báo cáo kiến trúc bằng HTML tự mở (`improve-codebase-architecture`) có tương thích tốt trên Windows?
*   **Cách của nguồn:** Chạy lệnh `start <path>` trên Windows để mở file HTML tạm từ thư mục temp.
*   **Cách của CCBA:** Chúng tôi chạy trên môi trường Windows (PowerShell) của kỹ sư. Việc tạo và mở HTML cục bộ hoàn toàn tương thích và không yêu cầu quyền admin đặc biệt. Tuy nhiên, đường dẫn lưu file cần được cấu hình vào thư mục `.md/scratch/` để dễ quản lý.
*   **Rủi ro/Đánh đổi:** Agent cần xin quyền thực thi lệnh mở trình duyệt. Rủi ro ở mức tối thiểu.

### Q2: Cơ chế lưu trữ tài liệu của `handoff` nên đặt ở đâu để tối ưu?
*   **Cách của nguồn:** Lưu vào thư mục tạm của OS (`$TMPDIR`) để tránh làm bẩn workspace git.
*   **Cách của CCBA:** Hiến pháp CCBA quy định mọi thành phẩm tri thức phải được tập trung và truy vết tại thư mục `.md/` của dự án.
*   **Đề xuất thích ứng:** Sẽ chuyển hướng lưu trữ file handoff về `.md/scratch/handoffs/` và cấu hình `.gitignore` cục bộ bỏ qua thư mục này để vừa không làm bẩn git, vừa giữ tri thức trong tầm kiểm soát của workspace.

### Q3: Việc spawn parallel sub-agents để review code (`code-review`) có làm tăng chi phí API?
*   **Cách của nguồn:** Gọi sub-agent song song để phân tích Standards và Spec riêng biệt nhằm tránh ô nhiễm context.
*   **Cách của CCBA:** Hiện tại QC pipeline chạy tuần tự để tiết kiệm chi phí gọi mô hình qua AI Gateway (LiteLLM Spark).
*   **Đánh giá:** Việc chạy song song chỉ nên áp dụng khi rà soát các pull request lớn hoặc phức tạp. Đối với công việc hằng ngày, quy trình QC tuần tự hiện tại của CCBA là tối ưu hơn về chi phí và tài nguyên.

### Q4: Việc áp dụng thuật ngữ `codebase-design` của Matt Pocock có làm xung đột thuật ngữ BIGBIM?
*   **Đánh giá:** Không xung đột. Các thuật ngữ của Matt Pocock chỉ áp dụng cho mã nguồn phần mềm (như interfaces, seams, adapters), còn các thuật ngữ BIGBIM (Sợi Chỉ Vàng, Sợi Chỉ Đỏ, Unique ID) áp dụng cho luồng thông tin mô hình công trình và hồ sơ pháp lý. Việc phân tách rõ ràng giúp Agent duy trì tính nhất quán.

### Q5: Quy trình phỏng vấn liên tục (`grilling loop`) có làm giảm hiệu suất làm việc nhanh?
*   **Rủi ro:** Khi cần sửa đổi nhanh các lỗi cú pháp hoặc tinh chỉnh nhỏ, việc Agent liên tục hỏi xoáy đáp xoay sẽ gây phiền toái cho kỹ sư.
*   **Giải pháp thích ứng:** Khi port skill này, bắt buộc giữ nguyên tham số `--fast` hoặc `--auto` để bỏ qua cổng phỏng vấn khi người dùng muốn thực thi nhanh.

---

## 4. Kế Hoạch Lộ Trình Triển Khai (Roadmap)

```mermaid
timeline
    title Lộ trình bổ sung kỹ năng mattpocock/skills vào CCBA Platform
    Pha 1 (Hiện tại) : improve-codebase-architecture (P0)
    Pha 2 (Kế tiếp) : handoff (P1) : codebase-design (P1) : diagnosing-bugs (P1)
    Pha 3 (Tương lai) : grill-me / grilling (P2) : wayfinder (P1) : wizard (P2)
```

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*

---

### 🟢 [RECOMMEND PORT] Skill: `mock-debugger` (Score: 85/100)
*   **Kho chứa nguồn**: `claudekit-engineer`
*   **Đánh giá**: Kỹ năng 'mock-debugger' cung cấp khả năng phân tích stack trace chuyên sâu và inject breakpoint tự động, giúp giảm đáng kể thời gian debug thủ công cho các tác vụ Python phức tạp. Hiện tại, nền tảng chưa có công cụ nào chuyên biệt cho việc trace-analyzer ở mức độ này, tránh được rủi ro trùng lặp.
*   **Các bước triển khai**:
    *   Kiểm tra sự tương thích của thư viện inject-breakpoint với môi trường runtime hiện tại của ccba-agent-platform.
    *   Tạo một module adapter để tích hợp log từ mock-debugger vào hệ thống logging tập trung của nền tảng.
    *   Thiết lập sandbox environment để kiểm thử tính an toàn khi thực thi code injection.
    *   Cập nhật tài liệu hướng dẫn sử dụng trong internal Hub và bổ sung các case test mẫu cho Python stack traces.

---

### 🟢 [RECOMMEND PORT] Skill: `mock-funnel-optimizer` (Score: 85/100)
*   **Kho chứa nguồn**: `claudekit-marketing`
*   **Đánh giá**: Kỹ năng này lấp đầy khoảng trống trong bộ công cụ tối ưu hóa chuyển đổi (CRO) của nền tảng. Hiện tại, chúng ta thiếu các công cụ tạo nội dung mang tính thử nghiệm (A/B testing) chuyên biệt cho micro-copy. Giá trị nghiệp vụ cao vì nó trực tiếp tác động đến tỷ lệ chuyển đổi, độ phức tạp triển khai thấp do tập trung vào xử lý văn bản, và không có công cụ hiện hữu nào trong Hub thực hiện chức năng tương tự.
*   **Các bước triển khai**:
    *   Kiểm tra tính tương thích của các prompt template với bộ thư viện LLM hiện tại của nền tảng.
    *   Tạo wrapper cho kỹ năng này để tuân thủ tiêu chuẩn logging và tracking của ccba-agent-platform.
    *   Thiết lập môi trường sandbox để kiểm thử khả năng tạo biến thể (variations) với các brand voice khác nhau.
    *   Cập nhật tài liệu kỹ thuật trong Hub và gắn thẻ (tag) vào nhóm 'Marketing Automation'.
    *   Triển khai phiên bản beta cho đội ngũ Growth Marketing để thu thập phản hồi về chất lượng micro-copy.

---

### 🟢 [RECOMMEND PORT] Skill: `grill-with-docs` (Score: 85/100)
*   **Kho chứa nguồn**: `claudekit-mattpocock-skills`
*   **Đánh giá**: Kỹ năng 'grill-with-docs' lấp đầy khoảng trống quan trọng trong việc tự động hóa quá trình 'onboarding' dự án và xây dựng context cho LLM. Hiện tại, nền tảng ccba-agent-platform chưa có công cụ nào chuyên biệt cho việc truy vấn ngược (reverse-engineering) cấu trúc từ tài liệu. Nó mang lại giá trị cao trong việc chuẩn hóa domain models ngay từ giai đoạn đầu phát triển.
*   **Các bước triển khai**:
    *   Kiểm tra tính tương thích của parser tài liệu hiện tại với định dạng đầu vào của grill-with-docs.
    *   Tạo branch 'feat/port-grill-with-docs' từ upstream để thử nghiệm tích hợp.
    *   Thiết lập bộ lọc (filter) để đảm bảo kỹ năng này chỉ quét các thư mục tài liệu được chỉ định (tránh đọc nhầm file hệ thống).
    *   Tích hợp với module 'Context Manager' của ccba-agent-platform để lưu trữ kết quả phân tích vào bộ nhớ tạm (Vector DB).
    *   Viết unit test cho các trường hợp tài liệu không cấu trúc (unstructured docs) để đảm bảo độ chính xác của output.

---

### 🔴 [IGNORE (Đã tồn tại)] Skill: `mock-debugger` (Score: 20/100)
*   **Kho chứa nguồn**: `engineer`
*   **Đánh giá**: Kỹ năng 'mock-debugger' đã tồn tại trong hệ thống local. Việc port từ upstream sẽ gây xung đột tên gọi (name collision) và tạo ra sự dư thừa kỹ thuật (technical redundancy). Hiện tại, chúng ta đã có kỹ năng 'diagnosing-bugs' và 'mock-debugger' sẵn có, việc port thêm sẽ làm phức tạp hóa cơ sở mã mà không mang lại giá trị gia tăng rõ rệt.
*   **Các bước triển khai**:
    *   Dừng ngay tiến trình port cho kỹ năng 'mock-debugger'.
    *   Thực hiện kiểm tra (audit) kỹ năng 'mock-debugger' hiện có trên local để xác định xem các tính năng từ upstream ('Automated breakpoint injector', 'trace analyzer') có thể được tích hợp bằng cách nâng cấp phiên bản hiện tại hay không.
    *   Nếu upstream có các logic vượt trội, hãy tạo một task 'Refactor/Enhance' cho kỹ năng 'mock-debugger' hiện tại thay vì tạo mới.
    *   Đánh dấu kỹ năng này là 'Duplicate' trong danh mục quản lý kỹ năng để tránh các yêu cầu port tương tự trong tương lai.

---

### 🟢 [RECOMMEND PORT] Skill: `mock-funnel-optimizer` (Score: 82/100)
*   **Kho chứa nguồn**: `marketing`
*   **Đánh giá**: Mặc dù ban đầu được thiết kế cho e-commerce, kỹ năng này mang lại giá trị thực tiễn rất lớn cho khối hành chính (Admin) của CCBA trong việc soạn thảo các tài liệu marketing, hồ sơ đề xuất thầu, tài liệu quy trình, form mẫu hồ sơ văn bản, và tối ưu hóa các thông điệp giao tiếp hành chính. Nó bổ trợ đắc lực cho `long-form-writer` bằng cách tập trung vào viết các biến thể ngắn, tối ưu hóa mức độ thuyết phục (persuasion) của micro-copy hành chính/thương mại.
*   **Các bước triển khai**:
    *   Bản địa hóa hệ thống template và prompts từ tiếng Anh thương mại điện tử sang tiếng Việt chuyên ngành xây dựng, thầu và tài liệu hành chính công sở.
    *   Tích hợp adapter kết nối với AI Gateway để khối Admin có thể gọi nhanh thông qua lệnh `/ccba-marketing-optimize` hoặc `/ccba-admin-opt`.
    *   Thiết lập các thư viện mẫu (boilerplate library) cho hồ sơ đề xuất thầu và quy trình bàn giao công việc của CCBA để làm dữ liệu nền (baseline) cho việc tối ưu.

---

### 🔴 [IGNORE] Skill: `grill-with-docs` (Score: 25/100)
*   **Kho chứa nguồn**: `mattpocock-skills`
*   **Đánh giá**: Kỹ năng 'grill-with-docs' có sự trùng lặp chức năng cốt lõi với kỹ năng 'grilling' hiện có trên hệ thống. Việc port thêm một kỹ năng mới gây ra sự dư thừa và phân mảnh quy trình làm việc. Thay vì tạo mới, chúng ta nên mở rộng kỹ năng 'grilling' hiện tại để hỗ trợ khả năng đọc và truy vấn tài liệu (document-contextual grilling) thay vì tách biệt thành một kỹ năng riêng.
*   **Các bước triển khai**:
    *   Kiểm tra tệp thực thi của kỹ năng 'grilling' hiện có.
    *   Cập nhật logic của 'grilling' để tích hợp khả năng đọc tài liệu (tận dụng 'markdown-document-processing' hoặc 'hybrid-rag-search' đã có).
    *   Cập nhật tài liệu hướng dẫn sử dụng cho 'grilling' để bao gồm ngữ cảnh 'grilling-with-docs'.
    *   Từ chối yêu cầu port 'grill-with-docs' từ thượng nguồn để giữ cho danh mục kỹ năng tinh gọn.

---

### 🔴 [IGNORE (Đã tồn tại)] Skill: `wayfinder` (Score: 75/100)
*   **Kho chứa nguồn**: `mattpocock-skills`
*   **Đánh giá**: Lỗi gọi AI Gateway: Request timed out.. Đề xuất rà soát thủ công.
*   **Các bước triển khai**:
    *   Rà soát thủ công tệp tin SKILL.md
    *   Port nếu cần thiết
