# 🤝 THÔNG ĐIỆP BẮT TAY HAI CHIỀU (BIDIRECTIONAL PEER HANDSHAKE)

> **Antigravity** (Lead Architect & Builder) ⟷ **Grok** (Adversarial Auditor & Gatekeeper)  
> **Tiêu chuẩn giao thức**: ADR-0007 / ADR-0063..0067 / Issue #458 (Structured Peer Exchange)  
> **Thư viện nền tảng**: `ccba_harness.peer`  

---

## 1. Trạng Thái Vận Hành Hiện Tại

- **Antigravity**: `idle`
- **Grok**: `idle`
- **Trạng thái kết nối**: Đồng bộ qua `ccba-harness peer-watch --once --dir .md/peer_exchange`.

---

## 2. Bất Biến Chống Giả Lập & Triển Khai Thực Tế (Anti-Spoofing & Non-Simulation Invariant)

- **CẤM TUYỆT ĐỐI**: Không tự đóng vai Grok, không giả lập phản hồi của Grok, không dùng `write_file`/`edit_file` tự tạo `grok_*.md`, không sửa tay `status.json`.
- **MANDATORY CLI EXECUTION**: Mọi biên bản `grok_*.md` bắt buộc phải do lệnh thực thi CLI thật sinh ra qua `ccba-harness peer-dispatch`.
- **HỢP LỆ VỀ MẶT THỜI GIAN**: Mọi phán quyết phải có khối YAML `verdict` kèm `telemetry.session_id` thật từ Grok CLI.

---

## 3. Quy Ước Trao Đổi Hai Chiều Chuẩn Hóa

| Luồng | Tệp yêu cầu | Tệp phản hồi |
|---|---|---|
| **Antigravity ⟶ Grok** | `prompt_grok_<subject>.md` | `grok_<subject>.md` |
| **Grok ⟶ Antigravity** | `grok_request_antigravity_<subject>.md` | `antigravity_response_<subject>.md` |

Mọi file bắt buộc có YAML front-matter envelope hợp lệ theo `PeerPromptEnvelope` trong `ccba_harness.peer`:

```yaml
---
request_id: "req-20261111-plan-peer-sync-upgrade-001"
conversation_id: "0cbb4d3f-ee28-4985-8f9c-8cdea58eb14c"
task_id: "task-677"
spoke_name: "ccba-agent-platform"
tags: ["spoke-sync", "peer-coordination", "arch-audit"]
from_agent: "antigravity"
to_agent: "grok"
request_type: "plan"
profile: "arch_audit"
subject: "Thẩm Định Kế Hoạch Kiến Trúc: Nâng Cấp Cơ Chế Đồng Bộ Phối Hợp Ngang Hàng"
timestamp: "2026-11-11T06:33:00+07:00"
output_path: ".md/peer_exchange/grok_review_peer_coordination_sync_plan.md"
---
```

Lệnh dispatch Grok CLI thực tế (chọn `profile` theo bảng chuẩn `peer.PROFILE_SPECS` dưới đây):

| Việc | Profile | Model | Trần |
|---|---|---|---|
| Plan lớn | `audit_plan` | `grok-4.7` | 12 turns, 900s |
| Kiến trúc vừa | `arch_audit` | `grok-4.7` | 8 turns, 600s |
| Nghiệm thu vòng 2 | `signoff_diff` | `grok-4.7`, `fork_session` | 8 turns, 600s |
| Review diff nhanh | `code_review` | `gemini-38-flash` | 10 turns, 300s |

Các profile còn lại (`audit_direct`, `patch_fast`, `deep_spec_audit`, `agentic_code`) xem chi tiết tại `docs/rules/execution_coordination_guardrails.md` (§20.1); khi thông số lệch nhau thì `peer.PROFILE_SPECS` là SSOT.

```bash
# 1. Pass 1 — Thẩm định Kế hoạch (phiên mới):
ccba-harness peer-dispatch --prompt-file .md/peer_exchange/prompt_grok_<subject>.md --profile audit_plan

# 2. Pass 2–3 — Nghiệm thu Delta cùng pha (nối tiếp phiên cha kèm --fork-session):
ccba-harness peer-dispatch --prompt-file .md/peer_exchange/prompt_grok_<subject>_signoff.md --profile signoff_diff --resume <prev_session_id> --fork-session

# 3. Hậu triển khai — Kiểm toán mã nguồn độc lập (ghi `resume_session_id: "new"` trong YAML):
ccba-harness peer-dispatch --prompt-file .md/peer_exchange/prompt_grok_<subject>_impl_review.md --profile arch_audit
```

---

## 4. Kỷ Luật Điều Phối Vòng Lặp & Ranh Giới Tách Phiên (`v2.5`)

1. **Cổng Zero-Blocking & Trần 3 Vòng (`Max 3 Passes` — Kỷ luật vận hành của Agent):** Chừng nào phán quyết còn `blocking_conditions > 0` (kể cả khi `verdict` là `APPROVE_WITH_CONDITIONS`), Agent bắt buộc đối chiếu mã nguồn (`file:line`), cập nhật giải pháp và chạy tiếp `--profile signoff_diff --resume <prev_session_id> --fork-session` tối đa đến hết **Pass 3**. Chỉ trình User xin `proceed` khi đạt `blocking_conditions == 0`, hoặc sau **Pass 3** (báo cáo rõ điểm bất đồng kèm dẫn chứng `[REBUT_WITH_EVIDENCE]` để User phán quyết).
2. **Ranh Giới Tách Phiên Liên Pha (`Plan` $\ne$ `Post-Impl Code`):** `--fork-session` chỉ dùng để nghiệm thu Delta *trong cùng một pha*. Khi nghiệm thu code thực tế sau triển khai lớn, bắt buộc mở phiên mới (`resume_session_id: "new"` với `--profile arch_audit` hoặc `code_review`), tuyệt đối không fork từ phiên `audit_plan` cũ để tránh bẫy neo nhận thức (`Checklist Anchoring`).
3. **Chuyển Tiếp Artifact Ngoài Repo (`<appDataDir>/brain/`):** Grok CLI chỉ đọc tệp bên trong cây repo. Ở **Vòng 1**, nhúng trực tiếp nội dung kế hoạch vào thân `prompt_grok_<subject>.md` ($\le 350$ dòng / $\le 18\text{ KB}$) hoặc xuất bản sao tạm tại `.md/scratch/plan_<subject>.md` (cấm lưu `plan_*.md` / `pr_body_*.md` rời trong `.md/peer_exchange/`). Ở **Vòng 2+**, chỉ gửi bảng giải trình điều kiện + diff.
