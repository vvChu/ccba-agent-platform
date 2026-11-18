# 🎫 WF-05: Làm sâu Seam OOXMLValidator (ParsedOOXMLPackage) & Đóng gói ZIP Tất định cho ccba_ooxml

> **Thuộc bản đồ:** [🗺️ Bản đồ Định hướng: Làm sâu Seam Workspace/Hub, Maskara & OOXML](../map.md)  
> **Loại ticket:** `Task [AFK]`  
> **Trạng thái:** `CLOSED` *(Hoàn tất `2026-11-18` qua PR `#807` `--squash` `144ee313` & PR `#808` `--merge` `552066eb`, Commit 1 anchor `7259350d8020834c52ab88e4c5681e165612cc8b`)*  
> **Assignee:** `Antigravity`  
> **Phụ thuộc:** Tham gia mở khóa [WF-06: Kiểm định Liên thông 4 Cổng ADR-0058, Đồng bộ Catalog/Docs SSOT & Đóng Bản đồ Wayfinder](wf_06_ci_verification_and_wayfinder_rollup.md)

---

## 1. Phạm vi Kỹ thuật (Ứng viên #3 — Seam `ooxml_processor.v1`)

Triển khai theo đúng phương án đã khóa tại `Q4`–`Q5` của [WF-01: Phản biện & Chốt Thiết kế Chi tiết cho 3 Ứng viên Kiến trúc (Workspace/Hub Root Seam, Maskara Redaction Seam, OOXMLValidator Seam)](wf_01_grilling_architecture_design_lock.md):

1. **Xây dựng bộ đệm `ParsedOOXMLPackage` & `_make_secure_xml_parser()` an toàn:**
   - Trong `packages/ccba-ooxml/src/ccba_ooxml/validation/`, dựng `ParsedOOXMLPackage` nạp mỗi tệp `.xml` và `.rels` đúng `1` lần theo thứ tự sắp xếp đường dẫn tương đối (`sorted(..., key=lambda p: p.relative_to(...).as_posix())`) bằng factory `_make_secure_xml_parser()` (`lxml.etree.XMLParser(resolve_entities=False, no_network=True)` tạo mới mỗi lần parse — an toàn đa luồng và gắn đúng `error_log`).
   - Giữ bản gốc DOM bất biến trong cache và cấp bản sao `clone_root()` (`copy.deepcopy`) riêng cho cả `5` bước có đột biến cây: `base.py:247`, `base.py:822`, `base.py:830`, `base.py:778`/`L919-921`, và [redlining.py](../../../../packages/ccba-ooxml/src/ccba_ooxml/validation/redlining.py#L91-L92) (chuyển `redlining.py` sang `lxml.etree` dùng `clone_root()`).
2. **Làm sâu `OOXMLValidator` & Phân rã `validation/base.py` `< 800 LOC`:**
   - Chuyển toàn bộ các phương thức kiểm định (`base.py` + `docx.py:84,133,175,220` + `redlining.py`) sang đọc chung `ParsedOOXMLPackage` và trả `list[ValidationIssue]` chứa đủ `file_path`, `line_number`, `severity`, `message`, giúp [validator.py](../../../../packages/ccba-ooxml/src/ccba_ooxml/validation/validator.py#L28-L89) bảo toàn trọn vẹn vị trí lỗi thay vì rơi `line_number=None` (`PPTXSchemaValidator` `pptx.py:87-251` xếp đợt sau).
   - Gated toàn bộ `print()` (kể cả `compare_paragraph_counts()` tại [docx.py](../../../../packages/ccba-ooxml/src/ccba_ooxml/validation/docx.py#L68) và `FAILED`/`PASSED`) chỉ xuất khi `self.verbose=True`.
   - Chia nhỏ [base.py](../../../../packages/ccba-ooxml/src/ccba_ooxml/validation/base.py#L44-L265) (`949 LOC`) thành `base.py`, `_parsed_package.py`, `_relationship_checks.py`, `_xsd_engine.py` (`<= 350 LOC` mỗi tệp, `<= 50 LOC` mỗi hàm) và rút riêng `validation/base.py` khỏi [module_budget_baseline.json](../../../../packages/ccba-harness/src/ccba_harness/module_budget_baseline.json#L10).
3. **Đóng gói ZIP tất định & Khóa SHA-256 Profile-B (`RULE-2.21`):**
   - Sắp xếp đủ `8` lời gọi `rglob()` tại `base.py:168,320,329,599`, [pack.py](../../../../packages/ccba-ooxml/src/ccba_ooxml/pack.py#L41-L51), và [unpack.py](../../../../packages/ccba-ooxml/src/ccba_ooxml/unpack.py#L29-L30) (gộp thành `1` list `sorted(...)` duy nhất); cố định `ZipInfo.date_time=(1980, 1, 1, 0, 0, 0)` trong `pack.py` và bảo toàn nguyên văn `stderr` `bug_path_4` của [verify-ccba-ooxml](../../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/SKILL.md#L53).
   - Chạy `Semantic Mutation Proof` trên cây sạch sau `PR-3a` và cập nhật `covered_sha256` / `sync_commit` cho `verify-ccba-ooxml` tại `PR-3b`.

## 2. Tiêu chí Hoàn thành (Completion Criteria)

- [x] Tự gán `Assignee` trên ticket trước khi thực thi.
- [x] Benchmark trên fixture `.docx` gồm `16` tệp XML chứng minh: giảm từ `86` lần `lxml.etree.parse()` (`105.54 ms`, `71/86` thiếu safe parser) xuống còn `16` (`<= 16`) lần parse trên thư mục unpacked dùng `resolve_entities=False, no_network=True` (`0% parser=None`, `5.65 ms`, `DOCXSchemaValidator` + `RedliningValidator`, `[đo thực tế]`) và `2` lần `pack_document()` tạo ZIP trùng khớp SHA-256 (`zip_match=True`).
- [x] Kiểm thử XML hỏng trên `word/document.xml` xác nhận `ValidationReport.issues` trả về đầy đủ `file_path` và `line_number` (`is not None`).
- [x] `validation/base.py` (`337 LOC`) và các submodule mới (`_parsed_package.py` `297`, `_relationship_checks.py` `319`, `_xsd_engine.py` `285`) đều `< 350 LOC` (`<= 50 LOC`/hàm); `module_budget_baseline.json` đã cập nhật gỡ `validation/base.py`.
- [x] `verify-patch --preset code --target packages/ccba-ooxml` (`2055.4 ms`) và `run_verify_ooxml.py` (`6 passed`) đạt exit `0`.
- [x] Cập nhật kết quả vào [🗺️ Bản đồ Định hướng: Làm sâu Seam Workspace/Hub, Maskara & OOXML](../map.md) và đóng ticket `WF-05` (`CLOSED`).

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
