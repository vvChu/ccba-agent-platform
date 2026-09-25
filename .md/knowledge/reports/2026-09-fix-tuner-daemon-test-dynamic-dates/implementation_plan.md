# Kế hoạch Triển khai (Implementation Plan)

## Xử lý Triệt để Lỗi Kiểm thử Time-Bomb tại `test_tuner_daemon.py:595`

---

## 1. Bối cảnh & Nguyên nhân Gốc rễ (Root Cause Analysis)

### Hiện tượng
Trong quá trình audit sau PR #350 vào ngày `2026-09-25`, test suite `test_tuner_daemon.py` phát sinh lỗi kiểm thử đơn vị:
```text
FAILED packages/ccba-harness/tests/test_tuner_daemon.py::test_load_historical_metrics_unbolded_scores_and_date_sort - AssertionError: assert 'skill_mixed' in set()
```

### Phân tích Cơ chế Time-Bomb
- Trong `packages/ccba-harness/src/ccba_harness/evals/daemon.py:313-330`:
  ```python
  today = datetime.date.today()
  cutoff_date = today - datetime.timedelta(days=cooldown_days)
  ...
  is_within_cooldown = r_date is not None and r_date >= cutoff_date
  ```
- Trong bài test `test_load_historical_metrics_unbolded_scores_and_date_sort` (`test_tuner_daemon.py:581-613`):
  - File report cũ: `nightly_tuner_report_20260920_010000.md` (ngày tĩnh `2026-09-20`).
  - File report mới: `nightly_tuner_report_2026-09-21_010000.md` (ngày tĩnh `2026-09-21`).
  - Lệnh gọi kiểm tra: `daemon._load_historical_metrics(cooldown_days=3)`.
  - Assertion kiểm tra: `assert "skill_mixed" in cooldown_skills`.
- **Tại thời điểm PR #317 (2026-09-21) đến 2026-09-24**:
  - `today` = 2026-09-24 $\rightarrow$ `cutoff_date` = `2026-09-24 - 3 ngày` = `2026-09-21`.
  - `r_date` (`2026-09-21`) $\ge$ `cutoff_date` (`2026-09-21`) $\rightarrow$ `True`.
  - `skill_mixed` được nạp vào `cooldown_skills` $\rightarrow$ Test **PASS**.
- **Khi bước sang ngày 2026-09-25**:
  - `today` = 2026-09-25 $\rightarrow$ `cutoff_date` = `2026-09-25 - 3 ngày` = `2026-09-22`.
  - `r_date` (`2026-09-21`) $\ge$ `cutoff_date` (`2026-09-22`) $\rightarrow$ **False**!
  - `cooldown_skills` trả về rỗng (`set()`).
  - Assertion dòng 612 `assert "skill_mixed" in cooldown_skills` phát nổ (**FAIL**).

---

## 2. CCBA Charter Governance & QC Matrix (ADR-0058)

Tuân thủ nghiêm ngặt **ADR-0058** (Live Collaboration Artifacts & Deterministic Exit-Code Binding):
- **Môi trường:** Hub Monorepo (`ccba-agent-platform`)
- **QC Level áp dụng:** Level 2 (Technical & Architecture Parity)
- **Ghế chịu trách nhiệm phê duyệt:** `TRUONG_PHONG_RD_HTQT` (hoặc Lead Architect)
- **Tiêu chuẩn nghiệm thu:** 
  1. 100% các lệnh trong `Verification Plan` trả về Exit Code 0.
  2. Báo cáo bàn giao `walkthrough.md` nhúng nguyên văn bảng kết quả thực thi từ `verify-patch`.
  3. Snapshot lưu trữ vĩnh viễn vào `.md/knowledge/reports/` trước khi đóng phiên.

---

## 3. Double-Pass Adversarial Review (Đã Phản Biện Chuyên Sâu)

### Vòng 1 — Code-First Research
- **Đọc mã nguồn thực tế**:
  - File `packages/ccba-harness/src/ccba_harness/evals/daemon.py` xử lý hoàn toàn chuẩn mực theo quy tắc ADR-0052. Logic production không có lỗi.
  - Ngay trong cùng tệp `test_tuner_daemon.py:471-475` (`test_load_historical_metrics_cooldown_and_real_llm_filter`), tác giả đã triển khai mẫu ngày động tương đối:
    ```python
    today = datetime.date.today()
    today_str = today.strftime("%Y%m%d")
    yesterday_str = (today - datetime.timedelta(days=1)).strftime("%Y%m%d")
    five_days_ago_str = (today - datetime.timedelta(days=5)).strftime("%Y%m%d")
    ```
    Bài test trên chạy hoàn toàn ổn định qua mọi ngày.
  - Tác giả khi bổ sung `test_load_historical_metrics_unbolded_scores_and_date_sort` tại commit `693ae9eb` đã sao chép ví dụ markdown từ báo cáo thực tế (ngày 20 và 21/09/2026) mà quên sử dụng ngày tương đối.

### Vòng 2 — Self-Adversarial Review (Kiểm Chứng 1.827 Ngày & Phòng Thủ Mtime)
1. **Kiểm chứng 1.827 ngày liên tục (2024–2028 qua các năm nhuận và chuyển tháng)**:
   - Đã chạy mô phỏng qua 5 năm liên tiếp: Regex bóc tách tên file (`r"nightly_tuner_report_(\d{4})[-_]?(\d{2})[-_]?(\d{2})"`) và regex nội dung đạt tỷ lệ khớp 1.827/1.827 ngày (100%).
   - `newer_date` ($T-1$) luôn $\ge$ `cutoff_date` ($T-3$) tại mọi thời điểm trong tương lai.
2. **Cơ chế Phòng thủ Mặt nạ Mtime (Mtime Fallback Defense)**:
   - Nếu parser ngày bị hỏng, `daemon.py` có fallback về `f.stat().st_mtime`. Do `rep_newer` được ghi sau, fallback mtime vẫn có thể vô tình xếp `rep_newer` lên đầu.
   - **Tuy nhiên**, dòng 613 kiểm tra `assert last_scanned_dates.get("skill_mixed") == newer_date`. Nếu fallback mtime bị kích hoạt, giá trị nhận được sẽ là ngày tạo tệp (`today`), khác với `newer_date` (`today - 1`). Do đó assertion này **chắc chắn sẽ fail**, bảo đảm không bao giờ để lọt lỗi parser ngày.
3. **Rà soát toàn bộ Monorepo về Static Date Time-Bombs**:
   - Đã quét toàn bộ test suite: không còn bài test nào khác trong monorepo so sánh `cutoff_date` với ngày tĩnh.

---

## 4. Kế hoạch Triển khai Chi tiết

### Mục tiêu Code Diff (`packages/ccba-harness/tests/test_tuner_daemon.py:576-614`)

```python
def test_load_historical_metrics_unbolded_scores_and_date_sort(tmp_path: Path) -> None:
    """Verify _load_historical_metrics handles plain unbolded scores and sorts by actual date."""
    reports_dir = tmp_path / ".md" / "knowledge" / "reports"
    reports_dir.mkdir(parents=True)

    today = datetime.date.today()
    older_date = today - datetime.timedelta(days=2)
    newer_date = today - datetime.timedelta(days=1)
    older_str = older_date.strftime("%Y%m%d")
    newer_str = newer_date.strftime("%Y-%m-%d")

    # Older report with no hyphens
    rep_older = reports_dir / f"nightly_tuner_report_{older_str}_010000.md"
    rep_older.write_text(
        f"""# 🌙 CCBA Nightly Auto-Tuner Evolution Report
> **Thời gian thực thi:** `{older_str}_010000` | **Engine:** `REAL_LLM`
### 📊 Bảng Đối Soát Tiến Hóa Kỹ Năng (Evolution Matrix)
| Kỹ Năng (Skill Name) | Điểm Ban Đầu | Điểm Sau Tối Ưu | Chênh Lệch (Delta) | Commits | Tokens | Trạng Thái |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `skill_mixed` | 60.0% | **60.0%** | `0.0%` | 0 | `100,000` | ⚪ UNCHANGED |
""",
        encoding="utf-8",
    )

    # Newer report with hyphens in date AND unbolded final score AND backticks on commits
    rep_newer = reports_dir / f"nightly_tuner_report_{newer_str}_010000.md"
    rep_newer.write_text(
        f"""# 🌙 CCBA Nightly Auto-Tuner Evolution Report
> **Thời gian thực thi:** `{newer_str}_010000` | **Engine:** `REAL_LLM`
### 📊 Bảng Đối Soát Tiến Hóa Kỹ Năng (Evolution Matrix)
| Kỹ Năng (Skill Name) | Điểm Ban Đầu | Điểm Sau Tối Ưu | Chênh Lệch (Delta) | Commits | Tokens | Trạng Thái |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `skill_mixed` | 85.0% | 85.0% | `0.0%` | `0` | `-` | ⚪ UNCHANGED |
""",
        encoding="utf-8",
    )

    daemon = NightlyTunerDaemon(root=tmp_path)
    scores, cooldown_skills, last_scanned_dates = daemon._load_historical_metrics(cooldown_days=3)

    # The newer report (85.0%) should win over the older report (60.0%)
    assert scores.get("skill_mixed") == 85.0
    assert "skill_mixed" in cooldown_skills
    assert last_scanned_dates.get("skill_mixed") == newer_date
```

---

## 5. Kế hoạch Kiểm định (Verification Plan — ADR-0058 Hard Completion Lock)

Tuân thủ **ADR-0058** (Deterministic Hard Completion Lock), các bước kiểm định tự động bắt buộc:
1. **Kiểm thử đơn vị tập trung**:
   ```bash
   .venv/bin/pytest packages/ccba-harness/tests/test_tuner_daemon.py -k "test_load_historical_metrics_unbolded_scores_and_date_sort" -vv
   ```
2. **Kiểm thử toàn bộ suite `test_tuner_daemon.py`**:
   ```bash
   .venv/bin/pytest packages/ccba-harness/tests/test_tuner_daemon.py -v
   ```
   (Kỳ vọng: 26/26 tests passed)
3. **Kiểm tra linter & formatting qua Python venv**:
   ```bash
   .venv/bin/python -m ruff check packages/ccba-harness/tests/test_tuner_daemon.py
   .venv/bin/python -m ruff format --check packages/ccba-harness/tests/test_tuner_daemon.py
   ```
4. **Khóa cứng nghiệm thu toàn monorepo kết hợp Scoped Test (ADR-0058)**:
   ```bash
   .venv/bin/python -m ccba_harness verify-patch --preset ci -c ".venv/bin/pytest packages/ccba-harness/tests/test_tuner_daemon.py -vv"
   ```
   (Kỳ vọng: 7/7 checks passed, Exit Code 0).

---

## 6. Đánh giá Rủi ro & Nguyên tắc KISS

- **Độ phức tạp**: Cực kỳ thấp (thay đổi ~15 dòng code kiểm thử trong 1 file duy nhất).
- **Rủi ro ảnh hưởng hệ thống**: 0% (không can thiệp logic của `ccba_harness/evals/daemon.py`).
- **Khả năng rollback**: Dễ dàng `git checkout` hoặc `git restore` nếu phát sinh bất thường.
