# ADR 0053: Teamwork Multi-Agent Orchestration Framework & Exclusive Seam Protocol

## 1. Trạng Thái (Status)
**ACCEPTED & ADOPTED** (2026-09-01)

## 2. Bối Cảnh (Context)
Khi CCBA Platform mở rộng quy mô phục vụ các dự án lớn (tái cấu trúc Monorepo đa gói, thẩm tra chất lượng thiết kế 4 bộ môn Kiến trúc - Kết cấu - MEP - PCCC, hoặc nạp kho pháp luật hàng loạt), các quy trình ReAct đơn luồng hoặc chu trình suy luận sâu ngắn hạn (`/boost` — ADR 0052) bộc lộ các hạn chế:
1. **Thiếu Khung Điều Phối Dài Hạn (Long-Running Coordination):** Các dự án lớn bao gồm nhiều milestones độc lập cần được phân công, theo dõi và nghiệm thu có hệ thống thay vì gộp chung vào 1 prompt khổng lồ.
2. **Nguy Cơ Xung Đột Ghi Đè (Concurrent Writing Conflicts):** Khi nhiều tác nhân cùng sửa đổi mã nguồn, hiện tượng race condition và ghi đè tệp làm mất dữ liệu đã được ghi nhận trong lịch sử (Session Learnings #32).
3. **Nhầm Lẫn Giữa Thẩm Quyền Con Người & Năng Lực AI:** Nguy cơ gán trực tiếp trách nhiệm pháp lý/quản trị của 11 Ghế CCBA Charter 2026 cho AI Agent mà không có sự kiểm soát của con người.

Lấy cảm hứng từ tính năng `/teamwork-preview` của Google Antigravity, chúng tôi thiết lập khung điều phối đa tác nhân chính thức (**Teamwork Framework**) được địa hóa cho CCBA.

## 3. Quyết Định Thiết Kế (Decisions)

### A. Mô Hình 3 Vai Trò Tối Giản (KISS Hierarchy)
Thay vì xây dựng hệ thống vai trò phức tạp, Teamwork Framework áp dụng mô hình 3 vai trò:
1. **Orchestrator (Nhạc Trưởng):** Agent chính chịu trách nhiệm phỏng vấn, lập `team_sheet.md`, dispatch workers theo batch, đọc kết quả trung gian, tổng hợp và **duy nhất có quyền ghi file chính thức** lên codebase.
2. **Workers (Tác Nhân Thực Thi):** Các subagents thực thi song song, độc lập trong từng đợt (batch).
3. **Success Auditor (Kiểm Định Nghiệm Thu):** Kiểm tra độc lập chất lượng code, an toàn bảo mật (Maskara) và đối soát phân vùng diff trước khi hoàn tất milestone.

### B. Tuân Thủ Nghiêm Ngặt Rào Chắn Đọc Độc Quyền (ADR 0035 Compliance)
- Toàn bộ Worker Subagents tuân thủ **Two-Layer Guardrail (ADR 0035)**:
  - Chỉ được cấp quyền đọc (`view_file`, `grep_search`, `read_resource`) và chạy scoped test cô lập.
  - Tuyệt đối không cấp quyền chỉnh sửa file chính thức hoặc thực thi lệnh Git nguy hiểm.
  - Toàn bộ kết quả nháp, code đề xuất và báo cáo phân tích được xuất vào thư mục sandbox cô lập: `.system_generated/scratch/worker_{N}/`.

### C. Cấu Trúc Team Sheet 2 Lớp Phân Tách Rõ Ràng
Tệp `.agents/teams/[project]_team_sheet.md` phân định rõ:
- **Lớp 1 — Accountability Mapping (Con người):** Ánh xạ các mốc bàn giao (Milestones) với các Ghế phụ trách trong 11 Ghế CCBA Charter 2026 (ADR 0046) để con người thực hiện ký duyệt (Sign-off).
- **Lớp 2 — Worker Assignments (AI Subagents):** Danh sách động 2–5 workers, mỗi entry chứa: Tên định danh, Phạm vi file độc quyền (Exclusive File Scope), Tiêu chí nghiệm thu (Acceptance Criteria) và chính sách Timeout.

### D. Giới Hạn Tác Nhân & Chiến Lược Phân Đợt (Worker Cap & Batching)
- Giới hạn tối đa **3 workers** chạy đồng thời trong cùng một thời điểm.
- Khi dự án có $> 3$ workstreams, Orchestrator chia thành các đợt tuần tự (Batches), mỗi batch tối đa 3 workers.

### E. Rào Chắn Quá Giờ & Cơ Chế Khôi Phục (Worker Timeout & Fallback)
- Thời hạn tối đa cho mỗi worker: **10 phút**.
- Nếu worker timeout hoặc gặp lỗi ngữ cảnh: Orchestrator đánh dấu milestone `INCOMPLETE`, lấy dữ liệu trung gian và chọn:
  - *Retry:* Dispatch worker mới với prompt hẹp hơn.
  - *Escalate:* Nếu là bế tắc logic sâu, đóng gói Deep Problem Brief và kích hoạt `/boost` (Escalation UP).

### F. Kiểm Toán Phân Vùng Hậu Hợp Nhất (Post-Merge Diff Audit)
- Sau mỗi milestone, Auditor/Orchestrator so khớp `git diff --name-only` với file scope trong `team_sheet.md` để đảm bảo không có sự can thiệp trái phép ngoài ranh giới seam.

### G. Phân Định Rõ Ràng `/boost` vs `/ccba-teamwork`
- **`/boost` (Escalation UP):** Suy luận sâu ngắn hạn trong 1 session để bẻ khóa bài toán bế tắc kỹ thuật đơn lẻ.
- **`/ccba-teamwork` (Coordination OUT):** Điều phối dài hạn nhiều workstreams độc lập song song qua nhiều milestones.

### H. Phân Định Ranh Giới 2 Nhóm Orchestrators (Multi-Agent Swarms vs User Rituals)
Hệ thống phân tầng Tầng 3 (Composite Orchestrator) chia thành 2 nhóm bản chất riêng biệt:
1. **Nhóm 1 — Autonomous Multi-Agent Swarms (`ccba-ai-qc`, `ccba-teamwork`):**
   - Có worker subagents chạy song song trong nền.
   - Bắt buộc tuân thủ Single-Writer Protocol (ADR-0053) và Exclusive Scratch Sandboxing (`.system_generated/scratch/worker_{N}/`).
   - Được bảo vệ liên tục bằng bộ kiểm thử áp lực CI tự động (`tests/governance/test_swarm_dogfood_ci.py`).
2. **Nhóm 2 — Human-Interactive User Rituals (`ccba-implement`, `ccba-new-feature`, `ccba-autoresearch`, `ccba-graduate-rd`, `ccba-knowledge-loop`, `ccba-release-feature`, `ccba-spoke-adopter`):**
   - Đóng vai trò là các nghi thức tương tác trực tiếp với người dùng (User-Invocable Commands).
   - Thiết lập `disable-model-invocation: true` (tiêu thụ 0 background tokens).
   - Không sinh workers chạy ngầm, không thuộc phạm vi áp dụng Swarm Stress Benchmark.

## 4. Hệ Quả (Consequences)
- **Triệt Tiêu Xung Đột Mã Nguồn:** Duy nhất Orchestrator ghi codebase, loại bỏ hoàn toàn race condition.
- **Bảo Vệ Ngân Sách Ngữ Cảnh:** Workers chạy cô lập trên scratch sandbox, không làm phình context của phiên chính.
- **Minh Bạch Thẩm Quyền:** Phân tách rành mạch giữa phê duyệt của con người (11 Ghế) và hỗ trợ kỹ thuật của AI.
- **Tương Thích Tuyệt Đối:** Tuân thủ 100% ADR 0035, ADR 0046, ADR 0052 và bộ linter của CCBA Platform.
