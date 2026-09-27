# Báo Cáo Nghiên Cứu: Áp Dụng Mô Hình "2,500 PRs/Month" & Bugbot Review Vào CCBA Agent Platform

> **Phương pháp nghiên cứu:** Dual-Agent Adversarial Research (`ccba-research`)  
> **Subagents tham gia:** Subagent A (`Solution Explorer` - `0712d249`) & Subagent B (`Risk & Boundary Challenger` - `8152a6a0`)  
> **Ngày hoàn thành:** 2026-09-27  
> **Trạng thái:** DECISION_READY

---

## 1. Tóm Tắt Thực Thi (Executive Summary)

Nghiên cứu này khảo sát khả năng tiếp thu và chuyển hóa mô hình vận hành **"2,500 PRs/tháng"** của Cursor (Background Agentic Workflow + Bugbot Pre-merge Review) vào hệ thống **CCBA Agent Services Platform**.

**Phát hiện cốt lõi:**
1. **Khả thi cao ở tầng Cổng Kiểm Chứng (Verification Gate):** CCBA đã sở hữu sẵn nền móng cốt lõi là **ADR-0058 (Deterministic Hard Completion Lock)** và công cụ `ccba_harness.verifier`. Việc đưa cổng này lên GitHub Actions kết hợp với cơ chế Self-Healing Loop sẽ triệt tiêu lỗi cú pháp và kiểm thử cơ bản trước khi đến tay con người.
2. **Nghẽn nút ở tầng Phân rã Tác vụ (Task Granularity):** Quy trình hiện tại (`ccba-to-spec`) tạo ra các đặc tả lớn; agent thường cố giải quyết nhiều việc trong 1 session gây phình to PR, tăng nguy cơ hallucination và nghẽn merge. Cần chuyển dịch dứt khoát sang **Atomic Micro-PRs ($\le 200$ LOC)** neo theo từng Seam đơn lẻ.
3. **Cảnh báo Đỏ từ Phản Biện Đối Kháng (Adversarial Warnings):** Tuyệt đối **không** xây dựng một autonomous bot tự động merge hoặc tự động trigger AI Review trên mọi commit. Việc này sẽ gây bão request làm sập LiteLLM Gateway Spark, rò rỉ secret trong raw diff (vi phạm `ccba-maskara`), và tạo vòng lặp vô hạn (bot-to-bot echo chamber).

**Kết luận chiến lược:** CCBA nên áp dụng mô hình Cursor theo hướng **"Deterministic Gate First, Advisory AI Review Second"** với quyền hạn nghiêm ngặt: AI Review chỉ mang tính chất tư vấn đọc (Read-only Advisory), việc merge phải qua kiểm chứng máy móc tất định và rào chắn rủi ro (Danger Triage).

---

## 2. Kết Quả Nghiên Cứu Chi Tiết (Key Findings)

### 2.1. Đề Xuất Kỹ Thuật (Từ Subagent A — Solution Explorer)

1. **Bộ CCBA Bugbot Rules (`.github/bugbot-rules.md`):**  
   Mã hóa các Invariants bất biến trong `AGENTS.md` thành rule máy đọc được để AI Review tự động kiểm tra:
   - *Platform-Aware KISS*: Không tạo utility ad-hoc khi `catalog.yaml` đã có Seam.
   - *Multi-Key Sorting*: Cấm `reverse=True`, bắt buộc `-round(score, 4)`.
   - *Decoupled Connection*: Cấm import ngược từ Consumer vào `*_client.py`.
   - *POSIX Permissions*: Bảo toàn `stat.S_IXUSR` khi ghi file thực thi.
2. **Atomic Micro-PR Pipeline & Seam-Anchored Slicing:**  
   Bẻ nhỏ User Story thành các micro-ticket độc lập ($\le 150-200$ dòng code), chỉ chạm tối đa 1 Seam duy nhất. Các agent có thể claim song song qua giao thức `Multi-Client Peer Claim Locking Invariant`.
3. **Deterministic Pre-Merge Gate & Self-Healing Loop:**  
   Đóng gói `python -m ccba_harness verify-patch` thành GitHub Actions Status Check. Khi fail, tự động xuất markdown báo lỗi và kích hoạt Background Healing Agent vá lỗi bằng `--force-with-lease`.
4. **Auto-Approval Matrix theo Merge Danger Triage:**  
   - *Two-way door + Localized* (docs, test case, typo, `.md/`): Auto-approve và auto-merge sau khi pass verifier.
   - *One-way door hoặc Hub-affecting*: Bắt buộc chuyển sang Human Review.

### 2.2. Rà Soát Rủi Ro Trọng Yếu & Biên Giới An Toàn (Từ Subagent B — Risk Challenger)

| Rủi Ro Trọng Yếu | Cơ Chế Phát Sinh | Hậu Quả Tiềm Tàng | Rào Chắn Bắt Buộc (Mitigation) |
| :--- | :--- | :--- | :--- |
| **Bão Quota & Nghẽn Gateway** | Kích hoạt AI Review trên mọi sự kiện push/sync PR. | Nghẽn GPU cục bộ trên Server Spark (`:8090`), cạn token Cloud, timeout pipeline QC/Legal. | **Explicit Opt-in Trigger:** Chỉ chạy khi có label `ai-review-requested` hoặc lệnh `/ccba-ai-review`. Loại trừ PR từ bot. |
| **Rò Rỉ Bí Mật (PII & Secrets)** | Gửi raw diff lên mô hình AI bên thứ ba. | Vi phạm `ccba-maskara` và rò rỉ connection strings/API keys trong diff. | **Maskara Gate:** Bắt buộc chạy `from ccba_maskara import redact_secrets_in_text` trước khi gửi diff cho LLM. |
| **Vòng Lặp Vô Hạn & Race Condition** | Bot tự động commit sửa code và tự merge. | Tạo vòng lặp *Bot commit $\to$ CI chạy $\to$ Bot review $\to$ Loop*. Xung đột `git push --force-with-lease`. | **Read-Only Advisory Guardrail:** AI Review chỉ có quyền comment, CẤM quyền `APPROVE`, cấm tự động merge code logic. |
| **Vi Phạm KISS (Over-engineering)** | Dựng thêm hạ tầng bot orchestrator phức tạp. | Thêm điểm lỗi đơn lẻ (Single Point of Failure), tăng chi phí bảo trì. | Tái sử dụng triệt để `ccba_harness` và GitHub Actions có sẵn. |

---

## 3. Ma Trận Đánh Giá Đề Xuất (Giá Trị × Độ Phức Tạp × Rủi Ro × KISS)

| Hạng Mục Đề Xuất | Giá Trị (Value) | Độ Phức Tạp (Complexity) | Rủi Ro (Risk) | Tuân Thủ KISS | Quyết Định Đề Xuất |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **1. Atomic Micro-PR Slicing** | **RẤT CAO** | **THẤP** | **THẤP** | **ĐẠT** | **TRIỂN KHAI NGAY (Sprint 1)** |
| **2. CI Pre-Merge Verifier Action** | **RẤT CAO** | **THẤP** | **THẤP** | **ĐẠT** | **TRIỂN KHAI NGAY (Sprint 1)** |
| **3. CCBA Bugbot Rules Template** | **CAO** | **THẤP** | **THẤP** | **ĐẠT** | **TRIỂN KHAI NGAY (Sprint 1)** |
| **4. Maskara Gate for PR Diffs** | **CAO** | **THẤP** | **THẤP** | **ĐẠT** | **TRIỂN KHAI (Sprint 2)** |
| **5. Auto-Approval cho Safe PRs** | **TRUNG BÌNH** | **TRUNG BÌNH** | **TRUNG BÌNH** | **ĐẠT** | **THỬ NGHIỆM HẠN CHẾ (Sprint 2)** |
| **6. Self-Healing Agent Loop** | **CAO** | **CAO** | **CAO** | **KHÔNG** | **TẠM HOÃN (Cần thiết kế ADR riêng)** |

---

## 4. Khuyến Nghị Triển Khai (Implementation Recommendations)

### Lộ Trình 2 Giai Đoạn Khả Thi:

#### Giai đoạn 1: Thiết Lập Nền Móng Tốc Độ An Toàn (Ngay lập tức)
1. **Tạo tệp cấu hình `.github/bugbot-rules.md`**: Đưa các Invariants cốt lõi của `AGENTS.md` thành checklist ngắn gọn 15 dòng cho Cursor Bugbot và GitHub Copilot Reviewer.
2. **Kích hoạt GitHub Actions Pre-Merge Gate**: Đóng gói lệnh `python -m ccba_harness verify-patch --preset pre-commit` vào `.github/workflows/pr-verifier.yml`. Mọi PR bắt buộc phải có thẻ xanh từ verifier mới được merge.
3. **Chuẩn hóa Atomic Task Slicing**: Bổ sung rào chắn trong `ccba-to-spec`: Mọi spec khi bẻ ticket phải đảm bảo $\le 200$ dòng diff, 1 Seam duy nhất.

#### Giai đoạn 2: Tự Động Hóa Có Kiểm Soát (Sau khi ổn định Giai đoạn 1)
1. **Tích hợp Maskara Sanitize Action**: Đảm bảo diff được làm sạch PII trước khi gửi đến bất kỳ cloud reviewer nào.
2. **Thử nghiệm Auto-Merge cho tài liệu**: Cho phép tự động merge các PR chỉ thay đổi tệp `.md/` hoặc docstrings sau khi vượt qua lint test.

---

## 5. Tài Liệu Tham Chiếu & Citations

1. **Hiến chương CCBA Layer 1:** [`AGENTS.md`](file:///home/vvc/ccba/ccba-agent-platform/AGENTS.md) — *ADR-0058 (Deterministic Hard Completion Lock), Multi-Client Peer Claim Locking Invariant, Static Seam Verification*.
2. **Bộ Kiểm Chứng Nền Tảng:** [`packages/ccba-harness/src/ccba_harness/verifier.py`](file:///home/vvc/ccba/ccba-agent-platform/packages/ccba-harness/src/ccba_harness/verifier.py) — *PatchVerificationReport, execute_command, run_patch_verification*.
3. **Rào Chắn Vận Hành & An Toàn:** [`docs/rules/execution_guardrails.md`](file:///home/vvc/ccba/ccba-agent-platform/docs/rules/execution_guardrails.md) — *Copilot review guardrails, Multi-Agent Peer Claim Locking, Pre-push lease protocol*.
4. **Rào Chắn Bảo Mật Thông Tin:** [`packages/ccba-maskara/AGENTS.md`](file:///home/vvc/ccba/ccba-agent-platform/packages/ccba-maskara/AGENTS.md) — *Redact secrets and sensitive PII invariant*.
5. **Circuit Breaker Pattern:** [`.agents/skills/ccba-api-circuit-breaker/SKILL.md`](file:///home/vvc/ccba/ccba-agent-platform/.agents/skills/ccba-api-circuit-breaker/SKILL.md) — *Rate limiting & cascading failure avoidance*.
6. **Cursor Bugbot Product Documentation:** [Bugbot by Cursor](https://cursor.com/bugbot) — *Logic bug detection, low false-positive rate, custom review rules*.

---

## 6. Câu Hỏi Chưa Làm Rõ (Unresolved Questions)

1. **Chi phí Token thực tế khi kích hoạt Bugbot trên toàn bộ repo:** Cần đo lường thực tế số lượng review calls trong 1 tuần thử nghiệm để đánh giá xem có ảnh hưởng đến hạn ngạch chung của team hay không.
2. **Mức độ tương thích giữa Bugbot Rules và GitHub Copilot Workspace:** Cần kiểm chứng xem cú pháp rules dạng markdown có được cả Cursor và Copilot parse tối ưu cùng lúc hay không.
