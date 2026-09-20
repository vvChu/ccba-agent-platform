# CCBA Agent Services Platform (Hub)

> **Bộ Não Trung Tâm & Nền Tảng Dịch Vụ AI Agent** cho Hệ Sinh Thái CCBA và Ngành Xây Dựng / BIM Việt Nam.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Architecture: Hub-and-Spoke](https://img.shields.io/badge/Architecture-Hub--and--Spoke-teal.svg)](#kien-truc-hub-and-spoke)
[![AI Gateway: 50+ Models](https://img.shields.io/badge/AI%20Gateway-50+%20Models-orange.svg)](#ccba-ai--ai-gateway-client)

---

## 🏛️ Kiến Trúc Hub-and-Spoke (Hub & Spoke Ecosystem)

CCBA Agent Services Platform vận hành theo kiến trúc **Hub-and-Spoke**:

```
                              ┌─────────────────────────────────────────┐
                              │            CCBA HUB (Bộ Não)             │
                              │  ├── Hiến pháp AGENTS.md (Layer 1)      │
                              │  ├── 73 Kỹ năng (Skills) & 68 Archived  │
                              │  ├── 9 Service Packages (ccba-*)        │
                              │  └── Spoke Synchronizer Engine          │
                              └────────────────────┬────────────────────┘
                                                   │
                   ┌───────────────────────────────┼───────────────────────────────┐
                   │ sync_spoke.py                 │ sync_spoke.py                 │ sync_spoke.py
                   ▼                               ▼                               ▼
       ┌───────────────────────┐       ┌───────────────────────┐       ┌───────────────────────┐
       │   SPOKE: SOFTWARE     │       │   SPOKE: DELIVERY     │       │    SPOKE: HYBRID      │
       │ (Phần mềm & Tooling)  │       │ (Kho Tri thức Pháp lý)│       │ (Nghiên cứu & Hub Ext)│
       │ mode: software        │       │ mode: delivery        │       │ mode: hybrid          │
       └───────────────────────┘       └───────────────────────┘       └───────────────────────┘
```

- **CCBA Hub (`ccba-agent-platform`)**: Repository trung tâm lưu trữ toàn bộ tài sản trí tuệ chung, bao gồm Hiến pháp tối cao [`AGENTS.md`](.agents/AGENTS.md), 73 kỹ năng AI (và 68 workflows được lưu trữ/hợp nhất theo ADR-0056), 9 gói thư viện lõi và công cụ điều phối đồng bộ.
- **Dự Án Con (Spokes)**: Các repositories chuyên biệt (như `ccba-legal-knowledge`, `ccba-qc-web-app`, các dự án thẩm tra công trình cụ thể). Spoke kế thừa toàn bộ năng lực AI của Hub thông qua cơ chế **Reuse-First Gate** và công cụ đồng bộ **`sync_spoke.py`**.

---

## 📁 Cấu Trúc Thư Mục Repository

```
ccba-agent-platform/                    ← Hub Repository
├── AGENTS.md                          ← Minimal Root Constitution (Layer 1 Anchor)
├── CLAUDE.md                          ← Claude Code Cross-Agent Parity Bridge
├── docs/
│   ├── adr/                           ← Architectural Decision Records (ADRs)
│   └── rules/                         ← Progressive Disclosure Rules (Guardrails, Git, Code Quality)
├── .agents/
│   ├── AGENTS.md                      ← Layer 1 Constitution Mirror
│   ├── skills/                        ← AI Agent skills (<!-- SKILL_COUNT_START -->73<!-- SKILL_COUNT_END --> skills) <!-- Last verified: 2026-09-18 -->
│   │   ├── ccba-ai-gateway-sdk/       ←   Kết nối AI Gateway (50+ models)
│   │   ├── ccba-spoke-adopter/        ←   Tiếp nhận Brownfield Spoke an toàn
│   │   ├── ccba-sharepoint-iac/       ←   SharePoint Lists Schema & IaC
│   │   ├── ccba-legal-document-tracker/ ← Theo dõi & rà soát VBPL
│   │   ├── ccba-completion-checklist/ ←   Quản lý HSHT công trình
│   │   ├── ccba-ai-qc-pccc-audit/     ←   Thẩm tra thiết kế PCCC AI
│   │   ├── ccba-codebase-design/      ←   Nguyên lý thiết kế Deep Modules
│   │   └── ...                        ←   Và 59+ kỹ năng chuyên dụng khác
│   ├── workflows/                     ← Workflows lưu trữ an toàn (.md.bak, hợp nhất vào skills)
│   └── templates/                     ← Biểu mẫu hành chính & kỹ thuật dùng chung
├── .md/                               ← Central Knowledge Base
│   ├── knowledge/                     ←   Tài liệu nghiên cứu, ADRs, Session Learnings
│   ├── seminars/                      ←   Agenda & biên bản thảo luận
│   └── extracted_docs/                ←   Văn bản pháp luật trích xuất thô
├── packages/                          ← 9 Internal Service Modules (pip installable)
│   ├── ccba-harness/                  ←   Testing harness, Two-Stage Decision Framework & GPI Calculator (ADR 0057), evals engine, singleton locks & process monitors
│   ├── ccba-ai/                       ←   AI Gateway SDK (v1.2.0), drop_params embedding, reasoning streaming token floor & timeout scaling
│   ├── ccba-maskara/                  ←   Secret detection, PII redaction & privacy guard
│   ├── ccba-ooxml/                    ←   OOXML presentation builder (Swiss Minimalist & Storytelling), Word Form Filler (auto_map_fields, Dual-Engine Word COM & Layout Guard) & Excel macro calculation
│   ├── ccba-pdf-prep/                 ←   PDF Vision Preprocessor (in-memory streaming, tiling, title-block, chunks)
│   ├── ccba-notebooklm/               ←   Google NotebookLM wrapper & Mock client
│   ├── ccba-legal-intel/              ←   Legal intelligence connectors, OKF v2.2 GoldStandardProcessor & VisualParityAuditor
│   ├── ccba-qc-core/                  ←   Multi-disciplinary design audit engine (PCCC, MEP, Architectural compliance)
│   └── mdconverter/                   ←   Document-to-Markdown converter (PDF/DOCX/HTML)
├── scripts/                           ← CLI Tooling & Governance Engines
│   ├── spoke/                         ←   Spoke governance, adoption & synchronization engines
│   ├── governance/                    ←   Unified Governance & Cross-Reference validation
│   ├── hooks/                         ←   Git hooks & guards (privacy, naming, simplify)
│   ├── shell/                         ←   Developer PowerShell & Bash productivity aliases
│   ├── tests/                         ←   Unit test suites cho Hub tools
│   ├── validation/                    ←   Release cleanliness & hermetic verification CLI
│   ├── adopt_spoke.py                 ←   Brownfield Spoke Adoption CLI Delegate
│   ├── validate_cross_references.py   ←   Constitution Cross-Reference Matrix Validator
│   ├── session_cleanup.py             ←   Workspace & Session Cleanup CLI Delegate
│   ├── sync_spoke.py                  ←   Spoke Synchronizer CLI Delegate
│   ├── safe_pytest.py                 ←   Safe Scoped Pytest Execution Wrapper
│   ├── safe_runner.py                 ←   Detached Background Command Runner
│   ├── validate_skills.py             ←   Skill Integrity & Schema Validator
│   └── validate_docs.py               ←   Documentation Accuracy & Drift Validator
├── conftest.py                        ← Pytest Scoped Guardrail Hook
└── pyproject.toml                     ← Workspace config
```

---

## 📦 9 Service Modules (Gói Dịch Vụ Cốt Lõi)

Toàn bộ các gói dịch vụ nằm trong thư mục `packages/` được thiết kế dưới dạng Deep Modules độc lập, có thể cài đặt trực tiếp vào môi trường Python của kỹ sư:

| Package | Mô tả Chức năng | Lệnh Cài Đặt (Editable Mode) |
| :--- | :--- | :--- |
| **`ccba-harness`** | Testing harness, Two-Stage Granularity Decision Framework & GPI Calculator (ADR 0057), Multi-Disciplinary Evals Engine v2/v3 (Legal Verbatim Provenance ADR 0059, PCCC Parametric, Uniclass 200 BIM, Three-Tier Slicing & Docker Ephemeral Sandbox), Singleton Process Locks, giám sát tệp tin và tiến trình an toàn. | `pip install -e "packages/ccba-harness"` |
| **`ccba-ai`** | AI Gateway SDK (v1.2.0) — Kết nối 50+ models qua 1 endpoint, hỗ trợ gemini-embedding-2 drop_params, streaming ceiling 16k tokens, auto-timeout scaling, bóc tách ChatResult.thinking và Circuit Breaker. | `pip install -e "packages/ccba-ai"` |
| **`ccba-maskara`** | Quét và che giấu (redact) thông tin nhạy cảm (API Keys, PII) trong log/tệp trước khi commit. | `pip install -e "packages/ccba-maskara"` |
| **`ccba-ooxml`** | Thao tác DOM file Office (.docx, .pptx, .doc), điền form biểu mẫu tự động bảo toàn bố cục (`WordFormFiller.auto_map_fields` & `FormLayoutGuard`), bảo vệ file mẫu bất biến (`TemplateProtectionError`), sinh slide PowerPoint tự động chuẩn Swiss Minimalist & Storytelling With You (`DeckBuilder`), bóc tách và tái dựng cấu trúc bảng phức tạp (`TableReconstructor`), kiểm định tính toàn vẹn XML và tính toán công thức Excel (`recalc_xlsx`). | `pip install -e "packages/ccba-ooxml"` |
| **`ccba-pdf-prep`** | Tiền xử lý PDF cho AI Vision: In-memory streaming (Zero Storage Bloat), phân mảnh thông minh (Tiling), bóc tách khung tên bản vẽ, chia nhỏ chunks. | `pip install -e "packages/ccba-pdf-prep"` |
| **`ccba-notebooklm`** | Tích hợp Google NotebookLM Cloud RAG, sinh Audio Overview, hỗ trợ Mock Client chạy test offline. | `pip install -e "packages/ccba-notebooklm"` |
| **`ccba-legal-intel`** | Pipeline tự động hóa TVPL VIP, đóng gói bộ chuẩn OKF Bundle v2.2 (`OKFBundlePackager`, `GoldStandardProcessor`), giải mã nhị phân công thức MathType MTEF (ADR 0040), kiểm định Visual Parity Gate 4, bóc tách phụ lục, AST diffing và hợp nhất Văn Bản Hợp Nhất (VBHN). | `pip install -e "packages/ccba-legal-intel"` |
| **`ccba-qc-core`** | Động cơ thẩm tra thiết kế đa bộ môn (PCCC, MEP, Kiến trúc), phân tích sai lệch quy chuẩn và xuất báo cáo đối soát. | `pip install -e "packages/ccba-qc-core"` |
| **`mdconverter`** | Chuyển đổi PDF/DOCX/HTML sang Markdown chuẩn, phục hồi bảng biểu vỡ và tiêm anchor điều khoản. | `pip install -e "packages/mdconverter[dev,llm]"` |

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy Trên Máy Client (Quick Start)

Dành cho Kỹ sư khi clone `ccba-agent-platform` về máy cá nhân để sử dụng hoặc phát triển tính năng mới:

### 1. Điều Kiện Tiên Quyết (Prerequisites)
- **Python**: Phiên bản `>= 3.10` (Khuyến nghị **Python 3.11**).
- **Tailscale VPN**: Kết nối vào mạng Server Spark (`100.83.192.30`) để truy cập AI Gateway nội bộ và các models GPU không tốn chi phí.
- **LibreOffice** *(Tùy chọn)*: Cài đặt nếu cần sử dụng tính năng tính toán công thức Excel headless (`recalc_xlsx`) trong `ccba-ooxml`.

---

### 2. Cài Đặt Môi Trường Ảo & Toàn Bộ 9 Packages

Mở terminal tại thư mục gốc dự án và thực hiện tuần tự:

```bash
# 1. Khởi tạo môi trường ảo Python
python -m venv .venv

# 2. Kích hoạt môi trường ảo
# Trên Windows (PowerShell / Command Prompt):
.venv\Scripts\activate
# Trên Linux / macOS:
source .venv/bin/activate

# 3. Cài đặt toàn bộ 9 internal packages ở chế độ Editable (-e)
pip install -e "packages/ccba-harness" \
            -e "packages/ccba-ai" \
            -e "packages/ccba-maskara" \
            -e "packages/ccba-ooxml" \
            -e "packages/ccba-pdf-prep" \
            -e "packages/ccba-notebooklm" \
            -e "packages/ccba-legal-intel" \
            -e "packages/ccba-qc-core" \
            -e "packages/mdconverter[dev,llm]"
```

---

### 3. Thiết Lập Biến Môi Trường (.env)

Khởi tạo tệp `.env` từ mẫu chuẩn:

```bash
# Trên Windows:
copy .env.example .env

# Trên Linux / macOS:
cp .env.example .env
```

Kiểm tra tệp `.env` cục bộ đã trỏ đúng vào AI Gateway Server:
```env
AI_GATEWAY_URL=http://100.83.192.30:8090/v1
AI_GATEWAY_KEY=your-spark-gateway-key
AI_MODEL=qwen-local-primary
```

---

### 4. Kiểm Tra & Xác Thực Hệ Thống (Verification)

Chạy các lệnh kiểm thử nhanh sau để bảo đảm toàn bộ hệ thống hoạt động hoàn hảo:

```bash
# 1. Thăm dò kết nối AI Gateway (Lấy danh sách 50+ models online thời gian thực)
python -c "from ccba_ai import ai; print('✅ AI Gateway Models:', len(ai.models()), 'models available!')"

# 2. Chạy toàn bộ Fast Test Suite (< 2.0s per test, loại trừ test mạng nặng)
pytest -m "not slow"

# 3. Chạy Governance Gate (Kiểm định 73 Skills & Toàn bộ Tài liệu Markdown)
python scripts/validate_skills.py
python scripts/validate_docs.py

# 4. Kiểm tra Linting Codebase
ruff check packages/ scripts/
```

---

## 🌐 Quy Trình Phát Triển Dự Án Con (From Hub to Spokes)

Sau khi thiết lập Hub trên máy, Kỹ sư có thể phát triển các dự án con (Spokes) độc lập:

### 1. Khởi Tạo Dự Án Spoke Mới (`/ccba-init-spoke`)
Tại thư mục Spoke mới, tạo tệp `.md/workspace_context.yaml` để khai báo ngữ cảnh:
```yaml
project:
  name: my-bim-audit-spoke
  mode: software  # Chọn: software | delivery | hybrid
  type: Thẩm tra thiết kế
  hub_path: D:/GitHubProjects/ccba-agent-platform
```

> **Quy ước Workspace Mode (`project.mode`):**
> - **`software`**: Dành cho các dự án ứng dụng web, CLI, tooling (.md tối giản, output $\rightarrow$ `docs/`).
> - **`delivery`**: Dành cho kho tri thức văn bản pháp luật, tài sản tri thức OKF Bundles (.md đầy đủ 10 thư mục con).
> - **`hybrid`**: Dành cho các Hub mở rộng hoặc Spoke R&D cần cả domain knowledge lẫn tooling.

---

### 2. Kế Thừa Dịch Vụ Hub (Reuse-First Gate)
Trong mã nguồn Python tại Spoke, Kỹ sư chỉ cần cài đặt `ccba-ai` từ Hub và import sử dụng trực tiếp:
```python
from ccba_ai import ai, ModelArchetype

# Gọi LLM với tự động định tuyến Archetype & Circuit Breaker
reply = ai.chat("Soát xét sự phù hợp giữa bản vẽ PCCC và QCVN 06:2022/BXD", model=ModelArchetype.REASONING)
print(reply)
```

---

### 3. Đồng Bộ Hóa Kỹ Năng & Workflows (Hub ➔ Spoke)
Khi Hub cập nhật kỹ năng mới hoặc muốn nạp thêm workflow vào Spoke:
```bash
# Chạy từ thư mục Hub trỏ đến Spoke:
python scripts/sync_spoke.py --spoke "D:/GitHubProjects/my-bim-audit-spoke"

# Hoặc đồng bộ một kỹ năng cụ thể:
python scripts/sync_spoke.py --spoke "D:/GitHubProjects/my-bim-audit-spoke" --sync-item "ccba-ai-qc-pccc-audit"
```

---

### 4. Đóng Góp Tính Năng Ngược Lên Hub (`/ccba-issue-to-hub` & `/ccba-contribute-to-hub`)
Hệ thống chuẩn hóa chu trình đóng góp 2 chiều:
- **Đề xuất Ý tưởng / RFC:** Kích hoạt `/ccba-issue-to-hub` để tự động tổng hợp bối cảnh, soạn RFC và tạo GitHub Issue lên Hub repo.
- **Đóng góp Mã nguồn & Tests:** Kích hoạt `/ccba-contribute-to-hub` để đóng gói code, package, tests và mở Pull Request lên Hub kèm Self-Healing CI Gate.

---

## ⚡ Kỹ Năng & Slash Commands Thường Dùng

| Lệnh Slash | Mô tả Nghiệp vụ |
| :--- | :--- |
| **`/ccba-init-spoke`** | Khởi tạo dự án Spoke mới đạt chuẩn kiến trúc CCBA Hub-and-Spoke. |
| **`/ccba-update-spoke`** | Cập nhật các kỹ năng và test guardrails mới nhất từ Hub về Spoke. |
| **`/ccba-issue-to-hub`** | Soạn thảo RFC và tạo GitHub Issue đề xuất ý tưởng/tính năng mới lên Hub. |
| **`/ccba-create-pr`** | Tự động phân giải base branch, đóng gói kiểm thử và mở Pull Request đa Spoke. |
| **`/ccba-contribute-to-hub`** | Đóng gói mã nguồn, tests và mở Pull Request lên Hub kèm Self-Healing CI. |
| **`/ccba-issue-tree`** | Phân rã bài toán phức tạp theo cây vấn đề McKinsey MECE (Why, What, How) và quản trị vòng đời. |
| **`/ccba-legal-advisor`** | Tư vấn & giải đáp pháp lý xây dựng: Phỏng vấn thích ứng và xuất Phiếu Ý kiến Pháp lý. |
| **`/ccba-ai-qc-pccc-audit`** | Thẩm tra lỗi thiết kế đa bộ môn (PCCC, MEP, Kiến trúc) qua Semantic Map-Reduce. |
| **`/ccba-markdown-document-processing`** | Chuyển đổi PDF/Word sang Markdown cấu trúc cao bằng `mdconverter`. |
| **`/ccba-codebase-design`** | Quét module nông, sinh sơ đồ Mermaid trực quan và làm sâu module. |
| **`/ccba-legal-document-tracker`** | Theo dõi, so sánh và phân tích các văn bản pháp luật xây dựng Việt Nam với VBHNEngine. |
| **`/ccba-notebooklm-connector`** | Kết nối Google NotebookLM để thực hiện RAG query và tạo Audio Overview podcast. |
| **`/ccba-session-retrospective`** | Tổng kết tri thức cuối phiên làm việc, tiến hóa kỹ năng và kích hoạt Governance Gate. |
| **`/ccba-implement`** | Triển khai lập trình khép kín: TDD $\rightarrow$ Eval Gate $\rightarrow$ Code Review $\rightarrow$ Commit. |
| **`/ccba-to-spec`** | Soạn thảo Đặc tả Kỹ thuật Spec và phân rã tác vụ độc lập từ ý tưởng ban đầu. |

---

## 🛡️ Rào Chắn Quản Trị & Đóng Góp (Governance & Quality Standards)

- **Hiến pháp Tối cao**: Tuân thủ 100% các quy định trong [`.agents/AGENTS.md`](.agents/AGENTS.md).
- **Nguyên lý KISS (Keep It Simple, Stupid)**: Luôn ưu tiên giải pháp đơn giản, giao diện nhỏ (Small Interface) sau đó mới triển khai sâu (Deep Implementation).
- **Kỷ Luật Kiểm Thử 2 Tầng (2-Tier Test Discipline)**: Toàn bộ Unit Tests thông thường bắt buộc chạy dưới **2.0 giây**. Các test nặng/mạng phải gắn `@pytest.mark.slow`.
- **An Toàn Đa Nền Tảng (P2.2)**: Tuyệt đối không can thiệp stream `sys.stdout.reconfigure()` ở root scope module để bảo vệ luồng bắt test của Pytest trên Windows.
- **Bảo Mật Tuyệt Đối**: Nghiêm cấm hardcode API Keys; toàn bộ mã nguồn phải pass qua `ccba-maskara` trước khi commit.

---

## 📜 License

Phát triển bởi **CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng** (IBST BIM Team) phục vụ sự phát triển của ngành Xây dựng & Tư vấn số hóa Việt Nam.  
Phát hành theo giấy phép **MIT License**.
