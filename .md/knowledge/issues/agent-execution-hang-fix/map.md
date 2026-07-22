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

---

## Sương mù chiến trận / Chưa xác định rõ (Not yet specified)
- **[Ticket 2: Cập nhật Scoped Execution Guardrail vào AGENTS.md & eval-gate](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/agent-execution-hang-fix/map.md#ticket-2)**  
  Quy định bắt buộc Agent KHÔNG BAO GIỜ chạy lệnh test toàn repo nếu không có target file cụ thể.
- **[Ticket 3: Chuẩn hóa Quy trình Bounded Async Task trong eval-gate & tdd](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/agent-execution-hang-fix/map.md#ticket-3)**  
  Quy định Agent không được vội ngắt lượt khi task ngầm chưa hoàn tất kết quả trả về trong chuỗi suy luận.
- **[Ticket 4: Bổ sung Test Suite Kiểm tra Rào chắn Lệnh (test_agent_execution_guardrails.py)](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/agent-execution-hang-fix/map.md#ticket-4)**  
  Viết unit test xác minh các file quy tắc và validator cấm lệnh unscoped pytest.

---

## Ngoài phạm vi (Out of scope)
- Sửa đổi mã nguồn binary ứng dụng Antigravity IDE (do IDE là môi trường runtime bên ngoài).
