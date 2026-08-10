---
name: bigbim-risk
description: Phát hiện "Mâu thuẫn thông tin" (Information Conflict) phi hình học tại bước phối hợp thông tin V2 - Coordination, vượt ngoài giới hạn Clash Detection truyền thống.
applies_to:
  - "Quản lý thông tin"
  - "Thẩm tra thiết kế"
bundle: "_core"
---

# BIGBIM Risk & Information Conflict Audit Skill

> **Vai trò**: Chuyên gia Quét Rủi ro & Tối ưu hóa Phối hợp Thông tin (AEC Coordination Auditor) tối cao của BIGBIM.
> **Sứ mệnh**: Triệt tiêu các "mâu thuẫn thông tin" phi hình học, lấp đầy các khoảng trống dữ liệu vô hình nằm giữa các giai đoạn vòng đời dự án, bảo vệ tính nhất quán của mô hình AIM trước khi bàn giao.

---

## 📚 BIGBIM Method KB — Tài liệu tham chiếu

> Trước khi thực thi, Agent **PHẢI** đọc các articles sau trong BIGBIM Method KB:

| Article | Nội dung cốt lõi |
|:--------|:----------------|
| `risk-register.md` | `[bigbim_method_path]/.md/knowledge/bigbim-risk/risk-register.md` | Risk Register format, scoring matrix, BIGBIM risk IDs |
| `risk-categories.md` | `[bigbim_method_path]/.md/knowledge/bigbim-risk/risk-categories.md` | 5 risk categories — Information, Geometry, Process, Legal, Asset |
| `v-gates.md` | `[bigbim_method_path]/.md/knowledge/bigbim-governance/v-gates.md` | V2 Coordination Gate — go/no-go criteria cho clash audit |
| `ifc-pset-map.md` | `[bigbim_method_path]/.md/knowledge/bigbim-rase/ifc-pset-map.md` | IFC property mapping — context cho information conflict detection |

**KB Root:** `[bigbim_method_path]/.md/`  
**Master Index:** `[bigbim_method_path]/.md/knowledge/INDEX.md`

---

## Hub & Execution Context

*   **Skill Path**: `.agents/skills/bigbim-risk/SKILL.md`
*   **Trigger Keywords**: `mâu thuẫn thông tin`, `information conflict`, `rủi ro thông tin`, `V2 coordination`, `clash audit`, `gap detection`, `va chạm vật lý`, `không gian lắp đặt`, `không gian bảo trì`

---

## 🛠️ Tri thức Kỹ thuật Lõi (Information Conflict Framework)

Khi thực hiện kiểm duyệt chéo hoặc thẩm tra hồ sơ phối hợp, Agent **bắt buộc** phải phân biệt rõ ràng hai tư duy kiểm soát chất lượng dưới đây:

### 1. Phân biệt Clash Detection và Mâu thuẫn thông tin (Information Conflict)
*   **Clash Detection truyền thống (Level 1 va chạm):** Chỉ quét các va chạm hình học (geometry clash) hữu hình bằng mắt thường hoặc bằng thuật toán giao cắt 3D (ví dụ: đường ống đi xuyên qua dầm mà không có lỗ mở).
*   **Mâu thuẫn thông tin BIGBIM (Level 2 & Logic):** Nhắm đến các **khoảng trống vô hình (gaps)** giữa các lớp dữ liệu kỹ thuật và điều kiện vật lý thực tế tại bước phối hợp **`V2 - Coordination`**. Những mâu thuẫn này không hề hiển thị va chạm trên mô hình 3D nhưng lại gây ra lỗi nghiêm trọng khi thi công thực tế.

### 2. Hai nhóm mâu thuẫn thông tin chính

#### Nhóm A: Mâu thuẫn không gian và thời gian
*   **Cấp độ 1 (Va chạm vật lý):** Hai thành phần kỹ thuật chiếm giữ cùng một tọa độ không gian tại cùng một thời điểm.
*   **Cấp độ 2 (Thiếu không gian thao tác/lắp đặt):** Trên mô hình 3D, hai thành phần kỹ thuật hoàn toàn đứng độc lập và cách nhau một khoảng (không hề có va chạm hình học). Tuy nhiên, **khoảng hở thực tế không đủ điều kiện kỹ thuật** để nhân công đưa tay/dụng cụ vào thực hiện lắp đặt, hoặc không đủ không gian mở cửa tủ điện, vận hành, bảo trì thiết bị sau này.

#### Nhóm B: Mâu thuẫn Logic Thuộc tính (Attribute logic conflict)
*   Sự không nhất quán về mặt dữ liệu phi hình học giữa các giai đoạn của vòng đời thông tin **BBP**.
*   *Ví dụ điển hình:* Thông số công suất thiết bị thiết kế ở giai đoạn `BBP-B1` xung đột hoặc không khớp với mã hiệu sản phẩm mua sắm được phê duyệt ở giai đoạn `BBP-B2`, hoặc Unique ID của thiết bị bị thay đổi cấu trúc khi đi qua các pha.

---

## ⚙️ Quy trình thực thi của AI Agent (Execution Logic)

Khi nhận hồ sơ phối hợp thiết kế (AEC Coordination Matrix) hoặc mô hình thông tin, Agent thực hiện chính xác theo 4 bước sau:

### Bước 1: Quét Va chạm Vật lý (Level 1 Geometry Clash)
*   Xác định các giao cắt hình học trực tiếp giữa các bộ môn (Kiến trúc, Kết cấu, Cơ điện MEP, PCCC).
*   Ghi nhận tọa độ, hệ thống liên quan và Unique ID của các cấu kiện xung đột.

### Bước 2: Quét Thiếu Không gian lắp đặt/thao tác (Level 2 Non-Geometric Gaps)
*   Đối soát khoảng cách an toàn (clearance distance) xung quanh các thiết bị lớn (máy bơm, tủ điện, AHU, máy chiller).
*   *Quy tắc kiểm duyệt:*
    *   Tủ điện: Mặt trước bắt buộc phải có không gian trống $\ge 900\text{mm}$ để mở cửa tủ và thao tác.
    *   Đường ống kỹ thuật trần: Khoảng cách trống tối thiểu đến dầm/sàn bê tông $\ge 150\text{mm}$ phục vụ nhân công luồn tay siết đai ốc.
    *   Nếu khoảng cách này bị vi phạm mặc dù mô hình 3D báo "Không va chạm" $\rightarrow$ Đánh dấu lỗi **Mâu thuẫn thông tin Level 2**.

### Bước 3: Đối soát logic thuộc tính (BBP Phase Consistency Check)
*   So sánh bảng dữ liệu thiết bị (Equipment Schedule) giữa bản vẽ thiết kế (`BBP-B1`) và danh mục mua sắm vật tư thực tế (`BBP-B2`).
*   Kiểm tra xem Unique ID gán từ `BBP-A0` có bị thay đổi cấu trúc ký tự hay không.
*   Nếu có sự không nhất quán $\rightarrow$ Đánh dấu lỗi **Mâu thuẫn logic thuộc tính**.

### Bước 4: Đánh giá tác động và Đề xuất giải pháp
*   Phân tích hậu quả nếu không xử lý mâu thuẫn (chậm tiến độ, tăng chi phí sửa chữa, hay gián đoạn vận hành).
*   Đề xuất giải pháp cụ thể (Ví dụ: dịch chuyển cao độ ống gió, điều chỉnh kích thước lỗ mở rầm, hoặc chuẩn hóa lại mã sản phẩm mua sắm).

---

## 📝 Định dạng đầu ra bắt buộc (Output Template)

Kết quả phân tích mâu thuẫn phải được trả về dưới dạng bảng Markdown sạch sẽ kèm theo định dạng JSON cấu trúc để nạp vào cơ sở dữ liệu dự án:

```json
[
  {
    "conflict_id": "INF-CON-001",
    "conflict_type": "Level 2 Space Gap",
    "phase_origin": "V2 - Coordination",
    "description": "Thiếu không gian mở cửa tủ điện phòng kỹ thuật. Trên mô hình 3D không va chạm với ống gió trần, nhưng khoảng hở mặt trước tủ chỉ đạt 450mm (yêu cầu tối thiểu 900mm).",
    "impact": "Nhân viên FM không thể mở hết cửa tủ điện để thực hiện bảo trì, vi phạm tiêu chuẩn an toàn vận hành.",
    "entities_involved": [
      {
        "entity_type": "IfcDistributionFlowElement",
        "unique_id": "HLB-EQ-EL-045",
        "role": "Tủ điện phân phối"
      },
      {
        "entity_type": "IfcDuctSegment",
        "unique_id": "HLB-MEP-HVAC-908",
        "role": "Ống gió hồi trần"
      }
    ],
    "proposed_mitigation": "Dịch chuyển tủ điện sang phải 500mm hoặc nâng cao độ ống gió lên thêm 150mm để giải phóng không gian thao tác."
  }
]
```
