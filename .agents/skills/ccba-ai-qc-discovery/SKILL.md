---
name: ccba-ai-qc-discovery
description: Tự động quét hồ sơ PDF, nhận diện cấu trúc bản vẽ, tìm mục lục và xây dựng Ma trận Phối hợp (Coordination Matrix).
applies_to:
  - "Thẩm tra thiết kế"
  - "Thiết kế"
  - "Kiểm định"
bundle: "_qc"
---

# CCBA AI QC Discovery Skill

Skill này tự động phân tích cấu trúc của bộ hồ sơ bản vẽ thiết kế, trích xuất mã bản vẽ (SheetNo) và phân loại theo tầng (Level) hoặc khu vực (Zone) để lập bản đồ dữ liệu cho dự án.

---

## Tiêu chí hoàn thành (Completion Criteria)

Tác vụ Discovery được coi là hoàn thành thành công khi và chỉ khi:
- [ ] Đã quét qua danh mục bản vẽ và tạo thành công tệp tin ma trận phối hợp tại đường dẫn:
  `[target_project]/.md/extracts/discovery/Coordination_Matrix.csv`
- [ ] Tệp tin `Coordination_Matrix.csv` không rỗng và chứa đầy đủ các cột dữ liệu tối thiểu: `Level`, `NormalizedLevel`, `ArchitecturalSheet`, `StructuralSheet`, `MEPSheet`, `FireProtectionSheet`.

---

## Hướng dẫn Vận hành

### 1. Quét tìm mục lục
Luôn ưu tiên đọc và phân tích 10 trang đầu của tệp PDF hồ sơ để tìm mục lục bản vẽ trước khi thực hiện cào dữ liệu toàn bộ tệp.

### 2. Xử lý PDF dạng quét (Scanned PDF)
NẾU bản vẽ ở dạng scan không có text layer $\rightarrow$ Bắt buộc kích hoạt chế độ `ocr-primary` trên AI Gateway để nhận diện chữ.

### 3. Công cụ thực thi
Chạy tập lệnh cào dữ liệu:
```bash
python .agents/skills/ccba-ai-qc-discovery/scripts/discovery_engine.py --target "[target_project]"
```
