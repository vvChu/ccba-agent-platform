# 📬 CCBA Peer Exchange Directory

Thư mục lưu trữ các thông điệp trao đổi song phương có cấu trúc giữa **Antigravity** và **Grok** (hoặc các AI agent khác) theo tiêu chuẩn **Structured Peer Exchange Protocol** (`ccba_harness.peer` / Issue #458 / ADR-0063..0067).

## Cấu Trúc Đặt Tên Tệp (File Naming Conventions)

| Hướng Tương Tác | Tên Tệp Yêu Cầu | Tên Tệp Phản Hồi |
|---|---|---|
| **Antigravity ⟶ Grok** | `prompt_grok_<subject>.md` | `grok_<subject>.md` |
| **Grok ⟶ Antigravity** | `grok_request_antigravity_<subject>.md` | `antigravity_response_<subject>.md` |

## Tiêu Chuẩn YAML Front-Matter

Mọi tệp trao đổi bắt buộc có header phong bì YAML front-matter được xác thực bởi Pydantic v2 model trong `ccba_harness.peer`:

- **Yêu cầu (Prompt)**: `PeerPromptEnvelope` (`request_id`, `conversation_id`, `task_id`, `spoke_name`, `tags`, `from_agent`, `to_agent`, `request_type`, `subject`, `timestamp`, `source_documents`, `output_path`, `profile`).
- **Phản hồi / Nghiệm thu (Verdict)**: `PeerVerdictBlock` (`request_id`, `verdict`, `conditions`, `risk_score`, `summary`, `telemetry`).

Ví dụ mẫu phong bì yêu cầu chuẩn:
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

## Lệnh Gọi Grok Thực Tế (Mandatory CLI Dispatch — ADR-0063..0067)

| Việc | Profile | Model | Trần |
|---|---|---|---|
| Plan lớn | `audit_plan` | `grok-4.7` | 12 turns, 900s |
| Kiến trúc vừa | `arch_audit` | `grok-4.7` | 8 turns, 600s |
| Nghiệm thu vòng 2 | `signoff_diff` | `grok-4.7`, `fork_session` | 8 turns, 600s |
| Review diff nhanh | `code_review` | `gemini-38-flash` | 10 turns, 300s |

Các profile còn lại (`audit_direct`, `patch_fast`, `deep_spec_audit`, `agentic_code`) xem tại `docs/rules/execution_coordination_guardrails.md` (§20.1); `peer.PROFILE_SPECS` là SSOT khi thông số lệch nhau.

```bash
ccba-harness peer-dispatch --prompt-file .md/peer_exchange/prompt_grok_<subject>.md --profile audit_plan
ccba-harness peer-watch --once --dir .md/peer_exchange
```

**Bất biến Chống Giả Lập (Anti-Spoofing Invariant)**: Cấm tuyệt đối Agent tự đóng vai Grok hoặc dùng `write_file`/`edit_file` để tự tạo tệp `grok_*.md` hay sửa tay `status.json`. Mọi phán quyết `grok_*.md` phải do `ccba-harness peer-dispatch` sinh ra kèm `telemetry.session_id` hợp lệ.
