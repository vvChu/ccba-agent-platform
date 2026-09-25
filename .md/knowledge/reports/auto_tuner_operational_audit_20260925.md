# Báo Cáo Kiểm Toán Toàn Diện Hiệu Năng & Kết Quả Vận Hành Của CCBA Auto-Tuner

> **Mã tài liệu:** `AUDIT-AUTO-TUNER-20260925`  
> **Thời gian thực hiện kiểm toán:** 25/09/2026 (07:30 - 07:45 GMT+7)  
> **Phương pháp kiểm toán:** Double-Pass Adversarial Review (Rule 8), Tracing Code End-to-End, Đo lường thực nghiệm trực tiếp trên hệ thống và Git Worktree ngầm.  
> **Quy chuẩn tham chiếu:** ADR-0023 (SkillOpt), ADR-0052 (Plateau Boost), ADR-0058 (Charter & Hard Completion Lock).  
> **Cấp độ quản trị:** `QC Level 2` — Phê duyệt bởi: `TRUONG_PHONG_RD_HTQT` | Thực thi: `KY_SU_THUC_THI`.

---

## 1. Tóm Tắt Quản Trị (Executive Summary)

Đợt kiểm toán vận hành ngày 25/09/2026 được tiến hành nhằm đánh giá toàn diện tính ổn định, hiệu quả cải tiến tri thức, và các nút thắt cổ chai kiến trúc của hệ thống **CCBA Auto-Tuner** chạy định kỳ mỗi đêm lúc 00:00 trên Server Spark (:8090).

### Các kết luận cốt lõi:
1. **Khắc phục triệt để sự cố PR #345:** Các bản vá hotfix PR #348 và PR #350 (merge ngày 24/09) đã phát huy hiệu quả xuất sắc. Hệ thống không còn tình trạng Goodhart Gaming, không còn lỗi đảo ngược thứ tự tiêu đề Markdown (Inverted Headings), và đã loại bỏ hoàn toàn hiện tượng tiêm nhiễm ADR bừa bãi.
2. **Tiến trình hôm nay (25/09) đạt hiệu suất thực chất cao:** Tính đến 07:35 sáng, daemon (PID `1360783`) đã chạy liên tục **7 giờ 35 phút**, xử lý được **36/73 kỹ năng** (~49.3%), sinh ra **8 commits cải tiến** chất lượng cao trên **7 kỹ năng** (mức tăng điểm thực chất từ `+0.5%` đến `+8.0%`).
3. **Phát hiện 2 "Điểm mù tử huyệt" đe dọa hệ thống:**
   - 🚨 **Nguy cơ tự động hủy PR hôm nay:** Do commit `31fc4fe9` vô tình làm mất tag `(ADR-0058)` trong `ccba-llm-pipeline-patterns/SKILL.md`, tệp `docs/adr/TRACEABILITY_MATRIX.md` trong worktree bị lệch đồng bộ. Hard Completion Lock trước khi tạo PR **chắc chắn sẽ thất bại**, khiến daemon hủy bỏ tạo PR và xóa sạch toàn bộ 8 commits cải tiến nếu không can thiệp trước 14:30 chiều nay!
   - 🔍 **Điểm mù vòng đời Ephemeral Worktree ban ngày:** Cơ chế trap shell xóa sạch worktree sau khi cron kết thúc khiến các công cụ giám sát đọc worktree bị sập vào ban ngày. Đã được khắc phục bằng công cụ mới với cơ chế **Dual-Mode Inspection**.
4. **Nguyên nhân gốc rễ của việc tràn cửa sổ ban đêm (12-15h thay vì 6h):** Không phải do giới hạn token, mà do:
   - Bẫy hàng đợi Cooldown (`WeightedPriorityQueue` chỉ xếp độ ưu tiên nhưng không có logic `continue` để bỏ qua kỹ năng cooldown).
   - I/O đồng bộ đơn luồng (`AIClient.chat_with_metadata` và rate limiter blocking sleep) làm nghẽn khả năng Continuous Batching của vLLM trên DGX Server Spark.

---

## 2. Kết Quả Kiểm Tra Thực Nghiệm (Live Empirical Audit: 25/09/2026)

### 2.1. Trạng Thái Vận Hành Trực Tiếp Của Daemon
- **Lệnh thực thi:** `python3 scripts/eval/nightly_tuner_daemon.py --max-iter 30 --use-real-llm --token-budget 10000000 --model qwen-local-primary`
- **PID hệ điều hành:** `1360783` `[đo thực tế: ps / fuser]`
- **Thời điểm khởi động:** `2026-09-25 00:00:26` `[phân tích log: nightly_cron.log:22757]`
- **Thời gian chạy liên tục (Uptime):** `07:35:00` `[đo thực tế: ps -o etime=]`
- **Môi trường cách ly:** Worktree `.worktrees/nightly-runner` trên nhánh `auto-tune/nightly-20260925_000026`
- **Tiến độ xử lý:** Đang tối ưu kỹ năng thứ **36/73** (`ccba-research`), hoàn thành **49.3%** hàng đợi.
- **Tốc độ gọi LLM trung bình:** **19.6 giây/request** (kết nối HTTP tới LiteLLM Spark :8090) `[đo thực tế]`.

### 2.2. Danh Sách 8 Commits Cải Tiến Đã Được Tạo Đêm Nay
Tính đến 07:35, Ratchet Tuner đã thẩm định và commit thành công 8 bước đột biến vượt trội:

| STT | Commit Hash | Kỹ Năng Tối Ưu | Điểm Cũ | Điểm Mới | Mức Tăng (Delta) | Archetype Kỹ Năng |
| :---: | :---: | :--- | :---: | :---: | :---: | :--- |
| 1 | `3c97b532` | `ccba-design` | 68.7% | **69.2%** | `+0.5%` | `coding` |
| 2 | `51d3c4ce` | `bigbim-classification` | 73.9% | **77.9%** | `+4.0%` | `bim` |
| 3 | `e798b124` | `ccba-adr-lifecycle` | 93.0% | **100.0%** | `+7.0%` | `orchestration` |
| 4 | `8784c277` | `ccba-grilling` | 93.0% | **96.0%** | `+3.0%` | `orchestration` |
| 5 | `eb49698d` | `ccba-api-circuit-breaker` | 93.0% | **100.0%** | `+7.0%` | `coding` |
| 6 | `31fc4fe9` | `ccba-llm-pipeline-patterns`| 88.5% | **96.5%** | `+8.0%` | `coding` |
| 7 | `8cba97ad` | `bigbim-risk` (Vòng 1) | 88.1% | **93.1%** | `+5.0%` | `bim` |
| 8 | `5943e248` | `bigbim-risk` (Vòng 2) | 93.1% | **95.0%** | `+1.9%` | `bim` |

---

## 3. Bảng Đối Soát Lịch Sử 3 Phiên Chạy Gần Nhất

| Chỉ Số Đánh Giá | Phiên 23/09/2026 | Phiên 24/09/2026 | Phiên 25/09/2026 (Live Audit) |
| :--- | :---: | :---: | :---: |
| **Báo cáo nguồn** | `nightly_tuner_report_20260923` | `nightly_tuner_report_20260924` | Đo lường trực tiếp qua CLI |
| **Kỹ năng quét hoàn tất**| 43 kỹ năng (dừng sớm) | 69 kỹ năng | 36/73 kỹ năng (đang chạy) |
| **Kỹ năng cải thiện** | 4 kỹ năng | 5 kỹ năng | **7 kỹ năng** (tính đến 07:35) |
| **Số Commits ghi nhận** | 5 commits | 7 commits | **8 commits** |
| **Tổng Token Tiêu Thụ** | 6,500,527 tokens | 10,001,774 (Chạm trần 10M) | ~3,350,000 tokens (Ước tính) |
| **Lỗi Heading / ADR Leak**| Có xuất hiện | Nghiêm trọng (Inverted H1-H4)| **0% (Đã triệt tiêu hoàn toàn)** |
| **Số phận Pull Request** | Không tạo (chạy test) | Tạo **PR #345** (Bị CLOSED) | **Nguy cơ hủy tạo PR lúc 15:00** |

---

## 4. Phân Tích Đối Kháng Chuyên Sâu (Double-Pass Adversarial Findings)

### 4.1. Lỗ Hổng Nguy Cấp: Nguy Cơ Tự Hủy PR Lúc 15:00 Chiều Nay
- **Căn cứ mã nguồn (`daemon.py:917-930`):**
  Trước khi thực hiện `git push` và mở Pull Request, daemon chạy lệnh:
  ```python
  verify_res = subprocess.run([sys.executable, "-m", "ccba_harness", "verify-patch", "--preset", "skill"], cwd=str(self.root), ...)
  if verify_res.returncode != 0:
      logger.error("verify-patch thất bại, hủy tạo PR.")
      return None
  ```
- **Kết quả kiểm chứng trực tiếp trong worktree (`.worktrees/nightly-runner`):**
  ```text
  [PASS] validate_skills.py --enforce-gpi (Exit: 0)
  [PASS] compile_catalog.py --check (Exit: 0)
  [FAIL] sync_hub_adr_matrix.py --check (Exit: 1)
  [FAIL] TRACEABILITY_MATRIX.md is out of sync!
  ```
- **Căn nguyên:** Commit `31fc4fe9` đã tối ưu tiêu đề trong `ccba-llm-pipeline-patterns/SKILL.md` và bỏ mất tag `(ADR-0058)`.
- **Hành động can thiệp khẩn cấp:** Trước 14:30 chiều nay, kỹ sư điều hành cần truy cập worktree và chạy lệnh:
  ```bash
  cd /home/vvc/ccba/ccba-agent-platform/.worktrees/nightly-runner
  python scripts/sync_hub_adr_matrix.py
  git commit -am "chore(adr): sync traceability matrix for nightly auto-tuner"
  ```
  Thao tác này sẽ đảm bảo cổng `verify-patch --preset skill` đạt Exit Code 0, cho phép daemon tạo PR thành công.

---

### 4.2. Bẫy Cooldown Trong Hàng Đợi (The Cooldown Trap)
- Trong [`daemon.py:400-450`](file:///home/vvc/ccba/ccba-agent-platform/packages/ccba-harness/src/ccba_harness/evals/daemon.py#L400-L450), hàng đợi ưu tiên `WeightedPriorityQueue` tính toán:
  `in_cooldown = 1 if (now - last_opt) < cooldown_hours else 0`
  Các kỹ năng dính cooldown bị phạt điểm ưu tiên và đẩy xuống cuối danh sách.
- **Điểm nghẽn cốt lõi:** Vòng lặp `for item in ranked_skills:` trong `daemon.py` **hoàn toàn không có câu lệnh `if item.in_cooldown: continue`**.
- Hậu quả: Dù bị đẩy xuống cuối, daemon vẫn kiên trì chạy qua từng kỹ năng một. Với độ trễ ~10-15 phút/kỹ năng, 73 kỹ năng tiêu tốn trọn vẹn 12-15 tiếng, làm vỡ hoàn toàn khung giờ ban đêm (00:00 - 06:00).

---

### 4.3. Điểm Mù Vòng Đời Ephemeral Worktree
- File [`scripts/cron/run_nightly_tuner.sh:151`](file:///home/vvc/ccba/ccba-agent-platform/scripts/cron/run_nightly_tuner.sh#L151) chứa hook:
  `trap cleanup_worktree EXIT` với lệnh `git worktree remove --force "$WORKTREE_DIR"`.
- Thư mục worktree tạm thời chỉ tồn tại khi cron đang chạy và **bị xóa sạch ngay khi kết thúc**.
- Nếu công cụ kiểm tra trạng thái chỉ nhắm vào worktree, toàn bộ các lượt kiểm tra ban ngày sẽ bị văng `FileNotFoundError`.
- **Giải pháp:** Đã thiết kế kiến trúc **Dual-Mode Inspection** trong công cụ mới `scripts/eval/check_nightly_status.py`.

---

### 4.4. Nút Thắt Đa Luồng & Rate Limiter Đồng Bộ
- Nhiều đề xuất trước đây nghĩ rằng chỉ cần chuyển sang `AsyncAIClient` là giải quyết được vấn đề tốc độ.
- **Thực tế kiểm tra mã nguồn:** [`AdaptiveRateLimiter`](file:///home/vvc/ccba/ccba-agent-platform/packages/ccba-harness/src/ccba_harness/evals/tuner.py#L110-L160) sử dụng hàm `self.sleeper(total_delay)` với giá trị mặc định là `time.sleep` (đồng bộ).
- Nếu chỉ gọi `await async_client.chat_with_metadata(...)` mà giữ nguyên `time.sleep` trong Rate Limiter, toàn bộ event loop của asyncio vẫn bị phong tỏa cứng. Cần truyền `asyncio.sleep` cho Rate Limiter khi tái cấu trúc.

---

### 4.5. Phân Tích 63 Hồ Sơ Leo Thang (Plateau Briefs)
- Hiện có **63 tệp plateau briefs** lưu tại `.md/knowledge/escalations/`.
- Hạn chế: Hàm `_save_plateau_brief` trong `daemon.py` chỉ xuất bảng điểm số thô sơ, chưa tuân thủ cấu trúc **Deep Problem Brief 5 trường** quy định tại ADR-0052 Section 3.B (Failure Manifest, Tested Hypotheses, Seams Involved, Error Logs, Actionable Recommendation).
- Kỹ sư khi mở file plateau không nhận được đủ ngữ cảnh nguyên nhân dính Điểm Liệt để kích hoạt `/boost`.

---

## 5. Giới Thiệu Công Cụ Giám Sát Mới: `check_nightly_status.py`

Nhằm đảm bảo khả năng quan sát (Observability) 100% an toàn và không gây gián đoạn tiến trình đang chạy, công cụ CLI `scripts/eval/check_nightly_status.py` đã được xây dựng và nghiệm thu theo chuẩn ADR-0058:

### Đặc tính kỹ thuật:
- **Cơ chế Dual-Mode Inspection:**
  - *Live Mode (Daemon đang chạy):* Quét PID an toàn bằng `fcntl.flock(..., LOCK_EX | LOCK_NB)` non-blocking, đọc mốc log phiên hiện tại, trích xuất 8 commit mới nhất từ worktree bằng cờ `git --no-optional-locks`, và kiểm tra cảnh báo đồng bộ `TRACEABILITY_MATRIX.md`.
  - *Post-Run Mode (Daemon đã kết thúc):* Tự động fallback đọc báo cáo tiến hóa `.md/knowledge/reports/nightly_tuner_report_*.md` mới nhất và đối soát Git branches trên repo chính.
- **Process Safety Invariant:** Tuyệt đối không import `ensure_single_instance` để không bao giờ vô tình kill nhầm tiến trình daemon.
- **Hỗ trợ định dạng JSON:** Cờ `--json` cung cấp dữ liệu cấu trúc phục vụ dashboard hoặc webhook cảnh báo.

### Cách sử dụng:
```bash
# Kiểm tra giao diện trực quan console
.venv/bin/python scripts/eval/check_nightly_status.py

# Xuất dữ liệu JSON máy đọc
.venv/bin/python scripts/eval/check_nightly_status.py --json
```

---

## 6. Lộ Trình Đề Xuất Cho Giai Đoạn 2 (Optimization Roadmap)

| Hạng Mục Tối Ưu | Mục Tiêu Kỹ Thuật | Tác Động Dự Kiến | Độ Phức Tạp |
| :--- | :--- | :--- | :---: |
| **1. Bộ Lọc Cooldown (`--skip-cooldown`)** | Thêm điều kiện bỏ qua kỹ năng `in_cooldown == 1` trong vòng lặp daemon. | Giảm số kỹ năng quét mỗi đêm từ 73 xuống 25-30, khớp chuẩn khung giờ 5-6h. | Thấp (KISS) |
| **2. Tự Động Đồng Bộ Matrix Trước Khi Tạo PR** | Gọi `sync_hub_adr_matrix.py` tự động bên trong `_create_pull_request` trước khi chạy `verify-patch`. | Triệt tiêu 100% nguy cơ tự hủy PR do lỗi đồng bộ tài liệu truy vết. | Thấp (KISS) |
| **3. Async Continuous Batching** | Chuyển `LLMTaskAdapter` sang `AsyncAIClient` và tích hợp `asyncio.sleep` cho Rate Limiter. | Tăng thông lượng 3x-4x, kéo giảm latency từ 19.6s xuống < 8s/call trên DGX Spark. | Trung bình |
| **4. Chuẩn Hóa Plateau Brief ADR-0052** | Nâng cấp `_save_plateau_brief` xuất đủ 5 trường của Deep Problem Brief. | Cung cấp đầy đủ log Điểm Liệt giúp kỹ sư can thiệp `/boost` chính xác. | Thấp |

---

## 7. Kết Quả Kiểm Định Nghiệm Thu (ADR-0058 Hard Completion Lock)

Mọi thành phần mã nguồn và tài liệu trong đợt kiểm toán này đã vượt qua kiểm định bất biến:

```text
# 🛡️ Deterministic Patch Verification Report: ✅ ALL PASSED
- Status: PASS (Exit Code: 0)
- Commands Executed:
  1. .venv/bin/ruff check scripts/eval/check_nightly_status.py (PASS)
  2. .venv/bin/ruff format --check scripts/eval/check_nightly_status.py (PASS)
  3. .venv/bin/mypy scripts/eval/check_nightly_status.py (PASS)
  4. python -m ccba_harness verify-patch --preset doc (PASS)
```

---
*Báo cáo được lập và lưu trữ tại Knowledge Base trung tâm `.md/knowledge/reports/` theo đúng Hiến pháp CCBA Platform.*
