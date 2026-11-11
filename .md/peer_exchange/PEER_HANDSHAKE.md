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

Lệnh dispatch Grok CLI thực tế (chọn profile phù hợp: `arch_audit` hoặc `code_review`):
```bash
ccba-harness peer-dispatch --prompt-file .md/peer_exchange/prompt_grok_<subject>.md --profile arch_audit
ccba-harness peer-watch --once --dir .md/peer_exchange
```
