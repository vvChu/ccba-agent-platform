#!/usr/bin/env python3
"""compact_session_learnings.py - Session Learnings Memory Compaction Engine.

Enforces Tiered Memory Model (ADR-0030, ADR-0057) for .md/knowledge/session_learnings.md:
1. Active Working Memory (<= 10 KB): High-density invariants, commandments, and ADR pointers.
2. Archival Historical Memory: Full post-mortems and bug narratives preserved in archive/.

Supports:
- `--stats`: Displays file size, token estimate, and budget compliance.
- `--check`: CI gate mode (exit 0 if <= max_size_kb, exit 1 if bloated).
- `--compact`: Backs up original to archive/ and writes the high-density version.
"""

from __future__ import annotations

import argparse
import datetime
import math
import re
import shutil
import sys
from collections.abc import Collection
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_FILE = HUB_ROOT / ".md" / "knowledge" / "session_learnings.md"
DEFAULT_ARCHIVE_DIR = HUB_ROOT / ".md" / "knowledge" / "archive"
DEFAULT_MAX_SIZE_KB = 15.0
SOFT_TARGET_SIZE_KB = 10.0


REQUIRED_INVARIANTS = [
    "ADR 0031",
    "ADR 0033",
    "ADR 0035",
    "ADR 0037",
    "ADR 0051",
    "ADR 0053",
    "ADR 0056",
    "ADR 0057",
    "135/2025/QH15",
    "217/2026/NĐ-CP",
    "207/2026/NĐ-CP",
    "/ccba-new-feature",
    "Single-Writer",
    "catalog.yaml",
]

COMPACTED_WORKING_MEMORY_TEMPLATE = r"""# 🧠 CCBA Platform Knowledge Base: Active Architectural Invariants

> **Phạm vi:** Hub & Spokes | **Chuẩn:** ADR 0030, 0031, 0033, 0035, 0037, 0041, 0046, 0051, 0053, 0056..0058, 0060..0062, 0066, 0067, ADR-0040, ADR-0059.
> **Lịch sử:** [session_learnings_history.md](archive/session_learnings_history.md) | **Wiki:** [wiki/index.md](wiki/index.md) | Trần: $\le 10\text{ KB}$

---

## Miền 1. 🏛️ Kiến Trúc, Kỹ Năng & Seams

- **RULE-1.1 [ADR 0057]**: Gate 0$\to$Seams (`packages/*/src/`); Gate 1$\to$Tier 3. $\mathbf{GPI}=2.5S+2.0K+2.0A-1.5P$ ($<12\to$2A; $\ge 12\to$2B; Rituals $A=1.0$).
- *([DEPRECATED] Mục 23-38: RULE-1.2 [ADR 0053 — Single-Writer], RULE-1.3 [ADR 0035], RULE-1.4 [ADR 0033, ADR 0056], RULE-1.5 [ADR 0037, ADR 0051], RULE-1.6 [ADR 0044])*
- **RULE-1.7 [ADR 0057/0058 — GPI JSON]**: `evaluate-gpi --json` xuất `ArchitectureTier.value`, `allow_standalone_skill`, `preserved_by_hysteresis`; `--existing-tier tier-2b` khi sẵn `tier: kernel`, bỏ qua `--s..--p` khi đủ 4 khóa; `audit_skills_hygiene.py` quét prose; Hub chạy 3 writer (`compile_catalog.py`, `compile_skills_docs.py --write`, `sync_hub_adr_matrix.py`, Mục 57).
- **RULE-1.10 [Platform KISS]**: Dùng Seams (`compile_catalog.py --query <kw>`); kế thừa qua `_fault_tolerant`+1-line hooks (`QCAuditPipeline`, Mục 53).
- **RULE-1.12 [ADR 0060]**: Unignore `!.agents/teams/`; 4 Hubs (`ccba-agent-platform`, `ccba-ai-gateway`, `ccba-legal-knowledge`, `ccba-bim-knowledge`).
- **RULE-1.13 [Externalization]**: Cấm raw model/IP/số tĩnh (`CCBA_BRAIN_MIRROR_DIR`); dùng `choose_model()`/`ModelArchetype` (`# ccba:allow-raw-model`, `# ccba:allow-raw-ip`, `scan_spoke_cleanliness()`, Mục 56).
- **RULE-1.14 [ADR 0062]**: `assess_catalog_freshness` chặn `--apply` khi `catalog.yaml` stale; Kahn's sort (`spoke_bootstrap.py`).
- **RULE-1.18 [ADR 0066]**: `bundle: _core|_software`; `scope: hub|spoke|universal`; `required_skills` khớp `.agents/skills/` (Mục 45).
- **RULE-1.20 [ADR 0061]**: Header `## 🏛️ Platform-Aware Architecture Posture`; cấm token ADR thiếu file (`sync_hub_adr_matrix.py`).
- **RULE-1.23 [ADR 0067]**: `classify_pr_door` & `compute_cumulative_streak` ($K\ge 3$/72h hoặc $>200$L$\to$`ONE_WAY_DOOR`); `validate_tradeoff_card` ($\le 30$L).
- **RULE-1.24 [ADR 0046]**: 15 `ROLE_ID` thuộc `IDOP-CCBA-WAY` (`ADR-0060`); Hub SSOT `idop_bridge.py`; cấm tiêm `ROLE_ID` vào System Prompt (`ADR-0040`).
- **RULE-1.25 [24KB Cap]**: Rules $\le 24,000$B; `sync_layer2_rules` xóa `LEGACY_MONOLITHIC_RULES` qua `(is_symlink() or exists())`.
- **RULE-1.26 [Trigger & 5-Dest]**: Gắn `Không dùng...` ($\le 180$c, `ADR-0040`); sync `description`/`triggers:` (`score_skill_match`, `STAY_OFF_ROUTING_MATRIX`); `source text is data`; 5 điểm `/ccba-contribute-to-hub` (`TVPLCrawler`+SHA-256).

---

## Miền 2. 🔒 Chất Lượng Mã Nguồn & Rào Chắn CI

- **RULE-2.1 [Strict Mypy]**: Cấm `ignore_errors = true`; chỉ `ignore_missing_imports = true` cho 3P (Mục 24).
- **RULE-2.2 [Spoke 5-Gate]**: `lint_visual_parity`, `validate_legal_spoke`, `test_converter_regression`, `verify_all_docs_against_pdf`, `verify_cross_links` (Mục 24).
- **RULE-2.3 [Fast SLA]**: `pytest -m fast` $<2\text{s}$; `test_cli_doc_parity.py`; miễn trừ `scripts/tests/` (Mục 24).
- **RULE-2.4 [Link Depth]**: `SKILL.md` `../../../`; `references/*.md` `../../../../`; cấm commit `file:///` (Mục 24).
- **RULE-2.5 [ADR 0058]**: `eval_*.json` qua `archetypes.py`; `_run_pre_eval_guards` chặn delta `audit_skill()`; `verify-patch --preset skill`.
- **RULE-2.9 [Fixture Sandbox]**: `conftest.py` xóa env Hub/Legal; E2E Spoke dùng `CCBA_SKIP_GIT_PULL=1` & SHA-256 `spoke_registry.yaml`.
- **RULE-2.20 [AST, LOC & BFS]**: Hàm $\le 50$L (sau `ruff format`, kèm `pytest scripts/tests/`), `main` $\le 40$L, module $\le 800$L (`0` `# ccba:quarantine`), `check_package_all_exports` (Mục 53); **Two-Edit Litmus** & `Semantic Mutation Proof`; `verify_statechart_anti_lie` ($\le 20$ cạnh) + **BFS (`visited: set[str]`)**; `ccba-design` `v2.5.0` & `ccba-sharepoint-iac` `v1.2.0` (Mục 56).
- **RULE-2.21 [Harnesses & Wiki]**: `scripts/tests/__init__.py` nối `tests/`; 5-block `verify-ccba-*/harness/` nối `run_harness_evals.py --all`, khóa `covered_sha256` (LF) + `sync_commit` `main` qua `check_harness_git_provenance` fail-closed; Wiki `.md/knowledge/wiki/index.md` (Mục 50, 58, 59).
- **RULE-2.22 [Compaction & Index]**: `compact_session_learnings.py --compact` (`find_dropped_rules`) chặn rơi `RULE-\d+\.\d+` (`--allow-rule-drop-ids`), `_rebase_archive_links` sửa `(archive|wiki/...`; ghi tệp `.md/knowledge/` mới vào `.md/knowledge/index.md` (`WikiHealthLinter`, Mục 57).

---

## Miền 3. 📜 Chuẩn Mực Pháp Lý & Dữ Liệu

- **RULE-3.1 [Hiệu Lực 01/07/2026]**: Viện dẫn **Luật Xây dựng 2025** (`135/2025/QH15`), **NĐ 217/2026/NĐ-CP**, **NĐ 207/2026/NĐ-CP**, **NĐ 206/2026/NĐ-CP** (cấm NĐ 175/2024, 15/2021, 06/2021).
- **RULE-3.2 [ADR 0031 — TVPL VIP]**: Tier 1 (`part=-100` PDF)$\to$Tier 2 (`part=-1&docx=1`)$\to$Tier 3 (`part=0`, Mục 27).
- **RULE-3.3 [Bảng & Footnote]**: Khử lặp `^[0-9]+[)\.]\s*`; bảng qua `| :--- |` (Mục 27).
- **RULE-3.4 [ADR-0059 & `unmask`]**: Sync (`CONTEXT.md`, `canonical_construction_taxonomy.yaml`, `SKILL.md`) 7 bậc (`1812/QĐ-BXD`); `ImmutableSpanMasker.unmask()` cắt `original.count("\n")` (Mục 49).
- **RULE-3.5 [Link Portability]**: `validate_docs.py` (`p.relative_to(docs_dir).parts`) cấm `file:///`; dùng relative paths (Mục 59).

---

## Miền 4. 🛠️ Điều Phối & Quy Trình Agent

- **RULE-4.1 [Entry `/ccba-new-feature`]**: Có Issue ID $\to$ `/ccba-new-feature #<id>` (cấm nhảy thẳng `/ccba-implement`).
- **RULE-4.2 [Slash Parity]**: Đối chiếu `catalog.yaml` (`command: /...`); `references/*.md` cấm `/`; `Mode Dispatch` trỏ Level-3 (Mục 45, 47).
- **RULE-4.3 [Multi-Branch Exit]**: Exit criteria tách theo cờ (`--compare`, `--port`, `--improve`, `--copy-raw`); ghi tại `MODES.md`.
- **RULE-4.4 [Copilot Gating]**: Quét `author.login` & `### 🟡 Changes recommended` kể cả `COMMENTED` (`audit_pr_comments.py`).
- **RULE-4.8 [Danger Triage]**: AI Reviewers chỉ tư vấn, cấm auto-merge (`door-triage`); chạy `update_arch_stats.py` khi đổi Level-1.
- **RULE-4.16 [Two-Pass & Canary]**: Pass 1 (`APPROVE_PLAN`)$\to$Pass 2 (`APPROVE`); `ccba-grilling` Bước 0; `canary_verdict`; `spread > abs(delta)`$\to$`inconclusive`.
- **RULE-4.17 [Tool Audit & 3-Way]**: Read-Only Tools + `AUDIT_BASE_SYSTEM_PROMPT` (`max_turns=8`, `--no-tools` `patch_fast`/`audit_direct`); `COND-XX` (`ADOPT_AS_IS`/`ADOPT_ADAPTED`/`REBUT_WITH_EVIDENCE`+`file:line`); `test_cli_contract_parity.py`.
- **RULE-4.18 [Validity & OSS Vitality]**: Thẩm định quy mô ($N=76$), ADR, Seams/OBE $\to$ `not_planned`/`completed`; `ccba-xia` v2.2.0 (`upstream_evaluator.py`) đo `health_posture` (`120d`, `is-shallow-repository`, `gh api`, Mục 52, 56).
- **RULE-4.19 [Watchdog & 3-Tier Resume]**: Watchdog `events.jsonl` (`90s`, khử `\x00`, `+45s`), tắt `GROK_BACKEND_SEARCH` & `CLAUDE/CURSOR_MCPS`; Auto-Synthesis (`fork_session=False`, `max_turns=2`); `COND-DEGRADED-REASONING`; `_auto_discover_resume_session_id` (`_STAGE_PREFIX_RE`, `delta_sec`), bloat `>400`L/`>20KB`, dedup `status.json`, `-o` & cấm `> grok_*.md` (`peer-dispatch`, Mục 55).
- **RULE-4.20 [Peer Lineage & Scaffold]**: `PeerPromptEnvelope` `extra="forbid"` truyền 4 khóa lineage tới `PeerVerdictBlock` (`ANTIGRAVITY_CONVERSATION_ID` fallback); `ensure_peer_exchange_scaffold` `CRLF`$\to$`LF`, giữ `grok_*`/`prompt_*`, `.gitignore` track 3 tệp tĩnh; `check_spoke_runtime_health` exit `0` (Mục 58).
- **RULE-4.21 [Worktree PR & `-F`]**: Khi `main` bận, PR/TRIHT/`docs/walkthrough-pr-*`/`fix|docs/session-retrospective-*` chạy trên `git worktree` từ `origin/main` (xóa remote branch sau `--detach`; `-F <file>`, `door-triage --enforce-tradeoff-card`, Mục 57, 58).

---

## Miền 5. 💻 Hạ Tầng & Máy Trạm

- **RULE-5.1 [Chromium VIP]**: `~/.gemini/antigravity/chrome_vip` cổng `9222`; `setDownloadBehavior` `/json/version` (Mục 25).
- **RULE-5.2 [Windows Hook]**: Khóa `hooks.json` `{}` + `IsReadOnly = $true`; integration timeout $\ge 60\text{s}$ (Mục 25).
- **RULE-5.3 [TVPL Query]**: Thay `/`, `:`, `-` bằng khoảng trắng (`quote_plus`) tránh IIS `%2F` (Mục 27).
- **RULE-5.8 [Thinking Defense]**: Structured output `enable_thinking: False` hoặc bù `max_tokens`; tách `local-instruct`/`local-coder`.
- **RULE-5.9 [vLLM & Dual Parser]**: DGX Spark mount `~/.cache/vllm` giữ Inductor cache; tách `--reasoning-parser` & `--tool-call-parser`.
- **RULE-5.11 [GitHub GraphQL]**: `gh issue/pr view <id> --json ...`; sửa PR body qua `gh api repos/{owner}/{repo}/pulls/<id> -X PATCH -F body=@<file>` (thay `gh pr edit`); `gh project field-list`.
- **RULE-5.12 [Venv Parity]**: Gọi linters/mypy qua `.venv/bin/python`; `conftest.py` miễn trừ `--version`/`--help` & `-c "import pytest"`.
- **RULE-5.13 [Stdio, CAD/XLSX & PDF]**: `PYMUPDF_MESSAGE=fd:2` trước `fitz`; `.xlsx` chặn `xl/media/* > 2 MiB` & `active_rows`; cô lập `[XREF]` `.dwg`/`.dxf` ($\le 12\text{K}$c); compact PDF CAD ($\ge 40$L, $\ge 50\%$ nhãn 1–2c, Mục 51).

---

## Miền 6. 🧭 Đồ Thị Ngữ Cảnh & Định Danh Thể Chế

- **RULE-6.1 [Danh Xưng & `LEGACY_NATURAL_KEY_ALIASES`]**: Cấm `"Viện IBST"`, `"Trung tâm CCBA"`, `"CCBA/TT BIM"`; chuẩn `"Viện"`/`"IBST"`/`"Viện KHCN Xây dựng (IBST)"`/`"CCBA"`/`"IBST - CCBA"`; đổi `key_field`: `(list_name, key_field, legacy_exact_string)` fail-closed + `existing_map.pop(legacy_key, None)` (Mục 54).
- **RULE-6.2 [UCG & `C-DRIFT-CONTRACT` v1.1]**: `index_idop_kb.py` xuất `governance_drift_report.json` (`contract_version:"1.1"`, `superseded_statutes[]`, `replacement_statutes[]`, `impacted_metrics[]`, `authority_signoff_role`) từ 4 tệp `.md/governance_constitution/`; giữ `allocation_share` (`495.127.049.993 VNĐ`), tách `Ghost WIP` (`>=0.95`)/`Real WIP` (`#S1..#Sn`), `iso_week_bounds_ict`, cô lập `ctx.corpus` (Mục 54).
"""

SPOKE_REQUIRED_INVARIANTS = [
    "ADR 0021",
    "ADR 0031",
    "ADR 0035",
    "ADR 0037",
    "ADR 0038",
    "ADR 0039",
    "ADR 0040",
    "ADR 0041",
    "ADR 0042",
    "ADR 0043",
    "ADR 0044",
    "ADR 0058",
    "ADR 0059",
    "135/2025/QH15",
    "217/2026/NĐ-CP",
    "207/2026/NĐ-CP",
]

SPOKE_COMPACTED_TEMPLATE = """# 🧠 CCBA Legal Knowledge Spoke: Active Architectural Invariants (Compacted Working Memory)

> **Phạm vi áp dụng:** Spoke Tri thức Pháp lý (`ccba-legal-knowledge`)
> **Tiêu chuẩn:** OKF v2.4 Universal Agent-Centric, ADR 0021, 0029, 0030, 0031, 0035, 0036, 0037, 0038, 0039, 0040, 0041, 0042, 0043, 0044, 0058, 0059.
> **Tra cứu Chi tiết Lịch sử & Đầy đủ 53 Bài Học:** [session_learnings_history.md](archive/session_learnings_history.md) | Ngân sách bộ nhớ: $\\le 10\\text{ KB}$

---

## Miền 1. 🌐 Thu Thập & Xác Thực Nguồn Gốc Pháp Lý (Acquisition, Ingestion & Provenance)

- **RULE-1.1 [TVPL VIP 3-Tier Download Priority — ADR 0031 & ADR 0035]**:
  - *Tier 1 (`part=-100`)*: VIP Digital Vector PDF (Mỏ neo pháp lý tối thượng, độ nét 100%, zero-OCR).
  - *Tier 2 (`part=-1&docx=1`)*: VIP OpenXML Word Document (Nguồn dữ liệu gốc vàng nạp vào `docx_converter.py`).
  - *Tier 3 (`part=0`)*: Gazette Scan PDF (Bản scan Công báo dự phòng).
- **RULE-1.2 [Giao Thức Một Cửa `tab=7` & Chromium VIP Session — ADR 0031]**:
  - Sử dụng Chromium CDP trên cổng `9222` độc lập với profile `~/.gemini/antigravity/chrome_vip`. Toàn bộ thao tác tải file DOCX/PDF bắt buộc đi qua giao thức `tab=7` và API tham số hóa TVPL.
- **RULE-1.3 [Lưu Trữ Song Song Dual-PDF & Vault Drive — ADR 0043]**:
  - Bản scan mờ lưu thành `sources/<slug>_raw_scan.pdf`. Bản Vector PDF kết xuất từ Word COM lưu thành `sources/<slug>.pdf` kèm cờ `pdf_origin: docx_vector_rendered` trong `metadata.yaml`. Đồng bộ cả 2 lên Google Drive Vault `CCBA_Legal_Vault`.

---

## Miền 2. 📐 Bóc Tách Đa Phương Thức & Chuẩn Hóa Toán Học KaTeX (Multimodal & KaTeX Integrity)

- **RULE-2.1 [Bóc Tách Xác Định MTEF MathType & Khử Tệp Đóng Kín — ADR 0040]**:
  - Bóc tách 100% công thức MathType nhị phân (MTEF v3/v5) từ OLE stream sang KaTeX, không qua OCR hay tốn AI token.
  - Áp dụng 4-Tier Hybrid Formula Fallback Engine. Vector WMF/EMF bắt buộc chuyển sang Dual-Format (SVG và PNG $\\ge 300\\text{ DPI}$). Nghiêm cấm lưu file `.wmf`/`.emf` nhị phân đóng kín.
- **RULE-2.2 [Cú Pháp Toán Học KaTeX Đa Dòng & Bảo Toàn Dấu — ADR 0038 & ADR 0044]**:
  - Trong các môi trường đa dòng (`aligned`, `cases`, `gather`), BẮT BUỘC dùng `\\qquad (X)` ở cuối dòng thay cho `\\tag{...}` để đảm bảo không sinh lỗi bôi đỏ KaTeX.
  - Bảo tồn tuyệt đối cặp ngoặc `\\left[` / `\\right]`. Tách chú thích hình `<!-- FIGURE: ... -->` ra khỏi khối KaTeX `$$`.
- **RULE-2.3 [Bảo Tồn Chú Thích Kẹp Giữa Sơ Đồ Đồ Họa — ADR 0039]**:
  - Bảo tồn 100% các đoạn `CHÚ THÍCH` và `CHÚ DẪN` kẹp giữa ảnh và tiêu đề hình. Xếp dọc đa tầng (Vertical Stack) lề an toàn $\\ge 40\\text{ px}$. Bắt buộc vượt qua Sub-Gate 11.2 Zero-Dropped Regulatory Notes.

---

## Miền 3. 📊 Cấu Trúc Bảng Biểu 2D & Mẫu Biểu Nguyên Tử (Deterministic Tables & Form Templates)

- **RULE-3.1 [Lưới Tọa Độ Ảo 2D & Forward-Fill Có Kiểm Soát — ADR 0041]**:
  - Thiết lập lưới tọa độ 2D từ `tblGrid`. Áp dụng Hierarchical Forward-Fill có kiểm soát cho ô gộp dọc (`vMerge`) trong CSV/JSON.
  - Phẳng hóa tiêu đề đa tầng bằng Em-dash ngữ nghĩa (`Tầng 1 — Tầng 2 — Tầng 3`). 100% CSV đạt chuẩn Zero Ragged Rows.
- **RULE-3.2 [Tách Rời Chú Thích Bảng & Định Tuyến Biểu Mẫu — ADR 0021 & ADR 0041]**:
  - Bóc tách 100% chú thích chân bảng (`footnotes`) ra khỏi ma trận dữ liệu quan hệ. Thoát an toàn ký tự `|` trong cell và KaTeX (`\\vert `).
  - Tách các biểu mẫu hành chính nguyên tử sang thư mục `templates/`, cấm để thư mục `templates/` rỗng.
- **RULE-3.3 [Định Danh Bảng Quy Chuẩn Đa Phần — ADR 0044]**:
  - Văn bản có nhiều phần (QCVN 07) bắt buộc bảng phải mang tiền tố mã định danh (ví dụ `bang_p01_01.csv`) và khai báo `part_id` trong `tables_catalog.json`.

---

## Miền 4. 🏛️ Chuẩn Hóa OpenXML DOM & Bảo Tồn Nguyên Văn Quy Phạm (OpenXML Sanitizer & Verbatim Parity)

- **RULE-4.1 [Tiền Xử Lý In-Memory DocxCanonicalSanitizer — ADR 0042]**:
  - Gọt sạch `w:rsid*`, loại bỏ `w:proofErr`, gộp run liền kề đồng nhất, chuẩn hóa Unicode NFC, tiêm `xml:space="preserve"`.
  - Giải nén borderless layout tables qua Multi-Factor Scoring (mật độ số liệu $\\ge 30\\%$). Bảo tồn tuyệt đối whitelist `<w:object>`, `<m:oMath>`, `<w:drawing>`.
- **RULE-4.2 [Bảo Tồn Nguyên Văn Quy Phạm 100% — ADR 0037 & ADR 0059]**:
  - NGHIÊM CẤM mọi hành vi tóm tắt, diễn đạt lại hoặc rút gọn thân văn bản quy phạm. Thân Markdown bắt buộc trích xuất xác định 1:1 từ DOCX và đạt Gate 11 Verbatim Parity $\\ge 98.0\\%$.
- **RULE-4.3 [Bảo Tồn Ký Tự Gốc & Thoát Ký Tự Gạch Đầu Dòng — ADR 0029 & ADR 0030]**:
  - Bảo tồn 100% dấu gạch đầu dòng `-` và `+` bằng cơ chế thoát ký tự `\\- ` và `&nbsp;&nbsp;\\+ `. Không dồn cục dòng; vượt qua `lint_visual_parity.py`.

---

## Miền 5. 🛡️ Hệ Thống Kiểm Định CI 12 Cổng & Hiệu Lực Pháp Lý Tuyệt Đối (CI Gates & Legal Governance)

- **RULE-5.1 [Rào Chắn Hiệu Lực Pháp Lý Tuyệt Đối — Từ 01/07/2026]**:
  - Mọi văn bản pháp luật viện dẫn BẮT BUỘC ĐANG CÓ HIỆU LỰC.
  - VĂN BẢN HIỆN HÀNH: **Luật Xây dựng 2025** (Luật số `135/2025/QH15`), **Nghị định 217/2026/NĐ-CP** (Quản lý Hoạt động Xây dựng — thay thế NĐ 175/2024 & NĐ 15/2021), **Nghị định 207/2026/NĐ-CP** (Quản lý Chất lượng & Bảo trì — thay thế NĐ 06/2021).
- **RULE-5.2 [12 Cổng Kiểm Định Nghiệm Thu Master CI Gate — ADR 0058]**:
  - Thực thi tự động: `python scripts/validate_legal_spoke.py`.
  - Tiêu chuẩn nghiệm thu 100%: 0 Errors, 0 Warnings, 100% Visual Parity, 100% Verbatim Match, 100% Valid Links, 100% PDF SHA-256 Match, 100% SVG/Cards Integrity.
- **RULE-5.3 [Single-User Multi-Device & Machine-State Decoupling]**:
  - Khi clone Spoke về nhiều máy (Windows, Linux, WSL), CẤM commit đường dẫn ổ đĩa tuyệt đối vào `workspace_context.yaml`. Đường dẫn Hub cô lập qua biến môi trường `CCBA_HUB_PATH`.
"""


def estimate_tokens(content: str) -> int:
    """Estimate token count for given text using 4 chars per token heuristic."""
    return math.ceil(len(content.encode("utf-8")) / 4)


def get_file_metrics(file_path: Path) -> dict[str, float | int | str | bool]:
    """Calculate size, lines, tokens, and budget status for a file."""
    if not file_path.exists():
        return {
            "exists": False,
            "bytes": 0,
            "kb": 0.0,
            "lines": 0,
            "tokens": 0,
            "valid": False,
        }

    raw_bytes = file_path.stat().st_size
    kb = round(raw_bytes / 1024, 2)
    content = file_path.read_text(encoding="utf-8")
    lines = len(content.splitlines())
    tokens = estimate_tokens(content)
    is_valid = kb <= DEFAULT_MAX_SIZE_KB

    return {
        "exists": True,
        "bytes": raw_bytes,
        "kb": kb,
        "lines": lines,
        "tokens": tokens,
        "valid": is_valid,
    }


def verify_invariants(content: str, invariants: list[str] | None = None) -> list[str]:
    """Return a list of missing invariant strings from content."""
    check_list = invariants if invariants is not None else REQUIRED_INVARIANTS
    return [inv for inv in check_list if inv not in content]


_ACTIVE_RULE_RE = re.compile(r"(?m)^\s*-\s+\*\*(RULE-\d+\.\d+)\b")
_MD_LINK_RE = re.compile(r"(\[[^\]]+\]\()([^)\s]+)(\))")


def _rebase_archive_links(content: str, source_file: Path, archive_dir: Path) -> str:
    """Rebase relative markdown links when copying source_file into a child archive_dir."""
    if archive_dir.resolve().parent != source_file.resolve().parent:
        return content

    archive_prefix = f"{archive_dir.name}/"

    def _replace(match: re.Match[str]) -> str:
        prefix, target, suffix = match.group(1), match.group(2), match.group(3)
        if target.startswith(("http://", "https://", "mailto:", "#", "/", "file://", "../")):
            return match.group(0)
        if target.startswith(archive_prefix):
            return f"{prefix}{target[len(archive_prefix) :]}{suffix}"
        clean_target = target.split("#", 1)[0].split("?", 1)[0]
        if target.startswith("wiki/") or (
            clean_target and (source_file.parent / clean_target).exists()
        ):
            return f"{prefix}../{target}{suffix}"
        return match.group(0)

    return _MD_LINK_RE.sub(_replace, content)


def _is_rule_deprecated(rule: str, text: str) -> bool:
    """Return True when rule is marked [DEPRECATED] on the same line (prefix or suffix)."""
    escaped = re.escape(rule)
    token = rf"\b{escaped}(?![.\-\/][\w\d])\b"
    pattern = rf"(?m)(?:^|[^\n])*(?:{token}[^\n]*?[\[\(]DEPRECATED[\]\)]|[\[\(]DEPRECATED[\]\)][^\n]*?{token})"
    return bool(re.search(pattern, text, re.IGNORECASE))


def find_dropped_rules(original_content: str, target_content: str) -> list[str]:
    """Return sorted active RULE-X.Y identifiers present in original_content but missing in target_content."""
    orig_rules = set(_ACTIVE_RULE_RE.findall(original_content))
    target_rules = set(_ACTIVE_RULE_RE.findall(target_content))
    missing = [
        rule
        for rule in (orig_rules - target_rules)
        if not _is_rule_deprecated(rule, target_content)
    ]
    return sorted(missing, key=lambda r: tuple(int(part) for part in r.split("-")[1].split(".")))


def backup_to_archive(source_file: Path, archive_dir: Path) -> tuple[Path, Path]:
    """Backup source file to a timestamped archive with rebased relative links."""
    archive_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamped_file = archive_dir / f"session_learnings_archive_{timestamp}.md"
    master_history_file = archive_dir / "session_learnings_history.md"

    raw_content = source_file.read_text(encoding="utf-8")
    rebased_content = _rebase_archive_links(raw_content, source_file, archive_dir)
    timestamped_file.write_text(rebased_content, encoding="utf-8")
    if not master_history_file.exists():
        shutil.copy2(timestamped_file, master_history_file)

    return timestamped_file, master_history_file


def run_check(
    file_path: Path,
    max_size_kb: float,
    invariants: list[str] | None = None,
    soft_target_kb: float = SOFT_TARGET_SIZE_KB,
) -> int:
    """CI check mode: Return 0 if file is within size budget, 1 otherwise."""
    metrics = get_file_metrics(file_path)
    if not metrics["exists"]:
        print(f"[FAIL] Target file does not exist: {file_path}", file=sys.stderr)
        return 1

    kb = float(metrics["kb"])
    if kb > max_size_kb:
        print(
            f"[FAIL] File size ({kb} KB) exceeds maximum allowed budget ({max_size_kb} KB).",
            file=sys.stderr,
        )
        return 1

    content = file_path.read_text(encoding="utf-8")
    missing = verify_invariants(content, invariants)
    if missing:
        print(f"[FAIL] Missing required architectural invariants: {missing}", file=sys.stderr)
        return 1

    if kb > soft_target_kb:
        print(
            f"[WARN] File size is {kb} KB <= {max_size_kb} KB (Hard Ceiling), but exceeds soft target ({soft_target_kb} KB). Compaction recommended."
        )
    else:
        print(f"[PASS] File size is {kb} KB <= {soft_target_kb} KB. All invariants preserved.")
    return 0


def run_stats(
    file_path: Path, max_size_kb: float, soft_target_kb: float = SOFT_TARGET_SIZE_KB
) -> None:
    """Print detailed file metrics and memory budget breakdown."""
    metrics = get_file_metrics(file_path)
    if not metrics["exists"]:
        print(f"File: {file_path} (NOT FOUND)")
        return

    kb = float(metrics["kb"])
    status = (
        "[PASS]"
        if kb <= soft_target_kb
        else ("[WARN: SOFT TARGET EXCEEDED]" if kb <= max_size_kb else "[OVERFLOW]")
    )
    print("=== Session Learnings Memory Metrics ===")
    print(f"File Path:        {file_path}")
    print(f"File Size:        {metrics['bytes']} bytes ({kb} KB)")
    print(f"Line Count:       {metrics['lines']} lines")
    print(f"Estimated Tokens: ~{metrics['tokens']:,} tokens")
    print(f"Soft Target:      {soft_target_kb} KB")
    print(f"Hard Ceiling:     {max_size_kb} KB")
    print(f"Status:           {status}")


def _report_compaction_result(old_size: int, new_size: int, max_size_kb: float) -> int:
    """Print compaction delta metrics and enforce max_size_kb budget."""
    new_kb = round(new_size / 1024, 2)
    saved_bytes = old_size - new_size
    reduction_pct = round((saved_bytes / old_size) * 100, 1) if old_size else 0.0

    print("[Success] Memory compaction completed:")
    print(f"  Before: {old_size:,} bytes (~{old_size // 4:,} tokens)")
    print(f"  After:  {new_size:,} bytes ({new_kb} KB, ~{new_size // 4:,} tokens)")
    print(f"  Saved:  {saved_bytes:,} bytes ({reduction_pct}% reduction)")

    if new_kb > max_size_kb:
        print(
            f"[Warning] Compacted size ({new_kb} KB) still exceeds {max_size_kb} KB",
            file=sys.stderr,
        )
        return 1
    return 0


def run_compact(
    file_path: Path,
    archive_dir: Path,
    max_size_kb: float,
    template: str | None = None,
    invariants: list[str] | None = None,
    allowed_rule_drops: Collection[str] = (),
) -> int:
    """Execute memory compaction, archive original, and verify zero-deletion & invariants."""
    if not file_path.exists():
        print(f"[Error] Source file not found: {file_path}", file=sys.stderr)
        return 1

    target_template = template if template is not None else COMPACTED_WORKING_MEMORY_TEMPLATE
    target_invariants = invariants if invariants is not None else REQUIRED_INVARIANTS

    source_text = file_path.read_text(encoding="utf-8")
    allowed_set = {r.strip() for r in allowed_rule_drops if r.strip()}
    dropped_rules = [
        r for r in find_dropped_rules(source_text, target_template) if r not in allowed_set
    ]
    if dropped_rules:
        print(
            f"[Error] Refusing lossy template overwrite — active rules would be dropped: {dropped_rules}. "
            "Edit session_learnings.md in-place or pass --allow-rule-drop-ids RULE-X.Y,...",
            file=sys.stderr,
        )
        return 1

    missing = verify_invariants(target_template, target_invariants)
    if missing:
        print(f"[Error] Compacted template missing invariants: {missing}", file=sys.stderr)
        return 1

    master_existed = (archive_dir / "session_learnings_history.md").exists()
    ts_file, master_file = backup_to_archive(file_path, archive_dir)
    print(f"[Archive] Full uncompressed file archived to: {ts_file.name}")
    master_action = "preserved (existing)" if master_existed else "initialized at"
    print(f"[Archive] Master history {master_action}: {master_file.name}")

    old_size = file_path.stat().st_size
    file_path.write_text(target_template.strip() + "\n", encoding="utf-8")
    return _report_compaction_result(old_size, file_path.stat().st_size, max_size_kb)


def _build_arg_parser() -> argparse.ArgumentParser:
    """Build argument parser for compact_session_learnings CLI."""
    parser = argparse.ArgumentParser(
        description="Session Learnings Memory Compaction Engine (ADR-0030, ADR-0057)."
    )
    parser.add_argument(
        "--profile",
        choices=["hub", "spoke"],
        default="hub",
        help="Profile to use (hub or spoke, default: hub).",
    )
    parser.add_argument("--target-dir", type=Path, default=None, help="Custom root directory.")
    parser.add_argument("--file", type=Path, default=None, help="Path to session_learnings.md.")
    parser.add_argument("--archive-dir", type=Path, default=None, help="Archive directory path.")
    parser.add_argument(
        "--max-size-kb",
        type=float,
        default=DEFAULT_MAX_SIZE_KB,
        help=f"Maximum size allowed in KB (default: {DEFAULT_MAX_SIZE_KB}).",
    )
    parser.add_argument("--check", action="store_true", help="Check size and invariants.")
    parser.add_argument("--stats", action="store_true", help="Display file metrics.")
    parser.add_argument("--compact", action="store_true", help="Execute compaction.")
    parser.add_argument(
        "--allow-rule-drop-ids",
        type=str,
        default="",
        help="Comma-separated active RULE-X.Y IDs explicitly permitted to drop during --compact.",
    )
    return parser


def _resolve_profile_targets(
    args: argparse.Namespace,
) -> tuple[Path, Path, str, list[str]]:
    """Resolve target file, archive directory, template, and invariants for the chosen profile."""
    if args.profile == "spoke":
        spoke_root = (
            args.target_dir.resolve()
            if args.target_dir
            else (HUB_ROOT.parent / "ccba-legal-knowledge").resolve()
        )
        target_file = args.file or (spoke_root / ".md" / "knowledge" / "session_learnings.md")
        target_archive = args.archive_dir or (spoke_root / ".md" / "knowledge" / "archive")
        return target_file, target_archive, SPOKE_COMPACTED_TEMPLATE, SPOKE_REQUIRED_INVARIANTS

    hub_root = args.target_dir.resolve() if args.target_dir else HUB_ROOT
    target_file = args.file or (hub_root / ".md" / "knowledge" / "session_learnings.md")
    target_archive = args.archive_dir or (hub_root / ".md" / "knowledge" / "archive")
    return target_file, target_archive, COMPACTED_WORKING_MEMORY_TEMPLATE, REQUIRED_INVARIANTS


def main() -> int:
    """CLI Entrypoint for compact_session_learnings."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    args = _build_arg_parser().parse_args()
    target_file, target_archive, target_template, target_invariants = _resolve_profile_targets(args)

    if args.check:
        return run_check(target_file, args.max_size_kb, target_invariants)
    if args.compact:
        allowed_ids = [r for r in str(args.allow_rule_drop_ids).split(",") if r.strip()]
        return run_compact(
            target_file,
            target_archive,
            args.max_size_kb,
            target_template,
            target_invariants,
            allowed_rule_drops=allowed_ids,
        )
    run_stats(target_file, args.max_size_kb)
    return 0


if __name__ == "__main__":
    sys.exit(main())
