---
request_id: req-discuss-wave7-software-skills-001
verdict: APPROVE_PLAN
conditions:
- id: COND-01
  description: 'Đã khóa. Tám skill, mỗi skill một mục "## 🏛️ Platform-Aware Architecture
    Posture (ADR-0061)" với lý do đúng thân bài trên đĩa. seam-exempt cho cả tám.
    seam-contracts.yaml giữ 16 seam_id. packages/ đứng ngoài đợt. ccba-eval-gate là
    caller của harness_eval.v1 (ccba_harness:EvalRunner) và scripts/eval/run_harness_evals.py.
    ccba-xia giữ sáu pha và đầu ra implementation_plan.md. ccba-research giữ ba pha.

    '
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-02
  description: 'Đã khóa. Frontmatter name, tier, bundle, command, triggers, description,
    metadata, disable-model-invocation và khối gpi đứng yên. Tám skill giữ tier kernel.
    Điểm giữ nguyên: chrome-debug 18.5, web-testing 16.5, git-guardrails 12.0, eval-gate
    14.0, domain-modeling 16.5, grilling 14.5, research 16.5, xia 16.5. git-guardrails
    đạt ngưỡng >= 12.0 và nằm trong deadband [11.5, 12.5). Validator đọc tier kernel
    làm existing tier. ccba-eval-gate giữ package_path packages/ccba-harness. Khối
    gpi một dòng của ccba-xia giữ nguyên dạng inline.

    '
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-03
  description: 'Đã khóa. Bảng Level 3 đứng nguyên trên đĩa với tên tệp thật. web-testing
    24 dòng. git-guardrails 1 dòng merge_conflict_resolution.md. eval-gate 2 dòng
    evaluations_guide.md và program_template.md. domain-modeling 2 dòng context_format.md
    và adr_format.md. grilling 1 dòng workflow_looping.md. research 3 dòng sequential_thinking_method.md,
    sequential_core-patterns.md, sequential_advanced-techniques.md. xia 1 dòng modes.md.
    ccba-chrome-debug không có references/. references/, scripts/, test_cases/ và
    tests/ đứng ngoài diff của cả bốn PR.

    '
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-04
  description: 'Đã khóa. PR 7A gỡ bốn đường dẫn ổ đĩa gắn tên người dùng trong ccba-chrome-debug/SKILL.md.
    Thư mục bin dùng $env:USERPROFILE\.gemini\antigravity\bin\. Ba lệnh pwsh -File
    dùng cùng tiền tố. Khối JSON chrome-devtools dùng command npx, args chrome-devtools-mcp,
    --browserUrl, http://127.0.0.1:9222, --no-usage-statistics. Câu văn giữ pin v1.9.0.
    Giữ loopback 127.0.0.1, cổng 9222 và các đường ~/.gemini/. Không thêm ccba:allow-machine-path.

    '
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-05
  description: 'Đã khóa. Bốn PR song song 7A–7D, bốn cặp thư mục tách biệt. Mỗi SKILL.md
    khóa bằng validate_skills.py --file --enforce-gpi, audit_skills_hygiene.py --file,
    và verify-patch --preset skill --target. Sau khi cả bốn PR có trên đĩa, chạy verify-patch
    --preset ci. Đoạn posture viết điểm dạng (S, K, A, P) = số. catalog.yaml đứng
    ngoài bốn PR.

    '
  blocking: false
  source_profile: arch_audit
  source_profiles: []
risk_score: 2
effort: M
summary: Kế hoạch Đợt 7 được phép bắt đầu. Tám skill nhận seam-exempt. GPI, tier và
  16 card seam đứng yên. Bốn PR song song. Lý do và bảng Level 3 khóa theo tệp đang
  có trên đĩa. PR 7A gỡ đường dẫn Windows gắn tên người dùng trong ccba-chrome-debug.
telemetry:
  session_id: 69cab501-1a78-4248-956a-5d4ca0538156
  primary_model: grok-4.7-build
  input_tokens: 751382
  output_tokens: 27477
  reasoning_tokens: 19376
  cached_read_tokens: 663040
  total_tokens: 778859
  model_calls: 14
  turn_count: 1
  cost_usd: 228842.44
  cost_mode: exact
  duration_seconds: 331.08
---
## PeerVerdictBlock

```yaml
peer_verdict:
  request_id: "req-discuss-wave7-software-skills-001"
  from_agent: "grok"
  to_agent: "antigravity"
  profile: "arch_audit"
  pass: 1
  verdict: APPROVE_PLAN
  risk_score: 2
  authorized_start: allowed
  dag:
    parallel: ["7A", "7B", "7C", "7D"]
    after: {}
  lock:
    - "python scripts/validate_skills.py --file <SKILL.md> --enforce-gpi"
    - "python scripts/governance/audit_skills_hygiene.py --file <skill_dir>"
    - "python -m ccba_harness verify-patch --preset skill --target <SKILL.md>"
  floor: "python -m ccba_harness verify-patch --preset ci"
  rationale: >
    Tám skill là SOP kernel trong bundle _software. seam-contracts.yaml có 16 seam_id.
    Card harness_eval.v1 trỏ ccba_harness:EvalRunner. Tám GPI đều >= 12.0.
    ccba-git-guardrails đạt 12.0, đúng ngưỡng Tier 2B và nằm trong deadband.
    Bốn PR không chung tệp. Lý do posture và tên Level 3 lấy từ thân bài trên đĩa.
    PR 7A gỡ đường dẫn ổ đĩa gắn tên người dùng trong ccba-chrome-debug.
```

Phán quyết: **APPROVE_PLAN**. Bốn PR song song được phép bắt đầu. Điểm rủi ro **2/5**. Phần rủi ro còn lại nằm ở kỷ luật khi chép lý do posture và khi sửa đường dẫn trong `ccba-chrome-debug`, đã khóa trong năm điều kiện `blocking: false` ở trên.

Tệp: `.md/peer_exchange/grok_discuss_wave7_software_skills.md`

## 1. Đối soát trên đĩa

`seam-contracts.yaml` có đúng 16 `seam_id`, từ `legal_markdown.v1` đến `notebooklm_rag.v1`. Card `harness_eval.v1` có `import_path: ccba_harness:EvalRunner`, `in: [eval_items]`, `out: [eval_report]`. Card `harness_verify.v1` giữ `import_path: ccba_harness:auto_apply_and_verify_patch`. Tên tám skill Đợt 7 không có trong file này.

Công thức trong `packages/ccba-harness/src/ccba_harness/gpi.py` là `(S × 2.5) + (K × 2.0) + (A × 2.0) − (P × 1.5)`. `GPI_STANDALONE_THRESHOLD` là 12.0. Deadband là `[11.5, 12.5)`. Tám số trên đĩa khớp frontmatter:

| Skill | `(S, K, A, P)` | GPI | Tier trên đĩa |
| :--- | :--- | :---: | :--- |
| `ccba-chrome-debug` | `(4.0, 3.0, 2.0, 1.0)` | 18.5 | `kernel` |
| `ccba-web-testing` | `(4.0, 3.0, 1.0, 1.0)` | 16.5 | `kernel` |
| `ccba-git-guardrails` | `(3.0, 2.0, 1.0, 1.0)` | 12.0 | `kernel` |
| `ccba-eval-gate` | `(3.0, 2.0, 2.0, 1.0)` | 14.0 | `kernel` |
| `ccba-domain-modeling` | `(4.0, 3.0, 1.0, 1.0)` | 16.5 | `kernel` |
| `ccba-grilling` | `(4.0, 2.0, 1.0, 1.0)` | 14.5 | `kernel` |
| `ccba-research` | `(4.0, 3.0, 1.0, 1.0)` | 16.5 | `kernel` |
| `ccba-xia` | `(4.0, 3.0, 1.0, 1.0)` | 16.5 | `kernel` |

Nhánh phân tầng gốc gán Tier 2B khi điểm `>= 12.0`. Điểm 12.0 của `ccba-git-guardrails` đã là Tier 2B trước hysteresis. Deadband cũng chứa 12.0. `SkillValidator` lấy `existing_tier` từ `tier: kernel` khi frontmatter không có khóa `existing-tier`. Khóa đó tiếp tục vắng. Hệ số và `tier` đứng yên.

Tám skill đều có khối `gpi` và không có `is-orchestrated`. Cổng 1 đọc cờ frontmatter. Thân bài có HITL hoặc subagent vẫn giữ `tier: kernel` trong đợt này. `compile_catalog.py` kéo `name`, `bundle`, `description`, `triggers`, `command`, `package_path`, `tier`. Mục posture nằm trong thân Markdown. `catalog.yaml` giữ nguyên khi các khóa đó đứng yên. Entry `ccba-eval-gate` đã có `package_path: packages/ccba-harness`.

## 2. COND-01 — tám lý do `seam-exempt`

Mỗi `SKILL.md` nhận một mục `## 🏛️ Platform-Aware Architecture Posture (ADR-0061)`, đặt sau tiêu đề H1, một lần. Lý do ghi trên đĩa là lý do của chính skill đó.

| Skill | Lý do ghi trên đĩa |
| :--- | :--- |
| `ccba-chrome-debug` | SOP kernel vòng đời Chrome CDP cổng 9222, Chrome DevTools MCP và profile cục bộ. GPI `(4.0, 3.0, 2.0, 1.0) = 18.5`. Caller của công cụ trình duyệt. 16 card không có card browser. |
| `ccba-web-testing` | SOP kernel kiểm thử web với Vitest, Playwright và k6, kèm a11y. GPI `(4.0, 3.0, 1.0, 1.0) = 16.5`. 24 dòng Level 3 đứng nguyên. |
| `ccba-git-guardrails` | SOP kernel chặn lệnh git hủy diệt cho đến khi người dùng cho phép: `git push` kể cả `--force` và `--force-with-lease`, `git reset --hard`, `git clean`, `git branch -D`, `git checkout .` và `git restore .`. GPI `(3.0, 2.0, 1.0, 1.0) = 12.0`, đạt Tier 2B và nằm trong deadband. |
| `ccba-eval-gate` | SOP kernel CI gate và self-healing. GPI `(3.0, 2.0, 2.0, 1.0) = 14.0`. Caller của `scripts/eval/run_harness_evals.py` và card `harness_eval.v1`. `package_path` giữ `packages/ccba-harness`. |
| `ccba-domain-modeling` | SOP kernel ngôn ngữ ubiquitous, `CONTEXT.md` và ADR khi đủ ba điều kiện trên đĩa. GPI `(4.0, 3.0, 1.0, 1.0) = 16.5`. Vòng đời ADR vẫn thuộc `ccba-adr-lifecycle`. |
| `ccba-grilling` | SOP kernel ba nhánh đang có: stress-test, grill-with-docs, visual prototype. GPI `(4.0, 2.0, 1.0, 1.0) = 14.5`. Điểm leo thang trỏ `/ccba-issue-tree`. |
| `ccba-research` | SOP kernel ba pha trên đĩa: phân rã và chọn chế độ, subagent nền, hợp nhất báo cáo 5 phần. GPI `(4.0, 3.0, 1.0, 1.0) = 16.5`. Báo cáo trích nguồn sơ cấp. Thu thập công báo vẫn thuộc các skill legal. |
| `ccba-xia` | SOP kernel sáu pha Recon, Map, Analyze, Challenge, Plan, Deliver. Đầu ra là `implementation_plan.md`. Thi công thuộc `/ccba-implement` hoặc `/ccba-tdd`. GPI `(4.0, 3.0, 1.0, 1.0) = 16.5`. Nội dung repo nguồn là dữ liệu không đáng tin. Đợt này giữ nguyên `packages/` và 16 card. |

Điểm trong đoạn posture viết bằng ngoặc thường: `(4.0, 3.0, 2.0, 1.0) = 18.5`. Mẫu dollar-ngoặc của thay thế lệnh shell đứng ngoài tám `SKILL.md`.

## 3. COND-03 — bảng Level 3

Hygiene trả exit code 1 cho cả YELLOW lẫn RED khi một reference markdown thiếu mặt trong bảng. Bảy bảng sau đứng nguyên. `ccba-chrome-debug` không có thư mục `references/`. Đợt này không tạo thư mục đó.

| Skill | Số dòng trên đĩa | Tệp |
| :--- | :---: | :--- |
| `ccba-web-testing` | 24 | `testing-pyramid-strategy.md`, `unit-integration-testing.md`, `e2e-testing-playwright.md`, `playwright-component-testing.md`, `component-testing.md`, `test-data-management.md`, `database-testing.md`, `ci-cd-testing-workflows.md`, `contract-testing.md`, `cross-browser-checklist.md`, `mobile-gesture-testing.md`, `interactive-testing-patterns.md`, `shadow-dom-testing.md`, `performance-core-web-vitals.md`, `visual-regression.md`, `test-flakiness-mitigation.md`, `accessibility-testing.md`, `security-testing-overview.md`, `security-checklists.md`, `vulnerability-payloads.md`, `api-testing.md`, `load-testing-k6.md`, `functional-testing-checklist.md`, `pre-release-checklist.md` |
| `ccba-git-guardrails` | 1 | `merge_conflict_resolution.md` |
| `ccba-eval-gate` | 2 | `evaluations_guide.md`, `program_template.md` |
| `ccba-domain-modeling` | 2 | `context_format.md`, `adr_format.md` |
| `ccba-grilling` | 1 | `workflow_looping.md` |
| `ccba-research` | 3 | `sequential_thinking_method.md`, `sequential_core-patterns.md`, `sequential_advanced-techniques.md` |
| `ccba-xia` | 1 | `modes.md` |

Đếm 24 của `ccba-web-testing` là đếm đủ hàng của bảng hiện có, và đủ 24 tệp markdown trong `references/`.

Đứng ngoài diff cùng với `references/`:

| Skill | Cây giữ nguyên |
| :--- | :--- |
| `ccba-web-testing` | `scripts/init-playwright.js`, `scripts/analyze-test-results.js` |
| `ccba-eval-gate` | `scripts/eval_runner.py`, `tests/test_eval_runner_autotune.py`, 23 tệp `test_cases/*.json` |
| `ccba-research` | `scripts/format-thought.js`, `scripts/process-thought.js` |

`export const`, `export default` và `export function` trong reference của `ccba-web-testing` là mã JavaScript. Regex RED của hygiene bắt `export NAME=` với dấu bằng dính vào định danh đầu. Các dòng đó đang xanh. Bảng và thư mục reference đứng nguyên nên trạng thái đó được giữ.

Mục Level 3 của `ccba-grilling` nằm sau dòng chữ ký và còn một đoạn vận hành phía dưới bảng. Thứ tự đó đứng nguyên.

## 4. COND-04 — `ccba-chrome-debug`

Trên đĩa còn bốn đường dẫn ổ đĩa gắn tên người dùng, cùng trong một skill:

| Vị trí | Việc trong PR 7A |
| :--- | :--- |
| Câu thư mục bin | `$env:USERPROFILE\.gemini\antigravity\bin\` |
| Ba lệnh `pwsh -File` | Cùng tiền tố cho `Launch-Chrome-Debug.ps1`, `Test-Chrome-Debug.ps1`, `Stop-Chrome-Debug.ps1` |
| JSON `chrome-devtools` | `"command": "npx"` và args `chrome-devtools-mcp`, `--browserUrl`, `http://127.0.0.1:9222`, `--no-usage-statistics` |

Câu văn phía trên fence JSON giữ pin `chrome-devtools-mcp` v1.9.0. Args bỏ cờ `-y`. `npx` phân giải gói đã có trên máy người vận hành.

Giữ nguyên các bất biến đang viết: cổng `9222`, `--remote-allow-origins=*`, loopback `127.0.0.1`, cấm `--remote-debugging-address=0.0.0.0`, profile `~/.gemini/antigravity-browser-profile`, hai tệp `browserAllowlist.txt` dưới `~/.gemini/`. Các đường tilde không mang tên người dùng và không mang chữ cái ổ đĩa.

Scanner machine-path của `check_spoke_cleanliness.py` và `check_hardcoded_parameters.py` quét script Python. Sửa này vẫn thuộc PR 7A vì chính `SKILL.md` đang được mở và rào chắn đường dẫn máy của đợt áp vào file đó. Chú thích `ccba:allow-machine-path` không được thêm vào markdown.

## 5. Bốn PR và khóa hoàn tất

| PR | Tệp | Việc |
| :--- | :--- | :--- |
| **7A** | `ccba-chrome-debug/SKILL.md`, `ccba-web-testing/SKILL.md` | Mục `seam-exempt`. GPI 18.5 và 16.5. COND-04 trên `ccba-chrome-debug`. Giữ 24 dòng Level 3 của `ccba-web-testing`. |
| **7B** | `ccba-git-guardrails/SKILL.md`, `ccba-eval-gate/SKILL.md` | Mục `seam-exempt`. Giữ GPI 12.0 và 14.0. Giữ `package_path` của `ccba-eval-gate`. Giữ 1 dòng và 2 dòng Level 3. |
| **7C** | `ccba-domain-modeling/SKILL.md`, `ccba-grilling/SKILL.md` | Mục `seam-exempt`. Giữ GPI 16.5 và 14.5. Giữ 2 dòng và 1 dòng Level 3. |
| **7D** | `ccba-research/SKILL.md`, `ccba-xia/SKILL.md` | Mục `seam-exempt`. Giữ GPI 16.5 và 16.5. Giữ khối `gpi` inline của `ccba-xia`. Giữ 3 dòng và 1 dòng Level 3. |

7A, 7B, 7C, 7D chạy bộ ba lệnh trên từng `SKILL.md` trong cặp của mình. Với `ccba-git-guardrails`, điểm 12.0 đi nhánh Tier 2B.

Đứng ngoài bốn PR: `packages/`, `seam-contracts.yaml`, `catalog.yaml`, `scripts/` ở gốc repo, `ccba-adr-lifecycle`, toàn bộ `references/`, `scripts/`, `test_cases/` và `tests/` của tám skill.

Phần để lại cho một đợt sau, và vì vậy điểm rủi ro là 2:

- Danh mục lệnh của `ccba-git-guardrails` tiếp tục yêu cầu phép trước mọi `git push`, kể cả `--force-with-lease`. Danh mục đó đứng nguyên.
- `ccba-eval-gate` tiếp tục gọi `scripts/eval_runner.py` cạnh card `harness_eval.v1`. Script đó đứng nguyên.
- `ccba-web-testing` vẫn dùng `https://example.com` trong Quick Start. `metadata.author` vẫn là `claudekit`.
- `ccba-grilling` vẫn nêu `ccba-prototype` ở nhánh visual prototype.
- Pha 2 của `ccba-xia` vẫn ghi hướng port tất định vào `packages/*/src/` cho một phiên sau. Đợt 7 giữ nguyên `packages/`.

Sau khi cả bốn PR xanh trên đĩa, đệ trình nghiệm thu Đợt 7 kèm `python -m ccba_harness verify-patch --preset ci`.