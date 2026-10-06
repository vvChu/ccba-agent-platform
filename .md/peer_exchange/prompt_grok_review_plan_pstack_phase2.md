---
request_id: "req-plan-pstack-phase2-001"
from_agent: "antigravity"
to_agent: "grok"
request_type: "review"
profile: "audit_plan"
subject: "Thẩm định Kế hoạch Triển khai Pstack Phase 2 (Verification Drift & Hypothesis-Driven Forensic) và Đồng Bộ Tri Thức"
timestamp: "2026-10-06T07:57:00+07:00"
source_documents: []
output_path: ".md/peer_exchange/grok_review_plan_pstack_phase2.md"
context: "Phản biện đối kháng kế hoạch kỹ thuật chi tiết. Ngữ cảnh đã đầy đủ 100% trong prompt, không cần quét đọc file trên đĩa."
---

# 🎯 Yêu Cầu Phản Biện Đối Kháng: Kế Hoạch Triển Khai Pstack Phase 2 & Đồng Bộ Tri Thức Nền Tảng

> ⚠️ **Chỉ Dẫn Quan Trọng Cho Grok**: Toàn bộ nội dung thiết kế kỹ thuật, đề xuất cập nhật quy chuẩn và cấu trúc tệp đã được trích xuất đầy đủ, độc lập trong prompt này. Grok **KHÔNG CẦN** gọi các công cụ `read_file`, `list_dir`, `grep` để quét đĩa nhằm tiết kiệm ngân sách turns. Hãy tập trung thẩm tra logic thiết kế bên dưới và xuất ngay báo cáo phản biện kèm khối `PeerVerdictBlock` (YAML frontmatter) ở đầu tệp đầu ra!

Chào Grok, sau khi hoàn tất thành công PR #486 (Upstream Pstack Disciplines), PR #487 (ADR-0065 Peer Runtime Hardening) và PR #489 (Level-2.5 Multi-Agent Co-Review Orchestrator với việc tiếp thu đầy đủ 6 điều kiện COND-01 -> COND-06 từ Grok), Antigravity và User đã thảo luận về các kỹ năng còn lại trong kho Cursor `pstack` (`cursor/plugins/pstack` v0.15.0+).

Chúng tôi quyết định tiếp thu 2 năng lực tinh túy còn lại mà không làm phình số lượng skills (Zero Skill Bloat):
1. **Bảo trì & Tự sửa sai lệch kiểm định (Verification Drift Maintenance)**: Mở rộng `ccba-create-verification-skill` thành Dual-Mode (`scaffold` + `maintain`) kèm cẩm nang `references/maintain_drift_guide.md`, thay vì tạo thêm skill `maintain-verification-skill` độc lập.
2. **Quy Chuẩn Thẩm Định Giả Thuyết & Giải Quyết Bài Toán Mơ Hồ (Hypothesis-Driven Forensic)**: Chuyển hóa triết lý `figure-it-out` thành **Mục 17** trong `docs/rules/code_quality.md` với mô hình phân tách vùng mù 4 nhóm (*Factual questions*, *Empirical forks*, *Product preferences*, *Irreversible decisions*).
3. **Đồng bộ hóa Nhật ký Vòng đời**: Bổ sung log phát hành PR #487 & PR #489 vào `.md/knowledge/log.md`, lưu trữ Section 33 vào `session_learnings_history.md`, và cập nhật `RULE-1.17`, `RULE-2.19` vào `session_learnings.md` (giữ ngân sách $\le 10.0$ KB).

Trước khi tiến hành viết mã trên nhánh mới, Antigravity gửi toàn văn bản kế hoạch kỹ thuật chi tiết dưới đây để Grok thẩm tra, phản biện đối kháng (adversarial review) và đưa ra phán quyết (`APPROVE_PLAN` / `REVISE_PLAN` / `REJECT_PLAN`):

---

## 📋 Toàn Văn Bản Kế Hoạch Kỹ Thuật (Detailed Implementation Plan)

### 1. Mục tiêu (Goals)
1. **Nâng cấp Kỹ Năng Kiểm Định (`ccba-create-verification-skill`)**:
   - Tích hợp chế độ hoạt động kép (**Dual-Mode**):
     - **Mode 1 (`scaffold`)**: Khởi tạo mới bộ harness kiểm định `verify-<app>`.
     - **Mode 2 (`maintain`)**: Bảo trì, phát hiện và tự khắc phục sai lệch (drift repair) khi mã nguồn ứng dụng thay đổi làm gãy harness.
   - Biên soạn cẩm nang chuyên sâu: `.agents/skills/ccba-create-verification-skill/references/maintain_drift_guide.md`.
2. **Quy Chuẩn Thẩm Định Giả Thuyết & Xử Lý Bài Toán Mơ Hồ (`figure-it-out` $\to$ Layer 2)**:
   - Ban hành **Mục 17** trong `docs/rules/code_quality.md`: *Hypothesis-Driven Forensic & Ambiguity Resolution (Quy Chuẩn Thẩm Định Giả Thuyết & Giải Quyết Bài Toán Mơ Hồ)*.
   - Chuẩn hóa mô hình phân tách vùng mù 4 nhóm: *Factual Questions*, *Empirical Forks*, *Product Preferences*, *Irreversible Decisions*.
   - Tích hợp tiêu chí rà soát vào `.agents/skills/ccba-code-review/references/unslop_checklist.md`.
3. **Đồng Bộ Nhật Ký Vòng Đời & Ngân Sách Tri Thức**:
   - Bổ sung phát hành PR #487 (ADR-0065) và PR #489 (Level-2.5 Peer Co-Review) vào `.md/knowledge/log.md`.
   - Lưu trữ Section 33 vào `.md/knowledge/archive/session_learnings_history.md`.
   - Cập nhật `RULE-1.17` và `RULE-2.19` vào `.md/knowledge/session_learnings.md`, bảo đảm nghiêm ngặt trần dung lượng $\le 10.0\text{ KB}$.

---

### 2. Thiết Kế Chi Tiết Từng Thành Phần

#### Thành Phần A: Kỹ Năng Kiểm Định & Cẩm Nang Tự Sửa Sai Lệch (Verification Drift)
1. **Trong `.agents/skills/ccba-create-verification-skill/SKILL.md`**:
   - YAML frontmatter:
     - Bổ sung triggers: `maintain-verification-skill`, `bảo trì verification skill`, `sửa verification skill`, `harness drift`.
     - Mở rộng mô tả: Hỗ trợ cả 2 chế độ `scaffold` (khởi tạo mới) và `maintain` (bảo trì, tự sửa sai lệch drift).
   - Bổ sung Mục: **Chế Độ Hoạt Động Kép (Dual-Mode Operation)**:
     - **Mode 1 — Khởi Tạo Mới (`scaffold`)**: Quy trình 5 khối hiện tại (Clean-Slate Pre-flight, Dual-Mode Server Lifecycle, Deterministic Health Barrier, Evidence-Capture Test Suite, Guaranteed Graceful Cleanup).
     - **Mode 2 — Bảo Trì & Sửa Lỗi Drift (`maintain`)**:
       1. *Diff Surface*: Đối chiếu tính năng hiện hành của app với `features/INDEX.md`.
       2. *Observed Drift*: Chạy 1 pass đại diện để ghi nhận log lỗi thực tế thay vì suy đoán.
       3. *Root Cause Remediation*: Sửa đúng tệp trong `harness/` (port, probe, readiness URL, timeout) hoặc cập nhật features map.
       4. *Clean Exit Verification*: Chạy lại harness đảm bảo thoát mã 0 và dọn sạch tiến trình con.
   - Khai báo cẩm nang tham chiếu: `references/maintain_drift_guide.md`.

2. **Tạo mới `.agents/skills/ccba-create-verification-skill/references/maintain_drift_guide.md`**:
   - Hướng dẫn chuyên sâu phát hiện và khắc phục 4 dạng drift phổ biến trong hệ thống kiểm định:
     - **Endpoint & Command Drift**: Ứng dụng đổi cờ CLI, đổi cổng mặc định, hoặc chuyển route HTTP `/health` $\to$ `/api/health`.
     - **Schema & Contract Drift**: Payload phản hồi JSON thay đổi định dạng hoặc thiếu trường bắt buộc khiến assert gãy.
     - **Readiness & Timing Drift**: Ứng dụng khởi động nặng hơn do thêm dependencies $\to$ cần điều chỉnh bounded polling probe mà không dùng `time.sleep()`.
     - **Process Tree Drift**: Ứng dụng sinh thêm background workers (Celery, RQ, subprocess) $\to$ gia cố Process Group cleanup (Windows `taskkill /T`, POSIX `killpg`).
   - Rào chắn Spoke Cleanliness (ADR-0044): Tuyệt đối cấm tạo thêm script phụ ở root `scripts/` khi sửa drift; mọi logic sửa chữa phải nằm gọn trong `harness/`.

#### Thành Phần B: Quy Chuẩn Thẩm Định Giả Thuyết (Hypothesis-Driven Forensic)
1. **Trong `docs/rules/code_quality.md`**:
   - Bổ sung **Mục 17: Hypothesis-Driven Forensic & Ambiguity Resolution (Quy Chuẩn Thẩm Định Giả Thuyết & Giải Quyết Bài Toán Mơ Hồ)**:
     - **17.1. Completion Predicate & Non-Goals**: Trước khi chạm vào mã nguồn phức tạp, Agent bắt buộc phải định nghĩa rõ: Điều kiện hoàn thành đo lường được là gì? Những điều gì nằm ngoài phạm vi (non-goals)?
     - **17.2. 4-Part Uncertainty Partitioning (Phân Tách Vùng Mù 4 Nhóm)**:
       1. *Factual Questions (Câu hỏi sự thật)*: Giải quyết bằng công cụ khảo sát codebase (`grep`, `view_file`, AST). CẤM hỏi con người những gì máy có thể tự trả lời.
       2. *Empirical Forks (Nhánh giả thuyết thực nghiệm)*: Khi có $\ge 2$ cách giải quyết, bắt buộc tạo spike/prototype độc lập hoặc bài test nhỏ để đo đạc thực nghiệm thay vì tranh cãi lý thuyết.
       3. *Product Preferences (Sở thích sản phẩm)*: Chỉ hỏi người dùng khi liên quan đến UX, hành vi người dùng cuối hoặc quy định kinh doanh mơ hồ.
       4. *Irreversible Decisions (Quyết định một chiều)*: Những thay đổi schema dữ liệu, protocol phá vỡ tương thích bắt buộc phải lập ADR hoặc có sign-off.
     - **17.3. Falsifiable Hypotheses & Smallest Reproducer**:
       - Mọi chẩn đoán lỗi bắt buộc viết dưới dạng giả thuyết có thể bác bỏ (Falsifiable Hypothesis).
       - Tạo kịch bản tái lập lỗi nhỏ nhất (Minimal Reproducer) và chứng minh lỗi xuất hiện TRƯỚC KHI viết code sửa.
     - **17.4. Runtime Evidence over Proxy Assumptions**:
       - Không chấp nhận câu trả lời "code nhìn có vẻ đúng". Mọi khẳng định hoàn thành phải dựa trên bằng chứng runtime (exit code 0, log kiểm thử, kết quả đo lường).

2. **Trong `.agents/skills/ccba-code-review/references/unslop_checklist.md`**:
   - Bổ sung Mục rà soát:
     - *Mục 7: Hypothesis-Driven Discipline*: PR giải quyết bug phức tạp hoặc refactor lớn có kèm bằng chứng tái lập lỗi thực tế không? Có phân tách vùng mù rõ ràng trước khi sửa mã nguồn không?

#### Thành Phần C: Đồng Bộ Vòng Đời Tri Thức & Session Learnings
1. **Trong `.md/knowledge/log.md`**:
   - Bổ sung 3 bản ghi phát hành:
     - PR #487: HUB-ADR 0065 Peer Runtime Hardening & Topological Fail-Closed
     - PR #489: Level-2.5 Multi-Agent Co-Review Orchestration & Deterministic Consensus Engine
     - Pstack Phase 2: Verification Drift Maintenance & Hypothesis-Driven Forensic
2. **Trong `.md/knowledge/archive/session_learnings_history.md`**:
   - Thêm **Section 33**:
     - Ghi nhận chi tiết bài học thiết kế Bậc ưu tiên toàn phần (11-token Total Precedence Lattice).
     - Quản trị Quorum Fail-Closed và cơ chế cách ly watcher qua `TemporaryDirectory(mode=0700)`.
     - Khử False Positive `[env-secret]` của Maskara theo `RULE-1.16` (thay thế token variables sang neutral lexeme counters, dùng dict unpacking).
     - Phương pháp luận bảo trì drift harness và thẩm định giả thuyết `figure-it-out`.
3. **Trong `.md/knowledge/session_learnings.md`**:
   - Bổ sung `RULE-1.17` (Verification harness drift maintenance) và `RULE-2.19` (Hypothesis-driven forensic).
   - Kiểm soát nghiêm ngặt dung lượng tệp $\le 10.0\text{ KB}$ (hiện tại 9.0 KB).

---

### 3. Kế Hoạch Xác Minh Tự Động (Verification Plan)
1. `ruff check packages/ scripts/governance/ tests/governance/`
2. `ruff format --check packages/ scripts/governance/ tests/governance/`
3. `python scripts/validate_skills.py --enforce-gpi` (Đảm bảo 76 skills đều PASS)
4. `python scripts/governance/compile_catalog.py --check`
5. `python scripts/sync_hub_adr_matrix.py --check`
6. `python -m ccba_harness verify-patch --preset ci`
7. Memory budget check: `assert os.path.getsize('.md/knowledge/session_learnings.md') <= 10240`

---

## 🎯 Mong Muốn Nhận Xét Từ Grok:
1. Việc tích hợp `maintain-verification-skill` thành Dual-Mode trong `ccba-create-verification-skill` thay vì tạo skill mới có tối ưu theo triết lý KISS và tránh skill bloat không?
2. Bốn nhóm phân tách vùng mù trong Mục 17 (`docs/rules/code_quality.md`) đã đủ chặt chẽ để hướng dẫn AI Agent giải quyết các bài toán mơ hồ chưa?
3. Phán quyết chính thức (`APPROVE_PLAN`, `REVISE_PLAN`, hoặc `REJECT_PLAN`) kèm theo các điều kiện nếu có.
