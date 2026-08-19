---
proposal_id: "2026-08-19_legislative-consolidator-okf-v2"
type: "tool"
name: "legislative-consolidator-okf-v2"
status: "open"
priority: "Cao"
proposed_by_project: "ccba-legal-knowledge"
proposed_date: "2026-08-19"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Tác vụ Admin"
---

# Đề Xuất: Nâng Cấp Động Cơ Hợp Nhất Văn Bản Pháp Luật Chuẩn OKF v2.0 (Legislative Consolidator Deep Seam)

## 1. Mô Tả (Description)
Nâng cấp và khái quát hóa module `VBHNMerger` và `ASTParser` trong package `ccba-legal-intel` trên Hub (`packages/ccba-legal-intel/src/ccba_legal/`) thành **Động cơ Hợp nhất Văn bản Pháp luật Chuẩn OKF v2.0 Đa Năng (Legislative Consolidator Engine)**, cho phép tự động hóa $100\%$ việc bóc tách bản vá sửa đổi và hợp nhất toàn văn cho cả Quy chuẩn (QCVN), Tiêu chuẩn (TCVN), Luật và Nghị định.

---

## 2. Vấn Đề Giải Quyết (Problem Statement)
- **Hiện trạng trên Hub:** Module `ast_parser.py` và `vbhn_merger.py` trên Hub hiện mới chỉ hỗ trợ thể thức Luật/Nghị định dạng `Điều X.`, `Chương Y.`, chưa hỗ trợ cây phân cấp chấm số của Quy chuẩn kỹ thuật (`### 1.1`, `#### 1.1.1`, `##### 1.1.1.1`, `1.4.X`).
- **Khoảng cách kỹ thuật ở Spoke:** Spoke `ccba-legal-knowledge` đã xử lý thành công thực tế cho QCVN 04:2021/BXD (Sửa đổi 01:2026) và QCVN 06:2022/BXD (Sửa đổi 1:2023) nhưng phải thông qua các script riêng biệt (`build_full_qcvn04_hopnhat.py`, `build_qcvn06_hopnhat.py`).
- **Hậu quả:** Khi có Thông tư hoặc Nghị định mới sửa đổi, kỹ sư phải viết lại script rời rạc, không tái sử dụng được năng lực lõi của Platform.

---

## 3. Giải Pháp & Cấu Trúc Đề Xuất (Proposed Architecture & Solution)

Dựa trên thiết kế kiến trúc đã được phê duyệt tại **[ADR 0017 (AST Structural Patching)](https://github.com/vvChu/ccba-legal-knowledge/blob/main/docs/adr/0017-ast-structural-patching-consolidation-engine.md)**:

1. **Nâng cấp `ccba_legal.ast_parser`:**
   - Bổ sung nhận diện cấu trúc phân cấp số chấm (`Numbered Heading Patterns`): `1.1`, `1.1.3`, `2.10.2.1`, `1.4.32`.
   - Bổ sung nhận diện thẻ neo inlined: `#### <a id="muc-1-4-32" name="muc-1-4-32"></a>1.4.32  Tên Thuật Ngữ`.
   - Hỗ trợ danh mục lồng đa tầng chuẩn CommonMark thụt lề 2 spaces (`  -`).

2. **Nâng cấp `ccba_legal.vbhn_merger` $\rightarrow$ `LegislativeConsolidator`:**
   - Bổ sung Semantic Action Tokens: `REPLACE_CLAUSE`, `INSERT_CLAUSE`, `REPEAL_CLAUSE`, `SUBSTITUTE_PHRASE`.
   - Tự động bao bọc điều khoản sửa đổi bằng GitHub-Flavored Markdown Callout:
     ```markdown
     > [!IMPORTANT]
     > *(Bổ sung/Sửa đổi bởi Điều X Thông tư Y/Z)*
     ```
   - Tự động sinh đồng thời 3 thành phẩm:
     * Tệp hợp nhất toàn văn: `*_hop_nhat_*.md`.
     * Cây AST giàu siêu dữ liệu: `clauses.json` (chứa `jurisdiction: 'CQXD' | 'CONG_AN'`, `source_pdf_page`, `grace_period_end`).
     * Bảng ma trận đối chiếu: `bang_so_sanh_*.md` (phân loại `🔴 Critical Defect` vs `🟡 Warning Notice`).

3. **Cung cấp CLI Seam Thống Nhất:**
   ```bash
   ccba-legal consolidate --base <base_bundle> --amendment <amendment_bundle> --output <output_dir>
   ```

---

## 4. Kế Hoạch Triển Khai & Kiểm Thử (Implementation & Verification Plan)
- **Tệp thay đổi trên Hub:**
  - `packages/ccba-legal-intel/src/ccba_legal/ast_parser.py` (Mở rộng regex và Node Hierarchy)
  - `packages/ccba-legal-intel/src/ccba_legal/vbhn_merger.py` (Nâng cấp thành Consolidator Engine)
  - `packages/ccba-legal-intel/tests/test_vbhn_merger.py` (Bổ sung test cases cho QCVN 04, QCVN 06, Luật Xây dựng)
- **Kiểm định:** Chạy toàn bộ test suite `pytest packages/ccba-legal-intel/tests/` đạt $100\%$ Passed.
