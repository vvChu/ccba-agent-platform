# Kế hoạch Kiểm thử Quy trình Tính Năng Mới (The Factory Model)

Mục tiêu của kế hoạch này là thiết lập và kiểm chứng quy trình phát triển tính năng mới (The Factory Model theo `/ccba-new-feature`) trên nhánh `experiment/kiem-tra-tinh-nang-moi`, xác nhận tính sẵn sàng của các cổng kiểm soát chất lượng tự động và tuân thủ tuyệt đối các invariants kiến trúc của CCBA Platform (ADR-0047, ADR-0057, ADR-0058).

## Đánh giá khả năng tái sử dụng (Reuse Assessment - ADR 0047)

Tra cứu `catalog.yaml` và các Deep Seams hiện có trên Hub:
- **Harness Verification Engine (ADR-0058)**: Tái sử dụng `python -m ccba_harness verify-patch --preset ci` để thực hiện Hard Completion Lock tất định cho toàn bộ hệ thống quản trị nền tảng (linter, format, telemetry, skill validation, catalog sync, adr matrix).
- **Linter & Code Formatter**: Tái sử dụng `python -m ruff check packages/ scripts/ tests/` và `python -m ruff format --check packages/ scripts/ tests/` cho toàn monorepo (đã qua kiểm chứng 701 files PASS).
- **Safe Test Runner**: Tái sử dụng `python -X utf8 scripts/safe_pytest.py -F --allow-unscoped` nếu cần chạy nhanh bộ unit tests logic.
- **Quyết định**: 100% tái sử dụng hạ tầng có sẵn trên Hub. Không chỉnh sửa tệp không tồn tại (`tests/conftest.py`) và không viết thêm scripts kiểm tra thừa thãi.

## CCBA Charter Governance & QC Matrix (ADR-0058)

- **Môi trường:** Hub Monorepo (`ccba-agent-platform`)
- **QC Level áp dụng:** Level 2 (Technical & Architecture Parity)
- **Ghế chịu trách nhiệm phê duyệt:** `TRUONG_PHONG_RD_HTQT` (hoặc Lead Architect)
- **Tiêu chuẩn nghiệm thu:** 
  1. 100% các lệnh trong `Verification Plan` trả về Exit Code 0.
  2. Báo cáo bàn giao `walkthrough.md` nhúng nguyên văn bảng kết quả thực thi từ `verify-patch`.
  3. Snapshot lưu trữ vĩnh viễn vào `.md/knowledge/reports/` trước khi đóng phiên.

## User Review Required

> [!IMPORTANT]
> Đây là phiên kiểm chứng quy trình The Factory Model (dry-run của `/ccba-new-feature`). Vì người dùng chưa cung cấp mã Issue nghiệp vụ cụ thể, phiên này tập trung xác thực tính sẵn sàng của toàn bộ Quality Gates môi trường. 
> 
> Nếu người dùng muốn triển khai một tính năng cụ thể trên nhánh này, vui lòng phản hồi mô tả tính năng để kích hoạt Bước 6 (Socrates Grilling) trước khi viết mã.

## Proposed Changes

Không sửa đổi mã nguồn nghiệp vụ. Giữ nguyên working tree sạch sẽ (`working tree clean`).

## Verification Plan

### 1. Automated Tests (Hard Completion Lock)
Thực thi kiểm định tất định chuẩn hóa hệ thống qua công cụ `ccba-harness`:
```bash
python -m ccba_harness verify-patch --preset ci
```
*(Bao gồm: ruff check, ruff format check, pytest telemetry/verify-patch, validate_skills --enforce-gpi, compile_catalog --check, và sync_hub_adr_matrix --check. Thời lượng thực tế: ~90 giây).*

Kiểm tra định dạng và linter toàn diện monorepo:
```bash
python -m ruff check packages/ scripts/ tests/
python -m ruff format --check packages/ scripts/ tests/
```

### 2. Manual Verification
- Xác nhận trạng thái Git working tree sạch sẽ (`git status --short`).
- Lập báo cáo bàn giao nghiệm thu `walkthrough.md`.
- Đồng bộ snapshot của artifacts từ thư mục đệm `<appDataDir>\brain\` vào thư mục `.md/knowledge/reports/2026-09-kiem-tra-tinh-nang-moi/` theo quy định ADR-0058.

## Factory Model Hand-off & Routing (Step 7)
- Sau khi User bấm **Proceed** phê duyệt kế hoạch:
  - Trường hợp A (Chỉ nghiệm thu quy trình): Thực thi ngay Bước 8 để chạy `verify-patch --preset ci` và xuất `walkthrough.md`.
  - Trường hợp B (Bổ sung tính năng nghiệp vụ): Định tuyến sang session mới qua `🟢 Standard (/ccba-implement)` hoặc `🟣 Deep Reasoning (/boost)` tùy độ phức tạp của module.
