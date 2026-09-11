# 0058. Live Collaboration Artifacts, Workspace Mirroring, and CCBA Charter 11-Seat Review Alignment

* **Status:** Accepted
* **Date:** 2026-09-10
* **Deciders:** CCBA Platform Core Team & Lead Engineer
* **Consulted:** ADR 0030 (Instruction Budget), ADR 0035 (Deep Modules), ADR 0046 (Personal Sandbox & CCBA Charter 2026), ADR 0053 (Teamwork Multi-Agent), ADR 0057 (Two-Stage Decision Framework)

---

## Context & Problem Statement

Khi triển khai các quy trình tự chủ đa tác tử (Autonomous Agentic Platform v2.0), sự tương tác giữa AI Agent và Kỹ sư đối mặt với 4 thách thức kiến trúc nghiêm trọng:

1. **Xung Đột Vùng Lưu Trữ & Vi Phạm Quy Tắc Toàn Cục 1:** Để Antigravity IDE hiển thị giao diện Tab trực quan kèm nút phê duyệt (`Proceed`), Agent bắt buộc phải ghi vào thư mục đệm nội bộ `<appDataDir>\brain\<conversation-id>/`. Tuy nhiên, Quy tắc Toàn cục số 1 quy định tất cả tài sản tri thức AI bắt buộc phải lưu trong `.\.md\` của Monorepo. Việc thiếu cơ chế đồng bộ dẫn tới nguy cơ mất dữ liệu sau khi đóng phiên hoặc làm rác Git working tree.
2. **Pha Loãng Chú Ý Do Bùng Nổ Artifacts (Attention Dilution):** Việc sinh quá nhiều tệp tin trạng thái rời rạc (`task_dashboard.md`, `qc_matrix.md`, `prompt_draft.md`, `risk_register.md`) làm phân tán nhận thức của lập trình viên, vi phạm nguyên tắc Keep It Simple, Stupid (KISS) và ADR-0030.
3. **Nguy Cơ Vượt Cấp Thẩm Thấu Dữ Liệu Chưa Kiểm Định:** Kỹ sư làm việc trong Spoke Cá nhân (`personal_sandbox`) có thể vô tình hoặc cố ý xuất bản tài liệu nháp ra môi trường chính thức mà không tuân thủ Quy chế CCBA 2026 (11 Ghế Trách nhiệm & 5 Cấp độ Thẩm duyệt QC theo ADR-0046).
4. **Hiện Tượng Tự Nhận Hoàn Thành (Premature Completion & Self-Certification):** Agent có xu hướng tự kết luận "đã hoàn thành tốt" bằng văn xuôi mà không cung cấp bằng chứng kiểm thử máy tính khách quan trước khi yêu cầu người dùng nghiệm thu.

---

## Decision Outcome

Đội ngũ kiến trúc CCBA quyết định ban hành và thực thi toàn diện:

### 1. Kiến Trúc Lưu Trữ Hai Vùng (Transient-to-Permanent Mirroring Architecture)
- **Vùng Đệm Tương Tác Sống (Transient Interactive Buffer):** Trong suốt quá trình thực thi phiên làm việc, Agent sử dụng `<appDataDir>\brain\<conversation-id>/` để tạo và cập nhật các Artifacts native (`ArtifactMetadata: {RequestFeedback: true, UserFacing: true}`). Điều này đảm bảo 100% trải nghiệm tương tác với IDE (Tab chuyên biệt, Diff Viewer, Nút Proceed).
- **Cơ Chế Snapshot Đồng Bộ Git (Final Snapshot Mirroring):** Khi người dùng nhấn nút duyệt hoặc khi hoàn thành task/commit Git, Agent tự động sao chép bản snapshot hoàn chỉnh của các Artifacts vào thư mục `.\.md\reports/` hoặc `.\.md/knowledge/` của Monorepo. Quá trình này bảo tồn tri thức vĩnh viễn trên Git mà không sinh file rác trung gian trong quá trình nháp.

### 2. Tiêu Chuẩn Bộ Ba Artifacts Chuẩn Mực (Trio Core Artifacts Standard)
Để chống pha loãng chú ý và tuân thủ triệt để KISS, nền tảng chuẩn hóa 3 Artifacts duy nhất:
1. **`implementation_plan.md` (Pre-execution Gate):** Bắt buộc cho mọi task phức tạp trước khi can thiệp mã nguồn. Tích hợp trực tiếp đề mục nội khối `## CCBA Charter Governance & QC Matrix` — người dùng chỉ nhìn 1 màn hình duy nhất để duyệt kế hoạch và thẩm quyền.
2. **`walkthrough.md` (Post-execution Evidence):** Bắt buộc sau khi hoàn thành. Nhúng trực tiếp Báo cáo Thẩm tra Khách quan từ máy tính và liên kết commit Git.
3. **`task_dashboard.md` (Multi-Agent Swarm Only):** Chỉ kích hoạt khi chạy chế độ Swarm đa tác tử (`ccba-teamwork` theo ADR-0053). Tuyệt đối không sinh file này trong các tác vụ đơn lẻ (Single-Agent).
4. *(Đặc thù)* **`learning_proposal.md`:** Chỉ kích hoạt khi chạy User Ritual `/learn`.

### 3. Ràng Buộc Thẩm Quyền 11 Ghế CCBA Charter & 5 Cấp Độ QC (ADR-0046 Alignment)
Agent tự động đọc `.md/workspace_context.yaml` để áp dụng chính sách phân quyền thích ứng:
- **Tại Personal Sandbox Spoke (`is_sandbox: true`):**
  - Khóa cứng trần phê duyệt ở **QC Level 1 (Technical Check)** với ghế chịu trách nhiệm là `KY_SU_THUC_THI`.
  - Bắt buộc đính kèm Watermark trên đầu mọi Artifact: `⚠️ [CCBA SANDBOX DRAFT — BẢN THẢO NGHIÊN CỨU NỘI BỘ — CHƯA PHÁT HÀNH CHÍNH THỨC]`. Cấm Agent tự ý gỡ bỏ watermark hoặc nâng cấp lên Level 2–5.
- **Tại Spoke Dự Án Chính Thức (`delivery_project`):**
  - Yêu cầu xác nhận đúng Ghế trách nhiệm:
    * Thay đổi code/kỹ thuật: `CHU_TRI_BO_MON` (QC Level 2).
    * Nghiệm thu bàn giao / IDOP Task Sign-off: `CHU_TRI_HOP_DONG_PM` (QC Level 3) + `IDOP_LEAD`.
    * Tư vấn pháp lý / Quy chuẩn VBPL: `CO_VAN_PHAP_LY_QA` (QC Level 4).
    * Hồ sơ xuất xưởng CĐT / Viện IBST: `GIAM_DOC` hoặc `PHO_GIAM_DOC` (QC Level 5).
- **Tại Hub Monorepo:** Thay đổi hệ sinh thái nền tảng do `TRUONG_PHONG_RD_HTQT` hoặc `GIAM_DOC` phê duyệt.

### 4. Khóa Hoàn Thành Cứng Bằng Bằng Chứng Máy Tính (Deterministic Exit-Code Binding)
- Trong `walkthrough.md`, Agent bắt buộc phải nhúng nguyên văn bảng kết quả từ công cụ `ccba-harness verify-patch` (xây dựng tại Ticket 2).
- **Quy tắc Khóa Cứng (Hard Completion Lock):** Nếu có bất kỳ lệnh kiểm tra nào (`pytest`, `ruff`, `mypy`) trả về Exit Code $\ne 0$, Agent **bị cấm tuyệt đối** tuyên bố hoàn thành hoặc đề xuất người dùng nghiệm thu. Agent bắt buộc phải kích hoạt vòng lặp tự sửa lỗi (Fix Loop) hoặc dừng khẩn cấp báo cáo sự cố kèm log chi tiết.

---

## Consequences

### Tích cực (Positive)
- **Hài hòa tuyệt đối giữa IDE và Git:** Tận dụng 100% sức mạnh UI của Antigravity IDE trong khi vẫn tuân thủ nghiêm ngặt Quy tắc Toàn cục số 1 (`.\.md\`).
- **Triệt tiêu Premature Completion:** Mọi xác nhận hoàn thành đều dựa trên bằng chứng Exit Code thực tế từ máy tính, loại bỏ hoàn toàn bẫy ảo giác và tự chứng nhận của LLM.
- **Tuân thủ Pháp lý & Hiến chương CCBA 2026:** Phân định rạch ròi giữa bản nháp nghiên cứu cá nhân và tài sản dự án chính thức, bảo vệ uy tín thương hiệu CCBA.
- **Tối ưu hóa Trải nghiệm & Token Budget:** Tiết kiệm tối đa token chú ý cho cả người dùng và mô hình bằng cách giới hạn số lượng artifacts.

### Đánh đổi & Thách thức (Trade-offs)
- Agent phải thực hiện thêm bước snapshot tự động khi kết thúc phiên.
- Quy trình nghiệm thu đòi hỏi các lệnh kiểm tra tự động phải được thiết lập rõ ràng từ trước.
