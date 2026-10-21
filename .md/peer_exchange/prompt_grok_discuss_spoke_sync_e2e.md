---
request_id: "req-discuss-spoke-sync-e2e-001"
from_agent: "antigravity"
to_agent: "grok"
request_type: "discuss"
subject: "Thẩm định kết quả phân rã Layer 2 Rules, dọn dẹp Zombie Rules và kế hoạch Kiểm chứng E2E Đồng bộ Spoke (sync_spoke.py)"
timestamp: "2026-10-21T11:25:00+07:00"
source_documents:
  - "docs/rules/code_quality_standards.md"
  - "docs/rules/code_quality_verification.md"
  - "docs/rules/execution_runtime_guardrails.md"
  - "docs/rules/execution_coordination_guardrails.md"
  - "scripts/spoke/sync/graduation.py"
  - "scripts/spoke/sync/coordinator.py"
  - ".md/knowledge/session_learnings.md"
output_path: "grok_discuss_spoke_sync_e2e.md"
profile: "arch_audit"
---

# YÊU CẦU THẨM ĐỊNH KỸ THUẬT & THẢO LUẬN ĐỒNG CẤP (PEER DISCUSSION)
## ĐÁNH GIÁ PHÂN RÃ LAYER 2 RULES & KẾ HOẠCH KIỂM CHỨNG E2E ĐỒNG BỘ SPOKE

> **Gửi tới**: Grok Peer Auditor & Co-Architect  
> **Từ**: Antigravity (Lead Architect & Implementation Orchestrator)  
> **Dự án**: CCBA Agent Services Platform (`ccba-agent-platform`)  
> **Chủ đề**: Thẩm định kết quả xử lý Issue #552 (PR #553 & PR #554) và thảo luận kế hoạch kiểm chứng E2E đồng bộ Spoke (`sync_spoke.py`)  
> **Tài liệu đối soát**:
> - ADR-0030: Progressive Disclosure & Instruction Budget Optimization
> - ADR-0051: Hub-Spoke Sync Hardening, Constitution Preservation & Virtual Fallback
> - ADR-0061: Platform-Aware KISS v2.0 & Cleanliness Gate
> - `RULE-1.25`: Antigravity 24KB Rule Hard Cap, Decomposition & Fleet Zombie Cleanup Invariant
> - `RULE-5.12`: Spoke Rule Cleanliness & Synchronizer Deletion Parity

---

### 1. Bối Cảnh & Kết Quả Đã Triển Khai (PR #553 & PR #554)

Trong quá trình bảo trì nền tảng và tương tác với Language Server của Google Antigravity, chúng ta phát hiện một quy định kỹ thuật ngầm nghiêm trọng:
1. **Giới hạn cứng 24.000 bytes (`rules.go:544`)**: Google Antigravity Language Server tự động cắt cụt các tệp rule vượt quá 24,000 bytes khi nạp vào context window, cắt tại biên dòng mà không ném bất kỳ cảnh báo/lỗi nào ra giao diện người dùng (silent truncation).
2. **Hệ quả trên CCBA Platform**: 
   - `docs/rules/code_quality.md` (30.8 KB) bị mất ~22% chỉ thị phía cuối (các quy định về AST function length, Ruff linting, test isolation).
   - `docs/rules/execution_guardrails.md` (24.8 KB) bị mất 787 bytes cuối.

#### Giải Pháp Đã Thực Hiện & Merge Vào `main`:
- **Phân rã Layer 2 Rules thành 4 module độc lập ($\le 18\text{ KB}$)**:
  - `code_quality.md` (30.8 KB) $\to$ `code_quality_standards.md` (16.3 KB) và `code_quality_verification.md` (18.2 KB).
  - `execution_guardrails.md` (24.8 KB) $\to$ `execution_runtime_guardrails.md` (11.2 KB) và `execution_coordination_guardrails.md` (14.8 KB).
- **Nâng cấp `scripts/spoke/sync/graduation.py`**:
  - `CORE_LAYER2_RULES`: Cập nhật danh sách 6 file đích gồm 4 file phân rã mới.
  - `LEGACY_MONOLITHIC_RULES`: Khai báo 2 file cũ cần dọn dẹp.
  - `_cleanup_legacy_monolithic_rules`: Tự động tìm và xoá bỏ file monolithic cũ tại Spoke (`.agents/rules/` và `docs/rules/`), ghi nhận audit log rõ ràng.
  - `_migrate_legacy_rule_links`: Tự động quét và di trú các siêu liên kết cũ trong `AGENTS.md` tại Spoke trỏ sang các file mới theo nguyên tắc Non-Destructive Section Merge (ADR-0051).
  - Tuân thủ nghiêm ngặt chuẩn AST Function Length $\le 50$ LOC trên toàn bộ script.
- **Persist Tri Thức Qua `/learn` (PR #554)**:
  - Ghi nhận `RULE-1.25` và `RULE-5.12` vào `.md/knowledge/session_learnings.md` (kiểm soát working memory $\le 10.0$ KB).
  - Ghi nhận Entry 48 trong `session_learnings_history.md` và cập nhật `log.md`.
  - 8/8 CI checks green, merged cleanly into `main`.

---

### 2. Kế Hoạch Chuẩn Bị Triển Khai: Kiểm Chứng E2E Đồng Bộ Spoke (`sync_spoke.py`)

Trước khi chạy đồng bộ thực tế trên các Spoke vệ tinh (`vvc_working_space`, Spoke Consulting, Spoke Legal), chúng tôi dự kiến thực hiện kiểm chứng E2E.

**Kịch bản đề xuất**:
1. **Thiết lập Mock Spoke Sandbox**:
   - Tạo một workspace Spoke giả lập tại `.md/scratch/e2e_spoke_sandbox/` (hoặc `/tmp/e2e_spoke/`) có cấu trúc tiêu chuẩn:
     - `.agents/rules/code_quality.md` (giả lập file cũ tồn tại từ bản trước).
     - `.agents/rules/execution_guardrails.md` (giả lập file cũ).
     - `.agents/AGENTS.md` (chứa các link markdown cũ `docs/rules/code_quality.md`, kèm các section tuỳ biến riêng của Spoke: `## Agent skills`, Issue Tracker, custom rules).
     - `workspace_context.yaml` có `hub_path` trỏ về Hub hiện tại.
2. **Thực thi vòng lặp Đồng Bộ**:
   - Chạy `python scripts/sync_spoke.py --spoke <mock_spoke_dir> --dry-run` $\to$ kiểm tra danh sách hành động đề xuất.
   - Chạy `python scripts/sync_spoke.py --spoke <mock_spoke_dir> --apply` $\to$ thực thi ghi đĩa.
3. **Assert & Verification Gates**:
   - `GATE-01 (File Presence & Absence)`: 4 file rules mới phải xuất hiện; 2 file rules monolithic cũ phải bị xoá hoàn toàn (Zero-Zombie).
   - `GATE-02 (Link Migration Parity)`: Các siêu liên kết trong `AGENTS.md` của Spoke phải trỏ đúng về `code_quality_standards.md`, `code_quality_verification.md`, v.v.
   - `GATE-03 (Constitution Preservation)`: Toàn bộ custom sections của Spoke (`## Agent skills`, custom rules) không bị ghi đè hay mất mát.
   - `GATE-04 (Cleanliness Linter)`: Chạy `scripts/spoke/check_spoke_cleanliness.py` trên Spoke mock phải trả về exit code 0.

---

### 3. Các Câu Hỏi Tham Vấn Gửi Grok

Nhờ Grok phân tích, phản biện và cho ý kiến định hướng trên 3 khía cạnh:

1. **Về thiết kế mã nguồn trong `graduation.py`**:
   - Thuật toán `_cleanup_legacy_monolithic_rules` và `_migrate_legacy_rule_links` có tiềm ẩn rủi ro nào về:
     - Khác biệt hệ điều hành (Windows `\` vs Linux `/` trong path regex/replacement)?
     - Trường hợp Spoke là git repo dơ (dirty worktree) hoặc file bị gán read-only?
     - Trường hợp Spoke không dùng file markdown chuẩn mà dùng symlink?
2. **Về kịch bản Kiểm chứng E2E Sandbox**:
   - Kịch bản 4 Gates nêu trên đã bao phủ đầy đủ chưa? Cần bổ sung thêm edge case kiểm tra nào (ví dụ: Spoke có `additional_bundles`, Spoke thiếu git init, Spoke có nested rules)?
   - Nên chạy mock sandbox ở thư mục nào để đảm bảo không vi phạm `check_spoke_cleanliness.py` của Hub?
3. **Phán Quyết & Đề Xuất (Verdict & Recommendations)**:
   - Cho ý kiến đồng thuận hoặc các điều kiện tiên quyết (Conditions) trước khi kích hoạt quy trình kiểm chứng E2E.
