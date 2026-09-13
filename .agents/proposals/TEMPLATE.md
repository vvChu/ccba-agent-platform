---
proposal_id: "YYYY-MM-DD_short-kebab-name"
type: "skills" # skills | rules | packages | workflows | schema
name: "short-kebab-name"
status: "proposed" # proposed | under_review | merged | rejected
priority: "Trung bình" # Khẩn cấp | Cao | Trung bình | Thấp
proposed_by_project: "example-spoke-project"
proposed_by_archetype: "specialized_extension" # specialized_extension | project_delivery | knowledge_corpus
proposed_date: "2026-09-13"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Tất cả Spokes"
---

# RFC Proposal: [Tiêu Đề Đề Bạt Sáng Kiến Spoke Lên Hub]

- **Tác giả đề xuất:** Kỹ sư / Agent đại diện Spoke (`[spoke_id]`)
- **Ngày lập:** YYYY-MM-DD
- **Trạng thái:** Đang đề xuất (Proposed)
- **Căn cứ pháp lý nền tảng:** [ADR-0045](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0045-hub-proposal-ingestion-governance.md), [ADR-0046](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0046-personal-sandbox-lifecycle-and-charter-2026-alignment.md), Quy chế Tổ chức CCBA 2026.

---

### 1. Bối cảnh & Động lực Thực tế tại Spoke (Context & Real-world Motivation)
Mô tả cụ thể bài toán kỹ thuật hoặc nghiệp vụ tư vấn xây dựng tại dự án Spoke đã dẫn tới việc phát triển sáng kiến/kỹ năng này:
1. **Nỗi đau thực tế (Pain point):** Vấn đề gặp phải khi xử lý hồ sơ, bản vẽ, thẩm tra hoặc điều phối.
2. **Quá trình ươm tạo tại Spoke:** Thống kê số lần sử dụng thực tế (từ telemetry: số lượt gọi, token tiết kiệm được).
3. **Giá trị khi phổ biến lên Hub:** Lý do công cụ/kỹ năng này nên trở thành năng lực dùng chung cho toàn bộ các Spokes khác thay vì chỉ giữ ở cấp độ cục bộ.

---

### 2. Đánh Giá Giá Trị × Rủi Ro × KISS (Evaluation Matrix)

| Tiêu Chí | Đánh Giá Cụ Thể | Ghi Chú / Bằng Chứng |
| :--- | :--- | :--- |
| **Giá trị Nghiệp vụ (Value)** | Cao / Rất cao | Giúp rút ngắn thời gian thẩm tra / tự động hóa khâu lặp lại |
| **Độ Phức tạp (Complexity)** | Thấp / Vừa phải | Tuân thủ nguyên tắc KISS, không tạo thêm tầng trừu tượng thừa |
| **Rủi ro Rò rỉ (Risk)** | Đã triệt tiêu 100% | Đã chạy kiểm tra qua `check_spoke_leakage.py` |
| **Bảo tồn Nghiệp vụ (Charter)** | Tuân thủ 100% | Không ảnh hưởng đến các kỹ năng chu kỳ dài |

---

### 3. Thiết Kế Deep Seams & Đặc Tả Kỹ Thuật tại Hub (Technical Specification)

1. **Vị trí tích hợp tại Hub Monorepo:**
   - Thư mục đích: `packages/<package-name>/src/<package_name>/` hoặc `.agents/skills/<skill-name>/`
   - Public Seam export: Hàm / Lớp giao diện công khai tại `__init__.py`.
2. **Giao diện công khai (Public Interface):**
   ```python
   def example_innovation_function(param_a: str, param_b: int) -> dict[str, Any]:
       """Docstring Google style mô tả rõ ràng chức năng."""
       ...
   ```
3. **Ngân sách hướng dẫn & Phân tầng (ADR-0030, ADR-0057):**
   - Điểm GPI dự kiến: `>= 12.0` (nếu là Standalone Kernel Skill) hoặc `< 12.0` (nếu là Progressive Reference).
   - Dung lượng token: Giới hạn $\le 300$ tokens trong tệp `SKILL.md` chính, chi tiết chuyển vào `references/`.

---

### 4. Quy Trình Thẩm Định 2 Cổng (Hybrid Ingestion Gates - ADR-0045)

Đề xuất này bắt buộc phải vượt qua 2 cổng kiểm tra trước khi được chấp thuận:
1. **Cổng Cứng Tự Động (Hard Gate - CI Automation):**
   - Lệnh kiểm tra: `python scripts/governance/check_spoke_leakage.py`
   - Tiêu chí: Không có đường dẫn tuyệt đối Windows, không chứa thư mục cấm (`.md/teach/`, `.tmp/`), frontmatter hợp lệ 100%.
2. **Cổng Mềm Tương Tác (Soft Gate - QC Level 5 Supervised Review):**
   - Workflow thẩm định: `/ccba-review-proposal` được chủ trì bởi Maintainer có thẩm quyền QC Level 5 (theo Điều 13 Quy chế CCBA 2026).
   - Kiểm tra mã nguồn, chạy bộ test cô lập và đối soát kiến trúc trước khi phê duyệt `gh pr merge`.

---

### 5. Cam Kết Bất Biến về Bảo Tồn Kỹ Năng (Constitutional Invariant)
- **Quy tắc cấm khai tử tự động (Zero-Usage Deprecation Ban):** Nền tảng Hub CCBA tôn trọng các kỹ năng chuyên ngành chu kỳ dài (nghiệm thu hoàn thành công trình 6-12 tháng mới sử dụng một lần). Tuyệt đối không cho phép bất kỳ thuật toán telemetry nào tự ý xóa bỏ hay hạ cấp kỹ năng chỉ vì chỉ số sử dụng bằng 0 trong ngắn hạn.
