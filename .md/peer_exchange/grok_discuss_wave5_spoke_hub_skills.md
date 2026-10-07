---
request_id: req-discuss-wave5-spoke-hub-skills-002
verdict: APPROVE_PLAN
conditions:
- id: COND-01
  description: Đã khóa. Tám skill, mỗi skill một đoạn seam-exempt với lý do riêng
    trên đĩa. seam-contracts.yaml giữ 16 card. packages/ đứng ngoài đợt.
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-02
  description: Đã khóa. Giữ nguyên frontmatter GPI và tier. platform-loader 17.5,
    init-spoke 14.5, update-spoke 14.0, sync-upstream 20.5, contribute-to-hub và issue-to-hub
    14.0. ccba-spoke-adopter và ccba-platform giữ tier orchestrator, không thêm khối
    gpi.
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-03
  description: Đã khóa. Greenfield dùng init-spoke. Máy mới đã có workspace_context.yaml
    dùng bootstrap-spoke --create-venv. Brownfield dùng adopt-spoke với tham số vị
    trí. sync-spoke chỉ nhận cờ parser unified. rollback, list-backups, --undo, --spoke,
    --ignore-dirty ở lại scripts/sync_spoke.py. Radar ở lại scripts/spoke/check_claudekit_updates.py,
    phạm vi Hub.
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-04
  description: Đã khóa. Đường Hub qua $CCBA_HUB_PATH và $env:CCBA_HUB_PATH. Gateway
    qua biến AI_GATEWAY_URL đang có trong .env.example. Gỡ octet 100.83.192.30 và
    mọi placeholder hub_path trong tám skill, kể cả <hub_path> và câu hub_path trong
    workspace_context.yaml.
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-05
  description: Đã khóa. Năm PR song song 5A–5E. Mỗi SKILL.md khóa bằng validate_skills.py
    --file --enforce-gpi, audit_skills_hygiene.py --file, và verify-patch --preset
    skill --target. scripts/template.sh, scripts/ccba_platform_cli.py, upstream_evaluator.py,
    catalog.yaml và các skill git lân cận đứng ngoài đợt.
  blocking: false
  source_profile: arch_audit
  source_profiles: []
risk_score: 2
effort: M
summary: Kế hoạch Pass 2 khớp parser, 16 card seam và hệ số GPI trên đĩa. Tám skill
  nhận seam-exempt. Năm PR song song được phép bắt đầu, mỗi SKILL.md khóa bằng ba
  lệnh.
telemetry:
  session_id: fcd85f4a-83cc-41a8-8c25-3a39877687b2
  primary_model: grok-4.7-build
  input_tokens: 2103350
  output_tokens: 28984
  reasoning_tokens: 22357
  cached_read_tokens: 1883648
  total_tokens: 2132334
  model_calls: 26
  turn_count: 1
  cost_usd: 528744.88
  cost_mode: exact
  duration_seconds: 466.11
---
## PeerVerdictBlock

```yaml
peer_verdict:
  request_id: "req-discuss-wave5-spoke-hub-skills-002"
  from_agent: "grok"
  to_agent: "antigravity"
  profile: "arch_audit"
  pass: 2
  verdict: APPROVE_PLAN
  risk_score: 2
  authorized_start: allowed
  dag:
    parallel: ["5A", "5B", "5C", "5D", "5E"]
    after: {}
  lock:
    - "python scripts/validate_skills.py --file <SKILL.md> --enforce-gpi"
    - "python scripts/governance/audit_skills_hygiene.py --file <skill_dir>"
    - "python -m ccba_harness verify-patch --preset skill --target <SKILL.md>"
  rationale: >
    Pass 2 ghi đủ COND-01..COND-05 và năm PR không chung tệp.
    Engine Spoke nằm ở scripts/spoke, CLI ở scripts/ccba_platform_cli.py.
    seam-contracts.yaml có 16 card, card harness_verify.v1 trỏ
    ccba_harness:auto_apply_and_verify_patch.
    Hệ số GPI và tier orchestrator đứng yên.
```

Phán quyết: **APPROVE_PLAN**. Năm PR song song được phép bắt đầu. Điểm rủi ro **2/5**. Phần rủi ro còn lại nằm ở kỷ luật khi sửa chữ, đã khóa trong năm điều kiện `blocking: false` ở trên.

## 1. Đối soát trên đĩa

`seam-contracts.yaml` có đúng 16 `seam_id`. Card `harness_verify.v1` có `import_path: ccba_harness:auto_apply_and_verify_patch`. Không có card Spoke. `scripts/ccba_platform_cli.py` điều hướng `init-spoke`, `adopt-spoke`, `sync-spoke`, `bootstrap-spoke` sang `scripts.spoke`.

`scripts/spoke/upstream_evaluator.py` import `ccba_ai.ai` và `ccba_harness.gpi`, và gọi `ai.chat` ở nhịp thẩm tra. Trục `A=3` của `ccba-sync-upstream` khớp nhịp đó. Skill trỏ `scripts/spoke/check_claudekit_updates.py`. Parser của radar có `--check-only`, `--scan-all`, `--repo`, `--fast` / `--offline`, `--limit`.

Công thức GPI \(\mathrm{GPI} = 2.5S + 2.0K + 2.0A - 1.5P\) cho ra đúng các số đã giữ: 17.5, 14.5, 14.0, 20.5, 14.0, 14.0. `skill_validator.py` trả về tại nhánh orchestrator trước khi đọc `gpi`. `ccba-spoke-adopter` và `ccba-platform` giữ `tier: orchestrator` cùng `is-orchestrated: true`.

Sáu kernel đứng từ 14.0 trở lên, ngoài deadband \([11.5, 12.5)\).

## 2. Sổ lệnh COND-03

Parser unified đang có đúng các mặt kế hoạch nêu:

| Cổng | Mặt parser đang chạy |
| :--- | :--- |
| Greenfield | `init-spoke [spoke_path] --name --archetype --type --mode --sync --bootstrap` |
| Máy mới, đã có `workspace_context.yaml` | `bootstrap-spoke --create-venv` qua `$CCBA_HUB_PATH` hoặc `$env:CCBA_HUB_PATH` |
| Brownfield | `adopt-spoke <path>` trên unified CLI. `--spoke` thuộc `scripts/adopt_spoke.py` |
| Downstream | Unified `sync-spoke` có `--apply`, `--all`, `--sync-item`, `--bootstrap`, `--verify`, `--pull-assets`, `--force`, `--dry-run`, `--include-sandboxes` |
| Wrapper sync | `scripts/spoke/sync/cli.py` giữ `--spoke`, `--rollback` / `--undo`, `--list-backups`, `--ignore-dirty`, `--no-backup`, `--allow-stale-catalog` |

`ccba-update-spoke` đã viết các ví dụ rollback trên `scripts/sync_spoke.py`. PR 5C giữ các ví dụ đó trên wrapper. `ccba-init-spoke` bước 2–3 hiện trỏ `sync_spoke.py` và `scripts/spoke/spoke_bootstrap.py` qua `[hub_path]`. Sổ tay đưa hai bước đó về `init-spoke --sync --bootstrap`, hoặc về `sync-spoke` / `bootstrap-spoke` khi chạy tách.

`argument-hint` của `ccba-spoke-adopter` hiện là `[--spoke <path>]`. Cùng PR 5C, hint chuyển thành tham số vị trí và ghi `--spoke` là mặt của `scripts/adopt_spoke.py`.

## 3. Đường máy và IP

Các chỗ còn lại trên tám skill:

| Vị trí | Việc trong PR sở hữu |
| :--- | :--- |
| `ccba-init-spoke/SKILL.md` bước 2–3 | `$CCBA_HUB_PATH` và `$env:CCBA_HUB_PATH` |
| `ccba-init-spoke/references/server_deployment.md` dòng 15 | Biến `AI_GATEWAY_URL` |
| `ccba-spoke-adopter/SKILL.md` ba khối `adopt_spoke.py` | Env path, mặt lệnh COND-03 |
| `ccba-contribute-to-hub/SKILL.md` dòng 62 (`<hub_path>`), 112, 146–147 | Env path. Hai lệnh `gh pr create` đầy đủ |
| `ccba-issue-to-hub/SKILL.md` dòng 65 | Catalog qua `$CCBA_HUB_PATH/.agents/skills/platform-loader/catalog.yaml` |
| `ccba-platform/SKILL.md` dòng 48–49 và cột `[hub_path]/...` | `AI_GATEWAY_URL`, rồi `$CCBA_HUB_PATH` / `$env:CCBA_HUB_PATH` |

`AI_GATEWAY_URL` trong `.env.example` là URL đầy đủ của gateway. Client đọc biến này. Dòng Tailscale bỏ octet và trỏ cùng biến gateway. Chú thích `# ccba:allow-raw-ip` không xuất hiện trong Markdown của đợt.

`platform-loader` và phần lớn `ccba-update-spoke` đã dùng env. PR của chúng thêm đoạn posture và giữ bảng chỉ mục, bảng Level 3.

## 4. Năm PR và khóa hoàn tất

Không có tệp dùng chung giữa năm PR. `name`, `tier`, `command`, `triggers`, `description`, `bundle` và khối `gpi` đứng yên, nên `compile_catalog.py --check` và `check_skills_docs_in_sync` đọc frontmatter mà vẫn xanh. Thân Markdown, nơi đặt đoạn posture, không đi vào `catalog.yaml`.

| PR | File | Việc |
| :--- | :--- | :--- |
| **5A** | `platform-loader/SKILL.md` | Đoạn `seam-exempt`. Giữ GPI 17.5 và bảng ba chỉ mục. |
| **5B** | `ccba-platform/SKILL.md` | Đoạn `seam-exempt`. Giữ orchestrator, năm bối cảnh, dòng `python -m ccba_harness verify-patch`. Gỡ IP và `[hub_path]`. |
| **5C** | `ccba-init-spoke`, `references/server_deployment.md`, `ccba-spoke-adopter`, `ccba-update-spoke` | Đoạn `seam-exempt`. Sổ lệnh COND-03. Env path. Gỡ IP. Giữ bảng Level 3. |
| **5D** | `ccba-sync-upstream/SKILL.md` | Đoạn `seam-exempt`. Giữ GPI 20.5, script radar, phạm vi Hub. |
| **5E** | `ccba-contribute-to-hub`, `ccba-issue-to-hub` | Đoạn `seam-exempt`. Giữ \((3,3,1,1)\). Env path. Hai lệnh `gh pr create`. Giữ bảng Level 3. |

5C chạy bộ ba lệnh trên từng skill trong ba thư mục. 5E chạy bộ ba lệnh trên từng skill trong hai thư mục. `validate_skills.py` đã gọi hygiene, catalog sync và skills-docs sync. `verify-patch --preset skill` thêm `compile_catalog.py --check` và `sync_hub_adr_matrix.py --check`.

Bốn skill có `references/` đã có bảng Level 3 trỏ đúng tệp hiện có: `interactive_wizard.md`, `server_deployment.md`, `upstream_sync_guide.md`, `propose_to_hub.md`, `proposal_review_sop.md`, `issue_triage_flow.md`, `agent-brief.md`, `out-of-scope.md`. Các bảng đó đứng yên.

Mẫu RED của hygiene (`$(...)`, `export VAR=`, `sudo apt`, `grep` có cờ, `awk`, `head -n`, `2>/dev/null`, `xargs`) ở ngoài fence có nhãn `linux`. Sổ tay chạy trên PowerShell giữ khối POSIX và khối PowerShell song song. `scripts/ccba-init-spoke/scripts/template.sh` có `$(tput ...)` và `2>/dev/null`. Hygiene chỉ quét `*.md`. File shell này đứng ngoài đợt.

Đứng ngoài năm PR: `scripts/ccba_platform_cli.py`, `scripts/spoke/upstream_evaluator.py`, `catalog.yaml`, `seam-contracts.yaml`, `packages/`, `ccba-create-pr`, `ccba-git-guardrails`, `ccba-release-feature`, `ccba-graduate-rd`.

Sau khi cả năm PR xanh trên đĩa, đệ trình nghiệm thu Đợt 5.