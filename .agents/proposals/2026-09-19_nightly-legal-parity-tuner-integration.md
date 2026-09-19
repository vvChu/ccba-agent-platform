---
proposal_id: "2026-09-19_nightly-legal-parity-tuner-integration"
type: "workflows"
name: "nightly-legal-parity-tuner-integration"
status: "proposed"
priority: "Cao"
proposed_by_project: "ccba-legal-knowledge"
proposed_by_archetype: "knowledge_corpus"
proposed_date: "2026-09-19"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Tất cả Spokes"
---

# RFC Proposal: Tích Hợp Pha 1 Legal Ground Truth Parity & Master CI Telemetry Vào Cỗ Máy Điều Phối Ban Đêm Của Hub

- **Tác giả đề xuất:** Kỹ sư / Agent đại diện Spoke (`ccba-legal-knowledge`)
- **Ngày lập:** 2026-09-19
- **Trạng thái:** Đang đề xuất (Proposed)
- **Căn cứ pháp lý nền tảng:** [ADR-0042](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0042-tiered-ai-pre-submission-gate-and-tri-repo-sync.md), [ADR-0045](file:///d:/GitHubProjects/ccba-agent-platform/docs/adr/0045-hub-proposal-ingestion-governance.md).

---

### 1. Bối cảnh & Động lực Thực tế tại Spoke (Context & Real-world Motivation)

1. **Nỗi đau thực tế (Pain point):**
   - Trước đây, cỗ máy ban đêm của Hub (`run_nightly_tuner.sh` / `.bat`) chỉ thực hiện Pha 2 (Document Auto-Evolution) và Pha 3 (Multi-Skill Nightly Auto-Tuner) mà chưa có cơ chế tự động đo lường và phát hiện sự trôi dạt (drift), rụng câu chữ hoặc gãy liên kết của 58 gói tri thức pháp luật quy chuẩn tại Spoke `ccba-legal-knowledge`.
   - Các kiểm định Master CI 15 cổng chỉ được chạy cục bộ khi lập trình viên có mặt trên máy, không có cơ chế tự động ghi telemetry và cảnh báo định kỳ qua đêm trên máy chủ Server Spark (100.83.192.30).

2. **Quá trình ươm tạo tại Spoke:**
   - Xây dựng thành công `verify_ground_truth_parity.py` (v2.0 Hardened) với thuật toán Greedy Multi-Span Coverage và Anti-Vacuous Table Regularity.
   - Xây dựng `run_nightly_telemetry.py` chạy 2 giai đoạn: Giai đoạn 1 (Đo VPS trên 11 Golden Cohorts - 30.8s) + Giai đoạn 2 (Quét 15 Master CI Gates trên 58 bundles - 62.8s) với chi phí **0 AI Token**.

3. **Giá trị khi phổ biến lên Hub:**
   - Hoàn thiện chuỗi pipeline 3 giai đoạn tự động tại Hub lúc 00:00 AM trên Server Spark.
   - Tự động hóa hoàn toàn: Kéo code mới nhất $\rightarrow$ Đo đối soát văn bản pháp luật $\rightarrow$ Tự động commit báo cáo $\rightarrow$ Báo Telegram nếu có hồi quy $\rightarrow$ Tiến hóa tài liệu $\rightarrow$ Tối ưu prompt kỹ năng.

---

### 2. Đánh Giá Giá Trị × Rủi Ro × KISS (Evaluation Matrix)

| Tiêu Chí | Đánh Giá Cụ Thể | Ghi Chú / Bằng Chứng |
| :--- | :--- | :--- |
| **Giá trị Nghiệp vụ (Value)** | Rất cao | Bảo vệ toàn vẹn nguồn tri thức chuẩn mực của toàn hệ sinh thái CCBA |
| **Độ Phức tạp (Complexity)** | Thấp (KISS) | Tích hợp trực tiếp vào shell script và batch script hiện hữu |
| **Rủi ro Rò rỉ (Risk)** | Đã triệt tiêu 100% | Sử dụng danh tính daemon dự phòng, cờ `--no-verify` tránh loop |
| **Bảo tồn Nghiệp vụ (Charter)** | Tuân thủ 100% | Phù hợp tuyệt đối với cấu trúc Tri-Repo của ADR-0042 |

---

### 3. Thiết Kế & Đặc Tả Kỹ Thuật tại Hub (Technical Specification)

1. **Vị trí tích hợp tại Hub:**
   - `scripts/cron/run_nightly_tuner.sh`: Thêm khối Pha 1 gọi `.md/tools/run_nightly_telemetry.py --cohorts golden ${DRY_RUN_FLAG}` tại Spoke directory, bọc lệnh push bằng danh tính daemon và gửi alert Telegram nếu thất bại.
   - `scripts/cron/run_nightly_tuner.bat`: Bổ sung khối Pha 1 tương ứng cho môi trường Windows, hỗ trợ `%DRY_RUN_ARG%` và Telegram alert fallback.
   - `.agents/skills/ccba-legal-ingest/SKILL.md`: Bổ sung quy chuẩn Safe Landing Download và giải phóng xung đột phiên TVPL.
   - `.agents/skills/ccba-markdown-document-processing/SKILL.md`: Bổ sung quy định kiểm chuẩn Ground Truth Parity và Anti-Vacuous Table.

---

### 4. Kế Hoạch Xác Thực (Verification Plan)

- `bash -n scripts/cron/run_nightly_tuner.sh`: Kiểm tra cú pháp bash script.
- `python scripts/validate_skills.py --enforce-gpi`: Đảm bảo toàn bộ 73 kỹ năng đạt chuẩn Hiến pháp ADR-0056 & ADR-0058.
- `python -m ccba_harness verify-patch --preset skill`: Xác thực trọn vẹn bộ kiểm thử governance.
