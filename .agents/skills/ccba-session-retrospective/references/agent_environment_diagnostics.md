# 🛠️ Hướng Dẫn Chẩn Đoán & Tối Ưu Hóa Môi Trường Làm Việc Của AI Agent (Agent Environment Diagnostics)

Tài liệu tham chiếu này kế thừa và phát triển phương pháp luận chẩn đoán môi trường từ kỹ năng thượng nguồn `retro` (`mattpocock-skills`), được bản địa hóa và tích hợp trực tiếp vào hệ sinh thái CCBA Agent Services Platform theo thể chế **ADR-0057** và mô hình quản trị ngữ cảnh đa tầng **ADR-0030**.

---

## 🎯 Mục Đích & Nguyên Tắc Vận Hành
Kỹ sư hoặc AI Agent chỉ nạp tài liệu này khi phiên làm việc gặp **ma sát công cụ (tool friction)**, xuất hiện **vòng lặp sửa lỗi kéo dài**, hoặc **tốn nhiều lượt tìm kiếm tệp tin**. Mục tiêu là tối ưu hóa chính môi trường làm việc của Agent để các phiên kế tiếp chạy nhanh hơn, chính xác hơn và tiết kiệm token hơn.

---

## 📋 7 Trụ Cột Chẩn Đoán Môi Trường (The 7 Diagnostic Pillars)

### 1. Navigation (Định Hướng & Bản Đồ Tệp Tin)
* **Triệu chứng nhận diện:** Agent phải gọi nhiều lệnh `run_command` (như `find`, `grep`, `locate`) hoặc tốn nhiều lượt `view_file` dò dẫm trong cây thư mục để tìm đúng mã nguồn / cấu hình.
* **Nguyên nhân:** Thiếu các con trỏ điều hướng (Navigation Pointers) rõ ràng từ các tệp tài liệu trung tâm.
* **Hành động khắc phục trong CCBA:**
  - Bổ sung liên kết điều hướng dạng Markdown `[filename](file:///path/to/file)` vào `AGENTS.md`, `CONTEXT.md` hoặc `PLATFORM.md`.
  - Nếu tệp tài liệu quá dài, tạo mục lục tham chiếu và tách nhỏ tài liệu chuyên sâu vào `docs/` hoặc `references/*.md`.

---

### 2. Automated Checks over Prompt Rules (Kiểm Tra Tất Định Thay Vì Viết Luật)
* **Triệu chứng nhận diện:** Agent mắc lỗi cú pháp, vi phạm quy ước đặt tên, sai mẫu import, hoặc bỏ sót kiểu dữ liệu (typing). Đội ngũ thường có xu hướng viết thêm một dòng cấm vào `AGENTS.md`.
* **Nguyên tắc cốt lõi (Matt Pocock):**
  > *"A repo with no guardrail is itself a finding. Reserve prompt rules for genuine judgement calls. Default to building the check over writing the rule."*
* **Hành động khắc phục trong CCBA:**
  - **Triệt tiêu Attention Dilution:** Tệp `AGENTS.md` càng dài thì khả năng chú ý của LLM càng suy giảm. Mọi quy tắc mang tính cơ học (cú pháp, định dạng, import shape, vị trí tệp, cấm thư viện thứ ba) **BẮT BUỘC** phải chuyển hóa thành kiểm tra tất định:
    + Script linter / AST inspection (như `scripts/governance/check_dependency_contracts.py`).
    + Pre-commit hook hoặc Git hooks (`scripts/hooks/`).
    + Bộ kiểm định quản trị `ccba-harness verify-patch --preset <preset>`.
  - Chỉ giữ lại trong `AGENTS.md` hoặc `CODING_STANDARDS.md` các tiêu chuẩn đòi hỏi **phán đoán trí tuệ (Judgement Calls)** mà không công cụ tất định nào thay thế được.

---

### 3. Role Decoupling & Context Pressure (Phân Tách Áp Lực Ngữ Cảnh)
* **Triệu chứng nhận diện:** Implementer Agent bị "ngợp ngữ cảnh" (Context Exhaustion), sinh ảo giác (hallucination), quên các quy định cốt lõi hoặc tạo ra mã nguồn chắp vá khi phải vừa viết tính năng lớn vừa tự rà soát hàng chục quy tắc chi tiết.
* **Nguyên tắc cốt lõi (Matt Pocock):**
  - **Implementer Agent** chịu áp lực ngữ cảnh cao nhất: phải đọc code, hiểu kiến trúc, sinh code và debug terminal.
  - **Reviewer Agent** chịu áp lực ngữ cảnh thấp nhất: bắt đầu từ cửa sổ ngữ cảnh mới (Fresh Window), chỉ nhận Git diff và danh sách tiêu chuẩn kiểm thử.
* **Hành động khắc phục trong CCBA:**
  - Tuyệt đối không ép Implementer Agent phải tự ghi nhớ toàn bộ checklist định dạng phức tạp trong lúc viết code.
  - Sau khi hoàn thành bản nháp (Draft), bàn giao ngay Git diff cho Reviewer Agent chuyên biệt qua kỹ năng `ccba-code-review` hoặc `ccba-ai-qc`. Reviewer Agent sẽ độc lập đối soát toàn diện theo checklist mà không làm ô nhiễm ngữ cảnh thực thi.

---

### 4. Global Invariants Budget (Quản Trị Ngân Sách Ngữ Cảnh ADR-0030)
* **Triệu chứng nhận diện:** Tệp chỉ dẫn nền tảng `AGENTS.md` hoặc tệp bài học `session_learnings.md` phình to quá giới hạn ngân sách ($> 10.0\text{ KB}$), làm cạn kiệt số lượng token đầu vào ngay khi khởi động phiên.
* **Hành động khắc phục trong CCBA:**
  - Tuân thủ nghiêm ngặt **Mô hình Bộ nhớ Đa tầng (Tiered Memory Model - ADR-0030)**:
    + **Tầng 1 (Root Invariants):** Chỉ giữ tối đa 10-15 quy tắc bất biến tối thượng trong `AGENTS.md`.
    + **Tầng 2A (Progressive References):** Di dời các chỉ dẫn tác vụ cụ thể, hướng dẫn chi tiết vào `references/*.md` của từng kỹ năng.
    + **Tầng 3 (Historical Archive):** Chạy `python scripts/governance/compact_session_learnings.py` để nén các bug narrative vào `session_learnings_history.md`.

---

### 5. Tool Economy (Tiết Kiệm Công Cụ & Tối Ưu Hóa Token)
* **Triệu chứng nhận diện:** Agent gọi các công cụ đọc tệp thô sơ không có giới hạn, đọc một tệp hàng nghìn dòng trong khi chỉ cần xem 20 dòng, hoặc thực hiện tìm kiếm toàn diện (brute-force grep) không định hướng.
* **Hành động khắc phục trong CCBA:**
  - Luôn sử dụng kỹ thuật đọc phân đoạn (Slice Notation) qua `StartLine` và `EndLine` của công cụ `view_file`.
  - Thay vì `grep` toàn bộ ổ đĩa, ưu tiên tra cứu Seam Capability Contracts:
    ```bash
    ccba-platform find-seam --in <types> --out <types>
    ```
  - Xây dựng CLI chuyên biệt (như `catalog_probe.py`) để trả về kết quả JSON tóm lược có cấu trúc thay vì in ra hàng nghìn dòng văn bản thô.

---

### 6. No-ops Elimination (Triệt Tiêu Chỉ Dẫn Vô Hiệu)
* **Triệu chứng nhận diện:** Các câu lệnh chỉ dẫn trong prompt hoặc steering file đã lỗi thời, trùng lặp với hành vi mặc định của mô hình, hoặc không bao giờ làm thay đổi đầu ra thực tế của Agent.
* **Hành động khắc phục trong CCBA:**
  - Trong quá trình Retrospective, rà soát và loại bỏ các quy tắc "thừa thãi".
  - Một chỉ dẫn chỉ có giá trị khi nó ngăn chặn được ít nhất một lỗi thực tế đã được kiểm chứng (Evidence-Backed Invariant).

---

### 7. Information Access (Quyền Truy Cập & Độ Sẵn Sàng Của Thông Tin)
* **Triệu chứng nhận diện:** Agent bị dừng lại giữa chừng hoặc đưa ra phán đoán sai vì thiếu thông tin môi trường, không có biến môi trường mẫu, không truy cập được log của service đang chạy ngầm, hoặc tài liệu API của bên thứ ba không có sẵn.
* **Hành động khắc phục trong CCBA:**
  - Duy trì tệp `.env.example` đầy đủ với các giá trị mẫu chuẩn xác.
  - Cung cấp cơ chế chuyển tiếp log (Teeing service logs) cho các daemon nền vào `.md/scratch/logs/`.
  - Cập nhật định kỳ các hợp đồng Deep Seam và schema của các MCP Server trong `.md/knowledge/`.
