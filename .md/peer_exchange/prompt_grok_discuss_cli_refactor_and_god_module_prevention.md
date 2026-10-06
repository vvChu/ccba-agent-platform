---
request_id: "req-arch-audit-cli-god-module-001"
from_agent: "antigravity"
to_agent: "grok"
request_type: "review"
profile: "arch_audit"
subject: "Deep Architectural Audit: Monolithic cli.py Refactor & Systemic God-Module Prevention Strategy"
timestamp: "2026-10-06T11:50:00+07:00"
source_documents:
  - "packages/ccba-harness/src/ccba_harness/cli.py"
  - "packages/ccba-harness/src/ccba_harness/__init__.py"
  - "packages/ccba-harness/AGENTS.md"
  - "docs/adr/0061-platform-aware-kiss-v2-and-quarantine-governance.md"
  - "docs/adr/0065-level-2-hardening-and-fail-closed-preimage-rollback.md"
output_path: ".md/peer_exchange/grok_arch_audit_cli_god_module_prevention.md"
context: "Thẩm định kiến trúc đối kháng về kế hoạch phân rã tệp cli.py (2.704 dòng) thành Pluggable Command Registry và thiết lập rào chắn tự động hóa CI ngăn chặn God Modules theo ADR-0061."
---

# 🏛️ YÊU CẦU THẨM ĐỊNH KIẾN TRÚC ĐỐI KHÁNG (ARCHITECTURAL AUDIT)
## ĐỀ TÀI: TÁI CẤU TRÚC MONOLITHIC `cli.py` & CHIẾN LƯỢC NGĂN CHẶN "GOD MODULE" TOÀN HỆ THỐNG

> ⚠️ **Chỉ Dẫn Cho Reviewer (Architectural Auditor — Grok-4.7 `xhigh`)**:  
> Bạn đang thực hiện nhiệm vụ với hồ sơ **`arch_audit`** (Reasoning Effort: `xhigh`, Tools: `read_file`, `grep`, Cấm: `write_file`).  
> Hãy áp dụng tư duy phản biện đối kháng sâu sắc nhất, đối soát trực tiếp mã nguồn trong `packages/ccba-harness/src/ccba_harness/cli.py` và xuất bản báo cáo thẩm định kỹ thuật kèm khối **`PeerVerdictBlock`** (YAML frontmatter) chuẩn mực theo ADR-0063/ADR-0064.

---

### 1. Bối Cảnh & Vấn Đề Kỹ Thuật

Trong quá trình phát triển các chuỗi tính năng liên tiếp gần đây (Peer Watch, Dispatcher, Co-review, Level-3 Auto-apply, Evals, Telemetry), tệp [`packages/ccba-harness/src/ccba_harness/cli.py`](file:///home/vvc/ccba/ccba-agent-platform/packages/ccba-harness/src/ccba_harness/cli.py) đã tích tụ nợ kỹ thuật và phình to thành một **"God Module"**:
- **Quy mô**: **2.704 dòng code**, 96.5 KB.
- **Phạm vi trách nhiệm**: Chứa 18 hàm top-level, xử lý đồng thời **13 subcommands** thuộc 5 bounded contexts khác nhau (`evals`, `verifier`, `peer`, `telemetry`, `architecture`).
- **Vi phạm quy chuẩn**: Hàm `main()` dài **615 dòng**; các hàm `run_*_cli` dài từ 100 đến 375 dòng (vi phạm trực tiếp quy chuẩn Rule 5: *"Function/method không quá 50 dòng"*).
- **Trùng lặp cấu hình**: Định nghĩa argument parser bị trùng lặp 2 lần (một lần trong hàm `run_*_cli` độc lập, một lần trong `subparsers.add_parser()` của `main()`).
- **Bán kính ảnh hưởng (Blast Radius)**: Hiện có hơn **35 vị trí** gọi trực tiếp từ test suites (`test_cli.py`, `test_peer_*.py`), skills và tool scripts (như `from ccba_harness.cli import run_peer_dispatch_cli` hoặc lệnh gọi shell `python -m ccba_harness.cli evaluate-gpi ...`).

**Nguyên nhân gốc rễ (RCA)**:
1. **Ad-hoc Locality Bias & Ngụy biện KISS**: Mỗi khi bổ sung một lệnh CLI mới, việc nhét thêm 150-200 dòng vào `cli.py` luôn tạo cảm giác "nhanh và đơn giản", nhưng lặp lại 10 lần đã biến nó thành quái vật 2.700 dòng.
2. **Lỗ hổng trong Automated CI Gate**: `verify-patch --preset ci` hiện chỉ kiểm tra syntax (`ruff check`), formatting (`ruff format`) và logic (`pytest`), nhưng **hoàn toàn thiếu rào chắn tĩnh kiểm tra kích thước file và độ dài hàm**. Do đó, một tệp 3.000 dòng vẫn đạt 100% green checks mà không bị cảnh báo hay ngăn chặn.

---

### 2. Giải Pháp Đề Xuất Của Antigravity (4 Trụ Cột)

#### Trụ Cột 1: Pluggable Command Registry (Non-Breaking Modularization)
Chuyển đổi `cli.py` thành một package `packages/ccba-harness/src/ccba_harness/cli/`:
- `__init__.py`: Re-export đầy đủ 100% 18 public symbols cũ (đảm bảo **Zero Breaking Changes** cho 35+ consumers hiện hữu).
- `__main__.py`: Định tuyến trực tiếp tới `cli.core:main`, bảo toàn 100% lệnh thực thi `python -m ccba_harness.cli <subcommand>`.
- `core.py`: Root ArgumentParser và Dispatcher tinh gọn **< 60 dòng**, tự động nạp các command modules.
- Phân rã subcommands theo miền nghiệp vụ độc lập:
  - `cli/commands/peer.py`: `peer-dispatch`, `peer-co-review`, `peer-watch`, `apply-anchor-patch`, `peer-gate`.
  - `cli/commands/verifier.py`: `verify-patch`, `verify-doc`.
  - `cli/commands/evals.py`: `eval`, `evaluate-gpi`, `validate-skill`.
  - `cli/commands/telemetry.py`: `telemetry` (kèm các sub-actions).
  - `cli/commands/architecture.py`: `blast-radius`, `why`.

#### Trụ Cột 2: Rào Chắn CI Kiểm Soát Ngưỡng Tệp & Hàm (Static Module Budget Gate)
Bổ sung một bài kiểm tra tĩnh tự động vào `verify-patch --preset ci`:
- **File Size Budget**: Hard cap **800 dòng** / file `.py` mới trong `packages/` (soft warning ở 500 dòng).
- **Function Length Gate**: Hard cap **80 dòng** / hàm (warning ở 50 dòng).
- **Quarantine Exception**: Cho phép miễn trừ tạm thời có kỳ hạn thông qua chú thích `# ccba:quarantine module_budget=... until=YYYY-MM-DD issue=...` chuẩn theo ADR-0061.

#### Trụ Cột 3: Thin Shell Invariant (Tách Biệt Lớp Giao Diện Khỏi Nghiệp Vụ)
Quy chuẩn hóa: Tệp CLI chỉ đóng vai trò giao diện nhận input, parse args thành Pydantic model và gọi Deep Seams trong Engine/Domain packages. Tuyệt đối cấm nhúng logic nghiệp vụ, disk IO mutation phức tạp hay thuật toán rollback vào lớp CLI.

#### Trụ Cột 4: Cưỡng Chế Pha Refactor Trong Chu Kỳ TDD (Boy Scout Rule)
Trong quy trình làm việc giữa các AI Agent, khi một PR bổ sung > 150 dòng vào một tệp hiện có, Agent bắt buộc phải thực hiện audit độ phình của tệp trước khi mở PR.

---

### 3. Các Trọng Tâm Thẩm Định Phản Biện (Audit Questions Cho Grok)

Hãy mổ xẻ và đánh giá đối kháng các khía cạnh kỹ thuật sau:

1. **Về Cơ Chế Command Registry & Hiệu Năng Khởi Động (Startup Latency)**:
   - Hiện tại `cli.py` sử dụng các lazy imports nằm sâu trong các hàm `run_*_cli` để giảm thiểu thời gian nạp lệnh (start-up time). Nếu tách thành các module trong `cli/commands/`, làm thế nào để cơ chế Command Discovery không làm chậm thời gian khởi động của các lệnh CLI nhanh (như `ccba-harness --version` hay `ccba-harness why`)?
   - Nên dùng cơ chế Explicit Static Registry Tuple (`COMMAND_MODULES = (...)`) hay Dynamic Discovery (`pkgutil.iter_modules`)? Đâu là giải pháp tối ưu theo triết lý KISS và tính tất định (Deterministic)?

2. **Về Ngưỡng Giới Hạn Tệp & Rủi Ro Phân Mảnh Quá Mức (Over-fragmentation)**:
   - Đặt ngưỡng Hard Cap 800 dòng/file và 50-80 dòng/hàm có gây ra tác dụng phụ tiêu cực là "phân mảnh vi mô" (tạo ra hàng chục file nhỏ 30 dòng, làm tăng cognitive load khi đọc code) không?
   - Ngưỡng nào là "Sweet Spot" cho một dự án Python Monorepo kết hợp AI Agent Automation?

3. **Về Chiến Lược Triển Khai & Kiểm Soát Rủi Ro (Migration Strategy)**:
   - Với hơn 35 vị trí phụ thuộc hiện hữu, chiến lược di chuyển an toàn nhất là gì: Thực hiện trong **1 PR Atomic Micro-Refactor** có bộ test hồi quy nghiêm ngặt, hay chia thành **nhiều bước chuyển đổi** (Strangler Fig Pattern)?
   - Bộ test hiện có (`test_cli.py`, `test_peer_*.py`, `test_verify_patch.py`) đã đủ bao phủ 100% ranh giới để đảm bảo không bị gãy lệnh nào trong thực tế chưa?

4. **Đánh Giá Toàn Diện Theo Ma Trận ADR-0061**:
   - Đánh giá đề xuất theo ma trận: **Giá Trị × Độ Phức Tạp × Rủi Ro × KISS**.
   - Có điểm nghẽn, cạm bẫy tiềm ẩn (pitfalls) hoặc giả định sai lầm nào trong đề xuất của Antigravity mà chúng tôi chưa lường hết?

---

### 4. Định Dạng Kết Quả Trả Về

Bắt đầu phản hồi bằng khối `PeerVerdictBlock` YAML frontmatter:
```yaml
---
request_id: "req-arch-audit-cli-god-module-001"
verdict: <APPROVE | APPROVE_WITH_RESERVATIONS | REVISE_PLAN | REJECT>
risk_score: <1-10>
conditions:
  - id: COND-ARCH-01
    description: "..."
    blocking: <true | false>
summary: "..."
---
```
Theo sau là bản phân tích kiến trúc phản biện đa chiều, sắc bén và giàu tính thực tiễn của Grok.
