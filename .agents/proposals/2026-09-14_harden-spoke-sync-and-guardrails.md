---
proposal_id: "2026-09-14_harden-spoke-sync-and-guardrails"
type: "packages"
name: "harden-spoke-sync-and-guardrails"
status: "merged"
merged_commit: "176f8127"
merged_date: "2026-09-14"
priority: "Cao"
proposed_by_project: "ccba-legal-knowledge"
proposed_by_archetype: "knowledge_corpus"
proposed_date: "2026-09-14"
applies_to:
  - "Phần mềm"
  - "Tất cả Spokes"
---

# RFC Proposal: Gia Cố Spoke Sync Hygiene, Phân Phối Guardrails & Khóa Scope Safe Pytest (Issue #274)

- **Tác giả đề xuất:** Lead Maintainer & Spoke `ccba-legal-knowledge` (qua workflow `/ccba-issue-to-hub`)
- **Ngày lập:** 2026-09-14
- **Trạng thái:** Đã hợp nhất (Merged — Commit: `176f8127`)
- **Mã Issue:** [#274](https://github.com/vvChu/ccba-agent-platform/issues/274)
- **Căn cứ pháp lý & kỹ thuật:** ADR-0044, ADR-0045, ADR-0057, ADR-0058, RULE-2.5.

---

### 1. Bối cảnh & Động lực Thực tế tại Spoke (Context & Motivation)

Trong quá trình thực thi đồng bộ Spoke (`/ccba-update-spoke`) tại dự án `ccba-legal-knowledge` (Spoke Pháp điển, Archetype: `knowledge_corpus`), đã phát hiện 5 bất cập ảnh hưởng trực tiếp đến chu trình đồng bộ, tính toàn vẹn git và rào chắn thực thi an toàn:
1. **Bẩn Git do Telemetry:** `sync_spoke.py` ghi `.md/data/telemetry_summary.json` nhưng `.gitignore` chưa ignore tệp này, khiến Spoke ngay sau khi sync bị dirty.
2. **Thiếu `safe_runner.py`:** `TestGuardrailCopier` chưa bổ sung `safe_runner.py` vào danh sách phân phối, khiến Spoke thiếu runner chạy nền an toàn.
3. **Safe Pytest Fallback Unscoped:** Khi `not allow_unscoped` và không có file test nào đổi trong git status, `safe_pytest` âm thầm gọi Pytest với target rỗng, dẫn đến quét toàn bộ 400+ tests (mất hơn 100s).
4. **Pre-commit Mutating Hook:** Pre-commit hook kích hoạt validator tự ghi đè các tệp matrix và roadmap, làm bẩn working tree ngay sau commit.
5. **Windows Subprocess Charmap cp1252 Error:** Các lệnh subprocess thiếu `encoding="utf-8", errors="replace"` gây crash luồng đọc trên Windows khi gặp ký tự tiếng Việt.

---

### 2. Thiết Kế & Giải Pháp Đã Triển Khai (Implemented Solution)

1. **Khóa Scope Chặt Chẽ Cho `safe_pytest` & Xử Lý Git Rename:**
   - Trong `packages/ccba-harness/src/ccba_harness/execution.py`:
     - Bổ sung `encoding="utf-8", errors="replace"` cho `git status --porcelain`.
     - Xử lý trường hợp file bị rename: `filepath = filepath.split(" -> ")[-1].strip()`.
     - Cho phép `target_file` nhận kiểu `str | list[str] | None`.
     - Phân biệt chính xác đường dẫn file thực tế với option flags của Pytest.
     - Khi `not targets` và `not allow_unscoped`: in thông báo chỉ dẫn và `return 0` ngay lập tức.
     - Dynamic discovery `default_paths` khi `allow_unscoped=True`.
2. **Nâng Cấp `scripts/safe_pytest.py`:**
   - Đổi cờ `-f / --file` thành `nargs="+"` nhận danh sách nhiều file test.
3. **Gia Cố Spoke Git Hygiene:**
   - Bổ sung `.md/data/telemetry_summary.json` và `.md/data/*.json` vào rules của `ensure_gitignore_rule()`.
   - Cưỡng chế chạy `ensure_gitignore_rule()` độc lập ngay trong `coordinator.py:820` trước khi ghi tệp telemetry (đáp ứng cho mọi Spoke kể cả phi-Python).
4. **Phân Phối `safe_runner.py`:**
   - Bổ sung `safe_runner.py` vào `TestGuardrailCopier.copy_if_needed()`.
5. **Chuẩn Hóa Windows Subprocess UTF-8 (RULE-2.5):**
   - Bổ sung `encoding="utf-8", errors="replace"` cho toàn bộ 14 vị trí `subprocess.run(text=True)` trong `spoke_bootstrap.py`, `coordinator.py`, `backup.py`, `_guard.py`, `orchestrator.py`, `tuner.py`, và `upstream_evaluator.py`.

---

### 3. Đánh Giá Giá Trị × Rủi Ro × KISS

| Tiêu Chí | Đánh Giá Cụ Thể |
| :--- | :--- |
| **Giá trị Nghiệp vụ (Value)** | Rất cao: Giảm thời gian test từ 105s về < 0.5s; bảo vệ working tree của 100% Spoke sạch sẽ sau sync. |
| **Độ Phức tạp (Complexity)** | Thấp: Tái sử dụng các Seams sẵn có, không thêm abstraction mới (KISS). |
| **Rủi ro Rò rỉ (Risk)** | Đã triệt tiêu 100%: `.gitignore` tự động cách ly dữ liệu telemetry cục bộ. |
| **Khóa Chất Lượng (ADR-0058)** | Vượt qua 100% cổng kiểm tra tất định: `python -m ccba_harness verify-patch --preset ci`. |
