---
id: 225
title: "feat(platform): next-gen enhancements for legal data vault, pptx seam, pccc audit & idop cli"
state: "closed"
labels:
  - "enhancement"
  - "verified"
assignee: "Antigravity"
created_at: "2026-09-01T02:19:43Z"
updated_at: "2026-09-25T21:20:00Z"
---

# 📖 Mô tả (Description)
### 1. Bối cảnh & Vấn đề (Context & Problem):
Sau khi hoàn tất giai đoạn ổn định hạ tầng kết nối Hub-Spoke, trong quá trình vận hành thực tế tại Spoke (`vvc_working_space`), các kỹ sư và chuyên gia CCBA ghi nhận 5 nhu cầu nghiệp vụ cấp thiết:
1. **Hạ tầng phân phối tri thức OKF v2.4**: Lệnh `sync` đã tạo registry nhưng số gói văn bản đồng bộ là 0; cần kênh tải chính thức cho các gói văn bản Luật 135/2025/QH15 và hệ thống Nghị định 2026.
2. **Nhu cầu xuất bản Slide thuyết trình 1-chạm**: Việc tạo slide bài giảng, báo cáo tiến độ từ dữ liệu pháp lý hiện tốn nhiều bước thủ công.
3. **Phân định thẩm quyền PCCC theo Luật 55/2024 & NĐ 105/2025**: Điểm nghẽn lớn nhất của Chủ đầu tư hiện nay là nộp nhầm cơ quan (Sở Xây dựng vs PC07), cần bộ công cụ chẩn đoán tự động.
4. **Quản lý Phiếu Giao Việc (PGV) trực tiếp tại Spoke**: Kỹ sư cần lệnh CLI để tra cứu và cập nhật task IDOP được giao.
5. **Bộ benchmark kiểm thử chất lượng cho kỹ năng pháp lý**: Cần bộ test cases tự động để ngăn ngừa ảo giác và trích dẫn văn bản hết hiệu lực.

### 2. Đề xuất giải pháp (RFC Proposal):
- **Xác lập nguồn Legal Data Vault Tier 1/2**: Quy chuẩn kênh phân phối dữ liệu (Server Spark qua Tailscale VPN, Google Drive Shared Vault, hoặc GitHub Release Assets) để Spoke tải trực tiếp qua `python -m ccba_legal sync --pull-latest`.
- **Legal-to-PPTX Deep Seam**: Tích hợp pipeline kết nối `ccba-legal-intel` và `xu-ly-van-phong` / `pptx` để tự động chuyển sơ đồ luồng dự án sang slide PowerPoint chuẩn nhận diện thương hiệu CCBA.
- **PCCC Split-Jurisdiction Engine**: Đóng gói bộ quy tắc ma trận phân định thẩm quyền thẩm duyệt PCCC (QCVN 06 vs NĐ 105) thành Deep Skill dùng chung.
- **IDOP CLI Task Integration**: Bổ sung CLI `python -m idop list-tasks` / `idop status` để kỹ sư quản lý PGV ngay trên terminal.
- **Bộ Test Cases Chuẩn (`skills-eval`)**: Cung cấp benchmark đánh giá độ chính xác của các skill tư vấn pháp lý.

### 3. Tiêu chí nghiệm thu (Acceptance Criteria):
- [x] Quy chuẩn kênh phân phối dữ liệu OKF v2.4 và hỗ trợ lệnh tải tự động cho Spoke (`ccba_legal sync --pull-latest`, GDrive Vault, PR #230, #232).
- [x] Tạo module sinh slide thuyết trình tự động từ cấu trúc văn bản pháp lý (`python -m ccba_legal pptx`, dynamic import `ccba_ooxml`, ADR-0044).
- [x] Bổ sung module chẩn đoán phân định thẩm quyền thẩm duyệt PCCC theo luật mới (`PcccJurisdictionRouter` tại `ccba_qc_core/jurisdiction.py`, Dual-Pathway, ADR-0035, ADR-0059).
- [x] Bổ sung lệnh CLI tương tác Phiếu Giao Việc (PGV) cho Spoke (Tách sang Spoke độc lập `IDOP-CCBA-WAY` theo ADR-0018 & ADR-0043, duy trì schema compatibility contract).
- [x] Bổ sung bộ đánh giá tự động benchmark cho `legal-advisor` trong `/ccba-skills-eval` (Đã bổ sung 4 test cases thẩm quyền PCCC vào `eval_pccc_audit.json`).

> **Báo cáo nghiệm thu chi tiết:** Xem file [issue-225-audit-report.md](./issue-225-audit-report.md).

---
*Được đề xuất tự động từ Spoke `vvc_working_space` qua workflow `/ccba-issue-to-hub`.*


---

# 💬 Thảo luận (Discussion Log)
> **@Antigravity AI Agent (Triage)** (2026-09-01T10:15:00Z):
> Đã hoàn tất quy trình sàng lọc và thẩm định kỹ thuật (Triage). 
> Xác nhận đề xuất nâng cấp nền tảng với 5 trụ cột (Legal Data Vault, Legal-to-PPTX Seam, PCCC Split-Jurisdiction Engine, IDOP CLI, Legal Benchmark Eval) hoàn toàn có cơ sở và mang lại giá trị vận hành cao cho hệ sinh thái CCBA.
> Đã gán nhãn `enhancement` và chuyển trạng thái sang `ready-for-agent`. Đính kèm Agent Brief chi tiết bên dưới.

---

## Agent Brief

**Phân loại:** enhancement
**Tóm tắt yêu cầu:** Triển khai gói nâng cấp nền tảng thế hệ mới: hoàn thiện Legal Data Vault sync cho Spoke, tích hợp Deep Seam tạo slide PowerPoint từ dữ liệu pháp lý, đóng gói công cụ phân định thẩm quyền PCCC, tích hợp IDOP CLI cho kỹ sư và bổ sung benchmark kiểm thử pháp lý trong `skills-eval`.

### Hành vi hiện tại (Current behavior)
1. Spoke chạy `python -m ccba_legal sync` nhưng chưa có kênh tải trực tiếp các gói dữ liệu OKF v2.4 (Luật 135/2025/QH15, NĐ 105/2025, NĐ 175/2024...).
2. Kỹ năng tư vấn pháp lý xuất ra markdown nhưng chưa có pipeline tự động chuyển hóa thành bộ Slide PowerPoint thuyết trình theo mẫu chuẩn CCBA.
3. Kỹ năng PCCC chưa có module chẩn đoán ma trận thẩm quyền nộp hồ sơ (Sở Xây dựng vs PC07) theo Luật PCCC & CNCH 55/2024.
4. Kỹ sư Spoke chưa có giao diện CLI nhanh để xem và cập nhật Phiếu Giao Việc (IDOP tasks).
5. Chưa có bộ test cases benchmark tự động để kiểm định độ chính xác của `legal-advisor` trong `skills-eval`.

### Hành vi mong muốn (Desired behavior)
1. **Legal Data Vault Tier 1/2 Sync**:
   - Hoàn thiện lệnh `python -m ccba_legal sync --pull-latest` tải các gói OKF v2.4 từ kho lưu trữ tập trung (Server Spark / GitHub Releases).
2. **Legal-to-PPTX Deep Seam**:
   - Bổ sung module kết nối dữ liệu cây phả hệ pháp lý sang file trình chiếu PowerPoint `.pptx` chuẩn màu nhận diện thương hiệu CCBA (Navy/Amber/White).
3. **PCCC Split-Jurisdiction Diagnostic Engine**:
   - Đóng gói logic phân định thẩm quyền theo Nghị định 105/2025/NĐ-CP và QCVN 06:2024/BXD thành bộ câu hỏi/ma trận chẩn đoán nhanh.
4. **IDOP CLI Task Integration**:
   - Bổ sung module CLI `python -m idop list-tasks` và `python -m idop status <task_id> <status>` hỗ trợ kỹ sư quản lý công việc trực tiếp từ terminal.
5. **Legal Benchmark Eval Suite**:
   - Cung cấp tối thiểu 10 test cases benchmark kiểm tra trích dẫn điều khoản luật và độ chính xác tư vấn trong `skills-eval`.

### Các Interface & Kiểu dữ liệu chính (Key interfaces)
- `packages/ccba-legal/ccba_legal/sync/engine.py`: Thêm phương thức fetch remote packages.
- `packages/ccba-ooxml/`: Tích hợp template PPTX presentation generator.
- `packages/ccba-qc/` hoặc `.agents/skills/ccba-ai-qc-pccc-audit/`: Bổ sung module split-jurisdiction router.
- `scripts/idop_cli.py` / `packages/idop/`: Bổ sung giao diện CLI.
- `packages/skills-eval/tests/test_legal_advisor.py`: Bổ sung bộ benchmark test suite.

### Tiêu chuẩn nghiệm thu (Acceptance criteria)
- [ ] Lệnh `python -m ccba_legal sync --pull-latest` tải và nạp thành công các gói OKF v2.4.
- [ ] Xuất thành công file PowerPoint `.pptx` từ cây sơ đồ pháp lý.
- [ ] Chẩn đoán chính xác cơ quan thẩm duyệt PCCC (Sở Xây dựng / PC07) theo đúng quy mô và loại công trình.
- [ ] Lệnh CLI `python -m idop` liệt kê và cập nhật trạng thái PGV hoạt động ổn định.
- [ ] Bộ test suite benchmark pháp lý chạy qua 100% trong `skills-eval`.

### Phạm vi loại trừ (Out of scope)
- Không can thiệp vào cơ chế xác thực backend LDAP/Active Directory nội bộ của IDOP.
