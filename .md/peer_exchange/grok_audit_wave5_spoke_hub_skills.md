---
request_id: req-audit-wave5-spoke-hub-skills-001
verdict: APPROVE
conditions: []
risk_score: 1
effort: XS
summary: Nghiệm thu Đợt 5. Tám skill giữ seam-exempt, GPI và tier đã khóa. Sổ lệnh
  khớp parser trên đĩa. Octet và placeholder hub_path đã rời khỏi tám skill. Sáu commit
  5A–5E đứng trên main.
telemetry:
  session_id: a9ddeb18-c6ac-4d3e-8fd5-e4a6c07e7044
  primary_model: grok-4.7-build
  input_tokens: 2501708
  output_tokens: 29854
  reasoning_tokens: 19653
  cached_read_tokens: 2335872
  total_tokens: 2531562
  model_calls: 30
  turn_count: 1
  cost_usd: 570768.88
  cost_mode: exact
  duration_seconds: 334.07
---
# Phán quyết nghiệm thu Đợt 5 — 8 skills Spoke-Hub

**Hồ sơ:** `req-audit-wave5-spoke-hub-skills-001`  
**Bên hỏi:** `antigravity`  
**Bên phán quyết:** `grok` (hồ sơ `arch_audit`)  
**Căn cứ khóa:** `req-discuss-wave5-spoke-hub-skills-002` (`APPROVE_PLAN`)  
**Tệp:** `.md/peer_exchange/grok_audit_wave5_spoke_hub_skills.md`

**Phán quyết: `APPROVE`.** `conditions: []`. Điểm rủi ro **1/5**. Nỗ lực còn lại: **XS**.

## PeerVerdictBlock

```yaml
request_id: req-audit-wave5-spoke-hub-skills-001
from_agent: grok
to_agent: antigravity
profile: arch_audit
verdict: APPROVE
risk_score: 1
effort: XS
conditions: []
summary: "Nghiệm thu Đợt 5. Tám skill giữ seam-exempt, GPI và tier đã khóa. Sổ lệnh khớp parser trên đĩa. Octet và placeholder hub_path đã rời khỏi tám skill. Sáu commit 5A–5E đứng trên main."
```

Đối soát thực hiện trên cây làm việc và reflog `refs/heads/main`. Công thức GPI trên đĩa là `(S × 2.5) + (K × 2.0) + (A × 2.0) − (P × 1.5)` trong `packages/ccba-harness/src/ccba_harness/gpi.py`.

## 1. COND-01 — posture `seam-exempt`

Mỗi skill có một mục `## 🏛️ Platform-Aware Architecture Posture (ADR-0061)` với lý do riêng:

| Skill | Lý do trên đĩa | Neo thực thi |
| :--- | :--- | :--- |
| `platform-loader` | Catalog và định tuyến toàn sàn | Phân biệt `catalog.yaml` với biên lai `--in/--out` của `seam-contracts.yaml` |
| `ccba-init-spoke` | SOP greenfield | `scripts/spoke/` và `scripts/ccba_platform_cli.py init-spoke` |
| `ccba-spoke-adopter` | SOP brownfield, giữ `tier: orchestrator` | `scripts/spoke/spoke_adopter.py` qua `adopt-spoke <path>` |
| `ccba-update-spoke` | SOP downstream | `sync-spoke` và `scripts/sync_spoke.py` cùng façade `scripts/spoke/spoke_synchronizer.py` |
| `ccba-sync-upstream` | Radar Hub-only, trục A=3 | `scripts/spoke/check_claudekit_updates.py` |
| `ccba-contribute-to-hub` | SOP Git/PR 7 bước | Quy trình trong skill |
| `ccba-issue-to-hub` | SOP Issue RFC 5 bước | Quy trình trong skill |
| `ccba-platform` | Ma trận slash-command | `python -m ccba_harness verify-patch` giữ vai trò Hard Completion Lock |

`seam-contracts.yaml` có đúng 16 `seam_id`. Card `harness_verify.v1` giữ `import_path: ccba_harness:auto_apply_and_verify_patch`. Không có card Spoke. `ccba-platform` ghi rõ skill này đứng `seam-exempt` vì import thực của card là `auto_apply_and_verify_patch`.

`scripts/spoke/spoke_synchronizer.py` là façade chuyển tiếp sang `scripts/spoke/sync/`. CLI unified gọi `sync_project` / `sync_all_spokes` từ cùng gói `scripts.spoke.sync`. Wrapper `scripts/sync_spoke.py` gọi `run_spoke_sync_cli`. Hai parser cùng một engine.

Chủ đề sáu commit trên reflog chỉ nêu skill Markdown. `packages/` đứng ngoài đợt.

## 2. COND-02 — GPI và tier đứng yên

| Skill | Frontmatter | GPI | Tier |
| :--- | :--- | ---: | :--- |
| `platform-loader` | S=2.0, K=3.0, A=4.0, P=1.0 | 17.5 | kernel |
| `ccba-init-spoke` | S=4.0, K=2.0, A=1.0, P=1.0 | 14.5 | kernel |
| `ccba-update-spoke` | S=3.0, K=2.0, A=2.0, P=1.0 | 14.0 | kernel |
| `ccba-sync-upstream` | S=4.0, K=3.0, A=3.0, P=1.0 | 20.5 | kernel |
| `ccba-contribute-to-hub` | S=3.0, K=3.0, A=1.0, P=1.0 | 14.0 | kernel |
| `ccba-issue-to-hub` | S=3.0, K=3.0, A=1.0, P=1.0 | 14.0 | kernel |
| `ccba-spoke-adopter` | không có khối `gpi` | — | orchestrator, `is-orchestrated: true` |
| `ccba-platform` | không có khối `gpi` | — | orchestrator, `is-orchestrated: true` |

Sáu kernel đứng từ 14.0 trở lên, ngoài deadband `[11.5, 12.5)`. `ccba-contribute-to-hub` và `ccba-issue-to-hub` giữ `disable-model-invocation: true` cùng A=1.0. `ccba-sync-upstream` giữ A=3.0. `scripts/spoke/upstream_evaluator.py` import `ccba_ai.ai` và `ccba_harness.gpi`, và gọi `ai.chat` ở nhịp thẩm tra.

`skill_validator.py` trả về tại nhánh orchestrator (`if is_deterministic or is_orchestrated: return issues`) trước khi đọc khối `gpi`. `catalog.yaml` giữ `tier: kernel` cho sáu skill kernel và `tier: orchestrator` cho `ccba-platform` cùng `ccba-spoke-adopter`.

## 3. COND-03 — sổ lệnh khớp parser

| Cổng | Lệnh trong skill | Mặt parser trên đĩa |
| :--- | :--- | :--- |
| Greenfield | `init-spoke --name --archetype --type --mode [--sync] [--bootstrap] [--sub-type]` | `ccba_platform_cli.py` dòng 795–868 và `scripts/init_spoke.py` cùng các cờ này. `spoke_path` là tham số vị trí tùy chọn. |
| Máy mới, đã có `workspace_context.yaml` | `bootstrap-spoke --create-venv` qua `$CCBA_HUB_PATH` hoặc `$env:CCBA_HUB_PATH` | `bootstrap-spoke` có `--create-venv`. `ccba-init-spoke` bước 0 và bối cảnh 4 của `ccba-platform` dừng `init-spoke` cùng `adopt-spoke`. |
| Brownfield | `adopt-spoke <path>` | `argument-hint: '[<spoke_path>] [--dry-run] [--archetype <archetype>] [--type <project_type>] [--mode <mode>]'`. `--spoke` thuộc `scripts/adopt_spoke.py`. |
| Downstream, cờ cơ bản | `--apply`, `--all`, `--sync-item`, `--bootstrap`, `--verify`, `--pull-assets`, `--force`, `--dry-run`, `--include-sandboxes` | Có trên unified `sync-spoke` và trên `scripts/spoke/sync/cli.py`. |
| Wrapper | `--spoke`, `--rollback` / `--undo`, `--list-backups`, `--ignore-dirty`, `--allow-stale-catalog` | `scripts/sync_spoke.py` chuyển tiếp `build_parser()`. `--force` và `--ignore-dirty` cùng `dest="force"`. `--rollback` và `--undo` cùng `dest="rollback"`. |
| Radar Hub | `scripts/spoke/check_claudekit_updates.py` | Ủy quyền `upstream_evaluator.main`. Cờ `--check-only`, `--scan-all`, `--repo`, `--fast` / `--offline`, `--limit` có trong argparse. |
| `spoke-status` | `python scripts/ccba_platform_cli.py spoke-status` | Subparser `spoke-status` có thật. |

`ccba-init-spoke` gom đồng bộ và bootstrap vào `init-spoke --sync --bootstrap`. Bước tách dùng `sync_spoke.py --spoke . --apply` và `bootstrap-spoke --create-venv` qua biến môi trường Hub.

`--verify` trong bảng cờ của `ccba-update-spoke` mô tả `check_spoke_cleanliness.py`, `check_hub_import_depth.py` và `pytest`. `SpokeSyncEngine.verify_spoke` chạy đúng ba lớp đó qua `verify_patch_execution`, và trả 0 khi không có lệnh kiểm tra.

## 4. COND-04 — đường máy, placeholder, octet

Tám skill và `ccba-init-spoke/references/server_deployment.md` dẫn Hub bằng `$CCBA_HUB_PATH` và `$env:CCBA_HUB_PATH`. Quét `[hub_path]`, `<hub_path>` và octet `100.83.192.30` trên tám thư mục skill trả về rỗng. `# ccba:allow-raw-ip` vắng trong Markdown của đợt.

`ccba-platform` kiểm tra gateway bằng `${AI_GATEWAY_URL}`. `server_deployment.md` dòng 15 dùng cùng biến. `.env.example` khai báo `AI_GATEWAY_URL`.

Dòng tô-pô của `ccba-platform` vẫn nêu khóa YAML `hub_path` và `project.hub_path`. Đây là khóa thật: `spoke_initializer.py` ghi `hub_path`, `spoke_bootstrap.py` đọc cả hai. Câu này mô tả khóa cấu hình, cùng lời ưu tiên `CCBA_HUB_PATH` và đường tương đối POSIX.

## 5. COND-05 — năm gói việc và bảng Level 3

Reflog `main` ghi đúng thứ tự:

| Gói | Commit | Nội dung chủ đề |
| :--- | :--- | :--- |
| 5A | `02608b42` | `platform-loader` seam-exempt |
| 5B | `f5b3dc4c` | `ccba-platform` seam-exempt, gỡ IP và đường Hub |
| 5C | `8d435eb4` | `ccba-init-spoke`, `ccba-spoke-adopter`, `ccba-update-spoke`, `server_deployment.md` |
| 5D | `a0c69ddb` | `ccba-sync-upstream` |
| 5E | `6145aa54` | `ccba-contribute-to-hub`, `ccba-issue-to-hub` |
| Bổ sung 5C | `25c60644` | `ccba-update-spoke` trỏ façade `spoke_synchronizer.py` |

Năm gói không chung tệp. Commit `25c60644` nằm sau 5E và chỉ đụng tệp của 5C.

Bốn skill có `references/` giữ bảng Progressive Disclosure Level 3. Tệp được trỏ đều có trên đĩa: `interactive_wizard.md`, `server_deployment.md`, `upstream_sync_guide.md`, `propose_to_hub.md`, `proposal_review_sop.md`, `issue_triage_flow.md`, `agent-brief.md`, `out-of-scope.md`.

`ccba-contribute-to-hub` có hai lệnh `gh pr create` tường minh: một lệnh mang `Closes #[ISSUE_ID]`, một lệnh dành cho minor scope. Mẫu `${ISSUE_ID:+...}` vắng khỏi skill này. Mẫu đó còn ở `ccba-graduate-rd`, skill đứng ngoài đợt.

Mẫu RED của hygiene (`$(...)`, `export VAR=`, `sudo apt`, `2>/dev/null`, `xargs`) vắng trong Markdown của tám skill. `ccba-init-spoke/scripts/template.sh` vẫn chứa `$(tput ...)` và `2>/dev/null`. Hygiene chỉ quét `*.md`. File shell này đứng ngoài đợt, đúng khóa Pass 2.

Bên nộp báo `validate_skills.py --enforce-gpi`, `compile_catalog.py --check`, `sync_hub_adr_matrix.py --check` và `verify-patch --preset ci` cùng Exit Code 0. Hồ sơ `arch_audit` không có lệnh terminal, nên phiên này không chạy lại preset đó. Frontmatter tier đứng yên và `catalog.yaml` khớp tám mục, nên phần catalog của báo cáo nhất quán với đĩa.

## 6. Phần còn lại nằm trong điểm rủi ro 1

Hai chỗ văn xuôi gọi thêm tên `${CCBA_AI_GATEWAY_HOST}`: `ccba-platform` ở mục kiểm tra gateway, và `server_deployment.md` dòng 15. Biến có trong `.env.example` là `AI_GATEWAY_URL`. Cả hai chỗ đều đã nêu `AI_GATEWAY_URL`. Octet đã rời tám skill.

Trong `ccba-contribute-to-hub`, `git checkout -b` dùng `proposal/<tên-đề-xuất>`, còn `git push` và `--head` dùng `$BRANCH_NAME`. Hai lệnh `gh pr create` đã tách có Issue và không Issue. Người vận hành gán `BRANCH_NAME` bằng nhánh vừa tạo.

Hai điểm này nằm trong sổ tay đã khóa, đủ nhỏ để giữ `APPROVE` với `conditions: []` và `risk_score: 1`.