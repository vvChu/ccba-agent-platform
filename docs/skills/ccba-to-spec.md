# ccba-to-spec

> **Mô tả ngắn**: Turn the current conversation into a spec and publish it to the project issue tracker — no interview, just synthesis of what you've already discussed.

---

## 1. Action Header & Kích Hoạt Nhanh

### Cú pháp Lệnh (Slash Command)
```bash
/ccba-to-spec
```

### Đồng bộ sang Phân vùng Spoke
```bash
python scripts/spoke/sync_spoke.py --skills ccba-to-spec
```

### Thông Số & Huy Hiệu Kỹ Năng
| Thuộc tính | Chi tiết |
| :--- | :--- |
| **Cổng Điều Hướng (Portal)** | ⚙️ Kỹ nghệ Phần mềm & Đa Tác nhân |
| **Phân Tầng Kiến Trúc (Tier)** | `Tier 2B (Kernel)` |
| **Gói Bundle** | `_core` |
| **Phương Thức Triệu Hồi** | User-invoked (Chỉ lệnh Slash Command) |
| **Điểm Đánh Giá GPI (ADR-0057)** | `S=4.0 | K=2.0 | A=1.0 | P=1.0 (Tổng: 8.0)` |

---

## 2. Mục Đích & Rào Chắn Bất Biến (Defining Constraints)

### Mục Đích Hoạt Động
Turn the current conversation into a spec and publish it to the project issue tracker — no interview, just synthesis of what you've already discussed.

Kỹ năng này hoạt động như một giao diện nhận thức chuẩn mực cho AI Agent và kỹ sư, đảm bảo tính tất định và khả năng tái lập trong toàn bộ vòng đời dự án.

### Rào Chắn Bất Biến (Platform Invariants)
1. **Bảo Vệ Ngân Sách Ngữ Cảnh (ADR-0030)**: Tệp `SKILL.md` của kỹ năng chỉ chứa hướng dẫn tác nghiệp cốt lõi, không chứa văn xuôi tiếp thị hay nội dung dư thừa gây tràn Context Window.
2. **Khóa Cứng Kỷ Luật Hoàn Thành (ADR-0058)**: Agent tuyệt đối không được báo cáo hoàn thành nhiệm vụ nếu bất kỳ lệnh kiểm thử tự động nào trả về mã lỗi khác 0 (`exit code != 0`).
3. **Cô Lập Vùng Ghi (Artifact Scope)**: Mọi tệp thành phẩm sinh ra phải nằm trong thư mục quy định của dự án, không làm ô nhiễm thư mục gốc (Project Root).
4. **Bảo Mật Bí Mật (Zero Secret Leaks)**: Tuyệt đối không hardcode API Keys, mật khẩu hoặc khóa chứng thực vào bất kỳ tệp tài liệu hay mã nguồn nào.

---

## 3. Khi Nào Sử Dụng & Kích Hoạt (Triggers)

### Từ Khóa Kích Hoạt (Triggers)
- `ccba-to-spec`
- `spec`
- `soạn spec`
- `tạo spec`
- `đặc tả kỹ thuật`
- `ccba-to-tickets`
- `to-tickets`
- `ccba-to-questionnaire`
- `to-questionnaire`

### Ngữ Cảnh Khuyến Nghị Triệu Hồi
- Khi cần thực thi nghiệp vụ liên quan trực tiếp đến vai trò: Biến ý tưởng thành Đặc tả Kỹ thuật và bẻ ticket lát cắt dọc.
- Trong chuỗi phát triển khi nhận tín hiệu bàn giao từ: **ccba-grilling / CONTEXT.md**

### Khi Nào KHÔNG Nên Dùng (Anti-patterns)
- Không dùng nếu cần tư vấn định hướng ban đầu: hãy gọi `/ccba-ask`.
- Không tự ý sửa đổi thủ công định nghĩa kỹ năng nếu gặp lỗi: hãy dùng `/ccba-skill-repair`.

---

## 4. Vị Trí Trong Chuỗi Giá Trị (The Pipeline Trail)

Kỹ năng `ccba-to-spec` giữ vị trí then chốt trong chuỗi giá trị tích hợp của nền tảng:

```text
[ ccba-grilling / CONTEXT.md ]
          │
          ▼
    >>> [ ccba-to-spec ] <<<  (Biến ý tưởng thành Đặc tả Kỹ thuật và bẻ ticket lát cắt dọc.)
          │
          ▼
[ ccba-implement / ccba-tdd ]
```

- **Đầu vào (Upstream)**: Nhận bối cảnh từ `ccba-grilling / CONTEXT.md`.
- **Thực thi (In-flight)**: Áp dụng các quy tắc kỹ thuật và công cụ tự động hóa để sản sinh kết quả chuẩn mực.
- **Đầu ra & Bàn giao (Downstream)**: Chuyển giao thành phẩm sạch sẽ sang `ccba-implement / ccba-tdd`.

---

## 5. Khóa Cứng Kỷ Luật & Tiêu Chí Hoàn Thành (ADR-0058)

### Lệnh Kiểm Thử Tự Động Bắt Buộc
Mọi thay đổi liên quan đến kỹ năng này bắt buộc phải vượt qua toàn bộ các kiểm thử tự động sau:
```bash
python -m ccba_harness verify-patch --preset skill
python scripts/validate_skills.py --file .agents/skills/ccba-to-spec/SKILL.md --enforce-gpi
```

### Danh Mục Kiểm Thức Hoàn Thành (Definition of Done - DoD)
- [ ] Lệnh kiểm chứng `verify-patch` trả về mã thoát `exit code 0`.
- [ ] Toàn bộ thuộc tính frontmatter trong `SKILL.md` đồng bộ 100% với `catalog.yaml`.
- [ ] Không có liên kết nội bộ bị đứt gãy hoặc tham chiếu file không tồn tại.
- [ ] Thành phẩm sinh ra nằm gọn trong thư mục đích, tuân thủ nguyên tắc KISS.
