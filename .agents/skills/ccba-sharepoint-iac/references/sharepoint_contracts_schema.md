# SharePoint IaC — List Schema Mẫu & Chi Tiết Kiểm Định M365 Reference

Tài liệu tham chiếu Level 3 cho `ccba-sharepoint-iac`, lưu trữ mẫu JSON Schema hoàn chỉnh cho SharePoint List (`Contracts`), chi tiết hai mặt phẳng OneDrive (`Slice P8.17`), 4 Site IDs chuẩn, Self-Healing DLQ (`W8-DLQ-MATCH-01`) và tóm lược M365 3-Tier.

## 1. JSON Schema Mẫu Cho SharePoint List (`Contracts`)

Mỗi List lưu thành tệp JSON trong `datamodel/sharepoint/lists/<domain>/<list_name>.json`:

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
      "Indexed": true,
      "DisplayName": "Số hợp đồng"
    },
    {
      "Name": "CustomerId",
      "Type": "Lookup",
      "Indexed": true,
      "Lookup": {
        "List": "Customers",
        "Field": "Title",
        "Behavior": "restrict"
      },
      "DisplayName": "Khách hàng (Bên A)"
    },
    {
      "Name": "PrimaryContractGroup",
      "Type": "ManagedMetadata",
      "TermSet": {
        "Group": "CCBA Taxonomy",
        "Name": "CCBA_NhomHopDongKT"
      },
      "DisplayName": "Nhóm HĐKT chính (Phụ lục 7)"
    },
    {
      "Name": "RequiresIBSTSign",
      "Type": "YesNo",
      "DisplayName": "Yêu cầu trình Viện ký"
    },
    {
      "Name": "IBSTSubmissionStatus",
      "Type": "Choice",
      "Choices": [
        "Not_Required",
        "Pending_Internal",
        "Submitted_to_IBST",
        "IBST_Approved",
        "IBST_Returned"
      ],
      "DisplayName": "Trạng thái trình Viện (Gateway)"
    }
  ]
}
```

## 2. Chi Tiết Storage, Canonical Sites & Self-Healing DLQ

- **Phân nhánh `ccba-storage` (5TB):** `Documents/iOPS/` (`01_Bidding/`, `02_Contracts/`, `03_Finance/`, `04_HR_Assets/`, `05_Projects/`, cách ly `00_CCBA_Onboarding_SOPs/`) và `Documents/iCDE/` (`thiet_ke_BIM/`, `tvgs_qlda/`, `tham_tra/`, `kiemdinh_khaosat/`, `other/`, gồm `other/00_CCBA_Academy_Learning/` theo ISO 19650 `S0 -> S1 -> S2 -> S3 -> A1`).
- **Two-Plane OneDrive RBAC (`Slice P8.17`):** Tách `idop_client` vs `mysite_client`; gắn `$expand=RoleAssignments/Member,RoleAssignments/RoleDefinitionBindings`; skip quyền kế thừa bằng `if perm.get("inheritedFrom") is not None: continue` (tránh `HTTP 400` do `"inheritedFrom": {}` truthy sai); giữ `scope == "existingAccess"`, `IsSiteAdmin=true`, nạp `viva_satellite_live_bindings.json` đối xứng `--dry-run`/`--apply`.
- **4 Canonical Site Collections (`tools.auth.site_preflight`):**
  - Zone 1 (`https://ibstbim.sharepoint.com`, `925e6eaa-8908-4094-8d1a-75c46c7901c9`)
  - `/sites/iCDE` (`186131e8-e45d-4d8a-b05a-0d46530cae43`) — qua `_assert_safe_portal_canvas()`, chặn `controlType=3` và `Lists/LessonsLearned`
  - Zone 2 (`/sites/idop`, `812726c1-098f-4755-8cd1-65a5a9eb37f2`) — khóa `IDOP Members` `Read` (`1073741826`), đồng bộ `Employees.SystemRoles`, giữ sạch `Home.aspx` / `L10-Traction-Room.aspx` / `IDOP-Cockpit.aspx`
  - App Catalog (`/sites/appcatalog`) — gói `idop-cockpit-spfx.sppkg` (`ClientComponentManifest`, `@odata.nextLink`, SHA-256 `'Client Side Assets'`).
- **Tự Phục Hồi SQLite DLQ (`W8-DLQ-MATCH-01`):** Bật `PRAGMA busy_timeout = 5000`; `_is_superseded_tvgs_dlq_row` chỉ xóa nợ DLQ khi thỏa đủ 5 cổng (`PUSH_SHAREPOINT` + `Projects`, `item_id in {sp_item_id, project_code}`, payload chứa `_TVGS_ACTION_SIGNATURE_KEYS`, lỗi mạng/HTTP `429/500/502/503/504`, `row_dt <= sync_dt`). Cấm `--dlq-replay` đè payload cũ.

## 3. Phân Hạng Drift Cấu Hình 3 Bậc & Ghi Cột Phức Hợp REST

- **3 Bậc Drift:** *(1) Access & RBAC Isolation* -> *(2) Schema, State & Flow Behavior* -> *(3) Content & Navigation* (khử nhiễu GUID liên môi trường với `bindings_path=None`, chạy Pre-Deploy Role Verification trước mọi lệnh ghi).
- **Complex Fields REST & Required Null Blocker:** Nạp 1 lượt hidden Note map (`&$top=500` + `@odata.nextLink`) via `resolve_list_hidden_note_map_async` + `apply_complex_fields_via_sp_rest_async`; chạy `scan_required_column_null_blockers` trước khi bật `Required=True`.
