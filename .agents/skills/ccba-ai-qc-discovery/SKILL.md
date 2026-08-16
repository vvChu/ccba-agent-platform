---
name: ccba-ai-qc-discovery
description: Tự động quét hồ sơ PDF, nhận diện cấu trúc bản vẽ và lập Ma trận Phối hợp (Pha 1 của QCAuditPipeline).
applies_to:
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_qc"
---

# CCBA AI QC Discovery Skill

Skill này tự động phân tích cấu trúc của bộ hồ sơ bản vẽ thiết kế, trích xuất mã bản vẽ (SheetNo) và phân loại theo tầng (Level) hoặc khu vực (Zone) để lập Ma trận Phối hợp (`Coordination_Matrix.csv`). Đây là **Pha 1** trong Deep Seam **`QCAuditPipeline`** ([`packages/ccba-ai`](../../packages/ccba-ai)).

---

## Tiêu chí hoàn thành (Completion Criteria)

Tác vụ Discovery được coi là hoàn thành khi và chỉ khi:
- [ ] Đã quét qua danh mục bản vẽ và tạo thành công tệp tin ma trận phối hợp tại đường dẫn:
  `[target_project]/.md/extracts/discovery/Coordination_Matrix.csv`
- [ ] Tệp tin `Coordination_Matrix.csv` không rỗng và chứa đầy đủ các cột dữ liệu tối thiểu: `Level`, `NormalizedLevel`, `ArchitecturalSheet`, `StructuralSheet`, `MEPSheet`, `FireProtectionSheet`.

---

## Hướng dẫn Vận hành

### 1. Quét tìm mục lục
Ưu tiên đọc và phân tích 10 trang đầu của tệp PDF hồ sơ để tìm mục lục bản vẽ trước khi thực hiện cào dữ liệu toàn bộ tệp.

### 2. Xử lý PDF dạng quét (Scanned PDF)
NẾU bản vẽ ở dạng scan không có text layer $\rightarrow$ Kích hoạt chế độ OCR trên AI Gateway để nhận diện ký tự.

### 3. Tích hợp trong Pipeline & Thực thi Độc lập
Khi chạy trọn gói qua `QCAuditPipeline`, pha này tự động thực thi. Nếu cần chạy độc lập:
```bash
python .agents/skills/ccba-ai-qc-discovery/scripts/discovery_engine.py --target "[target_project]"
```
