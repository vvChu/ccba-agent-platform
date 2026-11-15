# 🎫 WF-06: Kiểm định Liên thông 4 Cổng ADR-0058, Đồng bộ Catalog/Docs SSOT & Đóng Bản đồ Wayfinder

> **Thuộc bản đồ:** [🗺️ Bản đồ Định hướng: Làm sâu Seam Lõi & Hợp nhất Quản trị](../map.md)  
> **Loại ticket:** `Task [AFK]`  
> **Trạng thái:** `CLOSED` (Hoàn tất kiểm định 4 cổng ADR-0058, đồng bộ SSOT & đóng bản đồ `COMPLETED`)  
> **Assignee:** `AI Platform Architect`

---

## 1. Phạm vi Nghiệm thu Toàn hệ thống

1. Chạy đầy đủ **Bảng Xác nhận 4 Cổng (`ccba-codebase-design` Bước 5 / ADR-0058)**:
   - Cổng 1: `check_init_lazy_exports_parity` & `check_package_all_exports` (`0` vi phạm).
   - Cổng 2: `0` `ImportError` / regression trên toàn bộ test suite (`packages/*/tests`, `scripts/tests`, `tests/governance`).
   - Cổng 3: Benchmark subprocess `sys.modules` trước–sau `[đo thực tế]` trên `ccba_ai.routing`, `ccba_legal.models`, `ccba_harness.gpi`, `ccba_qc_core.jurisdiction`.
   - Cổng 4: `python -m ccba_harness verify-patch --preset ci` trả về exit `0`.
2. Đồng bộ `3` writers (`RULE-1.7`): `compile_catalog.py`, `compile_skills_docs.py --write`, `sync_hub_adr_matrix.py`, cộng cập nhật `packages/*/AGENTS.md`, `CONTEXT.md` (nếu có seam mới) và `.md/knowledge/index.md` / `log.md` (`WikiHealthLinter` exit `0`).
3. Đánh giá lại `FOG-002` (xem có cần mở đợt sau cho `ccba-pdf-prep` / `mdconverter` / `ccba-ooxml` không) và chuyển trạng thái [Bản đồ Định hướng](../map.md) sang `COMPLETED`.

## 2. Tiêu chí Hoàn thành (Completion Criteria)

- [x] Tất cả `4/4` cổng nghiệm thu và `verify-patch --preset ci` đạt exit `0`.
- [x] Có bảng đối chứng số đo `[đo thực tế]` trước/sau cho cả `3` ứng viên.
- [x] Tất cả các ticket ([WF-01: Phản biện & Chốt Thiết kế Chi tiết cho 3 Ứng viên Kiến trúc (PEP 562, Frontmatter Seam, Stdlib Parameter Scanner)](wf_01_grilling_architecture_design_lock.md), [WF-02: Thẩm định Kế hoạch Ngang hàng qua Peer Plan Audit (ADR-0067 One-Way Door Gate)](wf_02_peer_plan_audit_gate.md), [WF-03: Triển khai PEP 562 Lazy Package Seams, Deferred AIClient & Cô lập PyMuPDF cho 4 Package Lõi](wf_03_pep562_lazy_package_seams.md), [WF-04: Hợp nhất 9 Bộ Phân tích Frontmatter qua parse_markdown_frontmatter & Phân rã SkillValidator dưới 800 LOC](wf_04_unify_frontmatter_and_deepen_skill_validator.md), [WF-05: Chuẩn hóa Seam Quét Tham số, IP & Machine-Path Thuần Stdlib và Thu gọn check_spoke_cleanliness dưới 800 LOC](wf_05_unify_stdlib_parameter_cleanliness_scanners.md), [WF-06: Kiểm định Liên thông 4 Cổng ADR-0058, Đồng bộ Catalog/Docs SSOT & Đóng Bản đồ Wayfinder](wf_06_ci_verification_and_catalog_rollup.md)) đóng (`CLOSED`) và [Bản đồ Định hướng](../map.md) chốt `COMPLETED`.

---

## 3. Bảng Đối Chứng Số Đo Thực Nghiệm (`[đo thực tế]`)

### 3.1. Ứng viên #1 (`PR #751..#754`) — PEP 562 Lazy Seams & Cô lập `pymupdf`

Đo trong clean subprocess với `PYMUPDF_MESSAGE=fd:2` trên `main` (`27838d62`) so với nền trước chiến dịch (`283.72–644.24 ms`, `+1,214..+2,390` modules):

| Module mục tiêu | Thời gian nạp | Số module nạp thêm | Heavy imports (`openai`/`httpx`/`fitz`/`pymupdf`) | Stderr (`fitz` deprecation) | Nguồn |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ccba_ai.routing` | `4.27 ms` | `+31` modules | `heavy=[]` | `''` | `[đo thực tế]` |
| `ccba_legal.models` | `9.70 ms` | `+46` modules | `heavy=[]` | `''` | `[đo thực tế]` |
| `ccba_qc_core.jurisdiction` | `22.06 ms` | `+104` modules | `heavy=[]` | `''` | `[đo thực tế]` |
| `ccba_harness.gpi` | `12.98 ms` | `+57` modules | `heavy=[]` | `''` | `[đo thực tế]` |

### 3.2. Ứng viên #2 (`PR #755..#756`) — Phân rã `SkillValidator` & Hợp nhất `parse_markdown_frontmatter`

- **Phân rã `skill_validator.py`**: `1,481 LOC` $\to$ facade `skill_validator.py` (`263 LOC`) + `_skill_frontmatter.py` (`423 LOC`) + `_skill_content_checks.py` (`416 LOC`) + `_skill_gpi_gates.py` (`420 LOC`) — toàn bộ `<= 450 LOC`/module & `<= 50 LOC`/hàm (`[đo thực tế]`).
- **Hợp nhất Seam Frontmatter**: `parse_markdown_frontmatter` (`re.DOTALL`) & `SkillFrontmatterSpec(raw_block, ...)` phủ đủ `13` caller production, kèm fallback stdlib 3 tầng & `sorted()` bất biến inode tại [find_skills.py](../../../../scripts/spoke/find_skills.py).

### 3.3. Ứng viên #3 (`PR #757..#758`) — Seam Quét Tham số Thuần Stdlib & Đồng bộ Spoke Tier-0

- **Core Stdlib Seam**: `_parameter_cleanliness.py` đạt `442 LOC` (`<= 450 LOC`), đồng bộ sang `scripts/_guardrails/_parameter_cleanliness.py` (`[đo thực tế]`).
- **Hiệu năng & Độ chính xác `--dir .`**: [check_hardcoded_parameters.py](../../../../scripts/governance/check_hardcoded_parameters.py) `--dir .` giảm từ `8,676.16 ms` (`2,199` báo giả `.venv/`) xuống `0.30s` (`0` vi phạm trên `569` tệp `.py` non-test, `25` AST parses) (`[đo thực tế]`).
- **Thu gọn kích thước Module**: [check_spoke_cleanliness.py](../../../../scripts/spoke/check_spoke_cleanliness.py) giảm từ `979 LOC` $\to$ `745 LOC` (`< 800 LOC`); [peer_gate.py](../../../../packages/ccba-harness/src/ccba_harness/peer_gate.py) đạt `753 LOC` (`<= 800 LOC`) (`[đo thực tế]`).

### 3.4. Đánh giá `[FOG-002]` — Các Package Phụ Trợ (`[đo thực tế]`)

| Package phụ trợ | Thời gian nạp (`PYMUPDF_MESSAGE=fd:2`) | Số module nạp thêm | Heavy imports | Kết luận phân luồng |
| :--- | :--- | :--- | :--- | :--- |
| `ccba_pdf_prep` | `53.05 ms` | `+247` modules | `heavy=[]`, `stderr=''` | Đã sạch; không cần PEP 562 |
| `ccba_ooxml` | `116.69 ms` | `+493` modules | `heavy=[]`, `stderr=''` | Xếp backlog PEP 562 đợt kế tiếp |
| `mdconverter` | `357.86 ms` | `+1,461` modules | `heavy=['openai', 'httpx']`, `stderr=''` | Xếp backlog PEP 562 đợt kế tiếp |
