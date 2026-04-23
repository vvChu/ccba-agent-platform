---
description: Đề xuất tích hợp skill/workflow/tool mới từ dự án (Spoke) lên Hub
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
---

# Workflow: Propose to Hub (Đóng Góp Ngược Lên Hub)

Khi người dùng phát hiện một skill, workflow, hoặc tool hữu ích trong quá trình làm việc tại một dự án (Spoke) và muốn tích hợp vào Hub chung để tất cả các dự án khác đều được hưởng lợi.

Gọi lệnh: `/propose-to-hub`

---

## Bước 1: Thu thập thông tin đề xuất

Hỏi người dùng tuần tự các câu hỏi sau:

1. **Loại đề xuất?**
   - `skill` — Kỹ năng mới (có script/logic riêng)
   - `workflow` — Quy trình lệnh mới
   - `tool` — Cấu hình/tích hợp tool mới (VD: thêm model AI, plugin)

2. **Tên đề xuất**: Tên ngắn gọn, dạng kebab-case (VD: `auto-pdf-namer`, `qc-heatmap-exporter`)

3. **Mô tả**: 1-2 câu giải thích skill/workflow này làm gì.

4. **Vấn đề giải quyết**: Vấn đề thực tế gặp phải ở dự án là gì?

5. **Loại dự án áp dụng**: Chọn từ danh sách:
   - `Phần mềm` / `Thẩm tra thiết kế` / `Thiết kế` / `Kiểm định` / `Tất cả`

6. **Có code/script mẫu không?** (Nếu có, yêu cầu đường dẫn file hoặc paste nội dung)

7. **Mức độ ưu tiên**: `Cao` / `Trung bình` / `Thấp`

---

## Bước 2: Kiểm tra trùng lặp

Trước khi ghi proposal, kiểm tra xem đề xuất có bị trùng với skill/workflow đã có không:

```powershell
# Tìm keyword trong tên các skill/workflow hiện có tại Hub
Get-ChildItem -Path "D:\GitHubProjects\ccba-agent-platform\.agent" -Recurse -Name | Select-String -Pattern "<tên-đề-xuất>"
```

- Nếu **trùng**: Thông báo cho user và hỏi có muốn đề xuất **nâng cấp** skill/workflow hiện có thay vì tạo mới không.
- Nếu **không trùng**: Tiến hành Bước 3.

---

## Bước 3: Ghi Proposal vào Hub Registry

Sử dụng `write_to_file` để tạo file proposal tại Hub:

**Đường dẫn**: `D:\GitHubProjects\ccba-agent-platform\.agent\proposals\<YYYY-MM-DD>_<tên-đề-xuất>.md`

**Nội dung file**:

```markdown
---
proposal_id: "<YYYY-MM-DD>_<tên-đề-xuất>"
type: "<skill|workflow|tool>"
name: "<Tên đề xuất>"
status: "open"
priority: "<Cao|Trung bình|Thấp>"
proposed_by_project: "<Tên dự án Spoke>"
proposed_date: "<YYYY-MM-DD>"
applies_to:
  - "<Loại dự án>"
---

## Mô tả
<Mô tả 1-2 câu>

## Vấn đề giải quyết
<Vấn đề thực tế>

## Giải pháp đề xuất
<Logic/cách hoạt động>

## Code/Script mẫu (nếu có)
```code
<nội dung code nếu có>
```

## Tác động dự kiến
- Tiết kiệm thời gian: <ước tính>
- Có thể áp dụng cho: <danh sách loại dự án>

## Notes
<Ghi chú thêm nếu có>
```

---

## Bước 4: Kiểm tra thư mục proposals tại Hub

```powershell
# Liệt kê tất cả proposals đang mở
Get-ChildItem -Path "D:\GitHubProjects\ccba-agent-platform\.agent\proposals" -Filter "*.md" |
    Select-Object Name, LastWriteTime | Sort-Object LastWriteTime -Descending
```

Thông báo cho user: Tổng số proposals đang chờ xem xét.

---

## Bước 5: Báo cáo hoàn tất

```
✅ Đề xuất "<Tên>" đã được ghi nhận vào Hub.
📁 File: .agent/proposals/<YYYY-MM-DD>_<tên-đề-xuất>.md
📋 Status: Open — Chờ review từ Platform team.

💡 Gợi ý tiếp theo:
   - Nếu skill này đủ trưởng thành, hãy gọi /new-feature tại Hub
     để tạo branch và implement chính thức.
   - Để xem tất cả proposals đang mở: xem thư mục
     D:\GitHubProjects\ccba-agent-platform\.agent\proposals\
```

---

## Khi nào nên gọi workflow này?

- Sau `session-retrospective` nếu phát hiện pattern/logic tái sử dụng được
- Khi giải quyết được một vấn đề mà bạn nghĩ các dự án khác cũng sẽ gặp
- Khi tìm thấy tool/tích hợp mới hữu ích (VD: model AI tốt hơn, thư viện Python mới)
- Khi workflow hiện tại có thể cải tiến đáng kể
