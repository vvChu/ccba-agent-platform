---
request_id: req-audit-wave3-core-skills-004
verdict: APPROVE
conditions: []
risk_score: 1
effort: S
summary: COND-03 đóng trên advisor, ingest và tracker. Ba lệch hiệu lực, chiều cạnh
  thay thế và enum LegalDocStatus đã khớp chữ ký registry. Đợt 3 được nghiệm thu.
telemetry:
  session_id: b8a1a062-f43f-4583-9f1c-b59946962f44
  primary_model: grok-4.7-build
  input_tokens: 412007
  output_tokens: 14527
  reasoning_tokens: 10894
  cached_read_tokens: 357120
  total_tokens: 426534
  model_calls: 12
  turn_count: 1
  cost_usd: 127668.64
  cost_mode: exact
  duration_seconds: 193.04
---
# Phán quyết nghiệm thu Đợt 3, lượt 4 — 8 skills lõi

**Hồ sơ:** `req-audit-wave3-core-skills-004`
**Bên nộp:** `antigravity`
**Bên phán quyết:** `grok` (hồ sơ `arch_audit`)
**Căn cứ:** `APPROVE_WITH_CONDITIONS` tại `req-audit-wave3-core-skills-003`, `normalize_doc_status`, `LegalDocStatus`, `registry.py` dòng 668–705, và thân `SKILL.md` của advisor, ingest, tracker
**Tệp:** `.md/peer_exchange/grok_audit_wave3_core_skills.md`

**Phán quyết: `APPROVE`.** Điểm rủi ro **1/5**. `COND-03` đóng trên đúng ba tệp đã nêu ở lượt 3. `COND-04` và `COND-07` giữ nguyên trên đĩa.

## COND-03 — ba điểm đã khớp

| Điểm lượt 3 | Đối soát lượt 4 |
| :--- | :--- |
| Advisor, Tầng 3 | `.agents/skills/ccba-legal-advisor/SKILL.md` dòng 76 đi qua `python -m ccba_legal query` hoặc `ccba_legal.registry`, đối soát `ACTIVE` cùng `supersedes`, `replaces`, `replaced_docs`, `relations.*`. Câu này liệt kê đủ các khóa đi ra mà `registry.py` đọc ở dòng 679–684. |
| Chiều cạnh Mục 5 | Advisor dòng 129, ingest dòng 203, tracker dòng 138 dùng cùng một mệnh đề. Văn bản được trích khi `normalize_doc_status` trả `ACTIVE` (gồm `current`/`active`), các trường bị thay `superseded_by`, `replaced_by`, `replaced_by_docs` trống, và mã văn bản vắng mặt trong danh sách thay thế của mọi văn bản kế nhiệm. Văn bản kế nhiệm giữ `supersedes`, `replaces`, `replaced_docs`, `relations.*` vẫn nằm trong tập được trích dẫn. |
| Enum tracker | Tracker dòng 75 ghi `DRAFT` → `PENDING_EFFECTIVE` → `ACTIVE` → `SUPERSEDED` / `PARTIALLY_AMENDED` theo `LegalDocStatus`. Các tên này là thành viên enum trong `packages/ccba-legal-intel/src/ccba_legal/models.py` dòng 16–20. |

`registry.get` gom cạnh đi ra tại dòng 679–684 và cạnh đi vào tại dòng 693–698. Sổ Hub `.md/data/legal_registry.yaml` giữ Luật Xây dựng 2025 (`id: LXD-2025`, `status: ACTIVE`, `replaces: LXD-2014`, `supersedes: [50/2014/QH13, 62/2020/QH14]`) và Luật PCCC 2024 (`id: LPCCC-2024`, `status: ACTIVE`, có `supersedes`). Predicate Mục 5 giữ hai văn bản này trong tập trích dẫn.

`UNVERIFIED` vẫn là thành viên enum và là trạng thái tra cứu khi mã vắng mặt trong sổ (`registry.py` dòng 657–665). Chuỗi dòng 75 là chuỗi ghi khi cập nhật registry. Posture tracker dòng 44 tiếp tục công nhận `ACTIVE` và các khóa thay thế qua `ccba_legal query` / `ccba_legal.registry`.

## Điều kiện đã đóng từ các lượt trước

| Điều kiện | Đối soát giữ nguyên |
| :--- | :--- |
| `COND-04` | `ccba-ai-qc-pccc-audit/SKILL.md` dòng 44 và dòng 76–80 truyền `--model` từ `choose_model("audit")` (`ModelArchetype.REASONING`). `references/sop_cdt_tu_tham_dinh.md` dòng 40 gọi cùng seam. GPI giữ `s: 2, k: 2, a: 4, p: 3`. |
| `COND-07` | `ccba-legal-intel/SKILL.md` mục 1.1 là bundle OKF v2.4, mục 1.2 là CWE-22 và độ dài slug. Mục 2 giữ 11 quan hệ, gồm `replaced_docs` và `replaced_by_docs`. Dòng 48 và dòng 104 giao nạp TVPL, OKF, VBHN và 15 cổng cho `/ccba-legal-ingest`. Mục 3 giữ `sync`, `query`, `get-clause`, `get-table`, checklist và `pptx`. |
| Diagram, QC orchestrator | `ccba-excalidraw-diagram` ở thế `package-bound` và gọi `apply_smart_layout`. `ccba-mermaid-diagram` ở thế `seam-exempt`. `ccba-ai-qc` giữ `tier: orchestrator` và import `ccba_qc_core:QCAuditPipeline`. |

## Phạm vi đối soát của phiên này

Hồ sơ `arch_audit` đọc nguồn bằng `read_file` và `grep` (`PROFILE_SPECS` allowlist). Lời khai exit 0 của `validate_skills.py --enforce-gpi`, `verify-patch --preset doc`, `audit_skills_hygiene.py` và `pytest tests/governance/` thuộc biên bản bên nộp. Nội dung ba tệp COND-03 đã khớp chữ ký vòng đời trên đĩa, nên phán quyết kiến trúc là `APPROVE`.

`registry.get` còn gập `relations.superseded_by` và `relations.replaced_by` vào trường đã giải `superseded_by`. Mục 5 kiểm tra trường đã giải đó cùng phép tra ngược trên văn bản kế nhiệm. Bề mặt này nằm trong đường SSOT bắt buộc và giữ điểm rủi ro ở 1/5.