# CCBA Skill Repair — Detailed Checklists, Worktree Commands & Examples

Tài liệu tham chiếu Level 3 cho `ccba-skill-repair`, lưu trữ chi tiết danh mục lỗi thường gặp, lệnh tách `git worktree` cô lập (`RULE-4.21`), và cấu trúc chi tiết kiểm định GPI / Hygiene.

## 1. Quy Trình Worktree Cô Lập Khi Sửa Skill Từ Spoke (`RULE-4.21`)

Khi đứng tại Spoke (`CCBA_HUB_PATH` hợp lệ, khác toplevel Spoke):
- Kiểm tra 4 điều kiện an toàn trên `<hub_path>`:
  1. `git -C "<hub_path>" rev-parse --show-toplevel` khác toplevel Spoke.
  2. `git -C "<hub_path>" status --porcelain` rỗng.
  3. `git -C "<hub_path>" branch --show-current` là `main`.
  4. Chưa tồn tại nhánh hoặc PR trùng `fix/repair-<tên-skill>`.
- Nếu `<hub_path>` bận phiên song song hoặc `main` lệch `origin/main`, khởi tạo `git worktree` cô lập:

```bash
git -C "<hub_path>" fetch --prune origin
git -C "<hub_path>" worktree add -b "fix/repair-<tên-skill>" "/tmp/wt-hub-repair-<tên-skill>" origin/main
# Sau khi xong Steps 1-4 và push/mở PR:
python "<hub_path_or_wt>/scripts/governance/check_spoke_leakage.py" --root "<hub_path_or_wt>"
git -C "<hub_path>" worktree remove "/tmp/wt-hub-repair-<tên-skill>"
```

## 2. Danh Mục Lỗi Mục 1 (Triage & Linter Failure)

- Lỗi cú pháp YAML (`YAML_PARSE_ERROR`, `MALFORMED_FRONTMATTER`: thụt lề 2 spaces, cặp ngoặc kép/vuông, thẻ `---`) và thiếu `metadata.version` / `metadata.author`.
- Thiếu khối `gpi: {s, k, a, p}`, lệch `a: 1.0` khi bật `disable-model-invocation: true`, hoặc điểm rơi ngoài ngưỡng Tier 2B.
- Thiếu dòng `**Tiêu chí hoàn thành:**` (`**Completion Criterion:**`) ở các bước tuần tự.
- Liên kết gãy (`BROKEN_MARKDOWN_LINK`), sai liên kết ngược `../SKILL.md` từ `references/`, thiếu bảng Level 3 Reference Index, hoặc đường dẫn tuyệt đối chưa miễn trừ.
- Độ dài `description > 180` ký tự ở kỹ năng model-invoked (`disable-model-invocation` tắt).
- Lệch Slash Command ADR-0056 (`user-invocable: true` nhưng thiếu/sai `command: /<name>`) hoặc sai namespace.
- Lỗi `audit_skills_hygiene.py` (`RE_DEAD_WOOD`, `RE_BASHISMS`, `RE_START_PROCESS` thiếu `try/catch`, file `.md` lạc ở gốc hoặc file phi `.md` trong `references/`), hoặc Script Bloat (`scripts/*.py > 100 LOC`).

## 3. Công Thức GPI & Biến Tham Số (`evaluate-gpi`)

$$GPI = (s \times 2.5) + (k \times 2.0) + (a \times 2.0) - (p \times 1.5)$$

- **Chiều đánh giá (`1.0 - 5.0`):** `s` (Reasoning Steps), `k` (Schema/Interface Complexity), `a` (Autonomous Invocation, khóa `1.0` nếu `disable-model-invocation: true`), `p` (Parent Coupling).
- **Lệnh kiểm chứng Mode A (chưa đủ 4 khóa `gpi`) & Mode B (đã có `gpi`, hạ `a: 1.0` vào file trước khi chạy lại):**
  - Chưa khai báo sẵn `tier: kernel`: `python -m ccba_harness.cli evaluate-gpi --file <path-to-skill> [--s <S> --k <K> --a <A> --p <P>] --json`
  - Đã khai báo sẵn `tier: kernel` từ trước: gắn `--existing-tier tier-2b --json` để giữ ngưỡng hysteresis `[11.5, 12.0)` khi JSON trả về `breakdown.preserved_by_hysteresis == 1.0`.

## 4. Chi Tiết Allowlist Tự Vá Mức 1 vs Stop & Propose Mức 2

- **Mức 1 (trần 2 vòng SOP, kiểm tra `SHA-256` không đổi -> ngắt vòng, cấm đệ quy sửa/build):** Khôi phục YAML, thêm `metadata.version`/`author`, điền `command: /<name>` nếu đã bật `user-invocable: true`, rút gọn `description <= 180` (chỉ model-invoked), thêm `**Tiêu chí hoàn thành:**`, sửa link tương đối + Reference Index (giữ nguyên dòng có `# ccba:allow-machine-path` / `# ccba:allow-raw-ip`), dọn `RE_DEAD_WOOD`/`RE_START_PROCESS`/`RE_BASHISMS`.
- **Mức 2 (`Stop & Propose`):** Kích hoạt khi gặp Script Bloat (`> 100 LOC`), vi phạm Cổng 0/1, rơi về `"Tier 2A: Progressive Reference"` (`allow_standalone_skill: false`), tệp lạc thư mục, hoặc sai `name`/`bundle`. Tra cứu Seam qua `python scripts/governance/compile_catalog.py --in <input_types> --out <output_types> --json` và đề xuất kế hoạch riêng.
