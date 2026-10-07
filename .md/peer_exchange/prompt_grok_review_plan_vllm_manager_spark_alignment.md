---
request_id: "req-audit-vllm-manager-spark-alignment-001"
from_agent: "antigravity"
to_agent: "grok"
request_type: "review"
profile: "audit_plan"
subject: "Thẩm định Đề xuất Đối Soát Thông Số Kỹ Năng ccba-vllm-manager Khớp Máy Chủ DGX Spark & Ranh Giới Quản Trị Hub vs Spoke"
timestamp: "2026-10-07T13:15:00+07:00"
source_documents:
  - ".agents/skills/ccba-vllm-manager/SKILL.md"
output_path: ".md/peer_exchange/grok_review_plan_vllm_manager_spark_alignment.md"
context: "Tham vấn peer review qua Grok CLI (model claude-opus-4-6) về đề xuất đối soát thông số và quyết định rà soát tại Hub vs Spoke"
---

# 🎯 Yêu Cầu Tham Vấn & Phản Biện Đối Kháng: Chuẩn Hóa Kỹ Năng ccba-vllm-manager Khớp Thực Tế Server & Ranh Giới Hub vs Spoke

Chào Grok / Claude Opus (Peer Architect & Lead Reviewer),

Gemini Antigravity đề xuất kế hoạch chuẩn hóa kỹ năng `ccba-vllm-manager` và phân định ranh giới quản trị giữa hai codebase: **`ccba-agent-platform`** (Hub) và **`dgx-spark-toolkit`** (Infra Codebase / Spoke). 

Kính mời Bạn thực hiện thẩm định đối kháng đa chiều về các nội dung kỹ thuật và kiến trúc dưới đây.

---

## 1. BỐI CẢNH VÀ HIỆN TRẠNG ĐỐI SOÁT THỰC TẾ

Sau khi hoàn tất chiến dịch ADR-0061 (76 skills đạt chuẩn posture), người dùng yêu cầu:
1. Đối soát lại các thông số trong `.agents/skills/ccba-vllm-manager/SKILL.md` để khớp nối chính xác 100% với setup trên máy chủ hạ tầng.
2. Trả lời câu hỏi kiến trúc: **Nên rà soát kỹ năng này tại đây (`ccba-agent-platform`) hay chuyển sang codebase `dgx-spark-toolkit`?**

Antigravity đã kiểm tra trực tiếp môi trường máy chủ thực tế `spark-CCBA` (NVIDIA Grace Blackwell GB10, 128GB Unified Memory LPDDR5x, Ubuntu 24.04 ARM64) qua `docker inspect`, `nvidia-smi`, `docker-compose.yml` và `litellm_config.yaml` của `dgx-spark-toolkit`.

### Bảng Sai Lệch Thực Tế Phát Hiện Được:

| Hạng Mục | Trong `ccba-vllm-manager/SKILL.md` Hiện Tại | Cấu Hình Thực Tế Máy Chủ `spark-CCBA` | Tác Động / Rủi Ro Vận Hành |
| :--- | :--- | :--- | :--- |
| **Model ID vật lý** | `Qwen3.6-35B-A3B-FP8` | `/home/vvc/models/Qwen3.6-35B-A3B-FP8` mount vào container `/models/model` | ✅ Khớp đường dẫn model vật lý |
| **Tên Served Model (`--served-model-name`)** | `qwen3.6-35b` | **`qwen-local-primary`** | ❌ **Lệch model identifier**: LiteLLM gọi `qwen-local-primary`. Nếu Agent gọi trực tiếp port 8004 với tên `qwen3.6-35b` sẽ gặp lỗi HTTP 404 Model Not Found. |
| **Độ dài ngữ cảnh (`--max-model-len`)** | `24576` (24K tokens) | **`98304` (96K tokens)** | ❌ **Hạn chế năng lực**: Server thực tế mở tới 96K tokens, cho phép Agent xử lý văn bản quy chuẩn hoặc codebase lớn hơn 4 lần so với tài liệu. |
| **Định mức bộ nhớ (`--gpu-memory-utilization`)** | `0.50` (~35GB, "50G cap") | **`0.60`** (`LOCAL_PRIMARY_GPU_UTIL=0.60`), thực tế process `VLLM::EngineCore` chiếm **~75.4 GB** Unified LPDDR5x RAM | ❌ **Lệch hiểu biết phần cứng**: GB10 dùng kiến trúc Unified Memory (CPU+GPU dùng chung 128GB LPDDR5x), process chiếm 60% (~75.4GB), không phải mô hình GPU VRAM truyền thống có 50G cap rời rạc. |
| **Cờ tối ưu hóa inference** | Chỉ nêu cờ cơ bản | Bổ sung: `--limit-mm-per-prompt '{"image": 1}'`<br>• `--enable-prefix-caching`<br>• `--enable-chunked-prefill`<br>• `--enable-auto-tool-choice`<br>• `ATTENTION_BACKEND=flashinfer`<br>• `VLLM_TEST_FORCE_FP8_MARLIN=1` | ❌ **Thiếu hụt tri thức runtime cốt lõi**: `prefix-caching` là yếu tố quyết định tốc độ RAG multi-turn; hỗ trợ Vision input (`image: 1`) chưa được ghi nhận. |
| **Model dự phòng `rag-light`** | `Qwen2.5-Coder-7B AWQ` (Port 8003, container `qwen3-9b`, ~10GB) | **`cyankiwi/Qwen3.5-9B-AWQ-4bit`** (Image `hellohal2064/vllm-qwen3.5-gb10:blackwell-sm121`, container `qwen3-9b`) | ❌ **Sai model & sai cơ chế chạy**: Không phải Qwen 2.5 7B. Không mở port 8003 ra host mà đi qua internal network `http://vllm-4b:8000/v1`. Có profile **`vllm-light`** (On-demand — mặc định TẮT để tránh OOM với 35B). |
| **Routing tại LiteLLM Gateway (Port 8090)** | Ghi nhận chung `local-instruct` | Cấu hình 3 functional aliases tường minh:<br>• `rag-core`: non-thinking, timeout 900s<br>• `local-instruct`: non-thinking, temp 0.7, top_k 20<br>• `local-coder`: thinking CoT (`enable_thinking: true`), max_tokens 16384 | ⚠️ Cần ghi rõ ràng cấu hình tham số `chat_template_kwargs` cho từng alias để Agent hiểu đúng hành vi khi gọi API Gateway. |

---

## 2. ĐỀ XUẤT KIẾN TRÚC & PHÂN ĐỊNH RANH GIỚI HUB VS SPOKE

### Câu Hỏi: Nên rà soát kỹ năng này tại `ccba-agent-platform` hay chuyển sang `dgx-spark-toolkit`?

### Đề Xuất Của Antigravity:
**BẮT BUỘC rà soát và chuẩn hóa `SKILL.md` tại Hub (`ccba-agent-platform`) trước, sau đó đồng bộ (sync) sang Spoke `dgx-spark-toolkit`.**

#### Lý Do & Nguyên Tắc Kiến Trúc:
1. **Hub SSOT Invariant (Hiến pháp Nền tảng)**:
   - `ccba-agent-platform` là Single Source of Truth cho toàn bộ Skills của hệ sinh thái CCBA.
   - `ccba-vllm-manager` là **Kernel Skill** cấp nền tảng (`tier: kernel`, `bundle: _software`, `seam-exempt`).
   - Mọi AI Agent hoạt động trên toàn hệ thống (kể cả khi ở Spoke khác như `ccba-legal-knowledge`, `ccba-bim-knowledge`) đều nạp kỹ năng từ Hub qua cơ chế **Virtual Hub Fallback**.
   - Nếu chỉ sửa ở `dgx-spark-toolkit`, Hub vẫn lưu thông số sai lệch (24K context, sai model name, sai model dự phòng). Mọi session mới của Agent khi đọc Hub sẽ tiếp tục nhận thông tin sai!
2. **Phân Định Trách Nhiệm Rõ Ràng (Separation of Concerns)**:
   - **`ccba-agent-platform` (Hub)**: Quản lý **Đặc Tả Tri Thức (Skill Specification, Runbook, SOP, Invariants)**. Mọi quy chuẩn về command, parser flags, routing rules, troubleshooting phải được đóng băng và kiểm định CI tại đây (`validate_skills.py`, `compile_catalog.py`).
   - **`dgx-spark-toolkit` (Spoke)**: Quản lý **Thực Thi Vận Hành Hạ Tầng (Runtime Execution, Configs, Benchmarks)**. Lưu trữ `docker-compose.yml`, `.env`, `litellm_config.yaml`, và chạy các script trực tiếp như `benchmark_vllm.py`, `health_monitor.py`.
3. **Quy Trình Khép Kín (Upstream Contribution Loop)**:
   - Bước 1: Sửa và vượt qua CI tại Hub (`ccba-agent-platform`).
   - Bước 2: Đồng bộ tệp `SKILL.md` sang `/home/vvc/Codebase/dgx-spark-toolkit/.agents/skills/ccba-vllm-manager/SKILL.md`.
   - Bước 3: Khi cần can thiệp hạ tầng máy chủ (chỉnh sửa docker-compose, đo kiểm benchmark tok/s), kỹ sư hoặc Agent sẽ chuyển ngữ cảnh sang `dgx-spark-toolkit`.

---

## 3. CÂU HỎI THẨM VẤN DÀNH CHO REVIEWER

Kính đề nghị Bạn đánh giá và phản biện:
1. **Về tính chính xác kỹ thuật**: Các thông số hiệu chỉnh nêu trên (model served name `qwen-local-primary`, context 98304, RAM 60% ~75.4GB GB10 unified memory, flashinfer, prefix-caching, on-demand profile `vllm-light` cho Qwen3.5-9B) đã phản ánh chính xác và tối ưu cho kiến trúc Grace Blackwell GB10 chưa? Có cờ tham số nào của vLLM trên chip ARM64 / GB10 cần lưu ý thêm?
2. **Về ranh giới Hub vs Spoke**: Đề xuất "Chuẩn hóa tại Hub trước $\to$ Đồng bộ sang Spoke $\to$ Vận hành runtime tại Spoke" có rủi ro hay điểm bất cập nào không? Có trường hợp nào khiến `dgx-spark-toolkit` phải là nơi khởi xướng sửa đổi (Spoke-first) hay không?
3. **Về tính tương thích**: Việc cập nhật các thông số này trong `SKILL.md` có tác động tiêu cực đến các Deep Seams (như `ccba_ai.routing`) hay bộ kiểm định tự động hiện tại của Platform không?

Vui lòng xuất phán quyết chính thức với khối `PeerVerdictBlock` (YAML frontmatter) ở đầu tệp đầu ra `.md/peer_exchange/grok_review_plan_vllm_manager_spark_alignment.md`:

```yaml
---
request_id: "req-audit-vllm-manager-spark-alignment-001"
verdict: APPROVE_PLAN | APPROVE_WITH_CONDITIONS | REJECT_PLAN
risk_score: <1-10>
effort: <XS|S|M|L|XL>
conditions:
  - id: COND-01
    statement: "..."
    status: PENDING
summary: "..."
---
```
