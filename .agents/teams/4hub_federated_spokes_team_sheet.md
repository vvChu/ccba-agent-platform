# 📋 Team Sheet: 4-Hubs × Federated Spokes Architecture Deep Research & Ecosystem Orchestration

> **Mã dự án / Feature:** `4hub_federated_spokes`  
> **GitHub Issue:** [#366](https://github.com/vvChu/ccba-agent-platform/issues/366)  
> **Branch:** `feat/issue-366-4hubs-federated-spokes`  
> **Trạng thái:** COMPLETED  
> **Orchestrator:** Antigravity Lead Orchestrator (Session `be5939ae-e6f8-4dc5-b0b8-66e42873b167`)  
> **Ngày khởi tạo:** 2026-09-25  
> **Mục tiêu tổng quát:** Nghiên cứu chuyên sâu toàn diện và thiết lập khung kiến trúc 4-Hubs × Federated Spokes kết nối hạ tầng DGX Spark, CCBA Agent Platform, Kho tri thức pháp lý, VvC Notes và Microsoft 365 IDOP.  
> **Non-Goals (Ranh giới loại trừ):** Không thực thi các lệnh phá hủy dữ liệu trực tiếp trên database production hoặc thay đổi quyền root hệ thống khi chưa qua kiểm định an toàn; không thay đổi schema đầu ra của các parser OKF hiện hành (Zero-Regression).

---

## 🏛️ Lớp 1: Accountability Mapping (Phân Quyền Phê Duyệt Con Người — 11 Ghế CCBA Charter 2026)

| Milestone | Tên Mốc Bàn Giao | Ghế CCBA Chịu Trách Nhiệm Duyệt | Cấp QC Bắt Buộc | Tiêu Chí Ký Duyệt (Sign-off Criteria) | Trạng Thái |
|:---:|:---|:---|:---:|:---|:---:|
| **M1** | Khảo sát Hạ tầng Compute & AI Gateway | `TRUONG_PHONG_RD_HTQT` | Cấp 1 (Technical) | Đo lường chính xác RAM Prisma, kiểm thử Virtual Key API `/key/generate`, xác thực Whisper GPU GB10. | ✅ COMPLETED |
| **M2** | Khảo sát An ninh OS Topology & POSIX ACLs | `CO_VAN_PHAP_LY_QA` | Cấp 2 (Governance) | Thắt chặt an toàn thư mục cá nhân (`~/.ssh`, `~/.gemini`), giải pháp POSIX ACLs `ccba-devs` bảo đảm quyền ghi đa người dùng. | ✅ COMPLETED |
| **M3** | Khảo sát Tích hợp Microsoft 365 IDOP | `IDOP_LEAD` | Cấp 2 (Governance) | Đối soát 59 SharePoint lists schema, thiết kế Outbound Bridge Worker xử lý lỗi 429 và dead-letter queue. | ✅ COMPLETED |
| **M4** | Khảo sát Federated RAG & Legal Corpus | `CHU_TRI_BO_MON` | Cấp 1 (Technical) | Phân rã độ trễ BGE-M3 (19.4s), kiểm tra Milvus `legal_docs_v11` (4,051 entities) và Neo4j Graph. | ✅ COMPLETED |
| **M5** | Ban hành Kiến trúc Tổng thể & ADR-0060 | `GIAM_DOC` | Cấp 3 (Leadership) | ADR-0060 hoàn chỉnh, báo cáo lưu trữ Knowledge Base, 100% CI pass theo Deterministic Hard Completion Lock. | ✅ COMPLETED |

---

## ⚙️ Lớp 2: Worker Assignments (Phân Công AI Subagents Độc Quyền)

> **Nguyên tắc an toàn (ADR 0035 / ADR 0053):**
> - Mỗi Worker chỉ đọc và khảo sát trong **Phạm Vi Seam (File Scope)** được cấp.
> - Workers là **Read-Only** đối với cây mã nguồn chính — toàn bộ kết quả phân tích xuất vào `Sandbox Output Dir`.
> - **Duy nhất Orchestrator** được quyền tổng hợp, ghi file chính thức và commit Git (Single-Writer Protocol).
> - **Giới hạn đồng thời:** Tối đa 2-3 workers/batch (Worker Cap).

### Batch 1: Hạ Tầng Tính Toán & Hệ Điều Hành

#### 🤖 Worker 1: `compute-gateway-specialist`
- **Mục tiêu nhiệm vụ:** Khảo sát chi tiết tiến trình LiteLLM, Prisma Query Engine RAM footprint (10.22 GB), bảng `LiteLLM_SpendLogs` (347k dòng), thiết kế script cắt tỉa định kỳ, kiểm thử Virtual Key API `/key/generate`, và cấu hình Speaches Whisper GPU GB10.
- **Phạm vi Seam (Exclusive File Scope — Read Only):**
  - `/home/vvc/Codebase/dgx-spark-toolkit/services/ai-gateway/`
  - `/home/vvc/Codebase/dgx-spark-toolkit/docker-compose.yml`
  - `/home/vvc/Codebase/dgx-spark-toolkit/services/whisper-local/`
  - `packages/ccba-ai/src/ccba_ai/`
- **Sandbox Output Dir:** `.system_generated/scratch/teamwork/4hubs_federated_spokes/worker_1/`
- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  1. Báo cáo định lượng nguyên nhân tiêu thụ RAM của Prisma Query Engine.
  2. Dự thảo script SQL cắt tỉa `LiteLLM_SpendLogs` an toàn (retention 30 ngày) và script bash bảo trì.
  3. Đặc tả chi tiết Virtual Key API payload cho Spoke IDOP, BIM Planner, Legal Knowledge.
- **Chính sách Timeout:** 10 phút.
- **Trạng thái:** `COMPLETED`

#### 🤖 Worker 2: `os-topology-specialist`
- **Mục tiêu nhiệm vụ:** Khảo sát cấu trúc Linux Multi-User trên DGX Spark (`vvc`, `tta`, `tat`, `mtt`), phản biện rủi ro an ninh khi dùng `chmod o+x /home/vvc`, thiết kế script POSIX ACLs chuẩn hóa (`setup_ccba_devs_acls.sh`) với default inheritance và bảo vệ thư mục riêng tư.
- **Phạm vi Seam (Exclusive File Scope — Read Only):**
  - Hệ thống Linux permissions (`/home/vvc`, `/home/vvc/Codebase`, `/home/vvc/ccba`, `/home/vvc/VvC_Notes`)
  - `docs/rules/execution_guardrails.md`
  - `AGENTS.md`
- **Sandbox Output Dir:** `.system_generated/scratch/teamwork/4hubs_federated_spokes/worker_2/`
- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  1. Phân tích cụ thể các tệp nhạy cảm bị lộ nếu mở `chmod o+x /home/vvc`.
  2. Dự thảo hoàn chỉnh script `setup_ccba_devs_acls.sh` sử dụng `setfacl` với nhóm `ccba-devs`.
  3. Hướng dẫn cấu hình môi trường virtualenv `.venv` và `umask 0002` cho multi-user.
- **Chính sách Timeout:** 10 phút.
- **Trạng thái:** `COMPLETED`

---

### Batch 2: Tích Hợp Doanh Nghiệp & Dữ Liệu Pháp Lý

#### 🤖 Worker 3: `m365-bridge-specialist`
- **Mục tiêu nhiệm vụ:** Khảo sát toàn diện 59 SharePoint Lists schema tại `IDOP-CCBA-WAY/datamodel/sharepoint/lists/`, thiết kế kiến trúc chi tiết cho module Python Outbound Bridge Worker (`msal` + `httpx`), xử lý mã 429 throttling và cơ chế dead-letter queue.
- **Phạm vi Seam (Exclusive File Scope — Read Only):**
  - `/home/vvc/ccba/IDOP-CCBA-WAY/datamodel/sharepoint/lists/`
  - `/home/vvc/ccba/IDOP-CCBA-WAY/tools/config/environments.psd1`
  - `scripts/tests/test_idop_schema_compatibility.py`
  - `docs/adr/0043-idop-active-dev-resilience-and-fallback.md`
- **Sandbox Output Dir:** `.system_generated/scratch/teamwork/4hubs_federated_spokes/worker_3/`
- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  1. Phân loại 59 schemas theo độ ưu tiên đồng bộ (CDE, CRM, Hợp đồng, Phân bổ).
  2. Thiết kế chi tiết module Python Bridge Worker không phụ thuộc PowerShell.
  3. Đặc tả chiến lược xử lý rate limit (Token Bucket) và Dead-Letter Queue.
- **Chính sách Timeout:** 10 phút.
- **Trạng thái:** `COMPLETED`

#### 🤖 Worker 4: `federated-rag-specialist`
- **Mục tiêu nhiệm vụ:** Khảo sát Milvus Standalone (collection `legal_docs_v11` 4,051 entities), Neo4j Graph (19 nodes, 12 rels), phân rã độ trễ RAG BGE-M3 (19.4s), khảo sát cấu trúc liên kết `ccba-legal-knowledge` với `ccba-agent-platform` (Issue #232).
- **Phạm vi Seam (Exclusive File Scope — Read Only):**
  - `/home/vvc/Codebase/dgx-spark-toolkit/services/rag-service/`
  - `/home/vvc/ccba/ccba-legal-knowledge/`
  - `.md/knowledge/issues/issue-232.md`
  - `packages/ccba-ai/src/ccba_ai/mcp_server.py`
- **Sandbox Output Dir:** `.system_generated/scratch/teamwork/4hubs_federated_spokes/worker_4/`
- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  1. Định lượng các bước trong RAG pipeline và nguyên nhân BGE-M3 chiếm 19.4s.
  2. Đề xuất phương án tối ưu hóa (vLLM embedding profile / GPU dedicated worker).
  3. Kế hoạch đồng bộ hai chiều kho dữ liệu OKF v2.4 và SHA-256 Gazette Corpus.
- **Chính sách Timeout:** 10 phút.
- **Trạng thái:** `COMPLETED`

---

## 🔍 Lớp 3: Success Auditor Verification (Cổng Nghiệm Thu Độc Lập)

| Kiểm Tra | Lệnh / Công Cụ | Tiêu Chuẩn Đạt | Kết Quả |
|:---|:---|:---|:---:|
| **Living ADR Parity & Schema** | `python scripts/sync_hub_adr_matrix.py --check` | 100% ADRs hợp lệ, README và Matrix in sync | ✅ PASSED |
| **Catalog Manifest Parity** | `python scripts/governance/compile_catalog.py --check` | Catalog SSOT đồng bộ hoàn toàn | ✅ PASSED |
| **Maskara Security Scan** | `python scripts/governance/check_spoke_cleanliness.py` | Exit code 0, không rò rỉ secrets | ✅ PASSED |
| **Unit Test Suite** | `pytest packages/ccba-ai/tests packages/ccba-legal-intel/tests/test_federated_rag.py -q` | 194/194 Pass, 100% tests đạt | ✅ PASSED |
| **Deterministic Hard Completion Lock** | `python -m ccba_harness verify-patch --preset ci` | Exit code 0 bắt buộc (ADR-0058) | ✅ PASSED |

---

## 📝 Nhật Ký Tiến Độ (Progress Log)

- `2026-09-25 21:00`: Tạo GitHub Issue #366 và kích hoạt Claim Lock `feat/issue-366-4hubs-federated-spokes`.
- `2026-09-25 21:10`: Khởi tạo Team Sheet đa tác tử và chuẩn bị sandbox cho 4 workers.
- `2026-09-25 21:13`: Worker 2 (`os-topology-specialist`) hoàn thành xuất sắc báo cáo và script `setup_ccba_devs_acls.sh`.
- `2026-09-25 21:16`: Worker 1 (`compute-gateway-specialist`) hoàn thành báo cáo chuyên sâu LiteLLM, script cắt tỉa PostgreSQL, payload Virtual Keys, và Speaches Whisper GPU GB10.
- `2026-09-25 21:18`: Kích hoạt Batch 2 (Worker 3 và Worker 4).
- `2026-09-25 21:22`: Worker 3 (`m365-bridge-specialist`) hoàn thành phân tích 59 SharePoint lists schema, module Python `ccba_m365_bridge.py` với rate limiting và DLQ.
- `2026-09-25 21:24`: Worker 4 (`federated-rag-specialist`) hoàn thành giải mã nguyên nhân BGE-M3 swap VRAM (0.28s GPU vs 21.6s memory swap), tối ưu vLLM memory, và liên kết OKF v2.4 SHA-256 sidecars.
- `2026-09-25 21:25`: Lead Orchestrator tổng hợp toàn bộ báo cáo, ban hành ADR-0060 và lưu trữ Knowledge Base.
