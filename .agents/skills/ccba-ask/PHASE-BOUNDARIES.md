# Ranh giới Giai đoạn Context (Phase Boundaries Guide)

Một **giai đoạn (Phase)** là một khối công việc độc lập trong một phiên làm việc của Agent — như giai đoạn phỏng vấn (`/ccba-grilling`), giai đoạn soạn spec (`/ccba-to-spec`), giai đoạn bẻ ticket (`/ccba-to-tickets`), hoặc giai đoạn lập trình (`/ccba-implement`).

**Ranh giới giai đoạn (Phase Boundary)** là điểm giao giữa hai giai đoạn. Đây là điểm duy nhất để ra quyết định quản lý Context Budget. Tuyệt đối không thực hiện dọn dẹp hay nén context giữa chừng (mid-phase) vì sẽ làm Agent mất mạch suy nghĩ.

---

## 5 Lựa chọn Quản lý Context

| Lựa chọn | Hành vi & Tác động |
| :--- | :--- |
| **Continue (Tiếp tục)** | Giữ nguyên phiên làm việc hiện tại. Không chuyển đổi context. |
| **`/clear`** | Xóa sạch cửa sổ context, bắt đầu một phiên làm việc hoàn toàn mới. |
| **`/ccba-handoff`** | Đóng gói context thành file Markdown (.md) nhỏ gọn để chuyển tiếp. |
| **Subagent** | Ủy quyền một tác vụ cụ thể cho subagent chạy ngầm trong context riêng. |
| **`/compact`** | Nén lại toàn bộ context thành bản tóm tắt và khởi động phiên mới. |

---

## Cây Quyết định (Decision Tree)

Khi đứng tại ranh giới giai đoạn, hãy duyệt cây quyết định từ trên xuống dưới. **Lựa chọn đầu tiên thỏa mãn điều kiện "Đúng" (Yes) sẽ được áp dụng**:

### 1. Bạn có thể tiếp tục (Continue) trong phiên này không?
- **ĐIỀU KIỆN**: Giai đoạn tiếp theo bắt buộc phải dùng phiên làm việc này làm **Nguồn Gốc (Primary Source)**, HOẶC Context Budget còn đủ dung lượng trong vùng thông minh **Smart Zone** (~150k tokens) cho giai đoạn tiếp theo.
- *Ví dụ*: Chuyển từ phỏng vấn (`/ccba-grilling`) sang bẻ spec (`/ccba-to-spec`) và bẻ ticket (`/ccba-to-tickets`) nên nằm trong **1 phiên duy nhất** để giữ nguyên lý do thiết kế ban đầu.
- **Tiếp tục (Continue)** là phương án 0đ (không mất chi phí, không làm mất mát thông tin), hãy ưu tiên chọn trước tiên.

### 2. Context hiện tại có hoàn toàn không liên quan đến giai đoạn tiếp theo?
- **ĐIỀU KIỆN**: Tất cả các thử nghiệm, quyết định, và vết code cũ trong phiên đều có thể loại bỏ?
- **HÀNH ĐỘNG**: Chọn **`/clear`**. Đây là phương án tiết kiệm nhất: không mất thời gian và thu hồi lại 100% Context Budget.

> [!WARNING]
> Nếu lỡ `/clear` một context *đang còn giá trị*, bạn sẽ mất hoàn toàn lý do (the **why**) đằng sau các quyết định kiến trúc cũ mà không thể phục hồi lại từ git diff.

### 3. Bạn có cần bàn giao (Handoff) context sang môi trường/mục tiêu khác?
- **HÀNH ĐỘNG**: Sử dụng **`/ccba-handoff`** khi:
  - Chuyển đổi giữa các công cụ khác nhau (ví dụ: Antigravity ➔ Claude Code / Codex).
  - Chuyển sang một **thư mục làm việc khác** (ví dụ: chuyển sang repo prototype trong `/ccba-prototype`).
  - Đóng gói tài liệu để chuyển cho kỹ sư/người dùng khác tiếp quản.
  - Tách một nhánh công việc phụ xuất hiện giữa chừng mà không muốn derail luồng chính.

### 4. Tác vụ có thể tự động chạy mà không cần người dùng can thiệp?
- **HÀNH ĐỘNG**: Kích hoạt **Subagent**.
- *Ví dụ*: Quét kiểm định code review (`/ccba-code-review`), tra cứu tài liệu pháp lý ngầm (`ccba-research`). Subagent chạy trong context độc lập và trả về báo cáo kết quả.

### 5. Nếu không thỏa mãn các điều kiện trên ➔ Nén Context (`/compact`)
- **HÀNH ĐỘNG**: Sử dụng **`/compact`** kèm câu lệnh định hướng cụ thể (ví dụ: `/compact Chúng ta sẽ bắt đầu giai đoạn triển khai lập trình cho ticket #1`).
- `/compact` là **lựa chọn mặc định cuối cùng**, không phải là lựa chọn đầu tiên.

---

## Nguồn Gốc (Primary) vs Nguồn Thứ Cấp (Secondary)

Mọi lựa chọn ngoại trừ **Continue** đều biến một **Nguồn Gốc (Primary Source)** thành một **Nguồn Thứ Cấp (Secondary Source)** (bản tóm tắt).

| Loại Nguồn | Độ Đầy Đủ Thông Tin | Mức Độ Nhiễu Context | Dung Lượng Trống Còn Lại |
| :--- | :--- | :--- | :--- |
| **Primary (Continue)** | 100% Đầy đủ | Nhiều | Ít |
| **Secondary (`/compact`, `/ccba-handoff`)** | Có thể bị nén/mất mát | Thấp | Rất nhiều |

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
