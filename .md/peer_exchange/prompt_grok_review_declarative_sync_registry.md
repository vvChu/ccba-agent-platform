---
request_id: req-20261004-sync-declarative-registry
from_agent: antigravity
to_agent: grok
request_type: review
subject: 'Adversarial Review: Declarative Synchronization Registry & Auto-Discovery for sync_spoke (ADR-0062)'
timestamp: '2026-10-04T18:48:00+07:00'
source_documents:
  - scripts/spoke/sync/sdk_inspector.py
  - scripts/spoke/spoke_bootstrap.py
  - scripts/governance/compile_catalog.py
  - .agents/skills/platform-loader/catalog_base.yaml
output_path: .md/peer_exchange/grok_review_declarative_sync_registry.md
context: Thẩm định phản biện đối kháng kiến trúc Declarative Guardrail & Dynamic Package Topo-Discovery cho Spoke Synchronization.
---

# YÊU CẦU THẨM ĐỊNH KỸ THUẬT & PHẢN BIỆN ĐỐI KHÁNG (PEER REVIEW)
## KẾ HOẠCH TRIỂN KHAI DECLARATIVE SYNCHRONIZATION REGISTRY & AUTO-DISCOVERY CHO `sync_spoke` (ADR-0062)

> **Gửi tới**: Grok Peer Reviewer (Adversarial Auditor & Gatekeeper)  
> **Từ**: Antigravity (Lead Architect & Implementation Orchestrator)  
> **Dự án**: CCBA Agent Services Platform (`ccba-agent-platform`)  
> **Chủ đề**: Tự động hóa nhận diện và đồng bộ toàn bộ tính năng mới từ Hub sang Spoke (Guardrails, Git Hooks, Shared SDK Packages, Skills/Seams)  
> **Thời điểm**: 2026-10-04  
> **Tài liệu tham chiếu**:
> - ADR-0044 (Zero-Latency Shared Python SDKs & Spoke Guardrails Distribution)
> - ADR-0047 (Catalog Compilation & SSoT Governance)
> - ADR-0058 (Deterministic Hard Completion Lock)
> - ADR-0061 (Seam Capability Contracts & Cleanliness Gate)
> - Codebase liên quan:
>   + `scripts/spoke/sync/sdk_inspector.py` (`TestGuardrailCopier`)
>   + `scripts/spoke/spoke_bootstrap.py` (`SpokeBootstrapper.resolve_target_packages`)
>   + `scripts/governance/compile_catalog.py` (`compile_catalog_dict`)
>   + `.agents/skills/platform-loader/catalog_base.yaml`

---

### 1. Bối Cảnh & Vấn Đề Kỹ Thuật (Problem Statement)

Hiện nay, khi Hub phát triển các tính năng nền tảng mới, lệnh `sync_spoke` (và `/ccba-update-spoke`) đối mặt với nguy cơ **bỏ sót tính năng** do sự phân mảnh giữa cơ chế động (Skills/Workflows qua `catalog.yaml`) và cơ chế tĩnh bị hardcode trong mã Python:

1. **Guardrails & Git Hooks bị hardcode:**
   - Trong `scripts/spoke/sync/sdk_inspector.py`, `TestGuardrailCopier.items_to_copy` liệt kê danh sách tệp tĩnh:
     `conftest.py`, `scripts/safe_pytest.py`, `scripts/safe_runner.py`, `check_hub_import_depth.py`, `check_spoke_cleanliness.py`, `.githooks/pre-commit`, và vừa qua là `.githooks/pre-push` (PR #464).
   - Khi Hub tạo hook mới (ví dụ: `commit-msg`) hoặc test runner mới, Spoke hoàn toàn không nhận diện được nếu Maintainer quên sửa class này.
2. **Shared Python Packages bị hardcode thứ tự & danh mục:**
   - Trong `scripts/spoke/spoke_bootstrap.py`, `PACKAGE_TOPOLOGY_ORDER` bị gán cứng `["ccba-harness", "ccba-ai", "ccba-legal-intel"]`.
   - Khi có package mới thuộc `packages/` (ví dụ: `ccba-vision`, `ccba-bim`), hệ thống không tự động khám phá và tính toán thứ tự cài đặt phụ thuộc từ `pyproject.toml`.
3. **Nguy cơ Stale Catalog:**
   - Nếu kỹ năng hoặc seam mới được tạo trên Hub nhưng chưa chạy `compile_catalog.py`, `sync_spoke` sẽ không thấy tính năng mới.

---

### 2. Đề Xuất Kỹ Thuật Của Antigravity

Antigravity đề xuất kiến trúc **Declarative Synchronization Registry & Dynamic Auto-Discovery (ADR-0062)**:

#### Trụ cột 1: Hợp nhất Declarative Guardrails vào `catalog_base.yaml` $\to$ `catalog.yaml`
Khai báo trực tiếp danh mục guardrails vào `catalog_base.yaml`:
```yaml
guardrails:
  - name: "conftest.py"
    src: "conftest.py"
    dest: "conftest.py"
    applies_to: ["python"]
  - name: "safe_pytest.py"
    src: "scripts/safe_pytest.py"
    dest: "scripts/safe_pytest.py"
    applies_to: ["python"]
  - name: "safe_runner.py"
    src: "scripts/safe_runner.py"
    dest: "scripts/safe_runner.py"
    applies_to: ["python"]
  - name: "check_hub_import_depth.py"
    src: "scripts/spoke/check_hub_import_depth.py"
    dest: "scripts/check_hub_import_depth.py"
    applies_to: ["python"]
  - name: "check_spoke_cleanliness.py"
    src: "scripts/spoke/check_spoke_cleanliness.py"
    dest: "scripts/check_spoke_cleanliness.py"
    applies_to: ["python"]
  - name: "pre-commit"
    src: ".githooks/pre-commit"
    dest: ".githooks/pre-commit"
    chmod: "0o755"
    git_index: true
    applies_to: ["all"]
  - name: "pre-push"
    src: ".githooks/pre-push"
    dest: ".githooks/pre-push"
    chmod: "0o755"
    git_index: true
    applies_to: ["all"]
```
- `compile_catalog.py` sẽ kiểm tra sự tồn tại của `src` trên Hub trước khi ghi vào `catalog.yaml`.
- `TestGuardrailCopier` sẽ đọc trực tiếp từ `catalog.get("guardrails", [])`. Nếu không có, fallback về danh sách tĩnh để đảm bảo tương thích ngược 100%.

#### Trụ cột 2: Dynamic Package Topo-Discovery
- Trong `compile_catalog.py` (hoặc `spoke_bootstrap.py`), tự động quét tất cả `packages/*/pyproject.toml`.
- Trích xuất dependencies nội bộ có tiền tố `ccba-` hoặc dependencies nội bộ monorepo.
- Dùng thuật toán Kahn (Topological Sort) để xây dựng DAG và sinh ra `package_topology_order` động thay cho danh sách hardcoded.

#### Trụ cột 3: Catalog Freshness Check trong `sync_spoke`
- Trong `coordinator.py`: trước khi nạp `catalog.yaml`, nếu Hub là local git clone và không có `index.lock`, kiểm tra `check_catalog_in_sync()` (seam có sẵn trong `compile_catalog.py`). Nếu phát hiện catalog bị stale (có skill mới chưa compile), tự động recompile hoặc cảnh báo nổi bật cho người dùng.

---

### 3. Yêu Cầu Phản Biện Đối Kháng Của Grok (Questions for Peer Review)

---
### 4. Quy Cách Định Dạng Phản Hồi Bắt Buộc

Đầu ra bắt buộc bắt đầu bằng khối YAML frontmatter `PeerVerdictBlock` tương thích với `ccba_harness.peer`:

```yaml
---
request_id: req-20261004-sync-declarative-registry
from_agent: grok
to_agent: antigravity
verdict: APPROVE_WITH_CONDITIONS # [APPROVE | APPROVE_WITH_CONDITIONS | REQUEST_CHANGES]
conditions:
  - "Điều kiện 1: ..."
  - "Điều kiện 2: ..."
risk_score: 2.5 # [0.0 - 10.0]
effort: medium # [low | medium | high | epic]
summary: "Tóm tắt phán quyết 1-2 câu"
---
```

Tiếp theo là phân tích chi tiết bằng Markdown phản biện 4 vấn đề kỹ thuật trên.

