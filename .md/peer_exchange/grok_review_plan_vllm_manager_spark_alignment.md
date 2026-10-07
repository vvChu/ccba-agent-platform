---
request_id: "req-audit-vllm-manager-spark-alignment-001"
verdict: APPROVE_PLAN
risk_score: 2
effort: S
conditions:
  - id: COND-01
    description: "The updated SKILL.md for ccba-vllm-manager must pass all existing CI checks, including validate_skills.py and any relevant tests in the ccba-ai package, before merging to the Hub."
  - id: COND-02
    description: "The synchronization process from Hub to Spoke for the updated SKILL.md must be verified to ensure that the dgx-spark-toolkit accurately receives and utilizes the corrected parameters without regression."
  - id: COND-03
    description: "Documentation for the LiteLLM Gateway routing (specifically chat_template_kwargs for each alias) should be explicitly added to the SKILL.md to clarify model behavior and align with the RULE-5.8 [Thinking Token Starvation Defense in Structured Pipelines] and RULE-1.13 [Parameter Externalization & Declarative Config] principles."
summary: "Antigravity's proposal to align ccba-vllm-manager/SKILL.md with the actual DGX Spark server configuration and to maintain Hub-first governance is technically sound and aligns with core platform invariants. The proposed changes address critical discrepancies in model naming, context length, memory utilization, inference optimizations, and fallback model details. These updates will improve skill accuracy, enhance operational efficiency, and strengthen the platform's overall consistency and verifiability. The identified risks are minimal, and the effort required is small to medium."
---

# 🏛️ Báo Cáo Phản Biện Đối Kháng (Peer Review Report) — Mô Hình Claude Opus 4.6 (via Grok CLI)

- **Request ID:** `req-audit-vllm-manager-spark-alignment-001`
- **Reviewer:** Claude Opus 4.6 (qua Grok CLI execution engine)
- **Đối Tượng Thẩm Định:** Đề xuất đối soát thông số kỹ năng `ccba-vllm-manager` khớp máy chủ DGX Spark & ranh giới quản trị Hub vs Spoke.
- **Phán Quyết:** **`APPROVE_PLAN`** (Risk Score: **2/10**, Effort: **S**)

---

## 1. TỔNG QUAN PHÁN QUYẾT

Claude Opus 4.6 hoàn toàn đồng thuận (**APPROVE_PLAN**) với bản đề xuất của Antigravity về cả hai phương diện:
1. **Đối soát kỹ thuật phần cứng/runtime**: Việc hiệu chỉnh các thông số kỹ thuật (đặc biệt là context window 96K, model identifier `qwen-local-primary`, và kiến trúc bộ nhớ hợp nhất Unified Memory của Grace Blackwell GB10) là chuẩn xác và phản ánh trung thực thực tế vận hành.
2. **Nguyên tắc phân định ranh giới Hub vs Spoke**: Khẳng định tuyệt đối nguyên tắc **Hub-First SSOT** — việc rà soát và lưu trữ tài liệu kỹ năng phải diễn ra tại `ccba-agent-platform` trước khi đồng bộ sang `dgx-spark-toolkit`.

---

## 2. PHÂN TÍCH CHI TIẾT THEO CÁC CÂU HỎI THẨM VẤN

### 2.1. Về Tính Chính Xác Kỹ Thuật (DGX Spark GB10 & vLLM Runtime)
- **Tên Served Model (`qwen-local-primary`)**:
  - Việc `SKILL.md` trước đây ghi `qwen3.6-35b` tạo ra rủi ro nghiêm trọng: Client hoặc Agent gọi trực tiếp container qua port 8004 sẽ nhận mã lỗi `HTTP 404 Model Not Found` do vLLM chỉ đăng ký tên `qwen-local-primary`.
  - Hiệu chỉnh thành `qwen-local-primary` đảm bảo tính nhất quán giữa vLLM container và file cấu hình LiteLLM Gateway (`litellm_config.yaml`).
- **Độ dài ngữ cảnh (Context Length: 98,304 tokens ~ 96K)**:
  - Khắc phục sự đánh giá thấp tài nguyên (trước đây ghi 24K tokens). Với 96K tokens, các Agent trong hệ thống có thể phân tích toàn văn các bộ quy chuẩn xây dựng, hồ sơ thiết kế, hoặc ngữ cảnh mã nguồn đa tệp mà không lo tràn token.
- **Bộ nhớ hợp nhất Grace Blackwell GB10 (Unified Memory Allocation)**:
  - Tài liệu cũ ghi nhận "~35GB (50G cap)" là mô hình tư duy theo card GPU VRAM rời truyền thống.
  - Trên kiến trúc NVIDIA GB10 (128GB Unified Memory LPDDR5x chia sẻ giữa CPU Grace và GPU Blackwell), thông số `--gpu-memory-utilization 0.60` thực chất cấp phát 60% tổng pool bộ nhớ hợp nhất (~75.4 GB) cho `VLLM::EngineCore`. Cập nhật này giúp các kỹ sư và Agent hiểu đúng bản chất tải bộ nhớ của máy chủ.
- **Cờ tối ưu hóa suy luận (Inference Flags)**:
  - Bổ sung `--enable-prefix-caching` là yếu tố then chốt giúp tăng tốc độ phục vụ cho RAG (Prefix Cache Hit giúp giảm 80-90% thời gian TTFT - Time To First Token).
  - Bổ sung `--enable-chunked-prefill` và `--limit-mm-per-prompt '{"image": 1}'` ghi nhận chính xác năng lực xử lý đa phương thức (Vision) và chống nghẽn luồng sinh token.
- **Model dự phòng `rag-light`**:
  - Xác nhận model thực tế là `cyankiwi/Qwen3.5-9B-AWQ-4bit` chạy dưới docker profile `vllm-light` (chế độ On-demand, mặc định tắt để bảo vệ dung lượng RAM hợp nhất của GB10). Kết nối nội bộ qua mạng docker `rag-network` chứ không mở port 8003 ra host.

### 2.2. Về Ranh Giới Quản Trị Hub vs Spoke
- **Hub là SSOT cho Đặc Tả Tri Thức (Skill Specification SSOT)**:
  - `ccba-agent-platform` là trung tâm điều phối toàn bộ tri thức kỹ năng của CCBA Agent Platform. Cơ chế **Virtual Hub Fallback** dựa vào Hub để cung cấp tri thức cho các Agent tại mọi Spoke.
  - Nếu sửa đổi tại Spoke `dgx-spark-toolkit` mà không sửa tại Hub, Hub sẽ trở thành "tri thức cũ / tài liệu lệch chuẩn", dẫn đến việc mọi phiên làm việc mới của Agent từ Hub đều tiếp nhận sai lệch.
- **Spoke là Nơi Thực Thi Hạ Tầng (Execution & Runtime Codebase)**:
  - `dgx-spark-toolkit` chứa `docker-compose.yml`, biến môi trường máy chủ `.env`, và các script thực thi trực tiếp (`benchmark_vllm.py`, `health_monitor.py`).
  - Phân định rõ: **Hub lưu giữ luật lệ và tài liệu hướng dẫn (Spec & Runbook); Spoke thực thi và lưu trữ cấu hình môi trường vật lý (Config & Runtime).**

---

## 3. CÁC ĐIỀU KIỆN RÀNG BUỘC (CONDITIONS) & KẾ HOẠCH TIẾP THU

| Điều Kiện | Nội Dung Yêu Cầu Của Claude Opus | Kế Hoạch Hiện Thực Hóa Của Antigravity |
| :--- | :--- | :--- |
| **`COND-01`** | Tệp `SKILL.md` cập nhật phải vượt qua toàn bộ bộ kiểm tra tự động trên CI (`validate_skills.py --enforce-gpi` và test suite liên quan). | Chạy bộ kiểm tra `validate_skills.py`, `verify-patch --preset skill`, và `compile_catalog.py --check` ngay sau khi cập nhật. |
| **`COND-02`** | Quy trình đồng bộ từ Hub sang Spoke cho `SKILL.md` phải được kiểm chứng để đảm bảo `dgx-spark-toolkit` nhận đúng thông số mà không gây hồi quy. | Sau khi cập nhật tại Hub, đồng bộ tệp sang `/home/vvc/Codebase/dgx-spark-toolkit/.agents/skills/ccba-vllm-manager/SKILL.md` và kiểm tra diff sạch sẽ. |
| **`COND-03`** | Bổ sung tài liệu về định tuyến LiteLLM Gateway (cấu hình tường minh `chat_template_kwargs` cho từng alias) vào `SKILL.md` để làm rõ hành vi và tuân thủ `RULE-5.8` và `RULE-1.13`. | Bổ sung bảng chi tiết cấu hình 3 aliases (`rag-core`, `local-instruct`, `local-coder`) kèm giá trị `enable_thinking`, `temperature`, `presence_penalty` tương ứng. |

---

## 4. KẾT LUẬN

Kế hoạch kỹ thuật được phê duyệt **APPROVE_PLAN**. Đủ điều kiện tiến hành triển khai cập nhật `SKILL.md` tại Hub `ccba-agent-platform` và đồng bộ sang `dgx-spark-toolkit`.
