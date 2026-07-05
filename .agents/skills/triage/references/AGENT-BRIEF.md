# Quy chuẩn Biên soạn Agent Brief (Writing Agent Briefs)

Agent Brief là tài liệu mô tả yêu cầu công việc được đăng tải khi ticket chuyển sang trạng thái `ready-for-agent`. Đây là bản cam kết kỹ thuật để Agent tiếp theo làm việc độc lập.

## Nguyên tắc cốt lõi (Principles)

1. **Bền vững hơn chi tiết tuyệt đối (Durability over precision):**
   - Viết tài liệu sao cho vẫn có giá trị sử dụng ngay cả khi các tệp tin bị đổi tên, di chuyển hoặc tái cấu trúc trong tương lai.
   - **Do:** Mô tả các interface, kiểu dữ liệu (types), và các quy tắc hành vi.
   - **Don't:** Không dẫn chiếu trực tiếp số dòng hoặc đường dẫn tệp tuyệt đối dễ bị thay đổi.

2. **Mô tả hành vi, không mô tả quy trình (Behavioral, not procedural):**
   - Mô tả hệ thống cần làm **cái gì** (what) thay vì hướng dẫn Agent phải sửa code **như thế nào** (how).
   - **Đúng:** "Cấu hình `SkillConfig` cần nhận thêm một trường tùy chọn `schedule` kiểu dữ liệu `CronExpression`."
   - **Sai:** "Mở file src/types/skill.ts và thêm trường schedule vào dòng số 42."

3. **Tiêu chuẩn nghiệm thu đầy đủ (Complete acceptance criteria):**
   - Cung cấp danh sách các hộp kiểm `[ ]` cụ thể để Agent biết khi nào công việc hoàn thành và có thể chạy kiểm thử độc lập.

4. **Xác định rõ giới hạn phạm vi (Explicit scope boundaries):**
   - Liệt kê cụ thể những tính năng/thành phần nằm ngoài phạm vi thực hiện (Out of scope) để tránh Agent tự phát sinh code thừa.

---

## Mẫu Agent Brief tiêu chuẩn (Template)

```markdown
## Agent Brief

**Phân loại:** bug / enhancement
**Tóm tắt yêu cầu:** [Mô tả ngắn gọn 1 dòng về mục tiêu tính năng/lỗi cần sửa]

### Hành vi hiện tại (Current behavior)
[Mô tả trạng thái hiện tại hoặc mô tả lỗi đang gặp phải kèm các bước tái lập]

### Hành vi mong muốn (Desired behavior)
[Đặc tả chi tiết cách hệ thống hoạt động sau khi Agent hoàn thành công việc]

### Các Interface & Kiểu dữ liệu chính (Key interfaces)
- `Kiểu_Dữ_Liệu` — Các thay đổi cần có.
- `hàm_xử_lý()` — Kiểu trả về mong muốn.

### Tiêu chuẩn nghiệm thu (Acceptance criteria)
- [ ] Tiêu chuẩn 1
- [ ] Tiêu chuẩn 2

### Phạm vi loại trừ (Out of scope)
- Các thành phần không được sửa đổi trong ticket này.
```

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
