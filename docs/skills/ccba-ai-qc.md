# ccba-ai-qc

> **Mô tả ngắn**: Master Deep Skill điều phối toàn trình thẩm tra chất lượng thiết kế đa bộ môn (Discovery, Quad-View Vision, Heat Map Report) qua Deep Seam QCAuditPipeline.

---

## 1. Action Header & Kích Hoạt Nhanh

### Cú pháp Lệnh (Slash Command)
```bash
/ccba-ai-qc
```

### Đồng bộ sang Phân vùng Spoke
```bash
python scripts/spoke/sync_spoke.py --skills ccba-ai-qc
```

### Thông Số & Huy Hiệu Kỹ Năng
| Thuộc tính | Chi tiết |
| :--- | :--- |
| **Cổng Điều Hướng (Portal)** | 📐 BIGBIM & Thẩm tra AI-QC |
| **Phân Tầng Kiến Trúc (Tier)** | `Tier 3 (Orchestrator)` |
| **Gói Bundle** | `_qc` |
| **Phương Thức Triệu Hồi** | Song song (Slash Command & Model Trigger) |

---

## 2. Mục Đích & Rào Chắn Bất Biến (Defining Constraints)

### Mục Đích Hoạt Động
Master Deep Skill điều phối toàn trình thẩm tra chất lượng thiết kế đa bộ môn (Discovery, Quad-View Vision, Heat Map Report) qua Deep Seam QCAuditPipeline.

Kỹ năng này hoạt động như một giao diện nhận thức chuẩn mực cho AI Agent và kỹ sư, đảm bảo tính tất định và khả năng tái lập trong toàn bộ vòng đời dự án.

### Rào Chắn Bất Biến (Platform Invariants)
1. **Bảo Vệ Ngân Sách Ngữ Cảnh (ADR-0030)**: Tệp `SKILL.md` của kỹ năng chỉ chứa hướng dẫn tác nghiệp cốt lõi, không chứa văn xuôi tiếp thị hay nội dung dư thừa gây tràn Context Window.
2. **Khóa Cứng Kỷ Luật Hoàn Thành (ADR-0058)**: Agent tuyệt đối không được báo cáo hoàn thành nhiệm vụ nếu bất kỳ lệnh kiểm thử tự động nào trả về mã lỗi khác 0 (`exit code != 0`).
3. **Cô Lập Vùng Ghi (Artifact Scope)**: Mọi tệp thành phẩm sinh ra phải nằm trong thư mục quy định của dự án, không làm ô nhiễm thư mục gốc (Project Root).
4. **Bảo Mật Bí Mật (Zero Secret Leaks)**: Tuyệt đối không hardcode API Keys, mật khẩu hoặc khóa chứng thực vào bất kỳ tệp tài liệu hay mã nguồn nào.

---

## 3. Khi Nào Sử Dụng & Kích Hoạt (Triggers)

### Từ Khóa Kích Hoạt (Triggers)
- `qc`
- `audit`
- `quad-view`
- `discovery`
- `reporter`
- `collision-check`
- `qcauditpipeline`
- `ccba-ai-qc`
- `qc pipeline`
- `multi-discipline audit`
- `heat map report`

### Ngữ Cảnh Khuyến Nghị Triệu Hồi
- Khi cần thực thi nghiệp vụ liên quan trực tiếp đến vai trò: Master Orchestrator thẩm tra chất lượng thiết kế qua Deep Seam QCAuditPipeline.
- Trong chuỗi phát triển khi nhận tín hiệu bàn giao từ: **Mô hình thiết kế đa bộ môn (Kiến trúc, Kết cấu, MEP)**

### Khi Nào KHÔNG Nên Dùng (Anti-patterns)
- Không dùng nếu cần tư vấn định hướng ban đầu: hãy gọi `/ccba-ask`.
- Không tự ý sửa đổi thủ công định nghĩa kỹ năng nếu gặp lỗi: hãy dùng `/ccba-skill-repair`.

---

## 4. Vị Trí Trong Chuỗi Giá Trị (The Pipeline Trail)

Kỹ năng `ccba-ai-qc` giữ vị trí then chốt trong chuỗi giá trị tích hợp của nền tảng:

```text
[ Mô hình thiết kế đa bộ môn (Kiến trúc, Kết cấu, MEP) ]
          │
          ▼
    >>> [ ccba-ai-qc ] <<<  (Master Orchestrator thẩm tra chất lượng thiết kế qua Deep Seam QCAuditPipeline.)
          │
          ▼
[ Heat Map Report / Nghiệm thu thiết kế ]
```

- **Đầu vào (Upstream)**: Nhận bối cảnh từ `Mô hình thiết kế đa bộ môn (Kiến trúc, Kết cấu, MEP)`.
- **Thực thi (In-flight)**: Áp dụng các quy tắc kỹ thuật và công cụ tự động hóa để sản sinh kết quả chuẩn mực.
- **Đầu ra & Bàn giao (Downstream)**: Chuyển giao thành phẩm sạch sẽ sang `Heat Map Report / Nghiệm thu thiết kế`.

---

## 5. Khóa Cứng Kỷ Luật & Tiêu Chí Hoàn Thành (ADR-0058)

### Lệnh Kiểm Thử Tự Động Bắt Buộc
Mọi thay đổi liên quan đến kỹ năng này bắt buộc phải vượt qua toàn bộ các kiểm thử tự động sau:
```bash
python -m ccba_harness verify-patch --preset skill
python scripts/validate_skills.py --file .agents/skills/ccba-ai-qc/SKILL.md --enforce-gpi
```

### Danh Mục Kiểm Thức Hoàn Thành (Definition of Done - DoD)
- [ ] Lệnh kiểm chứng `verify-patch` trả về mã thoát `exit code 0`.
- [ ] Toàn bộ thuộc tính frontmatter trong `SKILL.md` đồng bộ 100% với `catalog.yaml`.
- [ ] Không có liên kết nội bộ bị đứt gãy hoặc tham chiếu file không tồn tại.
- [ ] Thành phẩm sinh ra nằm gọn trong thư mục đích, tuân thủ nguyên tắc KISS.
