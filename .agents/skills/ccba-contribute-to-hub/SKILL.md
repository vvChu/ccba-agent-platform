---
name: ccba-contribute-to-hub
description: Đóng gói mã nguồn, tests, proposal từ Spoke và mở PR lên Hub kèm Vòng
  lặp Dừng chờ CI & Copilot Review (Self-Healing Gate)
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _core
scope: universal
posture: seam-exempt
tier: kernel
disable-model-invocation: true
command: /ccba-contribute-to-hub
user-invocable: true
metadata:
  version: "1.3.2"
  author: "CCBA Hub"
gpi:
  s: 3.0
  k: 3.0
  a: 1.0
  p: 1.0
triggers:
- contribute
- contribute to hub
- đóng góp mã nguồn
- tạo pr lên hub
- mở proposal
- ccba-contribute-to-hub
- ccba-propose-to-hub
- propose-to-hub
- ccba-create-pr
- create-pr
---

# Workflow: Contribute to Hub (Đóng Góp Mã Nguồn Ngược Lên Hub Chuẩn OKF v2.0)

Quy trình chuẩn hóa để đóng gói mã nguồn, tests, proposal và mở GitHub Pull Request (PR) kèm hoàn tất thẩm định tự động từ Spoke lên Platform Hub (`ccba-agent-platform`). *(Lệnh: `/ccba-contribute-to-hub`)*

---

## 📋 Bước 1: Thu thập Thông tin, Liên Kết Issue & Cổng Kiểm Lọc R&D
Ghi nhận đầy đủ thông tin cốt lõi:
0. **Cổng Phân Loại 5 Điểm Rơi Phản Hồi Liên Bang (Layer 08 Learn — ADR-0045, ADR-0057, ADR-0059):**
   Trước khi mở Proposal/PR từ Spoke về Hub, bắt buộc phân loại phản hồi/bài học vào đúng 1 trong 5 điểm rơi:
   - **Điểm rơi 1 (Sửa 1 lần cho riêng 1 bản vẽ/hồ sơ):** Chỉ sửa đầu ra hiện tại (`one-off edit`), **DỪNG TẠI SPOKE**, cấm ghi thành rule hay đẩy lên Hub.
   - **Điểm rơi 2 (Quy ước cục bộ của riêng dự án Spoke):** Lưu tại `.md/workspace_context.yaml` hoặc `.md/knowledge/` của Spoke, **CẤM ĐẨY LÊN HUB** (tránh vi phạm Spoke Leakage Guard).
   - **Điểm rơi 3 (Văn bản quy phạm pháp luật / Biểu mẫu pháp lý dùng chung):** Bắt buộc đi qua đường thu thập chính quy `TVPLCrawler` (`ccba-legal-ingest`) và đóng dấu SHA-256 trên **Legal Data Hub (`ccba-legal-knowledge`, ADR-0059)**. Tuyệt đối **CẤM sửa tay `references/*.md` trên `ccba-agent-platform`** từ trí nhớ kỹ sư Spoke.
   - **Điểm rơi 4 (Quy trình hoặc tiêu chí kiểm tra đầu ra lặp lại ở nhiều dự án):** Đóng gói qua `/ccba-contribute-to-hub` để cập nhật mục `Done means` / Checklist trong `SKILL.md` (hoặc bộ ca kiểm thử `eval_*.json` qua `git_ratchet_tuner.py`) tại Hub (Tier 2B, kiểm định `python scripts/validate_skills.py --enforce-gpi` & `/ccba-review-proposal`).
   - **Điểm rơi 5 (Lỗi tính toán tất định hoặc bỏ sót bản ghi dữ liệu):** Đóng gói qua `/ccba-contribute-to-hub` để bổ sung `assert` và unit test trong `packages/*/src/` tại Hub (Tier 1 Deep Seam, Cổng 0 `ADR-0057`, kiểm định `python -m ccba_harness verify-patch --preset code`).
1. **Liên kết Issue & Cổng Tự Động Phân Loại Scope (Smart Scope-Aware Issue Gate):**
   - **Nếu có `--issue [ID]`:** Kế thừa trực tiếp mã Issue để liên kết và đóng tự động (`Closes #[ID]`).
   - **Nếu KHÔNG có `--issue`:** Agent tự động đánh giá quy mô thay đổi:
     * 🟢 **Quy mô Lớn (Major Scope):** Thêm module/deep seam mới trong `packages/`, cập nhật kiến trúc (ADR), hoặc thay đổi $\ge 100$ dòng code / $\ge 3$ files $\rightarrow$ **Agent chủ động gợi ý/tự động tạo 1 GitHub Issue** trên Hub để ghi nhận Changelog, Ký ức dài hạn (Traceability) và gắn vào PR.
     * ⚪ **Quy mô Nhỏ / Nội bộ (Minor Scope):** Vá lỗi nhỏ, sửa typo, cập nhật docstring, refactor nội bộ $< 100$ dòng $\rightarrow$ **Bỏ qua tạo Issue** để tránh làm rác Issue Tracker, mở PR trực tiếp.
2. **Loại đề xuất:** `tool` (Package trong `packages/`), `skill` (`.agents/skills/`), `workflow` (`.agents/workflows/`), hoặc `rules`.
3. **Tên đề xuất:** Dạng kebab-case (ví dụ: `modernize-annex-engine-okf-v23`).
4. **Mô tả & Vấn đề giải quyết:** Nỗi đau thực tế đã giải quyết tại Spoke.
5. **Cổng Kiểm Lọc R&D (Graduation Pre-Flight Gate):**
   - Đảm bảo mã nguồn đã được làm sạch qua `/ccba-graduate-rd` (loại bỏ 100% `print`, đường dẫn hardcoded, rác tạm; có đủ Type Hints & Docstrings Google style).
   - Test suite cục bộ trong `packages/[pkg]/tests/` phải đạt **100% PASS** trước khi tạo Proposal.
- **Tiêu chí hoàn thành:** Thu thập đầy đủ thông tin scope, tên đề xuất, liên kết issue và đảm bảo code đã clean qua `/ccba-graduate-rd`.

---

## 🔍 Bước 2: Kiểm tra Trùng lặp, Quy mô Thực tế & Biên giới Kiến trúc (Duplicate, Scale & OBE Gate)
Trước khi tạo mới, Agent **bắt buộc** kiểm tra hệ sinh thái Hub:
1. Xác định đường dẫn Hub qua biến môi trường `$CCBA_HUB_PATH` (PowerShell: `$env:CCBA_HUB_PATH`).
2. Đọc `$CCBA_HUB_PATH/.agents/skills/platform-loader/catalog.yaml`, `packages/`, `$CCBA_HUB_PATH/.agents/AGENTS.md`, `PLATFORM.md`.
3. **Cổng Thẩm định Tính Hợp Lý, Quy Mô & Hiệu Lực (Problem-Validity, Scale & OBE Gate — Rule 5 KISS & Rule 8):**
   - **Chống Dịch Cơ Học & Trùng lặp Seam:** Không đóng góp các lớp trừu tượng dịch cơ học từ khái niệm quản trị (như EOS GWC hay multi-tier dynamic routing) nếu trùng lặp 100% với Seams hiện có (`choose_model`, `MaskaraScanner`, `SandboxPromoter`, `verify-patch`).
   - **Kiểm toán Quy mô Thực tế (Empirical Scale Check):** Đo đếm quy mô dữ liệu thật ($N$ dòng/entries). Nếu $N \le 20$ và giải quyết trọn vẹn bằng grep/dict/JSONL phẳng (< 50ms) $\rightarrow$ từ chối tạo thêm CLI parser, SQLite daemon hoặc AST validator mới.
   - **Ranh giới Liên bang & Hiệu lực Lịch sử (OBE Check):** Không nhập khẩu schema nội bộ của repo liên bang khác (như bảng 15 `ROLE_ID` SharePoint Entra ID của `IDOP-CCBA-WAY`) làm lệch cấu hình `seat_role` / `qc_governance` hiện hữu; kiểm tra `git log` để tránh triển khai lại yêu cầu đã được giải quyết ở các PR/Phase sau.
*Nếu phát hiện đã tồn tại thành phần tương tự hoặc vi phạm cổng KISS/OBE:* Đề xuất tái sử dụng Seam hiện có, nâng cấp/mở rộng thay vì tạo mới trùng lặp, hoặc đóng Issue kèm biên bản phản biện thực chứng.
- **Tiêu chí hoàn thành:** Xác nhận không trùng lặp chức năng với các skill, tool hiện hữu trong `catalog.yaml` và `PLATFORM.md`, vượt qua cổng kiểm toán quy mô thực tế ($N > 20$ hoặc cần Seam mới) và đúng biên giới kiến trúc Liên bang.

---

## 📦 Bước 3: Đóng Gói Mã Nguồn & Tạo Proposal Trong Worktree Cô Lập
Thực thi **toàn bộ Bước 3–6 bên trong một `git worktree` cô lập** tại `/tmp/wt-hub-<tên-đề-xuất>` (tách từ `origin/main` của Hub); giữ bản checkout gốc `$CCBA_HUB_PATH` hoàn toàn sạch để tránh va chạm phiên song song (`RULE-4.21`):
1. **Khởi tạo Worktree Cô lập Từ `origin/main` (`RULE-4.21`):**
   ```bash
   BRANCH_NAME="proposal/<tên-đề-xuất>"
   WT_DIR="/tmp/wt-hub-<tên-đề-xuất>"
   git -C "$CCBA_HUB_PATH" fetch --prune origin
   git -C "$CCBA_HUB_PATH" worktree add -b "$BRANCH_NAME" "$WT_DIR" origin/main
   cd "$WT_DIR"
   ```
2. **Đóng gói Mã nguồn & Tests Vào Package Tương Ứng:**
   - Code: `packages/[pkg]/src/[submodule]/`, Public Deep Seam: `packages/[pkg]/src/__init__.py`, Tests: `packages/[pkg]/tests/`.
   - Format, linting & cập nhật kiến trúc ngay trong `"$WT_DIR"`:
     ```bash
     python -m ruff check --fix packages/[pkg]/ && python -m ruff format packages/[pkg]/ && python scripts/update_arch_stats.py
     ```
3. **Ghi Nhận Tệp Proposal Theo Quy Mô (`ADR 0045`):**
   - **Quy mô Lớn (Major Scope — $\ge 100$ dòng, hoặc $\ge 3$ tệp, hoặc thêm module/Seam/ADR/Skill mới):** Bắt buộc tạo tệp `.agents/proposals/[YYYY-MM-DD]_[tên-đề-xuất].md`:
     ```yaml
     ---
     proposal_id: "[YYYY-MM-DD]_[tên-đề-xuất]"
     type: "tool" # "tool" | "skill" | "workflow" | "rules"
     name: "[tên-đề-xuất]"
     status: "open"
     priority: "Cao"
     related_issue: "#[ISSUE_ID]" # Liên kết Issue nếu có
     proposed_by_project: "[tên-spoke]"
     proposed_by_archetype: "knowledge_corpus"
     proposed_date: "YYYY-MM-DD"
     applies_to: ["Phần mềm", "Thẩm tra thiết kế"]
     ---
     ```
   - **Quy mô Nhỏ / Nội bộ (Minor Scope — $< 100$ dòng vá lỗi nội bộ):** Bỏ qua tạo tệp proposal để tránh phát sinh rác kho mã, mở thẳng Micro-PR.
4. **Tái Biên Dịch Catalog/Docs, Kiểm Định Cục Bộ & Push Từ Worktree:**
   Chạy đầy đủ các cổng kiểm định bên trong `"$WT_DIR"` trước khi commit & push:
   ```bash
   python scripts/governance/compile_catalog.py
   python scripts/governance/compile_skills_docs.py --write
   python scripts/validate_skills.py --enforce-gpi
   python scripts/governance/check_spoke_leakage.py
   git add -A && git commit -m "feat([scope]): add [tên-đề-xuất]" && git push -u origin "$BRANCH_NAME"
   ```
- **Tiêu chí hoàn thành:** Worktree cô lập được tạo sạch từ `origin/main`, mã nguồn/proposal (nếu Major) đóng gói đúng chuẩn, catalog/docs đồng bộ, pass 100% `scripts/validate_skills.py --enforce-gpi` cùng `check_spoke_leakage.py`, và nhánh đã đẩy lên `origin` trong khi `$CCBA_HUB_PATH` vẫn nguyên vẹn.

---

## 🚀 Bước 4: Đánh Giá Cửa PR (`door-triage`) & Mở GitHub Pull Request
Kế thừa tiêu chuẩn khởi tạo PR từ kỹ năng [`/ccba-create-pr`](../ccba-create-pr/SKILL.md) kèm đo lường `ADR-0067` từ `"$WT_DIR"`:
- **Đo Cửa PR & Xác Thực Tradeoff Card (nếu `ONE_WAY_DOOR`) Trước Khi Mở PR:**
  Đo danh sách tệp thay đổi (`git diff --name-only origin/main...HEAD`) và tổng số dòng logic thay đổi (`git diff --shortstat origin/main...HEAD`), rồi kiểm định:
  ```bash
  python -m ccba_harness door-triage <changed_files> --logic-loc <n> --root "$WT_DIR" --pr-body-file <body_file> --enforce-tradeoff-card
  ```
- **Tạo Pull Request Qua GitHub CLI (`--repo vvChu/ccba-agent-platform`):**
  ```bash
  # Trường hợp có liên kết Issue (hoặc PR body đầy đủ kèm Tradeoff Card khi ONE_WAY_DOOR):
  gh pr create --repo vvChu/ccba-agent-platform --title "feat([scope]): add [tên-đề-xuất]" --body-file /tmp/pr_body.md --base main --head "$BRANCH_NAME"
  ```
- **Thủ công:** Truy cập `[PR-creation-URL]/pull/new/[BRANCH_NAME]`.
- **Tiêu chí hoàn thành:** `door-triage --enforce-tradeoff-card` hợp lệ (`exit 0`) và Pull Request được mở thành công trên `vvChu/ccba-agent-platform`.

---

## 🔄 Bước 5: Vòng Lặp Dừng Chờ & Tự Làm Xanh CI + Copilot Gate (Self-Healing Loop)

> [!IMPORTANT]
> **Tuyệt đối không kết thúc quy trình ngay sau khi mở PR.** Agent phải đồng hành cho đến khi $100\%$ CI Tích Xanh và Copilot Review sạch (`exit 0`).

1. **Dừng chờ động (Grace Period):** Dùng `schedule` hoặc `gh pr checks <PR_NUMBER> --repo vvChu/ccba-agent-platform --watch` hẹn kiểm tra: PR nhỏ (<100 dòng) `45s`, PR vừa (100-500 dòng) `60s-90s`, PR lớn (>500 dòng) `90s-180s`.
2. **Kiểm tra song song 2 cổng (Dual-Gate Fail-Closed):**
   - CI Status: `gh pr checks <PR_NUMBER> --repo vvChu/ccba-agent-platform`
   - Copilot Review:
     ```bash
     python "$WT_DIR/scripts/validation/audit_pr_comments.py" --repo vvChu/ccba-agent-platform --pr <PR_NUMBER>
     ```
3. **Tự khắc phục (Self-Healing Action):**
   - Nếu CI Fail: Đọc log qua `gh run view <RUN_ID> --repo vvChu/ccba-agent-platform --log-failed` $\rightarrow$ Sửa lỗi trong `"$WT_DIR"` $\rightarrow$ Commit & push bản vá.
   - Nếu Copilot góp ý: Refactor code trong `"$WT_DIR"` đối soát với chuẩn CCBA $\rightarrow$ Commit & push.
   - Tiêu chí: Lặp lại đến khi `gh pr checks <PR_NUMBER> --repo vvChu/ccba-agent-platform` pass 100% và `audit_pr_comments.py` trả mã thoát `0`.
- **Tiêu chí hoàn thành:** 100% CI Checks pass xanh và toàn bộ review của Copilot (nếu có) được giải quyết triệt để.

---

## ✅ Bước 6: Gỡ Worktree Sau Push & Bàn Giao Merge Cho Maintainer
Sau khi nhánh đã được push lên `origin`, di chuyển `cd` ra khỏi `"$WT_DIR"` (về lại thư mục Spoke) rồi mới gỡ bỏ worktree tạm:
```bash
cd "$SPOKE_ROOT"
git -C "$CCBA_HUB_PATH" worktree remove "$WT_DIR"
```
Tổng hợp báo cáo: Link PR, kết quả `door-triage`, kết quả CI `gh pr checks` và thông báo Maintainer kích hoạt `/ccba-release-feature` + `/ccba-review-proposal [PR_NUMBER]` để thực hiện squash-merge vào Hub `main`.
- **Tiêu chí hoàn thành:** Worktree tạm đã gỡ sạch sau khi chuyển thư mục làm việc ra ngoài, bản checkout Hub gốc giữ nguyên trạng và báo cáo bàn giao đầy đủ Link PR.

---

## 🔄 Bước 7: Vòng Khép Kín Hậu Hợp Nhất (Closed-Loop Spoke Sync Gate)
Sau khi PR được Squash Merge vào Hub `main`, thực thi chu trình 4 bước đóng vòng tại Spoke:
1. **Xác nhận Hợp nhất:** `gh pr view <PR_NUMBER> --repo vvChu/ccba-agent-platform --json state,mergedAt --jq '.state'` (phải là `MERGED`).
2. **Đồng bộ Downstream Từ `origin/main` Mới Nhất:** Tạo worktree tách rời trên `origin/main` của Hub (hoặc đảm bảo `$CCBA_HUB_PATH` đang khớp `origin/main`) rồi chạy `/ccba-update-spoke` hoặc:
   ```bash
   HUB_SYNC_WT="/tmp/wt-hub-sync-src"
   git -C "$CCBA_HUB_PATH" fetch --prune origin
   git -C "$CCBA_HUB_PATH" worktree add --detach "$HUB_SYNC_WT" origin/main
   CCBA_HUB_PATH="$HUB_SYNC_WT" CCBA_SKIP_GIT_PULL=1 python "$HUB_SYNC_WT/scripts/sync_spoke.py" --spoke . --apply
   git -C "$CCBA_HUB_PATH" worktree remove "$HUB_SYNC_WT"
   ```
3. **Tái cài đặt Editable Package (nếu có sửa `packages/`):**
   ```bash
   pip install -e "$CCBA_HUB_PATH/packages/[package-name]"
   ```
4. **Hồi quy Theo Archetype & Dọn Dẹp:** Đọc `project.archetype` trong `.md/workspace_context.yaml` và chạy bộ kiểm định tương ứng, sau đó xóa branch tạm và cập nhật `.md/knowledge/session_learnings.md`:
   - `knowledge_corpus`: `python scripts/validate_legal_spoke.py`
   - `project_delivery`, `enterprise_governance`, hoặc `specialized_extension`:
     ```bash
     python "${CCBA_HUB_PATH:-../ccba-agent-platform}/scripts/spoke/check_spoke_cleanliness.py" --path .
     python "${CCBA_HUB_PATH:-../ccba-agent-platform}/scripts/spoke/check_hub_import_depth.py" --path .
     ```
- **Tiêu chí hoàn thành:** Nhánh feature được merge, Spoke downstream đồng bộ sạch từ Hub `origin/main`, bộ kiểm định theo `archetype` đạt `exit 0` và `session_learnings.md` được cập nhật.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/propose_to_hub.md` | Quy trình đề xuất kỹ năng/tính năng mới từ Spoke lên Hub trung tâm |
| `references/proposal_review_sop.md` | Quy trình chuẩn SOP thẩm định các đề xuất Pull Request từ Spoke gửi lên Hub |
