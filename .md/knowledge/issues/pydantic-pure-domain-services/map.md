# Wayfinder Map: Refactor Dứt Điểm `ccba_ai.services` Sang Pydantic v2 Thuần Túy

> **Feature**: `pydantic-pure-domain-services`  
> **Khởi tạo**: 2026-08-14  
> **Trạng thái**: In Progress  
> **Assignee**: Antigravity Agent  

---

## 🎯 1. Điểm Đích (Destination) — [ĐẠT ĐƯỢC / REACHED]

Toàn bộ các domain services trong [`ccba_ai.services`](../../../../packages/ccba-ai/src/ccba_ai/services) (`seo.py`, `team.py`, `plan.py`) đã được chuyển đổi dứt điểm sang **Pydantic v2 `BaseModel` DTOs thuần túy** (không dùng các lớp bọc lai tạp `DictLikeModel`). Tất cả callers, CLI wrappers, và test suites đã được tái cấu trúc triệt để theo truy cập thuộc tính tường minh (`res.score`, `task.name`), bảo đảm type safety tuyệt đối và pass 100% test suite toàn repo (`605/605`).

---

## 📝 2. Ghi Chú (Notes)

- **Quy chuẩn Pydantic v2**: Sử dụng `model.model_dump()` và `model.model_dump_json()` thay vì `dict()` kiểu cũ.
- **2-Tier Test Discipline**: Mọi test file mới/sửa đổi phải chạy dưới 2.0 giây.
- **Zero Breaking Calls trong Hub/Spoke**: Toàn bộ public API được xuất bản trực tiếp tại `ccba_ai.models` và `ccba_ai.services`.

---

## 🏛️ 3. Quyết Định Đã Chốt (Decisions So Far)

1. **[Quyết định #1 — Loại bỏ DictLikeModel Hybrid](map.md)**: Không tạo class bọc giả lập dictionary để tránh anti-pattern "nửa nạc nửa mỡ". Thay vào đó, refactor dứt điểm toàn bộ callers.
2. **[Quyết định #2 — Đồng bộ Chuẩn Pydantic v2](map.md)**: Đặt các DTOs mới (`SEOAuditResult`, `TeamTask`, `PlanCreationResult`, `PhaseUpdateResult`, `PlanStatusResult`) trong `packages/ccba-ai/src/ccba_ai/models.py` bên cạnh `ChatResult` và `AuditReport`.
3. **[Quyết định #3 — Ghi nhận ADR-014](../../CONTEXT.md)**: Lưu trữ quyết định kiến trúc chính thức vào Sổ bộ Quyết định ADRs của Platform.

---

## 🗺️ 4. Bản Đồ Công Việc & Danh Sách Ticket (Work Breakdown)

| Ticket | Tiêu Đề | Loại | Phụ Thuộc | Trạng Thái |
| :--- | :--- | :---: | :---: | :---: |
| **[Ticket #1](ticket-01-models-definition.md)** | Định nghĩa Pydantic v2 DTOs trong `models.py` & Export | Task [AFK] | None | `CLOSED` ✅ |
| **[Ticket #2](ticket-02-seo-service-refactor.md)** | Refactor `seo.py`, CLI `seo_audit.py`, và `test_seo.py` | Task [AFK] | Ticket #1 | `CLOSED` ✅ |
| **[Ticket #3](ticket-03-team-service-refactor.md)** | Refactor `team.py`, File Mutex Lock & JSON Persistence | Task [AFK] | Ticket #1 | `CLOSED` ✅ |
| **[Ticket #4](ticket-04-plan-service-refactor.md)** | Refactor `plan.py` DTOs & `test_plan_manager.py` | Task [AFK] | Ticket #1 | `CLOSED` ✅ |
| **[Ticket #5](ticket-05-end-to-end-validation.md)** | Kiểm định Toàn Trình, Governance Gate & ADR-014 | Task [AFK] | Ticket #2, #3, #4 | `CLOSED` ✅ |

---

## 🌫️ 5. Chưa Xác Định Rõ (Not Yet Specified)
*(Trống — Toàn bộ lộ trình đã được làm rõ nét 100%).*

---

## 🚫 6. Ngoài Phạm Vi (Out of Scope)
- Không sửa đổi core AI Gateway transport (`client.py`, `async_client.py`, `routing.py`).
- Không can thiệp vào các package khác ngoài `packages/ccba-ai` và CLI wrapper tương ứng.
