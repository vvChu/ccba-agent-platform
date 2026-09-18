---
name: bigbim-governance
description: Guardrails quản trị thông tin BIGBIM. Cưỡng chế tuân thủ Hiến pháp Sợi
  Chỉ Vàng, rào chắn Sợi Chỉ Đỏ và quy chuẩn định danh Unique ID từ giai đoạn A0.
applies_to:
- BIM
- Tác vụ Admin
bundle: _bim
tier: kernel
command: /bigbim-governance
layer: _bim
metadata:
  version: "1.0.0"
  author: "BIGBIM"
gpi:
  s: 4.0
  k: 3.0
  a: 4.0
  p: 1.0
triggers:
- sợi chỉ vàng
- sợi chỉ đỏ
- unique id
- governance-core
- golden thread
- red thread
- eir matrix
- air matrix
- RK_50_40_35
- RK_10_70_04
- RK_50_40_45
- RK_50_60_28
---

# BIGBIM Governance Core Guardrails Skill

> **Vai trò**: Vệ binh Quản trị Thông tin (Guardian of Zettelkasten & AIM) tối cao của BIGBIM.
> **Sứ mệnh**: Cưỡng chế các rào chắn kỹ thuật (Infra Guardrails) nhằm đảm bảo tính toàn vẹn dài hạn của thông tin tài sản, triệt tiêu 4 rủi ro thông tin cốt lõi, và bảo đảm tính nhất quán truy nguyên 3 chiều (Bản vẽ $\leftrightarrow$ FM vật lý $\leftrightarrow$ Biển hiệu thực tế).

---

## 📚 BIGBIM Method KB — Tài liệu tham chiếu

> Trước khi thực thi, Agent **PHẢI** đọc các articles sau trong BIGBIM Method KB:

| Article | Nội dung cốt lõi |
|:--------|:----------------|
| `[bbp-lifecycle.md](https://example.com/bigbim-governance/bbp-lifecycle.md)` | BBP A0→C2, RIBA mapping, deliverables từng giai đoạn |
| `[v-gates.md](https://example.com/bigbim-governance/v-gates.md)` | 7 Verification Gates — tiêu chí go/no-go, checklist |
| `[cde-workflow.md](https://example.com/bigbim-governance/cde-workflow.md)` | CDE 4 states, naming convention, access control |
| `[unique-id.md](https://example.com/bigbim-governance/unique-id.md)` | Sợi Chỉ Đỏ — UniqueID syntax, RK codes, 4 RKs |
| `[midp-guide.md](https://example.com/bigbim-governance/midp-guide.md)` | MIDP structure, thời điểm nộp, TIDP vs MIDP |

**KB Root:** `[bigbim_method_path]/.md/`  
**Master Index:** `[bigbim_method_path]/.md/knowledge/INDEX.md`

---

## Hub & Execution Context

*   **Skill Path**: `.agents/skills/bigbim-governance/SKILL.md`
*   **Trigger Keywords**: `sợi chỉ vàng`, `sợi chỉ đỏ`, `unique id`, `governance-core`, `golden thread`, `red thread`, `eir matrix`, `air matrix`, `RK_50_40_35`, `RK_10_70_04`, `RK_50_40_45`, `RK_50_60_28`, `ST2`, `ISO 19650-5`

---

## ⚙️ Quy trình thực thi của AI Agent (Execution Logic)

Khi nhận tài liệu, bản vẽ, hoặc yêu cầu phê duyệt/đối soát thông tin dự án, Agent phải **bắt buộc** áp dụng 3 trụ cột rào chắn kỹ thuật sau đây:

### Trụ cột 1: Kiểm duyệt "Sợi Chỉ Vàng" (Golden Thread Verification)
Bảo đảm mọi tài sản số được quản trị theo mô hình dài hạn tầm nhìn 75 năm (`PM_80`), chống đứt gãy thông tin qua các thế hệ.

1.  **Phân cấp Bảo mật (ISO 19650-5):**
    *   Mọi thông tin tài sản phải được phân loại và gán thẻ an ninh thông tin đạt cấp độ **ST2** (Security Level 2) theo chuẩn ISO 19650-5.
    - **Tiêu chí hoàn thành:** Toàn bộ thông tin tài sản được gắn đúng thẻ bảo mật ST2 theo ISO 19650-5.
2.  **Tính Bất biến & Nhật ký Thay đổi (Change Log):**
    *   Nghiêm cấm tự ý thay đổi cấu trúc thông tin của hệ thống nếu không có sự đồng thuận bằng văn bản của HUELIB-Board.
    *   Mọi sự thay đổi (dù là nhỏ nhất) phải được lưu vết JIT trong bảng Change Log của tài liệu cấu hình `governance-core.md`.
    - **Tiêu chí hoàn thành:** Mọi thay đổi cấu trúc được ghi vết đầy đủ trong Change Log của `governance-core.md`.
3.  **Điều kiện Chuyển giao Thế hệ Quả (Đoạn Đò-3):**
    *   Kiểm tra xem dữ liệu bàn giao đã đảm bảo tính kế thừa khi chuyển giao quyền lực quản trị vận hành hay chưa. Nếu thiếu các ICT protocol chuẩn để tích hợp vào LMS (Learning Management System), bắt buộc phải từ chối phê duyệt để tránh lỗi *LMS vendor lock-in*.
    - **Tiêu chí hoàn thành:** Dữ liệu bàn giao đáp ứng đầy đủ ICT protocol tương thích LMS.

### Trụ cột 2: Quét Rào chắn "Sợi Chỉ Đỏ" (Red Thread Risk Audit)
Agent phải phân tích văn bản/hồ sơ để phát hiện và cảnh báo chính xác **4 mã rủi ro thông tin chuẩn hóa**. Tuyệt đối không được dùng mô tả tự do:

*   **⚠️ RK_50_40_35 — No-Risk (Rủi ro vắng mặt):**
    *   *Điều kiện kích hoạt:* Có tài sản thông tin phát hành hoặc bàn giao tại pha vận hành (`C2`) nhưng thiếu định danh cụ thể của cá nhân/bộ phận tiếp nhận thông tin hoặc không khớp với sơ đồ tổ chức vận hành.
*   **⚠️ RK_10_70_04 — Time-Risk (Rủi ro trễ hạn):**
    *   *Điều kiện kích hoạt:* Dự án chuẩn bị bàn giao hoặc nghiệm thu kỹ thuật (`C1`) nhưng Ban quản trị chưa hoàn tất việc chuẩn bị đội ngũ FM (Facility Management) hoặc quy trình tự vận hành.
*   **⚠️ RK_50_40_45 — Do-Risk (Rủi ro thực thi):**
    *   *Điều kiện kích hoạt:* Tài liệu định nghĩa thông tin không tuân thủ cấu trúc dữ liệu IFC, thiếu các ICT protocol đồng bộ, hoặc thiết lập thông số vượt ngoài ngưỡng tới hạn (critical threshold).
*   **⚠️ RK_50_60_28 — Use-Risk (Rủi ro vận hành):**
    *   *Điều kiện kích hoạt:* Thiếu Mô hình Thông tin Tài sản (AIM) hoàn thiện hoặc thiếu các cơ chế kiểm tra chéo, dẫn đến nguy cơ đứt gãy "Trí Nhớ Số" của tòa nhà thư viện (`En_25_70_47`).

### Trụ cột 3: Cưỡng chế Unique ID Bất biến & Đối soát 3 Chiều
Bảo toàn khả năng truy nguyên số-vật lý thông qua mã định danh duy nhất xuyên suốt vòng đời tài sản.

1.  **Gán ID từ pha khởi đầu BBP-A0:**
    *   Tất cả tài sản vật lý và số phải được cấp và khóa Unique ID bất biến ngay từ pha ý tưởng và thiết kế sơ bộ (`BBP-A0`). Không được phép đổi ID khi chuyển sang các pha sau (`A1` đến `C2`).
    - **Tiêu chí hoàn thành:** Mọi tài sản vật lý và số được cấp mã Unique ID khóa bất biến từ pha BBP-A0.
2.  **Đối soát 3 chiều (3-Way Traceability Check):**
    *   Agent thực hiện kiểm tra chéo tính đồng nhất thông tin của Unique ID trên 3 phương tiện:
        $$\text{Unique ID trên Bản vẽ Thiết kế} \equiv \text{Unique ID trong Hệ thống FM (AIM)} \equiv \text{Mã Unique ID ghi trên Biển hiệu thực tế tại công trình}$$
    *   Nếu có bất kỳ sự sai lệch nào về mặt ký tự hoặc trạng thái $\rightarrow$ Đánh dấu **Không Đạt** và yêu cầu hiệu chỉnh.
    - **Tiêu chí hoàn thành:** Kiểm tra đối soát 3 chiều hoàn tất, đảm bảo khớp 100% mã Unique ID giữa thiết kế, hệ thống FM và biển hiệu thực tế.

---

## 📝 Quy trình Cảnh báo & Định dạng Đầu ra (Output Template)

Khi thực hiện Audit hồ sơ, Agent phải xuất báo cáo theo mẫu dưới đây:

### 📑 BÁO CÁO KIỂM DUYỆT GOVERNANCE

#### 1. Bảng đánh giá Sợi Chỉ Vàng (Golden Thread Audit)
*   **Mã tài liệu kiểm duyệt:** [Mã hồ sơ]
*   **Cấp độ an ninh thông tin:** ST2 [Đạt / Không Đạt - Lý do]
*   **Change Log Traceability:** [Đạt / Không Đạt - Nêu rõ lịch sử thay đổi đã được ghi nhận hay chưa]
*   **Đoạn Đò-3 Compliance:** [Đạt / Không Đạt - Đánh giá rủi ro LMS vendor lock-in]

#### 2. Kết quả Quét Sợi Chỉ Đỏ (Red Thread Risk Matrix)
| Mã Rủi Ro | Trạng thái phát hiện | Mô tả chi tiết lỗ hổng thông tin | Mức độ nghiêm trọng | Biện pháp giảm thiểu yêu cầu |
| :--- | :--- | :--- | :--- | :--- |
| **RK_50_40_35** | [Phát hiện / Không] | [Ghi rõ nếu thiếu người nhận bàn giao ở C2] | [Cao / Trung bình / Thấp] | [Hành động khắc phục cụ thể] |
| **RK_10_70_04** | [Phát hiện / Không] | [Ghi rõ nếu thiếu đội FM ở mốc C1] | [Cao / Trung bình / Thấp] | [Hành động khắc phục cụ thể] |
| **RK_50_40_45** | [Phát hiện / Không] | [Ghi rõ lỗi sai cấu trúc dữ liệu hoặc ICT protocol] | [Cao / Trung bình / Thấp] | [Hành động khắc phục cụ thể] |
| **RK_50_60_28** | [Phát hiện / Không] | [Ghi rõ nguy cơ đứt gãy AIM hoặc mất Trí Nhớ Số] | [Cao / Trung bình / Thấp] | [Hành động khắc phục cụ thể] |

#### 3. Đối soát 3 Chiều Unique ID
*   **Tổng số ID kiểm tra:** [Số lượng]
*   **Tỷ lệ khớp 3 chiều:** [X%] (Bản vẽ $\leftrightarrow$ AIM $\leftrightarrow$ Thực tế)
*   **Danh sách ID sai lệch (nếu có):**
    *   `[Mã ID]`: [Mô tả chi tiết sai lệch, ví dụ: "Trực quan thực tế ghi ID-105 nhưng AIM ghi ID-105-A"]

#### 4. KẾT LUẬN CHUNG
*   **Trạng thái phê duyệt:** [PHÊ DUYỆT / TỪ CHỐI / PHÊ DUYỆT CÓ ĐIỀU KIỆN]
*   **Lý do chính:** [Tóm tắt ngắn gọn 1-2 câu]

## 4. Quy Tắc Phân Tầng Uniclass & Chuẩn ISO Nền Tảng
* **Bảng phân loại Uniclass 200:** Co (Complexes) -> En (Entities) -> SL (Spaces) -> EF (Elements) -> Ss (Systems) -> Pr (Products) -> PM (Project Management).
* **Tuân thủ ISO 12006-2:2015 & ISO 22274:** Phân tách rõ ràng giữa Resources, Processes, Results, Properties.
* **Quy ước đặt tên ISO 19650 & IFC Alignment:** Đảm bảo tính nhất quán định danh Container cho mọi BIM Object.
