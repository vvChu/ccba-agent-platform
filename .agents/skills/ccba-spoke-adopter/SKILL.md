---
name: ccba-spoke-adopter
description: Đánh giá hiện trạng và tiếp nhận an toàn các codebase hiện hữu (Brownfield
  Spokes) vào CCBA Platform mà không phá hủy cấu trúc dữ liệu cũ.
argument-hint: '[--spoke <path>] [--dry-run] [--archetype <archetype>] [--type <project_type>]
  [--mode <mode>]'
tier: orchestrator
is-orchestrated: true
user-invocable: true
disable-model-invocation: true
command: /ccba-spoke-adopter
category: management
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
Chạy lệnh kiểm tra và in ma trận đánh giá 3 tầng:
```powershell
# Chạy từ Hub:
python scripts/adopt_spoke.py --spoke [đường_dẫn_spoke] --dry-run
# Hoặc chạy trực tiếp tại Spoke:
python "[hub_path]\scripts\adopt_spoke.py" --spoke . --dry-run
```

**Tiêu chí hoàn thành:** Ma trận đánh giá hiện trạng 3 tầng được in đầy đủ.

### Bước 2: Thực Hiện Tiếp Nhận & Hợp Nhất Cấu Hình
Khi người dùng đồng ý, chạy lệnh tiếp nhận chính thức:
```powershell
# Chạy từ Hub:
python scripts/adopt_spoke.py --spoke [đường_dẫn_spoke]
# Hoặc chạy trực tiếp tại Spoke:
python "[hub_path]\scripts\adopt_spoke.py" --spoke .
```

**Tiêu chí hoàn thành:** Lệnh tiếp nhận chạy thành công và bảo tồn dữ liệu cũ.

### Bước 3: Tùy Biến Thể Loại, Chế Độ & Archetype (Tùy Chọn)
Nếu muốn chỉ định rõ loại hình dự án, chế độ vận hành hoặc Archetype:
```powershell
# Chạy từ Hub:
python scripts/adopt_spoke.py --spoke [đường_dẫn_spoke] --archetype "knowledge_corpus" --type "Pháp điển" --mode "software"
# Hoặc chạy trực tiếp tại Spoke:
python "[hub_path]\scripts\adopt_spoke.py" --spoke . --archetype "knowledge_corpus" --type "Pháp điển" --mode "software"
```

---

**Tiêu chí hoàn thành:** Archetype và chế độ dự án được tùy biến chính xác.

---

## 3. Tích Hợp Hệ Thống
* **Deep Seam Engine:** `scripts/spoke/spoke_adopter.py`
* **CLI Command:** `python scripts/adopt_spoke.py`
* **Slash Command:** `/ccba-spoke-adopter`
* **ADR Quy Chuẩn:** [`docs/adr/0036-brownfield-spoke-adoption-and-non-destructive-onboarding.md`](../../../docs/adr/0036-brownfield-spoke-adoption-and-non-destructive-onboarding.md)

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
