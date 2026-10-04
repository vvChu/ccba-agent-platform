# 🤝 THÔNG ĐIỆP BẮT TAY HAI CHIỀU (BIDIRECTIONAL PEER HANDSHAKE)

> **Antigravity** (Lead Architect & Builder) ⟷ **Grok** (Adversarial Auditor & Gatekeeper)  
> **Tiêu chuẩn giao thức**: ADR-0007 / Issue #458 (Structured Peer Exchange)  
> **Thư viện nền tảng**: `ccba_harness.peer`  

---

## 1. Trạng Thái Vận Hành Hiện Tại

- **Antigravity**: `idle`
- **Grok**: `idle`
- **Trạng thái kết nối**: Đồng bộ tự động qua `scripts/peer_bridge_watcher.py`.

---

## 2. Quy Ước Trao Đổi Hai Chiều Chuẩn Hóa

| Luồng | Tệp yêu cầu | Tệp phản hồi |
|---|---|---|
| **Antigravity ⟶ Grok** | `prompt_grok_<subject>.md` | `grok_<subject>.md` |
| **Grok ⟶ Antigravity** | `grok_request_antigravity_<subject>.md` | `antigravity_response_<subject>.md` |

Mọi file bắt buộc có YAML front-matter envelope hợp lệ theo `ccba_harness.peer`.
Dùng CLI helper để khởi tạo nhanh:
```bash
python scripts/peer_request_template.py --from grok --to antigravity --type implement --subject "..."
```
