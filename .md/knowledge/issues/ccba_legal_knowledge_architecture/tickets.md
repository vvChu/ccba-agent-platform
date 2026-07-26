# Danh sách Tickets: Khởi tạo ccba-legal-knowledge & Tái cấu trúc OKF v2.0

> **Liên kết:** [Wayfinder Map](map.md) | [Implementation Plan](../../../../artifacts/implementation_plan.md)  
> **Nguyên tắc:** Chỉ thực hiện các ticket nằm ở Biên giới (Frontier) - là những ticket không bị chặn hoặc tất cả blockers của nó đã ở trạng thái [x] hoàn thành.

---

## Ticket 01: Khởi tạo Knowledge Spoke `ccba-legal-knowledge` & Cấu trúc Native-First

**Nghiệp vụ cần làm:** Khởi tạo repository Spoke độc lập tại `D:\GitHubProjects\ccba-legal-knowledge` với cấu trúc `project.mode: delivery`, chứa `workspace_context.yaml` và `legal_registry.yaml` ngay tại Project Root, cùng thư mục `legal_docs/` cấp 1.

**Bị chặn bởi:** Không có — có thể bắt đầu ngay.

- [ ] Khởi tạo thư mục `D:\GitHubProjects\ccba-legal-knowledge`
- [ ] Tạo `workspace_context.yaml` với `project.mode: delivery` và `is_hub: false`
- [ ] Tạo `legal_registry.yaml` tại Root
- [ ] Tạo thư mục `legal_docs/` cấp 1 với các nhánh `REGULATION_QCVN/`, `STANDARD_TCVN/`, `LAW_LUAT/`, `DECREE_NGHI_DINH/`

---

## Ticket 02: Tái cấu trúc & Di chuyển dữ liệu OKF Bundles sang `ccba-legal-knowledge`

**Nghiệp vụ cần làm:** Chuyển toàn bộ dữ liệu OKF Bundles (QCVN 04, QCVN 06...) từ Hub sang Spoke mới với tên văn bản chuẩn hóa, tệp Hợp nhất 2026 và phân tách Thông tư hành chính.

**Bị chặn bởi:** Ticket 01.

- [ ] Copy bộ dữ liệu OKF QCVN 04 sang `D:\GitHubProjects\ccba-legal-knowledge\legal_docs\REGULATION_QCVN\qcvn_04_2021_bxd\`
- [ ] Copy bộ dữ liệu OKF QCVN 06 sang `D:\GitHubProjects\ccba-legal-knowledge\legal_docs\REGULATION_QCVN\qcvn_06_2022_bxd\`
- [ ] Đảm bảo `qcvn_04_2021_bxd_hop_nhat_2026.md` và `qcvn_04_2021_bxd.md` hiện diện đầy đủ
- [ ] Đảm bảo 0 broken links trong `index.md`

---

## Ticket 03: Nâng cấp Python Package `ccba-ai` (Smart Resolution Gateway)

**Nghiệp vụ cần làm:** Bổ sung module `legal_knowledge` vào Package `ccba-ai` hỗ trợ tra cứu RAG 3 tầng tự động (Local Spoke Path $\rightarrow$ Embedded Registry $\rightarrow$ Server Spark API Gateway `:8090`).

**Bị chặn bởi:** Ticket 01.

- [ ] Tạo module `packages/ccba-ai/ccba_ai/legal_knowledge.py`
- [ ] Cấu hình Smart Resolution fallback 3 tầng
- [ ] Export `from ccba_ai import legal_knowledge` trong `__init__.py`

---

## Ticket 04: Nâng cấp `tvpl_vip_crawler.py` (Atomic Ingestion & Dual Sync Pipeline)

**Nghiệp vụ cần làm:** Nâng cấp crawler tự động ghi OKF Bundle mới sang Spoke `ccba-legal-knowledge`, dọn dẹp bảng biểu tệp DOCX gốc để upload lên Google Drive (`1b9vm_1KQ8Fg8Crr1Q-i2xmE62UIHy-_2`) cho NotebookLM, và silent git push ngầm.

**Bị chặn bởi:** Ticket 01, Ticket 02.

- [ ] Cấu hình target path của crawler hướng về `D:\GitHubProjects\ccba-legal-knowledge\legal_docs\`
- [ ] Tự động dọn dẹp file Word gốc và upload lên Google Drive
- [ ] Tự động chạy `validate_docs.py` và `git commit/push` ngầm tại repo Spoke

---

## Ticket 05: Kiểm định CI/CD & Verification Test Suite

**Nghiệp vụ cần làm:** Chạy kiểm thử tự động toàn bộ 9/9 unit tests và kiểm tra tính toàn vẹn 100% trước khi hoàn tất bàn giao.

**Bị chặn bởi:** Ticket 01, Ticket 02, Ticket 03, Ticket 04.

- [ ] Chạy `pytest tests/test_legal_registry_rag.py tests/test_legal_grounding_gate.py tests/test_legal_template_generator.py`
- [ ] Đảm bảo 9/9 tests PASSED
- [ ] Cập nhật `walkthrough.md`
