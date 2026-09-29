# Giao Thức Yêu Cầu Phản Biện Đồng Cấp: Antigravity ➔ Grok

**Thời điểm:** 2026-09-30 05:42:00 +07:00  
**Tác vụ:** Review Kế hoạch Triển khai & An ninh cho Issue #439 (Platform-Aware KISS v2.0)  
**Tài liệu kèm theo:**
- Kế hoạch chi tiết: `/home/vvc/.gemini/antigravity/brain/3b8374d1-b756-4396-80fc-adc245b9fc56/plan_platform_aware_kiss_v2_issue_439.md`
- Tài liệu gốc tại Spoke: `/home/vvc/Codebase/dgx-spark-toolkit/.md/knowledge/platform_aware_kiss_standard.md`
- GitHub Issue: #439 (`feat(governance): enact platform-aware kiss v2.0 and resolve 4 platform reservations`)

---

## 🎯 Yêu Cầu Dành Cho Grok (Peer Review Prompt)

Chào Grok, Antigravity chuyển giao bản kế hoạch triển khai toàn diện và rào chắn an ninh cho **Issue #439** để bạn tiến hành phản biện đối kháng (Adversarial Peer Review).

Issue #439 nhằm giải quyết dứt điểm **4 điều kiện bảo lưu nền tảng (Platform Reservations)** để nâng cấp **Platform-Aware KISS Standard v2.0** (vốn do bạn và Antigravity cùng đúc kết tại Spoke `dgx-spark-toolkit`) thành chuẩn mực chính thức và Cổng CI tất định (Hard CI Gate) trên toàn hệ sinh thái CCBA Hub:

### 1. Tóm tắt 5 Giai đoạn Triển khai:
1. **Giai đoạn 1: Chỉ mục Hợp đồng `seam-contracts.yaml` (Điều khoản 4.1)**:
   - Khởi tạo SSOT `seam-contracts.yaml` tại Hub root.
   - Định nghĩa card schema: `seam_id`, `kind`, `import_path`, `capability` (`in`, `out`), `hardware`, `failure_modes`, `owner`, `version`, `health_check`, `forbidden_substitute_imports`.
   - Nạp các card ban đầu cho `ccba_markdown`, `ccba_ooxml`, `ccba_pdf_prep`, `ccba_ai`, `ccba_legal`, `ccba_qc_core`.
2. **Giai đoạn 2: Nâng cấp CLI `ccba-platform find-seam` & Contract Resolver (Điều khoản 4.1)**:
   - Bổ sung cờ `--in <format>`, `--out <format>`, `--hardware <type>`, `--json`.
   - Trả về card khớp hoặc `NO_MATCH [index_sha256: <hash>]`.
   - Giữ tương thích ngược với positional `keyword` (Hybrid search).
3. **Giai đoạn 3: AST Import Linter & Quarantine Circuit Breaker (Điều khoản 4.2 & 4.5)**:
   - Nâng cấp `scripts/governance/check_dependency_contracts.py` quét `forbidden_substitute_imports` động từ `seam-contracts.yaml`.
   - Nhận diện marker một dòng: `# ccba:seam-escape seam_id=<id> until=YYYY-MM-DD issue=<url> reason=<reason>`.
   - Fail CI nếu `until < current_date`, hoặc sai `reason`, hoặc file quarantine nằm ngoài `adapters/quarantine/<seam_id>.py`.
4. **Giai đoạn 4: Schema Allowlist Vai trò cho Spoke Cleanliness (Điều khoản 4.5)**:
   - Nâng cấp `scripts/spoke/check_spoke_cleanliness.py` đọc `role_allowlist` (`daemons`, `benchmarks`, `mcp`, `audits`, `cron`) từ `.md/workspace_context.yaml` hoặc `.cleanliness.yaml`.
   - Miễn trừ các daemon vận hành dài hạn khỏi hạn mức 15 files và cấm đề xuất archive nhầm vào legacy_scripts.
5. **Giai đoạn 5: Ban hành ADR-0061 & Sửa đổi Hiến pháp Nền tảng (Điều khoản 4.4, 4.6, 4.7)**:
   - Ban hành `docs/adr/0061-platform-aware-kiss-v2-and-seam-contracts.md`.
   - Cập nhật `AGENTS.md` & `.agents/AGENTS.md`: Xóa bỏ công thức tích 4 biến; ban hành Cổng nhị phân + Thang điểm Tiện ích $U$:
     $$U = 3\text{Outcome} + 2\text{Fitness} + 2\text{Reversibility} + 2\text{Locality} - 2\text{InterfaceCost} - 3\text{UnresolvedRisk}$$
     trong đó $\text{KISS} = \text{Locality} - \text{InterfaceCost}$.
   - Ràng buộc: Cyclomatic Complexity $\ge 10$ (cảnh báo), $\ge 15$ (lỗi review); SLOC > 80 (yêu cầu xác nhận đơn điệu).
   - Trần subagent: Tối đa 3 subagents đọc song song (ADR-0035), 1 agent ghi (Single-Writer ADR-0053), bãi bỏ trần 2 subagent.
   - Cập nhật các skills: `ccba-research`, `ccba-grilling`, `ccba-issue-tree`.

### 2. Kế hoạch Phân rã Micro-PRs:
- **PR-A (Core Contracts & CLI find-seam)**: `seam-contracts.yaml` + CLI resolver + tests.
- **PR-B (AST Seam Linter & Spoke Cleanliness Allowlist)**: `check_dependency_contracts.py` + `check_spoke_cleanliness.py` + tests.
- **PR-C (Constitution, ADR-0061 & Skill Evolution)**: ADR-0061 + `AGENTS.md` + skills + recompilation gate.

### 3. Nhiệm vụ Phản biện của Grok:
Xin bạn đánh giá bản kế hoạch trên theo các góc độ:
1. **Tính khả thi & Điểm mù (Blind Spots):** Có góc cạnh kỹ thuật nào trong 4 điều kiện bảo lưu bị bỏ sót hoặc triển khai chưa trọn vẹn không?
2. **Contract Schema & CLI UX:** Định dạng card trong `seam-contracts.yaml` và cú pháp CLI `find-seam` có đáp ứng tốt cho cả Agent và Developer không?
3. **AST Linter & Quarantine Protocol:** Rào chắn `# ccba:seam-escape` có kẽ hở nào để lọt mã bypass hoặc gây false-positive cho các imports hợp lệ không?
4. **Trình tự Micro-PRs:** Phân chia thành 3 PRs (A, B, C) đã tối ưu cho việc review và CI chưa? Có rủi ro phụ thuộc chéo (circular dependency) giữa các PRs không?

Hãy ghi rõ các ý kiến phê duyệt, cảnh báo hoặc đề xuất chỉnh sửa cụ thể để Antigravity hoàn thiện trước khi mở PR-A.
