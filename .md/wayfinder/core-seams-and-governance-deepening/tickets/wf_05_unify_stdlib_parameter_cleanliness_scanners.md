# 🎫 WF-05: Chuẩn hóa Seam Quét Tham số, IP & Machine-Path Thuần Stdlib và Thu gọn check_spoke_cleanliness dưới 800 LOC

> **Thuộc bản đồ:** [🗺️ Bản đồ Định hướng: Làm sâu Seam Lõi & Hợp nhất Quản trị](../map.md)  
> **Loại ticket:** `Task [AFK]`  
> **Trạng thái:** `CLOSED` (Hoàn tất `PR-3a` PR `#757` + `PR-3b`; mở khóa [WF-06: Kiểm định Liên thông 4 Cổng ADR-0058, Đồng bộ Catalog/Docs SSOT & Đóng Bản đồ Wayfinder](wf_06_ci_verification_and_catalog_rollup.md))  
> **Assignee:** `AI Platform Architect`

---

## 1. Phạm vi Kỹ thuật (Ứng viên #3)

1. **Seam Thuần Stdlib `scan_parameter_cleanliness` / `_ParameterCleanlinessScanner` (tên duy nhất, `0` xung đột):**
   - Thống nhất quy tắc ADR-0061 thuần stdlib giữa `3` bộ quét phân kỳ: [check_hardcoded_parameters.py](../../../../scripts/governance/check_hardcoded_parameters.py#L27-L150) (`150 LOC`), [check_spoke_cleanliness.py](../../../../scripts/spoke/check_spoke_cleanliness.py#L25-L175) (`745 LOC`), và [peer_gate.py](../../../../packages/ccba-harness/src/ccba_harness/peer_gate.py#L544-L600) (`753 LOC`).
   - Vá đồng bộ `4` khuyết tật đo được thực tế:
     1. Loại trừ đường dẫn `.venv` theo segment (`Path.parts`) thay vì chuỗi con `"/.venv/"` tại `check_hardcoded_parameters.py:70` (chấm dứt `2,199` báo giả trong `.venv/` / `8,676.16 ms`).
     2. Áp dụng miễn trừ `_is_statutory_clause_match` (`check_spoke_cleanliness.py:700-709`) cho số hiệu quy chuẩn như `'3.2.1.1'`.
     3. Không báo giả định danh cục bộ như `'qwen-local-primary'` / `'qwen-local'` (lệch ở `--dir packages`).
     4. Nâng cấp `WIN_PATH_PATTERN` (`check_hardcoded_parameters.py:32`) để nhận diện đúng đường dẫn Windows có khoảng trắng (`C:\Program Files\...`).
2. **Bảo toàn Ràng buộc Đồng bộ Spoke Tier-0 (`FOG-001` từ [WF-01: Phản biện & Chốt Thiết kế Chi tiết cho 3 Ứng viên Kiến trúc (PEP 562, Frontmatter Seam, Stdlib Parameter Scanner)](wf_01_grilling_architecture_design_lock.md)):**
   - Tuân thủ tuyệt đối ranh giới [sdk_inspector.py](../../../../scripts/spoke/sync/sdk_inspector.py#L70-L74) (thuần stdlib, không import `ccba_harness` hay `pyyaml` khi chạy độc lập tại Spoke), đồng thời thu gọn [check_spoke_cleanliness.py](../../../../scripts/spoke/check_spoke_cleanliness.py) từ `979 LOC` xuống `< 800 LOC` (`RULE-2.20`).

## 2. Tiêu chí Hoàn thành (Completion Criteria)

- [x] `python scripts/governance/check_hardcoded_parameters.py --dir .` chạy `< 1.0s` và trả exit `0` (`0` báo giả `.venv/`, `qwen-local*`, `'3.2.1.1'`).
- [x] `check_spoke_cleanliness.py` dưới trần `800 LOC`, pass fixture kiểm thử đồng bộ Spoke Tier-0 (`scripts/tests/`), `peer_gate.py` và [test_hardcoded_parameters.py](../../../../tests/governance/test_hardcoded_parameters.py) pass `100%`.
- [x] Cả `3` caller dùng thống nhất cùng một bộ chuẩn quy tắc, kiểm chứng qua test parity chéo ([test_parameter_scanner_parity.py](../../../../tests/governance/test_parameter_scanner_parity.py)).
