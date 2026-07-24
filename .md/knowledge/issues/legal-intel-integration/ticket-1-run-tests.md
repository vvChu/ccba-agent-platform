# Ticket 1: Kiểm thử đơn lập suite ccba-legal-intel

- **Loại:** Task [AFK]
- **Trạng thái:** OPEN
- **Bản đồ:** [Wayfinder Map](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/legal-intel-integration/map.md)

## Mô Tả Tác Vụ
Chạy kiểm thử cho package `packages/ccba-legal-intel/tests` trực tiếp từng file test đơn lập thay vì unscoped pytest để đảm bảo không bị dính timeout hoặc server restart interrupt.

## Danh Sách Test Files
- `test_adr.py`
- `test_conflict.py`
- `test_formatter.py`
- `test_intake.py`
- `test_parser_registry.py`
- `test_legal_pipeline_seam.py`

## Completion Criterion
Toàn bộ các test file trên trôi qua 100% không báo lỗi.
