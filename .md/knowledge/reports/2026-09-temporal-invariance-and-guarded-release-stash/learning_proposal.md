# 🧠 Đề Xuất Đúc Rút Tri Thức Nền Tảng (Learning Proposal v2 — Đã Thẩm Định Đối Kháng)

Sau phiên làm việc xử lý lỗi kiểm thử time-bomb ngoại lai tại `test_tuner_daemon.py:576`, đánh giá đối kháng độc lập chuyên sâu (`/boost`), và phát hành tính năng qua Pull Request [#351](https://github.com/vvChu/ccba-agent-platform/pull/351) (`/ccba-release-feature`), hệ thống đã tiến hành thẩm định đối kháng 2 vòng (Double-Pass Adversarial Review) trên bản đề xuất ban đầu và hoàn thiện bản đề xuất tinh chỉnh dưới đây:

---

## 1. Phân Loại & Phạm Vi (Classification & Scope)

| Hạng mục | Bản chất | Tệp tin mục tiêu | Phạm vi áp dụng |
| :--- | :--- | :--- | :--- |
| **Hạng mục 1: Ngân sách Tri thức & Quy chuẩn Kiểm thử** | **Rule** (Quy chuẩn kỹ thuật kiểm thử) | 1. `.md/knowledge/session_learnings.md`<br>2. `docs/rules/code_quality.md`<br>3. `packages/ccba-harness/tests/test_tuner_daemon.py` | Toàn bộ monorepo và các bài unit test có yếu tố thời gian / đa khóa sắp xếp |
| **Hạng mục 2: Kỷ luật Stash Buồng kín 4 Lớp** | **Skill Update** (Quy trình điều phối) | `.agents/skills/ccba-release-feature/SKILL.md` | Lệnh phát hành `/ccba-release-feature` |

---

## 2. Các Phát Hiện Đối Kháng Quan Trọng Đã Được Xử Lý

1. **Khắc phục Nguy cơ Tràn Ngân Sách 10 KB của `session_learnings.md`:**
   - Hiện trạng: Tệp đang ở mức `10,106 bytes` (ngưỡng trần cứng: `10,240 bytes` / `10.0 KB`).
   - Bản đề xuất v1 chiếm 939 bytes, sẽ làm dung lượng vọt lên `11,045 bytes` (10.79 KB) và làm trượt ngay lập tức bài test `test_compact_session_learnings.py`.
   - **Giải pháp v2:** Thu gọn văn phong của 6 quy tắc rườm rà (`RULE-1.8`, `RULE-1.9`, `RULE-2.8`, `RULE-3.3`, `RULE-4.6`, `RULE-5.2`) để thu hồi **355 bytes**, bảo toàn nguyên vẹn 100% 14 từ khóa `REQUIRED_INVARIANTS`. Bổ sung `RULE-2.10` tinh gọn chuẩn mực (**456 bytes**). Kết quả mô phỏng: file đạt **10,207 bytes (9.97 KB) $\le 10.0$ KB**, bảo đảm 100% PASS kiểm định tự động.

2. **Khắc phục Lỗ hổng Điều phối Stash Pop trong `ccba-release-feature`:**
   - Bản đề xuất v1 đặt pop stash tại Bước 3.1 (trước khi commit release metadata). Nếu phát sinh xung đột merge (conflict), lệnh commit tại Bước 3.5 sẽ crash với exit code 128 (`unresolved conflict`).
   - Nguy cơ "Ghost Stash Pop": Nếu Bước 0 không tạo stash nhưng trong danh sách có stash cũ, lệnh pop mù quáng sẽ nuốt nhầm dữ liệu lạ đổ lên `main`.
   - **Giải pháp v2 — Rào chắn 4 lớp (4-Layer Guarded Stash):**
     - *Lớp 1:* Gắn nhãn PR rõ ràng tại Bước 0: `"wip: concurrent work before release PR #[PR_NUMBER]"`.
     - *Lớp 2:* Chuyển việc pop stash xuống **Bước 3, Mục 6** (sau khi đã push release metadata sạch sẽ lên `main`).
     - *Lớp 3:* Kiểm tra định danh stash message chứa đúng `PR #[PR_NUMBER]` mới pop.
     - *Lớp 4 (Conflict Escape Hatch):* Nếu có conflict, kích hoạt ngay `git reset --merge` để hoàn tác `main` về trạng thái sạch 100%, bảo toàn stash trong danh sách và thông báo người dùng apply thủ công sang nhánh riêng.

3. **Thực thi Đồng bộ Chuẩn Mực vào Mã Nguồn (Standards-to-Code Enforcement):**
   - Theo Mục 12 `code_quality.md`, quy chuẩn mới về Collinear Multi-Key Sort phải được chứng minh bằng mã nguồn thực tế.
   - Bổ sung `os.utime` vào `test_tuner_daemon.py:600-613` để chủ động gán `rep_newer` có `mtime` lùi lại 3600s so với `rep_older`, bẻ gãy hoàn toàn bẫy kiểm thử cùng chiều.

---

## 3. Nội Dung Chi Tiết Bản Vá Đề Xuất (Refined Production Diffs)

### 3.1. Diff cho `.md/knowledge/session_learnings.md`
*(Thu gọn các đoạn văn xuôi để tạo khoảng trống 355 bytes và bổ sung `RULE-2.10`, giữ file ở mức 10,207 bytes / 9.97 KB)*

```markdown
- **RULE-1.8 [ADR 0044 & Issue #326 — Multi-Device Spoke & Universal Invariant Merge]**:
  - *Universal Invariant Regex*: Regex multiline bảo tồn 100% điều khoản cục bộ khi sync.
  - *Cross-Drive Fallback*: Khi `relpath` lỗi `ValueError`, fallback `hub_path` về `None`, tránh gắn cứng ổ đĩa.
- **RULE-1.9 [2-Phase Planning Guardrail — The Factory Model]**:
  - Refactoring bộ trích xuất/chuyển đổi BẮT BUỘC phân lập 2 giai đoạn: Phase 1 (Pure Structural — Zero-Regression 0.0%, dual-dispatch) và Phase 2 (Feature/Schema Mutations). Cấm scope conflation.

...

- **RULE-2.8 [Cross-Platform Sandbox Root Traversal Invariant]**:
  - CẤM độ sâu cố định `parents[N]` (tránh `PermissionError` trên Linux `/tmp`). BẮT BUỘC duyệt ngược tìm `(p / ".md").is_dir()`, fallback local `.cache/`, bọc `try...except (PermissionError, OSError)`.
- **RULE-2.9 [Test Fixture Isolation & Hub Discovery Decoupling]**:
  - Test fixtures và runners (`run_isolated_tests.py`, root `conftest.py`) BẮT BUỘC cô lập môi trường: xóa `CCBA_HUB_PATH` và `HUB_PATH`. CẤM rò rỉ biến môi trường máy trạm vào test subprocess.
- **RULE-2.10 [Temporal Invariance & Collinear Multi-Key Sort Guard]**:
  - *Temporal Invariance*: Test cooldown/TTL/sliding window CẤM ngày tĩnh cứng (`"YYYY-MM-DD"`); BẮT BUỘC ngày tương đối (`today - timedelta(...)`).
  - *Collinear Sort Guard*: Test sắp xếp đa khóa (ví dụ: `date` vs `mtime`) BẮT BUỘC fixture nghịch chiều (`os.utime`) cô lập tiêu chí ưu tiên, chống bẫy pass ngẫu nhiên do cùng chiều.

...

- **RULE-3.3 [Làm Sạch Bảng Biểu, Footnotes & ADR 0044 Multi-Part Disambiguation]**:
  - Footnote: Khử lặp số `re.sub(r"^[0-9]+[)\.]\s*", "", fn_clean).strip()`; khử lặp ô gộp OpenXML (`gridSpan`).
  - Subheader: `not is_numeric` trước khi gộp subheader tránh nuốt dữ liệu cùng giá trị.
  - Multi-Part: Đa phần mang tiền tố `bang_pXX_YY.csv` và `part_id: "pXX"` trong `tables_catalog.json`.

...

- **RULE-4.6 [PR Shift-Left CI & Zero-Red-Merge]**:
  - Chạm $\ge 2$ pkgs: BẮT BUỘC `verify-patch --preset ci`. CẤM `--admin`/`--auto`; dùng `gh pr checks --watch`, chờ Copilot review và 100% Green trước khi merge.

...

- **RULE-5.2 [Windows Path Quotes & Hook Protection]**:
  - Khi IDE bọc ngoặc kép `"C:\..."` vào `hooks.json`, vô hiệu bằng `{}` và khóa `IsReadOnly = $true`. Timeout $\ge 60\text{s}$ cho tests scan metadata trên Windows.
```

---

### 3.2. Diff cho `docs/rules/code_quality.md`
*(Thêm Mục 13 vào cuối tài liệu)*

```markdown
---

## 13. Temporal Invariance & Collinear Multi-Key Sort Testing (Kiểm Thử Bất Biến Thời Gian & Chống Bẫy Cùng Chiều)
Khi xây dựng các bài unit test có yếu tố thời gian hoặc kiểm thử độ ưu tiên giữa nhiều tiêu chí sắp xếp:
1. **Bất biến thời gian tương đối (Temporal Invariance):**
   - Tuyệt đối KHÔNG hardcode chuỗi ngày tĩnh (`"YYYY-MM-DD"`) trong các test case kiểm tra cơ chế cooldown, TTL, sliding window, hoặc phân loại theo thời gian thực thi gần nhất.
   - Luôn sử dụng hàm sinh ngày động tương đối dựa trên `datetime.date.today()` hoặc `datetime.datetime.now(datetime.timezone.utc)` (ví dụ: `older_date = today - timedelta(days=2)`, `newer_date = today - timedelta(days=1)`).
   - Đảm bảo tính bất biến toán học: Khoảng cách giữa các ngày kiểm thử và `cutoff_date` luôn giữ nguyên giá trị logic bất kể bài test được thực thi vào ngày nào trong tương lai.
2. **Chống bẫy kiểm thử cùng chiều (Collinear Multi-Key Sort Trap):**
   - Khi một hàm sắp xếp sử dụng khóa phức hợp (ví dụ: `(date, mtime)`), nếu fixture ghi tệp mới hơn sau tệp cũ hơn, thứ tự filesystem `st_mtime` và thứ tự ngày parsed sẽ cùng chiều ($mtime_{new} > mtime_{old}$ đồng thời $date_{new} > date_{old}$). Điều này tạo ra một "bài test pass ảo": ngay cả khi logic sắp xếp theo `date` hỏng hoàn toàn, test vẫn pass nhờ `st_mtime`.
   - **Quy chuẩn bắt buộc:** Khi kiểm thử thứ tự ưu tiên của khóa chính (`date`), fixture phải cố tình tạo ra xung đột với khóa phụ: thiết lập `os.utime` sao cho tệp có ngày mới hơn lại mang `mtime` cũ hơn (ví dụ lùi lại 3600s). Chỉ khi đó bài test mới thực sự chứng minh được khóa chính có độ ưu tiên cao hơn khóa phụ.
```

---

### 3.3. Diff cho `.agents/skills/ccba-release-feature/SKILL.md`
*(Bump version lên `1.2.2`, bổ sung rào chắn stash Bước 0 và Bước 3 Mục 6)*

```markdown
metadata:
  version: "1.2.2"
```

**Tại Bước 0, Cổng 0.1:**
```markdown
   - Nếu phát hiện tệp chưa commit thuộc tác vụ song song khác:
     1. Thực hiện stash có định danh rõ ràng kèm cả tệp untracked:
        ```bash
        git stash push -u -m "wip: concurrent work before release PR #[PR_NUMBER]"
        ```
     2. Xác nhận lại nhánh hiện tại trước khi kích hoạt Cổng 0.2:
        ```bash
        git branch --show-current
        ```
```

**Tại Bước 3, bổ sung Mục 6:**
```markdown
6. **Khôi phục Tác Vụ Song Song Đã Stash (Guarded Post-Release Stash Recovery):**
   - Kiểm tra xem Bước 0 có tạo stash cho PR hiện tại hay không:
     ```bash
     git stash list | grep "wip: concurrent work before release PR #[PR_NUMBER]"
     ```
   - Nếu tìm thấy mục stash tương ứng, khôi phục có rào chắn bảo vệ:
     ```bash
     git stash pop
     ```
   - *Rào chắn chống xung đột (Conflict Escape Hatch):* Nếu `git stash pop` gặp xung đột merge (conflict), Agent **tuyệt đối không để working tree ở trạng thái unmerged trên main**. BẮT BUỘC chạy ngay:
     ```bash
     git reset --merge
     ```
     Lệnh này sẽ khôi phục nhánh `main` về trạng thái sạch sẽ 100%, trong khi bản stash vẫn được giữ an toàn trong stash list. Sau đó, thông báo rõ ràng cho người dùng: *"Phát hiện xung đột khi pop stash lên main. Đã khôi phục trạng thái sạch của main bằng git reset --merge. Bản stash vẫn được bảo toàn; vui lòng tạo nhánh mới và áp dụng bằng `git checkout -b <branch> && git stash apply`"*.
```

---

### 3.4. Cập nhật Thực thi Test Gương Mẫu cho `packages/ccba-harness/tests/test_tuner_daemon.py`
Tại dòng 600-613:
```python
    # Đảo ngược mtime: Đặt rep_newer có mtime cũ hơn rep_older 3600 giây
    # để triệt tiêu hoàn toàn Collinear Test Trap theo Mục 13 Code Quality
    base_time = time.time()
    os.utime(rep_older, (base_time, base_time))
    os.utime(rep_newer, (base_time - 3600.0, base_time - 3600.0))
```

---

## 4. Kế Hoạch Kiểm Định Tất Định 5 Bước (ADR-0058 Hard Completion Lock)

Sau khi được phê duyệt, Agent sẽ thực thi chuỗi kiểm định tự động:
1. `python scripts/governance/compact_session_learnings.py --check` (Bảo đảm dung lượng $\le 10.0$ KB và đủ 14 invariants).
2. `pytest tests/governance/test_compact_session_learnings.py` (Xác nhận pass test governance).
3. `python scripts/validate_skills.py --file .agents/skills/ccba-release-feature/SKILL.md --enforce-gpi` (Xác nhận skill chuẩn ADR-0057).
4. `python scripts/governance/compile_catalog.py --check` & `python scripts/sync_hub_adr_matrix.py --check`.
5. `pytest packages/ccba-harness/tests/test_tuner_daemon.py -k "test_load_historical_metrics"` (Xác nhận fixture `os.utime` chạy sạch sẽ).
