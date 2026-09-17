# ccba-to-tickets — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Kỹ thuật phân rã tài liệu đặc tả thành danh mục nhiệm vụ (tickets) chi tiết
> **Mô tả gốc:** Phân rã một kế hoạch, spec hoặc hội thoại hiện tại thành các ticket phát triển dạng lát cắt dọc (tracer-bullet slices), xác định rõ ràng mối quan hệ chặn (blocking edges) và đăng tải lên công cụ theo dõi (Issue Tracker) đã cấu hình.

---

# Kỹ năng Phân Rã Công Việc thành Tickets (To Tickets)

Phân rã một kế hoạch, đặc tả yêu cầu (spec), hoặc nội dung thảo luận hiện tại thành một bộ các **ticket** công việc độc lập. Mỗi ticket đại diện cho một lát cắt dọc (vertical slice) và khai báo rõ ràng các ticket con/mối nối **chặn** (block) nó.

Công cụ theo dõi công việc (Issue Tracker) và nhãn phân loại (Triage Labels) phải được cấu hình trước đó (nếu chưa, chạy lệnh `/ccba-setup-skills`).

---

## Quy trình thực hiện (Process)

### Bước 1: Thu thập ngữ cảnh (Gather context)

Đọc toàn bộ ngữ cảnh cuộc hội thoại hiện tại. Nếu người dùng truyền vào một tham chiếu cụ thể (đường dẫn spec, mã số issue hoặc URL của ticket trên tracker) làm đối số, Agent tiến hành truy cập và đọc toàn bộ nội dung chi tiết cùng lịch sử bình luận của ticket đó.

**Tiêu chí hoàn thành:** Toàn bộ ngữ cảnh và spec được phân tích rõ ràng.

### Bước 2: Khảo sát Codebase (Explore the codebase)

Nếu chưa thực hiện khảo sát codebase, hãy chạy các công cụ quét để nắm được cấu trúc và trạng thái mã nguồn hiện tại. Tiêu đề và mô tả của ticket phải sử dụng đúng từ vựng trong Glossary (tài liệu miền tri thức `CONTEXT.md`) và tuân thủ các Quyết định Kiến trúc (ADRs) liên quan đến vùng code chuẩn bị chỉnh sửa.

Hãy tích cực tìm kiếm các cơ hội để tái cấu trúc mã nguồn trước (pre-factoring) giúp việc triển khai nghiệp vụ sau này dễ dàng hơn: *"Dọn dẹp mặt bằng trước khi xây dựng"*.

**Tiêu chí hoàn thành:** Khảo sát codebase hoàn tất và xác định cơ hội pre-factoring.

### Bước 3: Phác thảo lát cắt dọc (Draft vertical slices)

Chia nhỏ công việc thành các ticket theo nguyên lý **lát cắt dọc (tracer bullet)**:

<vertical-slice-rules>

- Mỗi lát cắt phải đi qua ĐẦY ĐỦ các tầng kiến trúc của hệ thống (Ví dụ: từ schema cơ sở dữ liệu $\rightarrow$ logic xử lý API $\rightarrow$ giao diện UI $\rightarrow$ bộ kiểm thử test case). Tuyệt đối không bẻ ticket cắt ngang (chỉ làm database hoặc chỉ làm UI).
- Một lát cắt hoàn thành phải có khả năng chạy thử nghiệm và kiểm chứng độc lập (demoable/verifiable).
- Quy mô của mỗi ticket phải vừa vặn để giải quyết trọn vẹn trong một phiên làm việc (context window) duy nhất của Agent.
- Mọi hoạt động tái cấu trúc dọn đường (pre-factoring) phải được tách thành ticket thực hiện trước.

</vertical-slice-rules>

Xác định **mối quan hệ chặn (blocking edges)** cho từng ticket: Chỉ rõ những ticket nào bắt buộc phải hoàn thành trước thì ticket này mới có thể bắt đầu. Ticket nào không bị chặn bởi bất kỳ ai có thể được thực hiện ngay lập tức (thuộc biên giới tri thức - Frontier).

**Ngoại lệ - Tái cấu trúc diện rộng (Wide Refactors)**:
Khi cần thực hiện một thay đổi cơ học nhưng có tầm ảnh hưởng lan rộng (blast radius) toàn bộ codebase (như đổi tên cột DB dùng chung, đổi kiểu dữ liệu của một struct/class cốt lõi) khiến việc bẻ lát cắt dọc không thể giữ cho CI luôn xanh, áp dụng chiến lược **mở rộng - thu hẹp (expand-contract)**:
1. **Mở rộng (Expand)**: Tạo ticket viết thêm code mới (form mới) chạy song song với code cũ mà không làm hỏng các call sites hiện tại.
2. **Di chuyển (Migrate)**: Tạo các ticket nhỏ hơn theo từng directory/package để chuyển dần các call sites sang dùng code mới.
3. **Thu hẹp (Contract)**: Sau khi không còn call site nào dùng code cũ, tạo ticket xóa bỏ hoàn toàn code cũ. Chiến lược này giúp giữ cho CI luôn xanh từ đầu đến cuối quy trình.

**Phân rã Epic quy mô lớn (Monorepo Features):** Đối với các Epic lớn hoặc tính năng đa package monorepo, khuyến nghị triệu hồi [`/ccba-issue-tree`](../../ccba-issue-tree/SKILL.md) (Workplan What-Tree) để phân loại toàn bộ đầu việc vào 4 thẻ chuẩn mực MECE: `[ANALYSIS]`, `[DECISION]`, `[COMMITMENT]`, và `[SYNTHESIS]`, đảm bảo bao phủ 100% không gian công việc (Collectively Exhaustive) không bỏ sót rủi ro tích hợp.

**Tiêu chí hoàn thành:** Danh sách lát cắt dọc được phác thảo với quan hệ chặn đầy đủ.

### Bước 4: Hỏi ý kiến người dùng (Quiz the user)

Trình bày danh sách ticket đề xuất dưới dạng danh mục được đánh số. Với mỗi ticket, hiển thị rõ ràng:
- **Tiêu đề (Title)**: Tên mô tả ngắn gọn, súc tích.
- **Bị chặn bởi (Blocked by)**: Danh sách các ticket gate nó.
- **Giá trị bàn giao (What it delivers)**: Hành vi end-to-end mà ticket này mang lại từ góc nhìn của người dùng (không viết danh sách kỹ thuật thuần túy).

Hỏi người dùng:
- Độ mịn của ticket đã hợp lý chưa? (quá thô hay quá chi tiết?)
- Các mối quan hệ chặn đã chính xác chưa?
- Có cần gộp hoặc tách nhỏ thêm ticket nào không?

Lặp lại thảo luận cho đến khi người dùng đồng ý duyệt danh sách.

**Tiêu chí hoàn thành:** Người dùng xác nhận và đồng ý duyệt danh sách ticket.

### Bước 5: Đăng tải lên Issue Tracker (Publish)

Đăng tải các ticket đã được duyệt lên tracker tương ứng theo cấu hình:

- **Local Markdown**: Ghi nhận danh sách vào tệp `tickets.md` đặt trong thư mục `.md/knowledge/issues/` (hoặc `.md/knowledge/issues/<feature-slug>/tickets.md`). Sắp xếp các ticket theo thứ tự phụ thuộc (blockers viết trước), sử dụng template bên dưới.
- **Tracker thật (GitHub, GitLab...)**: Tạo các issue tương ứng trên tracker theo thứ tự phụ thuộc để lấy ID làm tham chiếu chặn. Áp dụng các mối quan hệ chặn bản địa của tracker (như Sub-issues hoặc Issue dependencies). Gắn nhãn `ready-for-agent` cho các ticket sẵn sàng để Agent AFK tự động vào nhận việc.

Tuyệt đối không tự ý đóng hoặc sửa đổi issue cha (parent issue) khi chưa hoàn thành tất cả ticket con.

**Tiêu chí hoàn thành:** Các ticket được đăng tải lên tracker hoặc lưu vào tickets.md.

---

## Các biểu mẫu mẫu (Templates)

### Template file tickets.md (Local Markdown)

```markdown
# Danh sách Tickets: <tên tính năng/nhiệm vụ>

Tóm tắt ngắn gọn mục tiêu của chuỗi ticket này. Liên kết đến tài liệu spec/PRD nếu có.

👉 Nguyên tắc: Chỉ thực hiện các ticket nằm ở Biên giới (Frontier) - là những ticket không bị chặn hoặc tất cả blockers của nó đã ở trạng thái [x] hoàn thành.

## <Tiêu đề Ticket>

**Nghiệp vụ cần làm:** Mô tả hành vi end-to-end từ góc nhìn người dùng sau khi ticket này hoàn tất (không viết danh sách code cần sửa).

**Bị chặn bởi:** <Tên các ticket chặn> hoặc "Không có — có thể bắt đầu ngay".

- [ ] Tiêu chí nghiệm thu 1 (Acceptance criterion 1)
- [ ] Tiêu chí nghiệm thu 2

## <Tiêu đề Ticket tiếp theo>
...
```

### Template Issue (GitHub/GitLab)

```markdown
## Parent
Liên kết đến issue cha hoặc PRD (nếu có).

## Nghiệp vụ cần làm (What to build)
Mô tả hành vi end-to-end từ góc nhìn người dùng sau khi ticket này hoàn tất.

## Tiêu chí nghiệm thu (Acceptance criteria)
- [ ] Tiêu chí 1
- [ ] Tiêu chí 2

## Blocked by
- Danh sách liên kết đến các ticket chặn (#ID), hoặc "Không có — có thể bắt đầu ngay".
```

Tránh đưa các đoạn code cụ thể hoặc đường dẫn file cứng vào ticket vì chúng sẽ nhanh bị lỗi thời. Ngoại lệ: Nếu mẫu thử (prototype) tạo ra các đoạn code định nghĩa cấu trúc dữ liệu, state machine hoặc schema quan trọng, có thể chèn phiên bản rút gọn vào ticket.

Thực hiện từng ticket một theo biên giới frontier bằng kỹ năng `/ccba-implement` và nhớ dọn sạch context (clear context) giữa mỗi ticket để tránh ô nhiễm ngữ cảnh.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
