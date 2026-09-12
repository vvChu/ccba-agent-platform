#!/usr/bin/env python3
"""compile_skills_docs.py - CCBA Skills Documentation & Static Portal Compiler (ADR-0058).

Pure Python, zero-dependency compiler that generates:
1. Standardized 5-section Markdown documentation for each skill (docs/skills/<name>.md)
2. Central Markdown index (docs/skills/INDEX.md)
3. Open standard agent endpoint summaries (docs/llms.txt, docs/llms-full.txt)
4. Offline-first, responsive single-page web portal (docs/index.html)

Supports:
- `--write` (default): Compiles and writes all documentation files to disk.
- `--check`: CI gate checking if docs are 100% in sync with .agents/skills/ and portals.yaml.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = HUB_ROOT / ".agents" / "skills"
DOCS_DIR = HUB_ROOT / "docs"
DOCS_SKILLS_DIR = DOCS_DIR / "skills"
PORTALS_YAML_PATH = DOCS_SKILLS_DIR / "portals.yaml"
INDEX_MD_PATH = DOCS_SKILLS_DIR / "INDEX.md"
FAQ_MD_PATH = DOCS_SKILLS_DIR / "FAQ.md"
LLMS_TXT_PATH = DOCS_DIR / "llms.txt"
LLMS_FULL_TXT_PATH = DOCS_DIR / "llms-full.txt"
INDEX_HTML_PATH = DOCS_DIR / "index.html"


# ---------------------------------------------------------------------------
# Pipeline Trail Taxonomy & Flow Relationships
# ---------------------------------------------------------------------------

PIPELINE_MAP: dict[str, dict[str, str]] = {
    # 1. init_navigation (8 skills)
    "platform-loader": {
        "upstream": "Khởi động IDE / Mở phiên làm việc mới",
        "downstream": "ccba-ask / Kỹ năng nghiệp vụ cụ thể",
        "role": "Cửa ngõ nạp danh mục Service Catalog và thiết lập bối cảnh ban đầu.",
    },
    "ccba-ask": {
        "upstream": "Yêu cầu thô từ người dùng / Chưa rõ hướng đi",
        "downstream": "ccba-grilling / ccba-to-spec / Kỹ năng chuyên biệt",
        "role": "Bản đồ tư vấn định hướng lựa chọn Slash Command phù hợp nhất.",
    },
    "ccba-init-spoke": {
        "upstream": "Thành lập dự án mới từ Hub",
        "downstream": "ccba-setup-skills / ccba-update-spoke",
        "role": "Khởi tạo cấu trúc phân vùng Spoke chuẩn mực theo Archetype.",
    },
    "ccba-spoke-adopter": {
        "upstream": "Dự án có sẵn cần tích hợp CCBA Platform",
        "downstream": "ccba-setup-skills / ccba-git-guardrails",
        "role": "Nhận diện cấu hình và chuyển đổi dự án hiện hữu thành Spoke.",
    },
    "ccba-update-spoke": {
        "upstream": "Hub phát hành cập nhật mới",
        "downstream": "Kỹ năng nghiệp vụ cục bộ tại Spoke",
        "role": "Đồng bộ một chiều các kỹ năng và quy tắc từ Hub về Spoke.",
    },
    "ccba-setup-skills": {
        "upstream": "Khởi tạo hoặc cấu hình lại Spoke",
        "downstream": "Toàn bộ quy trình tác nghiệp",
        "role": "Cài đặt hàng loạt kỹ năng tương ứng với Archetype của Spoke.",
    },
    "ccba-handoff": {
        "upstream": "Kết thúc phiên làm việc / Sắp cạn Context Budget",
        "downstream": "Phiên làm việc sạch tiếp theo của Agent",
        "role": "Đóng gói bối cảnh, bài học kinh nghiệm và bàn giao phiên sạch sẽ.",
    },
    "ccba-wayfinder": {
        "upstream": "Dự án lớn, cấu trúc phức tạp nhiều tầng",
        "downstream": "Kỹ năng lập trình hoặc thẩm tra",
        "role": "Định vị nhanh các Deep Seams và tệp mã nguồn liên quan.",
    },

    # 2. core_engineering (18 skills)
    "ccba-grilling": {
        "upstream": "Ý tưởng sơ khai / Yêu cầu người dùng (Idea Phase)",
        "downstream": "ccba-to-spec / ccba-adr-lifecycle",
        "role": "Phỏng vấn phản biện sâu để làm rõ các giả định và góc khuất kỹ thuật.",
    },
    "ccba-to-spec": {
        "upstream": "ccba-grilling / CONTEXT.md",
        "downstream": "ccba-implement / ccba-tdd",
        "role": "Biến ý tưởng thành Đặc tả Kỹ thuật và bẻ ticket lát cắt dọc.",
    },
    "ccba-implement": {
        "upstream": "ccba-to-spec / Bản đặc tả & danh sách ticket",
        "downstream": "ccba-code-review / ccba-ai-qc / ccba-session-retrospective",
        "role": "Hiện thực hóa mã nguồn tối thiểu theo triết lý KISS và Deep Seam.",
    },
    "ccba-tdd": {
        "upstream": "ccba-to-spec / Ticket cần độ tin cậy cao",
        "downstream": "ccba-implement / ccba-code-review",
        "role": "Quy trình phát triển dẫn dắt bởi kiểm thử (Red - Green - Refactor).",
    },
    "ccba-teamwork": {
        "upstream": "Tác vụ quy mô lớn cần phân rã nhiều Agent",
        "downstream": "Các worker subagents độc lập",
        "role": "Điều phối Swarm đa tác nhân, giám sát tiến độ và tổng hợp kết quả.",
    },
    "ccba-code-review": {
        "upstream": "ccba-implement / PR chuẩn bị merge",
        "downstream": "Sửa lỗi / ccba-release-feature",
        "role": "Đánh giá phản biện mã nguồn, rà soát lỗ hổng và tuân thủ chuẩn mực.",
    },
    "ccba-codebase-design": {
        "upstream": "Phát hiện mã nguồn nông (Shallow Modules) / Cần tái cấu trúc",
        "downstream": "ccba-implement / ccba-to-spec",
        "role": "Thiết kế kiến trúc sâu, đóng gói module và củng cố Deep Seams.",
    },
    "ccba-diagnosing-bugs": {
        "upstream": "Lỗi phần mềm / CI Gate thất bại / Báo cáo bug",
        "downstream": "Viết test hồi quy -> ccba-implement vá lỗi",
        "role": "Điều tra nguyên nhân gốc rễ và khóa lỗi bằng kiểm thử tự động.",
    },
    "ccba-web-testing": {
        "upstream": "Giao diện web / REST API đã hoàn thiện",
        "downstream": "ccba-code-review / Báo cáo nghiệm thu",
        "role": "Kiểm thử tự động giao diện End-to-End và kiểm chứng hành vi người dùng.",
    },
    "ccba-design": {
        "upstream": "Yêu cầu giao diện hoặc trải nghiệm người dùng mới",
        "downstream": "ccba-to-spec / ccba-implement",
        "role": "Thiết kế kiến trúc hệ thống và giao diện người dùng mạch lạc.",
    },
    "ccba-domain-modeling": {
        "upstream": "Bắt đầu bài toán nghiệp vụ phức tạp",
        "downstream": "ccba-to-spec / Thiết kế Schema CSDL",
        "role": "Xây dựng mô hình miền và ngôn ngữ chung (Ubiquitous Language).",
    },
    "ccba-excalidraw-diagram": {
        "upstream": "Kiến trúc hệ thống hoặc quy trình cần trực quan hóa",
        "downstream": "Tài liệu kỹ thuật / Trình bày phương án",
        "role": "Sinh sơ đồ kiến trúc Excalidraw trực quan từ văn bản mô tả.",
    },
    "ccba-new-feature": {
        "upstream": "Kế hoạch bổ sung tính năng mới",
        "downstream": "ccba-implement / ccba-tdd",
        "role": "Scaffolding khung tính năng mới dọc theo toàn bộ các tầng mã nguồn.",
    },
    "ccba-release-feature": {
        "upstream": "Tính năng đã vượt qua toàn bộ CI Gates",
        "downstream": "Bàn giao / Đóng gói phiên bản",
        "role": "Đóng gói, gắn tag phiên bản và xuất bản bản phát hành.",
    },
    "ccba-session-retrospective": {
        "upstream": "Hoàn tất một chu kỳ phát triển hoặc phiên làm việc",
        "downstream": "session_learnings.md / ccba-handoff",
        "role": "Đúc rút bài học kinh nghiệm, rà soát hiệu suất và cải tiến quy trình.",
    },
    "ccba-git-guardrails": {
        "upstream": "Chuẩn bị commit hoặc tạo nhánh mới",
        "downstream": "Git push / Pull Request",
        "role": "Bảo vệ lịch sử Git, định dạng commit và ngăn ngừa xung đột nhánh.",
    },
    "ccba-api-circuit-breaker": {
        "upstream": "Tác vụ gọi LLM hoặc API bên ngoài quy mô lớn",
        "downstream": "Pipeline xử lý dữ liệu hàng loạt",
        "role": "Kiểm soát tốc độ gọi API, ngắt mạch khi lỗi và tránh cạn kiệt hạn mức.",
    },
    "ccba-append-only-logger": {
        "upstream": "Hệ thống đa tiến trình / Daemons chạy song song",
        "downstream": "Phân tích nhật ký / Giám sát lỗi",
        "role": "Ghi log an toàn luồng (Thread-safe), chống hỏng mã hóa và race condition.",
    },

    # 3. bim_aiqc (7 skills)
    "bigbim-classification": {
        "upstream": "Mô hình BIM sơ bộ / Hồ sơ thiết kế",
        "downstream": "bigbim-rase / bigbim-risk",
        "role": "Tự động phân loại vật tư Uniclass và chuẩn hóa định danh thực thể ISO.",
    },
    "bigbim-governance": {
        "upstream": "Khởi động dự án BIM từ giai đoạn A0",
        "downstream": "Phối hợp mô hình / Kiểm tra chất lượng",
        "role": "Cưỡng chế Hiến pháp Sợi Chỉ Vàng và rào chắn Sợi Chỉ Đỏ cho thông tin BIM.",
    },
    "bigbim-rase": {
        "upstream": "bigbim-classification / Tiêu chuẩn kỹ thuật",
        "downstream": "bigbim-risk / ccba-ai-qc",
        "role": "Phân tích quy tắc RASE và gắn kết tập thuộc tính IFC (Qto_xxx).",
    },
    "bigbim-risk": {
        "upstream": "bigbim-rase / Mô hình phối hợp V2",
        "downstream": "ccba-ai-qc / Báo cáo xung đột thông tin",
        "role": "Phát hiện xung đột thông tin phi hình học vượt ngoài va chạm vật lý.",
    },
    "bigbim-vbpl-digest": {
        "upstream": "Yêu cầu tra cứu quy chuẩn BIM Việt Nam",
        "downstream": "Tư vấn thiết kế / Thẩm tra tuân thủ",
        "role": "Tóm lược các nghị định, thông tư và tiêu chuẩn ISO 19650 cho BIM.",
    },
    "ccba-ai-qc": {
        "upstream": "Mô hình thiết kế đa bộ môn (Kiến trúc, Kết cấu, MEP)",
        "downstream": "Heat Map Report / Nghiệm thu thiết kế",
        "role": "Master Orchestrator thẩm tra chất lượng thiết kế qua Deep Seam QCAuditPipeline.",
    },
    "ccba-ai-qc-pccc-audit": {
        "upstream": "Hồ sơ thiết kế PCCC / Bản vẽ mặt bằng",
        "downstream": "ccba-ai-qc / Báo cáo thẩm tra PCCC",
        "role": "Thẩm tra lỗi thiết kế PCCC theo cơ chế Semantic Map-Reduce và QCVN 06.",
    },

    # 4. legal_compliance (10 skills)
    "ccba-legal-advisor": {
        "upstream": "Tình huống pháp lý xây dựng cần làm rõ",
        "downstream": "Phiếu Ý kiến Pháp lý (Legal Opinion)",
        "role": "Phỏng vấn làm rõ ngữ cảnh và tư vấn pháp lý xây dựng trích dẫn OKF v2.4.",
    },
    "ccba-legal-intel": {
        "upstream": "Văn bản quy phạm pháp luật mới ban hành",
        "downstream": "ccba-completion-checklist / Bảng kiểm tra",
        "role": "Tự động thu thập, phân tích khác biệt (diff) và tạo compliance checklist.",
    },
    "ccba-legal-document-tracker": {
        "upstream": "Cơ sở dữ liệu văn bản pháp quy",
        "downstream": "ccba-legal-advisor / Cập nhật hiệu lực",
        "role": "Theo dõi hiệu lực, so sánh văn bản sửa đổi bổ sung với VBHNEngine.",
    },
    "ccba-legal-ingest": {
        "upstream": "Tệp văn bản pháp lý thô (PDF/Docx/HTML)",
        "downstream": "Registry pháp lý OKF v2.4",
        "role": "Tiếp nhận, chuẩn hóa cấu trúc AST và thẩm định qua 15 Cổng CI.",
    },
    "ccba-tvpl-vip-crawler": {
        "upstream": "Liên kết Thư Viện Pháp Luật",
        "downstream": "ccba-legal-ingest",
        "role": "Thu thập nội dung số hóa bản quyền từ hệ thống TVPL VIP.",
    },
    "ccba-completion-checklist": {
        "upstream": "Giai đoạn kết thúc thi công / Nghiệm thu bàn giao",
        "downstream": "Hồ sơ hoàn thành công trình (Word/Markdown)",
        "role": "Lập và duy trì Danh mục Hồ sơ Hoàn thành Công trình theo luật hiện hành.",
    },
    "ccba-xu-ly-van-phong": {
        "upstream": "Tài liệu văn phòng, công văn, biên bản họp",
        "downstream": "Văn bản định dạng chuẩn công vụ",
        "role": "Tự động hóa xử lý văn thư và biểu mẫu hành chính xây dựng.",
    },
    "ccba-markdown-document-processing": {
        "upstream": "Tài liệu Word (.docx) hoặc PDF kỹ thuật",
        "downstream": "Markdown chuẩn hóa / Knowledge Base",
        "role": "Chuyển đổi và chuẩn hóa tài liệu phức tạp sang Markdown chất lượng cao.",
    },
    "ccba-pptx": {
        "upstream": "Nội dung thuyết trình / Đề cương báo cáo",
        "downstream": "File trình chiếu PowerPoint (.pptx)",
        "role": "Tạo slide thuyết trình kỹ thuật chuyên nghiệp, tự động căn chỉnh bố cục.",
    },
    "ccba-copywriting": {
        "upstream": "Ý tưởng truyền thông / Thông báo kỹ thuật",
        "downstream": "Bài viết hoàn thiện chuẩn văn phong",
        "role": "Biên tập bài viết kỹ thuật và tài liệu truyền thông chuẩn văn phong CCBA.",
    },

    # 5. governance_upkeep (25 skills)
    "ccba-adr-lifecycle": {
        "upstream": "Quyết định kiến trúc quan trọng nảy sinh",
        "downstream": "Bản ghi ADR mới / Living Traceability Matrix",
        "role": "Quản trị vòng đời quyết định kiến trúc: Scaffolding, Cascading và Matrix.",
    },
    "ccba-eval-gate": {
        "upstream": "Kỹ năng mới hoặc sửa đổi cần thẩm định",
        "downstream": "Đạt chuẩn xuất xưởng lên Hub",
        "role": "Chấm điểm GPI, đánh giá cổng CI và cưỡng chế chuẩn mực chất lượng kỹ năng.",
    },
    "ccba-maskara": {
        "upstream": "Trước khi commit, tạo log hoặc chia sẻ file",
        "downstream": "Mã nguồn sạch, an toàn bảo mật",
        "role": "Phát hiện và che giấu (redact) thông tin nhạy cảm (API Keys, Passwords).",
    },
    "ccba-platform": {
        "upstream": "Quản trị hệ thống Hub & Spoke toàn cục",
        "downstream": "Hạ tầng platform ổn định",
        "role": "Điểm tựa vận hành và bảo trì cấu trúc nền tảng CCBA Platform.",
    },
    "ccba-build-skill": {
        "upstream": "Nhu cầu đóng gói quy trình mới thành kỹ năng",
        "downstream": "ccba-eval-gate / SKILL.md chuẩn",
        "role": "Tạo khung kỹ năng mới tuân thủ Khung Quyết Định Hai Giai Đoạn (ADR-0057).",
    },
    "ccba-skill-repair": {
        "upstream": "Kỹ năng bị lỗi lint, trôi dạt metadata hoặc CI fail",
        "downstream": "Kỹ năng được phục hồi, vượt qua CI",
        "role": "Tự động chẩn đoán và sửa chữa nhanh các lỗi cấu trúc trong SKILL.md.",
    },
    "ccba-autoresearch": {
        "upstream": "Chủ đề nghiên cứu khoa học / Kỹ thuật mới",
        "downstream": "Báo cáo nghiên cứu đa chiều",
        "role": "Quy trình nghiên cứu 2 vòng: Code-First Research và Self-Adversarial Review.",
    },
    "ccba-graduate-rd": {
        "upstream": "Thử nghiệm thành công trong sandbox",
        "downstream": "Gói monorepo chính thức trong packages/",
        "role": "Tốt nghiệp các dự án nghiên cứu và chuyển đổi thành thư viện sản phẩm.",
    },
    "ccba-knowledge-loop": {
        "upstream": "Phiên làm việc phát sinh giải pháp hay lỗi hiếm",
        "downstream": ".md/knowledge/session_learnings.md",
        "role": "Đúc kết tri thức định kỳ và tối ưu hóa cẩm nang học tập của Agent.",
    },
    "ccba-ai-gateway-sdk": {
        "upstream": "Nhu cầu gọi mô hình AI từ mã Python",
        "downstream": "Kết quả suy luận từ AI Gateway",
        "role": "Giao diện lập trình chuẩn kết nối AI Gateway đa mô hình trên Server Spark.",
    },
    "ccba-ai-pdf-preprocessor": {
        "upstream": "Tệp PDF bản vẽ hoặc hồ sơ dung lượng lớn",
        "downstream": "Ảnh tiled và văn bản phân đoạn cho LLM",
        "role": "Tối ưu hóa tài liệu PDF cho thị giác máy tính và trích xuất ngữ cảnh.",
    },
    "ccba-hybrid-rag-search": {
        "upstream": "Truy vấn tìm kiếm tri thức dự án",
        "downstream": "Danh sách đoạn văn bản phù hợp nhất",
        "role": "Tìm kiếm kết hợp BM25 + Vector Embedding và xếp hạng lại bằng RRF Fusion.",
    },
    "ccba-llm-pipeline-patterns": {
        "upstream": "Thiết kế hệ thống xử lý ngôn ngữ quy mô lớn",
        "downstream": "Kiến trúc pipeline bền vững, tối ưu chi phí",
        "role": "Cẩm nang quy chuẩn thiết kế và phòng tránh lỗi cho LLM Pipelines.",
    },
    "ccba-file-stability-guard": {
        "upstream": "Xử lý file đồng bộ từ đám mây (OneDrive/GDrive)",
        "downstream": "Pipeline xử lý file an toàn",
        "role": "Kiểm tra kích thước thực tế đảm bảo file đã tải xong hoàn toàn.",
    },
    "ccba-notebooklm-connector": {
        "upstream": "Nguồn tài liệu video, PDF, URL hoặc Drive",
        "downstream": "Hỏi đáp RAG / Audio Overview",
        "role": "Tương tác với Google NotebookLM để nạp nguồn tri thức và tạo podcast âm thanh.",
    },
    "ccba-academic-writing": {
        "upstream": "Kết quả nghiên cứu thực nghiệm",
        "downstream": "Bài báo khoa học định dạng chuẩn",
        "role": "Hỗ trợ viết bài báo nghiên cứu khoa học chuẩn cấu trúc học thuật quốc tế.",
    },
    "ccba-research": {
        "upstream": "Vấn đề kỹ thuật cần nghiên cứu chuyên sâu",
        "downstream": "Tài liệu nghiên cứu kỹ thuật",
        "role": "Thực hiện khảo sát công nghệ, phân tích ưu nhược điểm và đề xuất giải pháp.",
    },
    "ccba-seminar-builder": {
        "upstream": "Nội dung đào tạo hoặc chia sẻ nội bộ CCBA",
        "downstream": "Bộ tài liệu seminar trong .md/teach/",
        "role": "Chuẩn bị đề cương, recap và lưu trữ tài liệu các buổi hội thảo nội bộ.",
    },
    "ccba-youtube-learn": {
        "upstream": "Video YouTube bài giảng / Hội thảo công nghệ",
        "downstream": "Bản tóm tắt tri thức cốt lõi",
        "role": "Trích xuất phụ đề, phân tích nội dung và tổng hợp tri thức từ video.",
    },
    "ccba-contribute-to-hub": {
        "upstream": "Cải tiến hoặc kỹ năng mới phát triển tại Spoke",
        "downstream": "Pull Request đóng góp ngược về Hub",
        "role": "Quy trình đóng gói và gửi đóng góp từ dự án vệ tinh về kho trung tâm Hub.",
    },
    "ccba-issue-to-hub": {
        "upstream": "Sự cố hoặc yêu cầu phát sinh từ Spoke",
        "downstream": "GitHub Issue đã được phân loại trên Hub",
        "role": "Tiếp nhận, lọc trùng lặp và chuyển giao vấn đề lên Hub để xử lý.",
    },
    "ccba-promote-sandbox": {
        "upstream": "Thử nghiệm thành công trong thư mục sandbox",
        "downstream": "Mã nguồn chính thức của hệ thống",
        "role": "Nâng cấp mã nguồn thử nghiệm thành thành phần chính thức của nền tảng.",
    },
    "ccba-sharepoint-iac": {
        "upstream": "Cấu trúc lưu trữ tài liệu dự án",
        "downstream": "Thư viện tài liệu SharePoint được đồng bộ",
        "role": "Quản lý hạ tầng SharePoint dưới dạng mã và đồng bộ hóa thư mục dự án.",
    },
    "ccba-xia": {
        "upstream": "Tài liệu kỹ thuật phức tạp cần bóc tách",
        "downstream": "Dữ liệu cấu trúc hóa chuẩn xác",
        "role": "Tác nhân thông minh chuyên trích xuất thông tin chuyên sâu từ tài liệu.",
    },
    "ccba-docs-manager": {
        "upstream": "Thay đổi tài liệu hoặc thêm kỹ năng mới",
        "downstream": "Hệ thống tài liệu nhất quán, không đứt gãy liên kết",
        "role": "Quản trị cấu trúc tài liệu, kiểm toán liên kết chéo và chuẩn hóa định dạng.",
    },
    "ccba-sync-upstream": {
        "upstream": "Kho chứa thượng nguồn (ClaudeKit, Matt Pocock, v.v.)",
        "downstream": "ccba-xia / Khuyến nghị porting",
        "role": "Kiểm tra cập nhật và thẩm tra tính năng thượng nguồn (ADR-0057 Radar).",
    },
}


# ---------------------------------------------------------------------------
# Core Data Models & Parsing Helpers
# ---------------------------------------------------------------------------

def extract_frontmatter_and_body(file_path: Path) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter and body from a markdown file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        if not content.startswith("---"):
            return {}, content
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}, content
        fm = yaml.safe_load(parts[1])
        fm_dict = fm if isinstance(fm, dict) else {}
        body = parts[2].strip()
        return fm_dict, body
    except Exception as e:
        print(f"[Warning] Failed to parse {file_path}: {e}", file=sys.stderr)
        return {}, ""


def load_portals(portals_path: Path = PORTALS_YAML_PATH) -> list[dict[str, Any]]:
    """Load portal taxonomy configuration from YAML."""
    if not portals_path.exists():
        raise FileNotFoundError(f"Portals file not found at {portals_path}")
    data = yaml.safe_load(portals_path.read_text(encoding="utf-8")) or {}
    portals = data.get("portals", [])
    if not isinstance(portals, list):
        raise ValueError("Field 'portals' in portals.yaml must be a list")
    return portals


def build_skill_portal_map(portals: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Create a mapping from skill name to portal info."""
    mapping: dict[str, dict[str, Any]] = {}
    for p in portals:
        p_id = p.get("id", "")
        p_name = p.get("name", "")
        p_icon = p.get("icon", "")
        for s_name in p.get("skills", []):
            mapping[str(s_name).strip()] = {
                "id": p_id,
                "name": p_name,
                "icon": p_icon,
            }
    return mapping


def get_all_skills_data(hub_root: Path = HUB_ROOT) -> list[dict[str, Any]]:
    """Scan and compile metadata for all active skills in .agents/skills/."""
    skills_dir = hub_root / ".agents" / "skills"
    portals = load_portals(hub_root / "docs" / "skills" / "portals.yaml")
    portal_map = build_skill_portal_map(portals)

    skill_files = sorted(skills_dir.glob("**/SKILL.md"))
    skills: list[dict[str, Any]] = []

    for sf in skill_files:
        fm, body = extract_frontmatter_and_body(sf)
        if not fm:
            continue

        name = str(fm.get("name") or sf.parent.name).strip()
        description = str(fm.get("description") or "").strip()
        bundle = str(fm.get("bundle") or "_core").strip()
        tier_raw = str(fm.get("tier") or "kernel").strip().lower()
        command = str(fm.get("command") or f"/{name}").strip()
        user_invocable = bool(fm.get("user-invocable", False))
        disable_model_inv = bool(fm.get("disable-model-invocation", False))

        raw_triggers = fm.get("triggers") or fm.get("keywords") or []
        if isinstance(raw_triggers, str):
            raw_triggers = [raw_triggers]
        triggers = [str(t).strip() for t in raw_triggers if str(t).strip()]

        # Resolve tier display
        if tier_raw == "orchestrator":
            tier_display = "Tier 3 (Orchestrator)"
            tier_badge = "orchestrator"
        else:
            tier_display = "Tier 2B (Kernel)"
            tier_badge = "kernel"

        # Resolve invocation display
        if user_invocable and disable_model_inv:
            invocable_display = "User-invoked (Chỉ lệnh Slash Command)"
            invocable_badge = "user"
        elif user_invocable and not disable_model_inv:
            invocable_display = "Song song (Slash Command & Model Trigger)"
            invocable_badge = "both"
        elif not user_invocable and not disable_model_inv:
            invocable_display = "Model-invoked (Tự động kích hoạt qua bối cảnh)"
            invocable_badge = "model"
        else:
            invocable_display = "User-invoked (Slash Command)"
            invocable_badge = "user"

        portal_info = portal_map.get(
            name,
            {"id": "governance_upkeep", "name": "Quản trị Nền tảng", "icon": "🛡️"},
        )

        pipeline_info = PIPELINE_MAP.get(
            name,
            {
                "upstream": "Quy trình tác nghiệp dự án",
                "downstream": "Bàn giao kết quả phiên làm việc",
                "role": description or "Thực thi tác vụ nghiệp vụ chuyên biệt.",
            },
        )

        gpi_info = fm.get("gpi")
        gpi_str = ""
        if isinstance(gpi_info, dict):
            s = gpi_info.get("s", 0)
            k = gpi_info.get("k", 0)
            a = gpi_info.get("a", 0)
            p = gpi_info.get("p", 0)
            total = sum([s, k, a, p])
            gpi_str = f"S={s} | K={k} | A={a} | P={p} (Tổng: {total:.1f})"

        skills.append({
            "name": name,
            "description": description,
            "bundle": bundle,
            "tier": tier_raw,
            "tier_display": tier_display,
            "tier_badge": tier_badge,
            "command": command,
            "user_invocable": user_invocable,
            "disable_model_invocation": disable_model_inv,
            "invocable_display": invocable_display,
            "invocable_badge": invocable_badge,
            "triggers": triggers,
            "portal": portal_info,
            "pipeline": pipeline_info,
            "gpi_str": gpi_str,
            "body": body,
            "skill_path": str(sf.relative_to(hub_root)).replace("\\", "/"),
        })

    # Sort with platform-loader first, then alphabetically
    skills.sort(key=lambda s: (0 if s["name"] == "platform-loader" else 1, s["name"]))
    return skills


# ---------------------------------------------------------------------------
# Generator 1: Standardized 5-Section Markdown Documentation
# ---------------------------------------------------------------------------

def generate_skill_markdown(skill: dict[str, Any]) -> str:
    """Generate standardized 5-section Markdown doc for a single skill."""
    name = skill["name"]
    command = skill["command"]
    desc = skill["description"]
    portal = skill["portal"]
    portal_display = f"{portal['icon']} {portal['name']}"
    tier_display = skill["tier_display"]
    bundle = skill["bundle"]
    inv_display = skill["invocable_display"]
    pipeline = skill["pipeline"]
    triggers = skill["triggers"]
    gpi_str = skill["gpi_str"]

    triggers_list = "\n".join([f"- `{t}`" for t in triggers]) if triggers else "- Không khai báo triggers cụ thể"

    gpi_row = f"| **Điểm Đánh Giá GPI (ADR-0057)** | `{gpi_str}` |\n" if gpi_str else ""

    md = f"""# {name}

> **Mô tả ngắn**: {desc}

---

## 1. Action Header & Kích Hoạt Nhanh

### Cú pháp Lệnh (Slash Command)
```bash
{command}
```

### Đồng bộ sang Phân vùng Spoke
```bash
python scripts/spoke/sync_spoke.py --skills {name}
```

### Thông Số & Huy Hiệu Kỹ Năng
| Thuộc tính | Chi tiết |
| :--- | :--- |
| **Cổng Điều Hướng (Portal)** | {portal_display} |
| **Phân Tầng Kiến Trúc (Tier)** | `{tier_display}` |
| **Gói Bundle** | `{bundle}` |
| **Phương Thức Triệu Hồi** | {inv_display} |
{gpi_row}
---

## 2. Mục Đích & Rào Chắn Bất Biến (Defining Constraints)

### Mục Đích Hoạt Động
{desc}

Kỹ năng này hoạt động như một giao diện nhận thức chuẩn mực cho AI Agent và kỹ sư, đảm bảo tính tất định và khả năng tái lập trong toàn bộ vòng đời dự án.

### Rào Chắn Bất Biến (Platform Invariants)
1. **Bảo Vệ Ngân Sách Ngữ Cảnh (ADR-0030)**: Tệp `SKILL.md` của kỹ năng chỉ chứa hướng dẫn tác nghiệp cốt lõi, không chứa văn xuôi tiếp thị hay nội dung dư thừa gây tràn Context Window.
2. **Khóa Cứng Kỷ Luật Hoàn Thành (ADR-0058)**: Agent tuyệt đối không được báo cáo hoàn thành nhiệm vụ nếu bất kỳ lệnh kiểm thử tự động nào trả về mã lỗi khác 0 (`exit code != 0`).
3. **Cô Lập Vùng Ghi (Artifact Scope)**: Mọi tệp thành phẩm sinh ra phải nằm trong thư mục quy định của dự án, không làm ô nhiễm thư mục gốc (Project Root).
4. **Bảo Mật Bí Mật (Zero Secret Leaks)**: Tuyệt đối không hardcode API Keys, mật khẩu hoặc khóa chứng thực vào bất kỳ tệp tài liệu hay mã nguồn nào.

---

## 3. Khi Nào Sử Dụng & Kích Hoạt (Triggers)

### Từ Khóa Kích Hoạt (Triggers)
{triggers_list}

### Ngữ Cảnh Khuyến Nghị Triệu Hồi
- Khi cần thực thi nghiệp vụ liên quan trực tiếp đến vai trò: {pipeline['role']}
- Trong chuỗi phát triển khi nhận tín hiệu bàn giao từ: **{pipeline['upstream']}**

### Khi Nào KHÔNG Nên Dùng (Anti-patterns)
- Không dùng nếu cần tư vấn định hướng ban đầu: hãy gọi `/ccba-ask`.
- Không tự ý sửa đổi thủ công định nghĩa kỹ năng nếu gặp lỗi: hãy dùng `/ccba-skill-repair`.

---

## 4. Vị Trí Trong Chuỗi Giá Trị (The Pipeline Trail)

Kỹ năng `{name}` giữ vị trí then chốt trong chuỗi giá trị tích hợp của nền tảng:

```text
[ {pipeline['upstream']} ]
          │
          ▼
    >>> [ {name} ] <<<  ({pipeline['role']})
          │
          ▼
[ {pipeline['downstream']} ]
```

- **Đầu vào (Upstream)**: Nhận bối cảnh từ `{pipeline['upstream']}`.
- **Thực thi (In-flight)**: Áp dụng các quy tắc kỹ thuật và công cụ tự động hóa để sản sinh kết quả chuẩn mực.
- **Đầu ra & Bàn giao (Downstream)**: Chuyển giao thành phẩm sạch sẽ sang `{pipeline['downstream']}`.

---

## 5. Khóa Cứng Kỷ Luật & Tiêu Chí Hoàn Thành (ADR-0058)

### Lệnh Kiểm Thử Tự Động Bắt Buộc
Mọi thay đổi liên quan đến kỹ năng này bắt buộc phải vượt qua toàn bộ các kiểm thử tự động sau:
```bash
python -m ccba_harness verify-patch --preset skill
python scripts/validate_skills.py --file .agents/skills/{name}/SKILL.md --enforce-gpi
```

### Danh Mục Kiểm Thức Hoàn Thành (Definition of Done - DoD)
- [ ] Lệnh kiểm chứng `verify-patch` trả về mã thoát `exit code 0`.
- [ ] Toàn bộ thuộc tính frontmatter trong `SKILL.md` đồng bộ 100% với `catalog.yaml`.
- [ ] Không có liên kết nội bộ bị đứt gãy hoặc tham chiếu file không tồn tại.
- [ ] Thành phẩm sinh ra nằm gọn trong thư mục đích, tuân thủ nguyên tắc KISS.
"""
    return md.strip() + "\n"


# ---------------------------------------------------------------------------
# Generator 2: INDEX.md Central Directory
# ---------------------------------------------------------------------------

def generate_index_markdown(portals: list[dict[str, Any]], skills: list[dict[str, Any]]) -> str:
    """Generate docs/skills/INDEX.md as a readable table of contents for terminals & IDEs."""
    skills_by_portal: dict[str, list[dict[str, Any]]] = {}
    for p in portals:
        skills_by_portal[p["id"]] = []

    for s in skills:
        p_id = s["portal"]["id"]
        if p_id in skills_by_portal:
            skills_by_portal[p_id].append(s)

    lines: list[str] = [
        "# CCBA Agent Platform — Danh Mục Kỹ Năng (Skills Catalog Index)",
        "",
        f"> **Tổng hợp**: {len(skills)} Kỹ năng Hoạt động được phân loại vào 5 Cổng Điều Hướng theo chuẩn ADR-0047, ADR-0057 và ADR-0058.",
        "",
        "Trang tài liệu này phục vụ tra cứu nhanh cho kỹ sư và AI Coding Agents trong Terminal hoặc IDE.",
        "Xem bản web trực quan tại [docs/index.html](../index.html) hoặc tóm tắt chuẩn máy đọc tại [docs/llms.txt](../llms.txt).",
        "",
        "---",
        "",
        "## Mục Lục Các Cổng Điều Hướng",
        "",
    ]

    for p in portals:
        lines.append(f"- [{p['icon']} {p['name']}](#{p['id']}) ({len(skills_by_portal.get(p['id'], []))} skills)")

    lines.extend(["", "---", ""])

    for p in portals:
        p_id = p["id"]
        p_name = p["name"]
        p_icon = p["icon"]
        p_desc = p["description"]
        p_skills = skills_by_portal.get(p_id, [])

        lines.extend([
            f"<a id=\"{p_id}\"></a>",
            f"## {p_icon} {p_name} ({len(p_skills)} Kỹ Năng)",
            "",
            f"*{p_desc}*",
            "",
            "| Kỹ Năng | Slash Command | Phân Tầng | Triệu Hồi | Tóm Tắt Nhiệm Vụ |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])

        for s in p_skills:
            name = s["name"]
            cmd = s["command"]
            tier = s["tier_badge"]
            inv = "User" if s["invocable_badge"] == "user" else ("Model" if s["invocable_badge"] == "model" else "Both")
            desc = s["description"].replace("\n", " ")
            if len(desc) > 80:
                desc = desc[:77] + "..."
            lines.append(f"| [{name}]({name}.md) | `{cmd}` | `{tier}` | `{inv}` | {desc} |")

        lines.extend(["", "---", ""])

    lines.extend([
        "## Tài Liệu Bổ Trợ & Quy Chuẩn",
        "",
        "- [Hỏi Đáp Thường Gặp (FAQ)](FAQ.md) — Hướng dẫn Hub vs Spoke, xử lý lỗi và đồng bộ.",
        "- [llms.txt](../llms.txt) — Endpoint mô tả nền tảng theo chuẩn mở cho AI Agents.",
        "- [llms-full.txt](../llms-full.txt) — Nội dung hợp nhất chi tiết của toàn bộ kỹ năng.",
        "",
        "---",
        "*CCBA Agent Services Platform — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*",
    ])

    return "\n".join(lines).strip() + "\n"


# ---------------------------------------------------------------------------
# Generator 3: Machine-Readable Agent Endpoints (llms.txt & llms-full.txt)
# ---------------------------------------------------------------------------

def generate_llms_txt(portals: list[dict[str, Any]], skills: list[dict[str, Any]]) -> str:
    """Generate docs/llms.txt following the llms.txt standard."""
    lines: list[str] = [
        "# CCBA Agent Platform Skills",
        "",
        f"> Curated registry of {len(skills)} engineering, BIM, legal, and governance agent skills for the CCBA Agent Services Platform.",
        "",
        "## Navigation Portals",
        "",
    ]

    for p in portals:
        lines.append(f"- [{p['name']}](skills/INDEX.md#{p['id']}): {p['description']}")

    lines.extend(["", "## Core Endpoints & Documentation", ""])
    lines.append(f"- [Skills Index](skills/INDEX.md): Markdown catalog index for all {len(skills)} skills.")
    lines.append("- [Skills FAQ](skills/FAQ.md): Frequently asked questions on Hub-Spoke, invocation, and troubleshooting.")
    lines.append(f"- [Full Consolidated Skills Text](llms-full.txt): Complete full-text documentation of all {len(skills)} skills.")

    lines.extend(["", f"## All Active Skills ({len(skills)} Skills)", ""])

    for s in skills:
        name = s["name"]
        desc = s["description"].replace("\n", " ")
        cmd = s["command"]
        lines.append(f"- [{name}](skills/{name}.md): {cmd} — {desc}")

    return "\n".join(lines).strip() + "\n"


def generate_llms_full_txt(skills: list[dict[str, Any]]) -> str:
    """Generate docs/llms-full.txt by concatenating all skill docs."""
    chunks: list[str] = [
        "# CCBA Agent Platform — Full Consolidated Skills Specification",
        "",
        f"> Complete documentation of all {len(skills)} active skills on the CCBA Agent Services Platform.",
        "> Generated for single-pass ingestion by AI coding agents and RAG indexers.",
        "",
        "=" * 80,
        "",
    ]

    for idx, s in enumerate(skills, start=1):
        md = generate_skill_markdown(s)
        chunks.append(f"<!-- SKILL {idx}/{len(skills)}: {s['name']} -->")
        chunks.append(md)
        chunks.append("\n" + "=" * 80 + "\n")

    return "\n".join(chunks).strip() + "\n"


# ---------------------------------------------------------------------------
# Generator 4: Offline-First Single-Page Web Portal (docs/index.html)
# ---------------------------------------------------------------------------

def generate_index_html(portals: list[dict[str, Any]], skills: list[dict[str, Any]]) -> str:
    """Generate single-page static HTML web portal with embedded JSON data."""
    # Prepare embedded JSON data for offline-first instant search and drawer display
    skills_json_data = []
    for s in skills:
        skills_json_data.append({
            "name": s["name"],
            "command": s["command"],
            "desc": s["description"],
            "bundle": s["bundle"],
            "tier": s["tier_badge"],
            "tier_display": s["tier_display"],
            "inv": s["invocable_badge"],
            "inv_display": s["invocable_display"],
            "portal_id": s["portal"]["id"],
            "portal_name": s["portal"]["name"],
            "portal_icon": s["portal"]["icon"],
            "triggers": s["triggers"],
            "gpi": s["gpi_str"],
            "upstream": s["pipeline"]["upstream"],
            "downstream": s["pipeline"]["downstream"],
            "role": s["pipeline"]["role"],
        })

    portals_json_data = []
    for p in portals:
        count = sum(1 for s in skills if s["portal"]["id"] == p["id"])
        portals_json_data.append({
            "id": p["id"],
            "name": p["name"],
            "icon": p["icon"],
            "desc": p["description"],
            "count": count,
        })

    embedded_skills_json = json.dumps(skills_json_data, ensure_ascii=False).replace("<", "\\u003c")
    embedded_portals_json = json.dumps(portals_json_data, ensure_ascii=False).replace("<", "\\u003c")

    html = f"""<!DOCTYPE html>
<html lang="vi" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CCBA Skills Portal — Danh Mục Kỹ Năng Agent Platform</title>
  <meta name="description" content="Cổng tra cứu {len(skills)} kỹ năng, quy trình chuẩn mực và công cụ tự động hóa cho kỹ sư xây dựng và AI Coding Agents trên CCBA Agent Services Platform.">
  <style>
    :root {{
      --bg: #0d1117;
      --bg-card: #161b22;
      --bg-card-hover: #1f242c;
      --border: #30363d;
      --border-accent: #388bfd;
      --text: #e6edf3;
      --text-muted: #8b949e;
      --primary: #58a6ff;
      --primary-hover: #79c0ff;
      --accent: #238636;
      --accent-hover: #2ea043;
      --badge-bg: #21262d;
      --code-bg: #0d1117;
      --chip-active: #1f6feb;
      --modal-overlay: rgba(0, 0, 0, 0.75);
    }}
    [data-theme="light"] {{
      --bg: #f6f8fa;
      --bg-card: #ffffff;
      --bg-card-hover: #f3f4f6;
      --border: #d0d7de;
      --border-accent: #0969da;
      --text: #1f2328;
      --text-muted: #656d76;
      --primary: #0969da;
      --primary-hover: #0550ae;
      --accent: #1a7f37;
      --accent-hover: #116329;
      --badge-bg: #eff2f5;
      --code-bg: #f6f8fa;
      --chip-active: #0969da;
      --modal-overlay: rgba(31, 35, 40, 0.5);
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.5;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    header {{
      border-bottom: 1px solid var(--border);
      background-color: var(--bg-card);
      position: sticky;
      top: 0;
      z-index: 50;
      backdrop-filter: blur(8px);
    }}
    .header-container {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 0.75rem 1.5rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      text-decoration: none;
      color: var(--text);
      font-weight: 700;
      font-size: 1.15rem;
    }}
    .brand-icon {{
      background: linear-gradient(135deg, #1f6feb, #238636);
      width: 32px;
      height: 32px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-size: 1.1rem;
    }}
    .nav-links {{
      display: flex;
      align-items: center;
      gap: 1rem;
      font-size: 0.875rem;
    }}
    .nav-links a {{
      color: var(--text-muted);
      text-decoration: none;
      transition: color 0.15s ease;
    }}
    .nav-links a:hover {{ color: var(--primary); }}
    .theme-btn {{
      background: var(--badge-bg);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 0.4rem 0.8rem;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.875rem;
      display: flex;
      align-items: center;
      gap: 0.35rem;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 2rem 1.5rem;
      flex: 1;
      width: 100%;
    }}
    .hero {{
      text-align: center;
      margin-bottom: 2.5rem;
    }}
    .hero h1 {{
      font-size: 2.25rem;
      font-weight: 800;
      letter-spacing: -0.025em;
      margin-bottom: 0.75rem;
      background: linear-gradient(135deg, var(--text) 40%, var(--primary));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .hero p {{
      color: var(--text-muted);
      max-width: 760px;
      margin: 0 auto 1.5rem;
      font-size: 1.05rem;
    }}
    .stats-pills {{
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 0.75rem;
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      background: var(--badge-bg);
      border: 1px solid var(--border);
      padding: 0.35rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.825rem;
      font-weight: 500;
    }}
    .search-section {{
      position: sticky;
      top: 57px;
      background: var(--bg);
      padding: 1rem 0;
      z-index: 40;
      border-bottom: 1px solid var(--border);
      margin-bottom: 1.5rem;
    }}
    .search-box {{
      position: relative;
      margin-bottom: 1rem;
    }}
    .search-input {{
      width: 100%;
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.85rem 1rem 0.85rem 2.75rem;
      font-size: 1rem;
      color: var(--text);
      outline: none;
      transition: border-color 0.2s;
    }}
    .search-input:focus {{
      border-color: var(--border-accent);
      box-shadow: 0 0 0 3px rgba(56, 139, 253, 0.2);
    }}
    .search-icon {{
      position: absolute;
      left: 1rem;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-muted);
      pointer-events: none;
    }}
    .portal-chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }}
    .chip {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 0.45rem 0.9rem;
      border-radius: 6px;
      font-size: 0.875rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      transition: all 0.15s;
    }}
    .chip:hover {{
      border-color: var(--border-accent);
      color: var(--text);
    }}
    .chip.active {{
      background: var(--chip-active);
      border-color: var(--chip-active);
      color: #fff;
      font-weight: 600;
    }}
    .chip .count {{
      background: rgba(0, 0, 0, 0.2);
      padding: 0.1rem 0.45rem;
      border-radius: 9999px;
      font-size: 0.75rem;
    }}
    .skills-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
      gap: 1.25rem;
    }}
    .skill-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: transform 0.15s, border-color 0.15s, box-shadow 0.15s;
    }}
    .skill-card:hover {{
      transform: translateY(-2px);
      border-color: var(--border-accent);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    }}
    .card-header {{
      margin-bottom: 0.75rem;
    }}
    .card-title-row {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 0.5rem;
      margin-bottom: 0.35rem;
    }}
    .skill-name {{
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--text);
      text-decoration: none;
      cursor: pointer;
    }}
    .skill-name:hover {{ color: var(--primary); }}
    .badge {{
      font-size: 0.72rem;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}
    .badge-kernel {{ background: #238636; color: #fff; }}
    .badge-orchestrator {{ background: #8957e5; color: #fff; }}
    .badge-portal {{ background: var(--badge-bg); border: 1px solid var(--border); color: var(--text-muted); }}
    .badge-user {{ background: #1f6feb; color: #fff; }}
    .badge-model {{ background: #9e6a03; color: #fff; }}
    .badge-both {{ background: #388bfd; color: #fff; }}
    .card-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.35rem;
      margin-bottom: 0.75rem;
    }}
    .skill-desc {{
      font-size: 0.875rem;
      color: var(--text-muted);
      margin-bottom: 1rem;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
      line-height: 1.45;
    }}
    .card-triggers {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.3rem;
      margin-bottom: 1rem;
    }}
    .tag {{
      font-size: 0.72rem;
      background: var(--badge-bg);
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 0.15rem 0.45rem;
      border-radius: 4px;
      font-family: monospace;
    }}
    .card-actions {{
      display: flex;
      gap: 0.5rem;
      padding-top: 0.75rem;
      border-top: 1px solid var(--border);
    }}
    .btn {{
      flex: 1;
      padding: 0.45rem 0.65rem;
      font-size: 0.8rem;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: var(--badge-bg);
      color: var(--text);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.35rem;
      font-weight: 500;
      transition: all 0.15s;
    }}
    .btn:hover {{
      border-color: var(--border-accent);
      background: var(--bg-card-hover);
    }}
    .btn-primary {{
      background: var(--primary);
      border-color: var(--primary);
      color: #fff;
    }}
    .btn-primary:hover {{
      background: var(--primary-hover);
      border-color: var(--primary-hover);
    }}
    /* Detail Modal */
    .modal-backdrop {{
      display: none;
      position: fixed;
      inset: 0;
      background: var(--modal-overlay);
      z-index: 100;
      backdrop-filter: blur(4px);
      align-items: center;
      justify-content: center;
      padding: 1.5rem;
    }}
    .modal-backdrop.open {{ display: flex; }}
    .modal-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 10px;
      max-width: 800px;
      width: 100%;
      max-height: 90vh;
      display: flex;
      flex-direction: column;
      box-shadow: 0 16px 36px rgba(0, 0, 0, 0.4);
    }}
    .modal-header {{
      padding: 1.25rem 1.5rem;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }}
    .modal-close {{
      background: none;
      border: none;
      color: var(--text-muted);
      font-size: 1.5rem;
      cursor: pointer;
      padding: 0.25rem 0.5rem;
    }}
    .modal-body {{
      padding: 1.5rem;
      overflow-y: auto;
      font-size: 0.925rem;
      line-height: 1.6;
    }}
    .modal-section {{ margin-bottom: 1.5rem; }}
    .modal-section h3 {{
      font-size: 1.05rem;
      color: var(--primary);
      margin-bottom: 0.5rem;
      border-bottom: 1px solid var(--border);
      padding-bottom: 0.25rem;
    }}
    .pipeline-box {{
      background: var(--code-bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0.85rem;
      margin-top: 0.5rem;
    }}
    .toast {{
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      background: #238636;
      color: #fff;
      padding: 0.75rem 1.25rem;
      border-radius: 8px;
      font-size: 0.875rem;
      font-weight: 600;
      box-shadow: 0 8px 24px rgba(0,0,0,0.3);
      display: none;
      z-index: 200;
      animation: fadeIn 0.2s ease;
    }}
    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(10px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    footer {{
      border-top: 1px solid var(--border);
      background: var(--bg-card);
      padding: 1.5rem;
      text-align: center;
      font-size: 0.825rem;
      color: var(--text-muted);
      margin-top: 3rem;
    }}
    footer a {{ color: var(--primary); text-decoration: none; }}
  </style>
</head>
<body>
  <header>
    <div class="header-container">
      <a href="#" class="brand">
        <span class="brand-icon">⚡</span>
        <span>CCBA Skills Portal</span>
      </a>
      <div class="nav-links">
        <a href="skills/INDEX.md">INDEX.md</a>
        <a href="skills/FAQ.md">FAQ</a>
        <a href="llms.txt">llms.txt</a>
        <a href="llms-full.txt">llms-full.txt</a>
        <a href="https://github.com/vvChu/ccba-agent-platform" target="_blank" rel="noopener">GitHub</a>
        <button id="themeToggle" class="theme-btn" title="Đổi giao diện Sáng / Tối">🌓 Theme</button>
      </div>
    </div>
  </header>

  <main>
    <section class="hero">
      <h1>CCBA Agent Platform Skills Catalog</h1>
      <p>Hệ thống {len(skills)} kỹ năng chuẩn hóa, quy trình tác nghiệp và rào chắn kỷ luật tự động hóa cho kỹ sư xây dựng và AI Coding Agents.</p>
      <div class="stats-pills">
        <span class="pill">⚡ <strong>{len(skills)}</strong> Active Skills</span>
        <span class="pill">🚀 <strong>5</strong> Portals</span>
        <span class="pill">🛡️ <strong>100%</strong> Deterministic CI (ADR-0058)</span>
        <span class="pill">📦 <strong>GitHub Pages</strong> Ready</span>
      </div>
    </section>

    <div class="search-section">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input type="text" id="searchInput" class="search-input" placeholder="Tìm nhanh theo tên kỹ năng, slash command (/ccba-...), triggers hoặc mô tả..." autocomplete="off">
      </div>
      <div class="portal-chips" id="portalChips"></div>
    </div>

    <div class="skills-grid" id="skillsGrid"></div>
  </main>

  <div class="modal-backdrop" id="skillModal">
    <div class="modal-card">
      <div class="modal-header">
        <div>
          <h2 id="modalTitle" style="font-size: 1.35rem;">Skill Details</h2>
          <div id="modalMeta" class="card-meta" style="margin-top: 0.35rem;"></div>
        </div>
        <button class="modal-close" id="modalClose">&times;</button>
      </div>
      <div class="modal-body" id="modalBody"></div>
    </div>
  </div>

  <div class="toast" id="toast"></div>

  <footer>
    <p>CCBA Agent Services Platform — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.</p>
    <p style="margin-top: 0.35rem;">Designed for Human Engineers & Autonomous AI Agents. Governed by Layer 1 Constitution & ADR-0058.</p>
  </footer>

  <script>
    const SKILLS = {embedded_skills_json};
    const PORTALS = {embedded_portals_json};

    let activePortal = "all";
    let searchQuery = "";

    // DOM Elements
    const searchInput = document.getElementById("searchInput");
    const portalChipsContainer = document.getElementById("portalChips");
    const skillsGrid = document.getElementById("skillsGrid");
    const skillModal = document.getElementById("skillModal");
    const modalTitle = document.getElementById("modalTitle");
    const modalMeta = document.getElementById("modalMeta");
    const modalBody = document.getElementById("modalBody");
    const modalClose = document.getElementById("modalClose");
    const toast = document.getElementById("toast");
    const themeToggle = document.getElementById("themeToggle");

    // Theme Management
    const savedTheme = localStorage.getItem("ccba_theme") || "dark";
    document.documentElement.setAttribute("data-theme", savedTheme);

    themeToggle.addEventListener("click", () => {{
      const current = document.documentElement.getAttribute("data-theme");
      const next = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("ccba_theme", next);
    }});

    // XSS Prevention Utility
    function escapeHtml(str) {{
      if (str === null || str === undefined) return "";
      return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }}

    // Clipboard Toast
    function showToast(msg) {{
      toast.textContent = msg;
      toast.style.display = "block";
      setTimeout(() => {{ toast.style.display = "none"; }}, 2200);
    }}

    function copyToClipboard(text, label) {{
      navigator.clipboard.writeText(text).then(() => {{
        showToast(`Đã sao chép ${{label}}: ${{text}}`);
      }}).catch(() => {{
        const ta = document.createElement("textarea");
        ta.value = text;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
        showToast(`Đã sao chép ${{label}}: ${{text}}`);
      }});
    }}

    // Render Portal Filter Chips
    function renderPortalChips() {{
      portalChipsContainer.innerHTML = "";
      const totalCount = SKILLS.length;

      const allChip = document.createElement("div");
      allChip.className = `chip ${{activePortal === "all" ? "active" : ""}}`;
      allChip.innerHTML = `Tất cả <span class="count">${{totalCount}}</span>`;
      allChip.addEventListener("click", () => {{
        activePortal = "all";
        renderPortalChips();
        renderSkills();
      }});
      portalChipsContainer.appendChild(allChip);

      PORTALS.forEach(p => {{
        const chip = document.createElement("div");
        chip.className = `chip ${{activePortal === p.id ? "active" : ""}}`;
        chip.innerHTML = `${{p.icon}} ${{escapeHtml(p.name)}} <span class="count">${{p.count}}</span>`;
        chip.addEventListener("click", () => {{
          activePortal = p.id;
          renderPortalChips();
          renderSkills();
        }});
        portalChipsContainer.appendChild(chip);
      }});
    }}

    // Render Skills Grid
    function renderSkills() {{
      const query = searchQuery.trim().toLowerCase();
      const filtered = SKILLS.filter(s => {{
        const matchPortal = activePortal === "all" || s.portal_id === activePortal;
        if (!matchPortal) return false;
        if (!query) return true;
        const textToSearch = `${{s.name}} ${{s.command}} ${{s.desc}} ${{s.triggers.join(" ")}} ${{s.bundle}} ${{s.portal_name}}`.toLowerCase();
        return textToSearch.includes(query);
      }});

      skillsGrid.innerHTML = "";
      if (filtered.length === 0) {{
        skillsGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--text-muted);">Không tìm thấy kỹ năng nào khớp với từ khóa "<strong>${{escapeHtml(searchQuery)}}</strong>".</div>`;
        return;
      }}

      filtered.forEach(s => {{
        const card = document.createElement("div");
        card.className = "skill-card";

        const tierClass = s.tier === "orchestrator" ? "badge-orchestrator" : "badge-kernel";
        const invClass = `badge-${{s.inv}}`;

        const visibleTriggers = s.triggers.slice(0, 3).map(t => `<span class="tag">#${{escapeHtml(t)}}</span>`).join(" ");
        const moreTriggers = s.triggers.length > 3 ? `<span class="tag">+${{s.triggers.length - 3}}</span>` : "";

        card.innerHTML = `
          <div>
            <div class="card-header">
              <div class="card-title-row">
                <span class="skill-name" data-skill="${{escapeHtml(s.name)}}" onclick="openModal(this.getAttribute('data-skill'))">${{escapeHtml(s.name)}}</span>
                <span class="badge ${{tierClass}}">${{s.tier === "orchestrator" ? "Orchestrator" : "Kernel"}}</span>
              </div>
              <div class="card-meta">
                <span class="badge badge-portal">${{s.portal_icon}} ${{escapeHtml(s.portal_name)}}</span>
                <span class="badge ${{invClass}}">${{escapeHtml(s.inv.toUpperCase())}}</span>
              </div>
            </div>
            <div class="skill-desc">${{escapeHtml(s.desc)}}</div>
            <div class="card-triggers">${{visibleTriggers}} ${{moreTriggers}}</div>
          </div>
          <div class="card-actions">
            <button class="btn" data-clipboard="${{escapeHtml(s.command)}}" onclick="copyToClipboard(this.getAttribute('data-clipboard'), 'Slash Command')">📋 ${{escapeHtml(s.command)}}</button>
            <button class="btn" data-clipboard="python scripts/spoke/sync_spoke.py --skills ${{escapeHtml(s.name)}}" onclick="copyToClipboard(this.getAttribute('data-clipboard'), 'Lệnh Sync')">🔄 Sync</button>
            <button class="btn btn-primary" data-skill="${{escapeHtml(s.name)}}" onclick="openModal(this.getAttribute('data-skill'))">Chi Tiết</button>
          </div>
        `;
        skillsGrid.appendChild(card);
      }});
    }}

    // Modal Details
    window.openModal = function(skillName) {{
      const s = SKILLS.find(item => item.name === skillName);
      if (!s) return;

      modalTitle.textContent = s.name;
      modalMeta.innerHTML = `
        <span class="badge ${{s.tier === 'orchestrator' ? 'badge-orchestrator' : 'badge-kernel'}}">${{escapeHtml(s.tier_display)}}</span>
        <span class="badge badge-portal">${{s.portal_icon}} ${{escapeHtml(s.portal_name)}}</span>
        <span class="badge badge-${{s.inv}}">${{escapeHtml(s.inv_display)}}</span>
        <span class="badge badge-portal">Bundle: ${{escapeHtml(s.bundle)}}</span>
      `;

      const triggersHtml = s.triggers.map(t => `<span class="tag">#${{escapeHtml(t)}}</span>`).join(" ");
      const gpiHtml = s.gpi ? `<p style="margin-top:0.35rem; color:var(--text-muted); font-size:0.85rem;"><strong>Điểm GPI (ADR-0057):</strong> <code>${{escapeHtml(s.gpi)}}</code></p>` : "";

      modalBody.innerHTML = `
        <div class="modal-section">
          <h3>1. Action Header & Kích Hoạt Nhanh</h3>
          <p><strong>Slash Command:</strong> <code>${{escapeHtml(s.command)}}</code></p>
          <p><strong>Lệnh Đồng Bộ Spoke:</strong> <code>python scripts/spoke/sync_spoke.py --skills ${{escapeHtml(s.name)}}</code></p>
          ${{gpiHtml}}
        </div>

        <div class="modal-section">
          <h3>2. Mục Đích & Rào Chắn Bất Biến</h3>
          <p>${{escapeHtml(s.desc)}}</p>
          <ul style="padding-left: 1.25rem; margin-top: 0.5rem; color: var(--text-muted);">
            <li><strong>ADR-0030 (Cognitive Budget):</strong> Giữ nguyên vẹn runtime context sạch sẽ cho Agent.</li>
            <li><strong>ADR-0058 (Hard Completion Lock):</strong> Khóa cứng kỷ luật nghiệm thu qua exit code 0.</li>
            <li><strong>Bảo Mật:</strong> Tuyệt đối không để rò rỉ API Keys hay thông tin mật (ccba-maskara).</li>
          </ul>
        </div>

        <div class="modal-section">
          <h3>3. Triggers & Kích Hoạt</h3>
          <div style="margin-bottom: 0.5rem;">${{triggersHtml}}</div>
        </div>

        <div class="modal-section">
          <h3>4. Vị Trí Trong Chuỗi Giá Trị (The Pipeline Trail)</h3>
          <div class="pipeline-box">
            <p><strong>Đầu vào (Upstream):</strong> ${{escapeHtml(s.upstream)}}</p>
            <p><strong>Vai trò (In-flight):</strong> ${{escapeHtml(s.role)}}</p>
            <p><strong>Đầu ra (Downstream):</strong> ${{escapeHtml(s.downstream)}}</p>
          </div>
        </div>

        <div class="modal-section">
          <h3>5. Khóa Cứng Kỷ Luật Kiểm Thử (ADR-0058)</h3>
          <p>Lệnh kiểm chứng tự động tất định:</p>
          <pre style="background:var(--code-bg); padding:0.75rem; border-radius:6px; border:1px solid var(--border); margin-top:0.35rem; font-size:0.85rem;"><code>python -m ccba_harness verify-patch --preset skill\npython scripts/validate_skills.py --file .agents/skills/${{escapeHtml(s.name)}}/SKILL.md --enforce-gpi</code></pre>
        </div>

        <div style="text-align: right; margin-top: 1.5rem;">
          <a href="skills/${{encodeURIComponent(s.name)}}.md" class="btn btn-primary" style="text-decoration:none; display:inline-flex;">Xem Markdown Đầy Đủ ➔</a>
        </div>
      `;

      skillModal.classList.add("open");
    }};

    modalClose.addEventListener("click", () => {{ skillModal.classList.remove("open"); }});
    skillModal.addEventListener("click", (e) => {{ if (e.target === skillModal) skillModal.classList.remove("open"); }});
    document.addEventListener("keydown", (e) => {{ if (e.key === "Escape") skillModal.classList.remove("open"); }});

    // Instant Search
    searchInput.addEventListener("input", (e) => {{
      searchQuery = e.target.value;
      renderSkills();
    }});

    // Init
    renderPortalChips();
    renderSkills();
  </script>
</body>
</html>
"""
    return html


# ---------------------------------------------------------------------------
# Synchronization Check & Compiler CLI Logic
# ---------------------------------------------------------------------------

def check_skills_docs_in_sync(hub_root: Path = HUB_ROOT) -> tuple[bool, str]:
    """Check if docs on disk match what compile_skills_docs would generate."""
    skills = get_all_skills_data(hub_root)
    portals = load_portals(hub_root / "docs" / "skills" / "portals.yaml")
    diffs: list[str] = []

    # 1. Check all individual skill markdown files
    skills_docs_dir = hub_root / "docs" / "skills"
    for s in skills:
        doc_file = skills_docs_dir / f"{s['name']}.md"
        if not doc_file.exists():
            diffs.append(f"Missing documentation file: docs/skills/{s['name']}.md")
            continue
        expected_content = generate_skill_markdown(s)
        current_content = doc_file.read_text(encoding="utf-8")
        if current_content.strip() != expected_content.strip():
            diffs.append(f"Content drift in: docs/skills/{s['name']}.md")

    # Check for orphaned doc files
    expected_skill_files = {f"{s['name']}.md" for s in skills}
    if skills_docs_dir.exists():
        actual_files = {f.name for f in skills_docs_dir.glob("*.md") if f.name not in ["INDEX.md", "FAQ.md"]}
        orphaned = actual_files - expected_skill_files
        if orphaned:
            diffs.append(f"Orphaned skill documentation files: {sorted(orphaned)}")

    # 2. Check INDEX.md
    index_file = skills_docs_dir / "INDEX.md"
    if not index_file.exists():
        diffs.append("Missing documentation index: docs/skills/INDEX.md")
    else:
        expected_index = generate_index_markdown(portals, skills)
        if index_file.read_text(encoding="utf-8").strip() != expected_index.strip():
            diffs.append("Content drift in: docs/skills/INDEX.md")

    # 3. Check llms.txt
    llms_file = hub_root / "docs" / "llms.txt"
    if not llms_file.exists():
        diffs.append("Missing endpoint file: docs/llms.txt")
    else:
        expected_llms = generate_llms_txt(portals, skills)
        if llms_file.read_text(encoding="utf-8").strip() != expected_llms.strip():
            diffs.append("Content drift in: docs/llms.txt")

    # 4. Check llms-full.txt
    llms_full_file = hub_root / "docs" / "llms-full.txt"
    if not llms_full_file.exists():
        diffs.append("Missing endpoint file: docs/llms-full.txt")
    else:
        expected_full = generate_llms_full_txt(skills)
        if llms_full_file.read_text(encoding="utf-8").strip() != expected_full.strip():
            diffs.append("Content drift in: docs/llms-full.txt")

    # 5. Check index.html
    html_file = hub_root / "docs" / "index.html"
    if not html_file.exists():
        diffs.append("Missing web portal file: docs/index.html")
    else:
        expected_html = generate_index_html(portals, skills)
        if html_file.read_text(encoding="utf-8").strip() != expected_html.strip():
            diffs.append("Content drift in: docs/index.html")

    if diffs:
        return False, "\n".join(diffs)
    return True, "All skills documentation and web assets are 100% in sync"


def compile_and_write(hub_root: Path = HUB_ROOT) -> None:
    """Compile and write all skill documentation and web assets to disk."""
    skills = get_all_skills_data(hub_root)
    portals = load_portals(hub_root / "docs" / "skills" / "portals.yaml")

    docs_skills_dir = hub_root / "docs" / "skills"
    docs_skills_dir.mkdir(parents=True, exist_ok=True)

    # 1. Write individual skill markdowns
    for s in skills:
        md_content = generate_skill_markdown(s)
        out_file = docs_skills_dir / f"{s['name']}.md"
        out_file.write_text(md_content, encoding="utf-8")

    # 2. Write INDEX.md
    index_content = generate_index_markdown(portals, skills)
    (docs_skills_dir / "INDEX.md").write_text(index_content, encoding="utf-8")

    # 3. Write llms.txt and llms-full.txt
    llms_content = generate_llms_txt(portals, skills)
    (hub_root / "docs" / "llms.txt").write_text(llms_content, encoding="utf-8")

    llms_full_content = generate_llms_full_txt(skills)
    (hub_root / "docs" / "llms-full.txt").write_text(llms_full_content, encoding="utf-8")

    # 4. Write index.html
    html_content = generate_index_html(portals, skills)
    (hub_root / "docs" / "index.html").write_text(html_content, encoding="utf-8")

    print(f"[OK] Compiled {len(skills)} skills docs, INDEX.md, llms.txt, llms-full.txt, and index.html successfully.")


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for docs compiler."""
    parser = argparse.ArgumentParser(description="CCBA Skills Documentation & Static Portal Compiler (ADR-0058)")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if docs on disk match what would be compiled (returns non-zero if out of sync).",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Compile and write all documentation and web assets to disk (default).",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print INDEX.md content to stdout instead of writing to disk.",
    )

    args = parser.parse_args(argv)

    if args.check:
        in_sync, msg = check_skills_docs_in_sync(HUB_ROOT)
        if in_sync:
            print("[OK] [Skills Docs Compiler] All skills documentation and web assets are 100% in sync.")
            return 0
        else:
            print("[ERROR] [Skills Docs Compiler] Documentation is OUT OF SYNC:", file=sys.stderr)
            print(f"  {msg}", file=sys.stderr)
            print("\n[INFO] Run 'python scripts/governance/compile_skills_docs.py --write' to regenerate.", file=sys.stderr)
            return 1

    if args.stdout:
        skills = get_all_skills_data(HUB_ROOT)
        portals = load_portals(HUB_ROOT / "docs" / "skills" / "portals.yaml")
        print(generate_index_markdown(portals, skills))
        return 0

    compile_and_write(HUB_ROOT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
