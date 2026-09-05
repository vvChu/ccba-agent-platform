# Định dạng Báo cáo Kiểm duyệt Vi mô Học thuật mẫu

Tài liệu này lưu trữ ví dụ về định dạng cấu trúc báo cáo (Mock report format) do công cụ `microstructure_audit.py` in ra console sau khi hoàn thành quét bản thảo bài báo.

```text
============================================================
ACADEMIC WRITING AUDIT REPORT
Target File: CCBA_RD_SEMINAR_005_Rev00-BIM_AI_Draft.md
============================================================

1. PASSIVE VOICE ANALYSIS (Section-Based Thresholds)
------------------------------------------------------------
- Section: Introduction (Max: 40%) -> Actual: 25.0% [PASS]
- Section: Methods (Range: 60%-80%) -> Actual: 72.5% [PASS]
- Section: Discussion (Max: 30%) -> Actual: 45.2% [FAIL]
  [Warning] Discussion section has excessive passive voice. Use active voice ('We found', 'Our results indicate') to convey authority.

2. STYLISTIC CHECKS
------------------------------------------------------------
- [L120] Intensifier Alert: 'clearly' - Avoid emotional intensifiers.
- [L142] Nominalization Alert: 'provide an argument' - Use active verb 'argue'.

3. VIETNAMESE TYPO & ABBREVIATION DICTIONARY
------------------------------------------------------------
- [L85] Unmarked Vietnamese Typo: 'betong' -> Suggest: 'bê tông'
- [L90] Non-standard Abbreviation: 'cb' -> Suggest: 'cảm biến'

4. CARS MODEL CHECKS (Introduction)
------------------------------------------------------------
- Move 1 (Territory): Detected ('has been widely studied')
- Move 2 (Niche): Detected ('however, few studies')
- Move 3 (Occupy): Detected ('in this paper, we propose')
- [STATUS] CARS compliance check passed.
============================================================
```
