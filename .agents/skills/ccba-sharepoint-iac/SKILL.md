---
name: ccba-sharepoint-iac
description: Quản trị hạ tầng SharePoint Online & M365 dạng mã nguồn (Infrastructure-as-Code).
  Hướng dẫn thiết kế JSON schema, kiểm định Lookups/Taxonomy và triển khai bằng PnP
  PowerShell.
disable-model-invocation: true
metadata:
  version: v1.0
  publisher: CCBA
bundle: _software
triggers:
- ccba-sharepoint-iac
- sharepoint iac
- sharepoint schema
- pnp powershell
- m365 iac
- datamodel sharepoint
---
# Kỹ Năng: SharePoint & M365 Infrastructure-as-Code (`sharepoint-iac`)

Kỹ năng này hướng dẫn AI Agent thiết kế, kiểm định và triển khai hạ tầng dữ liệu trên SharePoint Online (Microsoft 365) bằng phương pháp **Infrastructure-as-Code (IaC)** chuẩn hóa của CCBA Platform.

---

## 🎯 1. Nguyên Tắc Thiết Kế Cốt Lõi (Core Principles)

1. **Metadata-First Architecture (<5GB List Quota)**:
   - Các SharePoint Lists chỉ lưu trữ Text, Numbers, Dates, Lookups, Managed Metadata (Taxonomy) và Hyperlinks.
   - Tuyệt đối không đính kèm tệp binary trực tiếp vào List Items để bảo vệ 2TB Tenant Quota. Mọi tệp tin scan/PDF/bản vẽ phải được phân luồng sang thư mục chuyên dụng (hoặc 5TB Master OneDrive).
2. **Quy ước Đặt tên Cột Chuẩn Hóa**:
   - `InternalName`: Bắt buộc dùng **PascalCase** không dấu, không khoảng trắng (Ví dụ: `ContractCode`, `GrossAmount`, `PrimaryContractGroup`).
   - `DisplayName`: Tiếng Việt chuẩn có dấu (Ví dụ: `Mã Hợp đồng`, `Giá trị trước VAT`).
3. **Lookup Constraints**:
   - Luôn khai báo `Behavior: "restrict"` để đảm bảo tính toàn vẹn dữ liệu tham chiếu (Foreign Key Integrity).

---

## 📋 2. Cấu Trúc JSON Schema Chuẩn Cho SharePoint List

Mỗi List được lưu thành một tệp JSON trong `datamodel/sharepoint/lists/<domain>/<list_name>.json`:

```json
{
  "$schema": "datamodel/sharepoint/schemas/sp-list.schema.json",
  "ListName": "Contracts",
  "Description": "Quản lý Hợp đồng Kinh tế CCBA / IBST",
  "Columns": [
    {
      "Name": "ContractCode",
      "Type": "Text",
      "Required": true,
      "DisplayName": "Mã hợp đồng"
    },
    {
      "Name": "CustomerId",
      "Type": "Lookup",
      "Lookup": {
        "List": "Customers",
        "Field": "ID",
        "Behavior": "restrict"
      },
      "DisplayName": "Khách hàng"
    },
    {
      "Name": "PrimaryContractGroup",
      "Type": "ManagedMetadata",
      "TermSet": {
        "Group": "CCBA Taxonomy",
        "Name": "CCBA_NhomHopDongKT"
      },
      "DisplayName": "Nhóm HĐKT chính"
    },
    {
      "Name": "GrossAmount",
      "Type": "Number",
      "DisplayName": "Tổng giá trị (VND)"
    }
  ]
}
```

---

## 🛠️ 3. Quy Trình Kiểm Định & Triển Khai (Deployment Workflow)

Khi làm việc trên một Spoke có SharePoint IaC (như `idop-ccba-way`):

1. **Bước 1: Validate Schema Trước Khi Deploy**:
   ```powershell
   # Kiểm tra tính hợp lệ cú pháp JSON, Lookup references và Naming conventions
   .\idop.ps1 validate datamodel
   ```
   * **Tiêu chí hoàn thành:** Lệnh `.\idop.ps1 validate datamodel` trả về kết quả 100% hợp lệ không có lỗi cú pháp hoặc trường tham chiếu thiếu.

2. **Bước 2: Triển Khai Thử Nghiệm (DryRun)**:
   ```powershell
   # Quét sự khác biệt (diff) giữa JSON Schema và SharePoint Online thật
   .\idop.ps1 deploy lists -Environment IDOP -DryRun
   ```
   * **Tiêu chí hoàn thành:** Báo cáo diff hiển thị danh sách các trường thay đổi dự kiến mà không gặp lỗi kết nối hay quyền truy cập.

3. **Bước 3: Triển Khai Thật (Full Deployment)**:
   ```powershell
   # Đồng bộ cấu trúc vào môi trường production
   .\idop.ps1 deploy lists -Environment IDOP -Full
   ```
   * **Tiêu chí hoàn thành:** Toàn bộ SharePoint Lists và Managed Metadata được provisioning thành công trên SharePoint Online.

---

## 🔍 4. Checklist Rà Soát Chất Lượng (Quality Gate)

- [ ] Tên tệp tin JSON trùng khớp với tên bảng `ListName`.
- [ ] Mọi trường Managed Metadata đều có Term Set tồn tại trong Term Store.
- [ ] Không có trường nhị phân (Attachment/Binary) trong schema list.
- [ ] Toàn bộ lookup fields đều tham chiếu đến các bảng đã được định nghĩa.
