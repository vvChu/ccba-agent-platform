# refactor(evals): harden auto-tuner configuration precedence, concurrency token budgeting, and event loop decoupling

> **Loại công việc:** `enhancement` / `refactor`  
> **Nguồn gốc:** Đúc kết từ đợt kiểm toán đối kháng chuyên sâu (`/boost`) trên tài liệu `walkthrough.md` và kết quả thực nghiệm hai phiên chạy Nightly Auto-Tuner ngày 25/09 và 26/09/2026.  
> **Quy chuẩn tham chiếu:** ADR-0023 (SkillOpt), ADR-0052 (Plateau Boost), ADR-0058 (Hard Completion Lock).

---

## 1. Tóm Tắt & Bối Cảnh (Context)

Trong quá trình thẩm định và nghiệm thu gói nâng cấp Async Continuous Batching cho CCBA Nightly Auto-Tuner (`feat/nightly-tuner-hardening-and-async-batching`), cuộc kiểm toán đối kháng độc lập (**Double-Pass Adversarial Audit**) đã bóc tách được **5 điểm mù và rủi ro kiến trúc** cần được nghiên cứu và xử lý trong lộ trình tiếp theo nhằm bảo đảm tính ổn định lâu dài của hệ thống.

---

## 2. Chi Tiết 5 Rủi Ro Kiến Trúc Cần Nghiên Cứu (Architectural Risks)

### 2.1. Lỗi Đảo Ngược Độ Ưu Tiên Cấu Hình (Configuration Precedence Inversion)
- **Hiện tượng:**
  Trong `RatchetConfig` (`tuner.py`) và `NightlyTunerDaemon` (`daemon.py`), một số tham số cấu hình đang kiểm tra giá trị mặc định để nạp biến môi trường:
  ```python
  if self.concurrency == 5:
      env_concurrency = os.getenv("CCBA_TUNER_CONCURRENCY")
      if env_concurrency:
          self.concurrency = int(env_concurrency)

  if self.per_skill_mutation_budget == 250_000:
      env_ps_budget = os.getenv("CCBA_TUNER_PER_SKILL_MUTATION_BUDGET")
      if env_ps_budget:
          self.per_skill_mutation_budget = int(env_ps_budget)
  ```
- **Rủi ro:** Khi người dùng truyền tường minh giá trị đúng bằng mặc định (`concurrency=5` hoặc `per_skill_mutation_budget=250_000`) nhưng biến môi trường trên server đặt giá trị khác (ví dụ `CCBA_TUNER_CONCURRENCY=10`), biến môi trường sẽ âm thầm ghi đè lựa chọn của người dùng.
- **Giải pháp đề xuất:** Chuyển các giá trị mặc định sang sentinel `None` (tương tự trường `token_budget: int | None = None`). Nếu tham số là `None` $\to$ nạp từ env; nếu khác `None` $\to$ tuyệt đối ưu tiên giá trị do người dùng truyền vào.

---

### 2.2. Nguy Cơ Tràn Ngân Sách Token khi Chạy Bất Đồng Bộ (Concurrency Token Budget Overshoot)
- **Hiện tượng:**
  Trong `LLMTaskAdapter.create_async_eval_task`:
  ```python
  if self.token_tracker.is_exhausted:
      raise TokenBudgetExceededError(...)
  res = await call_fn(...)
  self.token_tracker.record_usage(p_tok, c_tok, latency_s=latency)
  ```
- **Rủi ro:** Khi $N$ tasks (`max_concurrency=5`) được bắn đồng thời qua `asyncio.gather`, tại thời điểm token tracker sắp chạm trần ngân sách (ví dụ chỉ còn 5,000 tokens), cả 5 tasks đều kiểm tra `is_exhausted == False` tại cùng một thời điểm trước khi có task nào hoàn tất để gọi `record_usage()`. Ngân sách thực tế có thể vượt trần một lượng $N \times \text{tokens/item}$.
- **Giải pháp đề xuất:** Bổ sung cơ chế **Token Reservation / Pre-allocation Barrier** (đặt cọc trước một lượng token ước lượng trước khi dispatch HTTP call, và hoàn trả/cập nhật sau khi nhận response).

---

### 2.3. Thiếu Ngưỡng Trần Cứng Ngân Sách Đột Biến Cho Kỹ Năng Đơn Lẻ (`hard_max_tokens_per_skill`)
- **Hiện tượng:**
  Trong `tuner.py:2088-2094`:
  ```python
  if (
      self.config.per_skill_mutation_budget is not None
      and mutation_tokens >= self.config.per_skill_mutation_budget
      and kept_count == 0  # <--- Chỉ dừng khi chưa có commit cải thiện nào!
  ):
  ```
- **Rủi ro:** Nếu một kỹ năng cải thiện nhẹ ở vòng đầu (`kept_count=1`), cơ chế bảo vệ 250k token bị vô hiệu hóa. Điển hình trong đêm 25/09, `ccba-design` tiêu tốn gần **2M tokens** (~20% ngân sách đêm). Sang đêm 26/09, `ccba-design` tiếp tục tiêu tốn **975,856 tokens** (~74% token toàn đêm) mà không đạt thêm cải thiện nào (`HALT_NO_FURTHER_STRATEGIES`).
- **Giải pháp đề xuất:** Bổ sung trần cứng `hard_max_tokens_per_skill` (ví dụ: tối đa 500,000 tokens/kỹ năng), bất kể `kept_count` có lớn hơn 0 hay không, ngăn chặn triệt để một kỹ năng độc chiếm tài nguyên của các kỹ năng phía sau.

---

### 2.4. Khả Năng Tương Thích Event Loop của `GitRatchetOptimizer` (Native Async Coroutine Support)
- **Hiện tượng:**
  `GitRatchetOptimizer.evaluate_content` hiện gọi `self.runner.run_sync()`. Trong `EvalRunner.run_sync`:
  ```python
  if loop and loop.is_running():
      raise RuntimeError("EvalRunner.run_sync() cannot be called from within a running event loop.")
  return asyncio.run(...)
  ```
- **Rủi ro:** Nếu tuner được nhúng vào một runtime bất đồng bộ (FastAPI, Async Agent Coordinator, hoặc bài test có `@pytest.mark.asyncio`), lời gọi sẽ sập ngay lập tức với `RuntimeError`.
- **Giải pháp đề xuất:** Bổ sung native coroutine `async def evaluate_content_async(...)` và `async def run_async(...)` song song với các interface đồng bộ hiện có.

---

### 2.5. Bảo Toàn Type Safety Trong `EvalRunner` (Lưu Exception Object Thay Vì Ép Chuỗi)
- **Hiện tượng:**
  Trong `EvalRunner`, mọi exception bị bắt và ép chuỗi thành `f"Task execution failed: {e}"` lưu vào trường `EvalItemResult.error: str | None`. Các lớp phía trên muốn nhận biết lỗi (như `CircuitBreakerOpenError` hoặc `TokenBudgetExceededError`) phải dùng regex so chuỗi.
- **Rủi ro:** Lỗi bị che giấu stack trace và làm mất tính an toàn kiểu dữ liệu (Type Safety) của Python.
- **Giải pháp đề xuất:** Bổ sung trường `exception: Exception | None = None` vào `EvalItemResult`, cho phép sử dụng `isinstance(result.exception, CircuitBreakerOpenError)` trực tiếp.

---

## 3. Tiêu Chí Nghiệm Thu (Acceptance Criteria)

- [ ] `RatchetConfig` và `NightlyTunerDaemon` sử dụng sentinel `None` cho các tham số có thể nạp từ biến môi trường.
- [ ] Bổ sung cơ chế đặt chỗ token reservation ngăn ngừa token budget overshoot khi chạy concurrent.
- [ ] Bổ sung tham số trần cứng `hard_max_tokens_per_skill` ngắt chu kỳ đột biến khi chạm ngưỡng token tuyệt đối.
- [ ] Cung cấp phương thức `evaluate_content_async` và `run_async` cho `GitRatchetOptimizer`.
- [ ] Thêm trường `exception: Exception | None` vào `EvalItemResult` và tái cấu trúc việc kiểm tra lỗi bằng `isinstance()`.
- [ ] Toàn bộ unit tests hiện có và bài test mới đạt 100% PASS, vượt qua `verify-patch --preset code`.
