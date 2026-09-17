# Báo cáo Nghiệm thu Kỹ thuật (Walkthrough) — Issue #280

**Mã Issue:** [#280](https://github.com/vvChu/ccba-agent-platform/issues/280)  
**Tiêu đề:** `fix(ccba-ai): resolve embedding HTTP 400, streaming token truncation, and add timeout scaling for large completions`  
**Nhánh:** `fix/issue-280-embedding-streaming-timeout`

---

## 1. Tóm tắt Thay đổi (Changes Made)

### Gói `ccba-ai` v1.2.0

1. **Khắc phục HTTP 400 cho Embedding (`ai.embed()` & `async_ai.embed()`):**
   - Đổi model mặc định từ `text-embedding-3-small` sang `gemini-embedding-2`.
   - Đính kèm `extra_body={"drop_params": True}` khi gọi `embeddings.create()` qua OpenAI SDK để LiteLLM tự động drop tham số `encoding_format: "base64"` trước khi forward tới Gemini API.
   - Bổ sung phương thức `AsyncAIClient.embed()` hỗ trợ native coroutine.
   - Cập nhật mock mode trả về vector 3072 chiều tương thích chuẩn `gemini-embedding-2`.
   - Bổ sung `MockEmbeddingsResource` cho `MockOpenAIClient` và `AsyncMockOpenAIClient`.

2. **Khắc phục Cắt cụt Luồng Streaming Tokens (`stream()` & `async stream()`):**
   - Áp dụng `resolve_max_tokens(target_model, max_tokens, baseline_default=1024, reasoning_allocation=16384)` trước khi khởi tạo streaming request.
   - Với các reasoning models (như `gemini-3.7-flash-high`, `-thinking`), `max_tokens` tự động nâng trần lên 16,384 tokens nếu caller để mặc định 1024, ngăn chặn việc suy luận làm cạn token stream.

3. **Bổ sung Tham số `timeout` & Cơ chế Auto-Timeout Scaling:**
   - Thêm `timeout: float | None = None` vào `chat()`, `chat_with_metadata()` (sync & async).
   - Áp dụng công thức Auto-Timeout Scaling đồng bộ cho cả `chat()`, `chat_with_metadata()` và `chat_multi()`:
     ```python
     if timeout is not None:
         effective_timeout = float(timeout)
     elif effective_max_tokens > 16384:
         effective_timeout = max(self.timeout, effective_max_tokens / 50.0)
     else:
         effective_timeout = self.timeout
     ```
   - Truyền `timeout=effective_timeout` vào request body lẫn fallback router.

4. **Bóc tách Độc lập `ChatResult.thinking` phục vụ Audit Trail:**
   - Thêm trường `thinking: str = ""` vào `ChatResult` (trong `models.py`).
   - Bổ sung `extract_thinking` và `extract_thinking_and_content` vào `LLMOutputParser` (sử dụng depth-tracking parser xử lý mượt mà cả thẻ lồng nhau, nhiều thẻ, lẫn unclosed tags).
   - Trong `chat_with_metadata()`, ưu tiên nhận `reasoning_content` từ OpenAI API spec hoặc trích xuất từ `<think>...</think>`. Khi `strip_thinking=True`, `content` sạch 100% trong khi `thinking` lưu giữ toàn bộ chuỗi tư duy độc lập.

5. **Đồng bộ Phiên bản & Triệt tiêu Pytest Warnings:**
   - Cập nhật `version = "1.2.0"` trong `pyproject.toml`.
   - Đăng ký markers `fast` và `unit` trong `pyproject.toml`, loại bỏ hoàn toàn 12 cảnh báo pytest unknown mark.
   - Cập nhật `ModelArchetype` bổ sung `ModelArchetype.GEMINI_38_FLASH`, `ModelArchetype.GEMINI_31_PRO_HIGH`, `ModelArchetype.CLAUDE_OPUS_46`, `ModelArchetype.EMBEDDING = "gemini-embedding-2"`.

---

## 2. Kết quả Kiểm định Tự động (Automated Verification)

### 2.1. Scoped Tests & Full Test Suite
- Chạy 100% bộ kiểm thử:
  ```powershell
  python -m pytest packages/ccba-ai/tests -q
  ```
  **Kết quả:** `173 passed, 0 warnings in 225.41s` (100% PASS, 0 warning).

### 2.2. Linter & Type Safety
- **Ruff Check:**
  ```powershell
  python -m ruff check packages/ccba-ai/
  ```
  **Kết quả:** `All checks passed!` (0 errors).
- **Mypy Type-Check:**
  ```powershell
  python -m mypy packages/ccba-ai/src/ccba_ai/
  ```
  **Kết quả:** `Success: no issues found in 25 source files` (Strict type safety).

### 2.3. Live Smoke Test trên Gateway Spark (100.83.192.30:8090)
- Kiểm tra trực tiếp cuộc gọi `embed()` và `async embed()` với LiteLLM proxy:
  ```powershell
  python -c "..."
  ```
  **Kết quả:**
  ```
  Sync embed SUCCESS! Length: 1 Dim: 3072
  Async embed SUCCESS! Length: 1 Dim: 3072
  ```
  Không còn bất kỳ lỗi HTTP 400 nào.

---

## 3. Đối chiếu Tiêu chí Nghiệm thu (Acceptance Criteria)

| Tiêu chí Nghiệm thu (Issue #280) | Trạng thái | Ghi chú kiểm chứng |
| :--- | :---: | :--- |
| `ai.embed()` & `async_ai.embed()` gọi thành công với `gemini-embedding-2` trên Gateway không vấp HTTP 400 | **PASS** | Đã xác thực cả unit test mock lẫn live smoke test trên Server Spark (dim=3072). |
| `stream()` & `async stream()` tự động nâng trần 16,384 tokens khi stream với reasoning models | **PASS** | `test_streaming_tokens.py` xác thực `create()` nhận `max_tokens=16384`. |
| `ai.chat(..., max_tokens=32768, timeout=180.0)` hoạt động hợp lệ không văng ngoại lệ TypeError | **PASS** | `test_timeout_scaling.py` xác thực thành công. |
| `ChatResult.thinking` lưu trữ chuỗi tư duy độc lập với `ChatResult.content` | **PASS** | `test_thinking_audit.py` kiểm tra trích xuất thinking cả từ `<think>` lẫn `reasoning_content`. |
| Bộ kiểm thử `packages/ccba-ai/tests` vượt qua 100% tests với 0 warnings | **PASS** | Đạt 173/173 passed, 0 warnings. |
