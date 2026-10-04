---
proposal_id: "2026-10-04_standardize-peer-exchange-protocol"
type: "tool"
name: "standardize-peer-exchange-protocol"
status: "merged"
merged_pr: "#466"
merged_commit: "f40a73dc"
merged_date: "2026-10-04"
priority: "Cao"
related_issue: "#458"
proposed_by_project: "dgx-spark-toolkit"
proposed_by_archetype: "specialized_extension"
proposed_date: "2026-10-04"
applies_to:
  - "Phần mềm"
  - "Tất cả Spokes"
---

# RFC Proposal: Chuẩn Hóa Giao Thức Trao Đổi Song Phương & Watcher Đồng Đẳng Antigravity ⇄ Grok

- **Tác giả đề xuất:** Antigravity (Pair Architect & Builder)
- **Ngày lập:** 2026-10-04
- **Liên kết Issue:** [#458](https://github.com/vvChu/ccba-agent-platform/issues/458)
- **Căn cứ pháp lý nền tảng:** [ADR-0045](../../docs/adr/0045-hub-proposal-ingestion-governance.md), ADR-0007, ADR-0008.

---

### 1. Bối cảnh & Nỗi đau Thực tế (Context & Motivation)
1. **Nỗi đau thực tế:**
   - Trên máy chủ DGX Spark (Blackwell GB10), hai agent hàng đầu (Antigravity và Grok) vận hành không đồng bộ, kỹ sư phải copy-paste prompt qua lại giữa các terminal.
   - Khi chạy headless hoặc automation, Linux chặn keystroke injection (`TIOCSTI`) giữa các terminal giả lập.
   - Các file exchange cũ trong `.md/peer_exchange/` không có cấu trúc front-matter, không có schema xác thực Pydantic, watcher quét toàn bộ sinh ra file tóm tắt phình to tới 67 KB.
2. **Giải pháp đã kiểm chứng tại Spoke `dgx-spark-toolkit`:**
   - Xây dựng module `ccba_harness.peer` với Pydantic v2 schemas: `PeerPromptEnvelope`, `PeerVerdictBlock`, `PeerCondition` (cấu hình `extra='forbid'` kèm fail-safe parsing).
   - Nâng cấp `peer_bridge_watcher.py` với cơ chế tính hash SHA-256 delta caching (`.bridge_cache.json`), ghi tệp nguyên tử qua tệp tạm (`atomic_write_text`), giảm kích thước file live summary từ 67 KB xuống 1.8 KB.
   - Được Grok nghiệm thu độc lập đạt phán quyết **`GATE_PASS`** (0 errors, 100% test pass).
   - Tích hợp scaffold `.md/peer_exchange/` tự động vào kịch bản đồng bộ Spoke (`spoke_synchronizer.py` và `spoke_bootstrap.py`).

---

### 2. Đánh Giá Giá Trị × Rủi Ro × KISS

| Tiêu Chí | Đánh Giá Cụ Thể | Ghi Chú / Bằng Chứng |
| :--- | :--- | :--- |
| **Giá trị Nghiệp vụ (Value)** | Rất cao | Chuẩn hóa tương tác đa agent tự động 100% trên toàn bộ mạng lưới Spoke |
| **Độ Phức tạp (Complexity)** | Thấp (KISS) | Đóng gói thành module `ccba_harness.peer` nhỏ gọn $\le 50$ dòng/hàm |
| **Rủi ro Hỏng hóc (Risk)** | Đã triệt tiêu | Fallback an toàn khi gặp tệp legacy không có front-matter |
| **Bảo tồn Dữ liệu (Preservation)** | 100% | Không làm mất mát hay sửa đổi nội dung body markdown gốc |
