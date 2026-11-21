---
name: ccba-skill-repair
description: Phục hồi và sửa chữa kỹ năng AI theo thể chế ADR-0057 và bộ kiểm định ccba-harness.
metadata:
  version: "1.1.1"
  author: "CCBA Hub"
disable-model-invocation: true
user-invocable: true
command: /ccba-skill-repair
bundle: _core
scope: universal
posture: seam-exempt
tier: kernel
gpi: {s: 3.0, k: 2.0, a: 1.0, p: 1.0}
triggers:
- skill-repair
- ccba-skill-repair
- sửa chữa skill
- phục hồi skill
- repair-skill
---
# Kỹ năng Phục Hồi và Sửa Chữa Kỹ Năng (CCBA Skill Repair)

Kỹ năng này điều phối quy trình khảo sát, phân loại kiến trúc và phục hồi chuẩn mực cho các tệp `SKILL.md` theo Khung Quyết Định Hai Giai Đoạn (ADR-0057 & RES-2026-ARCH-001 v1.2), cổng nghiệm thu tất định (ADR-0058) và nguyên tắc tái sử dụng hợp đồng Seam (ADR-0061) trên toàn hệ thống CCBA Agent Services Platform.

## 🤝 Hợp Đồng Phân Vai Với `/ccba-build-skill` v1.1.1

Để ngăn ngừa xung đột ngữ nghĩa giữa quy trình tạo mới (Greenfield) và quy trình bảo trì (Maintenance):
- **Greenfield (`/ccba-build-skill`):** Cấm truyền cờ `--existing-tier` ở bước tính GPI ban đầu (bắt buộc vượt ngưỡng trần `GPI >= 12.0`) và cấm chỉnh sửa bất kỳ hệ số `s, k, a, p` nào trong vòng tự sửa lỗi.
- **Maintenance (`/ccba-skill-repair`):** Được phép và bắt buộc truyền `--existing-tier tier-2b` khi tệp đích đã khai báo sẵn `tier: kernel`; chỉ được phép chuẩn hóa theo chiều giảm `a` về `1.0` khi phát hiện `disable-model-invocation: true` đi kèm `a > 1.0`.
- **Ưu tiên Hysteresis trước Checklist Greenfield:** Đối với kỹ năng `tier: kernel` hiện hữu có `GPI` thuộc vùng `[11.5, 12.0)`, kết quả JSON `breakdown.preserved_by_hysteresis == 1.0` cùng `allow_standalone_skill: true` được ưu tiên thắng quy tắc từ chối `GPI < 12.0` dành cho kỹ năng mới trong [skill_review_checklist.md](../ccba-build-skill/references/skill_review_checklist.md).
- **Phân biệt định dạng `tier`:** Trường `tier` trong JSON đầu ra của `evaluate-gpi --json` mang chuỗi `ArchitectureTier.value` đầy đủ (`"Tier 1: Package Function / Deep Seam"`, `"Tier 2A: Progressive Reference"`, `"Tier 2B: Standalone Kernel Skill"`, `"Tier 3: Composite Orchestrator"`), trong khi các mã ngắn `tier-1|tier-2a|tier-2b|tier-3` chỉ là tập tham số đầu vào hợp lệ của cờ CLI `--existing-tier`.

---

## Quy trình Thực hiện (Process)

### 0. Tiền kiểm tra môi trường & Phân định Hub vs. Spoke (Environment Pre-flight)

Xác định môi trường qua `git remote get-url origin`:
- **Tại Hub (`ccba-agent-platform`):** Làm việc trực tiếp từ Mục 1 trên cây Hub hiện tại.
- **Tại Spoke:** Đọc `<hub_path>` từ `CCBA_HUB_PATH` (nếu rỗng/sai/trùng toplevel Spoke -> **DỪNG NGAY**). Sau đó phân nhánh:
  * **Nhánh A — Thuộc Hub SSOT (có `<hub_path>/.agents/skills/<skill-dir>/SKILL.md` HOẶC có trong `<hub_path>/.agents/skills/platform-loader/catalog.yaml`):** **CẤM** sửa bản sao vật lý tại Spoke. Kiểm tra `status --porcelain`, `branch --show-current == main` và chưa có PR/nhánh `fix/repair-<tên-skill>`. Nếu Hub bận phiên song song hoặc lệch `origin/main`, tạo `git worktree` cô lập theo `RULE-4.21` (chi tiết tại `references/repair_examples_and_checklist.md`), chạy Mục 1–4, kiểm tra `python "<hub_path_or_wt>/scripts/governance/check_spoke_leakage.py" --root "<hub_path_or_wt>"`, rồi xin xác nhận trước khi mở PR.
  * **Nhánh B — Bản nháp thuần Spoke:** Chạy CLI gói `ccba-harness`:
    ```bash
    python -m ccba_harness validate-skill --file <path-to-skill> --enforce-gpi
    python -m ccba_harness.cli evaluate-gpi --file <path-to-skill> --json
    ```
- **Tiêu chí hoàn thành:** Xác định chính xác ngữ cảnh Hub hay Spoke, bảo đảm không ghi đè trái phép bản sao SSOT tại Spoke và sẵn sàng đúng bộ lệnh kiểm định tương ứng.

### 1. Khảo sát hư hỏng & Linter Failure (Triage & Failure Diagnosis)

Quét lỗi theo trình tự **YAML-First**:
- Chạy `python scripts/validate_skills.py --file <path-to-skill> --enforce-gpi` (gọi ngầm `audit_skills_hygiene.py`).
- **Cổng YAML-First:** Nếu báo `YAML_PARSE_ERROR` hoặc `MALFORMED_FRONTMATTER` -> vá cú pháp YAML (2 spaces, đóng ngoặc, `---`) và xác nhận bằng `python -m ccba_harness validate-skill --file <path-to-skill> --enforce-gpi` trước khi xét `tier` hay gọi `evaluate-gpi`.
- Kiểm tra `tier` & `gpi:`:
  * Nếu `tier: orchestrator`: miễn khối `gpi:`.
  * Nếu thiếu 4 khóa `s, k, a, p`: chuyển sang Chế độ A ở Mục 2 (không gọi `evaluate-gpi --file` trần khi thiếu `gpi:`).
  * Nếu đủ `gpi:`: chạy `python -m ccba_harness.cli evaluate-gpi --file <path-to-skill> --json`, chỉ truyền `--existing-tier tier-2b --json` khi frontmatter đã có sẵn `tier: kernel` từ trước.
- Lập danh sách vi phạm (YAML, GPI/`a: 1.0`, `**Tiêu chí hoàn thành:**`, link/Index Level 3, `description > 180` nếu model-invoked, Slash Command, `RE_DEAD_WOOD`/`RE_BASHISMS`/`RE_START_PROCESS`, Script Bloat `> 100 LOC`).
- **Tiêu chí hoàn thành:** Frontmatter YAML parse hợp lệ và lập xong danh sách phân loại chính xác mọi lỗi cấu trúc, vệ sinh hoặc thể chế của kỹ năng đích.

### 2. Phân tích cấu trúc & Vá khối `gpi:` (Structural Analysis & GPI Patching)

Phân loại 3 tầng trên YAML hợp lệ (ADR-0057 & RES-2026-ARCH-001 v1.2):
- **Miễn trừ Tier 3 (`tier: orchestrator`):** Tự xếp vào `"Tier 3: Composite Orchestrator"` (`allow_standalone_skill: false` là hợp lệ); **CẤM** thêm `gpi:`.
- **Cổng 0 & Cổng 1 (Stop & Propose):** Nếu thuần tất định không cần LLM -> `"Tier 1: Package Function / Deep Seam"`; nếu điều phối đa tác tử/HITL viết nhầm thành kernel -> Tier 3. Khi vi phạm -> **Stop & Propose**, không cấp `tier: kernel`.
- **Chế độ A (thiếu `gpi:`):** Trích xuất **4 dòng bằng chứng quan sát được** (khóa `a: 1.0` nếu `disable-model-invocation: true`), chạy:
  ```bash
  python -m ccba_harness.cli evaluate-gpi --file <path-to-skill> --s <S> --k <K> --a <A> --p <P> [--existing-tier tier-2b] --json
  ```
  Kiểm tra `ArchitectureTier.value` (`tier`), `allow_standalone_skill` và `breakdown.preserved_by_hysteresis`; chỉ ghi `gpi: {s, k, a, p}` nếu `tier == "Tier 2B: Standalone Kernel Skill"` và `allow_standalone_skill: true`, ngược lại **Stop & Propose** gộp vào `references/*.md`.
- **Chế độ B (Anti-Inflation Lock):** Cấm nâng hệ số `s, k, a, p`; chỉ được hạ `a: 1.0` vào file trước khi bật `disable-model-invocation: true` mà `a > 1.0`, rồi chạy lại `evaluate-gpi --file` (chỉ gắn `--existing-tier tier-2b --json` nếu vốn có sẵn `tier: kernel`).
- **Tiêu chí hoàn thành:** Phân định chuẩn xác tầng kiến trúc của kỹ năng; khối `gpi:` (nếu thuộc Tier 2B) được xác thực qua JSON `evaluate-gpi` mà không xảy ra bất kỳ hành vi bơm điểm giả tạo nào.

### 3. Khôi phục liên kết, Tiêu chí hoàn thành & Xử lý Scripts (Remediation & De-bloat)

- **Cấp độ 1 — Allowlist tự vá bề mặt (tối đa 2 vòng SOP):** Vá YAML/`metadata`, `command: /<name>` (chỉ khi `user-invocable: true`), `description <= 180` (chỉ model-invoked), `**Tiêu chí hoàn thành:**`, link tương đối (`../SKILL.md` + Level 3 Index) — **giữ nguyên** dòng có `# ccba:allow-machine-path` hoặc `# ccba:allow-raw-ip`, và dọn `RE_DEAD_WOOD`/`RE_START_PROCESS`/`RE_BASHISMS`.
  * **Cấm ở Mức 1:** Đổi `name`/`bundle`/`tier`, **CẤM tự ghi mới hoặc lật sang `tier: kernel`**, tự đảo `user-invocable`.
  * **SOP Loop Guard:** Trần 2 vòng như `SelfHealingEngine.max_iterations` (**CẤM gọi class `SelfHealingEngine`**, cấm rollback snapshot); ngắt ngay nếu **SHA-256** `SKILL.md` không đổi; cấm gọi đệ quy.
- **Cấp độ 2 — Stop & Propose:** Khi `scripts/` > **100 LOC**, vi phạm Cổng 0/1, rơi Tier 2A, tệp lạc thư mục hoặc sai `name`/`bundle` -> dừng và tra Seam via `python scripts/governance/compile_catalog.py --in <input_types> --out <output_types> --json` (chi tiết tại `references/repair_examples_and_checklist.md`).
- **Tiêu chí hoàn thành:** Mọi lỗi bề mặt thuộc Allowlist Mức 1 được khắc phục gọn trong tối đa 2 vòng lặp (bảo toàn các dòng miễn trừ `# ccba:allow-machine-path`), và mọi ca vi phạm kiến trúc Mức 2 đều có báo cáo Stop & Propose kèm bằng chứng tra cứu Seam.

### 4. Kiểm định bắt buộc & Xác nhận tuân thủ (Mandatory Verification & Compliance)

Khóa cứng đồng bộ 3 bề mặt Hub và tổ hợp nghiệm thu ADR-0058:

```bash
python scripts/governance/compile_catalog.py
python scripts/governance/compile_skills_docs.py --write
python scripts/sync_hub_adr_matrix.py
python scripts/validate_skills.py --file <path-to-skill> --enforce-gpi
python -m ccba_harness.cli evaluate-gpi --file <path-to-skill> [--existing-tier tier-2b] --json
python scripts/governance/compile_skills_docs.py --check
python -m pytest tests/governance/test_workflow_script_parity.py -q
python -m ccba_harness verify-patch --preset skill --target <path-to-skill>
```

- Với `evaluate-gpi`, bắt buộc xác nhận `tier == "Tier 2B: Standalone Kernel Skill"` và `allow_standalone_skill: true` (không chỉ nhìn mã thoát 0). Nếu dẫn tới script Spoke mới, đăng ký vào `SPOKE_SPECIFIC_SCRIPTS` trong `tests/governance/test_workflow_script_parity.py`. Tại Spoke dùng `python -m ccba_harness validate-skill --file <path-to-skill> --enforce-gpi`. Thất bại -> **DỪNG NGAY**, giữ diff và in `stderr`/JSON.
- **Tiêu chí hoàn thành:** Toàn bộ chuỗi đồng bộ 3 bề mặt, `validate_skills.py --enforce-gpi`, `compile_skills_docs.py --check`, `verify-patch --preset skill` đạt mã thoát `0` (100% PASS) và kết quả JSON `evaluate-gpi` xác nhận hợp lệ tầng kiến trúc đích.

---

## Tiêu chí hoàn thành (Completion Criteria)

* [x] Bước 0: Xác thực Hub vs. Spoke (`CCBA_HUB_PATH`), bảo vệ bản sao SSOT tại Spoke.
* [x] Bước 1–2: Vá `YAML_PARSE_ERROR` trước; tuân thủ miễn trừ Orchestrator, khóa Anti-Inflation GPI và giữ hysteresis qua `--existing-tier tier-2b --json`.
* [x] Bước 3–4: Allowlist Mức 1 (<= 2 vòng, khóa SHA-256, giữ `# ccba:allow-machine-path`), `Stop & Propose` cho Script Bloat/Seam, đồng bộ 3 bề mặt và PASS 100% tổ hợp nghiệm thu (`verify-patch --preset skill`).

## Progressive Disclosure & Reference Index (Level 3)

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/repair_examples_and_checklist.md` | Chi tiết lệnh `git worktree` cô lập từ Spoke (`RULE-4.21`), danh mục lỗi Triage Mức 1, công thức GPI và ranh giới Allowlist Mức 1 vs Stop & Propose Mức 2 |
