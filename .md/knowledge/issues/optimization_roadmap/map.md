# 🗺️ Wayfinder Map: Lộ Trình Tối Ưu Hóa Hệ Sinh Thái Hub-Spoke (Hub & Legal Knowledge Spoke)

> **Mã định danh bản đồ:** `wayfinder:optimization_roadmap`  
> **Trạng thái:** Active & Frontier Open  
> **Ngày khởi tạo:** 2026-08-15  
> **Phạm vi tác động:** `ccba-agent-platform` (Hub) & `ccba-legal-knowledge` (Spoke)

---

## 🎯 1. Điểm Đích (Destination)

Xây dựng hệ sinh thái Hub-Spoke hoàn thiện, đạt độ gắn kết cao nhưng không ghép nối chặt (high leverage, loose coupling, zero-duplication):
1. **Đóng gói Deep Seam Tái Sử Dụng:** Bóc tách và đưa công nghệ xử lý bảng kỹ thuật phức tạp (unmerging rowspan/colspan, đa cấp từ QCVN 06) từ Spoke lên package dùng chung trên Hub (`packages/ccba-ooxml` hoặc `packages/ccba-legal-intel`).
2. **Đồng Bộ Chuẩn Đóng Gói OKF:** Hợp nhất chuẩn biểu diễn tri thức OKF giữa Hub (`OKFBundlePackager` v2.0) và Spoke (OKF v0.2 `clauses.json`, `qa_benchmark.json`, `tables/`) để tương thích 100% hai chiều.
3. **Chu trình Tự Động Hóa Toàn Trình (End-to-End Autonomous Ingestion):** Khép kín luồng từ TVPL VIP Crawler trên Hub $\rightarrow$ Đẩy vào Gold Standard Ingestion trên Spoke $\rightarrow$ Tự động sinh QA benchmark và kiểm định qua `validate_legal_spoke.py`.

---

## 📝 2. Ghi Chú & Rào Chắn (Notes & Guardrails)

* **Hiến pháp Hub-Spoke (ADR 0036 & ADR 0037):** Tuyệt đối không sao chép dữ liệu văn bản từ Spoke về Hub. Mọi tham chiếu đều dùng Con trỏ động (`[legal_knowledge_kb]`).
* **Reuse-First Gate (P7.1):** Kiểm tra `catalog.yaml` và các Deep Seams hiện hữu trước khi viết bất kỳ hàm mới nào.
* **Kỷ Luật Kiểm Thử 2 Tầng (P3.1):** Mọi unit test mới trên Hub phải chạy dưới 2.0s; các test tích hợp cào/chuyển đổi nặng gắn `@pytest.mark.slow`.
* **KISS Principle:** Ưu tiên tái cấu trúc và bóc tách tinh gọn thay vì sinh thêm các lớp trừu tượng thừa thãi.

---

## ⚖️ 3. Quyết Định Đã Chốt (Decisions So Far)

* **[D01: Phân Ranh Giới Kiến Trúc Rõ Ràng](../../../../docs/adr/0036-brownfield-spoke-adoption-and-governance-engine.md):** Hub giữ vai trò Nền tảng (Platform Framework & Shared Deep Modules); Spoke `ccba-legal-knowledge` giữ vai trò Trung tâm Dữ liệu & Tri thức Pháp điển (Domain Knowledge Corpus & Execution).
* **[D02: Zero-Duplication SSOT](../../../../docs/adr/0037-constitution-traceability-matrix-and-zero-duplication.md):** Giải phóng 110,647 dòng tệp `.txt`/`.md` lịch sử trên Hub, chỉ lưu logic xử lý và tham chiếu qua `catalog.yaml: legal_knowledge_kb`.
* **[D03: Độc Lập Vận Hành Của Spoke]:** Spoke sở hữu CLI độc lập (`spoke_cli.py`), test suite riêng (28 passed) và validator 4 tầng riêng (`validate_legal_spoke.py`).
* **[D04: Định Vị Deep Seam Bóc Tách Bảng Phức Tạp `TableReconstructor` trong `packages/ccba-ooxml`]:**
  - **Vị trí chuẩn:** `packages/ccba-ooxml/src/ccba_ooxml/tables.py` (vì bảng biểu Word xuất hiện ở mọi bộ môn: Pháp lý, QC Thẩm tra, Hồ sơ hoàn thành, Hợp đồng).
  - **DTO chuẩn hóa:** `StructuredTable` (gồm `table_id`, `title`, `headers`, `rows`, `footnotes`) cung cấp 3 phương thức xuất khẩu: `.to_markdown()`, `.to_json()`, `.to_csv()`.
  - **Public Interface:** `TableReconstructor.extract_docx_tables(docx_path)` và `TableReconstructor.replace_markdown_tables(md_path, tables)`.
  - **Tái sử dụng:** `packages/ccba-legal-intel` và các Spokes (`ccba-legal-knowledge`, `idop-ccba-way`) tái sử dụng trực tiếp qua `from ccba_ooxml import TableReconstructor, StructuredTable`.
* **[D05: Chuẩn Hóa Đặc Tả Gói Tri Thức OKF Bundle v2.0](../../../../docs/adr/0038-unified-okf-v2-bundle-specification.md):**
  - **Cấu trúc SSOT:** Tệp `metadata.yaml` độc lập trong từng bundle directory (loại bỏ frontmatter trong `.md`).
  - **AST `clauses.json`:** Mảng danh sách phẳng có bổ sung `node_type` và `parent_id` (tra cứu $O(1)$ và tái dựng cây AST trong 1 vòng lặp).
  - **Đối chuẩn `qa_benchmark.json`:** Mở rộng 5 trường (`question`, `answer`, `anchor`, `citation`, `ground_truth_context`) phục vụ đo lường và rào chắn `LegalGroundingGate`.
* **[D06: Giao Thức Chuyển Giao Tự Động Crawl $\rightarrow$ Ingestion](../../../../docs/adr/0039-autonomous-crawler-to-spoke-ingestion-protocol.md):**
  - **Quy trình 4 bước:** Crawl (Hub) $\rightarrow$ Sandbox Temp $\rightarrow$ Ingest & Validate (Spoke) $\rightarrow$ Auto-Purge Temp & Sync Cloud.
  - **Lệnh Launcher thống nhất:** `ccba-platform ingest-legal <TVPL_URL> [--spoke <name>]`.
  - **Zero-Duplication Invariant:** Tự động xóa sạch tệp `.docx` tạm sau khi Spoke xác nhận `Exit Code 0`.

---

## 🧭 4. Danh Sách Ticket Tại Biên Giới (Frontier Tickets)

Mọi câu hỏi kiến trúc cốt lõi tại Biên giới đã được giải quyết trọn vẹn:

### 🎫 Ticket 1: [Research] Thiết kế Deep Seam Bóc Tách Bảng Phức Tạp (Complex Table Reconstructor)
* **Loại:** `Research [AFK]`
* **Assignee:** Antigravity Agent
* **Trạng thái:** `COMPLETED` ✅ (Đã chốt thiết kế tại Quyết định D04 — `packages/ccba-ooxml`)

### 🎫 Ticket 2: [Research/Grilling] Hợp Nhất Hợp Đồng Cấu Trúc OKF Bundle (OKF Schema Alignment)
* **Loại:** `Grilling [HITL]`
* **Assignee:** Antigravity Agent & User
* **Trạng thái:** `COMPLETED` ✅ (Đã chốt đặc tả tại [ADR 0038](../../../../docs/adr/0038-unified-okf-v2-bundle-specification.md))

### 🎫 Ticket 3: [Design] Thiết Kế Giao Thức Điều Phối Tự Động Crawl $\rightarrow$ Ingestion Khép Kín
* **Loại:** `Research [AFK]`
* **Assignee:** Antigravity Agent
* **Trạng thái:** `COMPLETED` ✅ (Đã chốt giao thức tại [ADR 0039](../../../../docs/adr/0039-autonomous-crawler-to-spoke-ingestion-protocol.md))

---

## 🏁 5. Kết Luận Bản Đồ Wayfinder & Bàn Giao Thực Thi (Handoff to Implementation)

Bản đồ Wayfinder `wayfinder:optimization_roadmap` đã hoàn thành 100% sứ mệnh định hướng (Decisions charted). Không còn sương mù kỹ thuật nào cản trở.

Toàn bộ hệ thống sẵn sàng bước vào giai đoạn **Thực Thi Mã Nguồn ([`/ccba-implement`](../../../../.agents/workflows/ccba-implement.md))**:
1. **Gói 1 (Core Deep Seam):** Xây dựng `TableReconstructor` trong `packages/ccba-ooxml/src/ccba_ooxml/tables.py`.
2. **Gói 2 (Schema v2.0):** Nâng cấp `OKFBundlePackager` (Hub) & `gold_standard_processor.py` (Spoke) theo ADR 0038.
3. **Gói 3 (Autonomous CLI):** Tích hợp lệnh `ccba-platform ingest-legal` theo ADR 0039.


