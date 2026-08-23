# ADR 0047: Catalog Manifest Compiler & Frontmatter Single Source of Truth (SSOT)

* **Status:** Accepted
* **Date:** 2026-08-23
* **Deciders:** CCBA Platform Core Team
* **Consulted:** ADR 0040 (Skills Hierarchy), ADR 0041 (Taxonomy & Archetypes), ADR 0044 (Shared SDKs)

---

## Context & Problem Statement

Tệp danh mục trung tâm `catalog.yaml` (`.agents/skills/platform-loader/catalog.yaml`) đóng vai trò là Service Catalog và Discovery Index cho toàn bộ hệ thống Hub-Spoke. Tuy nhiên, khi hệ sinh thái tăng trưởng (vượt 73 skills và 64 workflows, 1.626 dòng YAML), phương thức bảo trì thủ công (manual duplication) bộc lộ các vấn đề:
1. **Trùng lặp nguồn chân lý (Dual SSOT):** Kỹ sư phải khai báo metadata (name, description, bundle, triggers) ở cả file `SKILL.md` / `workflow.md` và file `catalog.yaml`.
2. **Nguy cơ lệch pha (Drift & Desync):** Khi cập nhật triggers hoặc mô tả trong `SKILL.md` mà quên sửa `catalog.yaml`, hệ thống phân phối kỹ năng về Spoke sẽ sử dụng dữ liệu cũ.
3. **Gánh nặng bảo trì:** Thao tác thêm/sửa/xóa skill thủ công trong file 1.626 dòng làm tăng khả năng lỗi cú pháp và merge conflicts.

---

## Decision Drivers

1. **KISS & Zero Latency:** Tốc độ đọc `catalog.yaml` khi runtime phải giữ nguyên ở mức cực nhanh (~2ms), không được chuyển sang dynamic directory scanning gây chậm trên Windows.
2. **Single Source of Truth (SSOT):** YAML Frontmatter trong từng file `.md` (`SKILL.md`, `.agents/workflows/*.md`) là nơi duy nhất khai báo thông tin kỹ năng.
3. **Deterministic & Automated:** Tự động hóa quá trình biên dịch `catalog.yaml` với thời gian thực thi < 30ms.
4. **Enforced via CI Gates:** Tích hợp cơ chế `--check` vào CI testing để ngăn chặn commit bị lệch pha.

---

## Considered Options

* **Option 1: Status Quo (Thủ công):** Tiếp tục nhập tay cả 2 nơi. (Bị loại do rủi ro desync cao).
* **Option 2: Pure Dynamic Discovery (Bỏ catalog.yaml):** Quét đĩa `glob('**/*.md')` mỗi khi runtime. (Bị loại vì làm chậm tiến trình sync 10-20x trên Windows).
* **Option 3: Catalog Compiler / Manifest Generator (Accepted):** Giữ `catalog.yaml` làm compiled manifest, tự động sinh từ frontmatter và `catalog_base.yaml`.

---

## Decision Outcome

Quyết định triển khai **Option 3**:

1. **Tách cấu hình tĩnh cấp cao:**
   * Lưu các trường tĩnh độc lập (`hub_path`, `hub_repo`, `notebook_ids`, `bundles`, `rules`, `knowledge`) tại `.agents/skills/platform-loader/catalog_base.yaml`.
2. **Frontmatter SSOT:**
   * Mọi `SKILL.md` và `.agents/workflows/*.md` lưu trữ `name`, `description`, `bundle`, `triggers`/`keywords`, `package_path` trực tiếp trong YAML frontmatter.
3. **Compiler Engine (`scripts/governance/compile_catalog.py`):**
   * Quét toàn bộ frontmatters và kết hợp với `catalog_base.yaml` để biên dịch ra `catalog.yaml`.
   * Cung cấp CLI flags:
     * `--write` (mặc định): Biên dịch và ghi đè `catalog.yaml`.
     * `--check`: Chế độ CI gate (exit code 0 nếu khớp 100%, 1 nếu phát hiện sai lệch).
4. **CI Gate Integration:**
   * Bổ sung bài test `test_catalog_yaml_is_compiled_and_in_sync()` vào `tests/governance/test_taxonomy_integrity.py`.

---

## Consequences

### Positive
* **Loại bỏ 100% việc sửa thủ công `catalog.yaml`:** Lập trình viên chỉ cần tạo/sửa file `SKILL.md` hoặc `workflow.md`.
* **Zero Runtime Overhead:** Runtime performance không đổi vì vẫn đọc từ compiled YAML manifest.
* **Tự động bảo vệ bởi CI:** Không thể merge code nếu `catalog.yaml` bị lệch với frontmatters.

### Negative / Trade-offs
* Cần chạy `python scripts/governance/compile_catalog.py` sau khi thêm/sửa skill hoặc workflow (được tự động hóa qua pre-commit / CI gate).
