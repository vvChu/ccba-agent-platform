# Biên Bản Quyết Định Kiến Trúc & Stress-Test: `/ccba-skill-repair` (Grilling Resolution Log)

- **Ngày thực hiện:** 2026-11-11
- **Phương thức:** `/ccba-grilling` (Stress-Test & Phỏng vấn dồn dập Cây thiết kế)
- **Đối tượng:** Kỹ năng [`ccba-skill-repair`](../../../.agents/skills/ccba-skill-repair/SKILL.md)
- **Tình trạng:** Đã hoàn thành phỏng vấn (All Frontier Nodes Resolved)

---

## 1. Tóm Tắt Định Vị & Bất Biến Bảo Tồn

Kỹ năng `/ccba-skill-repair` đóng vai trò kép trong hệ sinh thái CCBA Agent Services Platform:
1. **Lệnh sửa chữa chủ động (User Ritual):** Chuẩn hóa cú pháp YAML, frontmatter, liên kết tương đối, tiêu chí hoàn thành và thẩm định thể chế 3 tầng cho các kỹ năng hiện hữu hoặc di sản.
2. **Chuẩn tham chiếu phục hồi tự động (Bounded Self-Healing Reference):** Cung cấp rào chắn sửa lỗi có giới hạn cho Bước 6 của [`ccba-build-skill`](../../../.agents/skills/ccba-build-skill/SKILL.md) v1.1.0.

### Ràng buộc Tương thích Ngược Bắt buộc (CI Regression Locks `[đo thực tế]`)
Mọi nâng cấp đối với `ccba-skill-repair` bắt buộc bảo toàn nguyên vẹn:
- Khối `gpi: {s: 3.0, k: 2.0, a: 1.0, p: 1.0}` (`gpi_score = 12.0`, nằm trong dải trễ Hysteresis `[11.5, 12.5)`), `description`, `command: /ccba-skill-repair` và tư thế `seam-exempt` (khóa bởi [`test_ccba_skill_repair_phase3_spec_contract`](../../../tests/governance/test_skill_scaffolding_and_gpi.py)).
- Bốn tiêu đề bước quy trình và hai chuỗi lệnh CLI gốc trong thân bài.
- Bộ 5 ca kiểm thử chuẩn trong [`eval_skill_repair.json`](../../../.agents/skills/ccba-eval-gate/test_cases/eval_skill_repair.json) và 3 bộ chấm điểm regex trong [`domain.py`](../../../packages/ccba-harness/src/ccba_harness/evals/scorers/domain.py).

---

## 2. Ma Trận 4 Quyết Định Kiến Trúc Đã Chốt (Decision Resolution Matrix)

| STT | Nút Thiết Kế (Frontier Node) | Điểm Mù Ở Bản `v1.0.0` | Quyết Định Đã Chốt (`v1.1.0` Target) | Cơ Chế Kiểm Chứng Độc Lập |
| :---: | :--- | :--- | :--- | :--- |
| **01** | **Quy chế Vá `gpi:` & Hysteresis (Bước 2)** | Cho phép LLM tự nhẩm toán và tự vá `gpi:` không phân biệt thêm mới hay sửa cũ (dễ bơm điểm ảo); ghi cứng `$GPI < 12.0 \to$ Tier 2A` mâu thuẫn với Hysteresis. | **Phân tách 2 chế độ + JSON Gate**:<br>- *Missing GPI Backfill:* Khi thiếu `gpi:`, được đề xuất 4 trục kèm **4 dòng bằng chứng quan sát được** (`disable-model-invocation: true` khóa cứng `a: 1.0`) và kiểm chứng qua `evaluate-gpi --json`.<br>- *Anti-Inflation Lock:* Khi đã có `gpi:`, **CẤM** tự ý nâng $s, k, a, p$ để lách `INSUFFICIENT_GPI_SCORE`.<br>- *Hysteresis `[11.5, 12.5)`:* Căn cứ vào `allow_standalone_skill` và `preserved_by_hysteresis` trong JSON của `evaluate-gpi --file <path> --json`. | `python -m ccba_harness.cli evaluate-gpi --file <path> --json` |
| **02** | **Chính sách Khắc phục 2 Cấp độ & Trần Lặp (Bước 3)** | Yêu cầu tự trích xuất script `> 100 LOC` sang `packages/*/src/` ngay trong luồng sửa markdown; không có trần vòng lặp. | **Two-Tier Remediation Policy** đồng bộ với [`SelfHealingEngine`](../../../packages/ccba-harness/src/ccba_harness/healing.py):<br>- *Cấp 1 (Auto-Patch tại chỗ, tối đa 2 vòng):* Vá YAML, frontmatter cơ bản, `description <= 180` ký tự, `Tiêu chí hoàn thành:`, link tương đối. Ngắt sớm nếu SHA-256 không đổi.<br>- *Cấp 2 (Stop & Propose):* Gặp **Script Bloat (`> 100 LOC`)**, vi phạm **Cổng 0 / Cổng 1**, hoặc giáng cấp **Tier 2A** $\to$ **CẤM** di dời code ngầm; lập Biên bản Chẩn đoán (tra cứu Seam qua `compile_catalog.py`) và chờ người dùng duyệt kế hoạch riêng kèm `verify-patch --preset code`. | Bộ đếm trần `<= 2` + kiểm tra bất biến SHA-256. |
| **03** | **Đồng bộ 3 Bề mặt & Khóa Cứng Nghiệm thu (Bước 4)** | Chỉ chạy `validate_skills.py`, `evaluate-gpi` và `compile_catalog.py` có điều kiện $\to$ bỏ sót drift `docs/index.html` và `TRACEABILITY_MATRIX.md`. | **Chu trình Đồng bộ 3 Bề mặt & Hard Lock**:<br>1. Giữ nguyên 2 câu lệnh gốc cho tương thích hồi quy.<br>2. Chạy đồng bộ bắt buộc trên Hub: `compile_catalog.py` $\to$ `compile_skills_docs.py --write` $\to$ `sync_hub_adr_matrix.py`.<br>3. Khóa cứng nghiệm thu bằng `compile_skills_docs.py --check` và `python -m ccba_harness verify-patch --preset skill --target <path>` đạt **Exit Code = 0**. | `python -m ccba_harness verify-patch --preset skill --target <path>` |
| **04** | **Pre-flight Môi trường Hub vs. Spoke (Bước 0/1)** | Ngầm định cwd luôn là Hub; sửa trực tiếp bản sao ở Spoke gây Split-Brain Drift hoặc lỗi thiếu script Hub. | **Environment Pre-flight & Anti-Split-Brain**:<br>- Đọc `git remote get-url origin`.<br>- *Ở Hub:* Chạy toàn trình.<br>- *Ở Spoke với skill thuộc Hub:* **CẤM** sửa bản sao tại Spoke; kiểm tra `$CCBA_HUB_PATH` (tồn tại, sạch, khác toplevel Spoke) để sửa trên nhánh đề xuất tại Hub và đóng góp qua `/ccba-contribute-to-hub` (có xác nhận người dùng), rồi mới `sync_spoke.py`.<br>- *Ở Spoke với bản nháp cục bộ:* Dùng cặp CLI độc lập `python -m ccba_harness validate-skill --file <path> --enforce-gpi` và `evaluate-gpi --file <path> --json`. | `git remote get-url origin` & `ccba_harness validate-skill` |

---

## 3. Sơ Đồ Luồng Vận Hành Chuẩn Hóa (`/ccba-skill-repair` v1.1.0)

```text
[ Kích hoạt /ccba-skill-repair <path-to-skill> ]
                      │
                      ▼
       [ Pre-flight Hub vs. Spoke ]
       ├── Hub Mode ─────────────────────────────────────────┐
       └── Spoke Mode                                        │
           ├── Skill đồng bộ từ Hub? ──> Chuyển sang $CCBA_HUB_PATH (cây sạch)
           └── Bản nháp cục bộ Spoke? ──> Dùng ccba_harness validate-skill + evaluate-gpi --json
                      │                                      │
                      ▼                                      ▼
       [ 1. Khảo sát & Chẩn đoán Lỗi (validate_skills / evaluate-gpi --json) ]
                      │
                      ▼
       [ 2. Phân loại Vi phạm: Bề mặt hay Kiến trúc? ]
       ├── Vi phạm Kiến trúc (Cổng 0/1, allow_standalone_skill=false, Script > 100 LOC)
       │   └── DỪNG SỬA NGẦM (Stop & Propose): Xuất Biên bản Chẩn đoán + Chờ duyệt Plan
       │
       └── Lỗi Bề mặt & Thiếu Metadata (YAML, Link, Completion Criteria, Missing GPI)
           ├── Missing GPI: Đính kèm 4 bằng chứng (Ritual khóa a=1.0) + evaluate-gpi --json
           ├── Existing GPI: CẤM bơm điểm s/k/a/p; tôn trọng Hysteresis [11.5, 12.5)
           └── Auto-Patch tại chỗ (Trần <= 2 vòng; ngắt sớm nếu SHA-256 không đổi)
                      │
                      ▼
       [ 3. Chuỗi Đồng bộ 3 Bề mặt (trên Hub) ]
       └── compile_catalog.py ──> compile_skills_docs.py --write ──> sync_hub_adr_matrix.py
                      │
                      ▼
       [ 4. Khóa Cứng Nghiệm thu (Hard Completion Lock) ]
       └── verify-patch --preset skill --target <path> & compile_skills_docs.py --check
           ├── Exit Code == 0 ──> Báo cáo bảng khắc phục (Spoke: Hỏi xác nhận mở PR Hub)
           └── Exit Code != 0 (sau 2 vòng) ──> Dừng báo lỗi kèm stderr (CẤM báo hoàn tất)
```
