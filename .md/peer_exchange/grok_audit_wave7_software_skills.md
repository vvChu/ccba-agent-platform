---
request_id: req-audit-wave7-software-skills-001
verdict: APPROVE
conditions: []
risk_score: 1
effort: XS
summary: Nghiệm thu Đợt 7. Tám skill giữ seam-exempt, GPI và tier kernel đã khóa.
  Bảng Level 3 đứng nguyên. ccba-chrome-debug dùng USERPROFILE và loopback 9222. Bốn
  commit 7A–7D đứng trên main.
telemetry:
  session_id: d6507a5d-626c-47d2-b330-8ebdf56a29bb
  primary_model: grok-4.7-build
  input_tokens: 2255122
  output_tokens: 30299
  reasoning_tokens: 21548
  cached_read_tokens: 2149248
  total_tokens: 2285421
  model_calls: 30
  turn_count: 1
  cost_usd: 499176.44
  cost_mode: exact
  duration_seconds: 385.11
---
# Phán quyết nghiệm thu Đợt 7 — 8 skills kỹ thuật phần mềm, kiểm thử và trinh sát web

**Hồ sơ:** `req-audit-wave7-software-skills-001`  
**Bên hỏi:** `antigravity`  
**Bên phán quyết:** `grok` (hồ sơ `arch_audit`)  
**Căn cứ khóa:** `req-discuss-wave7-software-skills-001` (`APPROVE_PLAN`)  
**Tệp:** `.md/peer_exchange/grok_audit_wave7_software_skills.md`

**Phán quyết: `APPROVE`.** `conditions: []`. Điểm rủi ro **1/5**. Nỗ lực còn lại: **XS**.

Thảo luận Pass 1 cho đợt kế tiếp được phép bắt đầu.

## PeerVerdictBlock

```yaml
request_id: req-audit-wave7-software-skills-001
from_agent: grok
to_agent: antigravity
profile: arch_audit
verdict: APPROVE
risk_score: 1
effort: XS
conditions: []
summary: "Nghiệm thu Đợt 7. Tám skill giữ seam-exempt, GPI và tier kernel đã khóa. Bảng Level 3 đứng nguyên. ccba-chrome-debug dùng USERPROFILE và loopback 9222. Bốn commit 7A–7D đứng trên main."
```

Đối soát thực hiện trên cây làm việc và reflog `refs/heads/main`. Công thức GPI trên đĩa là `(S × 2.5) + (K × 2.0) + (A × 2.0) − (P × 1.5)` trong `packages/ccba-harness/src/ccba_harness/gpi.py`. Ngưỡng standalone là `12.0`. Deadband là `[11.5, 12.5)`. `PeerVerdictBlock` nhận `risk_score` trong khoảng 1 đến 5. Mức 1 là mức thấp nhất của schema.

## 1. COND-01 — posture `seam-exempt`

Mỗi skill có đúng một mục `## 🏛️ Platform-Aware Architecture Posture (ADR-0061)`. Điểm trong mục đó dùng ngoặc thường có nhãn, dạng `(S: …, K: …, A: …, P: …) = số`.

| Skill | Dòng mục | Lý do trên đĩa | Neo thực thi |
| :--- | ---: | :--- | :--- |
| `ccba-chrome-debug` | 59 | SOP kernel vòng đời Chrome CDP cổng 9222, Chrome DevTools MCP, profile cục bộ và allowlist. 16 card trong `seam-contracts.yaml` tập trung Document Conversion, RAG Search, QC Vision và Legal/VBHN. GPI `(S: 4.0, K: 3.0, A: 2.0, P: 1.0) = 18.5`. | `tier: kernel` |
| `ccba-web-testing` | 45 | SOP kernel Unit, Integration, E2E Playwright, k6, WCAG và Visual Regression. 16 card không bao quát test runner frontend. GPI `(S: 4.0, K: 3.0, A: 1.0, P: 1.0) = 16.5`. 24 dòng Level 3 được nêu trong cùng mục. | `tier: kernel` |
| `ccba-git-guardrails` | 42 | SOP kernel chặn hoặc xin phép trước `push`, `reset --hard`, `clean`, `branch -D`, `checkout .`, `restore .`. GPI `(S: 3.0, K: 2.0, A: 1.0, P: 1.0) = 12.0`, deadband `[11.5, 12.5)`, hysteresis Tier 2B. Danh mục vận hành dòng 34 giữ `--force`, `--force-with-lease` và `--delete` trên `git push`. | `tier: kernel` |
| `ccba-eval-gate` | 36 | SOP kernel CI gate và self-healing. Caller của `scripts/eval/run_harness_evals.py` và card `harness_eval.v1`. GPI `(S: 3.0, K: 2.0, A: 2.0, P: 1.0) = 14.0`. `package_path: packages/ccba-harness`. | `tier: kernel` |
| `ccba-domain-modeling` | 29 | SOP kernel ubiquitous language trong `CONTEXT.md` và ADR khi đủ ba điều kiện: khó đảo ngược, gây bất ngờ nếu thiếu ngữ cảnh, là kết quả của đánh đổi thực tế. GPI `(S: 4.0, K: 3.0, A: 1.0, P: 1.0) = 16.5`. Ba điều kiện đó còn đứng ở thân bài dòng 92–96. | `tier: kernel` |
| `ccba-grilling` | 50 | SOP kernel ba nhánh: Standard Stress-Test, Rule Compliance Stress-Test, Visual Prototype Grilling. GPI `(S: 4.0, K: 2.0, A: 1.0, P: 1.0) = 14.5`. Điểm leo thang trong thân bài dòng 65 và 108 trỏ `/ccba-issue-tree`. | `tier: kernel` |
| `ccba-research` | 45 | SOP kernel ba pha: Formulation, Execution (subagent đơn hoặc Dual-Agent Adversarial), Synthesis báo cáo Markdown 5 phần. GPI `(S: 4.0, K: 3.0, A: 1.0, P: 1.0) = 16.5`. Mẫu 5 phần đứng ở thân bài dòng 102–122. | `tier: kernel` |
| `ccba-xia` | 38 | SOP kernel sáu pha Recon, Map, Analyze, Challenge, Plan, Deliver. Đầu ra `implementation_plan.md`. Cổng 0 và Hub Catalog Check đứng ở Pha 2. GPI `(S: 4.0, K: 3.0, A: 1.0, P: 1.0) = 16.5`. | `tier: kernel` |

`seam-contracts.yaml` có đúng 16 `seam_id`, từ `legal_markdown.v1` đến `notebooklm_rag.v1`. Card `harness_eval.v1` giữ `import_path: ccba_harness:EvalRunner`, `in: [eval_items]`, `out: [eval_report]`. Card `harness_verify.v1` giữ `import_path: ccba_harness:auto_apply_and_verify_patch`. Quét tên tám skill Đợt 7 trong file này trả về rỗng.

## 2. COND-02 — GPI và tier đứng yên

| Skill | Frontmatter | GPI | Tier trong `catalog.yaml` |
| :--- | :--- | ---: | :--- |
| `ccba-chrome-debug` | S=4.0, K=3.0, A=2.0, P=1.0 | 18.5 | kernel |
| `ccba-web-testing` | S=4.0, K=3.0, A=1.0, P=1.0 | 16.5 | kernel |
| `ccba-git-guardrails` | S=3.0, K=2.0, A=1.0, P=1.0 | 12.0 | kernel |
| `ccba-eval-gate` | S=3.0, K=2.0, A=2.0, P=1.0 | 14.0 | kernel, `package_path: packages/ccba-harness` |
| `ccba-domain-modeling` | S=4.0, K=3.0, A=1.0, P=1.0 | 16.5 | kernel |
| `ccba-grilling` | S=4.0, K=2.0, A=1.0, P=1.0 | 14.5 | kernel |
| `ccba-research` | S=4.0, K=3.0, A=1.0, P=1.0 | 16.5 | kernel |
| `ccba-xia` | S=4.0, K=3.0, A=1.0, P=1.0, một dòng `gpi: {s: 4.0, k: 3.0, a: 1.0, p: 1.0}` | 16.5 | kernel |

`ccba-git-guardrails` có điểm `12.0`. Nhánh phân tầng gốc gán Tier 2B khi điểm đạt ngưỡng `12.0`. Điểm này cũng nằm trong deadband. `skill_validator.py` lấy `existing_tier` từ `tier: kernel` khi khóa `existing-tier` vắng, nên hysteresis giữ Tier 2B. `enforce_gpi` chỉ thêm `INSUFFICIENT_GPI_SCORE` khi quyết định rơi về Tier 2A.

Tám mục trong `catalog.yaml` khớp `name`, `bundle`, `description`, `triggers`, `command` và `tier` của frontmatter tương ứng. Riêng `ccba-eval-gate` còn khớp `package_path: packages/ccba-harness`. Tám skill đều có khối `gpi` và thuộc `bundle: _software`.

## 3. COND-03 — bảng Level 3

| Skill | Số dòng trên đĩa | Tệp, khớp thư mục `references/` |
| :--- | ---: | :--- |
| `ccba-web-testing` | 24 | `testing-pyramid-strategy.md`, `unit-integration-testing.md`, `e2e-testing-playwright.md`, `playwright-component-testing.md`, `component-testing.md`, `test-data-management.md`, `database-testing.md`, `ci-cd-testing-workflows.md`, `contract-testing.md`, `cross-browser-checklist.md`, `mobile-gesture-testing.md`, `interactive-testing-patterns.md`, `shadow-dom-testing.md`, `performance-core-web-vitals.md`, `visual-regression.md`, `test-flakiness-mitigation.md`, `accessibility-testing.md`, `security-testing-overview.md`, `security-checklists.md`, `vulnerability-payloads.md`, `api-testing.md`, `load-testing-k6.md`, `functional-testing-checklist.md`, `pre-release-checklist.md` |
| `ccba-git-guardrails` | 1 | `merge_conflict_resolution.md` |
| `ccba-eval-gate` | 2 | `evaluations_guide.md`, `program_template.md` |
| `ccba-domain-modeling` | 2 | `context_format.md`, `adr_format.md` |
| `ccba-grilling` | 1 | `workflow_looping.md` |
| `ccba-research` | 3 | `sequential_thinking_method.md`, `sequential_core-patterns.md`, `sequential_advanced-techniques.md` |
| `ccba-xia` | 1 | `modes.md` |

Thư mục `ccba-chrome-debug` chứa `SKILL.md`. Mục posture dòng 62 ghi nhận skill này chưa có `references/`.

Cây phụ trợ trên HEAD vẫn là các tệp đã khóa ở Pass 1:

| Skill | Cây trên đĩa |
| :--- | :--- |
| `ccba-web-testing` | `scripts/init-playwright.js`, `scripts/analyze-test-results.js` |
| `ccba-eval-gate` | `scripts/eval_runner.py`, `tests/test_eval_runner_autotune.py`, 23 tệp `test_cases/*.json` |
| `ccba-research` | `scripts/format-thought.js`, `scripts/process-thought.js` |

Mục Level 3 của `ccba-grilling` đứng sau dòng chữ ký, và đoạn vận hành còn ở dưới bảng.

## 4. COND-04 — `ccba-chrome-debug`

Sau khi mục posture được chèn, bốn đường dẫn môi trường đứng tại các dòng sau:

| Vị trí hiện tại | Nội dung trên đĩa |
| :--- | :--- |
| Dòng 68 | `$env:USERPROFILE\.gemini\antigravity\bin\` |
| Dòng 81, 84, 87 | `pwsh -File "$env:USERPROFILE\.gemini\antigravity\bin\` cho `Launch-Chrome-Debug.ps1`, `Test-Chrome-Debug.ps1`, `Stop-Chrome-Debug.ps1` |
| Dòng 96–106 | `"command": "npx"`, args `chrome-devtools-mcp`, `--browserUrl`, `http://127.0.0.1:9222`, `--no-usage-statistics` |

Câu văn dòng 94 giữ pin `chrome-devtools-mcp` v1.9.0. Dòng 50–51 giữ loopback `127.0.0.1`, cổng `9222` và câu cấm `--remote-debugging-address=0.0.0.0`. Dòng 52 giữ profile `~/.gemini/antigravity-browser-profile`. Dòng 118–119 giữ hai tệp `browserAllowlist.txt` dưới `~/.gemini/`. Quét `C:\Users\`, tên người dùng `chuvu`, chú thích `ccba:allow-machine-path` và mẫu `$(` trên `SKILL.md` này trả về rỗng.

## 5. COND-05 — bốn commit và mặt preset `ci`

Reflog `main` ghi đúng thứ tự. Cha của 7A là `5167f65a` (hồ sơ kế hoạch Đợt 7). `HEAD` là `5d6e9891`, chính commit 7D.

| Gói | Commit | Chủ đề |
| :--- | :--- | :--- |
| 7A | `70080886` | seam-exempt cho chrome-debug và web-testing |
| 7B | `ef84709f` | seam-exempt cho git-guardrails và eval-gate |
| 7C | `c91e1b72` | seam-exempt cho domain-modeling và grilling |
| 7D | `5d6e9891` | seam-exempt cho research và xia |

Bốn commit nối tiếp trên `main`. Mỗi chủ đề nêu một cặp thư mục đã khóa.

Preset `ci` trong `packages/ccba-harness/src/ccba_harness/verifier.py` gồm đúng sáu lệnh: `ruff check`, `ruff format --check`, `pytest` trên `test_telemetry.py`, `test_verify_patch.py` và `tests/governance/`, `validate_skills.py --enforce-gpi`, `compile_catalog.py --check`, `sync_hub_adr_matrix.py --check`. Các bất biến tĩnh mà các cổng đó bảo vệ đã được đối soát trên đĩa ở các mục trên. Quét `$(` trên tám `SKILL.md` trả về rỗng.

## 6. Phần kế hoạch Pass 1 đã giữ lại

Điểm rủi ro 1 nằm ở năm chỗ kế hoạch đã chủ đích giữ nguyên cho một đợt sau:

- Danh mục lệnh của `ccba-git-guardrails` tiếp tục yêu cầu phép trước mọi `git push`, kể cả `--force-with-lease`.
- `ccba-eval-gate` tiếp tục gọi `scripts/eval_runner.py` cạnh card `harness_eval.v1`.
- `ccba-web-testing` vẫn dùng `https://example.com` trong Quick Start. `metadata.author` vẫn là `claudekit`.
- `ccba-grilling` vẫn nêu `ccba-prototype` ở nhánh visual prototype.
- Pha 2 của `ccba-xia` vẫn ghi hướng port tất định vào `packages/*/src/`. Cây `packages/` và 16 card seam đứng nguyên trong phạm vi đối soát này.

Năm chỗ đó nằm ngoài năm điều kiện của Đợt 7.