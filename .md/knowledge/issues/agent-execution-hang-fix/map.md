# Wayfinder Map: Khắc phục Triệt để Sự cố Agent Execution Hang & Unscoped Background Task

## Điểm đích (Destination)
Loại bỏ hoàn toàn rủi ro Agent bị treo/đợi ngầm (Execution Hang) do chạy lệnh kiểm thử không khoanh vùng (unscoped commands) hoặc vội vàng ngắt lượt khi background task đang diễn ra. Thiết lập hệ thống rào chắn (Guardrails) và quy chuẩn xử lý tác vụ ngầm có thời hạn (Bounded Async Task Management) trên toàn bộ CCBA Platform.

---

## Ghi chú (Notes)
- Tuân thủ Hiến pháp CCBA Layer 1 (`.agents/AGENTS.md`).
- Áp dụng nguyên tắc Reuse-First Gate (đánh giá khả năng tái sử dụng Hub/Spoke).
- Mọi thay đổi mã nguồn/quy tắc phải được người dùng phê duyệt qua `implementation_plan.md`.

---

## Quyết định đã chốt (Decisions so far)
- **[Ticket 1: Phân tích Nguyên nhân Gốc rễ Agent Execution Hang](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/agent-execution-hang-fix/map.md#ticket-1)** — *Đã hoàn thành*  
  Xác định 3 nguyên nhân cốt lõi: (1) Chạy `pytest -q` toàn diện không khoanh vùng target file, (2) Tự động đẩy task ngầm rồi vội vã End Turn nhường lượt, (3) Mất đồng bộ state làm orphaned gRPC channel.
- **[Ticket 2: Cập nhật Scoped Execution Guardrail vào AGENTS.md & eval-gate](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/agent-execution-hang-fix/map.md#ticket-2)** — *Đã hoàn thành*  
  Đã bổ sung mục 4 vào `.agents/AGENTS.md` bắt buộc khoanh vùng file/folder khi chạy test.
- **[Ticket 3: Chuẩn hóa Quy trình Bounded Async Task trong eval-gate & tdd](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/agent-execution-hang-fix/map.md#ticket-3)** — *Đã hoàn thành*  
  Đã quy định cấm Agent ngắt lượt khi background task chưa thu thập xong kết quả log.
- **[Ticket 4: Bổ sung Test Suite Kiểm tra Rào chắn Lệnh (test_agent_execution_guardrails.py)](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/agent-execution-hang-fix/map.md#ticket-4)** — *Đã hoàn thành*  
  Đã thêm bộ unit test `tests/test_agent_execution_guardrails.py` kiểm định thành công (2 passed in 0.06s).

---

## Sương mù chiến trận / Chưa xác định rõ (Not yet specified)
- *Tất cả các ticket trong lộ trình Wayfinder đã được giải quyết hoàn tất 100%.*

---

## Ngoài phạm vi (Out of scope)
- Sửa đổi mã nguồn binary ứng dụng Antigravity IDE (do IDE là môi trường runtime bên ngoài).
