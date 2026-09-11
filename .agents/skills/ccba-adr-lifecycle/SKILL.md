---
name: ccba-adr-lifecycle
description: Autonomous lifecycle governance for Architecture Decision Records (ADRs)
  - Scaffolding, status cascading, Living Traceability Matrix compilation, and CI
  parity validation.
bundle: _governance
tier: kernel
layer: _governance
user-invocable: true
command: /ccba-adr-lifecycle
gpi:
  s: 4.0
  k: 3.0
  a: 4.0
  p: 1.0
triggers:
- ccba-adr-lifecycle
- tao adr
- cap nhat adr
- adr sync
- adr lifecycle
- manage adr
- ccba-architecture-sync
- architecture-sync
conforms_to:
- HUB-ADR-0032
- HUB-ADR-0037
- HUB-ADR-0047
- HUB-ADR-0051
metadata:
  version: 1.2.0
---

# Skill: Quản Trị Vòng Đời Quyết Định Kiến Trúc (`ccba-adr-lifecycle`)

Kỹ năng này hướng dẫn Agent tự động quản trị toàn bộ vòng đời của các **Quyết định Kiến trúc (ADR)** trên nền tảng CCBA Platform (cả Hub và Spoke): Từ khởi tạo ADR mới, lan truyền trạng thái thay thế (`SUPERSEDED`), tự động biên dịch bảng mục lục `README.md`, tự động quét radar cập nhật `TRACEABILITY_MATRIX.md`, và chạy cổng kiểm định chống lệch pha tài liệu.

---

## 🏛️ Vòng Đời 4 Bước Của Một Quyết Định Kiến Trúc (The ADR Loop)

```
[1. Khởi tạo Scaffold] ──► [2. Soạn Thảo & Review] ──► [3. Biên Dịch Matrix] ──► [4. Kiểm Định CI Gate]
```

---

### Bước 1: Khởi Tạo ADR Mới (Scaffolding)
Khi người dùng hoặc Agent đề xuất một quyết định kiến trúc mới:
1. Đọc thư mục `docs/adr/` để lấy số thứ tự lớn nhất tiếp theo (ví dụ: `0034`).
2. Tạo file `docs/adr/00XX-<slug-name>.md` với cấu trúc chuẩn:

```markdown
---
id: "HUB-ADR-00XX"
title: "Tiêu Đề Quyết Định Kiến Trúc"
status: "ACCEPTED"               # ACCEPTED | SUPERSEDED | DEPRECATED
date: "YYYY-MM-DD"
pillar: "Trụ Cột Liên Quan"     # Trụ cột 1, 2 hoặc 3
supersedes: []                  # Danh sách ADR cũ bị thay thế (ví dụ: ["HUB-ADR-0010"])
---
# HUB-ADR 00XX: Tiêu Đề Quyết Định Kiến Trúc

## 1. Trạng Thái (Status)
**ACCEPTED & ADOPTED** (YYYY-MM-DD)

## 2. Bối Cảnh (Context)
Mô tả vấn đề, bất cập hiện tại và lý do cần đưa ra quyết định này.

## 3. Quyết Định Thiết Kế (Decision)
Mô tả chi tiết giải pháp kỹ thuật, cấu trúc mô-đun, và các quy tắc bất biến (Core Invariants).

## 4. Hệ Quả & Lợi Ích (Consequences)
- Lợi ích mang lại.
- Tác động đến các kỹ năng và workflow hiện có.
```

**Tiêu chí hoàn thành:** Tệp ADR mới `docs/adr/00XX-<slug-name>.md` được tạo với đúng frontmatter và cấu trúc chuẩn.

---

### Bước 2: Lan Truyền Trạng Thái Thay Thế (Status Cascading)
* Nếu ADR mới có trường `supersedes: ["HUB-ADR-00YY"]`:
  1. Mở file `docs/adr/00YY-*.md`.
  2. Cập nhật trạng thái thành:
     ```markdown
     ## 1. Trạng Thái (Status)
     **SUPERSEDED by `[HUB-ADR 00XX](<00XX-slug>.md)`** (YYYY-MM-DD)
     ```

**Tiêu chí hoàn thành:** Tất cả ADRs bị thay thế được cập nhật trạng thái `SUPERSEDED` chính xác.

---

### Bước 3: Tái Biên Dịch Mục Lục & Ma Trận Truy Xuất (Two-Tier Traceability Sync)
Chạy script đồng bộ tự động theo cơ chế **Hai Tầng (Two-Tier Architecture Matrix — HUB-ADR-0037, HUB-ADR-0051)**:
* **Tại Hub (Platform Mode):**
  ```powershell
  python scripts/sync_hub_adr_matrix.py
  ```
  - Tái tạo bảng mục lục `docs/adr/README.md`.
  - Quét radar toàn bộ `SKILL.md`, `AGENTS.md`, `CONTEXT.md`, `session_learnings.md` để biên dịch `docs/adr/TRACEABILITY_MATRIX.md`.

* **Tại Spoke (Two-Tier Preservation Mode):**
  ```powershell
  python [hub_path]/scripts/sync_hub_adr_matrix.py --spoke-dir .
  ```
  - **Tier 1 (Platform Constitution):** Giữ nguyên và liên kết 100% ADRs dùng chung từ Hub.
  - **Tier 2 (Domain-Specific Decisions):** Tự động phát hiện và bảo toàn các ADRs nghiệp vụ cục bộ của Spoke trong `## 🌐 Tier 2 — Domain-Specific Architecture Decisions`.
  - **Non-Destructive Preservation:** Bảo lưu nguyên vẹn các bảng đối soát và ghi chú tùy biến của Spoke trong `TRACEABILITY_MATRIX.md`.

**Tiêu chí hoàn thành:** `docs/adr/README.md` và `TRACEABILITY_MATRIX.md` được tái biên dịch đầy đủ mà không làm mất dữ liệu Spoke.

---

### Bước 4: Kiểm Định Khóa Cổng CI (Zero-Tolerance Parity Gate)
Thực thi kiểm định chống lệch pha (Documentation & Traceability Drift):
```powershell
python scripts/sync_hub_adr_matrix.py --check
```
* **Tiêu chuẩn nghiệm thu:**
  - 0 Duplicate numbers hoặc Numbering gaps.
  - 0 Broken ADR links trong toàn bộ codebase.
  - 100% Khớp nối giữa các file ADR, bảng mục lục `README.md` và `TRACEABILITY_MATRIX.md`.

**Tiêu chí hoàn thành:** Lệnh `python scripts/sync_hub_adr_matrix.py --check` thoát mã 0 với 0 lỗi parity.


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/architecture_sync_guide.md` | Quy trình đồng bộ tài liệu kiến trúc với ma trận ADR và bộ số liệu hệ thống |

