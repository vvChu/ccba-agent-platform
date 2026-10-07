---
name: ccba-vllm-manager
description: Quản trị mô hình vLLM trên DGX Spark Blackwell GB10, tối ưu hóa AOT Inductor cache, và cấu hình phân tách reasoning/tool parsers.
applies_to:
- Phần mềm
- Tác vụ Admin
bundle: _software
tier: kernel
command: /ccba-vllm-manager
metadata:
  version: "1.1.0"
  author: "CCBA Hub"
gpi:
  s: 3.0
  k: 2.0
  a: 3.0
  p: 1.0
triggers:
- vllm
- qwen
- reasoning parser
- inductor cache
- dgx spark
- local llm
---

# vLLM Manager

Kỹ năng này cung cấp cho Agents và Kỹ sư hạ tầng toàn bộ tri thức và chỉ dẫn vận hành để quản lý **vLLM model serving** trên máy trạm NVIDIA DGX Spark (128GB LPDDR5x unified memory, chip Grace Blackwell GB10).

| Model vật lý | Functional Alias | Port vLLM | Container | VRAM / RAM | Đặc tính kỹ thuật |
|---|---|---|---|---|---|
| Qwen3.6-35B-A3B-FP8 | `rag-core` / `local-coder` | 8004 | `qwen36b` | ~35GB (50G cap) | ✅ MoE + FlashInfer + Dual Parser (`qwen3` / `qwen3_coder`) |
| Qwen3.6-35B (Instruct) | `local-instruct` | 8090 (Gateway) | Via `qwen36b` | — | ✅ Forced `enable_thinking: False`, siêu tốc độ ~0.4s |
| Qwen2.5-Coder-7B AWQ | `rag-light` | 8003 | `qwen3-9b` | ~10GB | ✅ Fast Fallback (AWQ 4-bit) |

> [!TIP]
> **Quy tắc Bất Biến Routing**: LUÔN sử dụng functional aliases (`local-instruct`, `rag-core`, `local-coder`) thay vì nhúng tên mô hình vật lý trực tiếp vào mã nguồn.

---

## 🏛️ Platform-Aware Architecture Posture (ADR-0061)

Skill này thuộc thế năng **`seam-exempt`** (hạ tầng & vận hành container model serving cấp OS/Docker). Không kết nối trực tiếp với Seam Contract ứng dụng mà đóng vai trò hướng dẫn quản trị runtime cho cụm máy chủ suy luận vLLM trên DGX Spark.

---

## 1. Tối Ưu Hóa Hạ Tầng: AOT Inductor Cache Volume Mount

Dòng mô hình hybrid attention + MoE thế hệ mới (như Qwen 3.6) sử dụng `torch.compile` / Inductor graph để tăng tốc độ inference. Mỗi lần container vLLM khởi động lại, quá trình biên dịch đồ thị AOT mất từ **35 - 45 giây**.

### Chỉ dẫn Volume Mount Bắt Buộc
BẮT BUỘC mount thư mục lưu trữ cache từ host vào container trong `docker-compose.yml` hoặc lệnh `docker run`:

```yaml
# Trích đoạn docker-compose.yml dịch vụ vllm-36b
services:
  vllm-36b:
    image: vllm/vllm-openai:latest
    container_name: qwen36b
    volumes:
      - ${VLLM_CACHE_DIR}:/root/.cache/vllm  # Persistent AOT Inductor Cache
      - ${HF_HOME}:/root/.cache/huggingface
    ipc: host
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

> [!IMPORTANT]
> Việc mount `${VLLM_CACHE_DIR}:/root/.cache/vllm` giúp vLLM nạp lại đồ thị đã biên dịch ngay lập tức khi container khởi động lại, triệt tiêu thời gian chờ 40s.

---

## 2. Cấu Hình Phân Tách Parser (Dual Parser & Anti-Double-Parser)

Khi sử dụng Qwen 3.6 với cả khả năng suy luận (Reasoning CoT) và gọi công cụ (Tool / Function Calling), cấu hình parser phải tuân thủ nghiêm ngặt nguyên tắc phân định vai trò:

### Cấu hình phía vLLM Container
Khởi động container với các cờ parser chuyên dụng:
```bash
python3 -m vllm.entrypoints.openai.api_server \
  --model /models/Qwen3.6-35B-A3B-FP8 \
  --served-model-name qwen3.6-35b \
  --reasoning-parser qwen3 \
  --tool-call-parser qwen3_coder \
  --max-model-len 24576 \
  --gpu-memory-utilization 0.50 \
  --kv-cache-dtype fp8
```

### Rào Chắn Tránh Xung Đột Double-Parser tại LiteLLM Gateway
- Khi vLLM đã bật `--tool-call-parser qwen3_coder`, vLLM sẽ tự động bóc tách cú pháp gọi hàm `xml/hermes` và xuất ra JSON function calls chuẩn OpenAI.
- **CẤM** cấu hình thêm `tool_call_parser: openai` tại file `config.yaml` của LiteLLM cho cùng endpoint vLLM này. Việc cấu hình trùng lặp sẽ gây xung đột kép (double-parser), làm méo mó schema tham số hàm trả về cho Client.

---

## 3. Quản Lý Thinking Token & Fast Extraction

Theo chuẩn mực **RULE-5.8**:
- Khi cần trích xuất JSON hoặc sinh HyDE queries (`max_tokens <= 512`), BẮT BUỘC gọi qua alias `local-instruct` hoặc gửi:
  ```json
  {
    "chat_template_kwargs": {
      "enable_thinking": false
    }
  }
  ```
- Không bao giờ dựa vào system prompt để yêu cầu mô hình reasoning ngừng suy nghĩ.

---

## 4. Kiểm Tra Sức Khỏe & Giám Sát Tài Nguyên (Health Check)

```bash
# 1. Kiểm tra nhanh trạng thái các containers
docker ps -a --filter "name=qwen" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 2. Kiểm tra endpoint readiness
curl -s http://localhost:8004/v1/models | jq

# 3. Kiểm tra qua AI Gateway (Functional Alias)
curl -s http://localhost:8090/v1/models -H "Authorization: Bearer $LITELLM_MASTER_KEY" | jq

# 4. Kiểm tra metrics hiệu năng vLLM (Prometheus endpoint)
curl -s http://localhost:8004/metrics
```

### Các chỉ số Prometheus trọng yếu
- `vllm:num_requests_running`: Số lượng request đang xử lý đồng thời.
- `vllm:gpu_cache_usage_perc`: Tỷ lệ sử dụng bộ nhớ KV Cache. Nếu $> 95\% \to$ có nguy cơ OOM hoặc trễ cao.
- `vllm:avg_generation_throughput_toks_per_s`: Tốc độ sinh token thực tế (kỳ vọng $\ge 120-160$ tok/s trên Blackwell GB10).

---

## 5. Xử Lý Sự Cố Thường Gặp (Troubleshooting)

### Sự cố 1: Container bị Out of Memory (OOM) hoặc VRAM Fragmented
```bash
# Khởi động lại container 35B để giải phóng KV cache
docker restart qwen36b
# Kiểm tra bộ nhớ thống nhất
nvidia-smi
```

### Sự cố 2: Thinking Token Starvation (JSON trả về rỗng)
- **Hiện tượng**: `finish_reason: "length"`, `content: None` hoặc `""`.
- **Khắc phục**: Chuyển sang gọi model alias `local-instruct` hoặc thêm `"chat_template_kwargs": {"enable_thinking": false}`.

## Bộc Lộ Dần & Cấu Trúc Tinh Gọn (Progressive Disclosure)
* **Cấu trúc tài liệu Level 3:** Phân tách rõ ràng giữa quy trình cốt lõi và tài liệu hướng dẫn chuyên sâu qua bảng chỉ mục Level 3.
* **Tham chiếu liên kết:** Mọi tài liệu mở rộng tuân thủ cơ chế bộc lộ dần theo cấp độ (Level 1/2/3 Progressive Disclosure) và được dẫn xuất qua bảng chỉ mục Level 3.
* **Chống rác dữ liệu (Anti-Debris Invariant):** Không để lại comment nháp, TODO tạm thời hay các chỉ thị thừa không cần thiết.
