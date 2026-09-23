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
import shutil
import sys
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_FILE = HUB_ROOT / ".md" / "knowledge" / "session_learnings.md"
DEFAULT_ARCHIVE_DIR = HUB_ROOT / ".md" / "knowledge" / "archive"
DEFAULT_MAX_SIZE_KB = 10.0

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

COMPACTED_WORKING_MEMORY_TEMPLATE = """# 🧠 CCBA Platform Knowledge Base: Active Architectural Invariants (Compacted Working Memory)

> **Phạm vi áp dụng:** Hub (`ccba-agent-platform`) & Spokes (`ccba-legal-knowledge`, etc.)
> **Tiêu chuẩn:** OKF v2.2, ADR 0016, 0021, 0030, 0031, 0033, 0035, 0037, 0046, 0051, 0053, 0056, 0057.
> **Tra cứu Chi tiết Lịch sử & Bug Post-Mortems:** [session_learnings_history.md](archive/session_learnings_history.md) | Ngưỡng bộ nhớ: $\\le 10\\text{ KB}$

---

## Miền 1. 🏛️ Kiến Trúc, Phân Tầng Kỹ Năng & Quản Trị Seams (Architecture & Governance)

- **RULE-1.1 [ADR 0057 — Khung 2 Giai Đoạn & Chỉ Số GPI]**:
  - *Cổng 0 (Determinism)*: Tác vụ thuần giải thuật/I/O $\\rightarrow$ chuyển xuống Monorepo Package Deep Seams (`packages/*/src/`). Kỹ năng `SKILL.md` tuyệt đối không chứa code logic nghiệp vụ trần.
  - *Cổng 1 (Orchestration)*: Tác vụ đa luồng/StateGraph/HITL $\\rightarrow$ chuyển lên Tier 3 Composite Orchestrator (short-circuit Cổng 1, không tính GPI).
  - *Công thức GPI*: $\\mathbf{GPI} = (S \\times 2.5) + (K \\times 2.0) + (A \\times 2.0) - (P \\times 1.5)$. Nếu $\\text{GPI} < 12.0 \\rightarrow$ Tier 2A (`references/*.md`); Nếu $\\text{GPI} \\ge 12.0 \\rightarrow$ Tier 2B (`.agents/skills/ccba-<name>/`). User Rituals (`disable-model-invocation: true`) bắt buộc $A = 1.0$.
- **RULE-1.2 [ADR 0053 — Single-Writer Protocol Cho Orchestrators]**:
  - Mọi quy trình điều phối đa tác tử (`ccba-teamwork`, swarms) bắt buộc tuân thủ Single-Writer: Lead Orchestrator là thực thể duy nhất ghi mã nguồn và logs. Subagents phân tán chỉ xuất Unified Diff / Structured Patch vào `.system_generated/scratch/`, nghiêm cấm sửa file trực tiếp.
- **RULE-1.3 [ADR 0035 — Deep Modules, Seams & Zero-Exemption AST]**:
  - Thin Seam: Module/package chỉ bộc lộ `__all__` hoặc `__init__.py`. Tuyệt đối không import private submodule `_*`.
  - Zero-Exemption: Gỡ bỏ toàn bộ bypass hardcoded theo tên file trong `check_dependency_contracts.py`. Tệp thử nghiệm lịch sử chuyển vào `archive/`.
- **RULE-1.4 [ADR 0033 & ADR 0056 — Spoke Directory Hygiene & Zombie Prevention]**:
  - Cấu trúc `.\\.md\\`: Gốc chỉ chứa cấu hình (`workspace_context.yaml`); dữ liệu nạp vào `.\\.md\\extracted_docs\\`; tri thức vào `.\\.md\\knowledge\\`; thử nghiệm vào `.\\.md\\archive\\`.
  - Spoke Synchronizer (`coordinator.py`): Đổi tên workflows cũ thành `.md.bak` (nhãn `DEPRECATED_MIGRATED_TO_SKILL`), xóa thư mục cũ theo `SKILL_DEPRECATION_ALIASES`, không tự sinh thư mục `.agents/workflows/` rỗng.
- **RULE-1.5 [ADR 0037 & ADR 0051 — Two-Tier Traceability Matrix & Status Regex]**:
  - Tier 1: Platform Constitution (55 Hub ADRs). Tier 2: Spoke Domain Decisions (`docs/adr/`). Bảo toàn bảng tùy chỉnh qua thẻ `<!-- CUSTOM_SECTIONS_START -->` ... `<!-- CUSTOM_SECTIONS_END -->`.
  - Regex bắt trạng thái ADR phải bao quát tiền tố list marker `(?:\\*|-)?\\s*\\*\\*\\s*Status:\\s*\\*\\*`. Lọc bỏ file non-ADR (`notes.md`, `template.md`).
- **RULE-1.6 [ADR 0044 — Federated RAG & Dynamic Import]**:
  - Tier 0 import Tier 1 dùng `try: from ccba_legal.xxx import yyy; except ImportError: pass`. Cache BM25 Singleton cấp module; Cache Embedding `.npy` bắt buộc kiểm tra SHA-256 qua `.sha256` sidecar.

---

## Miền 2. 🔒 Chất Lượng Mã Nguồn & Rào Chắn CI (Code Quality & Strict Testing)

- **RULE-2.1 [Strict Mypy Type-Safety — Chống Anti-Pattern AP9.1]**:
  - NGHIÊM CẤM dùng `[[tool.mypy.overrides]] ignore_errors = true` trong `pyproject.toml`. Ép kiểu tường minh cho binary I/O, fonts, dicts. Chỉ dùng `ignore_missing_imports = true` cho third-party thiếu stubs.
- **RULE-2.2 [Spoke CI Gates Verification Pipeline]**:
  - 5 Cổng Zero-Tolerance bắt buộc trước khi nghiệm thu: (1) `lint_visual_parity.py`, (2) `validate_legal_spoke.py`, (3) `test_converter_regression.py`, (4) `verify_all_docs_against_pdf.py` (SHA-256 Valid), (5) `verify_cross_links.py`.
- **RULE-2.3 [Fast Feedback Loops (< 2s) & Parity Contract Tests]**:
  - Unit tests nòng cốt phải đạt SLA $< 2\\text{s}$ (`pytest -m fast`). `test_cli_doc_parity.py`: Khớp nối 100% giữa CLI và `SKILL.md`. `drift_auditor.py`: Miễn trừ `not filepath.startswith("scripts/tests/")` chống cảnh báo giả.
- **RULE-2.4 [Relative Link Resolution Depth]**:
  - Tệp trong `.agents/skills/<skill>/SKILL.md` trỏ về package monorepo dùng 3 cấp lùi: `../../../packages/<pkg>`.
  - Tệp trong `references/<ref>.md` trỏ về root monorepo dùng 4 cấp lùi: `../../../../`.
  - CẤM TUYỆT ĐỐI commit đường dẫn `file:///` hoặc URI `conversation://` vào kho Git.

---

## Miền 3. 📜 Chuẩn Mực Pháp Lý & Dữ Liệu Hiện Hành (Legal & Data Standards)

- **RULE-3.1 [Rào Chắn Hiệu Lực Pháp Lý Tuyệt Đối — Từ 01/07/2026]**:
  - MỌI văn bản pháp luật viện dẫn (kể cả mock fixtures, demo slides) BẮT BUỘC ĐANG CÓ HIỆU LỰC (CURRENT / IN-FORCE).
  - VĂN BẢN HIỆN HÀNH: **Luật Xây dựng 2025** (Luật số `135/2025/QH15`), **Nghị định 217/2026/NĐ-CP** (Quản lý Hoạt động Xây dựng — thay thế NĐ 175/2024 & NĐ 15/2021), **Nghị định 207/2026/NĐ-CP** (Quản lý Chất lượng & Bảo trì — thay thế NĐ 06/2021).
  - TUYỆT ĐỐI CẤM dùng NĐ 175/2024, NĐ 15/2021, NĐ 06/2021 làm căn cứ pháp lý hiện tại.
- **RULE-3.2 [TVPL VIP 3-Tier Download Priority — ADR 0031]**:
  - Tier 1 (`part=-100`): VIP Digital Vector PDF (Mỏ neo Pháp lý Tối thượng).
  - Tier 2 (`part=-1&docx=1`): VIP OpenXML Word Document (Nguồn dữ liệu gốc vàng nạp `docx_converter.py`).
  - Tier 3 (`part=0`): Gazette Scan PDF (Dự phòng).
- **RULE-3.3 [Làm Sạch Bảng Biểu & Chú Thích Pháp Lý]**:
  - Footnote: Khử lặp số thứ tự: `re.sub(r"^[0-9]+[)\\.]\\s*", "", fn_clean).strip()`. Bảng Markdown nhận diện qua cặp dòng tiêu đề và phân cách `| :--- |`.

---

## Miền 4. 🛠️ Điều Phối & Quy Trình Agent (Workflows, Commands & Review)

- **RULE-4.1 [Entry Point Duy Nhất Khi Có Issue ID: `/ccba-new-feature`]**:
  - Khi đã xác định Issue ID, LUÔN đề xuất `/ccba-new-feature #<id>` làm hành động tiếp theo (bao trọn 8 bước Factory Model).
  - CẤM TUYỆT ĐỐI nhảy thẳng vào `/ccba-implement`, `/ccba-to-spec`, `/ccba-to-tickets`.
- **RULE-4.2 [Slash Command Parity & Active Commands SSOT]**:
  - BẮT BUỘC đối chiếu `catalog.yaml` trước khi đề xuất bất kỳ lệnh `/command`. Chỉ kỹ năng có `command: /...` mới được gắn tiền tố `/`.
  - Tài liệu tham chiếu trong `references/*.md` (Tier 2A) CẤM dùng tiền tố `/` (hướng dẫn người dùng gọi Master Skill kèm nạp reference).
- **RULE-4.3 [Tiêu Chí Hoàn Thành Đa Nhánh & DRY Reference]**:
  - Tiêu chí hoàn thành phải có nhánh kiểm chứng cho từng cờ (`--compare`, `--port`, `--improve`, `--copy-raw`).
  - Quy tắc kết hợp cờ chỉ tuyên bố 1 lần duy nhất tại mục `Kết hợp không hợp lệ` trong `MODES.md`.
- **RULE-4.4 [GitHub Copilot Multi-Tier Review Gating]**:
  - Quét `author.login` thay vì `user.login`. Bắt buộc kiểm tra `### 🟡 Changes recommended` và review `body` của Copilot kể cả khi trạng thái là `COMMENTED`. Cấm merge nếu chưa sửa hoặc giải trình.

---

## Miền 5. 💻 Hạ Tầng & Môi Trường Máy Trạm (Windows, Chrome CDP & Tooling)

- **RULE-5.1 [Chromium VIP Session Engine & CDP Browser Target]**:
  - Profile độc lập: `~/.gemini/antigravity/chrome_vip` trên cổng `9222`. Lệnh `Browser.setDownloadBehavior` BẮT BUỘC gọi qua Browser Target WebSocket (`http://127.0.0.1:{port}/json/version`).
  - Toàn bộ DOM Selectors đăng nhập, xác nhận phiên TVPL kế thừa tập trung từ `TVPLSelectors` trong `selectors.py`.
- **RULE-5.2 [Windows Path Quotes & Hook Protection]**:
  - Khi Antigravity IDE trên Windows tự bọc đường dẫn `hooks.json` trong dấu ngoặc kép `"C:\\..."`, vô hiệu hóa bằng `{}` và khóa thuộc tính `IsReadOnly = $true` trên PowerShell chống lỗi `Cannot find module`.
  - Thiết lập timeout $\\ge 60\\text{s}$ cho integration tests có scan metadata trên Windows.
- **RULE-5.3 [Query Sanitization & Turnstile Bypass]**:
  - Query TVPL có dấu `/`, `:`, `-` phải thay bằng dấu cách (`quote_plus`) chống lỗi IIS mã hóa `%2F`.
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


def backup_to_archive(source_file: Path, archive_dir: Path) -> tuple[Path, Path]:
    """Backup source file to a timestamped archive and update master history."""
    archive_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamped_file = archive_dir / f"session_learnings_archive_{timestamp}.md"
    master_history_file = archive_dir / "session_learnings_history.md"

    content = source_file.read_text(encoding="utf-8")
    timestamped_file.write_text(content, encoding="utf-8")
    shutil.copy2(timestamped_file, master_history_file)

    return timestamped_file, master_history_file


def run_check(file_path: Path, max_size_kb: float, invariants: list[str] | None = None) -> int:
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

    print(f"[PASS] File size is {kb} KB <= {max_size_kb} KB. All invariants preserved.")
    return 0


def run_stats(file_path: Path, max_size_kb: float) -> None:
    """Print detailed file metrics and memory budget breakdown."""
    metrics = get_file_metrics(file_path)
    if not metrics["exists"]:
        print(f"File: {file_path} (NOT FOUND)")
        return

    kb = float(metrics["kb"])
    status = "[PASS]" if kb <= max_size_kb else "[OVERFLOW]"
    print("=== Session Learnings Memory Metrics ===")
    print(f"File Path:        {file_path}")
    print(f"File Size:        {metrics['bytes']} bytes ({kb} KB)")
    print(f"Line Count:       {metrics['lines']} lines")
    print(f"Estimated Tokens: ~{metrics['tokens']:,} tokens")
    print(f"Budget Limit:     {max_size_kb} KB")
    print(f"Status:           {status}")


def run_compact(
    file_path: Path,
    archive_dir: Path,
    max_size_kb: float,
    template: str | None = None,
    invariants: list[str] | None = None,
) -> int:
    """Execute memory compaction, archive original, and verify invariants."""
    if not file_path.exists():
        print(f"[Error] Source file not found: {file_path}", file=sys.stderr)
        return 1

    target_template = template if template is not None else COMPACTED_WORKING_MEMORY_TEMPLATE
    target_invariants = invariants if invariants is not None else REQUIRED_INVARIANTS

    # Step 1: Backup original
    ts_file, master_file = backup_to_archive(file_path, archive_dir)
    print(f"[Archive] Full uncompressed file archived to: {ts_file.name}")
    print(f"[Archive] Master history updated at:        {master_file.name}")

    # Step 2: Validate template invariants
    missing = verify_invariants(target_template, target_invariants)
    if missing:
        print(f"[Error] Compacted template missing invariants: {missing}", file=sys.stderr)
        return 1

    # Step 3: Write compacted content
    old_size = file_path.stat().st_size
    file_path.write_text(target_template.strip() + "\n", encoding="utf-8")
    new_size = file_path.stat().st_size

    new_kb = round(new_size / 1024, 2)
    saved_bytes = old_size - new_size
    reduction_pct = round((saved_bytes / old_size) * 100, 1)

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


def main() -> int:
    """CLI Entrypoint for compact_session_learnings."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Session Learnings Memory Compaction Engine (ADR-0030, ADR-0057)."
    )
    parser.add_argument(
        "--profile",
        choices=["hub", "spoke"],
        default="hub",
        help="Profile to use (hub or spoke, default: hub).",
    )
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=None,
        help="Custom root directory for profile (e.g. path to ccba-legal-knowledge).",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=None,
        help="Path to session_learnings.md file.",
    )
    parser.add_argument(
        "--archive-dir",
        type=Path,
        default=None,
        help="Directory to store historical archives.",
    )
    parser.add_argument(
        "--max-size-kb",
        type=float,
        default=DEFAULT_MAX_SIZE_KB,
        help="Maximum size allowed in KB (default: 10.0).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if file meets size and invariant requirements.",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Display file metrics and budget status.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Execute compaction and archive original.",
    )

    args = parser.parse_args()

    # Resolve profile targets
    if args.profile == "spoke":
        spoke_root = (
            args.target_dir.resolve()
            if args.target_dir
            else (HUB_ROOT.parent / "ccba-legal-knowledge").resolve()
        )
        target_file = (
            args.file if args.file else (spoke_root / ".md" / "knowledge" / "session_learnings.md")
        )
        target_archive = (
            args.archive_dir if args.archive_dir else (spoke_root / ".md" / "knowledge" / "archive")
        )
        target_template = SPOKE_COMPACTED_TEMPLATE
        target_invariants = SPOKE_REQUIRED_INVARIANTS
    else:
        hub_root = args.target_dir.resolve() if args.target_dir else HUB_ROOT
        target_file = (
            args.file if args.file else (hub_root / ".md" / "knowledge" / "session_learnings.md")
        )
        target_archive = (
            args.archive_dir if args.archive_dir else (hub_root / ".md" / "knowledge" / "archive")
        )
        target_template = COMPACTED_WORKING_MEMORY_TEMPLATE
        target_invariants = REQUIRED_INVARIANTS

    if args.check:
        return run_check(target_file, args.max_size_kb, target_invariants)

    if args.stats:
        run_stats(target_file, args.max_size_kb)
        return 0

    if args.compact:
        return run_compact(
            target_file, target_archive, args.max_size_kb, target_template, target_invariants
        )

    # Default action if no flags provided
    run_stats(target_file, args.max_size_kb)
    return 0


if __name__ == "__main__":
    sys.exit(main())
