# Hướng Dẫn Truy Cập Từ Xa (Remote Access)

Tài liệu này hướng dẫn cách kết nối từ máy cá nhân tới các dịch vụ AI trên Server Spark.

## 1. Thông Tin Server (Spark)

| | |
|---|---|
| **Hostname** | `spark-CCBA` |
| **IP Tailscale** | `100.83.192.30` |
| **AI Gateway** | port `8090` — 44 models |
| **Direct vLLM Primary** | port `8004` — Qwen 35B (active) |
| **Direct vLLM Fallback** | port `8003` — (currently inactive/offline) |
| **API Key** | `$LITELLM_MASTER_KEY` (mặc định: `sk-spark-secure-key-2026`) |

---

## 2. Mở Firewall (Chạy 1 lần trên Server)

```bash
sudo bash /home/vvc/Codebase/dgx-spark-toolkit/scripts/setup-remote-access.sh
```

---

## 3. Kết Nối Từ Client

### Cách A: Tailscale VPN ⭐ (Khuyến nghị)

```bash
# Test kết nối
curl http://100.83.192.30:8090/v1/models \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY"
```

### Cách B: SSH Tunneling (qua Firewall)

```bash
# Chạy trên máy Client (mở tunnel cho AI Gateway :8090 và Direct vLLM Primary :8004):
ssh -N -L 8090:localhost:8090 -L 8004:localhost:8004 vvc@<LAN_IP>

# Sau đó dùng localhost để gọi AI Gateway:
curl http://localhost:8090/v1/models \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY"

# Hoặc truy cập vLLM trực tiếp trên port 8004:
curl http://localhost:8004/v1/models
```

> 💡 Port 8004 là direct vLLM primary (`qwen-local-primary`). Port 8003 (vLLM fallback) hiện tại ở trạng thái inactive/offline. Note: `<LAN_IP>` có thể thay thế bằng `<SERVER_IP>` tùy theo môi trường kết nối.

---

## 4. Setup Client Chi Tiết

> 📖 Xem hướng dẫn đầy đủ + file cấu hình sẵn dùng tại:
> - **Guide**: [`playbooks/client-setup-guide.md`](./client-setup-guide.md)
> - **Files**: [`examples/client-setup/`](../examples/client-setup/)
>   - `.env.ai-gateway` — Template biến môi trường
>   - `test-connection.sh` — Script test kết nối
>   - `ai_client.py` — Python module sẵn dùng
>   - `ai-client.ts` — TypeScript module sẵn dùng
