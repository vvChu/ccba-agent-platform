---
proposal_id: "2026-08-19_legislative-consolidator-okf-v2"
type: "tool"
name: "legislative-consolidator-okf-v2"
status: "merged"
merged_commit: "b52e705"
merged_date: "2026-08-21"
priority: "Cao"
proposed_by_project: "ccba-legal-knowledge"
proposed_date: "2026-08-19"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Tác vụ Admin"
---

# Đề Xuất & Triển Khai: Legislative Consolidator Deep Seam (OKF v2.0)

## 1. Tóm Tắt & Mục Tiêu (Executive Summary)
Đóng gói và tích hợp chính thức **Động cơ Hợp nhất Văn bản Pháp luật Chuẩn OKF v2.0 (Legislative Consolidator Deep Seam)** vào package `packages/ccba-legal-intel` trên Hub (`ccba_legal.consolidator`), cho phép tự động hóa $100\%$ việc vá cấu trúc AST và kết xuất đồng thời 3 thành phẩm chuẩn OKF v2.0 cho hàng trăm Luật, Nghị định, Thông tư, QCVN và TCVN.

---

## 2. Kiến Trúc Hybrid Đã Kiểm Chứng (ADR 0017)

Thay vì dùng Regex/NLP thuần túy giòn và dễ lỗi hoặc Prompt LLM tự do gây ảo giác (hallucination), hệ thống hoạt động theo mô hình **Hybrid 4 Bước**:

```
[Văn bản Sửa đổi] 
       │
       ▼ (1. LLM-Assisted Extraction qua AI Gateway)
[patch_manifest.yaml] 
       │
       ▼ (2. Con người duyệt / Human-in-the-loop 30 giây)
[Deterministic Patcher Engine]
       │
       ▼ (3. Vá cấu trúc AST Dual-Mode: QCVN + Luật)
[3 Thành Phẩm OKF v2.0]
  ├── 1. *_hop_nhat_*.md (kèm Callouts > [!NOTE], > [!WARNING])
  ├── 2. clauses.json (AST giàu siêu dữ liệu: jurisdiction, pdf page, cong bao number)
  └── 3. bang_so_sanh_thay_doi.md (Ma trận đối chiếu rủi ro kiểm toán)
```

---

## 3. Các Action Token Đã Triển Khai Trong Mã Nguồn

- `REPLACE`: Sửa đổi toàn bộ nội dung điều khoản/bảng biểu.
- `INSERT_AFTER` / `INSERT_BEFORE`: Bổ sung điều khoản mới vào vị trí xác định.
- `INSERT_RANGE_AFTER`: Bổ sung dải nhiều điều khoản con (ví dụ: thuật ngữ 1.4.31 đến 1.4.34).
- `APPEND`: Bổ sung nội dung vào cuối điều khoản/chương hiện có.
- `REPEAL`: Bãi bỏ điều khoản (gạch ngang kèm Callout cảnh báo).
- `SUBSTITUTE_PHRASE`: Thay thế cụm từ kỹ thuật chính xác.

---

## 4. Các Thành Phần Mã Nguồn Được Đóng Gói Vào Hub

- `packages/ccba-legal-intel/src/ccba_legal/consolidator/`:
  - `patch_manifest_schema.py`: Schema YAML và Dataclasses.
  - `dual_mode_parser.py`: Bộ phân tích cú pháp đa chế độ (QCVN số chấm `1.1.3` + Luật `Điều X`).
  - `patcher.py`: Động cơ vá AST và xuất 3 thành phẩm.
  - `manifest_generator.py`: Module AI Gateway hỗ trợ trích xuất manifest.
  - `__main__.py`: CLI interface.
- `packages/ccba-legal-intel/src/ccba_legal/__init__.py`: Export public deep seams.
- `packages/ccba-legal-intel/tests/test_consolidator.py`: Bộ kiểm thử tự động toàn diện.

---

## 5. Kết Quả Kiểm Thử (Verification & Test Results)

- Toàn bộ test suite `pytest packages/ccba-legal-intel/tests/test_consolidator.py` đạt **`100% PASSED`**.
- Đã kiểm chứng thực nghiệm thành công trên dữ liệu thực tế:
  - **QCVN 04:2021/BXD + Sửa đổi 01:2026 (TT 31/2026/TT-BXD)**
  - **QCVN 06:2022/BXD + Sửa đổi 1:2023 (TT 09/2023/TT-BXD)**
