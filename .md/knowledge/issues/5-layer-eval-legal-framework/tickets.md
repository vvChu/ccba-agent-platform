# Danh sách Ticket Chi Tiết: Khung Phòng Vệ 5 Tầng AI Skills Evals & Thống Nhất Ngôn Ngữ Pháp Lý

**Mã bản đồ**: `issue-5-layer-eval-legal-framework`  
**Đường dẫn bản đồ**: [map.md](map.md)  

---

## ✅ Ticket 1: Rà soát & Tái thiết kế Schema Test Cases (Tầng 1 & Tầng 2)

- **Mã Ticket**: `ticket-5-layer-1`
- **Loại**: `Task [AFK]`
- **Trạng thái**: ✅ Completed
- **Tệp tin tác động**: `.agents/skills/eval-gate/test_cases/eval_*.json`
- **Kết quả**:
  - Loại bỏ 100% prompt rác không đúng chuyên môn (quicksort, Fibonacci, sick leave email).
  - Áp dụng quy chuẩn Domain-Adjacent & Cross-Skill Evaluation.
  - Sử dụng Primary Artifact Identifiers cho `negative_regex` để chống False Negative khi AI trả lời Disclaimer.

---

## ✅ Ticket 2: Nâng cấp Robustness & Dry-Run Noise Linter (Tầng 3)

- **Mã Ticket**: `ticket-5-layer-2`
- **Loại**: `Task [AFK]`
- **Trạng thái**: ✅ Completed
- **Tệp tin tác động**: `[MODIFY] .agents/skills/eval-gate/scripts/eval_runner.py`
- **Kết quả**:
  - Tích hợp `--dry-run` validate cú pháp JSON và regex pattern trong 0.05s.
  - Tích hợp Noise Prompt Linter tự động quét và block nếu phát hiện pattern rác trong file eval JSON.

---

## ✅ Ticket 3: Superseded Legal Document Linter & CI Gate Alignment (Tầng 4)

- **Mã Ticket**: `ticket-5-layer-3`
- **Loại**: `Task [AFK]`
- **Trạng thái**: ✅ Completed
- **Tệp tin tác động**: 
  - `[MODIFY] scripts/validate_docs.py`
  - `[MODIFY] docs/adr/0010-skills-integration-and-rag-boundaries.md`
- **Kết quả**:
  - Tích hợp Superseded Legal Doc Linter vào `validate_docs.py`.
  - Cưỡng chế quy chuẩn tham chiếu **Luật Xây dựng 2025 (135/2025/QH15)** & **NĐ 105/2025/NĐ-CP**.
  - Quét 23 markdown files: PASS 100% (0 errors).

---

## ✅ Ticket 5.1: Thiết kế Schema & Parser cho `log_eval_miner.py` (Tầng 5 - Phase 1)

- **Mã Ticket**: `ticket-5-layer-5-1`
- **Loại**: `Task [AFK]`
- **Trạng thái**: ✅ Completed
- **Tệp tin tác động**: `[NEW] scripts/log_eval_miner.py`
- **Kết quả**:
  - Viết xong parser đọc `transcript.jsonl` từ `.system_generated/logs/`.
  - Tích hợp `redact_sensitive_info` theo Maskara Privacy chuẩn (E-mail, Phone, API Key, IP Address).

---

## ✅ Ticket 5.2: Thuật toán nhận diện Router Failures & Disclaimer Mismatches (Tầng 5 - Phase 2)

- **Mã Ticket**: `ticket-5-layer-5-2`
- **Loại**: `Task [AFK]`
- **Trạng thái**: ✅ Completed
- **Tệp tin tác động**: `[MODIFY] scripts/log_eval_miner.py`
- **Kết quả**:
  - Nhận diện chính xác các `USER_INPUT` dẫn tới Disclaimer khước từ phạm vi.
  - Tự động đóng gói và xuất test cases chuẩn 4 tầng vào `.agents/skills/eval-gate/test_cases/eval_<skill>.json`.

---

## ✅ Ticket 5.3: Tích hợp CLI `--mine-logs` & Unit Tests (Tầng 5 - Phase 3)

- **Mã Ticket**: `ticket-5-layer-5-3`
- **Loại**: `Task [AFK]`
- **Trạng thái**: ✅ Completed
- **Tệp tin tác động**: 
  - `[NEW] scripts/tests/test_log_eval_miner.py`
  - `[MODIFY] .agents/skills/eval-gate/scripts/eval_runner.py`
- **Kết quả**:
  - Đã viết unit test `test_log_eval_miner.py` (5/5 PASS 100%).
  - Đã thêm flag `--mine-logs` vào `eval_runner.py`.
  - Chạy `python scripts/safe_pytest.py -f scripts/tests/test_log_eval_miner.py` OK.
