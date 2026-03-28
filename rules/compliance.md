# CCBA Legal Compliance Rules

> Quy tắc đảm bảo tuân thủ pháp luật khi Agent xử lý nội dung VBPL.

## Nguyên tắc cốt lõi

1. **AI là trợ lý, không phải chuyên gia pháp lý** — Mọi output liên quan VBPL cần review bởi người có chuyên môn
2. **Trích dẫn chính xác** — Không diễn giải sai hoặc sáng tạo nội dung pháp luật
3. **Phân biệt rõ ràng** — Draft vs Enacted vs Effective

## Trạng thái VBPL

| Status | Ý nghĩa | Agent được phép |
|--------|---------|---------------|
| `draft` | Dự thảo, chưa ban hành | ⚠️ Phân tích, nhưng phải ghi rõ "DỰ THẢO" |
| `enacted` | Đã thông qua, chưa có hiệu lực | ✅ Phân tích, ghi rõ ngày hiệu lực |
| `current` | Đang có hiệu lực | ✅ Áp dụng bình thường |
| `superseded` | Đã bị thay thế | ⚠️ Chỉ tham chiếu lịch sử, ghi rõ "HẾT HIỆU LỰC" |

## Quy tắc khi tạo nội dung

### Checklist hồ sơ hoàn thành
- Dựa trên VBPL có hiệu lực (status: current)
- Nếu có VBPL mới sắp có hiệu lực → tạo 2 phiên bản song song
- Luôn ghi rõ căn cứ pháp lý (Điều, Khoản, NĐ)

### Bảng so sánh VBPL
- Cột "Cũ" và "Mới" phải trích dẫn nguyên văn hoặc ghi rõ "tóm tắt"
- Đánh giá mức tác động bắt buộc kèm lý giải

### Công văn / Thư kỹ thuật
- Phần căn cứ pháp lý phải liệt kê đầy đủ văn bản
- Không tham chiếu dự thảo để làm căn cứ chính thức

## Nguồn tin cậy

| Ưu tiên | Nguồn | URL |
|---------|-------|-----|
| 1 | Cổng TTĐT Bộ Xây dựng | moc.gov.vn |
| 2 | Cổng TTĐT Chính phủ | vanban.chinhphu.vn |
| 3 | Hệ thống VBPL Quốc gia | vbpl.vn |
| 4 | Local registry | `.agent/skills/legal-document-tracker/registry/legal_registry.yaml` |
| 5 | Thư viện Pháp luật (tham khảo) | thuvienphapluat.vn |

## Giai đoạn chuyển tiếp (đến 01/07/2026)

> [!WARNING]
> Từ nay đến 01/07/2026, hệ thống VBPL đang trong giai đoạn chuyển tiếp:
> - Luật XD 2014 → Luật XD 2025
> - NĐ 06/2021 → NĐ QLCL 2026 (đang dự thảo)
> 
> Agent PHẢI ghi rõ: "Áp dụng theo VBPL hiện hành đến 30/06/2026" hoặc
> "Theo dự thảo NĐ QLCL 2026 (chưa ban hành chính thức)".
