---
name: ccba-adr-lifecycle
description: Autonomous lifecycle governance for Architecture Decision Records (ADRs) - Scaffolding, status cascading, Living Traceability Matrix compilation, and CI parity validation.
bundle: _governance
layer: _governance
triggers:
- ccba-adr-lifecycle
- tao adr
- cap nhat adr
- adr sync
- adr lifecycle
- manage adr
conforms_to:
- "ADR-0032"
- "ADR-0047"
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
id: "ADR-00XX"
title: "Tiêu Đề Quyết Định Kiến Trúc"
status: "ACCEPTED"               # ACCEPTED | SUPERSEDED | DEPRECATED
date: "YYYY-MM-DD"
pillar: "Trụ Cột Liên Quan"     # Trụ cột 1, 2 hoặc 3
supersedes: []                  # Danh sách ADR cũ bị thay thế (ví dụ: ["ADR-0010"])
---
# ADR 00XX: Tiêu Đề Quyết Định Kiến Trúc

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

---

### Bước 2: Lan Truyền Trạng Thái Thay Thế (Status Cascading)
* Nếu ADR mới có trường `supersedes: ["ADR-00YY"]`:
  1. Mở file `docs/adr/00YY-*.md`.
  2. Cập nhật trạng thái thành:
     ```markdown
     ## 1. Trạng Thái (Status)
     **SUPERSEDED by [ADR 00XX](00XX-....md)** (YYYY-MM-DD)
     ```

---

### Bước 3: Tái Biên Dịch Mục Lục & Ma Trận Truy Xuất (Traceability Sync)
Chạy script đồng bộ tự động:
* **Tại Spoke:**
  ```powershell
  python scripts/sync_adr_matrix.py
  ```
* **Tại Hub:**
  ```powershell
  python scripts/sync_hub_adr_matrix.py
  ```
* **Kết quả tự động cập nhật:**
  - Tái tạo bảng mục lục `docs/adr/README.md`.
  - Quét toàn bộ `SKILL.md`, `AGENTS.md`, `CONTEXT.md`, `session_learnings.md` để tái sinh `docs/adr/TRACEABILITY_MATRIX.md`.

---

### Bước 4: Kiểm Định Khóa Cổng CI (Zero-Tolerance Parity Gate)
Thực thi kiểm định:
```powershell
python scripts/validate_adr_parity.py
```
* **Tiêu chuẩn nghiệm thu:**
  - 0 Duplicate numbers hoặc Numbering gaps.
  - 0 Broken ADR links trong toàn bộ codebase.
  - 100% Khớp nối giữa các file ADR và bảng mục lục.
