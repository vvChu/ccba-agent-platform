# 🎫 WF-02: Thẩm định Kế hoạch Ngang hàng qua Peer Plan Audit (ADR-0067 One-Way Door Gate)

> **Thuộc bản đồ:** [🗺️ Bản đồ Định hướng: Làm sâu Seam Workspace/Hub, Maskara & OOXML](../map.md)  
> **Loại ticket:** `Task [HITL]`  
> **Trạng thái:** `CLOSED` *(Hoàn tất `2026-11-18` — Pass 2 `APPROVE_PLAN`, `risk_score: 2`, `blocking_conditions: 0`, Kỹ sư Trưởng xác nhận `Proceed`)*  
> **Assignee:** `AI Platform Architect & Grok 4.7 Auditor`  
> **Phụ thuộc:** Mở khóa [WF-03: Làm sâu Seam Phân giải Workspace & Hub Root (resolve_workspace_and_hub_roots) cho ccba_legal, ccba_harness và scripts/spoke](wf_03_deepen_workspace_and_hub_root_seam.md) và [WF-05: Làm sâu Seam OOXMLValidator (ParsedOOXMLPackage) & Đóng gói ZIP Tất định cho ccba_ooxml](wf_05_deepen_ooxml_validator_and_pack_seam.md)

---

## 1. Bối cảnh & Câu hỏi Cốt lõi

Toàn bộ chiến dịch tái cấu trúc chạm vào nhiều tệp nguồn (`> 3` files, `> 200` LOC), thuộc ứng viên hạng `Strong` và tác động trực tiếp các Public Seam (`ccba_harness`, `ccba_legal`, `ccba_maskara`, `mdconverter`, `ccba_ooxml`) thuộc danh mục `ONE_WAY_DOOR` theo [ADR-0067](../../../../docs/adr/0067-one-way-door-manifest-and-backpressure-circuit-breaker.md). Theo cổng phân nhánh tác động kiến trúc của `/ccba-codebase-design` Bước 4 và `RULE-4.19` / `RULE-4.20`, Kế hoạch triển khai từ [WF-01: Phản biện & Chốt Thiết kế Chi tiết cho 3 Ứng viên Kiến trúc (Workspace/Hub Root Seam, Maskara Redaction Seam, OOXMLValidator Seam)](wf_01_grilling_architecture_design_lock.md) phải vượt qua Peer Plan Audit trước khi sửa bất kỳ tệp mã nguồn production nào.

## 2. Phạm vi Thực thi

1. Đọc hướng dẫn giao thức peer tại `.md/peer_exchange/PEER_HANDSHAKE.md` và chạy `door-triage --enforce-tradeoff-card` kiểm chứng cấu trúc `TradeoffCard` (`Core Invariant`, `Invalidation Condition`, `Git Hunk Reference` `<= 30` dòng theo `RULE-1.23`).
2. Chạy `ccba-harness peer-dispatch --profile audit_plan` (`WaitMsBeforeAsync: 500`, không gọi thẳng CLI `grok` thô) trên Kế hoạch triển khai đã khóa từ [WF-01: Phản biện & Chốt Thiết kế Chi tiết cho 3 Ứng viên Kiến trúc (Workspace/Hub Root Seam, Maskara Redaction Seam, OOXMLValidator Seam)](wf_01_grilling_architecture_design_lock.md).
3. Nếu còn `blocking_conditions > 0` (`REVISE_PLAN` hoặc `APPROVE_WITH_CONDITIONS`), hiệu chỉnh kế hoạch kèm bằng chứng `file:line` (`ADOPT_AS_IS` / `ADOPT_ADAPTED` / `REBUT_WITH_EVIDENCE` theo `RULE-4.17`) và chạy nối tiếp `--profile signoff_diff --resume <sid> --fork-session` tối đa tới hết Pass 3 (`RULE-4.19`) cho tới khi `blocking_conditions == 0`.
4. Trình kết quả thẩm định ngang hàng lên Kỹ sư Trưởng và chờ lệnh xác nhận `proceed` tường minh.

## 3. Tiêu chí Hoàn thành (Completion Criteria)

- [x] Tự gán `Assignee` trên ticket trước khi thực thi.
- [x] `door-triage --enforce-tradeoff-card` hợp lệ (`TRADEOFF_CARD_INVALID == 0` trên cả `5/5` card `PR-1a`..`PR-3b`).
- [x] `peer-dispatch` đạt `APPROVE_PLAN` với `blocking_conditions == 0` (Pass 2 `signoff_diff`, `session_id: f044627a-7a05-410f-afff-6fd52351166d`, `risk_score: 2`).
- [x] Kỹ sư Trưởng xác nhận `proceed` trước khi mở khóa sửa mã ở [WF-03: Làm sâu Seam Phân giải Workspace & Hub Root (resolve_workspace_and_hub_roots) cho ccba_legal, ccba_harness và scripts/spoke](wf_03_deepen_workspace_and_hub_root_seam.md) và [WF-05: Làm sâu Seam OOXMLValidator (ParsedOOXMLPackage) & Đóng gói ZIP Tất định cho ccba_ooxml](wf_05_deepen_ooxml_validator_and_pack_seam.md).
- [x] Cập nhật kết quả vào [🗺️ Bản đồ Định hướng: Làm sâu Seam Workspace/Hub, Maskara & OOXML](../map.md) và đóng ticket `WF-02` (`CLOSED`).

### 📊 Nhật Ký Thẩm Định Ngang Hàng (`WF-02` Peer Plan Audit Trail)

| Vòng | Profile | `session_id` | Phán quyết | `risk_score` | `blocking_conditions` | Chi phí / Thời gian | Ghi chú |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| Pass 1 | `audit_plan` | `bbf5de60-3b77-4605-b224-1cad5dc02335` | `REVISE_PLAN` | `4` | `3` + `5` non-blocking | — | Nêu `COND-PII-DIALECT`, `COND-WS-ANCHOR`, `COND-OOXML-SHARE` cùng `5` điều kiện phạm vi; đã giải trình `8/8` trong Decision Log `v1.1` |
| Pass 2 | `signoff_diff` | `f044627a-7a05-410f-afff-6fd52351166d` | `APPROVE_PLAN` | `2` | `0` (`2` non-blocking pins) | `$0.299` / `192.25s` | Pin thực thi: `COND-XSD-DUAL-PATH` (`base.py:848`), `COND-MAP-SYNC` (đã đồng bộ `map.md` mục 1); mở khóa xin `proceed` cho `WF-03` & `WF-05` |

> **Cổng `door-triage --enforce-tradeoff-card`:** `5/5` card (`PR-1a`..`PR-3b`) trả `exit=0`, `tradeoff_card_valid=true`, `status=approval_required` (`HUMAN_APPROVAL_REQUIRED`).

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
