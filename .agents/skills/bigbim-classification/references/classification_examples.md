# BIGBIM Classification — Output JSON Template & Extended ISO Alignment Reference

Tài liệu tham chiếu Level 3 cho `bigbim-classification`, lưu trữ mẫu JSON chuẩn đầu ra và bảng đối chiếu mở rộng giữa Uniclass 200, ISO 12006-2, ISO 19650 và IFC4X3.

## 1. Mẫu JSON Đầu Ra Chuẩn (`Output Template`)

Kết quả phân loại chi tiết trả về kèm bảng Markdown theo lược đồ sau:

```json
[
  {
    "classification_id": "CLASS-001",
    "project_type": "Building",
    "uniclass_code": "SL_25_10_72",
    "uniclass_table": "Spaces/locations (SL)",
    "title_vi": "Không gian đọc sách công cộng",
    "standard_mapping": {
      "iso_12006": "Result",
      "iso_19650_naming": "HLB-B1-L02-SL_25_10_72-005",
      "wbs_level": "Level 4 - Room Space"
    },
    "metadata": {
      "building_ref": "En_25_70_47",
      "floor": "L02",
      "zone": "Public Area"
    }
  }
]
```

## 2. Đối Chiếu Phân Tầng Uniclass 200, Digital Memory & WBS ISO 21511

- **Bảng phân loại Uniclass 200 mở rộng:** `Co` (Complexes) $\rightarrow$ `En` (Entities) $\rightarrow$ `SL` (Spaces) $\rightarrow$ `EF` (Elements) $\rightarrow$ `Ss` (Systems) $\rightarrow$ `Pr` (Products) $\rightarrow$ `PM` (Project Management).
- **Tuân thủ ISO 12006-2:2015 & ISO 22274:** Phân tách rõ ràng `Resources`, `Processes`, `Results`, `Properties`.
- **Trí Nhớ Số (Digital Memory) & IFC4X3 Spatial Hierarchy:** Bảo tồn nhất quán định danh Information Container cho mọi BIM Object theo phân cấp `Site -> Building -> Floor -> Space/Room` (dân dụng) hoặc dọc tim tuyến `Alignment -> KM` (hạ tầng).
- **Phân Rã WBS Chuẩn ISO 21511 (Level 1-4) & IFC Entity Alignment:** Tích hợp mã phân loại chi phí/tiến độ và đồng bộ các lớp `IfcSystem`, `IfcProduct`, `IfcSpace` theo chuẩn OpenBIM.
