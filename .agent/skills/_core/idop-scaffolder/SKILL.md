---
name: ccba-idop-scaffolder
description: SharePoint IDOP deployment support toolkit
applies_to:
  - "Phần mềm"
bundle: "_core"
---

# SharePoint IDOP Scaffolder Skill

## 1. Triggers
Kích hoạt skill này khi người dùng yêu cầu:
- Khởi tạo thư mục dự án SharePoint (CDE layout)
- Tạo 7 list JSON schemas và 7 PnP PowerShell scripts
- Tạo spec và định nghĩa flow của Power Automate
- Chạy scaffolder cho IDOP SharePoint

## 2. Cách thực thi (Execution Guidelines)

Dùng CLI script `scripts/idop_scaffolder.py` để tự động hóa việc scaffold.

### Lệnh chạy CLI:
```bash
python scripts/idop_scaffolder.py [options]
```

### Các tùy chọn CLI hỗ trợ:
- `--cde`: Khởi tạo cấu trúc thư mục CDE (01_WIP, 02_Shared, 03_Published, 04_Archive, 05_Contract Reference).
- `--lists`: Tạo 7 danh sách JSON schema và file cấu hình PnP PowerShell (`.ps1`) tương ứng.
- `--workflows`: Tạo tài liệu đặc tả Power Automate (`PowerAutomate_spec.md`) và mock Flow Definition (`PowerAutomate_flow_definition.json`).
- `--all`: Chạy cả 3 tác vụ trên.
- `-o`, `--output-dir`: Đường dẫn thư mục đầu ra (mặc định là `./CDE`).

### Cấu trúc 7 SharePoint Lists:
1. **CRM**: Quản lý thông tin đầu mối/khách hàng.
2. **Contracts**: Quản lý hợp đồng (Lookup CRM).
3. **Finance**: Quản lý thu chi liên quan đến hợp đồng (Lookup Contracts).
4. **Approvals**: Quản lý quy trình phê duyệt hợp đồng (Lookup Contracts).
5. **HRAdmin**: Quản lý hồ sơ nhân viên và kỹ năng.
6. **LegalQA**: Quản lý các câu hỏi/kiểm toán pháp lý của hợp đồng (Lookup Contracts).
7. **RDProjects**: Quản lý dự án R&D.
