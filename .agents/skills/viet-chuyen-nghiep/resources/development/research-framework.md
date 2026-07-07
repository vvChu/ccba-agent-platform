# Nghiên Cứu Phong Cách Viết — Framework Thực Thi

**Module:** Công cụ Ban Phát Triển
**Mục đích:** Quy trình chuẩn hóa để thu thập, phân tích, và tích hợp phong cách viết từ báo chí vào skill.

---

## Hướng Dẫn Sử Dụng

```
Mỗi conversation:
1. Đọc file này để nắm quy trình
2. Đọc file kết quả hiện tại (research-results.md) để biết đã làm đến đâu
3. Chọn 3-5 bài tiếp theo trong danh sách chưa phân tích
4. Đọc bài → Điền bảng phân tích → Ghi kết quả vào research-results.md
5. Sau mỗi batch: cập nhật bảng tổng hợp pattern ở cuối file
```

---

## Bước 1: Chọn Bài

Từ danh sách nguồn, chọn bài đạt **3/4 tiêu chí**:

- ✅ Có lập luận (không phải tin thuần túy)
- ✅ Tương tác cao (nhiều comment/share)
- ✅ Đại diện thể loại (phóng sự, bình luận, phân tích...)
- ✅ Viết tốt (cấu trúc rõ, kết ấn tượng)

---

## Bước 2: Phân Tích (Template)

Copy template sau cho MỖI bài:

```markdown
### [Tên bài] — [Nguồn]

**URL:** [link]
**Thể loại:** [phóng sự / bình luận / phân tích / tiểu luận / giải thích / tin tức]
**Lĩnh vực:** [tổng hợp / pháp luật / kinh tế / giáo dục / KHCN / sức khỏe / xã hội / văn hóa]

#### Staged Assessment
- L1 Phong cách đặc biệt: [Có/Không]
- L2 Kỹ thuật nghệ thuật: [Có/Một phần/Không]
- L3 Tầng nghĩa ẩn: [Có/Không]
- L4 Mức độ phức tạp: [Cao/Trung bình/Thấp]

#### Cấu trúc
- **Hook:** [Loại hook + trích dẫn câu đầu]
- **Chuyển tiếp:** [Từ nối đặc trưng]
- **Nhịp đoạn:** [Mô tả pattern biến thiên]
- **Kết bài:** [Loại closing + trích dẫn]

#### Kỹ thuật phát hiện
| Kỹ thuật | Evidence (trích dẫn) | Đã có trong skill? |
|----------|---------------------|-------------------|
| [tên] | "[trích]" | Có/Không |

#### Style DNA
- Đặc điểm 1: [tên] — "[evidence]"
- Đặc điểm 2: [tên] — "[evidence]"

#### Kết luận
- Pattern mới cần bổ sung: [có/không] → [mô tả]
- Bài mẫu đáng lưu: [có/không]
```

---

## Bước 3: Tổng Hợp Pattern (Cuối Mỗi Batch)

Sau khi phân tích xong 3-5 bài, cập nhật bảng tổng hợp:

```markdown
## Bảng Tổng Hợp Pattern

| # | Pattern | Phát hiện từ | Thể loại | Đã có trong skill? | Đề xuất |
|---|---------|-------------|----------|-------------------|---------|
| 1 | [tên] | [bài nào] | [thể loại] | [Có/Không] | [thêm vào file nào] |
```

---

## Bước 4: Tích Hợp Vào Skill (Sau Khi Đủ Data)

Khi đã phân tích đủ ~20 bài trở lên:

```
1. Đọc bảng tổng hợp pattern
2. Lọc pattern mới (chưa có trong skill)
3. Phân loại: thuộc ban nào? (style/, quality/, content/)
4. Viết format chuẩn nhân viên (header + quy tắc + checklist)
5. Cập nhật lead file → bảng nhân sự
6. Cập nhật SKILL.md nếu cần thêm dispatch mới
7. Ghi changelog vào upgrade.md
```

---

## Danh Sách Nguồn — Tracking

### Batch 1: Tổng hợp + Pháp luật + Kinh tế

| # | Nguồn | Bài | Trạng thái |
|---|-------|-----|-----------|
| 1 | VnExpress Ý kiến | (chưa chọn) | ⬜ |
| 2 | VnExpress Ý kiến | (chưa chọn) | ⬜ |
| 3 | Tuổi Trẻ Phóng sự | (chưa chọn) | ⬜ |
| 4 | Tuổi Trẻ Cuối tuần | (chưa chọn) | ⬜ |
| 5 | Báo Pháp Luật | (chưa chọn) | ⬜ |
| 6 | Báo Pháp Luật | (chưa chọn) | ⬜ |
| 7 | CafeF | (chưa chọn) | ⬜ |
| 8 | VnEconomy | (chưa chọn) | ⬜ |

### Batch 2: Giáo dục + KHCN + Sức khỏe + Xã hội
| # | Nguồn | Bài | Trạng thái |
|---|-------|-----|-----------|
| 9 | Dân Trí | (chưa chọn) | ⬜ |
| 10 | Tia Sáng | (chưa chọn) | ⬜ |
| 11 | Sức Khỏe & Đời Sống | (chưa chọn) | ⬜ |
| 12 | Lao Động | (chưa chọn) | ⬜ |
| 13 | Người Lao Động | (chưa chọn) | ⬜ |
| 14 | VietnamNet | (chưa chọn) | ⬜ |
| 15 | Giáo dục & Thời đại | (chưa chọn) | ⬜ |

### Batch 3: Văn hóa + Quốc tế + Content hiện đại
| # | Nguồn | Bài | Trạng thái |
|---|-------|-----|-----------|
| 16 | Nhân Dân Cuối Tuần | (chưa chọn) | ⬜ |
| 17 | Thế Giới & Việt Nam | (chưa chọn) | ⬜ |
| 18 | BBC Vietnamese | (chưa chọn) | ⬜ |
| 19 | Vietcetera | (chưa chọn) | ⬜ |
| 20 | Spiderum | (chưa chọn) | ⬜ |

### Batch 4: Quốc tế
| # | Nguồn | Bài | Trạng thái |
|---|-------|-----|-----------|
| 21 | The Atlantic | (chưa chọn) | ⬜ |
| 22 | The Economist | (chưa chọn) | ⬜ |
| 23 | HBR | (chưa chọn) | ⬜ |
| 24 | Wired | (chưa chọn) | ⬜ |
| 25 | Paul Graham | (chưa chọn) | ⬜ |
| 26 | Morgan Housel | (chưa chọn) | ⬜ |

Ký hiệu: ⬜ Chưa chọn | 🔲 Đã chọn | ✅ Đã phân tích
