# Hướng Dẫn Truy Cập Từ Xa (Remote Access)

Tài liệu này hướng dẫn cách kết nối từ máy cá nhân tới các dịch vụ AI trên Server Spark.

## 1. Thông Tin Server (Spark)

| | |
|---|---|
| **Hostname** | `spark-CCBA` |
| **IP Tailscale** | `100.83.192.30` |
| **AI Gateway** | port `8090` — 22 models |
| **API Key** | `$LITELLM_MASTER_KEY` (xem `.env`) |

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
# Chạy trên máy Client:
ssh -N -L 8090:localhost:8090 vvc@<LAN_IP>

# Sau đó dùng localhost:
curl http://localhost:8090/v1/models \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY"
```

---

## 4. Setup Client Chi Tiết

> 📖 Xem hướng dẫn đầy đủ + file cấu hình sẵn dùng tại:
> - **Guide**: [`playbooks/client-setup-guide.md`](./client-setup-guide.md)
> - **Files**: [`examples/client-setup/`](../examples/client-setup/)
>   - `.env.ai-gateway` — Template biến môi trường
>   - `test-connection.sh` — Script test kết nối
>   - `ai_client.py` — Python module sẵn dùng
>   - `ai-client.ts` — TypeScript module sẵn dùng
