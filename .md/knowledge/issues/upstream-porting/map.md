# Bản đồ Wayfinder: Triển khai & Đồng bộ Tính năng từ `port_recommendations.md`

## Điểm đích (Destination)

Nền tảng CCBA Agent Platform được cập nhật hoàn chỉnh các tính năng đáng giá từ thượng nguồn `mattpocock/skills` (theo báo cáo [port_recommendations.md](../../port_recommendations.md)):
1. Kỹ năng mới `to-questionnaire` được port hoàn chỉnh tại `.agents/skills/to-questionnaire/SKILL.md`.
2. Kỹ năng `grilling` được nâng cấp tích hợp tư duy "design tree & frontier questions" từ `batch-grill-me`.
3. Kỹ năng `ask` được cập nhật thêm nguyên tắc "Branching (Prototype vs Spec)" và "Context Hygiene".
4. Toàn bộ thay đổi được đăng ký hợp lệ trong `catalog.yaml` và vượt qua kiểm định `validate_skills.py`.

## Ghi chú (Notes)

- **Reuse-First Gate**: Tuyệt đối không tạo skill trùng lặp. Đã loại bỏ các skill trùng tên hoặc trùng chức năng cốt lõi (`improve-codebase-architecture`, `to-tickets`, `wayfinder`, `grilling`).
- **Nguồn dữ liệu thượng nguồn**: Tệp local clone tại `.md/scratch/repos/mattpocock-skills` (SHA: `ed37663c`).
- **Tiêu chuẩn chất lượng**: Mọi SKILL.md phải đạt chuẩn `writing-great-skills` và pass lệnh `python scripts/validate_skills.py`.

---

## Quyết định đã chốt (Decisions so far)

- [Báo cáo Đánh giá Porting (port_recommendations.md)](../../port_recommendations.md): Phân loại rõ ràng 1 skill PORT mới (`to-questionnaire`), 1 skill UPGRADE (`batch-grill-me` ➔ `grilling`), và 5 skill IGNORE.
- [Port Skill to-questionnaire](../../../../.agents/skills/to-questionnaire/SKILL.md): Hoàn tất port kỹ năng tạo Bảng hỏi bất đồng bộ với chuẩn frontmatter CCBA.
- [Nâng cấp Skill grilling](../../../../.agents/skills/grilling/SKILL.md): Tích hợp quản lý Cây Thiết kế (Design Tree), Frontier Questions, và tự động tra cứu Facts qua sub-agent.
- [Bổ sung Cải tiến Skill ask](../../../../.agents/skills/ask/SKILL.md): Tích hợp quy tắc Vệ sinh Context (Context Hygiene) và rẽ nhánh Prototype vs Spec từ `ask-matt`.
- [Đăng ký Catalog & Validate](../../../../.agents/skills/platform-loader/catalog.yaml): Đã thêm `to-questionnaire` vào `catalog.yaml` và pass lệnh `python scripts/validate_skills.py` (81 skills [OK]).

---

## Danh sách Tickets

### T1: Port Kỹ năng `to-questionnaire` [Task — AFK]

- **Mục tiêu:** Tạo kỹ năng mới `.agents/skills/to-questionnaire/SKILL.md` từ tệp thượng nguồn `.md/scratch/repos/mattpocock-skills/skills/in-progress/to-questionnaire/SKILL.md`.
- **Đầu ra mong muốn:**
  - [x] `.agents/skills/to-questionnaire/SKILL.md` được tạo với đúng frontmatter tiêu chuẩn CCBA.
  - [x] Thêm các ví dụ và hướng dẫn sử dụng kết hợp với `ccba-research` & `handoff`.
- **Trạng thái:** ✅ Hoàn tất

---

### T2: Tích hợp Tư duy "Design Tree & Frontier" từ `batch-grill-me` vào `grilling` [Task — AFK]

- **Mục tiêu:** Nâng cấp kỹ năng hiện có `.agents/skills/grilling/SKILL.md` bằng cách tiếp thu cơ chế phân loại câu hỏi theo phụ thuộc (frontier) và quản lý cây thiết kế (design tree) từ `batch-grill-me`.
- **Đầu ra mong muốn:**
  - [x] `.agents/skills/grilling/SKILL.md` được cập nhật thêm phần Hướng dẫn Quản lý Frontier & Design Tree.
  - [x] Đảm bảo giữ nguyên interface và trigger tương thích ngược.
- **Trạng thái:** ✅ Hoàn tất

---

### T3: Đăng ký Catalog & Kiểm định Hệ thống [Task — AFK]

- **Mục tiêu:** Cập nhật tệp catalog và kiểm định toàn bộ skills trong nền tảng.
- **Đầu ra mong muốn:**
  - [x] Cập nhật `.agents/skills/platform-loader/catalog.yaml` để khai báo `to-questionnaire`.
  - [x] Lệnh `python scripts/validate_skills.py` chạy thành công 100% không có lỗi parser/schema.
- **Trạng thái:** ✅ Hoàn tất

---

### T4: Rà soát & Cherry-pick Bản vá Nhỏ từ Upstream [Research — AFK]

- **Mục tiêu:** Kiểm tra các tệp SKILL.md bị bỏ qua (`wayfinder`, `to-tickets`, `improve-codebase-architecture`, `ask-matt`) xem thượng nguồn có bản sửa lỗi/nâng cấp nhỏ nào đáng giá để cherry-pick vào bản local không.
- **Đầu ra mong muốn:**
  - [x] Đã nghiên cứu và bổ sung các điểm cải tiến từ `ask-matt` vào [.agents/skills/ask/SKILL.md](../../../../.agents/skills/ask/SKILL.md) (Rẽ nhánh Prototype/Spec & Context Hygiene).
  - [x] Đã đối soát `wayfinder`, `to-tickets`, `improve-codebase-architecture` — bản local hiện tại đã bao hàm đầy đủ các cải tiến.
- **Trạng thái:** ✅ Hoàn tất

---

## Sương mù chiến trận (Not yet specified)

- Không còn sương mù chưa được làm rõ.

---

## Ngoài phạm vi (Out of scope)

- Không port trùng lặp các skill đã có bản tương đương tốt hơn trên local.
- Không sửa đổi mã nguồn Python core ngoài phạm vi quản lý skill và catalog.

---
*Wayfinder map — Đã hoàn thành 100%.*
