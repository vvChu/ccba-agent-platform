---
request_id: req-discuss-wave6-sdlc-skills-001
verdict: APPROVE_PLAN
conditions:
- id: COND-01
  description: Đã khóa. Tám skill, mỗi skill một mục Markdown "## 🏛️ Platform-Aware
    Architecture Posture (ADR-0061)" với lý do riêng. seam-contracts.yaml giữ 16 seam_id.
    packages/ đứng ngoài đợt. harness_verify.v1 giữ import_path ccba_harness:auto_apply_and_verify_patch.
    Skill gọi verify-patch với vai caller.
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-02
  description: Đã khóa. Frontmatter name, tier, command, triggers, description, bundle,
    is-orchestrated và khối gpi đứng yên. Bốn orchestrator tiếp tục kết thúc ở Cổng
    1, khối gpi vẫn vắng. Kernel giữ code-review 16.5, diagnosing-bugs 14.5, create-pr
    14.0, tdd 12.0. tdd đạt ngưỡng >= 12.0 và nằm trong deadband [11.5, 12.5). Validator
    đọc tier kernel làm existing tier. ccba-code-review giữ tier kernel.
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-03
  description: Đã khóa. Bảng Level 3 đứng nguyên trên đĩa. implement 4 dòng, tdd 2
    dòng, diagnosing-bugs 1 dòng, code-review 14 dòng (10 tệp gốc references/ và 4
    checklist). Thư mục references/ đứng ngoài diff của cả bốn PR.
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-04
  description: Đã khóa. ccba-graduate-rd dùng $CCBA_HUB_PATH và $env:CCBA_HUB_PATH.
    BRANCH_NAME thành hai lệnh gán tường minh. Bước 6 thành hai lệnh gh pr create.
    Đoạn cuối ghi nhận skill chưa có thư mục references/.
  blocking: false
  source_profile: arch_audit
  source_profiles: []
- id: COND-05
  description: Đã khóa. Bốn PR song song 6A–6D, bốn cặp thư mục tách biệt. Mỗi SKILL.md
    khóa bằng validate_skills.py --file --enforce-gpi, audit_skills_hygiene.py --file,
    và verify-patch --preset skill --target. Sau khi cả bốn PR có trên đĩa, chạy verify-patch
    --preset ci.
  blocking: false
  source_profile: arch_audit
  source_profiles: []
risk_score: 2
effort: M
summary: Kế hoạch Đợt 6 được phép bắt đầu. Tám skill nhận seam-exempt. GPI, tier và
  16 card seam đứng yên. Bốn PR song song. Lý do trên đĩa theo sáu pha của diagnosing-bugs
  và 14 dòng Level 3 của code-review. graduate-rd viết hai nhánh và hai lệnh gh pr
  create.
telemetry:
  session_id: b4212484-b6dd-408e-8e32-91702b45833b
  primary_model: grok-4.7-build
  input_tokens: 960712
  output_tokens: 27230
  reasoning_tokens: 20038
  cached_read_tokens: 866816
  total_tokens: 987942
  model_calls: 15
  turn_count: 1
  cost_usd: 266757.2
  cost_mode: exact
  duration_seconds: 338.09
---
## PeerVerdictBlock

```yaml
peer_verdict:
  request_id: "req-discuss-wave6-sdlc-skills-001"
  from_agent: "grok"
  to_agent: "antigravity"
  profile: "arch_audit"
  pass: 1
  verdict: APPROVE_PLAN
  risk_score: 2
  authorized_start: allowed
  dag:
    parallel: ["6A", "6B", "6C", "6D"]
    after: {}
  lock:
    - "python scripts/validate_skills.py --file <SKILL.md> --enforce-gpi"
    - "python scripts/governance/audit_skills_hygiene.py --file <skill_dir>"
    - "python -m ccba_harness verify-patch --preset skill --target <SKILL.md>"
  floor: "python -m ccba_harness verify-patch --preset ci"
  rationale: >
    Tám skill là SOP chu trình kỹ thuật. seam-contracts.yaml có 16 seam_id.
    Card harness_verify.v1 trỏ ccba_harness:auto_apply_and_verify_patch.
    Bốn orchestrator dừng tại Cổng 1. Bốn kernel giữ hệ số hiện có.
    ccba-tdd đạt GPI 12.0, đúng ngưỡng Tier 2B.
    Bốn PR không chung tệp.
```

Phán quyết: **APPROVE_PLAN**. Bốn PR song song được phép bắt đầu. Điểm rủi ro **2/5**. Phần rủi ro còn lại nằm ở kỷ luật khi chép lý do posture và khi sửa `ccba-graduate-rd`, đã khóa trong năm điều kiện `blocking: false` ở trên.

## 1. Đối soát trên đĩa

`seam-contracts.yaml` có đúng 16 `seam_id`, từ `legal_markdown.v1` đến `notebooklm_rag.v1`. Card `harness_verify.v1` có `import_path: ccba_harness:auto_apply_and_verify_patch`, `in: [anchor_patch, verify_preset]`, `out: [verification_report]`. Tám skill Đợt 6 không có tên trong file này.

Công thức \(\mathrm{GPI} = 2.5S + 2.0K + 2.0A - 1.5P\) cho ra đúng bốn số đang giữ:

| Skill | \((S, K, A, P)\) | GPI | Tier trên đĩa |
| :--- | :--- | :---: | :--- |
| `ccba-code-review` | \((4.0, 3.0, 1.0, 1.0)\) | 16.5 | `kernel` |
| `ccba-diagnosing-bugs` | \((4.0, 2.0, 1.0, 1.0)\) | 14.5 | `kernel` |
| `ccba-create-pr` | \((3.0, 3.0, 1.0, 1.0)\) | 14.0 | `kernel` |
| `ccba-tdd` | \((3.0, 2.0, 1.0, 1.0)\) | 12.0 | `kernel` |

`GPI_STANDALONE_THRESHOLD` là 12.0. Nhánh phân tầng gốc gán Tier 2B khi điểm \(\ge 12.0\). Điểm 12.0 của `ccba-tdd` đã là Tier 2B trước hysteresis. Deadband \([11.5, 12.5)\) cũng chứa 12.0. `SkillValidator` lấy `existing_tier` từ `tier: kernel` khi frontmatter không có khóa `existing-tier`. Khóa đó tiếp tục vắng. Hệ số và `tier` đứng yên.

`ccba-new-feature`, `ccba-implement`, `ccba-release-feature`, `ccba-graduate-rd` đều có `tier: orchestrator` và `is-orchestrated: true`. Validator trả về ngay sau Cổng 1, trước khi đọc `gpi`. Bốn frontmatter này tiếp tục không có khối `gpi`.

`compile_catalog.py` chỉ kéo `name`, `bundle`, `description`, `triggers` hoặc `keywords`, `command`, `package_path`, `tier`. Mục posture nằm trong thân Markdown, sau frontmatter. `catalog.yaml` giữ nguyên khi các khóa đó đứng yên.

## 2. COND-01 — tám lý do `seam-exempt`

Mỗi `SKILL.md` nhận một mục `## 🏛️ Platform-Aware Architecture Posture (ADR-0061)`. Lý do ghi trên đĩa là lý do của chính skill đó.

| Skill | Lý do ghi trên đĩa |
| :--- | :--- |
| `ccba-new-feature` | SOP orchestrator cho feature branch, claim lock và Factory Model (planning, bàn giao session, coding). Tra `catalog.yaml` theo reuse-first. |
| `ccba-implement` | SOP orchestrator cho Red-Green-Refactor và scoped test. `verify-patch --preset code` là caller của `harness_verify.v1`. Chữ "seam" trong skill là ranh giới kiểm thử. |
| `ccba-tdd` | SOP kernel Red-Green-Refactor. GPI \((3,2,1,1) = 12.0\), đạt ngưỡng Tier 2B và nằm trong deadband. |
| `ccba-diagnosing-bugs` | SOP kernel sáu pha đang có trên đĩa: feedback loop, reproduce, hypothesise, instrument, fix, cleanup. GPI \((4,2,1,1) = 14.5\). |
| `ccba-code-review` | SOP kernel hai trục Standards và Spec. Hai sub-agent đọc-only, báo cáo tổng hợp theo Single-Writer đã viết ở bước 4. GPI \((4,3,1,1) = 16.5\). `verify-patch` là caller của `harness_verify.v1`. |
| `ccba-create-pr` | SOP kernel mở Pull Request trong repo hiện tại. GPI \((3,3,1,1) = 14.0\). `ccba-contribute-to-hub` đã kế thừa skill này cho chiều Spoke sang Hub. |
| `ccba-release-feature` | SOP orchestrator cho TRIHT, squash merge và đóng issue. Lệnh `scripts/sync_spoke.py --spoke` giữ đúng mặt wrapper đã khóa ở Đợt 5. |
| `ccba-graduate-rd` | SOP orchestrator tốt nghiệp scratch vào package có sẵn ở một phiên sau. Đợt 6 giữ nguyên `packages/` và 16 card. |

`ccba-code-review` giữ `tier: kernel`. Hai sub-agent đã bị chặn ủy thác lại và đã có Single-Writer. Cổng 1 của validator đọc `is-orchestrated` từ frontmatter. Skill này không mang cờ đó, và GPI 16.5 đứng trên ngưỡng 12.0.

## 3. COND-03 — bảng Level 3

Hygiene trả exit code 1 cho cả YELLOW lẫn RED khi một reference thiếu mặt trong bảng. Bốn bảng sau đứng nguyên, và cả thư mục `references/` đứng ngoài diff.

| Skill | Số dòng trên đĩa | Tệp |
| :--- | :---: | :--- |
| `ccba-implement` | 4 | `discard_feature_sop.md`, `prototyping_patterns.md`, `prototype_logic.md`, `prototype_ui.md` |
| `ccba-tdd` | 2 | `tests.md`, `mocking.md` |
| `ccba-diagnosing-bugs` | 1 | `mock_debugging_patterns.md` |
| `ccba-code-review` | 14 | 10 tệp gốc trong `references/` và 4 tệp `references/checklists/` (`base`, `python`, `api`, `web-app`) |

Đếm 14 là đếm đủ hàng của bảng hiện có. Mười tệp gốc và bốn checklist cùng nằm trong một bảng.

`ccba-new-feature`, `ccba-create-pr`, `ccba-release-feature` không có `references/`. `ccba-graduate-rd` cũng không có thư mục đó. Đoạn cuối của `ccba-graduate-rd` được viết lại thành một câu: skill chưa có `references/`; bảng Level 3 xuất hiện cùng lúc với tệp tham chiếu. Đợt này không tạo thư mục `references/` mới.

## 4. COND-04 — `ccba-graduate-rd`

Trên đĩa còn ba chỗ trong cùng một skill:

| Vị trí | Việc trong PR 6D |
| :--- | :--- |
| Dòng 86, `` `hub_path` `` | `$CCBA_HUB_PATH` và `$env:CCBA_HUB_PATH`, cùng mẫu câu đã có ở `ccba-contribute-to-hub` |
| Dòng 89, `${ISSUE_ID:+...}` | Hai lệnh gán: `proposal/issue-<ISSUE_ID>-<PROPOSAL_NAME>` khi có Issue, `proposal/<PROPOSAL_NAME>` khi không có Issue |
| Bước 6, `--body "$PR_BODY"` | Hai lệnh `gh pr create` đầy đủ, một lệnh có `Closes #<ISSUE_ID>`, một lệnh không có |

Mẫu hai lệnh `gh pr create` lấy đúng khối đang đứng trong `ccba-contribute-to-hub` bước 4. Các `$VAR` thường trong fence `bash` của bảy skill còn lại giữ nguyên. Mở rộng `:+` chỉ có ở dòng 89.

`audit_skills_hygiene.py` gắn RED cho `$(...)`, `export VAR=`, `sudo apt`, `grep` có cờ, `awk`, `head -n`, `2>/dev/null`, `xargs` khi đứng ngoài fence ngôn ngữ `linux`. Tám cây skill không chứa các mẫu đó. `${ISSUE_ID:+...}` nằm ngoài regex RED. COND-04 vẫn gỡ nó để PowerShell và Bash đọc cùng một nghĩa, đúng sổ đã khóa ở Đợt 5.

## 5. Bốn PR và khóa hoàn tất

| PR | Tệp | Việc |
| :--- | :--- | :--- |
| **6A** | `ccba-new-feature/SKILL.md`, `ccba-implement/SKILL.md` | Mục `seam-exempt`. Giữ orchestrator. Giữ 4 dòng Level 3 của `ccba-implement`. |
| **6B** | `ccba-tdd/SKILL.md`, `ccba-diagnosing-bugs/SKILL.md` | Mục `seam-exempt`. Giữ GPI 12.0 và 14.5. Giữ 2 dòng và 1 dòng Level 3. Lý do bugs ghi sáu pha. |
| **6C** | `ccba-code-review/SKILL.md`, `ccba-create-pr/SKILL.md` | Mục `seam-exempt`. Giữ GPI 16.5 và 14.0. Giữ 14 dòng Level 3. `ccba-code-review` giữ `tier: kernel`. |
| **6D** | `ccba-release-feature/SKILL.md`, `ccba-graduate-rd/SKILL.md` | Mục `seam-exempt`. Giữ orchestrator. COND-04 trên `ccba-graduate-rd`. |

6A, 6B, 6C, 6D chạy bộ ba lệnh trên từng `SKILL.md` trong cặp của mình. `validate_skills.py --enforce-gpi` với orchestrator trả về tại Cổng 1. Với `ccba-tdd`, điểm 12.0 đi nhánh Tier 2B.

Đứng ngoài bốn PR: `packages/`, `seam-contracts.yaml`, `catalog.yaml`, `scripts/`, `ccba-contribute-to-hub`, `ccba-issue-to-hub`, toàn bộ `references/` của bốn skill có bảng Level 3.

Phần để lại cho một đợt sau, và vì vậy điểm rủi ro là 2: `ccba-new-feature` bước 8 vẫn liệt kê `safe_pytest`, `ruff`, `mypy` song song với `verify-patch` mà `ccba-implement` đã dùng; `ccba-new-feature` và `ccba-release-feature` vẫn checkout `main` trong khi `ccba-create-pr` đã dùng `<default_branch>`. Hai chỗ đó đứng nguyên trong Đợt 6 để diff giữ đúng posture và COND-04.

Sau khi cả bốn PR xanh trên đĩa, đệ trình nghiệm thu Đợt 6 kèm `python -m ccba_harness verify-patch --preset ci`.