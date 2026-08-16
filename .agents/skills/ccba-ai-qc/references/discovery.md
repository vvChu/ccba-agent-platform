# 📑 Progressive Reference: Pha 1 — Discovery & Lập Ma Trận Phối Hợp

> Thuộc Master Skill [`ccba-ai-qc`](../SKILL.md).

Pha Discovery tự động phân tích cấu trúc của bộ hồ sơ bản vẽ thiết kế, trích xuất mã bản vẽ (SheetNo) và phân loại theo tầng (Level) hoặc khu vực (Zone) để lập Ma trận Phối hợp (`Coordination_Matrix.csv`).

---

## 1. Tiêu Chí Hoàn Thành (Completion Criteria)
- [x] Đã quét qua danh mục bản vẽ và tạo thành công tệp tin ma trận phối hợp tại đường dẫn:
  `[target_project]/.md/extracts/discovery/Coordination_Matrix.csv`
- [x] Tệp tin `Coordination_Matrix.csv` không rỗng và chứa đầy đủ các cột dữ liệu tối thiểu: `Level`, `NormalizedLevel`, `ArchitecturalSheet`, `StructuralSheet`, `MEPSheet`, `FireProtectionSheet`.

---

## 2. Hướng Dẫn Vận Hành Chi Tiết

### A. Quét tìm mục lục (TOC Scanning)
Ưu tiên đọc và phân tích 10 trang đầu của tệp PDF hồ sơ để tìm mục lục bản vẽ trước khi thực hiện cào dữ liệu toàn bộ tệp.

### B. Xử lý PDF dạng quét (Scanned PDF)
NẾU bản vẽ ở dạng scan không có text layer $\rightarrow$ Kích hoạt chế độ OCR trên AI Gateway để nhận diện ký tự.

### C. Lệnh chạy Độc lập
Khi cần kiểm thử độc lập module Discovery Engine:
```powershell
python .agents/skills/ccba-ai-qc/scripts/discovery_engine.py --target "[target_project]"
```
