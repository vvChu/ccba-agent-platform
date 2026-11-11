# Biên Bản Quyết Định Kiến Trúc & Stress-Test: `/ccba-build-skill` (Grilling Resolution Log)

- **Ngày thực hiện:** 2026-11-11
- **Phương thức:** `/ccba-grilling` (Stress-Test & Phỏng vấn dồn dập Cây thiết kế)
- **Đối tượng:** Kỹ năng [`ccba-build-skill`](../../../.agents/skills/ccba-build-skill/SKILL.md)
- **Tình trạng:** Đã hoàn thành phỏng vấn (All Frontier Nodes Resolved)

---

## 1. Tóm Tắt Định Vị Kỹ Năng

Kỹ năng `/ccba-build-skill` đóng vai trò là **"Nhà máy Tác tạo Kỹ năng Chuẩn mực" (Skill Factory)** của CCBA Agent Platform, thuộc nhóm Tier 2B Standalone Kernel Skill ($GPI = 14.0$). Kỹ năng chịu trách nhiệm chuyển hóa các nguồn tri thức thô thành các chỉ dẫn hành vi tất định cho Agent, tuân thủ nghiêm ngặt [ADR-0057](../../../docs/adr/0057-two-stage-granularity-decision-framework-and-gpi.md), [ADR-0058](../../../docs/adr/0058-live-collaboration-artifacts-workspace-mirroring-and-charter-alignment.md) và [ADR-0061](../../../docs/adr/0061-platform-aware-kiss-v2-and-quarantine-governance.md).

---

## 2. Bảng Biên Bản 5 Quyết Định Then Chốt (Decision Resolution Matrix)

| STT | Vấn Đề Thiết Kế (Frontier Node) | Hiện Trạng Trước Grilling | Quyết Định Đã Chốt (Resolution) | Cơ Chế Kiểm Chứng Tương Ứng |
| :---: | :--- | :--- | :--- | :--- |
| **01** | **Cơ chế Nạp Nguồn (Ingestion)** | Phụ thuộc 100% vào Google NotebookLM (`python -m ccba_notebooklm`), nghẽn khi gặp tài liệu mật hoặc không có internet. | **Dual-Mode Ingestion**: Mode A (Cloud RAG qua NotebookLM) cho tài liệu công khai/URL; Mode B (Local Fallback qua `ccba-ai` / parser nội bộ) cho tài liệu nhạy cảm hoặc offline. | `scripts/maskara.py` quét sạch bí mật trước khi xử lý. |
| **02** | **Cổng Kiến Trúc & Tính GPI** | Agent tự suy luận và nhẩm điểm số theo barem lý thuyết trong prompt, dễ bị ảo giác điểm số (*hallucination*). | **Cổng Kiểm Soát Cứng bằng CLI**: Bắt buộc chạy `python -m ccba_harness evaluate-gpi --s ... --k ... --a ... --p ...` để nhận diện phân tầng và kiểm tra dải trễ (*hysteresis deadband* $[11.5, 12.5)$). | `ccba-harness evaluate-gpi` trả về exit code 0 và tier định tuyến. |
| **03** | **Khởi Tạo Thành Phẩm (Scaffolding)** | Chỉ tạo duy nhất tệp `SKILL.md`, thiếu ca kiểm thử hành vi ban đầu và chưa tự động phân tầng Level 3. | **Full-Stack Scaffolding**: Bắt buộc sinh kèm tệp ca kiểm thử mẫu tại `.agents/skills/ccba-eval-gate/test_cases/eval_<tên-skill>.json` (gồm 1 ca happy-path + 1 ca red-team). Phân tầng sang `references/` nếu dài. | `python -m ccba_harness eval --skill <tên>` sẵn sàng chạy kiểm thử hồi quy. |
| **04** | **Phân Định Hub vs. Spoke** | Ngầm định chạy tại Hub root, gây lỗi `FileNotFoundError` khi chạy tại Spoke và phá vỡ luồng Upstream. | **Environment Pre-flight Check**: Kiểm tra `git remote get-url origin`. Nếu ở Spoke, định tuyến tạo file sang `$CCBA_HUB_PATH` và kích hoạt luồng đóng góp ngược `/ccba-contribute-to-hub`. | Rào chắn phân định môi trường tại dòng đầu của quy trình. |
| **05** | **Khóa Cứng & Tự Phục Hồi Lỗi** | Khi `verify-patch` thất bại, dừng quy trình hoặc yêu cầu can thiệp thủ công. | **Self-Healing Loop (Tối đa 2 vòng)**: Tự động triệu hồi các bước sửa chữa của `/ccba-skill-repair` (vá YAML, sửa link gãy, biên dịch lại catalog) trước khi báo cáo người dùng. | `python -m ccba_harness verify-patch --preset skill` đạt Exit Code 0. |

---

## 3. Kiến Trúc Luồng Vận Hành Mới Chuẩn Hóa (Standard Operating Procedure)

```text
[ Người dùng kích hoạt /ccba-build-skill <nguồn> ]
                      │
                      ▼
        [ 0. Environment Pre-flight ]
        ├── Hub?  ──> Tiếp tục tại chỗ
        └── Spoke? ──> Trỏ về $CCBA_HUB_PATH & Chuẩn bị Upstream Loop
                      │
                      ▼
         [ 1. Quét Bảo Mật & Ingestion ]
        ├── Cloud RAG: Python -m ccba_notebooklm
        └── Local Fallback: ccba-ai + Local Text Extractor
                      │
                      ▼
         [ 2. Chưng Cất Tri Thức ]
        └── Kết xuất tệp Markdown vào .md/knowledge/
                      │
                      ▼
         [ 3. Deterministic Architecture & GPI Gate ]
        └── python -m ccba_harness evaluate-gpi --s S --k K --a A --p P
            ├── Tier 1 (Deterministic)  ──> DỪNG: Đẩy về packages/*/src/
            ├── Tier 3 (Orchestrated)   ──> DỪNG: Đẩy về .agents/workflows/
            ├── Tier 2A (GPI < 12.0)    ──> Tạo .agents/skills/<parent>/references/
            └── Tier 2B (GPI >= 12.0)   ──> Tiến hành Tạo Standalone Kernel Skill
                      │
                      ▼
         [ 4. Full-Stack Skill Scaffolding ]
        ├── Tạo .agents/skills/ccba-<name>/SKILL.md (kèm khối gpi: chuẩn)
        ├── Tạo thư mục references/ (nếu vượt ngân sách ngữ cảnh)
        └── Tạo .agents/skills/ccba-eval-gate/test_cases/eval_<name>.json
                      │
                      ▼
         [ 5. Slash Command & Catalog Compilation ]
        └── python scripts/governance/compile_catalog.py
                      │
                      ▼
         [ 6. Hard Completion Lock & Self-Healing Loop ]
        └── python -m ccba_harness verify-patch --preset skill --target ...
            ├── PASS (Exit 0) ──> Hoàn tất bàn giao (Spoke: Kích hoạt /ccba-contribute-to-hub)
            └── FAIL (Exit != 0) ──> Kích hoạt /ccba-skill-repair loop (tối đa 2 lần thử lại)
```
