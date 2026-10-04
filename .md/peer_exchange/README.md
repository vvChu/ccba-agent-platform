# 📬 CCBA Peer Exchange Directory

Thư mục lưu trữ các thông điệp trao đổi song phương có cấu trúc giữa **Antigravity** và **Grok** (hoặc các AI agent khác) theo tiêu chuẩn **Structured Peer Exchange Protocol** (`ccba_harness.peer` / Issue #458).

## Cấu Trúc Đặt Tên Tệp (File Naming Conventions)

| Hướng Tương Tác | Tên Tệp Yêu Cầu | Tên Tệp Phản Hồi |
|---|---|---|
| **Antigravity ⟶ Grok** | `prompt_grok_<subject>.md` | `grok_<subject>.md` |
| **Grok ⟶ Antigravity** | `grok_request_antigravity_<subject>.md` | `antigravity_response_<subject>.md` |

## Tiêu Chuẩn YAML Front-Matter

Mọi tệp trao đổi bắt buộc có header phong bì YAML front-matter được xác thực bởi Pydantic v2 model trong `ccba_harness.peer`:

- **Yêu cầu (Prompt)**: `PeerPromptEnvelope` (`request_id`, `from_agent`, `to_agent`, `request_type`, `subject`, `timestamp`, `source_documents`, `output_path`).
- **Phản hồi / Nghiệm thu (Verdict)**: `PeerVerdictBlock` (`request_id`, `verdict`, `conditions`, `risk_score`, `effort`, `summary`).
