# Công cụ theo dõi công việc: Local Markdown (Offline)

Các lỗi (bugs), yêu cầu tính năng (Specs) và nhiệm vụ phát triển của dự án này được lưu trữ ngoại tuyến dưới dạng các file Markdown cục bộ trong thư mục `.md/knowledge/issues/`.

## Quy ước cấu trúc file (Conventions)

- Mỗi tính năng/nhiệm vụ lớn được nhóm vào một thư mục con: `.md/knowledge/issues/<feature-slug>/`
- Tài liệu Đặc tả Kỹ thuật (Spec) được đặt tại: `.md/knowledge/specs/spec-{slug}.md`
- Các issue chi tiết được đánh số và đặt tên theo định dạng: `.md/knowledge/issues/<feature-slug>/issues/<NN>-<slug>.md` (bắt đầu đánh số từ `01`).
- Trạng thái điều phối (Triage state) được ghi nhận ở dòng `Status: <trạng_thái>` nằm ở các dòng đầu tiên của file issue (xem chi tiết các trạng thái tại `triage_labels.md` nếu dự án có cài đặt triage, hoặc các trạng thái cơ bản: `claimed`, `resolved`, `open`).
- Lịch sử thảo luận, bình luận và log tiến độ sẽ được Agent append vào cuối file dưới tiêu đề `## Comments`.

## Khi Agent cần tạo Issue mới ("publish to the issue tracker")

Tạo một file Markdown mới tại đường dẫn tương ứng dưới `.md/knowledge/issues/<feature-slug>/issues/` (tự động tạo thư mục cha nếu chưa tồn tại).

## Khi Agent cần đọc nội dung Issue ("fetch the relevant ticket")

Đọc trực tiếp file Markdown tương ứng. Người dùng hoặc hệ thống sẽ cung cấp đường dẫn đầy đủ của file issue hoặc số thứ tự issue cần xử lý.

---

## Các thuật ngữ trong Quy trình Điều phối (Wayfinding)

Sử dụng bởi kỹ năng `/ccba-wayfinder` để quản lý các tác vụ phức tạp (Foggy problems) bằng cách dựng bản đồ nghiệp vụ cục bộ:

- **Bản đồ (Map)**: Được lưu tại tệp `.md/knowledge/issues/<feature-slug>/map.md`. Tệp này chứa ghi chú (Notes), các quyết định đã chốt (Decisions-so-far) và sơ đồ công việc.
- **Ticket con (Child ticket)**: Được lưu tại `.md/knowledge/issues/<feature-slug>/issues/<NN>-<slug>.md`. Trong file này bắt buộc có:
  - Trường `Type: <loại>` (`research`/`prototype`/`grilling`/`task`).
  - Trường `Status: <trạng_thái>` (`claimed`/`resolved`/`needs-triage`).
- **Rào cản/Phụ thuộc (Blocking)**: Được ghi nhận qua dòng `Blocked by: NN, NN` ở đầu file. Một ticket chỉ được unblock khi tất cả các file issue có số thứ tự tương ứng được đánh dấu trạng thái là `resolved`.
- **Claim Ticket**: Sửa dòng trạng thái thành `Status: claimed` và lưu file trước khi tiến hành viết code.
- **Resolve Ticket**: Trả lời câu hỏi bằng cách append câu trả lời dưới tiêu đề `## Answer`, sửa trạng thái thành `Status: resolved`, và cập nhật tóm tắt kết quả (kèm link tệp) vào Decisions-so-far trong file `map.md`.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
