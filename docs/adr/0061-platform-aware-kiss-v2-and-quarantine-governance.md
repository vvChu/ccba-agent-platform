# 0061. Platform-Aware KISS v2.0 & Capability Quarantine Governance

* **Status:** Accepted
* **Date:** 2026-09-30
* **Deciders:** CCBA Platform Core Team, Systems Architect & Lead Engineer, Peer Reviewer (Grok 4.7 xhigh)
* **Consulted:** ADR 0044 (Spoke Package Bootstrap), ADR 0047 (Catalog Manifest Compiler), ADR 0051 (Virtual Hub Fallback), ADR 0057 (Two-Stage Granularity Decision Framework & GPI), ADR 0058 (Deterministic Hard Completion Lock), ADR 0060 (4-Hubs × Federated Spokes Architecture), Issue #439

---

## Context & Problem Statement

Trong quá trình thẩm định tài liệu hướng dẫn kiến trúc của Spoke `dgx-spark-toolkit` (`.md/knowledge/platform_aware_kiss_standard.md`), đội ngũ kỹ thuật nền tảng đã phát hiện 4 điểm bảo lưu cốt tử (Platform Reservations) đe dọa trực tiếp tính toàn vẹn của Hiến pháp Nền tảng (Layer 1 Constitution):

1. **Bảo Lưu 1 — Thiếu Chỉ Mục Năng Lực Máy Đọc & Nhập Nhằng Biên Lai Hợp Đồng:**
   - Cơ chế tra cứu seam trước đây (`ccba-platform find-seam <kw>`) dựa thuần túy trên tìm kiếm chuỗi tự do (full-text substring match).
   - Tác tử AI dễ nhầm lẫn giữa gợi ý từ khóa (Keyword Hint) với Biên lai Kiểm toán Hợp đồng (Audit Receipt). Không có schema máy đọc xác định đầu vào/đầu ra (`capability.in/out`) và ràng buộc phần cứng (`hardware`).
2. **Bảo Lưu 2 — Thất Thoát Ranh Giới Thư Viện Gốc & Thiếu Cơ Chế Quản Trị Cách Ly (Quarantine Governance):**
   - Chú thích miễn trừ `# ccba:allow-raw-bypass` xuất hiện rải rác trong mã nguồn monorepo và spoke mà không có thời hạn hết hạn (`until`), không có phân loại lý do kỹ thuật (`reason`), và không truy vết tới GitHub Issue theo dõi.
   - Nguy cơ hình thành các silo dữ liệu cục bộ vĩnh viễn (permanent tech debt) trá hình dưới danh nghĩa KISS.
3. **Bảo Lưu 3 — Đánh Nhầm Kịch Bản Tạm Thời & Ma Sát Ngân Sách Script Tại Spoke:**
   - Bộ linter kiểm tra vệ sinh Spoke (`check_spoke_cleanliness.py`) nhận diện kịch bản tạm thời thuần túy qua tiền tố (`fix_*`, `audit_*`, `patch_*`).
   - Các kịch bản kiểm toán thường trực (như `audit_memory.py` thuộc vai trò `audits`) hoặc tiến trình nền `daemon` bị đánh đồng là file tạm thời, gây ma sát không cần thiết trong quá trình vận hành Spoke.
4. **Bảo Lưu 4 — Rò Rỉ Trạng Thái Máy Tuyệt Đối & Xung Đột Đa Thiết Bị (Multi-Device Portability):**
   - Khi một kho mã nguồn Spoke được clone trên nhiều máy tính (Windows, Linux DGX Spark, macOS, WSL), việc hardcode đường dẫn ổ đĩa tuyệt đối (e.g. `D:\GitHubProjects\...`) vào mã nguồn hoặc `workspace_context.yaml` gây xung đột git và đổ vỡ quy trình CI/CD.
   - Biểu thức chính quy quét rò rỉ đường dẫn máy trước đây bỏ sót các tiền tố raw string (`r"..."`) hoặc đường dẫn ổ đĩa không có dấu gạch chéo kết thúc.

---

## Decision Outcome

Đội ngũ kiến trúc CCBA quyết định ban hành **HUB-ADR-0061** chuẩn hóa khung thể chế **Platform-Aware KISS v2.0** và **Hệ Thống Quản Trị Bộ Điều Hợp Cách Ly (Quarantine Adapter Governance)**:

### 1. Chỉ Mục Hợp Đồng Năng Lực Nền Tảng (`seam-contracts.yaml`)

- Khởi tạo tệp đặc tả duy nhất (Single Source of Truth) tại gốc Hub: `seam-contracts.yaml`.
- Mỗi thẻ năng lực (Capability Card) tuân thủ cấu trúc tối thiểu:
  ```yaml
  cards:
    - seam_id: <identifier>.v<version>
      kind: package | skill | workflow
      import_path: <module>:<Symbol>      # Dành cho package
      command: /<slash-command>           # Dành cho skill
      skill_path: .agents/skills/.../SKILL.md
      capability:
        in: [<data_types>]                # e.g. [pdf, docx]
        out: [<data_types>]               # e.g. [markdown]
      hardware: [any | dgx_spark | cuda]
      failure_modes: [<modes>]
      owner: <team_or_portal>
      implementation_packages: [<pkg_root_modules>]
      forbidden_substitute_imports: [<ast_modules>] # e.g. [fitz, pymupdf]
  ```
- **Ngữ Nghĩa Bao Hàm (Inclusion Semantics):**
  - Mọi giá trị `--in` yêu cầu phải nằm trong `capability.in` của thẻ (thẻ được phép nhận nhiều định dạng đầu vào hơn truy vấn).
  - Mọi giá trị `--out` yêu cầu phải nằm trong `capability.out` của thẻ.
  - Lọc phần cứng: Thẻ có `hardware: [any]` thỏa mãn mọi yêu cầu phần cứng; thẻ chuyên biệt (như `dgx_spark`) chỉ khớp khi truy vấn chỉ định tương ứng.
- **Biên Lai Kiểm Toán Hợp Đồng (Audit Receipt) & Mã Thoát CLI:**
  - Lệnh CLI: `ccba-platform find-seam --in <types> --out <types> [--hardware <hw>] [--json]`.
  - Mã thoát quy chuẩn:
    - `0`: Khớp thành công ít nhất một thẻ năng lực (`status: MATCH`).
    - `2`: Không tìm thấy thẻ năng lực phù hợp (`status: NO_MATCH`), trả về `index_sha256` tính từ đúng các byte thô của tệp `seam-contracts.yaml` trên đĩa.
    - `1`: Sai cú pháp hoặc thiếu tham số.
  - **Phân Định Từ Khóa Vị Trí:** Truy vấn bằng từ khóa vị trí (ví dụ `ccba-platform find-seam pdf`) chỉ trả về gợi ý `KEYWORD_HINT - NOT A CONTRACT RECEIPT` và **CẤM** được coi là biên lai hợp đồng kiểm toán Seam.

### 2. Thể Chế Quản Trị Bộ Điều Hợp Cách Ly (Quarantine Adapter Governance)

- **Cấm Tuyệt Đối Nhánh OR:** Không chấp nhận quy tắc lỏng lẻo "có marker hoặc có import Seam". Chỉ chấp nhận hai trường hợp:
  1. Tệp thuộc danh sách `implementation_packages` của chính Seam Card đó.
  2. Tệp là bộ điều hợp cách ly có chú thích Quarantine Marker còn hiệu lực.
- **Cú Pháp Marker Cưỡng Chế:**
  ```python
  # ccba:quarantine seam_id=<id> reason=<reason> until=<YYYY-MM-DD> issue=<url>
  ```
- **Bộ Quy Tắc Rào Chắn Kiểm Định AST:**
  1. `seam_id`: Bắt buộc tồn tại trong `seam-contracts.yaml`, cấm ký tự path traversal (`..`, `/`, `\`). Card được chỉ định bắt buộc phải quản trị module đang được import (khóa triệt để việc mượn thẻ khác để lách linter).
  2. `reason`: Bắt buộc thuộc một trong 4 giá trị hợp lệ:
     - `hardware_mismatch`: Phần cứng hiện tại không đáp ứng yêu cầu của Seam Card.
     - `seam_regression`: Phát hiện lỗi hồi quy trong Seam đang chờ Hub vá.
     - `health_timeout`: Dịch vụ Seam bị timeout hoặc không phản hồi.
     - `version_conflict`: Xung đột phiên bản phụ thuộc chưa thể giải quyết ngay.
  3. `until`: Định dạng `YYYY-MM-DD`. Linter so sánh trực tiếp với ngày UTC thực tế của hệ thống (`datetime.now(timezone.utc).date()`). Nếu ngày hiện tại vượt quá `until`, linter báo lỗi `QuarantineExpiredViolation`.
  4. `issue`: Bắt buộc khớp biểu thức: `^https://github\.com/vvChu/ccba-agent-platform/issues/\d+$`.
  5. **Vị Trí Lưu Trữ:** Khi bật chế độ cưỡng chế nghiêm ngặt (`--enforce-quarantine-path`), mã nguồn cách ly bắt buộc phải nằm trong `adapters/quarantine/<seam_id>.py`.
- **Chuyển Tiếp Êm Dịu Cho Hub Monorepo:**
  - Mặc định bảo lưu 13 vị trí sử dụng legacy bypass `# ccba:allow-raw-bypass` trên Hub để tránh làm gián đoạn CI hiện hành.
  - Cung cấp cờ `--strict-quarantine` để từ chối toàn bộ legacy bypass và cờ `--dry-run-quarantine` để in báo cáo kiểm toán chi tiết.

### 3. Cơ Chế Allowlist Theo Vai Trò Tại Spoke

- **Quy Tắc: Allowlist Vai Trò THẮNG Tiền Tố Tạm Thời:**
  - Một kịch bản có tên bắt đầu bằng tiền tố tạm thời (`EPHEMERAL_PREFIXES`: `fix_*`, `audit_*`, `patch_*`, `test_tmp_*`, `debug_*`, `tmp_*`, `temp_*`, `oneoff_*`, `scratch_*`), nếu được đăng ký vào vai trò thường trực trong `workspace_context.yaml` (dưới mục `cleanliness.roles`), sẽ **KHÔNG** bị cảnh báo ephemeral hay đề xuất archive.
  - Ví dụ: `audit_memory.py` thuộc vai trò `audits` được công nhận là kịch bản kiểm toán hợp lệ.
- **Tiến Trình Nền (Daemon):**
  - Các script daemon (như `daemon_sync.py`) được tính đúng vào ngân sách 15 tệp của Spoke và không bị gắn nhãn ephemeral chỉ vì tên.
- **Phạm Vi Quét:**
  - Linter vệ sinh script chỉ áp dụng tại thư mục gốc `scripts/*.py` của Spoke, không áp dụng cho các cây thư mục `services/` hoặc `scripts/cron/*.sh`.

### 4. Khử Khớp Trạng Thái Máy Tuyệt Đối (Machine-State Decoupling)

- Cấm tuyệt đối commit đường dẫn ổ đĩa tuyệt đối vào `workspace_context.yaml`. Đường dẫn Hub trên từng máy phải được phân giải độc lập qua biến môi trường hệ thống `CCBA_HUB_PATH`.
- Mẫu Regex chuẩn hóa trong bộ quét vệ sinh:
  ```python
  re.compile(r"""(?:[rR]?["']|[=:]\s*)[A-Za-z]:(?:[\\/]+[A-Za-z0-9_.-]*|[\\/]*["'])""")
  ```
- Mọi đường dẫn fallback mặc định trên môi trường Windows bắt buộc phải được đánh dấu bằng chú thích `# ccba:allow-machine-path`.

### 5. Bảo Toàn Khung Quyết Định Hai Giai Đoạn (ADR-0057)

- Khung thể chế này hoàn toàn tương thích và không làm suy giảm các rào chắn của **ADR-0057**:
  - Cổng 0: Tính Tất Định (Determinism Gate) $\to$ Vượt qua nếu có thể giải quyết bằng logic thuần túy.
  - Cổng 1: Điều Phối Tác Tử (Orchestration Gate) $\to$ Chỉ cấp phép tạo Standalone Kernel Skill (Tier 2B) khi đạt điểm GPI $\ge 12.0$.
  - Mọi giải pháp mã nguồn đơn lẻ dưới 15 dòng phải tuân thủ nguyên tắc KISS, tận dụng trực tiếp Seam hiện có thay vì tạo thêm module phụ thuộc.

---

## Known Limitations

- **AST Inspection Gap Đối Với Out-of-Band HTTP Clients:**
  Bộ quét AST tĩnh duyệt qua các câu lệnh `import` và `from ... import`. Nếu một tác tử tự viết client HTTP thô (raw `urllib` hoặc `requests`) để gọi trực tiếp tới endpoint backend mà không import thư viện thuộc danh mục cấm, linter tĩnh sẽ không phát hiện. Giới hạn này được ghi nhận rõ và sẽ được kiểm soát bổ sung qua Network Egress Gate trong các pha tiếp theo.

---

## Consequences & Verification

- **Tích Cực:**
  - Khép kín hoàn toàn 4 điều kiện bảo lưu kiến trúc từ đợt thẩm định toolkit.
  - Cung cấp cơ chế máy đọc tự động cho việc kiểm toán và sinh biên lai hợp đồng (Audit Receipts).
  - Tách bạch rõ ràng giữa mã nguồn sản xuất, bộ điều hợp cách ly có thời hạn, và mã nguồn tạm thời.
  - Ngăn ngừa triệt để tình trạng xung đột mã nguồn do rò rỉ đường dẫn máy Windows/Linux.
- **Tiêu Chuẩn Kiểm Định (Hard Completion Lock):**
  - Toàn bộ các thay đổi phải vượt qua bộ kiểm tra tất định:
    `python -m ccba_harness verify-patch --preset code`
  - Đảm bảo 100% test suites trong `tests/governance/` (hơn 280 tests) và `scripts/tests/` đều vượt qua thành công.
