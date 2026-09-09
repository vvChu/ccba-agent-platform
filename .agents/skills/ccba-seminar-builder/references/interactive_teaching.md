# ccba-teach — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Mẫu hình giảng dạy tương tác trong các buổi seminar và đào tạo nội bộ
> **Mô tả gốc:** Hỗ trợ giảng dạy và đào tạo kiến thức tương tác, lưu trữ lộ trình và bài học trong thư mục chuyên biệt.

---

# Kỹ năng Đào tạo & Giảng dạy Tương tác (Teach)

Kỹ năng này thiết lập một không gian học tập tương tác (Teaching Workspace) được cô lập, cho phép tự động sinh bài giảng, theo dõi lịch sử ôn tập và tổng kết tiến trình học tập của cán bộ nhân viên hoặc đối tác.

## Không gian học tập (Teaching Workspace)

Để bảo vệ cấu trúc codebase, toàn bộ các tệp tin của không gian học tập sẽ được lưu trữ cục bộ bên trong thư mục ẩn **`.md/teach/`**:

- `.md/teach/MISSION.md`: Định nghĩa mục tiêu học tập cốt lõi của học viên. Định dạng theo [teach_mission-format.md](./teach_mission-format.md).
- `.md/teach/PROGRESS.md`: Bản tóm tắt tiến trình học tập hợp nhất (Consolidated Progress) để Agent đọc nhanh và tránh Context Bloat.
- `.md/teach/RESOURCES.md`: Danh mục tài nguyên, tài liệu tham khảo chính quy. Định dạng theo [teach_resources-format.md](./teach_resources-format.md).
- `.md/teach/NOTES.md`: Nơi ghi nhận sở thích, thói quen và các lưu ý đặc biệt về học viên.
- `.md/teach/lessons/`: Thư mục lưu trữ các bài học dưới dạng tệp HTML tĩnh (tên tệp: `0001-<dash-case-name>.html` tăng dần).
- `.md/teach/reference/`: Thư mục lưu trữ các cheat sheets, cú pháp mẫu hay bảng tra cứu nhanh dạng HTML. Định dạng theo [teach_glossary-format.md](./teach_glossary-format.md).
- `.md/teach/learning-records/`: Thư mục lưu trữ chi tiết nhật ký học tập (tên tệp: `0001-<dash-case-name>.md` tăng dần). Định dạng theo [teach_learning-record-format.md](./teach_learning-record-format.md).
- `.md/teach/assets/`: Các tài nguyên dùng chung (stylesheets CSS, mã script tương tác quiz...) được chia sẻ giữa các bài học HTML.

---

## Chỉ dẫn thực hiện quy trình dạy học

### Bước 1: Thiết lập Mục tiêu học tập (Onboarding & Mission Setup)
- Hỏi học viên về chủ đề muốn học và lý do quan trọng của chủ đề đó đối với họ.
- Tạo tệp `.md/teach/MISSION.md` và `.md/teach/NOTES.md` để ghi nhận thông tin.
- Tạo tệp `.md/teach/PROGRESS.md` khởi tạo danh sách lộ trình dự kiến.
- **Tiêu chí hoàn thành:** Tệp `MISSION.md` và `PROGRESS.md` được tạo thành công và học viên xác nhận đồng ý với lộ trình đề ra.

### Bước 2: Biên soạn & Trình diễn bài học (Lesson Delivery)
- Trước khi soạn bài mới, đọc `PROGRESS.md` để nắm bắt bài học kế tiếp trong vùng phát triển (ZPD).
- Tạo bài học HTML mới lưu vào `.md/teach/lessons/000X-*.html`. Thiết kế bài học đẹp mắt, tối giản, liên kết đến stylesheet dùng chung trong thư mục `assets/`.
- Thực hiện chạy lệnh mở bài học trên trình duyệt tự động cho học viên:
  ```powershell
  start .md/teach/lessons/000X-*.html
  ```
- **Bắt buộc**: In một bản tóm tắt nội dung bài học bằng Markdown trực tiếp trong giao diện chat IDE để học viên xem nhanh mà không cần chuyển màn hình.
- **Tiêu chí hoàn thành:** Tệp HTML bài học được tạo, lệnh mở trình duyệt chạy thành công, và nội dung tóm tắt Markdown được xuất đầy đủ trong chat.

### Bước 3: Đánh giá & Ghi nhận tiến độ (Feedback & Progress Consolidation)
- Tổ chức các câu hỏi trắc nghiệm (quizzes) hoặc bài tập nhỏ tương tác trực tiếp trong chat.
- Sau khi học viên hoàn thành, tạo nhật ký tiến độ mới tại `.md/teach/learning-records/000X-*.md` ghi nhận bài học rút ra.
- **Bắt buộc**: Cập nhật trạng thái bài học (từ `Chưa học` sang `Đã hoàn thành`) vào tệp hợp nhất **`.md/teach/PROGRESS.md`** để làm căn cứ cho các phiên tiếp theo.
- **Tiêu chí hoàn thành:** Nhật ký học tập được tạo và tệp `PROGRESS.md` được cập nhật chính xác trạng thái bài học mới nhất.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
