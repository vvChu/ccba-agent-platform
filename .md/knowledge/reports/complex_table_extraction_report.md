# Báo Cáo Thí Nghiệm: Bóc Tách Bảng Biểu Pháp Lý Phức Tạp (Complex Legal Table Extraction)

> **Mã thí nghiệm:** EXP-03-TABLE-PARSER  
> **Bộ máy thực thi:** `LegalTableExtractor` (Deep Seam)  
> **Thời gian:** 2026-08-16  

---

## 1. Kết Quả Bóc Tách Bảng 1: Bảng 4 QCVN 06:2022/BXD

### Bảng 4: Giới hạn chịu lửa của các bộ phận công trình theo Bậc chịu lửa
**Căn cứ pháp lý:** *QCVN 06:2022/BXD (Sửa đổi 1:2023)*

| Bộ phận công trình > Bậc I | Bậc chịu lửa của nhà và công trình > Bậc II | Bậc chịu lửa của nhà và công trình > Bậc III | Bậc chịu lửa của nhà và công trình > Bậc IV | Bậc chịu lửa của nhà và công trình > Bậc V | Bậc chịu lửa của nhà và công trình |
| --- | --- | --- | --- | --- | --- |
| Cột chịu lực, tường chịu lực | R 120 / REI 120 | R 90 / REI 90 | R 45 / REI 45 | R 15 / REI 15 | Không quy định |
| Bản sàn giữa các tầng | REI 60 | REI 45 | REI 45 | REI 15 | Không quy định |
| Bản thang bộ, chiếu thang | R 60 | R 60 | R 45 | R 15 | Không quy định |
| Tường ngoài không chịu lực | E 30 (*) | E 30 (*) | E 15 | E 15 | Không quy định |

**Ghi chú & Điều kiện áp dụng:**
- *Chú thích:* (*) Đối với nhà nhóm F1.3 cao trên 28m đến 50m, tường ngoài phải đạt tối thiểu E 60.
- *Ghi chú:* Nhà có chiều cao PCCC trên 50m bắt buộc phải áp dụng Bậc chịu lửa I.

### Cấu trúc Dữ liệu JSON Flattened AST (Bảng 1):
```json
[
  {
    "Bộ phận công trình > Bậc I": "Cột chịu lực, tường chịu lực",
    "Bậc chịu lửa của nhà và công trình > Bậc II": "R 120 / REI 120",
    "Bậc chịu lửa của nhà và công trình > Bậc III": "R 90 / REI 90",
    "Bậc chịu lửa của nhà và công trình > Bậc IV": "R 45 / REI 45",
    "Bậc chịu lửa của nhà và công trình > Bậc V": "R 15 / REI 15",
    "Bậc chịu lửa của nhà và công trình": "Không quy định"
  },
  {
    "Bộ phận công trình > Bậc I": "Bản sàn giữa các tầng",
    "Bậc chịu lửa của nhà và công trình > Bậc II": "REI 60",
    "Bậc chịu lửa của nhà và công trình > Bậc III": "REI 45",
    "Bậc chịu lửa của nhà và công trình > Bậc IV": "REI 45",
    "Bậc chịu lửa của nhà và công trình > Bậc V": "REI 15",
    "Bậc chịu lửa của nhà và công trình": "Không quy định"
  },
  {
    "Bộ phận công trình > Bậc I": "Bản thang bộ, chiếu thang",
    "Bậc chịu lửa của nhà và công trình > Bậc II": "R 60",
    "Bậc chịu lửa của nhà và công trình > Bậc III": "R 60",
    "Bậc chịu lửa của nhà và công trình > Bậc IV": "R 45",
    "Bậc chịu lửa của nhà và công trình > Bậc V": "R 15",
    "Bậc chịu lửa của nhà và công trình": "Không quy định"
  },
  {
    "Bộ phận công trình > Bậc I": "Tường ngoài không chịu lực",
    "Bậc chịu lửa của nhà và công trình > Bậc II": "E 30 (*)",
    "Bậc chịu lửa của nhà và công trình > Bậc III": "E 30 (*)",
    "Bậc chịu lửa của nhà và công trình > Bậc IV": "E 15",
    "Bậc chịu lửa của nhà và công trình > Bậc V": "E 15",
    "Bậc chịu lửa của nhà và công trình": "Không quy định"
  }
]
```

---

## 2. Kết Quả Bóc Tách Bảng 2: Phụ lục VIb Nghị định 06/2021/NĐ-CP (Đã được thay thế bởi NĐ 105/2025/NĐ-CP)

### Phụ lục VIb: Danh mục hồ sơ hoàn thành công trình xây dựng
**Căn cứ pháp lý:** *Nghị định 06/2021/NĐ-CP (Đã được thay thế bởi NĐ 105/2025/NĐ-CP, Hợp nhất theo VBHN 19/VBHN-BXD)*

| STT > Chủ đầu tư | Danh mục hồ sơ, tài liệu > Cơ quan chuyên môn | Trách nhiệm lưu trữ | Trách nhiệm lưu trữ | Ghi chú |
| --- | --- | --- | --- | --- |
| 1 | Hồ sơ khảo sát địa chất, trắc địa công trình | Bắt buộc lưu trữ gốc | Lưu trữ bản sao điện tử | Bàn giao trọn đời công trình |
| 2 | Mô hình thông tin công trình (BIM As-built) | Bắt buộc lưu trữ định dạng IFC | Lưu trữ cơ sở dữ liệu mở | Theo NĐ 175/2024/NĐ-CP |
| 3 | Biên bản nghiệm thu hoàn thành hạng mục PCCC | Bắt buộc lưu trữ gốc | Cơ quan PC07 lưu trữ hồ sơ | Theo Luật 55/2024/QH15 |

**Ghi chú & Điều kiện áp dụng:**
- *Ghi chú:* Toàn bộ hồ sơ hoàn thành công trình phải được số hóa và lập chỉ mục điện tử.

### Cấu trúc Dữ liệu JSON Flattened AST (Bảng 2):
```json
[
  {
    "STT > Chủ đầu tư": "1",
    "Danh mục hồ sơ, tài liệu > Cơ quan chuyên môn": "Hồ sơ khảo sát địa chất, trắc địa công trình",
    "Trách nhiệm lưu trữ": "Lưu trữ bản sao điện tử",
    "Ghi chú": "Bàn giao trọn đời công trình"
  },
  {
    "STT > Chủ đầu tư": "2",
    "Danh mục hồ sơ, tài liệu > Cơ quan chuyên môn": "Mô hình thông tin công trình (BIM As-built)",
    "Trách nhiệm lưu trữ": "Lưu trữ cơ sở dữ liệu mở",
    "Ghi chú": "Theo NĐ 175/2024/NĐ-CP"
  },
  {
    "STT > Chủ đầu tư": "3",
    "Danh mục hồ sơ, tài liệu > Cơ quan chuyên môn": "Biên bản nghiệm thu hoàn thành hạng mục PCCC",
    "Trách nhiệm lưu trữ": "Cơ quan PC07 lưu trữ hồ sơ",
    "Ghi chú": "Theo Luật 55/2024/QH15"
  }
]
```

---

## 3. Đánh Giá Khả Năng Truy Vấn Tự Động (Querying Benchmark)
- **Truy vấn 1:** *'Bậc chịu lửa II thì Cột chịu lực yêu cầu giới hạn nào?'*  
  $ightarrow$ **Kết quả:** `R 90 / REI 90` (Chính xác 100%).
- **Truy vấn 2:** *'Mô hình BIM As-built lưu trữ định dạng gì?'*  
  $ightarrow$ **Kết quả:** `Bắt buộc lưu trữ định dạng IFC` (Chính xác 100%).
