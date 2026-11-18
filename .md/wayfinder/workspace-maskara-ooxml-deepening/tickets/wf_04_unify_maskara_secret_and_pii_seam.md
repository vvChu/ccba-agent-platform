# 🎫 WF-04: Làm sâu Seam Che giấu Secret & PII Việt Nam (ccba_maskara) và Hợp nhất 3 Bộ Quét Phân kỳ

> **Thuộc bản đồ:** [🗺️ Bản đồ Định hướng: Làm sâu Seam Workspace/Hub, Maskara & OOXML](../map.md)  
> **Loại ticket:** `Task [AFK]`  
> **Trạng thái:** `CLOSED` *(Hoàn tất `2026-11-18` qua PR `#806`, merge commit `6b033325` (`--merge`), Commit 1 anchor `646cf2d79b382ba8e33bb2540676c272bfc99435`)*  
> **Assignee:** `AI Platform Architect`  
> **Phụ thuộc:** Tham gia mở khóa [WF-06: Kiểm định Liên thông 4 Cổng ADR-0058, Đồng bộ Catalog/Docs SSOT & Đóng Bản đồ Wayfinder](wf_06_ci_verification_and_wayfinder_rollup.md)

---

## 1. Phạm vi Kỹ thuật (Ứng viên #2 — Seam `maskara_scanner.v1`)

Triển khai theo đúng phương án đã khóa tại `Q3` của [WF-01: Phản biện & Chốt Thiết kế Chi tiết cho 3 Ứng viên Kiến trúc (Workspace/Hub Root Seam, Maskara Redaction Seam, OOXMLValidator Seam)](wf_01_grilling_architecture_design_lock.md):

1. **Làm sâu `ccba_maskara` làm SSOT duy nhất cho Secret & PII Việt Nam (`COND-PII-DIALECT`):**
   - Bổ sung `PII_REGEX_PATTERNS` (`email`, `phone` có cả leading + trailing `\b`, `ip-private` khớp exact regex `_miner_catalog.py:61`, `cccd` dùng `(?<![-\w.])\d{12}(?![-\w.])`, `cmnd` dùng `(?<![-\w.])\d{9}(?![-\w.])` xếp sau `phone`) vào `ccba_maskara` ([_rules.py](../../../../packages/ccba-maskara/src/ccba_maskara/_rules.py#L9-L90), [_scanner.py](../../../../packages/ccba-maskara/src/ccba_maskara/_scanner.py#L127-L337)) qua interface mới `redact_secrets_and_pii(..., dialect="maskara"|"bracket_suffix"|"bracket_prefix")`, bảo toàn 1:1 token maps (`env-secret` `group(1)` &rarr; `[SECRET_REDACTED]` ở `bracket_suffix`; bỏ `cccd`/`cmnd` trong `bracket_suffix`). Giữ nguyên `REGEX_PATTERNS` và `scan_text(include_pii=False)` cho pre-commit.
   - Đưa singleton về helper nội bộ `_get_default_scanner()` trong [ccba_maskara/__init__.py](../../../../packages/ccba-maskara/src/ccba_maskara/__init__.py#L30-L62) (KHÔNG đưa vào `_LAZY_EXPORTS` để tránh side-effect lúc `import ccba_maskara` và bảo toàn `check_init_lazy_exports_parity`).
   - Bảo toàn rào chắn `RULE-5.11` (`env-secret` và cảnh báo biến `token=`) trong `MaskaraScanner`.
2. **Hợp nhất `mdconverter.style` & `ccba_harness.evals._miner_catalog` thành Thin Adapters:**
   - Thêm `"ccba-maskara"` vào dependencies trong [packages/mdconverter/pyproject.toml](../../../../packages/mdconverter/pyproject.toml#L17-L32) (hợp lệ với [check_dependency_contracts.py](../../../../scripts/governance/check_dependency_contracts.py#L43-L50)).
   - Chuyển `redact_sensitive_info` tại [packages/mdconverter/src/mdconverter/style.py](../../../../packages/mdconverter/src/mdconverter/style.py#L15-L52) (bổ sung `ccba-maskara` vào [mdconverter/pyproject.toml](../../../../packages/mdconverter/pyproject.toml)) và [packages/ccba-harness/src/ccba_harness/evals/_miner_catalog.py](../../../../packages/ccba-harness/src/ccba_harness/evals/_miner_catalog.py#L14-L78) (`L297-L331`, giữ nguyên nhánh `try/except ImportError` fallback và không đụng `ccba-harness/pyproject.toml`) thành thin adapters gọi `redact_secrets_and_pii`, xóa bỏ ~`95 LOC` regex chép tay và hằng chết `SENSITIVE_PATTERNS`.
   - Khẳng định tương thích 100% với bộ test hiện hữu ([test_scanner.py](../../../../packages/ccba-maskara/tests/test_scanner.py#L59), [test_miner.py](../../../../packages/ccba-harness/tests/test_miner.py#L23-L30), [test_log_eval_miner.py](../../../../scripts/tests/test_log_eval_miner.py#L46-L57), [test_phase1_mdconverter_seams.py](../../../../packages/mdconverter/tests/test_phase1_mdconverter_seams.py#L164-L173)) và khóa kết quả khảo sát `[FOG-002]` trên `527` tệp.
3. **Kiểm định & Khóa SHA-256 Profile-B (`COND-SHA-SCOPE`):**
   - Chạy `Semantic Mutation Proof` và chỉ cập nhật `covered_sha256` / `sync_commit` cho [verify-ccba-maskara](../../../../packages/ccba-harness/.agents/skills/verify-ccba-maskara/SKILL.md) (không đụng `verify-ccba-mdconverter` nếu `mdconverter/__init__.py` không thay đổi).

## 2. Tiêu chí Hoàn thành (Completion Criteria)

- [x] Tự gán `Assignee` trên ticket trước khi thực thi.
- [x] Kiểm thử thực nghiệm xác nhận `mdconverter.style.redact_sensitive_info` chặn được `sk-proj-*`, `sk-ant-*`, `github_pat_*`, còn `redact_secrets_and_pii` / `_miner_catalog` chặn được SĐT & CCCD 12 số (`[đo thực tế]`: `0` rò rỉ).
- [x] Đóng `[FOG-002]` bằng số đo tỷ lệ khớp nhầm thực tế trên `527` tệp (`docs/`, `.agents/skills/`, `evals/`): CMND `\b\d{9}\b` `0` FP; CCCD dùng `(?<![-\w.])\d{12}(?![-\w.])` loại trừ UUID tail, chỉ còn `1` CCCD mẫu thật `001090001234`.
- [x] `check_dependency_contracts.py` đạt `0` vi phạm; `verify-patch --preset code` pass trên `ccba-maskara`, `mdconverter` và `ccba-harness`.
- [x] `verify-ccba-maskara` chạy qua `run_verify_maskara.py` đạt exit `0` sau khi cập nhật `covered_sha256` (dùng `gh pr merge --merge`).
- [x] Cập nhật kết quả vào [🗺️ Bản đồ Định hướng: Làm sâu Seam Workspace/Hub, Maskara & OOXML](../map.md) và đóng ticket `WF-04` (`CLOSED`).

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
