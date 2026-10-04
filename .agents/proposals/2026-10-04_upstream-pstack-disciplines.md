---
proposal_id: "2026-10-04_upstream-pstack-disciplines"
type: "packages"
name: "upstream-pstack-disciplines"
issue_id: "#461"
status: "proposed"
priority: "Cao"
proposed_by_project: "ccba-agent-platform"
proposed_by_archetype: "platform_tooling"
proposed_date: "2026-10-04"
applies_to:
  - "Tất cả Spokes"
  - "Phần mềm"
  - "Architecture Governance"
---

# RFC Proposal: Upstream Pstack Disciplines Lên Hub (Issue #461)

- **Tác giả đề xuất:** Platform Architect / Lead Orchestrator
- **Ngày lập:** 2026-10-04
- **Liên kết Issue:** [#461](https://github.com/vvChu/ccba-agent-platform/issues/461)
- **Căn cứ pháp lý nền tảng:** ADR-0007, ADR-0009, ADR-0044, ADR-0058, ADR-0061.

---

### 1. Bối cảnh & Động lực Thực tế (Context & Motivation)
Sau khi thực nghiệm thành công 5 thành phần Pstack (ADR-0009) tại Spoke `dgx-spark-toolkit` với biên lai kiểm thử nghiệm thu `GATE_PASS` từ Grok 4.7 xhigh, các kỷ luật mang tính nền tảng cần được đóng gói trực tiếp lên Hub (`packages/ccba-harness`) để:
1. Cho phép mọi Spoke (`ccba-legal-knowledge`, `IDOP-CCBA-WAY`, `bim-planner`, v.v.) tự động thụ hưởng các kỷ luật kiểm định tự động mà không phải sao chép mã nguồn cục bộ.
2. Tiết kiệm ngân sách script (`15/15`) tại các Spoke theo quy chuẩn Spoke Cleanliness (ADR-0044).
3. Cung cấp năng lực phân tích bán kính ảnh hưởng (`blast-radius`) và truy nguyên quyết định kiến trúc (`architecture-why`) trên toàn bộ hệ sinh thái Hub-Spoke.

---

### 2. Các Thành Phần Kỹ Thuật Đóng Gói

1. **6-Stage Automated Peer Implementation Gate** (`ccba_harness.peer_gate`):
   - Chuẩn hóa 6 tầng kiểm định: `pytest`, `flake8`, `ast_function_length` (KISS $\le 50$), `import_cycle_check`, `hub_import_depth`, `secret_ip_cleanliness`.
   - Entry point CLI: `ccba-harness peer-gate` (hỗ trợ cờ `--branch`, `--file`, `--output-verdict`, `--json`).
2. **Cross-Repo Blast Radius Analyzer** (`ccba_harness.blast_radius`):
   - AST Parser phân tích import và symbol dependency giữa Hub packages/skills và các Spoke đăng ký trong `.md/data/spoke_registry.yaml`.
   - Phân cấp rủi ro và xác định chính xác các test suite cần kích hoạt (`ccba-harness blast-radius <targets>`).
3. **Architecture Why Explainer** (`ccba_harness.architecture`):
   - Tra cứu tri thức kỹ thuật từ ADRs, Traceability Matrix và Git commit history.
   - Entry point CLI: `ccba-harness why "<câu hỏi kiến trúc>"`.

---

### 3. Đánh Giá Giá Trị × Rủi Ro × KISS

| Tiêu Chí | Đánh Giá Cụ Thể | Ghi Chú / Bằng Chứng |
| :--- | :--- | :--- |
| **Giá trị Nghiệp vụ (Value)** | Rất cao | Phân phối 3 kỷ luật quản trị cho 100% Spokes qua shared package `ccba-harness` |
| **Độ Phức tạp (Complexity)** | Vừa phải (Modular) | Tách biệt thành 3 module chuyên biệt trong `ccba_harness`, tuân thủ SRP |
| **Rủi ro Hồi quy (Risk)** | Thấp (Zero-Regression) | 7/7 unit tests chuyên biệt pass 100%, 3/3 verify-patch passed |
| **Bảo tồn Hiến pháp (Charter)**| Tuyệt đối | Cưỡng chế KISS $\le 50$, Zero-Inbound, và Deep Seams provenance |
