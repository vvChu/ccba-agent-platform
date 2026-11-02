# ccba-llm-wiki — Reference Guide (Dated & Commit-Pinned Historical LLM Wiki)

> **Mục đích & Ngữ cảnh sử dụng:** Duy trì bộ nhớ tri thức bền vững qua nhiều phiên làm việc (vượt qua rào cản cắt gọn ngữ cảnh — context compaction) bằng cấu trúc LLM Wiki lưu trữ lịch sử có gắn ngày tháng và định danh commit SHA.
> **Nguồn gốc:** Thích ứng từ `chief-of-staff` (`v1.3.2` #1304) của Matt Pocock (MIT License), địa phương hóa theo quy ước cô lập không gian tên `.md/knowledge/wiki/` của CCBA Platform (`COND-02`).

---

## 1. Kiến Trúc Không Gian Tên & Bảo Toàn Mục Lục Gốc (`COND-02`)

Tri thức tích lũy trong cửa sổ ngữ cảnh của một phiên làm việc sẽ bị mất khi compaction hoặc khi kết thúc phiên. **LLM Wiki** là tập hợp các trang Markdown liên kết chéo nhau trên đĩa để truyền tri thức sang các phiên kế tiếp:

1. **Cô lập Không gian tên tại `.md/knowledge/wiki/` (`COND-02`):**
   - Toàn bộ hệ thống trang của LLM Wiki phải đặt bên trong thư mục `.md/knowledge/wiki/` để **bảo tồn nguyên vẹn tệp mục lục gốc [`.md/knowledge/index.md`](../../../../.md/knowledge/index.md)** của dự án.
   - Tệp điều hướng trung tâm của Wiki đặt tại **`.md/knowledge/wiki/index.md`**, đồng thời duy trì liên kết hai chiều (bidirectional link) với `.md/knowledge/index.md`.
2. **Cấu trúc Tệp trong `.md/knowledge/wiki/`:**
   - **`.md/knowledge/wiki/index.md`**: Liệt kê mọi trang trong Wiki kèm liên kết tương đối và tóm tắt đúng 1 dòng, được gom nhóm theo danh mục (*Decisions*, *Subsystems*, *Recurring Problems*, *User Preferences*).
   - **`.md/knowledge/wiki/<topic-slug>.md`**: Mỗi trang giải quyết đúng **một chủ đề duy nhất** (một quyết định kiến trúc, một sự cố lặp lại, một phân hệ kỹ thuật, hoặc một quy ước của người dùng) và liên kết chéo tới các trang liên quan.
   - **Nguyên tắc Viện dẫn Nguồn gốc (Never Copy Raw Sources):** Tuyệt đối không sao chép nguyên văn hoặc chỉnh sửa các nguồn dữ liệu gốc (Issues, PRs, transcripts, báo cáo subagent). Các trang Wiki chỉ **viện dẫn (cite)** đường dẫn hoặc mã định danh tới các nguồn đó.

---

## 2. Ba Thao Tác Duy Trì Sự Sống Cho Wiki (The Three Wiki Operations)

### 2.1. Nạp Tri Thức (`Ingest`)
- Khi Agent học được một dữ kiện bền vững (một quyết định thiết kế mới chốt, một chỉnh sửa từ người dùng, hoặc một phát hiện quan trọng từ subagent):
  - Không chỉ tạo một trang mới rời rạc, mà phải **cập nhật tất cả các trang chủ đề có liên quan** và cập nhật `.md/knowledge/wiki/index.md`.
- **Tiêu chí hoàn thành:** Mọi trang chủ đề bị ảnh hưởng và `.md/knowledge/wiki/index.md` được đồng bộ đầy đủ sau mỗi phát hiện mới.

### 2.2. Truy Vấn Trước Quyết Định (`Query`)
- Trước khi đưa ra một quyết định kiến trúc hoặc thiết kế mới, Agent bắt buộc đọc `.md/knowledge/wiki/index.md` và mở các trang chủ đề mà nó trỏ tới.
- Nếu câu trả lời hoặc kết luận tổng hợp được trong phiên hiện tại có giá trị sử dụng lâu dài cho các phiên sau, hãy đóng gói nó thành một trang Wiki mới.
- **Tiêu chí hoàn thành:** Đã đối chiếu `.md/knowledge/wiki/index.md` trước khi ra quyết định mới.

### 2.3. Kiểm Toán & Khử Trôi Dạt (`Lint`)
- Định kỳ rà soát thư mục `.md/knowledge/wiki/` để phát hiện và xử lý:
  - Các khẳng định mâu thuẫn nhau giữa hai trang;
  - Các trang mồ côi (*orphan pages*) không có trong `.md/knowledge/wiki/index.md`;
  - Các liên kết tương đối bị đứt;
  - Các khẳng định cũ đã bị vượt qua bởi các commits hoặc nguồn dữ liệu mới hơn.
- **Tiêu chí hoàn thành:** Không còn trang mồ côi, liên kết hỏng hoặc khẳng định mâu thuẫn chưa được đánh dấu kế thừa.

---

## 3. Bất Biến "Ghi Lịch Sử, Không Ghi Hiện Tại" (`Write History, Not the Present`)

Một trang Wiki **không bao giờ được tự nhận là đang mô tả trạng thái hiện tại tuyệt đối của mã nguồn**, bởi tài liệu tĩnh không thể tự đuổi kịp từng dòng code thay đổi mỗi ngày. Hãy viết Wiki như một **biên niên sử có mốc định danh (Historical Record)**:

1. **Gắn ngày tháng (`YYYY-MM-DD`) cho mọi khẳng định:**
   - *Mẫu chuẩn:* `"Vào ngày 2026-11-01, nhóm dự án quyết định tách lớp Tier 2A cho các tài liệu tham chiếu có GPI < 12.0."`
2. **Gắn mã định danh `repo@commit_sha` cho mọi khẳng định về mã nguồn:**
   - *Mẫu chuẩn:* `"Tính đến ccba-agent-platform@27101e0, bộ kiểm tra test_skills_docs_integrity.py khóa cứng tổng số 76 Hub Skills."`
3. **Nghiêm cấm dùng từ chỉ hiện tại không kèm mốc định danh:**
   - Tuyệt đối không viết các từ *"hiện tại" (`currently`)*, *"bây giờ" (`now`)*, hoặc *"đang là" (`is`)* khi nói về hành vi của code mà không có ngày tháng (`YYYY-MM-DD`) hoặc mã commit (`repo@commit_sha`) đứng ngay bên cạnh.
4. **Cập nhật theo cơ chế Kế thừa (`Superseded`), không xóa lịch sử:**
   - Khi thiết kế hoặc hành vi mã nguồn thay đổi, hãy **thêm một dòng khẳng định mới kèm ngày và commit SHA mới**, đồng thời đánh dấu dòng khẳng định cũ là `[Superseded by YYYY-MM-DD @ <new_sha>]` thay vì xóa trắng hoặc ghi đè làm mất dấu vết lịch sử.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
