---
name: CCBA AI QC Batch Orchestrator
description: Điều phối quá trình quét Audit chất lượng hồ sơ thiết kế (QC) đa bộ môn (Arch, KC, MEP, PCCC) trên quy mô lớn, thao tác hàng loạt qua file Coordination Matrix.
applies_to:
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_qc"
---

# CCBA AI QC Batch Orchestrator

**Batch Orchestrator** được phát triển nhằm mục đích tự động hoá dây chuyền kiểm soát chất lượng (QC Workflow) khi có nhiều danh mục hồ sơ hoặc nhiều tầng cần kiểm tra. Quá trình kiểm tra lỗi đa bộ môn (Multidisciplinary Audit) thường đòi hỏi gọi LLM quét từng tọa độ không gian độc lập, Orchestrator giúp tiến hành hàng loạt nhằm tiết kiệm 90% thời gian chạy máy.

## Quy trình sử dụng (The Pipeline)

Quá trình chạy dựa vào **Nguồn sự thật duy nhất (Single Source of Truth)** là file `Coordination_Matrix.csv`.

**Tự động hóa với Discovery Engine:** Người dùng tuyệt đối không cần, và không nên lập file cấu hình ma trận này bằng tay (như điều bạn vừa trăn trở). Thay vào đó, **Luôn bắt đầu bằng Skill `ccba-ai-qc-discovery`**: Skill Discovery sẽ thực hiện vòng lặp quét nhận diện mọi tờ PDF trong hồ sơ, tự động lọc Text và khung tên bốc bóc ra `Coordination_Matrix.csv` tự động 100%.

### Cách gọi Command

Cụm Orchestrator nhận đường dẫn gốc của thư mục dự án (chứa `.md` Data Hub) để lấy file csv và ảnh:

```bash
python .agent/skills/ccba-ai-qc-batch-orchestrator/scripts/orchestrator.py --project-dir "D:/Path/To/Project" --matrix ".md/extracts/discovery/Project_Coordination_Matrix.csv" --concurrency 4
```

### Kiến trúc Hoạt động (Internal Logic)

1. **Parser Module:** Đọc cột `NormalizedLevel` và các nhóm `Sheet` / `Title` bên trong file `Coordination_Matrix.csv`.
2. **Missing Document Handler:** Nếu một cấu kiện thiếu sheet (như file CSV trả về rỗng), hoặc không tìm thấy trang thực tế thì sinh ra 1 khung ảnh trắng `blank.png`.
3. **Async Batcher:** Quản lý hàng chờ (Task Queue). Tạo và bắn nhiều tác vụ Quad-View (L01, L02, L03...) song song lên API LiteLLM.
4. **Integration Handoff:** Pass dữ liệu API JSON Output về ngược lại cho `IDOPReporter` để sinh thành báo cáo văn bản Markdown/Docx hoàn chỉnh.
