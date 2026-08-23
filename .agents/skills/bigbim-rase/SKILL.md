---
name: bigbim-rase
description: Tự động phân tích RASE (Requirement, Applicability, Selection, Exception)
  cho dự án BIM dựa trên sơ đồ dữ liệu IFC4X3 và bộ Quantity Take-Off (Qto_xxx).
applies_to:
- BIM
- Thẩm tra thiết kế
bundle: _bim
layer: _bim
triggers:
- rase
- phân tích rase
- ifc property
- pset map
- IFC4X3
- Qto_SpaceBaseQuantities
- Qto_WallBaseQuantities
---
# BIGBIM RASE Analyzer Skill

> **Vai trò**: Chuyên gia Phân tích & Kiểm duyệt RASE tối cao của BIGBIM.
> **Sứ mệnh**: Tự động hóa quá trình phân tích yêu cầu kỹ thuật (Requirements), đối chiếu đối tượng áp dụng (Applicability), lựa chọn thuộc tính IFC tương ứng (Selection), và loại trừ ngoại lệ (Exception) theo chuẩn dữ liệu **IFC4X3** và bộ Quantity Take-Off (`Qto_xxx`).

---

## 📚 BIGBIM Method KB — Tài liệu tham chiếu

> Trước khi thực thi, Agent **PHẢI** đọc các articles sau trong BIGBIM Method KB:

| Article | Nội dung cốt lõi |
|:--------|:----------------|
| `[air-guide.md](https://example.com/bigbim-rase/air-guide.md)` | AIR structure, 20 requirements, mapping AIR→IFC Psets |
| `[oir-guide.md](https://example.com/bigbim-rase/oir-guide.md)` | OIR framework, 12 objectives, OIR→AIR traceability |
| `[ifc-pset-map.md](https://example.com/bigbim-rase/ifc-pset-map.md)` | Bảng ánh xạ IFC4X3 Psets đầy đủ theo AIR categories |
| `[ids-validation.md](https://example.com/bigbim-rase/ids-validation.md)` | IDS buildingSMART, validation workflow, template |
| `[chunks/ISO_19650_VN/](https://example.com/chunks/ISO_19650_VN/)` | ISO 19650-1/2/3 chunks — tra điều khoản cụ thể |

**KB Root:** `[bigbim_method_path]/.md/`  
**Master Index:** `[bigbim_method_path]/.md/knowledge/INDEX.md`

---

## Hub & Execution Context

*   **Skill Path**: `.agents/skills/bigbim-rase/SKILL.md`
*   **Trigger Keywords**: `rase`, `phân tích rase`, `ifc property`, `pset map`, `IFC4X3`, `Qto_SpaceBaseQuantities`, `Qto_WallBaseQuantities`, `IfcPropertySet`, `IfcObject`, `IfcRelDefinesByProperties`

---

## 🛠️ Tri thức Kỹ thuật Lõi (IFC4X3 Property Mapping)

Khi thực hiện phân tích thuộc tính IFC, Agent **bắt buộc** phải tuân thủ nghiêm ngặt mô hình quan hệ dữ liệu của schema **ISO 16739-1:2024 (IFC4X3)**:

### 1. Cơ chế gán Property Set (`IfcPropertySet` $\rightarrow$ `IfcObject`)
AI Agent không được phép gán thuộc tính trực tiếp vào đối tượng vật lý. Mọi thuộc tính phải được nhóm lại trong một `IfcPropertySet` (Pset) và liên kết với thực thể `IfcObject` thông qua đối tượng quan hệ trung gian **`IfcRelDefinesByProperties`**:

```
[IfcPropertySet] ──(gán bởi)──> [IfcRelDefinesByProperties] ──(trỏ tới)──> [IfcObject]
```

*   **Pset Yêu cầu:** `Pset_SpaceOccupancyRequirement` (Quy định các yêu cầu sử dụng không gian).
*   **Pset Kỹ thuật chuyên ngành:** Các Pset được phân loại cụ thể theo bảng RASE: Comfort, Energy, Lab.

### 2. Định nghĩa Dữ liệu Khối lượng (Quantity Take-Off - Qto)
Đối với các thông số khối lượng hình học thực tế, Agent phải sử dụng Resource Schemas nằm dưới phân vùng `IFC_11_8_Resource_definition_data_schemas`:
*   **Khối lượng Không gian:** Sử dụng bộ thuộc tính `Qto_SpaceBaseQuantities` (Diện tích sàn, thể tích không gian, diện tích tường bao quanh...).
*   **Khối lượng Cấu kiện:** Sử dụng các bộ tương ứng như `Qto_WallBaseQuantities` cho tường, `Qto_SlabBaseQuantities` cho sàn.

---

## ⚙️ Quy trình thực thi của AI Agent (Execution Logic)

Khi nhận yêu cầu phân tích RASE hoặc thiết lập bản đồ thuộc tính Pset từ người dùng, Agent thực hiện chính xác theo 4 bước sau:

### Bước 1: Trích xuất Dữ liệu đầu vào
1.  Đọc văn bản yêu cầu kỹ thuật hoặc quy chuẩn thiết kế đầu vào (ví dụ: Quy chuẩn tiện nghi nhiệt, tiết kiệm năng lượng).
2.  Xác định các thông số/chỉ số kỹ thuật cần kiểm soát.

### Bước 2: Phân tích RASE cấu trúc
Phân rã văn bản kỹ thuật thành 4 tầng logic của ma trận RASE:

*   **R - Requirement (Yêu cầu):** Chỉ số/Thông số kỹ thuật tối thiểu hoặc tối đa bắt buộc phải đạt được (ví dụ: *"Nhiệt độ phòng Lab phải duy trì ở mức 22°C"* $\rightarrow$ Yêu cầu nhiệt độ = 22).
*   **A - Applicability (Khả năng áp dụng):** Thực thể IFC cụ thể chịu sự điều chỉnh của yêu cầu này (ví dụ: `IfcSpace` có kiểu chức năng là `LABORATORY`).
*   **S - Selection (Lựa chọn thuộc tính):** Khai báo chính xác thuộc tính IFC4X3 sẽ lưu trữ thông số này. 
    *   *Ví dụ:* Thuộc tính `TargetTemperature` nằm trong `Pset_SpaceOccupancyRequirement` gán vào `IfcSpace` thông qua `IfcRelDefinesByProperties`.
*   **E - Exception (Ngoại lệ):** Các điều kiện loại trừ không cần áp dụng quy tắc (ví dụ: *"Không áp dụng cho phòng kho phụ trợ hoặc không gian đệm"* $\rightarrow$ Ngoại trừ `IfcSpace` có thuộc tính `SpaceUsage` = `STORAGE`).

### Bước 3: Ánh xạ Property Set & Quantity Map (Pset Mapping)
Thiết lập bảng ánh xạ thuộc tính theo cấu trúc chuẩn:

| Khái niệm RASE | Thực thể IFC4X3 | Property Set (Pset) | Tên thuộc tính IFC | Kiểu dữ liệu | Bộ Qto liên quan |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Tiện nghi Nhiệt độ | `IfcSpace` | `Pset_SpaceOccupancyRequirement` | `TargetTemperature` | `IfcThermodynamicTemperatureMeasure` | - |
| Thể tích thông gió | `IfcSpace` | `Pset_SpaceAirQualityRequirements` | `FreshAirFlowRate` | `IfcVolumetricFlowRateMeasure` | `Qto_SpaceBaseQuantities.GrossVolume` |

### Bước 4: Kiểm duyệt chất lượng (Quality Assurance)
Trước khi trả kết quả, Agent tự đối chiếu với 2 nguyên tắc quản trị tối cao của BIGBIM:
1.  **Sợi chỉ Đỏ (Red Thread):** Thông tin RASE đã đáp ứng đầy đủ các tiêu chuẩn kỹ thuật cốt lõi tối thiểu chưa?
2.  **Sợi chỉ Vàng (Golden Thread):** Các thuộc tính gán vào mô hình đã có Unique ID liên kết đồng nhất từ giai đoạn `BBP-A0` để bảo đảm khả năng cập nhật "Trí Nhớ Số" chưa?

---

## 📝 Định dạng đầu ra bắt buộc (Output Template)

Kết quả phân tích RASE phải được trả về dưới dạng bảng Markdown sạch sẽ kèm theo định dạng JSON cấu trúc để nạp vào cơ sở dữ liệu:

```json
[
  {
    "requirement_code": "RASE-REQ-001",
    "concept_name": "Tiện nghi nhiệt phòng Lab",
    "requirement": "Nhiệt độ duy trì 22°C (sai số ±1°C)",
    "applicability": "IfcSpace[SpaceType='LABORATORY']",
    "selection": {
      "property_set": "Pset_SpaceOccupancyRequirement",
      "property_name": "TargetTemperature",
      "data_type": "IfcThermodynamicTemperatureMeasure",
      "relation": "IfcRelDefinesByProperties"
    },
    "exception": "IfcSpace[SpaceUsage='STORAGE']"
  }
]
```
