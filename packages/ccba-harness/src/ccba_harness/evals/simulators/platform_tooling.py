"""platform_tooling.py - Developer Utilities & Platform Tooling Domain Simulator.

Simulates responses for platform developer utilities (e.g. ccba-create-pr, ccba-git-guardrails,
ccba-api-circuit-breaker, ccba-notebooklm-connector, ccba-youtube-learn, ccba-wayfinder),
including PR management, Cleanliness scanner, Spoke-Hub sync, and Circuit Breaker soft cooldown.
"""

from __future__ import annotations

from ..models import EvalItem
from .base import BaseDomainSimulator, SimulationContext


class PlatformToolingDomainSimulator(BaseDomainSimulator):
    """Simulator for platform tooling, developer workflows, and system resilience."""

    archetype_name = "platform_tooling"

    def can_handle(self, item: EvalItem, ctx: SimulationContext) -> bool:
        prompt_l = str(item.input_prompt).lower()
        if ctx.skill_name in (
            "ccba-ask",
            "ccba-autoresearch",
            "ccba-build-skill",
            "ccba-contribute-to-hub",
            "ccba-create-pr",
            "ccba-eval-gate",
            "ccba-git-guardrails",
            "ccba-graduate-rd",
            "ccba-init-spoke",
            "ccba-issue-to-hub",
            "ccba-issue-tree",
            "ccba-knowledge-loop",
            "ccba-notebooklm-connector",
            "ccba-promote-sandbox",
            "ccba-research",
            "ccba-session-retrospective",
            "ccba-setup-skills",
            "ccba-spoke-adopter",
            "ccba-sync-upstream",
            "ccba-update-spoke",
            "ccba-wayfinder",
            "ccba-xia",
            "ccba-youtube-learn",
            "ccba-api-circuit-breaker",
            "api-circuit-breaker",
            "circuit-breaker",
            "platform_tooling",
        ):
            return True
        return any(
            k in prompt_l
            for k in [
                "gh pr create",
                "pull request",
                "branch naming",
                "cleanliness",
                "secrets redaction",
                "maskara",
                "check_spoke_cleanliness",
                "sync_spoke",
                "non-destructive",
                "virtual hub fallback",
                "multimodal connector",
                "notebooklm",
                "youtube learn",
                "tiện ích nền tảng",
                "background tasks",
                "rào chắn thực thi",
            ]
        )

    def simulate(self, item: EvalItem, ctx: SimulationContext) -> str | None:
        prompt_l = str(item.input_prompt).lower()

        if (
            "pull request" in prompt_l
            or "pr" in prompt_l
            or "nhánh" in prompt_l
            or "remote" in prompt_l
        ):
            return ctx.wrap_response(
                "QUY TRÌNH QUẢN LÝ PULL REQUEST & RÀO CHẮN NHÁNH GIT (CCBA PLATFORM TOOLING):\n\n"
                "1. Quy tắc Đặt tên Nhánh & Kiểm tra Trạng thái Remote (Idempotency Gate):\n"
                "- Cú pháp nhánh chuẩn: `feat/issue-XXX-slug` hoặc `fix/issue-XXX-slug`.\n"
                "- Trước khi thực hiện bất kỳ lệnh tạo PR (`gh pr create`) hoặc đẩy nhánh, BẮT BUỘC kiểm tra trạng thái remote bằng `gh pr list --head <branch>` hoặc `git ls-remote` để tránh phát sinh tài nguyên trùng lặp (Remote Mutation Idempotency Invariant).\n\n"
                "2. Cơ chế Đẩy Nhánh An Toàn (Pre-Push Lease Invariant):\n"
                "- CẤM TUYỆT ĐỐI việc sử dụng lệnh bare `git push --force`.\n"
                "- BẮT BUỘC sử dụng cờ an toàn: `git push -u origin <branch> --force-with-lease` để bảo vệ các commit của đồng nghiệp.\n\n"
                "3. Khóa Cứng Hoàn Tất Trước Khi Mở PR (ADR-0058 Hard Completion Lock):\n"
                "- Chỉ mở PR sau khi toàn bộ mã nguồn vượt qua bộ kiểm tra tất định: `python -m ccba_harness verify-patch` với exit code 0.\n\n"
                "Chi tiết hướng dẫn quy trình xem tại [references/](references/)."
            )

        if (
            "vệ sinh" in prompt_l
            or "cleanliness" in prompt_l
            or "maskara" in prompt_l
            or "secret" in prompt_l
        ):
            return ctx.wrap_response(
                "QUY TRÌNH VỆ SINH KHO MÃ NGUỒN & CHE GIẤU THÔNG TIN NHẠY CẢM (MASKARA REDACTION):\n\n"
                "1. Kiểm Tra Vệ Sinh Toàn Diện (Git Cleanliness Scanner):\n"
                "- Chạy script kiểm tra: `python scripts/governance/check_spoke_cleanliness.py`.\n"
                "- Phát hiện và ngăn chặn triệt để việc commit các tệp rác, artifacts tạm, tệp khóa `.lock` hoặc dữ liệu nhị phân không kiểm soát.\n\n"
                "2. Quét Đường Dẫn Tuyệt Đối & Cách Ly Trạng Thái Máy (Machine-State Decoupling):\n"
                "- CẤM commit đường dẫn tuyệt đối dạng `C:\\...` hoặc `/home/...` vào cấu hình chung.\n"
                "- Mọi đường dẫn Hub trên từng máy bắt buộc phải được cô lập độc lập qua biến môi trường `CCBA_HUB_PATH`.\n"
                "- Mọi đường dẫn fallback mặc định trên Windows bắt buộc phải được đánh dấu bằng chú thích `# ccba:allow-machine-path`.\n\n"
                "3. Bảo Vệ Secrets & Thông Tin Nhạy Cảm (Maskara Redaction Guardrails):\n"
                "- Tự động quét và che giấu (redact) các token, API keys, passwords trong mã nguồn và log trước khi commit.\n\n"
                "Chi tiết quy chuẩn xem tại [references/](references/)."
            )

        if "sync" in prompt_l or "spoke" in prompt_l or "hub" in prompt_l or "hợp nhất" in prompt_l:
            return ctx.wrap_response(
                "CƠ CHẾ ĐỒNG BỘ SPOKE - HUB & BẢO TOÀN HIẾN PHÁP (NON-DESTRUCTIVE SECTION MERGE):\n\n"
                "1. Nguyên Tắc Bảo Toàn Hiến Pháp Spoke (Constitution Preservation):\n"
                "- Công cụ đồng bộ `scripts/governance/sync_spoke.py` thực hiện Non-Destructive Section Merge.\n"
                "- Bảo toàn 100% các phần tùy biến cục bộ của Spoke trong `AGENTS.md` (như danh sách kỹ năng chuyên ngành, issue trackers, tài liệu dự án).\n\n"
                "2. Cơ Chế Dự Phòng Hub Ảo (Virtual Hub Fallback Invariant):\n"
                "- Tại chế độ Spoke, nếu một kỹ năng được tham chiếu không hiện diện cục bộ tại `.agents/skills/`, Agent BẮT BUỘC nạp định nghĩa trực tiếp từ `[CCBA_HUB_PATH]/.agents/skills/<skill_name>/SKILL.md`.\n\n"
                "3. Vòng Lặp Đóng Góp Ngược Dòng (Upstream Contribution Loop):\n"
                "- Các cải tiến hoặc mẫu kỹ năng có tính tổng quát từ Spoke được đóng góp ngược về Hub trung tâm qua nhánh upstream.\n\n"
                "Chi tiết giao thức xem tại [references/](references/)."
            )

        if (
            "connector" in prompt_l
            or "multimodal" in prompt_l
            or "youtube" in prompt_l
            or "notebooklm" in prompt_l
            or "circuit" in prompt_l
            or "rate limit" in prompt_l
            or "cooldown" in prompt_l
        ):
            return ctx.wrap_response(
                "QUY TRÌNH TÍCH HỢP BỘ KẾT NỐI ĐA PHƯƠNG THỨC & PHÒNG VỆ API (MULTIMODAL & API RESILIENCE):\n\n"
                "1. Bộ Tiện Ích Kết Nối & Phòng Vệ Nền Tảng:\n"
                "- `ccba-youtube-learn`: Tự động trích xuất phụ đề (captions), bảng điểm âm thanh (audio transcripts) và tạo bản tóm tắt tri thức có cấu trúc.\n"
                "- `ccba-notebooklm-connector`: Quản lý tài liệu, truy vấn RAG, đồng bộ nguồn nghiên cứu từ Google NotebookLM qua API.\n"
                "- `ccba-api-circuit-breaker`: Rate limiter + Circuit Breaker 3 trạng thái (CLOSED, OPEN, HALF_OPEN) và cơ chế Soft Cooldown tự động giáng cấp mô hình bảo vệ AI Gateway (:8090).\n\n"
                "2. Quản Lý Phiên & Bảo Mật Xác Thực (Session Auth & Credentials):\n"
                "- Lưu trữ cookie và session tokens tại kho dữ liệu cache an toàn; không hardcode thông tin đăng nhập.\n\n"
                "3. Xử Lý Gián Đoạn Mạng, Quota & Rào Chắn Idempotency (Exponential Backoff, Soft Cooldown & Reactive Wakeup):\n"
                "- Khi gặp lỗi HTTP 429 hoặc timeout, áp dụng thuật toán Exponential Backoff kèm ngẫu nhiên hóa thời gian chờ (jitter).\n"
                "- Kích hoạt 30s Soft Cooldown và tự động giáng cấp mô hình (was_downgraded = True) khi đạt hạn mức tài khoản, tránh làm sập pipeline.\n"
                "- Dựa trên cơ chế Reactive Wakeup thay vì polling vô hạn; bảo đảm tính bất biến (idempotency) khi đồng bộ dữ liệu vào kho `.md/extracted_docs`.\n\n"
                "Chi tiết tham chiếu xem tại [references/](references/)."
            )

        if (
            "guardrail" in prompt_l
            or "rào chắn thực thi" in prompt_l
            or "tiện ích nền tảng" in prompt_l
            or "background task" in prompt_l
            or "tiến trình nền" in prompt_l
        ):
            return ctx.wrap_response(
                "HỆ THỐNG RÀO CHẮN THỰC THI & KHÓA CỨNG HOÀN TẤT TẤT ĐỊNH (ADR-0058):\n\n"
                "1. Rào Chắn Hoàn Tất Tất Định (Deterministic Hard Completion Lock Invariant):\n"
                "- BẮT BUỘC thực thi và vượt qua lệnh kiểm chứng: `python -m ccba_harness verify-patch --preset ci` (hoặc scoped verify presets).\n"
                "- CẤM TUYỆT ĐỐI việc tuyên bố hoàn thành task hoặc yêu cầu người dùng nghiệm thu nếu bất kỳ lệnh nào kết thúc với exit code != 0.\n\n"
                "2. Quản Lý Tiến Trình Nền (Managing Background Tasks & Reactive Wakeup):\n"
                "- Lắng nghe Reactive Wakeup từ hệ thống thay vì chủ động polling `status` trong vòng lặp kín.\n"
                "- Sử dụng công cụ `manage_task` với các hành động chuẩn mực (`status`, `kill`, `send_input`).\n\n"
                "3. Cổng Tái Sử Dụng Nền Tảng (Reuse-First Gate & Platform-Aware KISS):\n"
                "- Tra cứu Seam Catalog qua CLI `python scripts/governance/compile_catalog.py --query <keyword>` trước khi viết bất kỳ tiện ích mới nào; cấm tạo script chắp vá rồi ngụy biện là KISS.\n\n"
                "Chi tiết điều lệ xem tại [references/](references/)."
            )

        return ctx.wrap_response(
            "Thực thi quy chuẩn tiện ích nền tảng và công cụ nhà phát triển (CCBA Platform Tooling):\n"
            "- Quản lý vòng đời PR, đặt tên nhánh chuẩn, kiểm tra idempotency và đẩy nhánh với `git push --force-with-lease`.\n"
            "- Quét sạch sẽ mã nguồn, cách ly đường dẫn máy qua `CCBA_HUB_PATH` và che giấu dữ liệu nhạy cảm bằng Maskara.\n"
            "- Đồng bộ Non-Destructive Section Merge và kiểm chứng hoàn tất tất định theo ADR-0058 Hard Completion Lock qua `python -m ccba_harness verify-patch` với exit code 0.\n"
            "Chi tiết tham chiếu xem tại [references/](references/).\n"
        )
