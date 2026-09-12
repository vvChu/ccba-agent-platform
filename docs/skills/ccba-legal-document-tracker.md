# ccba-legal-document-tracker

> **Mô tả ngắn**: Theo dõi, so sánh và phân tích các VBPL xây dựng Việt Nam với VBHNEngine và Registry.

---

## 1. Action Header & Kích Hoạt Nhanh

### Cú pháp Lệnh (Slash Command)
```bash
/ccba-legal-document-tracker
```

### Đồng bộ sang Phân vùng Spoke
```bash
python scripts/spoke/sync_spoke.py --skills ccba-legal-document-tracker
```

### Thông Số & Huy Hiệu Kỹ Năng
| Thuộc tính | Chi tiết |
| :--- | :--- |
| **Cổng Điều Hướng (Portal)** | ⚖️ Pháp lý Xây dựng & Tự động hóa Văn phòng |
| **Phân Tầng Kiến Trúc (Tier)** | `Tier 2B (Kernel)` |
| **Gói Bundle** | `_consulting` |
| **Phương Thức Triệu Hồi** | Song song (Slash Command & Model Trigger) |
| **Điểm Đánh Giá GPI (ADR-0057)** | `S=4.0 | K=3.0 | A=4.0 | P=1.0 (Tổng: 12.0)` |

---

## 2. Mục Đích & Rào Chắn Bất Biến (Defining Constraints)

### Mục Đích Hoạt Động
Theo dõi, so sánh và phân tích các VBPL xây dựng Việt Nam với VBHNEngine và Registry.

Kỹ năng này hoạt động như một giao diện nhận thức chuẩn mực cho AI Agent và kỹ sư, đảm bảo tính tất định và khả năng tái lập trong toàn bộ vòng đời dự án.

### Rào Chắn Bất Biến (Platform Invariants)
1. **Bảo Vệ Ngân Sách Ngữ Cảnh (ADR-0030)**: Tệp `SKILL.md` của kỹ năng chỉ chứa hướng dẫn tác nghiệp cốt lõi, không chứa văn xuôi tiếp thị hay nội dung dư thừa gây tràn Context Window.
2. **Khóa Cứng Kỷ Luật Hoàn Thành (ADR-0058)**: Agent tuyệt đối không được báo cáo hoàn thành nhiệm vụ nếu bất kỳ lệnh kiểm thử tự động nào trả về mã lỗi khác 0 (`exit code != 0`).
3. **Cô Lập Vùng Ghi (Artifact Scope)**: Mọi tệp thành phẩm sinh ra phải nằm trong thư mục quy định của dự án, không làm ô nhiễm thư mục gốc (Project Root).
4. **Bảo Mật Bí Mật (Zero Secret Leaks)**: Tuyệt đối không hardcode API Keys, mật khẩu hoặc khóa chứng thực vào bất kỳ tệp tài liệu hay mã nguồn nào.

---

## 3. Khi Nào Sử Dụng & Kích Hoạt (Triggers)

### Từ Khóa Kích Hoạt (Triggers)
- `VBPL`
- `pháp luật`
- `legal`
- `registry`
- `nghị định`
- `thông tư`
- `văn bản pháp luật`
- `luật xây dựng`
- `ccba-update-legal-registry`
- `update-legal-registry`

### Ngữ Cảnh Khuyến Nghị Triệu Hồi
- Khi cần thực thi nghiệp vụ liên quan trực tiếp đến vai trò: Theo dõi hiệu lực, so sánh văn bản sửa đổi bổ sung với VBHNEngine.
- Trong chuỗi phát triển khi nhận tín hiệu bàn giao từ: **Cơ sở dữ liệu văn bản pháp quy**

### Khi Nào KHÔNG Nên Dùng (Anti-patterns)
- Không dùng nếu cần tư vấn định hướng ban đầu: hãy gọi `/ccba-ask`.
- Không tự ý sửa đổi thủ công định nghĩa kỹ năng nếu gặp lỗi: hãy dùng `/ccba-skill-repair`.

---

## 4. Vị Trí Trong Chuỗi Giá Trị (The Pipeline Trail)

Kỹ năng `ccba-legal-document-tracker` giữ vị trí then chốt trong chuỗi giá trị tích hợp của nền tảng:

```text
[ Cơ sở dữ liệu văn bản pháp quy ]
          │
          ▼
    >>> [ ccba-legal-document-tracker ] <<<  (Theo dõi hiệu lực, so sánh văn bản sửa đổi bổ sung với VBHNEngine.)
          │
          ▼
[ ccba-legal-advisor / Cập nhật hiệu lực ]
```

- **Đầu vào (Upstream)**: Nhận bối cảnh từ `Cơ sở dữ liệu văn bản pháp quy`.
- **Thực thi (In-flight)**: Áp dụng các quy tắc kỹ thuật và công cụ tự động hóa để sản sinh kết quả chuẩn mực.
- **Đầu ra & Bàn giao (Downstream)**: Chuyển giao thành phẩm sạch sẽ sang `ccba-legal-advisor / Cập nhật hiệu lực`.

---

## 5. Khóa Cứng Kỷ Luật & Tiêu Chí Hoàn Thành (ADR-0058)

### Lệnh Kiểm Thử Tự Động Bắt Buộc
Mọi thay đổi liên quan đến kỹ năng này bắt buộc phải vượt qua toàn bộ các kiểm thử tự động sau:
```bash
python -m ccba_harness verify-patch --preset skill
python scripts/validate_skills.py --file .agents/skills/ccba-legal-document-tracker/SKILL.md --enforce-gpi
```

### Danh Mục Kiểm Thức Hoàn Thành (Definition of Done - DoD)
- [ ] Lệnh kiểm chứng `verify-patch` trả về mã thoát `exit code 0`.
- [ ] Toàn bộ thuộc tính frontmatter trong `SKILL.md` đồng bộ 100% với `catalog.yaml`.
- [ ] Không có liên kết nội bộ bị đứt gãy hoặc tham chiếu file không tồn tại.
- [ ] Thành phẩm sinh ra nằm gọn trong thư mục đích, tuân thủ nguyên tắc KISS.
