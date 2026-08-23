---
name: bigbim-classification
description: Tự động hóa viết bảng thực thể (En) và phân loại vật tư (PM) theo Uniclass
  200, tích hợp chuẩn ISO (22274, 21511, 12006-2), ISO 19650 Room Naming & IFC Alignment.
applies_to:
- BIM
- Thiết kế
bundle: _bim
layer: _bim
---
# BIGBIM Classification & Naming Skill

> **Vai trò**: Chuyên gia Kiến trúc thông tin & Phân loại học tối cao của BIGBIM.
> **Sứ mệnh**: Định hình "Trí Nhớ Số" (Digital Memory) cho mọi tài sản xây dựng, chuyển hóa các mô hình BIM từ chi phí trung gian thành tài sản dài hạn có khả năng kế thừa xuyên suốt vòng đời. Tự động hóa quá trình phân loại cấu kiện, đặt tên phòng phi tuyến tính (Dân dụng) và phân vùng tuyến tính định vị địa lý (Hạ tầng).

---

## 📚 BIGBIM Method KB — Tài liệu tham chiếu

> Trước khi thực thi, Agent **PHẢI** đọc các articles sau trong BIGBIM Method KB:

| Article | Đường dẫn tham chiếu (dưới `[bigbim_method_path]/.md/`) | Nội dung cốt lõi |
|:--------|:---------------------------------------------------------|:----------------|
| `uniclass-ss.md` | `knowledge/bigbim-classification/uniclass-ss.md` | Ss Systems — bảng phân loại, mapping BIM object types |
| `uniclass-en.md` | `knowledge/bigbim-classification/uniclass-en.md` | En Entities — phân loại công trình theo loại hình |
| `uniclass-pr.md` | `knowledge/bigbim-classification/uniclass-pr.md` | Pr Products — sản phẩm, catalog, NBS lookup guide |
| `ifc-entity-guide.md` | `knowledge/bigbim-classification/ifc-entity-guide.md` | IFC4X3 entity hierarchy, spatial structure rules |
| `naming-convention.md` | `knowledge/bigbim-classification/naming-convention.md` | File naming, discipline codes, revision codes |

**KB Root:** `[bigbim_method_path]/.md/`  
**Master Index:** `knowledge/INDEX.md` (dưới KB Root)

---

## Hub & Execution Context

*   **Skill Path**: `.agents/skills/bigbim-classification/SKILL.md`
*   **Trigger Keywords**: `phân loại`, `naming convention`, `room naming`, `uniclass`, `ISO 22274`, `ISO 21511`, `ISO 12006-2`, `Trí Nhớ Số`, `Digital Memory`, `ifc alignment`, `gis`, SL_table, En_table, PM_80

---

## 🛠️ Tri thức Kỹ thuật Lõi (Classification Foundation)

Khi thực hiện phân loại cấu kiện hoặc thiết lập quy ước đặt tên (Naming Convention), Agent **bắt buộc** phải tuân thủ nghiêm ngặt hệ thống lý thuyết của **BBH-Classification**:

### 1. Tích hợp 3 tiêu chuẩn ISO nền tảng
*   **ISO 22274:2013 (Nguyên lý thiết kế):** Đảm bảo hệ thống phân loại có tính logic chặt chẽ, các nhánh phân loại độc lập, không chồng chéo và có khả năng mở rộng không giới hạn khi bổ sung công nghệ mới.
*   **ISO 21511:2021 (Cấu trúc WBS):** Cấu trúc phân rã công việc (Work Breakdown Structure) để phân chia thực thể phức tạp thành các phân vị có thể quản lý được về mặt tiến độ và chi phí.
*   **ISO 12006-2:2015 (Framework đối tượng):** Phân chia vòng đời đối tượng xây dựng thành 4 lớp cốt lõi:
    *   *Resources (Nguồn lực):* Vật liệu, nhân công, thiết bị.
    *   *Processes (Quy trình):* Các công việc, hoạt động thi công/vận hành.
    *   *Results (Kết quả):* Các thực thể/sản phẩm hoàn thành (Complexes, Entities, Spaces, Elements).
    *   *Properties (Thuộc tính):* Đặc tính kỹ thuật, kích thước, hiệu suất.

### 2. Cấu trúc bảng Uniclass phân cấp
Agent thực hiện phân loại theo mô hình phân tầng từ vĩ mô đến vi mô của Uniclass:
$$\text{Co (Complexes)} \rightarrow \text{En (Entities)} \rightarrow \text{SL (Spaces/locations)} \rightarrow \text{EF (Elements)} \rightarrow \text{Ss (Systems)} \rightarrow \text{Pr (Products)}$$

---

## ⚙️ Quy trình thực thi của AI Agent (Execution Logic)

Khi nhận yêu cầu phân loại hoặc đặt tên từ người dùng, Agent thực hiện chính xác theo quy trình sau:

### Nhánh 1: Phân loại Không gian Dân dụng (Building - Phi tuyến tính)
Áp dụng cho các công trình dân dụng, tòa nhà (En_25_70_47):
1.  **Phân cấp không gian:** Phân rã không gian theo mô hình 3 cấp:
    $$\text{Tầng (Floor)} \rightarrow \text{Vùng chức năng (Zone)} \rightarrow \text{Phòng độc lập (Room)}$$
2.  **Chuẩn hóa đặt tên phòng (ISO 19650 Room Naming):**
    *   Sử dụng bảng **Uniclass SL (Spaces/locations)** để tra cứu mã chức năng không gian.
    *   Quy ước đặt tên Container Thông tin (Information Container - IC) phòng:
        $$\text{[Mã_Dự_Án]}-\text{[Mã_Tòa_Nhà]}-\text{[Tầng]}-\text{[Mã_SL_Uniclass]}-\text{[Số_Thứ_Tự]}$$
        *Ví dụ:* `HLB-B1-L02-SL_25_10_72-005` (Phòng đọc sách số 5 tại Tầng 2 tòa nhà HUELIB).

### Nhánh 2: Phân loại Không gian Hạ tầng (Infrastructure - Tuyến tính)
Áp dụng cho các công trình hạ tầng giao thông, cầu đường, đê kè:
1.  **Tọa độ địa lý & Định vị tuyến (GIS & IFC Alignment):**
    *   Không gian không được chia theo tầng mà phải chia dọc theo tuyến chính của dự án dựa trên tọa độ thực địa GIS và lý trình **IFC Alignment**.
2.  **Quy ước định vị phân cấp:**
    $$\text{Tuyến (Alignment)} \rightarrow \text{Lý trình (km/m)} \rightarrow \text{Nút giao/Phân đoạn} \rightarrow \text{Cấu kiện vật lý (Nhịp, Trụ, Dầm)}$$
    *   *Quy ước đặt tên:*
        $$\text{[Tên_Tuyến]}-\text{KM[Lý_Trình]}-\text{[Phân_Phân_Đoạn]}-\text{[Mã_EF_Uniclass]}$$
        *Ví dụ:* `Tuyen_NH1-KM012_500-NVD1-EF_20_10` (Hệ kết cấu móng tại lý trình km 12+500 của tuyến Quốc lộ 1).


### Nhánh 3: Tự động hóa phân loại bằng AI (AI-based Semantic Auto-Classification)
Áp dụng khi cần phân loại hàng loạt cấu kiện phi cấu trúc hoặc tên không chuẩn hóa:
1.  **Trích xuất thuộc tính IFC (ifcopenshell):** Quét mô hình để trích xuất cả thông tin hình học và metadata thô (Family Name, Material, Description).
2.  **Tiền xử lý & Sửa lỗi chính tả (Typo Normalization):**
    *   Thực hiện làm sạch dữ liệu và sửa các lỗi chính tả thô tiếng Việt (ví dụ: mất dấu, sai diacritics) trước khi vector hóa để tránh làm lệch vector embedding.
3.  **Xử lý ngữ nghĩa sâu (BERT/LLM Embeddings):** Chuyển đổi mô tả thô sang vector embedding để nắm bắt ngữ nghĩa thay vì so khớp từ khóa chính xác.
4.  **Dự đoán mã Uniclass (ISO 12006-2 Alignment):**
    *   Phân loại sang các bảng Uniclass tương ứng.
    *   *Mục tiêu độ chính xác (F1-Score):* Đạt trên 90% đối với cấu kiện Kiến trúc (Architectural); trên 80% đối với các thiết bị MEP chuyên sâu (do MEP có độ viết tắt cao và ít từ ngữ cảnh).

---

## 📝 Định dạng đầu ra bắt buộc (Output Template)

Kết quả phân loại phải được trả về dưới dạng bảng Markdown kèm theo định dạng JSON cấu trúc:

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

## 7. Rào Chắn Phân Định Bẫy Red-Team & Chuẩn Hóa Lỗi Viết Tắt
* **Bẫy Hộp Kỹ Thuật (Hybrid Enclosure):** Phân loại vỏ hộp bao che là `EF_25_10` (Kiến trúc Result), chứa các hệ thống MEP con `Ss` bên trong.
* **Bẫy Viết Tắt (Slang Normalization):** Tự động chuẩn hóa `btct` -> Bê tông cốt thép (`EF_20_20`), `san T3` -> `L03`.
* **Bẫy Hai Góc Nhìn (Result vs Resource):** Bóc tách rõ `EF_25_30` (Mô hình BIM Object Result) vs `Pr_30_59_24` (Mua sắm BOQ Resource) bảo tồn Trí Nhớ Số.
* **Bẫy Khoang Đệm Ngăn Cháy (Airlock Buffer):** Bắt buộc phân loại là `SL_25_30_70` (Không gian đệm an toàn/Air-lock).
* **Định danh Tuyến Hạ tầng IFC Alignment & ISO 19650:** Định danh cấu trúc không gian Spatial Structure và Trí Nhớ Số dọc tim tuyến (KM).