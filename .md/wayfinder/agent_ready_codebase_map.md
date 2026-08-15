# 🗺️ Bản đồ Định hướng Wayfinder: Chuyển đổi Codebase Chuẩn AI-Loved (Deep Modules & Progressive Disclosure)

> **Tài liệu tham chiếu gốc**: [How To Make Codebases AI Agents Love — Matt Pocock (AI Hero)](https://www.aihero.dev/how-to-make-codebases-ai-agents-love)  
> **Ngữ cảnh thực thi**: CCBA Agent Services Platform (`ccba-agent-platform`)

---

## 1. Điểm đích (Destination)

Toàn bộ kiến trúc mã nguồn của **CCBA Agent Services Platform** (và tiêu chuẩn áp dụng cho các Spoke) được tổ chức theo triết lý **Deep Modules & Grey Box Seams**:
1. **Giao diện công khai tinh gọn (Thin Seam)**: Mỗi module/package chỉ bộc lộ một giao diện bề mặt tối giản (`__all__`, `__init__.py` hoặc type definitions), giấu toàn bộ độ phức tạp bên trong.
2. **Độ bộc lộ tiệm tiến (Progressive Disclosure)**: Cấu trúc thư mục phản chiếu sơ đồ tư duy (mental map), AI Agent mới khởi tạo (vốn không có bộ nhớ dài hạn) có thể nắm bắt toàn bộ năng lực hệ thống ngay từ layer trên cùng mà không bị quá tải token.
3. **Vòng phản hồi siêu tốc (Fast Feedback Loops < 2s)**: Mỗi deep module có bộ test suite cô lập (Fast Unit Tests) giúp AI Agent tự xác thực độc lập việc triển khai (Implementation) mà không làm vỡ các module khác.
4. **Rào chắn phụ thuộc (Dependency Boundaries)**: Nghiêm cấm rò rỉ logic hoặc import vòng giữa các module nông.

---

## 2. Ghi chú & Tri thức Nền tảng (Notes)

- **Triết lý Cốt lõi**:
  - *AI là "nhân viên mới không có trí nhớ" (Memento guy)*: Khi spawn ra, AI chỉ nhìn thấy cấu trúc file và mã nguồn trước mắt.
  - *3 Thiệt hại của Codebase thiết kế sai*: Phản hồi chậm (Poor feedback loop), Khó định hướng (Hard to navigate), Kiệt sức nhận thức (Cognitive burnout).
  - *Mô hình Hộp Xám (Grey Box Modules)*: Kỹ sư/Con người sở hữu và thiết kế Giao diện (Interface / Seam), AI sở hữu việc thực thi (Implementation), và Bộ kiểm thử (Tests) bảo đảm tính chính xác.
- **Kỹ năng liên quan**:
  - `/ccba-improve-codebase-architecture` (Quét và làm sâu module).
  - `/domain-modeling` (Chuẩn hóa ngôn ngữ và seam trong `CONTEXT.md`).
  - `/ccba-setup-ts-deep-modules` & Dependency Boundary Linters.
  - `/eval-gate` & `/tdd` (Kiểm thử nhanh và khép kín).

---

## 3. Quyết định đã chốt (Decisions so far)

- **[Đã chốt - 2026-08-15] Khởi lập Bản đồ Định hướng từ Bài giảng Matt Pocock**: Xác định 5 ticket trọng tâm bao phủ 3 trụ cột: (1) Khảo sát module nông, (2) Thiết lập Thin Seams, (3) Tối ưu hóa Fast Test Loops, (4) Rào chắn kiểm định Dependency, và (5) Chuẩn hóa Domain Vocabulary.

---

## 4. Các Ticket ở Biên giới (Frontier Unblocked Tickets)

```mermaid
flowchart TD
    subgraph Frontier ["Biên giới (Frontier Unblocked)"]
        T1["[T1: Research] Khảo sát Module Nông (Shallow Modules Audit)"]
        T2["[T2: Task] Chuẩn hóa Seam & Public Exports cho Monorepo Packages"]
        T3["[T3: Task] Thiết lập Isolated Fast Test Suite (< 2s) cho từng Package"]
    end

    subgraph Blocked ["Bị chặn (Blocked / Dependent)"]
        T4["[T4: Task] Cấu hình Rào chắn Dependency Linter (Import-Linter / Cruiser)"]
        T5["[T5: Grilling] Phỏng vấn Chốt Seams cho các Sub-systems Trọng tâm"]
    end

    T1 --> T4
    T2 --> T5
    T3 --> T5
```

### Ticket 1: [Research/AFK] `[Khảo sát Module Nông trong Codebase]`
- **Mục tiêu**: Rà soát các packages (`packages/ccba-legal-intel`, `packages/ccba-ai`, `packages/ccba-qc-core`, `src/`) để xác định những nơi đang bị "xé lẻ" thành quá nhiều file nhỏ/hàm nhỏ rời rạc mà thiếu interface tổng thể bao bọc.
- **Loại ticket**: Research [AFK]
- **Đầu ra**: Báo cáo `.md/knowledge/shallow_modules_audit.md` liệt kê các module nông kèm kết quả Deletion Test.
- **Trạng thái**: Open (Unblocked)
- **Assignee**: AI Agent

### Ticket 2: [Task/AFK] `[Chuẩn hóa Seam & Public Exports cho Monorepo Packages]`
- **Mục tiêu**: Định hình rõ ràng public interface cho từng package thông qua `__all__` trong `__init__.py` và `AGENTS.md` cục bộ của package, loại bỏ việc bên ngoài import sâu vào các internal submodules.
- **Loại ticket**: Task [AFK]
- **Đầu ra**: Các Deep Seams được khai báo tường minh tại root của từng package.
- **Trạng thái**: Open (Unblocked)
- **Assignee**: AI Agent

### Ticket 3: [Task/AFK] `[Thiết lập Isolated Fast Test Suite (< 2s) cho từng Package]`
- **Mục tiêu**: Tách biệt rõ ràng unit test nhanh (Pure Logic, Mock I/O) chạy dưới 2 giây khỏi các integration test nặng hoặc e2e. Đảm bảo Agent nhận được phản hồi tức thì sau mỗi lần sửa implementation.
- **Loại ticket**: Task [AFK]
- **Đầu ra**: Cấu hình `pytest -m fast` hoặc scoped pytest scripts phản hồi siêu tốc.
- **Trạng thái**: Open (Unblocked)
- **Assignee**: AI Agent

### Ticket 4: [Task/AFK] `[Cấu hình Rào chắn Dependency Linter]`
- **Mục tiêu**: Cài đặt và cấu hình công cụ kiểm soát ranh giới phụ thuộc (ví dụ `import-linter` trong Python hoặc `dependency-cruiser` trong Node/TS) để tự động bắt lỗi khi có import vi phạm seam.
- **Loại ticket**: Task [AFK]
- **Blocked by**: Ticket 1, Ticket 2
- **Trạng thái**: Blocked

### Ticket 5: [Grilling/HITL] `[Phỏng vấn Chốt Seams cho các Sub-systems Trọng tâm]`
- **Mục tiêu**: Thực hiện grilling với Kỹ sư trưởng để thống nhất boundary cho các hệ thống phức tạp: QC Pipeline, Legal Intel RAG, TVPL VIP Crawler, Document Conversion Pipeline.
- **Loại ticket**: Grilling [HITL]
- **Blocked by**: Ticket 2, Ticket 3
- **Trạng thái**: Blocked

---

## 5. Sương mù chiến trận / Chưa xác định rõ (Not yet specified)

- **Agent Friction Index (Chỉ số Cản trở AI)**: Cơ chế tự động benchmark đo số lượng token tiêu tốn và số tool calls cần thiết để một Agent hoàn thành một tác vụ lập trình trước và sau khi làm sâu module.
- **Auto-Generated Type Registry**: Cơ chế tự động trích xuất public API contracts thành định dạng siêu gọn dành riêng cho LLM System Prompt.

---

## 6. Ngoài phạm vi (Out of Scope)

- Thay đổi thuật toán core hoặc thay đổi quy trình nghiệp vụ đã được quy định trong các QCVN/Luật Xây dựng (chỉ thay đổi cách đóng gói cấu trúc module, seam, và harness kiểm thử).
