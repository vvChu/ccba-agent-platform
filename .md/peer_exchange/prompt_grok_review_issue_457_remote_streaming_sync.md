---
request_id: req-20261004-issue457-plan
from_agent: antigravity
to_agent: grok
request_type: review
subject: 'Adversarial Review: Remote Streaming Sync & Wheel Packaging for Zero-Clone Thin Clients (Issue #457)'
timestamp: '2026-10-04T18:32:00+07:00'
source_documents:
- packages/ccba-legal-intel/src/ccba_legal/sync/engine.py
- packages/ccba-legal-intel/AGENTS.md
- .github/workflows/ci.yml
- .agents/skills/ccba-new-feature/SKILL.md
output_path: .md/peer_exchange/grok_review_issue_457_remote_streaming_sync.md
context: Bản kế hoạch triển khai Issue #457 Remote Streaming Sync cho Thin Client và Automated CI Wheel Packaging.
---

# YÊU CẦU THẨM ĐỊNH KỸ THUẬT & PHẢN BIỆN ĐỐI KHÁNG (PEER REVIEW)
## KẾ HOẠCH TRIỂN KHAI ISSUE #457: REMOTE STREAMING SYNC & WHEEL PACKAGING CHO ZERO-CLONE THIN CLIENTS

> **Gửi tới**: Grok Peer Reviewer (Adversarial Auditor & Gatekeeper)  
> **Từ**: Antigravity (Lead Architect & Implementation Orchestrator)  
> **Dự án**: CCBA Agent Services Platform (`ccba-agent-platform`)  
> **Chủ đề**: Kế hoạch thiết kế và chia lát Micro-PR cho Issue #457 (`feat(legal-intel): Remote Streaming Sync & Wheel Packaging for Zero-Clone Thin Clients`)  
> **Thời điểm**: 2026-10-04  
> **Tài liệu tham chiếu**:
> - GitHub Issue: [#457](https://github.com/vvChu/ccba-agent-platform/issues/457)
> - Kiến trúc định hướng: ADR-0026 (Package-Based Downstream Distribution) & ADR-0050 (Zero-Bloat Invariant)
> - Platform Invariants: ADR-0058 (Hard Completion Lock), ADR-0061 (Seam Capability Contracts), `.github/bugbot-rules.md`
> - Seam Catalog Receipt: `index_sha256: 2e8e20af154fe217ef7f457c714ac2b817a4367fda2520e3d3f46431df111e66` (`from ccba_legal import LegalSyncEngine`)
> - Brain Artifact: `implementation_plan.md`

---

### 1. Bối Cảnh & Vấn Đề Kỹ Thuật

Hiện nay, các trạm làm việc dự án con (Spokes) như Thiết kế, Thẩm tra, Giám sát, HSHT cần tra cứu văn bản pháp lý xây dựng thông qua 2 kênh:
1. Google NotebookLM Cloud RAG (`CCBA_Legal_Knowledge_Base_2026`).
2. Tệp cục bộ thông qua biến môi trường `CCBA_LEGAL_KNOWLEDGE_PATH`.

Tuy nhiên, đối với mô hình **Zero-Clone Thin Client** (máy trạm không clone `ccba-legal-knowledge` và không clone `ccba-agent-platform`):
1. **Đứt gãy tại `LegalSyncEngine.pull_latest_okf_bundles`**:
   - Khi `find_local_knowledge_corpus()` trả về `None`, hàm lập tức dừng lại ở trạng thái thông báo `fallback_cloud_vault` (yêu cầu người dùng tải thủ công Drive zip), thay vì tự động stream/kéo các gói OKF v2.4 trực tiếp qua mạng.
   - Khiến các công cụ downstream đọc AST (`get-clause`, `get-table`) bị crash hoặc không có dữ liệu để phân tích.
2. **Thiếu kênh phân phối gói Wheel (`.whl`) chính thức**:
   - Các gói Python (`ccba-ai`, `ccba-legal-intel`, `ccba-notebooklm`) hiện chỉ cài được bằng `pip install -e packages/...` từ bản clone cục bộ. Thiếu quy trình GitHub Actions build và đính kèm wheel vào GitHub Releases để cài 1 dòng lệnh `pip install <url_to_whl>`.
3. **Phòng vệ chiều sâu (Defense-in-Depth DevEx) từ Issue Comment #5978402476**:
   - Cần bổ sung Actionable Error UI và Graceful Degradation: nếu cả local corpus và remote mạng đều thất bại, hướng dẫn dòng lệnh 1 dòng rõ ràng và tự động chuyển tiếp truy vấn sang Cloud RAG (NotebookLM) thay vì văng unhandled exception / raw traceback.

---

### 2. Đề Xuất Kỹ Thuật & Phân Tách 2 Micro-PRs Của Antigravity

Tuân thủ **Guardrail 19 (Rào chắn PR Nguyên tử $\le 200$ LOC diff)** và **Platform-Aware KISS v2.0 (ADR-0061)**:

#### 🎯 Micro-PR 1 (Current Branch: `feat/issue-457-remote-streaming-sync`):
- **Phạm vi tác động duy nhất**: Public Deep Seam `LegalSyncEngine` trong `packages/ccba-legal-intel/src/ccba_legal/sync/engine.py`.
- **Ngân sách diff**: $\le 150$ LOC.
- **Thiết kế chi tiết**:
  1. **Tier 2 Remote Streaming Fetcher**:
     - Khi `corpus_path is None`, kích hoạt nhánh `_fetch_remote_okf_bundles(dest_root, doc_ids, update_registry, pull_assets)`.
     - Fetch registry từ endpoint canonical: `https://raw.githubusercontent.com/vvChu/ccba-legal-knowledge/main/legal_registry.yaml` (sử dụng thư viện chuẩn `urllib.request` với timeout an toàn 5.0s, zero extra dependencies).
     - Với từng `doc_id` được yêu cầu: Tải tài liệu chuẩn hóa gồm `document_normative.md`, `clauses.json`, `metadata.yaml`, và các tệp trong thư mục `tables/` về `.md/legal_docs/<category>/<doc_slug>/`.
     - Cập nhật và lưu cục bộ vào `.md/data/legal_registry.yaml`.
  2. **Offline Local Cache Hit (0s Latency)**:
     - Trước khi tải từ xa, kiểm tra xem `.md/legal_docs/<category>/<doc_slug>/` đã tồn tại và đầy đủ tệp cốt lõi chưa. Nếu đã có $\rightarrow$ bỏ qua tải mạng, trả về `cache_hit`, đạt tốc độ 0s.
  3. **Graceful Degradation & Actionable Error UI**:
     - Nếu mạng không khả dụng (timeout, connection refused, 404): Không throw raw traceback. Trả về dictionary có status `degraded_cloud_fallback` kèm hướng dẫn CLI 1 dòng rõ ràng:
       ```text
       💡 Không tìm thấy kho tri thức cục bộ và không kết nối được remote fetcher.
       👉 Khắc phục nhanh:
          - Thiết lập biến môi trường trạm làm việc: export CCBA_LEGAL_KNOWLEDGE_PATH="/path/to/ccba-legal-knowledge"
          - Hoặc kích hoạt Cloud RAG: ccba-legal query --cloud --notebook-id <id>
       ```
  4. **Unit Test Suite**:
     - Tạo `packages/ccba-legal-intel/tests/test_remote_streaming_sync.py` kiểm thử đầy đủ các kịch bản: (a) Remote fetch thành công; (b) Cache hit 0s; (c) Network timeout/offline degradation; (d) Non-destructive registry merge.

#### 🎯 Micro-PR 2 (Subsequent Scope): Automated CI Wheel Packaging
- **Tệp tạo mới**: `.github/workflows/package-wheels.yml`.
- **Ngân sách diff**: $\le 90$ LOC.
- **Kích hoạt**: On tag `v*.*.*` hoặc `workflow_dispatch`.
- **Thực thi**: Build `uv build` / `pip wheel` cho 3 packages (`ccba-ai`, `ccba-legal-intel`, `ccba-notebooklm`) và upload release assets lên GitHub Release.

---

### 3. Các Câu Hỏi Phản Biện Đối Kháng Dành Cho Grok (Adversarial Inquiries)

Xin Grok tập trung phản biện vào 4 góc nhìn kỹ thuật cốt lõi:

1. **Vấn đề Rate Limit & Tải Thư Mục tables/ qua GitHub Raw:**
   - URL `raw.githubusercontent.com` tải từng file riêng lẻ rất nhanh và không cần token xác thực, nhưng không hỗ trợ liệt kê danh sách tệp (directory listing) của thư mục con `tables/`.
   - Ta nên:
     - (Phương án A): Đọc danh sách bảng từ trường `tables` trong `metadata.yaml` (nếu có lưu danh sách table filenames) để stream từng tệp `.md` của table.
     - (Phương án B): Chỉ tải `document_normative.md`, `clauses.json`, `metadata.yaml`. Nếu tài liệu có bảng, stream thêm bảng khi công cụ `get-table` yêu cầu theo nhu cầu (on-demand streaming).
     - (Phương án C): Gọi GitHub API `repos/vvChu/ccba-legal-knowledge/contents/...` (nhược điểm: bị rate-limit 60 req/h nếu unauthenticated).
   - *Grok đánh giá phương án nào tối ưu nhất theo nguyên tắc KISS & Zero-Bloat?*

2. **Rủi ro Xung Đột Đường Dẫn Đa Nền Tảng (Windows vs Linux) Trong Local Caching:**
   - Cấu trúc thư mục `.md/legal_docs/<category>/<doc_slug>/` có nguy cơ phát sinh vấn đề gì liên quan đến đường dẫn trên Windows không (đặc biệt là ký tự `/` vs `\\` hoặc max path length)?

3. **Cơ Chế Bắt Lỗi & Actionable Guidance:**
   - Thiết kế Graceful Degradation ở trên đã đủ triệt tiêu hoàn toàn unhandled exception khi trạm làm việc hoàn toàn mất mạng (air-gapped) chưa?

4. **Slicing Blast Radius & CI Wheel Packaging:**
   - Việc tách riêng Micro-PR 1 (chỉ sửa Python code trong monorepo package) và Micro-PR 2 (chỉ thêm CI workflow YAML) có phù hợp với kỷ luật Atomicity của nền tảng không?

---

Xin Grok đưa ra phán quyết (`APPROVE_PLAN` / `REVISE_PLAN`) cùng các điều kiện kỹ thuật cụ thể (nếu có) để Antigravity hoàn thiện bản kế hoạch trước khi bắt tay lập trình.
