---
proposal_id: "2026-09-12_modernize-skills-and-graduate-auditor"
type: "skill"
name: "modernize-skills-and-graduate-auditor"
status: "merged"
merged_pr: "#267"
merged_commit: "4a93b32f"
merged_date: "2026-09-12"
priority: "Cao"
related_issue: "#266"
proposed_by_project: "ccba-agent-platform"
proposed_by_archetype: "platform_hub"
proposed_date: "2026-09-12"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
  - "Tác vụ Admin"
---

# Đề Xuất Nâng Cấp Toàn Diện Kiến Trúc 69 Skills & Chính Thức Hóa Bộ Kiểm Toán Vệ Sinh Kỹ Năng (Issue #266)

## 1. Tóm Tắt & Vấn Đề Cốt Lõi Cần Giải Quyết

Qua quá trình rà soát và kiểm định chuyên sâu trên toàn bộ 69 kỹ năng đang vận hành trong CCBA Hub Platform (`.agents/skills/`), phát hiện nhiều bất cập tích tụ theo thời gian:
1. **Tàn dư ngoại lai (Dead Wood):** Còn sót lại các cú pháp ngoại lai như `/ck:*`, `/ultrathink`, `git-manager`, `AskUserQuestion`, thẻ XML `<tasks>`, các hàm `TaskCreate`, `TaskGet`.
2. **Cấu trúc thư mục chưa chuẩn hóa ADR-0057:** Tồn tại các tệp Markdown trơ trọi tại thư mục gốc của kỹ năng; đồng thời một số tệp mã nguồn (`.sh`, `.js`, `.yaml`, `.template`, `.cjs`) bị đặt nhầm vào `references/` thay vì `scripts/` hoặc `resources/`.
3. **Lệnh Linux/Bash không tương thích Windows PowerShell:** Chứa các lệnh `export`, `sudo apt-get`, bare `grep`, `2>/dev/null`, `xargs`, `$(...)` gây lỗi trên môi trường máy trạm Windows của kỹ sư.
4. **Thiếu vắng chỉ mục Khai mở Tăng tiến (Level 3 Reference Index):** Nhiều kỹ năng có thư mục `references/` phong phú nhưng thiếu bảng chỉ mục Level 3, hoặc thiếu router index trung gian (như `viet_chuyen_nghiep/` trong `ccba-copywriting` chứa 27 submodules không được định tuyến).
5. **Metadata Schema chưa chuẩn hóa SSOT:** Một số kỹ năng thiếu `metadata.version` hoặc khai báo sai trường `metadata.author` (dùng `publisher: CCBA` hoặc thiếu trường).
6. **Thiếu công cụ kiểm toán vệ sinh tự động:** Trước đây chỉ có kịch bản kiểm thử tĩnh trong scratch, chưa được tích hợp vào rào chắn kiểm thử cứng tất định của nền tảng (ADR-0058 Hard Completion Lock).

---

## 2. Giải Pháp Kỹ Thuật Đã Triển Khai

1. **Chuẩn hóa Toàn Diện 69 Skills (100% Xanh Thực Chất):**
   - Tẩy sạch 100% các tàn dư ClaudeKit và Dead Wood.
   - Di chuyển các tệp `.md` phụ trợ vào `references/`.
   - Di chuyển 6 tệp tài nguyên non-.md từ `references/` về đúng thư mục chức năng: `resources/` (templates, yaml) và `scripts/` (shell, js).
   - Cập nhật toàn bộ bảng **Progressive Disclosure & Reference Index (Level 3)**, xây dựng tệp router đa tầng `references/viet_chuyen_nghiep/INDEX.md` bảo vệ ngân sách ngữ cảnh.
   - Bản địa hóa toàn bộ lệnh shell sang Windows PowerShell (`$env:`, `Select-String`, `git grep`, hướng dẫn cài đặt qua `winget` / `choco`).
   - Chuẩn hóa 100% metadata frontmatter có đầy đủ `metadata.version` và `metadata.author: "CCBA Hub"`.

2. **Chính thức hóa Công cụ Quản trị `scripts/governance/audit_skills_hygiene.py`:**
   - Xây dựng CLI đầy đủ hỗ trợ `--check`, `--no-check`, `--file`, `--report`, `--json`, `--verbose`.
   - Đóng gói 5 trụ cột kiểm định vệ sinh: Frontmatter SSOT, Clean Dead Wood, Directory Hygiene, Level 3 Router Resolution, và Windows PowerShell Compatibility (kèm kiểm tra an toàn headless `Start-Process` trong khối `try/catch`).
   - Tích hợp trực tiếp hàm `check_skills_hygiene()` vào `scripts/validate_skills.py` và `ccba_harness verify-patch --preset skill`.
   - Bổ sung bộ 40 unit tests tự động trong `tests/governance/test_audit_skills_hygiene.py` bao gồm các ca kiểm thử nghịch đảo (Adversarial Injection).

3. **Tái biên dịch & Đồng bộ SSOT Catalog & Web Portal:**
   - Biên dịch lại `catalog.yaml` (69 skills).
   - Biên dịch lại Web Docs Portal tĩnh (`docs/index.html`), `docs/INDEX.md`, `llms.txt`, `llms-full.txt`.
   - Đồng bộ Living Traceability Matrix (`docs/adr/TRACEABILITY_MATRIX.md`).

---

## 3. Danh Sách Các Tệp Tin Thay Đổi Cốt Lõi

- **Công cụ & Kiểm thử Quản trị:**
  - `[NEW]` `scripts/governance/audit_skills_hygiene.py`
  - `[NEW]` `tests/governance/test_audit_skills_hygiene.py`
  - `[MODIFY]` `scripts/validate_skills.py`
- **Tài liệu & Cổng Web:**
  - `[NEW]` `docs/skills/portals.yaml`
  - `[NEW]` `docs/index.html`, `docs/INDEX.md`, `llms.txt`, `llms-full.txt`
  - `[MODIFY]` `catalog.yaml`, `docs/adr/README.md`, `docs/adr/TRACEABILITY_MATRIX.md`
- **Chuẩn hóa 69 Skills:**
  - Cập nhật 69 tệp `SKILL.md` trong `.agents/skills/`.
  - Bổ sung `INDEX.md` định tuyến cho `ccba-copywriting/references/viet_chuyen_nghiep/`.
  - Phân loại tài nguyên sang `resources/` và `scripts/` cho `ccba-ask`, `ccba-init-spoke`, `ccba-research`, `ccba-setup-skills`.

---

## 4. Bằng Chứng Nghiệm Thu Tự Động (Verification Record)

```bash
# 1. Kiểm toán vệ sinh toàn bộ 69 skills
python scripts/governance/audit_skills_hygiene.py --check
# Kết quả: [OK] Audit completed for 69 skill(s).
#          [GREEN]  Fully Compliant: 69
#          [YELLOW] Need Improvement: 0
#          [RED]    Critical Upgrades Needed: 0

# 2. Khóa cứng hoàn tất tất định
python -m ccba_harness verify-patch --preset skill
# Kết quả: Overall Status: PASS (2/2 passed)

# 3. Đồng bộ Catalog và Web Portal
python scripts/governance/compile_catalog.py --check
python scripts/governance/compile_skills_docs.py --check
# Kết quả: 100% in-sync

# 4. Kiểm thử Unit tests Quản trị
python -m pytest tests/governance/ -q
# Kết quả: 203 passed, 1 skipped
```
