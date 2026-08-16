---
description: Đánh giá hiện trạng và tiếp nhận an toàn một codebase hiện hữu (Brownfield) vào mạng lưới CCBA Platform.
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
  - "Tác vụ Admin"
bundle: "_core"
disable-model-invocation: true
---
# Tiếp Nhận Spoke Hiện Hữu (/ccba-adopt-spoke)

Workflow này tự động hóa việc đánh giá hiện trạng, phân tích rủi ro và tiếp nhận thích ứng an toàn (**Non-Destructive Adoption**) một repository/codebase đã có sẵn vào mạng lưới **CCBA Hub-and-Spoke**, bảo tồn 100% dữ liệu nghiệp vụ và Hiến pháp riêng của Spoke.

---

## Các Bước Thực Hiện:

### 1. Đánh Giá Hiện Trạng & Xuất Ma Trận Rủi Ro (Discovery Matrix)
Agent chạy kiểm tra trước (Dry-Run) để lập báo cáo hiện trạng:
```powershell
python [hub_path]\scripts\adopt_spoke.py --spoke . --dry-run
```
Trình bày kết quả ma trận đánh giá cho người dùng:
* Stack công nghệ phát hiện (PowerShell/SharePoint, Python, Node.js, BIM CAD...).
* Tình trạng Git repository và tệp `workspace_context.yaml`.
* Các tệp tin được bảo vệ (AGENTS.md, datamodel, specs).

### 2. Thực Hiện Tiếp Nhận & Hợp Nhất Cấu Hình An Toàn
Sau khi người dùng đồng ý, Agent thực thi tiếp nhận:
```powershell
python [hub_path]\scripts\adopt_spoke.py --spoke .
```

Quá trình này sẽ tự động:
1. **Tạo bản sao lưu:** `workspace_context.yaml.bak_<timestamp>`.
2. **Additive Merge:** Bổ sung trường tương thích Hub, giữ nguyên 100% các nhóm tài liệu của Spoke.
3. **Cài đặt Guardrails:** Thiết lập Maskara pre-commit hook trong `.git/hooks/`.
4. **Đồng bộ Kỹ năng:** Bơm an toàn bundle Kỹ năng & Workflows phù hợp vào `.agents/skills/`.
5. **Đăng ký Hub Registry:** Đăng ký Spoke vào danh bạ mã hóa của CCBA Platform.

### 3. Báo Cáo Hoàn Tất
In thông báo:
*"🎉 Spoke đã được tiếp nhận thành công vào CCBA Platform! Toàn bộ cấu trúc nghiệp vụ cũ được bảo tồn 100%."*

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
