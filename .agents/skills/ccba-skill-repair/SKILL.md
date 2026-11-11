---
name: ccba-skill-repair
description: Phục hồi và sửa chữa kỹ năng AI theo thể chế ADR-0057 và bộ kiểm định ccba-harness.
metadata:
  version: "1.1.0"
  author: "CCBA Hub"
disable-model-invocation: true
user-invocable: true
command: /ccba-skill-repair
bundle: _core
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

## 🏛️ Platform-Aware Architecture Posture

- **Seam Capability Posture**: `seam-exempt`. Kỹ năng này là SOP kernel chuyên trách chẩn đoán và phục hồi tệp `SKILL.md`, phối hợp trực tiếp với các CLI kiểm định chính thức (`validate_skills.py`, `ccba_harness validate-skill`, `evaluate-gpi`, `verify-patch --preset skill`). Các card trong `seam-contracts.yaml` không bao phủ nghiệp vụ sửa chữa đặc tả kỹ năng, do đó kỹ năng mang tư thế `seam-exempt` và tuyệt đối không sinh thêm script Python ad-hoc cục bộ.
- **Governance Compliance**: Đạt chuẩn Governance ADR-0057 Tier 2B Standalone Kernel Skill với điểm GPI (`s: 3.0, k: 2.0, a: 1.0, p: 1.0`) = `12.0 >= 12.0` (thuộc nhánh Tier 2B và nằm trong dải trễ hysteresis `[11.5, 12.5)`). Khối `gpi` một dòng được khóa bất biến và kỹ năng không sử dụng thư mục `references/` phụ trợ.

## 🤝 Hợp Đồng Phân Vai Với `/ccba-build-skill` v1.1.1

Để ngăn ngừa xung đột ngữ nghĩa giữa quy trình tạo mới (Greenfield) và quy trình bảo trì (Maintenance):
- **Greenfield (`/ccba-build-skill`):** Cấm truyền cờ `--existing-tier` ở bước tính GPI ban đầu (bắt buộc vượt ngưỡng trần `GPI >= 12.0`) và cấm chỉnh sửa bất kỳ hệ số `s, k, a, p` nào trong vòng tự sửa lỗi.
- **Maintenance (`/ccba-skill-repair`):** Được phép và bắt buộc truyền `--existing-tier tier-2b` khi tệp đích đã khai báo sẵn `tier: kernel`; chỉ được phép chuẩn hóa theo chiều giảm `a` về `1.0` khi phát hiện `disable-model-invocation: true` đi kèm `a > 1.0`.
- **Ưu tiên Hysteresis trước Checklist Greenfield:** Đối với kỹ năng `tier: kernel` hiện hữu có `GPI` thuộc vùng `[11.5, 12.0)`, kết quả JSON `breakdown.preserved_by_hysteresis == 1.0` cùng `allow_standalone_skill: true` được ưu tiên thắng quy tắc từ chối `GPI < 12.0` dành cho kỹ năng mới trong [skill_review_checklist.md](../ccba-build-skill/references/skill_review_checklist.md).
- **Phân biệt định dạng `tier`:** Trường `tier` trong JSON đầu ra của `evaluate-gpi --json` mang chuỗi `ArchitectureTier.value` đầy đủ (`"Tier 1: Package Function / Deep Seam"`, `"Tier 2A: Progressive Reference"`, `"Tier 2B: Standalone Kernel Skill"`, `"Tier 3: Composite Orchestrator"`), trong khi các mã ngắn `tier-1|tier-2a|tier-2b|tier-3` chỉ là tập tham số đầu vào hợp lệ của cờ CLI `--existing-tier`.

---

## Quy trình Thực hiện (Process)

### 0. Tiền kiểm tra môi trường & Phân định Hub vs. Spoke (Environment Pre-flight)

Xác định môi trường làm việc qua `git remote get-url origin` trước khi chạm vào bất kỳ tệp kỹ năng nào:
- **Trường hợp đứng tại Hub (`origin` chứa `ccba-agent-platform`):** Tiến hành trực tiếp từ Mục 1 trên cây thư mục Hub hiện tại.
- **Trường hợp đứng tại Spoke:** Đọc `<hub_path>` từ biến môi trường `CCBA_HUB_PATH` (`$CCBA_HUB_PATH` trên Bash hoặc `$env:CCBA_HUB_PATH` trên PowerShell). Nếu `CCBA_HUB_PATH` trống, không trỏ tới thư mục kho Hub hợp lệ hoặc trùng toplevel Spoke $\rightarrow$ **DỪNG NGAY** trước khi phân nhánh (tuyệt đối không tự rơi xuống Nhánh B khi chưa xác minh được kho Hub). Sau khi `<hub_path>` đã resolve hợp lệ, phân nhánh theo **sự tồn tại thực tế trên Hub** (lưu ý: riêng tiền tố `ccba-*` / `bigbim-*` **không đủ** để kết luận thuộc Hub SSOT vì bản nháp cục bộ hợp lệ tại Spoke cũng mang các tiền tố này):
  * **Nhánh A — Kỹ năng thuộc Hub SSOT (tồn tại tệp `<hub_path>/.agents/skills/<skill-dir>/SKILL.md` HOẶC có `name` đăng ký trong `<hub_path>/.agents/skills/platform-loader/catalog.yaml`):**
    * **CẤM tuyệt đối** sửa trực tiếp bản sao vật lý tại `.agents/skills/` của Spoke nhằm ngăn chặn hiện tượng Split-Brain Drift khi chạy đồng bộ ngược.
    * Kiểm tra tuần tự 4 điều kiện an toàn trên `<hub_path>` (**CẤM** tự động chạy `git checkout` chuyển nhánh có sẵn hoặc `git pull`):
      * `<hub_path>` tồn tại hợp lệ và `git -C "<hub_path>" rev-parse --show-toplevel` khác với toplevel của Spoke hiện tại.
      * Cây làm việc Hub hoàn toàn sạch: `git -C "<hub_path>" status --porcelain` trả về rỗng.
      * Hub đang đứng đúng nhánh tích hợp mặc định `main`: `git -C "<hub_path>" branch --show-current` trả về `main`.
      * Chưa tồn tại nhánh `fix/repair-<tên-skill>` cục bộ hoặc Pull Request mở trùng tên trên remote.
    * Nếu bất kỳ điều kiện nào vi phạm $\rightarrow$ **DỪNG NGAY** và thông báo để người dùng xử lý trạng thái kho Hub.
    * Khi cả 4 điều kiện đạt: tạo nhánh mới `git -C "<hub_path>" checkout -b fix/repair-<tên-skill>`, thực hiện toàn bộ Mục 1–4 trên `<hub_path>`, chạy kiểm tra chống rò rỉ dữ liệu Spoke bằng lệnh đa nền tảng:
      ```bash
      python "<hub_path>/scripts/governance/check_spoke_leakage.py" --root "<hub_path>"
      ```
      Sau khi nghiệm thu đạt 100%, dừng lại xin xác nhận rõ ràng của người dùng trước khi mở PR qua `/ccba-contribute-to-hub`.
  * **Nhánh B — Bản nháp cục bộ thuần Spoke (chưa có `<hub_path>/.agents/skills/<skill-dir>/SKILL.md` VÀ chưa có tên trong `catalog.yaml` của Hub):** Do Spoke không chứa `scripts/validate_skills.py`, sử dụng trực tiếp CLI của gói `ccba-harness`:
    ```bash
    python -m ccba_harness validate-skill --file <path-to-skill> --enforce-gpi
    python -m ccba_harness.cli evaluate-gpi --file <path-to-skill> --json
    ```
- **Tiêu chí hoàn thành:** Xác định chính xác ngữ cảnh Hub hay Spoke, bảo đảm không ghi đè trái phép bản sao SSOT tại Spoke và sẵn sàng đúng bộ lệnh kiểm định tương ứng.

### 1. Khảo sát hư hỏng & Linter Failure (Triage & Failure Diagnosis)

Quét lỗi tĩnh, vệ sinh kỹ năng và hiện trạng GPI theo đúng trình tự ưu tiên **YAML-First**:
- Trên Hub, chạy lệnh chẩn đoán tổng thể có cưỡng chế chỉ số GPI và kiểm toán vệ sinh (`audit_skills_hygiene.py`):
  ```bash
  python scripts/validate_skills.py --file <path-to-skill> --enforce-gpi
  ```
- **Cổng chặn YAML-First (bắt buộc xử lý trước mọi bước khác):**
  * Nếu kết quả báo `YAML_PARSE_ERROR` hoặc `MALFORMED_FRONTMATTER` khiến parser không đọc được metadata $\rightarrow$ thực hiện **vá cú pháp YAML mức 1 ngay lập tức** (chuẩn hóa thụt lề `2 spaces`, đóng kín cặp dấu ngoặc kép/ngoặc vuông, khôi phục cặp thẻ phân cách `---`) và xác nhận lại tức thời ở cấp tệp bằng lệnh:
    ```bash
    python -m ccba_harness validate-skill --file <path-to-skill> --enforce-gpi
    ```
    *(Lưu ý: dùng `validate-skill` ở bước trung gian này để xác nhận YAML hợp lệ ngay lập tức mà không bị nhiễu bởi kiểm tra đồng bộ `catalog.yaml` / `docs/` toàn cục của `validate_skills.py` trước khi tới Mục 4).*
  * Tuyệt đối **KHÔNG** đọc `tier`, không xét Cổng 0/Cổng 1 và không gọi `evaluate-gpi` khi frontmatter YAML chưa parse thành công.
- Sau khi YAML đã parse hợp lệ, kiểm tra trường `tier` và khối `gpi:` trong frontmatter:
  * Nếu khai báo `tier: orchestrator` $\rightarrow$ ghi nhận kỹ năng thuộc nhóm Composite Orchestrator (được miễn trừ khối `gpi:`).
  * Nếu là kỹ năng thường nhưng thiếu hoặc chưa đủ 4 khóa `s, k, a, p` (`MISSING_GPI_METRICS`) $\rightarrow$ ghi nhận để chuyển sang Chế độ A ở Mục 2 (không gọi `evaluate-gpi --file` trần lúc này vì thiếu `gpi:` sẽ ném `ValueError` với mã thoát `1`).
  * Nếu đã có đủ khối `gpi:` $\rightarrow$ chạy lệnh đánh giá chỉ số Granularity & Placement Index (GPI) kèm xuất JSON, trong đó **chỉ gắn `--existing-tier tier-2b` khi frontmatter vốn đã khai báo sẵn `tier: kernel` trước phiên sửa** (do `audit_skill()` tự ánh xạ `tier: kernel` còn `evaluate_skill_file()` thì không):
    ```bash
    python -m ccba_harness.cli evaluate-gpi --file <path-to-skill>
    # Khi tệp CHƯA khai báo sẵn tier: kernel:
    python -m ccba_harness.cli evaluate-gpi --file <path-to-skill> --json
    # Chỉ khi tệp ĐÃ khai báo sẵn tier: kernel từ trước:
    python -m ccba_harness.cli evaluate-gpi --file <path-to-skill> --existing-tier tier-2b --json
    ```
- Tổng hợp đầy đủ danh mục vi phạm phát hiện được:
  * Lỗi cú pháp YAML (`YAML_PARSE_ERROR`, `MALFORMED_FRONTMATTER`) và thiếu trường quản trị (`metadata.version`, `metadata.author`).
  * Thiếu khối `gpi: {s, k, a, p}`, lệch chuẩn `a: 1.0` trên kỹ năng `disable-model-invocation: true`, hoặc điểm rơi ngoài ngưỡng Tier 2B.
  * Thiếu dòng `**Tiêu chí hoàn thành:**` (hoặc `**Completion Criterion:**`) ở các bước quy trình tuần tự.
  * Liên kết tương đối bị gãy (`BROKEN_MARKDOWN_LINK`), liên kết ngược sai chuẩn `../SKILL.md` từ trong `references/`, thiếu bảng Level 3 Reference Index khi có tệp `references/*.md`, hoặc dùng đường dẫn ổ đĩa tuyệt đối chưa được đóng dấu miễn trừ.
  * Độ dài `description` vượt quá 180 ký tự đối với kỹ năng model-invoked (`disable-model-invocation` không bật).
  * Lệch hợp đồng Slash Command ADR-0056 (`user-invocable: true` nhưng thiếu hoặc sai `command: /<name>`), hoặc sai chuẩn namespace `ccba-` / `bigbim-`.
  * Vi phạm vệ sinh `audit_skills_hygiene.py` (`RE_DEAD_WOOD`, `RE_BASHISMS` không tương thích Windows PowerShell, `RE_START_PROCESS` thiếu khối `try/catch` bảo vệ headless, tệp `.md` lạc ở thư mục gốc kỹ năng hoặc tệp phi `.md` nằm trong `references/`).
  * Vi phạm rào chắn Chống Script Bloat: thư mục `scripts/` chứa tệp vượt quá **100 LOC**.
- **Tiêu chí hoàn thành:** Frontmatter YAML parse hợp lệ và lập xong danh sách phân loại chính xác mọi lỗi cấu trúc, vệ sinh hoặc thể chế của kỹ năng đích.

### 2. Phân tích cấu trúc & Vá khối `gpi:` (Structural Analysis & GPI Patching)

Phân loại kiến trúc 3 tầng theo Khung Quyết Định Hai Giai Đoạn (ADR-0057 & RES-2026-ARCH-001 v1.2) trên dữ liệu YAML đã hợp lệ:
- **Miễn trừ Tier 3 Orchestrator:** Nếu frontmatter khai báo `tier: orchestrator` (điều phối `>= 2` sub-domains, StateGraph checkpoints hoặc cổng HITL), validator tự động xếp vào `"Tier 3: Composite Orchestrator"` (`allow_standalone_skill: false` trong JSON là hành vi chuẩn của Tier 3). **CẤM** chèn nhầm khối `gpi:` vào kỹ năng `tier: orchestrator`.
- **Cổng 0 (The Determinism Gate) & Cổng 1 (The Orchestration Gate) — Chế độ Stop & Propose:**
  * **Cổng 0:** Nếu tác vụ giải quyết được 100% bằng thuật toán tất định thuần túy (regex, AST parse, toán học, file I/O không cần LLM suy luận) $\rightarrow$ thuộc `"Tier 1: Package Function / Deep Seam"` trong `packages/*/src/`.
  * **Cổng 1:** Nếu tác vụ mang bản chất điều phối đa tác tử phức hợp hoặc HITL nhưng đang viết nhầm thành kernel skill $\rightarrow$ thuộc `"Tier 3: Composite Orchestrator"`.
  * Khi phát hiện vi phạm Cổng 0 hoặc Cổng 1: **DỪNG SỬA TẠI CHỖ (Stop & Propose)**, tra cứu Seam liên quan và xuất báo cáo chẩn đoán đề xuất phương án chuyển đổi kiến trúc để người dùng phê duyệt kế hoạch riêng; tuyệt đối không cấp phép Standalone Kernel Skill.
- **Công thức Chỉ số Granularity & Placement Index (GPI) cho ứng viên Tier 2:**
  * $s$ (Reasoning Steps): `1.0 - 5.0` (số bước suy luận nhận thức).
  * $k$ (Interface / Schema Complexity): `1.0 - 5.0` (độ phức tạp tham số/schema).
  * $a$ (Autonomous Model Invocation): `1.0 - 5.0` (mức độ tự chủ kích hoạt của mô hình; bắt buộc `a = 1.0` nếu `disable-model-invocation: true`).
  * $p$ (Parent Domain Coupling): `1.0 - 5.0` (mức độ phụ thuộc vào Master Skill sở hữu).
  $$GPI = (s \times 2.5) + (k \times 2.0) + (a \times 2.0) - (p \times 1.5)$$
- **Chế độ A — Bổ sung khối `gpi:` bị thiếu (chỉ áp dụng khi frontmatter chưa có đủ `s, k, a, p`):**
  * Trích xuất tường minh **4 dòng bằng chứng quan sát được** từ nội dung `SKILL.md` tương ứng với từng chiều `S, K, A, P` trước khi gán điểm; khóa cứng `a: 1.0` nếu `disable-model-invocation: true`.
  * Chạy kiểm chứng công thức bằng CLI (chỉ có tác dụng khi tệp chưa đủ 4 khóa `gpi`; **tuyệt đối không gắn `--existing-tier`** trừ phi frontmatter vốn đã có sẵn `tier: kernel` trước phiên sửa):
    ```bash
    # Mặc định khi tệp CHƯA có sẵn tier: kernel:
    python -m ccba_harness.cli evaluate-gpi --file <path-to-skill> --s <S> --k <K> --a <A> --p <P> --json
    # Chỉ khi tệp ĐÃ có sẵn tier: kernel từ trước phiên sửa:
    python -m ccba_harness.cli evaluate-gpi --file <path-to-skill> --s <S> --k <K> --a <A> --p <P> --existing-tier tier-2b --json
    ```
  * Đọc JSON đầu ra của đúng câu lệnh áp dụng trên theo thứ tự: kiểm tra `tier` (`ArchitectureTier.value`) trước, sau đó kiểm tra cờ top-level `allow_standalone_skill` và `breakdown.preserved_by_hysteresis`.
  * Nếu `tier == "Tier 2B: Standalone Kernel Skill"` và `allow_standalone_skill: true` $\rightarrow$ ghi khối một dòng `gpi: {s: <S>, k: <K>, a: <A>, p: <P>}` vào frontmatter.
  * Nếu `allow_standalone_skill: false` (ví dụ rơi về `"Tier 2A: Progressive Reference"` do $GPI < 12.0$ trên skill chưa có `tier: kernel`) $\rightarrow$ chuyển sang **Stop & Propose** đề xuất gộp vào `references/*.md` của Master Skill phù hợp; **NGHIÊM CẤM** nâng khống hệ số để ép đạt `12.0`.
- **Chế độ B — Khóa chống lạm phát điểm trên khối `gpi:` đã tồn tại (Anti-Inflation Lock):**
  * **NGHIÊM CẤM** tự ý tăng bất kỳ hệ số `s, k, a, p` nào trong khối `gpi:` sẵn có nhằm lách cổng kiểm định.
  * Ngoại lệ duy nhất được phép chỉnh sửa là **hạ `a` xuống `1.0`** khi phát hiện mâu thuẫn `disable-model-invocation: true` nhưng `a > 1.0`. Do `evaluate-gpi --file` bỏ qua các cờ `--s/--k/--a/--p` khi frontmatter đã có đủ 4 khóa, Agent phải **ghi giá trị `a: 1.0` vào tệp trước**, rồi chạy lại câu lệnh tương ứng với trạng thái `tier` gốc của tệp:
    ```bash
    # Khi tệp CHƯA có sẵn tier: kernel trước phiên sửa (cấm truyền --existing-tier):
    python -m ccba_harness.cli evaluate-gpi --file <path-to-skill> --json
    # Chỉ khi tệp ĐÃ có sẵn tier: kernel trước phiên sửa:
    python -m ccba_harness.cli evaluate-gpi --file <path-to-skill> --existing-tier tier-2b --json
    ```
  * Rẽ nhánh giữ/hạ tầng theo đúng JSON của câu lệnh tương ứng trên: chỉ đối với tệp **vốn đã có sẵn `tier: kernel` trước phiên sửa**, nếu JSON có `--existing-tier tier-2b` trả về `tier == "Tier 2B: Standalone Kernel Skill"` và `allow_standalone_skill: true` (kể cả nhờ `breakdown.preserved_by_hysteresis == 1.0` trong đoạn `[11.5, 12.0)`), mới được giữ nguyên `tier: kernel`. Với tệp chưa phải `tier: kernel` (hoặc khi JSON tương ứng trả về `allow_standalone_skill: false`), phải dừng sửa tại chỗ và chuyển sang **Stop & Propose** đề xuất hạ xuống Tier 2A.
- **Tiêu chí hoàn thành:** Phân định chuẩn xác tầng kiến trúc của kỹ năng; khối `gpi:` (nếu thuộc Tier 2B) được xác thực qua JSON `evaluate-gpi` mà không xảy ra bất kỳ hành vi bơm điểm giả tạo nào.

### 3. Khôi phục liên kết, Tiêu chí hoàn thành & Xử lý Scripts (Remediation & De-bloat)

Thực thi sửa chữa theo ranh giới tách bạch nghiêm ngặt giữa **Allowlist Tự Vá Mức 1** và **Stop & Propose Mức 2**:
- **Cấp độ 1 — Allowlist tự vá bề mặt tại chỗ (Trần tối đa 2 vòng lặp SOP):**
  * Chỉ được phép tự động sửa các hạng mục bề mặt sau:
    * Khôi phục cú pháp YAML frontmatter và bổ sung `metadata.version` / `metadata.author` bị thiếu.
    * Điền hoặc đồng bộ `command: /<name>` theo chuẩn ADR-0056 **chỉ khi** tệp đã khai báo sẵn `user-invocable: true`.
    * Cô đọng `description` xuống `<= 180` ký tự **chỉ đối với** kỹ năng model-invoked (không áp trần 180 cho kỹ năng có `disable-model-invocation: true`).
    * Bổ sung dòng `- **Tiêu chí hoàn thành:**` (hoặc `- **Completion Criterion:**`) cho từng bước quy trình tuần tự còn thiếu.
    * Chuẩn hóa các liên kết Markdown sang đường dẫn tương đối hợp lệ (gồm sửa liên kết ngược thành `../SKILL.md` trong `references/` và cập nhật bảng Level 3 Reference Index cho các tệp `references/*.md`), **NHƯNG BẮT BUỘC giữ nguyên** mọi dòng có chú thích miễn trừ hợp lệ `# ccba:allow-machine-path` hoặc `# ccba:allow-raw-ip`.
    * Loại bỏ các tàn dư văn bản lỗi thời (`RE_DEAD_WOOD`), bọc `try/catch` cho lệnh khởi chạy tiến trình (`RE_START_PROCESS`) hoặc thay thế cú pháp `RE_BASHISMS` đơn giản sang lệnh đa nền tảng tương đương mà không làm đổi nghĩa quy trình.
  * **Các hành vi bị CẤM trong tự vá Mức 1:** CẤM tự đổi định danh `name`, `bundle`, khóa `tier` (đặc biệt **CẤM tự ghi mới hoặc lật sang `tier: kernel`** ở Mức 1 để trục lợi cơ chế hysteresis), hoặc tự đảo giá trị boolean `user-invocable`.
  * **Cơ chế chống lặp vô hạn (SOP Loop Guard):** Giới hạn tối đa **2 vòng lặp** sửa chữa — kiểm định (đồng bộ mức trần số nguyên `2` với `SelfHealingEngine.max_iterations`, nhưng đây là quy tắc SOP thuần túy: **CẤM gọi class `SelfHealingEngine`**, **CẤM rollback snapshot** để giữ nguyên diff phục vụ chẩn đoán). Ngắt vòng lặp ngay lập tức nếu mã băm **SHA-256** của tệp `SKILL.md` không thay đổi giữa hai lần thử liên tiếp. **CẤM gọi đệ quy** `/ccba-skill-repair` hoặc `/ccba-build-skill`.
- **Cấp độ 2 — Phẫu thuật Kiến trúc & Vệ sinh Thư mục (Stop & Propose — CẤM tự động di dời code trong cùng lệnh vá):**
  * Kích hoạt ngay khi gặp một trong các trường hợp: (1) thư mục `scripts/` chứa mã nguồn vượt trần **100 LOC** (vi phạm rào chắn Chống Script Bloat); (2) vi phạm Cổng 0 / Cổng 1; (3) kỹ năng rơi xuống Tier 2A (`allow_standalone_skill: false`); (4) phát hiện tệp `.md` lạc ở gốc kỹ năng hoặc tệp phi `.md` nằm trong `references/` cần di dời/xóa vật lý; hoặc (5) `name` / `bundle` sai chuẩn cần quyết định phân phối lại.
  * Quy trình bắt buộc: dừng chỉnh sửa phức hợp, tra cứu hợp đồng Seam sẵn có trên nền tảng theo ADR-0061 bằng lệnh:
    ```bash
    python scripts/governance/compile_catalog.py --in <input_types> --out <output_types> --json
    ```
    Sau đó lập báo cáo chẩn đoán chi tiết (nêu rõ vị trí vi phạm, Seam tái sử dụng được hoặc gói đích `packages/*/src/` để rút gọn wrapper xuống `< 100 LOC`) và trình người dùng phê duyệt kế hoạch triển khai riêng.
- **Tiêu chí hoàn thành:** Mọi lỗi bề mặt thuộc Allowlist Mức 1 được khắc phục gọn trong tối đa 2 vòng lặp (bảo toàn các dòng miễn trừ `# ccba:allow-machine-path`), và mọi ca vi phạm kiến trúc Mức 2 đều có báo cáo Stop & Propose kèm bằng chứng tra cứu Seam.

### 4. Kiểm định bắt buộc & Xác nhận tuân thủ (Mandatory Verification & Compliance)

Khóa cứng chu trình đồng bộ và nghiệm thu tất định theo ADR-0058 trước khi tuyên bố hoàn tất:
- **Đồng bộ 3 bề mặt quản trị trong mỗi vòng lặp trên Hub:** Sau mỗi lần chỉnh sửa `SKILL.md` trên Hub, bắt buộc chạy đủ 3 trình biên dịch đồng bộ **trước khi** chạy các lệnh kiểm định `--check` để không làm hao phí vòng lặp vì lệch chỉ mục:
  ```bash
  python scripts/governance/compile_catalog.py
  python scripts/governance/compile_skills_docs.py --write
  python scripts/sync_hub_adr_matrix.py
  ```
- **Tổ hợp lệnh nghiệm thu bắt buộc (Hard Completion Lock):**
  * Chạy kiểm định tĩnh và vệ sinh kỹ năng:
    ```bash
    python scripts/validate_skills.py --file <path-to-skill> --enforce-gpi
    ```
  * Chạy đánh giá GPI và kiểm tra cấu trúc JSON theo đúng trạng thái `tier` gốc trước phiên sửa (áp dụng cho mọi kỹ năng không phải `tier: orchestrator`):
    ```bash
    python -m ccba_harness.cli evaluate-gpi --file <path-to-skill>
    # Mặc định khi tệp CHƯA có sẵn tier: kernel trước phiên sửa:
    python -m ccba_harness.cli evaluate-gpi --file <path-to-skill> --json
    # Chỉ khi tệp ĐÃ có sẵn tier: kernel từ trước phiên sửa:
    python -m ccba_harness.cli evaluate-gpi --file <path-to-skill> --existing-tier tier-2b --json
    ```
    *(Bắt buộc xác nhận trong JSON trường `tier == "Tier 2B: Standalone Kernel Skill"` và `allow_standalone_skill: true`; **tuyệt đối không chỉ nhìn mã thoát `0`** vì `evaluate-gpi` vẫn trả mã thoát `0` ngay cả khi `allow_standalone_skill: false`).*
  * Trên Hub, khóa cứng bằng kiểm tra tài liệu Portal và cổng nghiệm thu preset `skill`:
    ```bash
    python scripts/governance/compile_skills_docs.py --check
    python -m ccba_harness verify-patch --preset skill --target <path-to-skill>
    ```
    *(Trên bản nháp cục bộ thuần Spoke, nghiệm thu bằng `python -m ccba_harness validate-skill --file <path-to-skill> --enforce-gpi` kết hợp kiểm tra JSON của `evaluate-gpi`).*
- **Xử lý khi kiểm định thất bại:** Nếu sau tối đa 2 vòng lặp (hoặc khi mã băm SHA-256 đứng yên) bất kỳ lệnh kiểm định nào trả về mã thoát khác `0` hay `allow_standalone_skill: false` trên kỹ năng non-orchestrator $\rightarrow$ **DỪNG NGAY** theo ADR-0058, giữ nguyên diff trên đĩa, in nguyên văn `stderr` / JSON chẩn đoán cho người dùng và nghiêm cấm tuyên bố hoàn thành.
- **Tiêu chí hoàn thành:** Toàn bộ chuỗi đồng bộ 3 bề mặt, `validate_skills.py --enforce-gpi`, `compile_skills_docs.py --check`, `verify-patch --preset skill` đạt mã thoát `0` (100% PASS) và kết quả JSON `evaluate-gpi` xác nhận hợp lệ tầng kiến trúc đích.

---

## Tiêu chí hoàn thành (Completion Criteria)

*   [x] Bước 0: Xác thực an toàn môi trường Hub vs. Spoke (`CCBA_HUB_PATH` sạch, đúng nhánh `main`, không sửa trực tiếp bản sao SSOT tại Spoke).
*   [x] Bước 1: Vá dứt điểm `YAML_PARSE_ERROR` trước tiên và lập danh sách chẩn đoán toàn diện lỗi linter, `audit_skills_hygiene.py` và GPI.
*   [x] Bước 2: Tuân thủ miễn trừ `tier: orchestrator`, khóa chống lạm phát GPI, bảo lưu hysteresis `[11.5, 12.5)` qua `--existing-tier tier-2b --json` và dừng đề xuất khi vi phạm Cổng 0/1 hoặc Tier 2A.
*   [x] Bước 3: Khắc phục các lỗi thuộc Allowlist Mức 1 trong trần 2 vòng lặp (kèm chốt chặn SHA-256 và bảo toàn `# ccba:allow-machine-path`), chuyển mọi ca Script Bloat `> 100 LOC` sang chế độ Stop & Propose kèm tra cứu Seam.
*   [x] Bước 4: Đồng bộ đủ 3 bề mặt Hub và vượt qua 100% lệnh `python scripts/validate_skills.py --file <path> --enforce-gpi`, `python -m ccba_harness.cli evaluate-gpi --file <path>` (xác thực JSON `allow_standalone_skill`), `compile_skills_docs.py --check` cùng `python -m ccba_harness verify-patch --preset skill --target <path>`.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
