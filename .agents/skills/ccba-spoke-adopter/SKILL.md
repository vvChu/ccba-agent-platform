---
name: ccba-spoke-adopter
description: Đánh giá hiện trạng và tiếp nhận an toàn các codebase hiện hữu (Brownfield
  Spokes) vào CCBA Platform mà không phá hủy cấu trúc dữ liệu cũ.
argument-hint: '[<spoke_path>] [--dry-run] [--archetype <archetype>] [--type <project_type>]
  [--mode <mode>]'
tier: orchestrator
is-orchestrated: true
user-invocable: true
disable-model-invocation: true
command: /ccba-spoke-adopter
category: management
metadata:
  version: "1.0.0"
  author: "CCBA Hub"
keywords:
- spoke
- adopt
- brownfield
- onboarding
- migration
- schema-merge
- hub-and-spoke
bundle: _core
triggers:
- spoke
- adopt
- brownfield
- onboarding
- migration
- schema-merge
- hub-and-spoke
- adopt spoke
- tiếp nhận dự án
- onboard spoke
- kết nối dự án cũ
- adopt-spoke
---
# Kỹ Năng Tiếp Nhận Spoke Hiện Hữu (Brownfield Spoke Adopter)

Kỹ năng này chịu trách nhiệm đánh giá hiện trạng, phân tích rủi ro và thực hiện tiếp nhận thích ứng (Adaptive Non-Destructive Onboarding) cho các codebase đã có sẵn vào mạng lưới CCBA Agent Platform.

---

## 🏛️ Platform-Aware Architecture Posture (ADR-0061)

Skill này thuộc thế năng **`seam-exempt`** (SOP brownfield tiếp nhận dự án cũ). Skill hướng dẫn quy trình onboarding thích ứng bảo tồn dữ liệu; engine thực thi nằm ở `scripts/spoke/spoke_adopter.py` qua lệnh unified `ccba-platform adopt-spoke <path>` (hoặc script wrapper `scripts/adopt_spoke.py`). Giữ nguyên `tier: orchestrator`.

---

## 1. Nguyên Tắc Cốt Lõi: Bảo Tồn Tuyệt Đối (Zero Data Loss)

1. **Additive Merge (Chỉ thêm, không xóa):** Khi cập nhật `workspace_context.yaml`, giữ nguyên 100% tất cả các trường cấu hình cũ của Spoke (`document_groups`, `custom_milestones`, `databases`, `reading_sequences`).
2. **Tự Động Sao Lưu:** Luôn tạo bản sao lưu `workspace_context.yaml.bak_<timestamp>` trước khi thực hiện hợp nhất.
3. **Bảo Vệ Hiến Pháp Riêng:** Giữ nguyên các tệp `AGENTS.md` và `CLAUDE.md` đã được tùy biến sâu của Spoke, không ghi đè bằng template chung.
4. **Cài Đặt Rào Chắn An Toàn (Maskara):** Tự động cài đặt Git Pre-commit Hook để bảo vệ khóa API và tài khoản bí mật.

---

## 2. Quy Trình Vận Hành 4 Bước

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  1. DISCOVERY   │ ──► │  2. RISK MATRIX  │ ──► │ 3. ADDITIVE MERGE│ ──► │  4. SAFE SYNC    │
│  Quét Stack/Git │     │  Cảnh báo rủi ro │     │ Sao lưu & Hợp nhất│    │ Bơm Kỹ năng & Reg│
└─────────────────┘     └──────────────────┘     └──────────────────┘     └──────────────────┘
```

### Bước 1: Khởi Chạy Đánh Giá Hiện Trạng (Dry-Run Preview)
Chạy lệnh kiểm tra và in ma trận đánh giá 3 tầng (unified CLI nhận tham số vị trí):
```bash
# POSIX (Linux / macOS / WSL) — Chạy từ Spoke:
python "$CCBA_HUB_PATH/scripts/ccba_platform_cli.py" adopt-spoke . --dry-run
```
```powershell
# PowerShell (Windows) — Chạy từ Spoke:
python "$env:CCBA_HUB_PATH\scripts\ccba_platform_cli.py" adopt-spoke . --dry-run
```
*(Hoặc từ Hub: `python scripts/ccba_platform_cli.py adopt-spoke <đường_dẫn_spoke> --dry-run`. Script wrapper cũ `scripts/adopt_spoke.py --spoke <path>` cũng được hỗ trợ).*

**Tiêu chí hoàn thành:** Ma trận đánh giá hiện trạng 3 tầng được in đầy đủ.

### Bước 2: Thực Hiện Tiếp Nhận & Hợp Nhất Cấu Hình
Khi người dùng đồng ý, chạy lệnh tiếp nhận chính thức:
```bash
# POSIX — Chạy từ Spoke:
python "$CCBA_HUB_PATH/scripts/ccba_platform_cli.py" adopt-spoke .
```
```powershell
# PowerShell — Chạy từ Spoke:
python "$env:CCBA_HUB_PATH\scripts\ccba_platform_cli.py" adopt-spoke .
```
*(Hoặc từ Hub: `python scripts/ccba_platform_cli.py adopt-spoke <đường_dẫn_spoke>`)*

**Tiêu chí hoàn thành:** Lệnh tiếp nhận chạy thành công và bảo tồn dữ liệu cũ.

### Bước 3: Tùy Biến Thể Loại, Chế Độ & Archetype (Tùy Chọn)
Nếu muốn chỉ định rõ loại hình dự án, chế độ vận hành hoặc Archetype:
```bash
# POSIX — Chạy từ Spoke:
python "$CCBA_HUB_PATH/scripts/ccba_platform_cli.py" adopt-spoke . --archetype "knowledge_corpus" --type "Pháp điển" --mode "software"
```
```powershell
# PowerShell — Chạy từ Spoke:
python "$env:CCBA_HUB_PATH\scripts\ccba_platform_cli.py" adopt-spoke . --archetype "knowledge_corpus" --type "Pháp điển" --mode "software"
```

---

**Tiêu chí hoàn thành:** Archetype và chế độ dự án được tùy biến chính xác.

---

## 3. Tích Hợp Hệ Thống
* **Deep Seam Engine:** `scripts/spoke/spoke_adopter.py`
* **CLI Command:** Unified `python scripts/ccba_platform_cli.py adopt-spoke <path>` (Wrapper: `scripts/adopt_spoke.py --spoke <path>`)
* **Slash Command:** `/ccba-spoke-adopter`
* **ADR Quy Chuẩn:** [`docs/adr/0036-brownfield-spoke-adoption-and-non-destructive-onboarding.md`](../../../docs/adr/0036-brownfield-spoke-adoption-and-non-destructive-onboarding.md)

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
