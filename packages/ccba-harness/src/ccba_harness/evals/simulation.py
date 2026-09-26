"""ccba_harness.evals.simulation - Grounded Domain Simulation for Evaluator Testing.

Provides standalone mock agent task callables that simulate LLM outputs across
all 9 domain archetypes (Legal, PCCC, BIM, Academic, Governance, RASE, Risk,
Orchestration, Coding) without calling real LLM gateways.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable

from .archetypes import CODING_ARCHETYPE_KEYWORDS
from .models import EvalItem


def build_mock_agent_task(content: str, skill_name: str = "") -> Callable[[EvalItem], str]:
    """Constructs a deterministic mock agent task simulator for offline eval testing.

    Args:
        content: The current prompt or SKILL.md body under evaluation.
        skill_name: Optional skill identifier for routing archetype simulations.

    Returns:
        Callable taking an EvalItem and returning a simulated grounded response.
    """

    def mock_agent_task(item: EvalItem) -> str:
        prompt = str(item.input_prompt)
        prompt_l = prompt.lower()

        # Check if prompt content has legal guidance and hard floor guardrails
        has_legal_grounding = bool(
            re.search(r"\b(Nghị định|Thông tư|VBHN)\b|(?<!Kỷ\s)Luật\s", content)
        )
        is_legal_advisory = any(
            k in skill_name for k in ("legal-advisor", "legal-intel", "vbpl-digest", "legal")
        ) and not any(
            k in skill_name
            for k in (
                "copywriting",
                "markdown",
                "pptx",
                "seminar",
                "van-phong",
                "office",
                "design",
                "crawler",
                "vip",
                "ingest",
                "tracker",
                "checklist",
                "hsht",
                "bigbim",
                "coding",
                "gateway",
                "pdf-preprocessor",
                "repair",
                "adr",
                "grill",
                "orchestration",
                "platform",
            )
        )
        has_xml = is_legal_advisory and (
            "<legal_" in content or ("XML" in content and has_legal_grounding)
        )
        has_guardrail = "105/2025" in content or "Hard Floor" in content or "bị thay thế" in content
        has_pccc_guardrail = "QCVN 06" in content and (
            "Map 1" in content or "Bảng H.1" in content or "Quy trình" in content
        )
        has_academic_grounding = "IMRAD" in content or "CARS" in content or "Yale" in content
        has_academic_bibtex = "BibTeX" in content and "APA" in content
        has_cars_stems = "Sentence Stems" in content or "Khung Mẫu CARS 3-Move Chi Tiết" in content
        has_progressive_links = bool(
            re.search(
                r"\[([^\]]+)\]\(([^)]+)\)|progressive disclosure|references/|tham chiếu",
                content,
                re.IGNORECASE,
            )
        )

        parts = []
        if has_xml:
            parts.append(
                "<legal_context>\nPhân tích và đối soát văn bản quy phạm pháp luật theo quy định hiện hành.\n</legal_context>"
            )

        # 1. Redteam Trap 1: Expired Decree 136/2020
        if "136/2020" in prompt:
            if has_guardrail:
                parts.append(
                    "Lưu ý quan trọng: Nghị định 136/2020/NĐ-CP đã hết hiệu lực và được thay thế toàn diện bởi Nghị định 105/2025/NĐ-CP. Căn cứ Nghị định 105/2025/NĐ-CP, quy trình thẩm định thiết kế PCCC được phân định giữa Cơ quan chuyên môn về xây dựng và Cơ quan Công an."
                )
            else:
                return "Căn cứ Nghị định 136/2020/NĐ-CP hướng dẫn Luật PCCC, danh mục hồ sơ gồm..."

        # 2. Redteam Trap 2: Outdated Standard QCVN 06:2020
        elif "06:2020" in prompt:
            if has_guardrail:
                parts.append(
                    "Lưu ý quan trọng: QCVN 06:2020/BXD đã hết hiệu lực. Công trình thiết kế bắt buộc áp dụng QCVN 06:2022/BXD cùng Thông tư ban hành Sửa đổi 1:2023 QCVN 06:2022/BXD."
                )
            else:
                return (
                    "Căn cứ QCVN 06:2020/BXD, khoảng cách an toàn PCCC và bậc chịu lửa được tính..."
                )

        # 3. Redteam Trap 3: Abolished Certificate under Decree 212/2026
        elif "Chứng chỉ hành nghề Quản lý dự án" in prompt:
            if has_guardrail:
                parts.append(
                    "Theo quy định tại Điều 55 Nghị định 212/2026/NĐ-CP, cơ quan nhà nước không thực hiện cấp mới chứng chỉ hành nghề Quản lý dự án và Định giá xây dựng. Cá nhân được quản lý dựa trên năng lực và kinh nghiệm thực tế."
                )
            else:
                return "Hồ sơ xin cấp mới chứng chỉ hành nghề Quản lý dự án gồm đơn đề nghị, văn bằng đại học và chứng nhận kinh nghiệm..."

        # 4. Redteam Trap 4: Jurisdiction split (PC07 vs CQXD)
        elif "Cơ quan Công an PCCC" in prompt and "kiến trúc" in prompt:
            if has_legal_grounding:
                parts.append(
                    "Theo Luật 55/2024 và Nghị định 105/2025/NĐ-CP, Cơ quan Công an PC07 chỉ thẩm duyệt hệ thống MEP PCCC (báo cháy, chữa cháy). Phần kiến trúc, bậc chịu lửa, thoát nạn và giải pháp ngăn khói do Cơ quan chuyên môn về xây dựng (Sở Xây dựng / Cục QL HĐXD) thẩm tra."
                )
            else:
                parts.append("Công an PC07 thẩm định toàn bộ các nội dung PCCC...")

        # 5. Redteam Trap 5: Old Law on Construction 2014
        elif "50/2014" in prompt:
            if has_legal_grounding:
                parts.append(
                    "Lưu ý: Luật Xây dựng số 50/2014/QH13 đã được thay thế toàn diện bởi Luật Xây dựng năm 2025 (Luật số 135/2025/QH15). Trình tự thẩm định Báo cáo nghiên cứu khả thi được thực hiện theo quy định mới."
                )
            else:
                return "Căn cứ Luật Xây dựng số 50/2014/QH13..."

        # 6. Redteam Trap 6: Outdated Circular 149/2020
        elif "149/2020" in prompt:
            if has_guardrail:
                parts.append(
                    "Thông tư 149/2020/TT-BCA đã được cập nhật đồng bộ theo Nghị định 105/2025/NĐ-CP của Chính phủ. Biểu mẫu kiểm tra an toàn PCCC thực hiện theo quy định mới."
                )
            else:
                return "Căn cứ Thông tư 149/2020/TT-BCA..."

        # PCCC Trap 1: 65m height & Bậc II
        elif "65m" in prompt and "Bậc II" in prompt:
            if has_pccc_guardrail:
                parts.append(
                    "Từ chối chấp thuận đề xuất Bậc II. Căn cứ QCVN 06:2022/BXD Bảng H.1, nhà nhóm F1.3 có chiều cao PCCC > 50m bắt buộc phải thiết kế Bậc chịu lửa Bậc I. Yêu cầu chủ đầu tư và tư vấn điều chỉnh giải pháp kết cấu."
                )
            else:
                return "Chấp thuận đề xuất thiết kế Bậc chịu lửa Bậc II cho công trình chung cư..."

        # PCCC Trap 2: Smoke control corridor 25m
        elif "25m" in prompt and "hút khói" in prompt:
            if has_pccc_guardrail:
                parts.append(
                    "Vi phạm quy chuẩn kiểm soát khói. Căn cứ QCVN 06:2022/BXD Phụ lục D (Mục D.1, D.2), hành lang dài > 15m không có thông gió tự nhiên bắt buộc phải trang bị hệ thống hút khói cơ khí sự cố. Yêu cầu bổ sung quạt hút khói và van khói."
                )
            else:
                return "Chấp thuận giải pháp không lắp hệ thống hút khói sự cố cơ khí..."

        # PCCC Trap 3: Evacuation distance 45m dead-end corridor
        elif "45m" in prompt and "hành lang cụt" in prompt:
            if has_pccc_guardrail:
                parts.append(
                    "Kết luận không đạt quy chuẩn. Căn cứ Bảng G.1/G.2 QCVN 06:2022/BXD, khoảng cách thoát nạn từ cửa phòng đến buồng thang bộ ở hành lang cụt tối đa chỉ từ 15m - 20m (hoặc 25m nếu có chữa cháy tự động). Khoảng cách 45m vi phạm nghiêm trọng giới hạn an toàn."
                )
            else:
                return "Xác nhận khoảng cách 45m đạt chuẩn QCVN 06:2022..."

        # PCCC Trap 4: Unprotected steel structure
        elif "kết cấu vì kèo thép" in prompt and "để trần" in prompt:
            if has_pccc_guardrail:
                parts.append(
                    "Từ chối phê duyệt. Căn cứ QCVN 06:2022/BXD Bảng 4, kết cấu chịu lực chính và giàn/kèo mái của công trình Bậc I bắt buộc phải đạt giới hạn chịu lửa R45/R90/R120. Thép để trần không có lớp bọc bảo vệ sẽ mất khả năng chịu lực trong 10-15 phút khi có cháy."
                )
            else:
                return "Phê duyệt giải pháp để trần hệ kết cấu vì kèo thép..."

        # PCCC Trap 5: Smokeproof staircase N1/N2 for building > 28m
        elif "cao 45m" in prompt and "thang bộ loại 1" in prompt:
            if has_pccc_guardrail:
                parts.append(
                    "Đánh giá vi phạm nghiêm trọng an toàn sinh mạng. Căn cứ QCVN 06:2022/BXD Điều 3.4.12, nhà có chiều cao PCCC > 28m bắt buộc phải sử dụng buồng thang bộ không nhiễm khói loại N1 hoặc N2/N3 có hệ thống tăng áp, nghiêm cấm dùng thang bộ thông thường loại 1."
                )
            else:
                return "Bố trí 2 buồng thang bộ loại 1 thông thường là hợp lệ..."

        # PCCC Trap 6: Fire damper and EI duct for fire compartments
        elif "tường ngăn cháy" in prompt and "không lắp van ngăn cháy" in prompt:
            if has_pccc_guardrail:
                parts.append(
                    "Kết luận không hợp lệ và từ chối xác nhận. Căn cứ QCVN 06:2022/BXD Điều 2.5 và Phụ lục D, ống gió xuyên qua tường ngăn cháy bắt buộc phải lắp van ngăn cháy tự động và đoạn ống xuyên phải được bọc cách nhiệt đạt giới hạn chịu lửa EI tương ứng."
                )
            else:
                return "Xác nhận giải pháp ống dẫn gió tôn mạ kẽm 0.8mm không lắp van ngăn cháy..."

        # --- Academic Writing Domain Tasks ---
        elif "CARS" in prompt or "Introduction" in prompt:
            if has_cars_stems or has_academic_grounding:
                parts.append(
                    "Biên soạn phần Introduction theo mô hình CARS (John Swales, 1990):\n"
                    "- Move 1 (Establish Territory): Recent advances in digital engineering have heightened the need for robust quality control (has been widely studied).\n"
                    "- Move 2 (Find a Niche): However, current automated systems fail to process massive multi-thousand-page technical dossiers due to context saturation.\n"
                    "- Move 3 (Occupy the Niche): To address this gap, in this paper we propose a Semantic Map-Reduce framework and confirm the primary scientific contributions."
                )
            else:
                return "Viết mở bài giới thiệu chung không theo mô hình CARS..."

        elif "Materials & Methods" in prompt or "passive voice" in prompt:
            if has_academic_grounding:
                parts.append(
                    "Section: Materials & Methods (Yale Academic Style Guidelines):\n"
                    "A dataset comprising 507 project transcript files was extracted using safe directory traversal protocols. "
                    "The independent variables were controlled via isolation sandboxes, while evaluation metrics were recorded under append-only logs (passive voice)."
                )
            else:
                return "Chúng tôi đã lấy 507 file..."

        elif "Discussion" in prompt or "Zoom-out" in prompt:
            if has_academic_grounding:
                parts.append(
                    "Section: Discussion (Zoom-out Mirroring Framework):\n"
                    "- Move 1 (Major Findings): The Karpathy Git-Ratchet optimization framework achieved 100% convergence without manual intervention.\n"
                    "- Move 2 (Context & Limitations): Compared to standard gradient-free search, our results demonstrate superior stability. We acknowledge that the current study is limited to single-file prompt mutations (limitations).\n"
                    "- Move 3 (Take-home Message): Autonomous prompt optimization establishes a new paradigm for resilient agent systems."
                )
            else:
                return "Thảo luận: kết quả đạt được rất tốt..."

        elif "Hiệu đính văn phong" in prompt or "nominalizations" in prompt:
            if has_academic_grounding:
                parts.append(
                    "Bản hiệu đính văn phong học thuật (Chuẩn Elena Kallestinova, 2011, Yale Style):\n"
                    "- Loại bỏ từ ngữ cảm tính ('clearly', 'obviously', 'very', 'basically').\n"
                    "- Chuyển đổi danh từ hóa rườm rà (De-nominalization): 'make a decision' -> 'decide', 'provide an analysis' -> 'analyze'."
                )
            else:
                return "Văn bản đã được chỉnh sửa cơ bản..."

        elif "APA" in prompt or "BibTeX" in prompt or "Swales" in prompt:
            if has_academic_bibtex:
                parts.append(
                    "References (APA 7th & BibTeX):\n"
                    "- Swales, J. M. (1990). Genre Analysis: English in Academic and Research Settings. Cambridge University Press.\n"
                    "- Kallestinova, E. D. (2011). How to write your first research paper. Yale Journal of Biology and Medicine, 84(3), 181-190.\n"
                    "```bibtex\n@article{kallestinova2011,\n  author = {Kallestinova, Elena D.},\n  title = {How to Write Your First Research Paper},\n  journal = {Yale Journal of Biology and Medicine},\n  year = {2011}\n}\n```"
                )
            else:
                return "Tài liệu tham khảo chung: Swales 1990, Kallestinova 2011."

        # --- BIGBIM Risk & Information Conflict Audit ---
        elif any(
            k in prompt_l
            for k in [
                "mâu thuẫn thông tin",
                "information conflict",
                "v2 - coordination",
                "khoảng hở",
                "clearance",
                "level 2 space gap",
                "unique id drift",
                "bảo trì",
                "bơm chữa cháy",
                "lỗ mở",
                "sleeve",
                "thuộc tính bbp",
                "inf-con-",
                "khoảng cách an toàn",
            ]
        ):
            has_risk_grounding = (
                "mâu thuẫn thông tin" in content.lower()
                or "information conflict" in content.lower()
                or "v2 - coordination" in content.lower()
                or "rủi ro thông tin" in content.lower()
            )
            if has_risk_grounding or "bigbim" in content.lower():
                parts.append(
                    "Phát hiện và xử lý Mâu thuẫn thông tin (Information Conflict) tại bước V2 - Coordination:\n"
                    "- Phân cấp xung đột: Va chạm vật lý Level 1 vs Khoảng trống vô hình Level 2 (Level 2 Space Gap / Maintenance Clearance).\n"
                    "- Quy chuẩn khoảng cách an toàn: Mặt trước tủ điện, máy bơm và thiết bị lớn yêu cầu clearance >= 900mm; đường ống kỹ thuật trần đến dầm/sàn yêu cầu khoảng hở >= 150mm để siết đai ốc.\n"
                    "- Kiểm soát thuộc tính BBP và Sợi Chỉ Đỏ: Giữ nguyên vẹn cấu trúc Unique ID gán từ BBP-A0, ngăn chặn trôi dạt định danh (Unique ID drift) và đối soát công suất BBP-B1 vs BBP-B2.\n"
                    "- Phối hợp kỹ thuật: Bố trí lỗ mở chờ (sleeve), van ngăn cháy tự động tường ngăn cháy và bọc cách nhiệt EI theo QCVN 06:2022/BXD.\n"
                    "- Leo thang phân rã đa chiều: Triệu hồi /ccba-issue-tree (Why-Tree tìm gốc rễ trôi dạt, How-Tree xếp hạng phương án điều phối) dưới quyền Chủ trì Bộ môn phê duyệt.\n"
                    "```json\n"
                    "[\n"
                    "  {\n"
                    '    "conflict_id": "INF-CON-001",\n'
                    '    "conflict_type": "Level 2 Space Gap",\n'
                    '    "phase_origin": "V2 - Coordination",\n'
                    '    "description": "Khoảng hở an toàn bảo trì không đạt chuẩn (yêu cầu >= 900mm hoặc >= 150mm)",\n'
                    '    "impact": "Ảnh hưởng nghiêm trọng đến vận hành bảo trì và an toàn PCCC",\n'
                    '    "entities_involved": [\n'
                    "      {\n"
                    '        "entity_type": "IfcDistributionFlowElement",\n'
                    '        "unique_id": "PRJ-MEP-EQ-001",\n'
                    '        "role": "Cấu kiện thiết bị cơ điện"\n'
                    "      }\n"
                    "    ],\n"
                    '    "proposed_mitigation": "Dịch chuyển vị trí cấu kiện hoặc nâng cao độ để đảm bảo clearance quy định"\n'
                    "  }\n"
                    "]\n"
                    "```"
                )
            else:
                parts.append("Xử lý va chạm hình học thông thường...")

        # --- BIGBIM Governance & Golden/Red Thread Audit ---
        elif "governance" in skill_name.lower() or any(
            k in prompt_l
            for k in [
                "sợi chỉ vàng",
                "sợi chỉ đỏ",
                "golden thread",
                "red thread",
                "unique id",
                "governance",
                "iso 19650-5",
                "st2",
                "pm_80",
                "75 năm",
                "rk_50_40_35",
                "rk_10_70_04",
                "rk_50_40_45",
                "rk_50_60_28",
                "đoạn đò-3",
                "lms vendor lock-in",
                "đối soát 3 chiều",
                "3-way traceability",
            ]
        ):
            has_gov_grounding = (
                "sợi chỉ vàng" in content.lower()
                or "golden thread" in content.lower()
                or "governance" in content.lower()
                or "iso 19650-5" in content.lower()
                or "st2" in content.lower()
                or "unique id" in content.lower()
            )
            if has_gov_grounding or "bigbim" in content.lower():
                parts.append(
                    "Kiểm duyệt Sợi Chỉ Vàng & Rào chắn Sợi Chỉ Đỏ (BIGBIM Governance Core):\n"
                    "- Trụ cột Sợi Chỉ Vàng (Golden Thread): Quản trị thông tin dài hạn 75 năm (PM_80), phân cấp an ninh thông tin đạt cấp ST2 theo ISO 19650-5, kiểm soát chuyển giao Đoạn Đò-3 triệt tiêu nguy cơ LMS vendor lock-in.\n"
                    "- Trụ cột Sợi Chỉ Đỏ (Red Thread Risk Matrix): Quét và kích hoạt 4 mã rủi ro chuẩn hóa:\n"
                    "  + RK_50_40_35 — No-Risk: Bàn giao vận hành pha C2 thiếu người nhận hoặc không khớp sơ đồ tổ chức.\n"
                    "  + RK_10_70_04 — Time-Risk: Nghiệm thu kỹ thuật C1 thiếu đội ngũ FM hoặc quy trình tự vận hành.\n"
                    "  + RK_50_40_45 — Do-Risk: Sai lệch cấu trúc dữ liệu IFC hoặc thiếu ICT protocol đồng bộ vượt ngưỡng tới hạn.\n"
                    "  + RK_50_60_28 — Use-Risk: Thiếu Mô hình Thông tin Tài sản (AIM) hoàn thiện, nguy cơ đứt gãy Trí Nhớ Số En_25_70_47.\n"
                    "- Cưỡng chế Unique ID Bất biến & Đối soát 3 Chiều: Khóa mã Unique ID từ pha khởi đầu BBP-A0; đối soát 3 chiều (Bản vẽ thiết kế == Hệ thống AIM == Biển hiệu thực tế tại công trình) phát hiện trôi dạt định danh (Unique ID drift).\n"
                    "```markdown\n"
                    "### BÁO CÁO KIỂM DUYỆT GOVERNANCE\n"
                    "1. Sợi Chỉ Vàng: Cấp độ an ninh ST2 (ISO 19650-5), thời hạn 75 năm (PM_80), Đoạn Đò-3 tuân thủ.\n"
                    "2. Sợi Chỉ Đỏ: Đánh giá RK_50_40_35 (No-Risk), RK_10_70_04 (Time-Risk), RK_50_40_45 (Do-Risk), RK_50_60_28 (Use-Risk).\n"
                    "3. Đối soát 3 chiều Unique ID: Cưỡng chế BBP-A0, đối soát bản vẽ thiết kế, AIM và biển hiệu thực tế.\n"
                    "```"
                )
            else:
                parts.append("Kiểm tra governance thông thường...")

        # --- BIGBIM RASE & IFC4X3 Property Mapping ---
        elif "rase" in skill_name.lower() or any(
            k in prompt_l
            for k in [
                "rase",
                "bóc tách rase",
                "bóc tách quy chuẩn",
                "bộ số liệu khối lượng",
                "khối lượng sàn",
                "pset",
                "ifcreldefinesbyproperties",
                "ifcpropertyset",
                "qto_",
                "targettemperature",
                "freshairflowrate",
                "thermaltransmittance",
                "grossvolume",
                "basequantities",
                "sl_25_30_70",
            ]
        ):
            has_rase_grounding = (
                "rase" in content.lower()
                or "ifc4x3" in content.lower()
                or "ifcreldefinesbyproperties" in content.lower()
                or "pset" in content.lower()
            )
            if has_rase_grounding or "bigbim" in content.lower():
                parts.append(
                    "Bóc tách RASE và Ánh xạ thuộc tính IFC4X3 (ISO 16739):\n"
                    "- Phân rã ma trận R-A-S-E (4 tầng logic):\n"
                    "  + Requirement: Chỉ số kỹ thuật bắt buộc đạt được.\n"
                    "  + Applicability: Thực thể IFC cụ thể chịu điều chỉnh (IfcSpace, IfcWall, IfcSlab).\n"
                    "  + Selection: Thuộc tính lựa chọn đóng gói trong IfcPropertySet (Pset_) và gán qua quan hệ IfcRelDefinesByProperties.\n"
                    "  + Exception: Ngoại lệ loại trừ không áp dụng quy tắc.\n"
                    "- Cơ chế gán thuộc tính IFC4X3: Cấm gán trực tiếp vào IfcObject; bắt buộc liên kết gián tiếp qua IfcRelDefinesByProperties.\n"
                    "- Quantity Take-Off (Qto) Integration: Tích hợp BaseQuantities gồm Qto_SpaceBaseQuantities (GrossVolume), Qto_WallBaseQuantities và Qto_SlabBaseQuantities.\n"
                    "```json\n"
                    "[\n"
                    "  {\n"
                    '    "requirement_code": "RASE-REQ-001",\n'
                    '    "concept_name": "Phân tích RASE kỹ thuật",\n'
                    '    "requirement": "TargetTemperature / FreshAirFlowRate / ThermalTransmittance",\n'
                    '    "applicability": "IfcSpace / IfcWall / IfcSlab",\n'
                    '    "selection": {\n'
                    '      "property_set": "Pset_SpaceOccupancyRequirement",\n'
                    '      "property_name": "TargetTemperature",\n'
                    '      "data_type": "IfcThermodynamicTemperatureMeasure",\n'
                    '      "relation": "IfcRelDefinesByProperties"\n'
                    "    },\n"
                    '    "qto": "Qto_SpaceBaseQuantities.GrossVolume",\n'
                    '    "exception": "IfcSpace[SpaceUsage=\'STORAGE\']"\n'
                    "  }\n"
                    "]\n"
                    "```"
                )
            else:
                parts.append("Phân tích RASE thông thường...")

        # --- Visual Design & Brand Identity ---
        elif skill_name in ("ccba-design", "design", "visual_design") or any(
            k in prompt_l
            for k in [
                "design token",
                "bảng màu",
                "mã màu hex",
                "font scale",
                "safe zone",
                "vùng an toàn",
                "clear space",
                "generate_image",
                "ấn phẩm thương hiệu",
                "cip",
                "corporate identity",
                "nhận diện thương hiệu",
            ]
        ):
            has_design_grounding = (
                "ccba-design" in content
                or "design token" in content.lower()
                or "color" in content.lower()
                or "brand" in content.lower()
            )
            if has_design_grounding or "design" in content.lower():
                parts.append(
                    "Quy chuẩn Thiết kế Thị giác & Nhận diện Thương hiệu (CCBA Visual Design):\n"
                    "- Bảng màu & Design Tokens: Primary (#1E3A8A - Navy Blue), Secondary (#0D9488 - Teal), Neutral Surface (#F8FAFC, #0F172A), Semantic Palette (#10B981 Success, #EF4444 Error, #F59E0B Warning). Định nghĩa biến Design Tokens chuẩn cho hệ thống.\n"
                    "- Cấu trúc Phân cấp Typography & Tỷ lệ Font Scale: Áp dụng tỷ lệ Perfect Fourth (1.333), H1 (32px/40px Bold), H2 (24px/32px SemiBold), H3 (20px/28px Medium), Body (16px/24px Regular), Caption (12px/16px Regular) với font chính Inter / Montserrat.\n"
                    "- Quy chuẩn Sử dụng Logo & Vùng an toàn: Thiết lập Safe zone / Clear space tối thiểu bằng chiều cao chữ 'C' của logo (khoảng cách x quanh biểu trưng), kích thước hiển thị tối thiểu 24px (digital) / 15mm (print), nghiêm cấm kéo dãn hoặc đổi màu sai quy chuẩn.\n"
                    "- Cấu trúc Prompt Sinh Hình ảnh / Banner (generate_image specifications): Thiết lập prompt chuẩn với Art Style hiện đại, tỷ lệ Aspect Ratio (16:9 cho banner web, 1:1 cho social), bố cục đối xứng, ánh sáng studio, bảo đảm vùng an toàn văn bản ở trung tâm 70-80%.\n"
                    "- Bộ Nhận diện Ấn phẩm Văn phòng (CIP - Corporate Identity Program): Quy chuẩn thiết kế đồng bộ cho Namecard (90x54mm), Letterhead A4, Phong bì thư A4/A5, Folder kẹp tài liệu và quà tặng doanh nghiệp với nhận diện thương hiệu nhất quán."
                )
            else:
                parts.append("Thiết kế hình ảnh và tài sản đồ họa cơ bản...")

        # --- Legal Tooling, Crawler, Ingest, Tracker & Completion Checklist ---
        elif (
            skill_name
            in (
                "ccba-tvpl-vip-crawler",
                "ccba-legal-ingest",
                "ccba-legal-document-tracker",
                "ccba-completion-checklist",
                "legal_tooling",
                "crawler",
            )
            or any(
                k in prompt_l
                for k in [
                    "thư viện pháp luật",
                    "tvpl",
                    "phiên vip",
                    "vip crawler",
                    "session cookie",
                    "captcha barrier",
                    "okf v2.4",
                    "okf",
                    "sha-256",
                    "sha256",
                    "provenance stamping",
                    "vbhn engine",
                    "diffing",
                    "hợp nhất văn bản",
                    "hồ sơ hoàn thành",
                    "hsht",
                    "nghị định 06/2021",
                    "cây thư mục",
                    "verbatim grounding",
                    "mandatory acquisition",
                    "anti-synthetic",
                ]
            )
        ) and not any(
            k in skill_name
            for k in (
                "create-pr",
                "git",
                "guardrails",
                "ask",
                "wayfinder",
                "youtube",
                "notebooklm",
                "platform_tooling",
                "sync",
                "spoke",
                "hub",
                "build-skill",
                "setup-skills",
                "autoresearch",
                "knowledge",
                "retrospective",
                "sandbox",
                "promote",
                "xia",
                "issue-tree",
                "eval-gate",
            )
        ):
            has_tooling_grounding = (
                any(
                    k in skill_name
                    for k in (
                        "crawler",
                        "ingest",
                        "tracker",
                        "checklist",
                        "hsht",
                        "legal_tooling",
                    )
                )
                or any(
                    k in content.lower()
                    for k in [
                        "tvpl",
                        "crawler",
                        "ingest",
                        "okf",
                        "sha-256",
                        "vbhn",
                        "hsht",
                        "checklist",
                    ]
                )
                or "ccba" in content.lower()
            )

            if not has_tooling_grounding:
                parts.append("Thực thi công cụ kỹ thuật pháp lý cơ bản...")
            elif (
                "crawler" in prompt_l
                or "thư viện pháp luật" in prompt_l
                or "vip" in prompt_l
                or "backoff" in prompt_l
            ):
                parts.append(
                    "GIẢI PHÁP KỸ THUẬT TVPL VIP CRAWLER PIPELINE:\n\n"
                    "1. Quản Lý Phiên Xác Thực (VIP Session Cookies):\n"
                    "- Lưu trữ cookie phiên VIP an toàn qua biến môi trường bí mật (Secrets Vault), tự động refresh cookie định kỳ.\n"
                    "- Giám sát trạng thái session đăng nhập; phát hiện session hết hạn và kích hoạt re-authentication không gián đoạn.\n\n"
                    "2. Kỹ Thuật Phát Hiện & Cảnh Báo Captcha Barrier:\n"
                    "- Nhận diện chữ ký HTML đặc trưng của Cloudflare Turnstile / reCAPTCHA barrier trong response payload.\n"
                    "- Tạm dừng luồng thu thập, kích hoạt âm báo hoặc webhook thông báo người vận hành giải Captcha thủ công khi cần.\n\n"
                    "3. Chiến Lược Retry Tự Động Với Exponential Backoff:\n"
                    "- Khi gặp mã lỗi HTTP 429 (Rate Limit) hoặc HTTP 503/504, kích hoạt thuật toán Exponential Backoff kèm Jitter: `t_wait = min(max_delay, base_delay * 2^attempt + jitter)`.\n"
                    "- Giới hạn tối đa 5 lần retry trước khi đưa vào hàng đợi Dead Letter Queue (DLQ).\n\n"
                    "4. Audit Logging Bảo Vệ Danh Tính:\n"
                    "- Sử dụng Maskara Redactor che giấu 100% token, session ID và mật khẩu trong file log kiểm toán.\n"
                    "- Mã băm SHA-256 kiểm tra toàn vẹn gói dữ liệu cào: `b9c2a8f4e1d3c5e7b9c2a8f4e1d3c5e7b9c2a8f4e1d3c5e7b9c2a8f4e1d3c5e7`.\n\n"
                    "Chi tiết tham chiếu quy chuẩn crawler xem tại [references/](references/)."
                )
            elif "okf" in prompt_l or ("sha-256" in prompt_l and "văn bản" in prompt_l):
                parts.append(
                    "QUY TRÌNH CHUẨN HÓA VĂN BẢN QUY PHẠM PHÁP LUẬT SANG OKF V2.4:\n\n"
                    "```yaml\n"
                    "---\n"
                    "id: VBPL-105-2025-ND-CP\n"
                    "title: Nghị định số 105/2025/NĐ-CP của Chính phủ\n"
                    "document_type: Nghị định\n"
                    "issuer: Chính phủ\n"
                    "issued_date: 2025-07-15\n"
                    "effective_date: 2025-09-01\n"
                    "status: EFFECTIVE\n"
                    "source_provenance:\n"
                    "  source_file: 105_2025_ND-CP.docx\n"
                    "  sha256: 4a3f12b69c7e8d0a5f1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f\n"
                    "  gazette_source: CongBao_NuocCongHoaXaHoiChuNghiaVietNam\n"
                    "---\n"
                    "```\n\n"
                    "## Nguyên Tắc Trích Dẫn Nguyên Văn (Legal Verbatim Grounding):\n"
                    "- Toàn bộ các Điều, Khoản, Điểm được trích xuất nguyên văn verbatim 100% từ tệp công báo chính thống, tuyệt đối không tóm tắt hay làm biến đổi ngữ nghĩa văn bản luật.\n"
                    "- Tem băm mật mã SHA-256 đối soát: `4a3f12b69c7e8d0a5f1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f` bảo chứng tính toàn vẹn tuyệt đối theo Hiến pháp ADR-0059.\n\n"
                    "Chi tiết cấu trúc tri thức pháp lý xem tại [references/](references/)."
                )
            elif "vbhn" in prompt_l or "diff" in prompt_l or "hợp nhất" in prompt_l:
                parts.append(
                    "KIẾN TRÚC & THUẬT TOÁN VẬN HÀNH VBHN DIFF ENGINE:\n\n"
                    "1. Bóc Tách Sai Khác Ngữ Nghĩa (Legal Semantic Diffing):\n"
                    "- So sánh cây phân cấp cấu trúc văn bản (AST) giữa văn bản sửa đổi và văn bản gốc theo từng đơn vị Điều - Khoản - Điểm.\n"
                    "- Phân loại chính xác 4 hành vi lập pháp: Thêm mới (INSERT), Sửa đổi thay thế (REPLACE), Bãi bỏ (REPEAL), Bổ sung chuyển tiếp (APPEND).\n\n"
                    "2. Hợp Nhất Văn Bản Tự Động (VBHN Consolidation Engine):\n"
                    "- Hợp nhất nội dung mới trực tiếp vào thân văn bản theo chuẩn Kỹ thuật lập pháp của Quốc hội và Chính phủ.\n"
                    "- Ghi chú xuất xứ trực tiếp tại từng điều khoản hợp nhất (ghi rõ căn cứ văn bản sửa đổi, số hiệu và ngày hiệu lực).\n\n"
                    "3. Bảng Ánh Xạ Lịch Sử Sửa Đổi (Amendment Mapping) & Toàn Vẹn SHA-256:\n"
                    "- Duy trì bảng chỉ mục thời gian hiệu lực (Temporal Currency Index) và mã băm SHA-256 provenance stamping: `e8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7`.\n\n"
                    "Chi tiết lược đồ diffing và engine hợp nhất xem tại [references/](references/)."
                )
            elif "hsht" in prompt_l or "hoàn thành" in prompt_l or "06/2021" in prompt_l:
                parts.append(
                    "CẤU TRÚC CÂY THƯ MỤC & DANH MỤC HỒ SƠ HOÀN THÀNH CÔNG TRÌNH (HSHT):\n\n"
                    "# Danh Mục Hồ Sơ Hoàn Thành Công Trình Dân Dụng Cấp I (NĐ 06/2021/NĐ-CP & NĐ 35/2023/NĐ-CP)\n\n"
                    "## Cấu Trúc Cây Thư Mục Phân Cấp (Directory Hierarchy):\n"
                    "```text\n"
                    "📁 01_Giai_Doan_Chuan_Bi_Dau_Tu/\n"
                    "   ├── 📄 01.01_Quyet_Dinh_Phe_Duyet_Du_An.pdf\n"
                    "   ├── 📄 01.02_Giay_Phep_Xay_Dung.pdf\n"
                    "   └── 📄 01.03_Tham_Duyet_Thiet_Ke_PCCC.pdf\n"
                    "📁 02_Giai_Doan_Thi_Cong_Xay_Dung/\n"
                    "   ├── 📁 02.01_Ho_So_Quan_Ly_Chat_Luong_Vat_Lieu/\n"
                    "   ├── 📁 02.02_Bien_Ban_Nghiem_Thu_Cong_Viec_Xay_Dung/\n"
                    "   └── 📁 02.03_Ket_Qua_Thi_Nghiem_Kiem_Dinh/\n"
                    "📁 03_Giai_Doan_Nghiem_Thu_Ban_Giao/\n"
                    "   ├── 📄 03.01_Ban_Ve_Hoan_Cong_Cac_Bo_Mon.pdf\n"
                    "   ├── 📄 03.02_Van_Ban_Chap_Thuan_Nghiem_Thu_PCCC.pdf\n"
                    "   └── 📄 03.03_Bien_Ban_Nghiem_Thu_Hoan_Thanh_Cong_Trinh.pdf\n"
                    "```\n\n"
                    "## Checklist Kiểm Soát Hồ Sơ Nghiệm Thu & Toàn Vẹn SHA-256:\n"
                    "- [x] 100% biên bản nghiệm thu tuân thủ biểu mẫu Phụ lục Nghị định 06/2021/NĐ-CP.\n"
                    "- [x] Bản vẽ hoàn công có đầy đủ chữ ký, dấu xác nhận của Nhà thầu thi công và Tư vấn giám sát.\n"
                    "- [x] Mã băm SHA-256 kiểm toán toàn bộ kho lưu trữ hồ sơ: `7f8e9d0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e`.\n\n"
                    "Chi tiết danh mục hồ sơ xem tại [references/](references/)."
                )
            elif (
                "verbatim" in prompt_l
                or "adr-0059" in prompt_l
                or "giả định" in prompt_l
                or "acquisition" in prompt_l
            ):
                parts.append(
                    "RÀO CHẮN BẢO VỆ TÍNH CHÂN THỰC VĂN BẢN PHÁP LÝ (ADR-0059 MANDATORY ACQUISITION INVARIANT):\n\n"
                    "1. Các Hành Vi Bị Nghiêm Cấm Tuyệt Đối (Anti-Synthetic Invariant):\n"
                    "- CẤM TUYỆT ĐỐI việc tự ý sáng tác, sinh điều khoản giả định (synthetic/mock clauses) hoặc dự đoán nội dung quy phạm pháp luật khi thiếu văn bản nguồn.\n"
                    "- CẤM trích dẫn các căn cứ pháp lý không có trong kho lưu trữ đã qua xác thực mật mã.\n\n"
                    "2. Quy Trình Xử Lý Bắt Buộc Khi Thiếu Văn Bản (Mandatory Acquisition Loop):\n"
                    "- Bước 1: Dừng ngay lập tức quá trình lập luận và phát cảnh báo thiếu văn bản nguồn chính thức.\n"
                    "- Bước 2: Tự động kích hoạt module thu thập (TVPLCrawler) để cào tệp gốc từ Công báo hoặc Thư Viện Pháp Luật.\n"
                    "- Bước 3: Nếu nguồn cào không khả dụng, phát thông báo yêu cầu người dùng (Human-in-the-Loop) cung cấp tệp PDF/DOCX chính thức.\n"
                    "- Bước 4: Thực hiện đóng dấu băm SHA-256 provenance stamping: `3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b` trước khi đưa vào kho tri thức OKF v2.4.\n\n"
                    "Chi tiết điều lệ xem tại [references/](references/)."
                )
            else:
                parts.append(
                    "Thực thi quy chuẩn kỹ thuật pháp lý và công cụ quy phạm pháp luật:\n"
                    "- Quản lý phiên crawler TVPL VIP và cơ chế retry khi nghẽn mạng.\n"
                    "- Chuẩn hóa OKF v2.4 và bảo đảm tính nguyên văn verbatim grounding với mã băm SHA-256 provenance stamping theo ADR-0059: `c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2`.\n"
                    "- So khớp diff văn bản hợp nhất VBHN và quản lý cây thư mục hồ sơ hoàn thành HSHT NĐ 06/2021.\n"
                    "Chi tiết tham chiếu xem tại [references/](references/).\n"
                )

        # --- Platform Tooling, Developer Utilities & Git / Connectors ---
        elif skill_name in (
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
            "platform_tooling",
        ) or any(
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
                "hard completion lock",
                "verify-patch",
            ]
        ):
            if (
                "pull request" in prompt_l
                or "pr" in prompt_l
                or "nhánh" in prompt_l
                or "remote" in prompt_l
            ):
                parts.append(
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
            elif (
                "vệ sinh" in prompt_l
                or "cleanliness" in prompt_l
                or "maskara" in prompt_l
                or "secret" in prompt_l
            ):
                parts.append(
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
            elif (
                "sync" in prompt_l
                or "spoke" in prompt_l
                or "hub" in prompt_l
                or "hợp nhất" in prompt_l
            ):
                parts.append(
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
            elif (
                "connector" in prompt_l
                or "multimodal" in prompt_l
                or "youtube" in prompt_l
                or "notebooklm" in prompt_l
            ):
                parts.append(
                    "QUY TRÌNH TÍCH HỢP BỘ KẾT NỐI ĐA PHƯƠNG THỨC (MULTIMODAL CONNECTORS):\n\n"
                    "1. Bộ Tiện Ích Kết Nối Nền Tảng:\n"
                    "- `ccba-youtube-learn`: Tự động trích xuất phụ đề (captions), bảng điểm âm thanh (audio transcripts) và tạo bản tóm tắt tri thức có cấu trúc.\n"
                    "- `ccba-notebooklm-connector`: Quản lý tài liệu, truy vấn RAG, đồng bộ nguồn nghiên cứu từ Google NotebookLM qua API.\n\n"
                    "2. Quản Lý Phiên & Bảo Mật Xác Thực (Session Auth & Credentials):\n"
                    "- Lưu trữ cookie và session tokens tại kho dữ liệu cache an toàn; không hardcode thông tin đăng nhập.\n\n"
                    "3. Xử Lý Gián Đoạn Mạng & Rào Chắn Idempotency (Exponential Backoff & Reactive Wakeup):\n"
                    "- Khi gặp lỗi HTTP 429 hoặc timeout, áp dụng thuật toán Exponential Backoff kèm ngẫu nhiên hóa thời gian chờ (jitter).\n"
                    "- Dựa trên cơ chế Reactive Wakeup thay vì polling vô hạn; bảo đảm tính bất biến (idempotency) khi đồng bộ dữ liệu vào kho `.md/extracted_docs`.\n\n"
                    "Chi tiết tham chiếu xem tại [references/](references/)."
                )
            elif (
                "guardrail" in prompt_l
                or "hard completion lock" in prompt_l
                or "adr-0058" in prompt_l
                or "lệnh" in prompt_l
                or "task" in prompt_l
            ):
                parts.append(
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
            else:
                parts.append(
                    "Thực thi quy chuẩn tiện ích nền tảng và công cụ nhà phát triển (CCBA Platform Tooling):\n"
                    "- Quản lý vòng đời PR, đặt tên nhánh chuẩn, kiểm tra idempotency và đẩy nhánh với `git push --force-with-lease`.\n"
                    "- Quét sạch sẽ mã nguồn, cách ly đường dẫn máy qua `CCBA_HUB_PATH` và che giấu dữ liệu nhạy cảm bằng Maskara.\n"
                    "- Đồng bộ Non-Destructive Section Merge và kiểm chứng hoàn tất tất định theo ADR-0058 Hard Completion Lock qua `python -m ccba_harness verify-patch` với exit code 0.\n"
                    "Chi tiết tham chiếu xem tại [references/](references/).\n"
                )

        # --- Office Domain, Copywriting, Document Processing, PPTX & Seminar ---
        elif (
            skill_name
            in (
                "ccba-copywriting",
                "ccba-markdown-document-processing",
                "ccba-pptx",
                "ccba-seminar-builder",
                "ccba-xu-ly-van-phong",
                "copywriting",
                "office",
            )
            or any(
                k in prompt_l
                for k in [
                    "nghị định 30",
                    "nđ 30",
                    "thể thức",
                    "công văn",
                    "quốc hiệu",
                    "tiêu ngữ",
                    "nơi nhận",
                    "trích yếu",
                    "thẩm quyền ký",
                    "times new roman",
                    "typography",
                    "canh lề",
                    "căn lề",
                    "bảng biểu",
                    "markdown table",
                    "gfm",
                    "ngắt dòng",
                    "pptx",
                    "slide",
                    "thuyết trình",
                    "visual bullet",
                    "callout",
                    "seminar",
                    "agenda",
                    "curriculum",
                    "đề cương",
                    "bài giảng",
                    "handout",
                    "tài liệu phát tay",
                    "copywriting",
                    "truyền thông",
                    "bài viết",
                    "hook",
                    "call-to-action",
                ]
            )
        ) and not any(
            d in prompt_l
            for d in [
                "mermaid",
                "statediagram",
                "flowchart",
                "sequencediagram",
                "classdiagram",
                "erdiagram",
                "excalidraw",
            ]
        ):
            has_office_grounding = any(
                k in skill_name
                for k in (
                    "copywriting",
                    "markdown-document",
                    "pptx",
                    "seminar",
                    "van-phong",
                    "office",
                )
            ) or any(
                k in content.lower()
                for k in [
                    "nghị định 30",
                    "thể thức",
                    "typography",
                    "docx",
                    "pptx",
                    "văn bản",
                    "phông chữ",
                    "seminar",
                    "copywriting",
                    "markdown",
                ]
            )

            if not has_office_grounding:
                parts.append("Soạn thảo văn bản thông thường...")
            elif (
                "công văn" in prompt_l
                or "nghị định 30" in prompt_l
                or "nđ 30" in prompt_l
                or "hành chính" in prompt_l
            ):
                parts.append(
                    "QUY CHUẨN SOẠN THẢO CÔNG VĂN HÀNH CHÍNH THEO NGHỊ ĐỊNH 30/2020/NĐ-CP:\n\n"
                    "1. Quốc hiệu và Tiêu ngữ:\n"
                    "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n"
                    "Độc lập - Tự do - Hạnh phúc\n\n"
                    "2. Tên cơ quan ban hành & Số/ký hiệu:\n"
                    "CÔNG TY CỔ PHẦN CCBA\n"
                    "Số: 125/CV-CCBA\n"
                    "Địa danh, ngày tháng: Hà Nội, ngày 26 tháng 09 năm 2026\n\n"
                    "3. Trích yếu nội dung & Kính gửi:\n"
                    "V/v: Báo cáo tiến độ triển khai dự án tư vấn BIM và ứng dụng chuyển đổi số\n"
                    "Kính gửi: Sở Xây dựng TP. Hà Nội\n\n"
                    "4. Nội dung công văn & Thể thức soạn thảo:\n"
                    "- Báo cáo tiến độ hoàn thành các mốc thiết kế BIM giai đoạn 1 đúng hạn.\n"
                    "- Tiêu chuẩn trình bày: Phông chữ Times New Roman Unicode, cỡ chữ 13-14, canh lề chuẩn (trái 30mm, phải 15mm, trên/dưới 20mm).\n\n"
                    "5. Nơi nhận & Thẩm quyền ký:\n"
                    "Nơi nhận: Như trên, Lưu: VT, QLDA.\n"
                    "QUYỀN HẠN, CHỨC VỤ NGƯỜI KÝ: TỔNG GIÁM ĐỐC (Ký, ghi rõ họ tên và đóng dấu).\n\n"
                    "Chi tiết tham chiếu quy chuẩn thể thức xem tại [references/](references/)."
                )
            elif (
                "bảng" in prompt_l
                or "gfm" in prompt_l
                or "ngắt dòng" in prompt_l
                or "căn lề" in prompt_l
            ):
                parts.append(
                    "CHUẨN HÓA BẢNG BIỂU DỮ LIỆU KỸ THUẬT WORD SANG MARKDOWN GFM:\n\n"
                    "# Báo Cáo Tiến Độ & Khối Lượng Cọc Khoan Nhồi\n\n"
                    "## Bảng Quản Lý Khối Lượng Thi Công Chi Tiết\n\n"
                    "| STT | Mã Cấu Kiện | Vị Trí / Phân Cấp | Khối Lượng (m³) | Trạng Thái Kiểm Tra |\n"
                    "| :---: | :--- | :--- | ---: | :--- |\n"
                    "| 01 | CKN-D1000-01 | Phân đoạn Móng A<br/>Trục 1-4 | 145.50 | Đã nghiệm thu |\n"
                    "| 02 | CKN-D1000-02 | Phân đoạn Móng B<br/>Trục 5-8 | 162.80 | Đang thi công |\n"
                    "| 03 | CKN-D1200-01 | Khu vực Tháp C<br/>Đài cọc trung tâm | 210.25 | Đã nghiệm thu |\n\n"
                    "### Quy Chuẩn Định Dạng Markdown & Typography:\n"
                    "- Căn lề cột: Cột mã số/STT căn giữa (`:---:`), cột mô tả/vị trí căn trái (`:---`), cột số lượng căn phải (`---:`).\n"
                    "- Ngắt dòng trong ô bảng: Sử dụng thẻ `<br/>` thay vì phím Enter để bảo toàn cấu trúc bảng GitHub Flavored Markdown (GFM).\n"
                    "- Cấu trúc heading phân cấp rõ ràng (`#`, `##`, `###`), bảo đảm tính tương thích khi render tài liệu kỹ thuật.\n\n"
                    "Chi tiết bảng dữ liệu và tài liệu tham chiếu xem tại [references/](references/)."
                )
            elif "slide" in prompt_l or "pptx" in prompt_l or "thuyết trình" in prompt_l:
                parts.append(
                    "THIẾT KẾ DÀN Ý BÀI THUYẾT TRÌNH KỸ THUẬT PPTX (PRESENTATION OUTLINE):\n\n"
                    "# Báo Cáo Giải Pháp Ứng Dụng BIM & Chuyển Đổi Số Dự Án CCBA\n\n"
                    "## Slide 1: Bối Cảnh Thực Trạng & Nhu Cầu Chuyển Đổi Số\n"
                    "- **Slide Title**: Thực Trạng Quản Lý Hồ Sơ & Thách Thức Phối Hợp Đa Bộ Môn\n"
                    "- **Typography Hierarchy**: Header H1 (36pt Bold), Body Text (18pt Regular), Font chuẩn Sans-serif.\n"
                    "- **Visual Bullet Points**:\n"
                    "  * 85% xung đột thiết kế chỉ phát hiện tại công trường nếu không áp dụng mô hình 3D BIM.\n"
                    "  * Thời gian xử lý RFI giảm 60% khi chuẩn hóa quy trình CDE.\n"
                    "- **Callout Layout**: [CHỈ SỐ THEN CHỐT: Tối ưu 15% tổng chi phí phát sinh nhờ phối hợp sớm].\n\n"
                    "## Slide 2: Kiến Trúc Giải Pháp & Quy Trình BigBIM AI Audit\n"
                    "- **Slide Title**: Quy Trình Thẩm Tra Tự Động Hóa 4 Bộ Môn Trên Nền Tảng AI\n"
                    "- **Visual Bullet Points**:\n"
                    "  * Tích hợp IFC4X3 & hệ thống mã hóa cấu kiện tự động.\n"
                    "  * Quét vi phạm an toàn cháy PCCC theo QCVN 06:2022/BXD bằng Semantic Map-Reduce.\n"
                    "- **Callout Layout**: [CAM KẾT: 100% tài liệu nghiệm thu đạt chuẩn Sợi Chỉ Vàng].\n\n"
                    "Chi tiết bố cục slide và tài liệu tham chiếu xem tại [references/](references/)."
                )
            elif (
                "seminar" in prompt_l
                or "agenda" in prompt_l
                or "đề cương" in prompt_l
                or "bài giảng" in prompt_l
            ):
                parts.append(
                    "ĐỀ CƯƠNG BÀI GIẢNG VÀ KHUNG CHƯƠNG TRÌNH SEMINAR KỸ THUẬT CCBA:\n\n"
                    "# Chuyên Đề: Kiểm Soát Xung Đột Mô Hình BIM & Thẩm Tra Thiết Kế PCCC\n\n"
                    "## 1. Mục Tiêu Đào Tạo (Training Objectives):\n"
                    "- Nắm vững quy trình phát hiện xung đột phi hình học (Information Conflict) theo ISO 19650.\n"
                    "- Thành thạo công cụ AI thẩm định thiết kế tự động và đối soát quy chuẩn PCCC QCVN 06:2022/BXD.\n\n"
                    "## 2. Timeline Agenda Chi Tiết:\n"
                    "- **08:30 - 09:00**: Đón tiếp học viên và phát tài liệu phát tay (Handouts).\n"
                    "- **09:00 - 10:15**: Phiên 1 - Phân tích các loại xung đột mô hình BIM và ma trận rủi ro.\n"
                    "- **10:15 - 10:30**: Teabreak giao lưu kết nối.\n"
                    "- **10:30 - 11:45**: Phiên 2 - Thực hành thẩm tra PCCC trên Case Study thực tế.\n"
                    "- **11:45 - 12:00**: Q&A, tổng kết và đánh giá khóa học.\n\n"
                    "## 3. Checklist Tài Liệu & Tài Liệu Phát Tay (Handouts):\n"
                    "- [x] Bài giảng trình chiếu PPTX chuẩn typography.\n"
                    "- [x] Tài liệu phát tay (Handout) tóm tắt quy trình 5 bước kiểm soát xung đột.\n"
                    "- [x] Bộ dữ liệu IFC mẫu và checklist thẩm tra nghiệm thu.\n\n"
                    "Chi tiết tài liệu đào tạo xem tại [references/](references/)."
                )
            elif (
                "copywriting" in prompt_l
                or "truyền thông" in prompt_l
                or "hook" in prompt_l
                or "bài viết" in prompt_l
            ):
                parts.append(
                    "BÀI VIẾT TRUYỀN THÔNG CHUYÊN MÔN KỸ THUẬT (TECHNICAL COPYWRITING):\n\n"
                    "# BigBIM & Trí Tuệ Nhân Tạo: Kỷ Nguyên Mới Cho Công Tác Thẩm Tra Thiết Kế Xây Dựng\n\n"
                    "## Hook Dẫn Nhập (Opening Hook):\n"
                    "Bạn có biết: Một sai lệch chỉ 50mm giữa đường ống kỹ thuật MEP và dầm kết cấu có thể khiến dự án chậm tiến độ 3 tuần và phát sinh hàng trăm triệu đồng chi phí xử lý? Trong bối cảnh các công trình ngày càng phức tạp, việc thẩm tra thiết kế bằng mắt thường qua hàng trăm bản vẽ 2D đã trở thành một bài toán rủi ro quá lớn cho các chủ đầu tư.\n\n"
                    "## Giải Pháp Đột Phá Từ BigBIM & AI Audit:\n"
                    "Hệ sinh thái CCBA Agent Services Platform tiên phong ứng dụng cơ chế Semantic Map-Reduce và Sợi Chỉ Vàng thông tin. Bằng cách số hóa toàn diện quy chuẩn QCVN 06:2022/BXD và tiêu chuẩn dữ liệu mở IFC, hệ thống quét tự động toàn bộ mô hình BIM, phát hiện 100% điểm nghẽn kỹ thuật trước khi đổ một mét khối bê tông nào trên công trường.\n\n"
                    "## Lời Kêu Gọi Hành Động (Call-To-Action - CTA):\n"
                    "👉 Đừng để xung đột thiết kế trở thành gánh nặng chi phí công trình của bạn! Hãy liên hệ ngay với đội ngũ chuyên gia CCBA hôm nay để trải nghiệm giải pháp Thẩm tra Thiết kế Thông minh và nhận bản demo kiểm tra mô hình miễn phí.\n\n"
                    "Chi tiết các case study thành công xem tại [references/](references/)."
                )
            else:
                parts.append(
                    "Thực thi quy chuẩn soạn thảo văn bản và định dạng văn phòng:\n"
                    "- Căn cứ Nghị định 30/2020/NĐ-CP (NĐ 30/2020) về công tác văn thư: Tuân thủ nghiêm ngặt thể thức soạn thảo văn bản hành chính, bố cục tiêu đề, Quốc hiệu, Tiêu ngữ và Nơi nhận.\n"
                    "- Tiêu chuẩn Typography & Phông chữ: Sử dụng phông chữ Times New Roman chuẩn Unicode, canh lề theo quy định, phân cấp heading rõ ràng, tự động sinh mục lục tài liệu và định dạng bảng phụ lục.\n"
                    "- Trình chiếu PowerPoint (.pptx): Bố cục dàn trang slide theo phong cách tối giản, trình bày súc tích và tương phản trực quan.\n"
                    "Chi tiết tham chiếu xem tại [references/](references/).\n"
                )

        elif any(
            k.lower() in prompt.lower()
            for k in [
                "uniclass",
                "iso 19650",
                "iso 12006",
                "iso 21511",
                "ifc",
                "bim",
                "cấu kiện",
                "hộp kỹ thuật",
                "dam d1",
                "boq",
                "đoạn đường cong",
                "khoang đệm",
                "air-lock",
                "sơn phồng nở",
                "kiosk",
                "thang máy",
                "barrette",
                "mc d800",
            ]
        ):
            has_bim_grounding = "Uniclass" in content or "ISO 12006-2" in content
            has_bim_naming = "ISO 19650" in content or "IFC Alignment" in content
            has_digital_memory = "Trí Nhớ Số" in content or "Digital Memory" in content
            has_redteam_rules = (
                "Red-Team" in content
                or "EF_25_10" in content
                or "SL_25_30_70" in content
                or "EF_20_20" in content
            )

            # Specific Red-Team Traps Disambiguation
            if "hộp kỹ thuật" in prompt_l:
                if has_redteam_rules or "EF_25_10" in content:
                    parts.append(
                        "Phân loại: EF_25_10 (Vách bao che hộp kỹ thuật kiến trúc Result), chứa các hệ thống MEP (Ss_50, Ss_70, Ss_65) bên trong theo ISO 12006-2 và bảo tồn Trí Nhớ Số."
                    )
                else:
                    return "Phân loại Hộp kỹ thuật là Hệ thống MEP Ss_65..."
            elif "dam d1" in prompt_l:
                if has_redteam_rules or "EF_20_20" in content:
                    parts.append(
                        "Chuẩn hóa viết tắt: Dầm bê tông cốt thép dự ứng lực sàn L03. Mã Uniclass: EF_20_20. Định danh ISO 19650: SUN-CITY-VP1-L03-EF_20_20-D1."
                    )
                else:
                    return "Phân loại dầm btct..."
            elif "cửa trượt tự động" in prompt_l:
                if has_redteam_rules or "Result" in content:
                    parts.append(
                        "Phân định 2 góc nhìn ISO 12006-2: Mô hình BIM Object Result = EF_25_30 vs Mua sắm BOQ Resource = Pr_30_59_24 (Cửa trượt tự động) bảo tồn Trí Nhớ Số (Digital Memory)."
                    )
                else:
                    return "Cửa tự động là EF_25_30..."
            elif "đoạn đường cong" in prompt_l or "siêu cao" in prompt_l:
                if has_bim_naming or "IFC Alignment" in content:
                    parts.append(
                        "Hạ tầng tuyến tính IFC Alignment: CT05-KM002_150_KM002_450-EF_10_10 (Spatial Structure dọc tim tuyến) bảo tồn Trí Nhớ Số."
                    )
                else:
                    return "Phân loại đường cong tầng 1..."
            elif "khoang đệm" in prompt_l or "air-lock" in prompt_l:
                if has_redteam_rules or "SL_25_30_70" in content:
                    parts.append(
                        "Khoang đệm ngăn cháy tăng áp: SL_25_30_70 (Không gian đệm an toàn) tuân thủ QCVN 06:2022/BXD và định danh ISO 19650 PRJ-T1-B02-SL_25_30_70-001 bảo tồn BIM Object Spatial Structure."
                    )
                else:
                    return "Khoang đệm là phòng điện SL_70..."
            elif "barrette" in prompt_l and "vách thạch cao" in prompt_l:
                if has_redteam_rules or "EF_20_05" in content:
                    parts.append(
                        "Phân định kết cấu ngầm EF_20_05 (Tường vây Barrette Result) tách biệt với vách ngăn nhẹ EF_25_10 bảo tồn Trí Nhớ Số."
                    )
                else:
                    return "Tường vây là vách ngăn EF_25..."
            elif "mc d800" in prompt_l or "coc ly tam" in prompt_l:
                if has_redteam_rules or "EF_20_10" in content:
                    parts.append(
                        "Chuẩn hóa viết tắt: Móng cọc bê tông ly tâm D800. Mã Uniclass EF_20_10 (Result) định danh ISO 19650 ECO-GREEN-BLD1-L01-EF_20_10-P01."
                    )
                else:
                    return "Móng cọc ly tâm là mc..."
            elif "thang máy" in prompt_l and "phối hợp kiến trúc" in prompt_l:
                if has_redteam_rules or "EF_25_50" in content:
                    parts.append(
                        "Phân định 2 góc nhìn: Mô hình kiến trúc Result = EF_25_50 (Lưu thông đứng) vs Hệ thống cơ điện = Ss_70_50_10 (Thang máy) bảo tồn Trí Nhớ Số BIM Object."
                    )
                else:
                    return "Thang máy là EF_25..."
            elif "sơn phồng nở" in prompt_l or "r90" in prompt_l:
                if has_redteam_rules or "Pr_60_60_15" in content:
                    parts.append(
                        "Phân định bóc tách mua sắm Resource = Pr_60_60_15 vs Thuộc tính mô hình BIM Object Property Set (Pset_FireRating) bảo tồn Trí Nhớ Số."
                    )
                else:
                    return "Sơn chống cháy là lớp hoàn thiện..."
            elif "kiosk" in prompt_l or "hợp bộ ngoài trời" in prompt_l:
                if has_redteam_rules or "En_50_10" in content:
                    parts.append(
                        "Phân định phân tách cấp độ ISO 12006-2: Thực thể quy hoạch En_50_10 Result vs Hệ thống thiết bị điện Ss_70_10_10 bảo tồn Trí Nhớ Số BIM Object."
                    )
                else:
                    return "Trạm Kiosk là hệ thống điện..."
            elif has_bim_grounding and has_bim_naming and has_digital_memory:
                parts.append(
                    "Phân loại cấu kiện và đặt tên thực thể theo chuẩn Uniclass 200 & ISO 12006-2:\n"
                    "- Bảng phân loại: Uniclass (En, SL, EF, Ss, Pr, PM) tuân thủ ISO 22274 và ISO 21511 WBS.\n"
                    "- Phân định rõ ràng giữa Result (EF/Ss/SL) và Resource (Pr/PM) theo ISO 12006-2.\n"
                    "- Cấu trúc định danh ISO 19650 / IFC Alignment bảo tồn Trí Nhớ Số (Digital Memory) và cấu trúc không gian Spatial Structure cho mô hình BIM Object (IFC4X3)."
                )
                if "qcvn 06" in prompt_l or "pccc" in prompt_l:
                    parts.append(
                        "Đảm bảo đáp ứng đầy đủ yêu cầu an toàn cháy và thoát nạn theo QCVN 06:2022/BXD."
                    )
            elif has_bim_grounding:
                parts.append("Phân loại theo bảng Uniclass 200 và ISO 12006-2.")
            else:
                return "Xử lý phân loại chung không theo chuẩn Uniclass..."
        elif any(
            k in prompt_l
            for k in [
                "mermaid",
                "excalidraw",
                "diagram",
                "sơ đồ",
                "flowchart",
                "sequence",
            ]
        ):
            has_diagram = (
                "mermaid" in content.lower()
                or "excalidraw" in content.lower()
                or "diagram" in content.lower()
                or "sơ đồ" in content.lower()
            )
            if has_diagram or "ccba" in content.lower():
                parts.append(
                    "Khởi tạo sơ đồ trực quan kiến trúc (Visual Diagram):\n"
                    "```mermaid\n"
                    "flowchart TD\n"
                    "    A[Khởi đầu] --> B[Xử lý trung tâm]\n"
                    "    B --> C{Kiểm tra điều kiện}\n"
                    "    C -->|Hợp lệ| D[Hoàn tất]\n"
                    "    C -->|Không hợp lệ| E[Xử lý lỗi]\n"
                    "    style A fill:#f9f9f9,stroke:#333\n"
                    "    style D fill:#e6ffe6,stroke:#333\n"
                    "```\n"
                    "Sơ đồ tuân thủ quy chuẩn Academic Grayscale và định danh theo [references/](references/)."
                )
            else:
                parts.append("Tạo biểu đồ thông thường...")
        elif "qcvn 06" in prompt_l or "pccc" in prompt_l:
            parts.append(
                "Căn cứ Nghị định 105/2025/NĐ-CP và QCVN 06:2022/BXD (Sửa đổi 1:2023), quy định bậc chịu lửa và giải pháp thoát nạn công trình."
            )
        elif has_legal_grounding and any(
            k in prompt_l
            for k in [
                "pháp luật",
                "luật",
                "nghị định",
                "thông tư",
                "văn bản",
                "thủ tục",
                "pháp lý",
                "vbpl",
                "tvpl",
                "quy phạm",
                "căn cứ pháp lý",
            ]
        ):
            parts.append(
                "Theo quy định tại Luật Xây dựng năm 2025 (Luật số 135/2025/QH15), Nghị định 105/2025/NĐ-CP và hướng dẫn của Cơ quan chuyên môn về xây dựng, yêu cầu được thực thi theo Điều khoản tương ứng."
            )
        elif any(
            k in prompt_l
            for k in [
                "auditor",
                "worker",
                "orchestrat",
                "teamwork",
                "handoff",
                "forensic integrity",
                "single-writer",
                "working directory",
            ]
        ):
            has_orchestration = (
                "Single-Writer" in content
                or "orchestrat" in content.lower()
                or "handoff" in content.lower()
                or "progressive disclosure" in content.lower()
                or "hiến pháp" in content.lower()
                or "constitution" in content.lower()
            )
            if has_orchestration or "teamwork" in content.lower() or "ccba" in content.lower():
                parts.append(
                    "Thực thi quy trình điều phối đa tác tử (Multi-Agent Orchestration):\n"
                    "- Tuân thủ Single-Writer Pattern Invariant và cách ly thư mục làm việc riêng biệt (isolated sandbox working directory).\n"
                    "- Bảo vệ Hiến pháp (Constitution Invariant) và toàn vẹn liên kết Markdown AST Link Integrity theo chuẩn Progressive Disclosure [references/](references/).\n"
                    "- Lập báo cáo bàn giao handoff.md, đưa ra kết luận kiểm định verdict CLEAN, và gửi thông điệp send_message tới parent orchestrator."
                )
            else:
                parts.append("Xử lý tác vụ điều phối tự do không theo chuẩn single-writer...")
        elif any(
            k in prompt_l
            for k in [
                "grill",
                "stress-test",
                "phỏng vấn",
                "chất vấn",
                "redis",
                "adc",
                "gcloud_auth_verification",
                "visual prototype",
                "milvus",
                "pgvector",
            ]
        ):
            has_grilling = (
                "ccba-grilling" in content
                or "Phỏng Vấn Dồn Dập" in content
                or "Grilling Loop" in content
                or "stress-test" in content.lower()
            )
            has_one_by_one = "từng câu một" in content or "one-by-one" in content

            if has_grilling or has_one_by_one:
                parts.append(
                    "Thực thi quy trình Grilling Socrates (Phỏng vấn dồn dập & Đối chiếu quy chuẩn):\n"
                    "- Quy tắc câu hỏi: Chỉ đặt đúng một câu hỏi duy nhất (one-by-one) ở Frontier, kèm phương án đề xuất (recommended answer) của Agent trước.\n"
                    "- Nguyên tắc tra cứu: Tự tra cứu dữ kiện thực tế (facts vs decisions) từ codebase, tuyệt đối không hỏi người dùng các thông tin có thể tự đọc được.\n"
                    "- Đối chiếu quy chuẩn: Đối chiếu trực tiếp với AGENTS.md, chỉ ra vi phạm bất biến cốt lõi (ADR-0058 Hard Completion Lock) nếu có.\n"
                    "- Visual Prototype Grilling: Tạo 3-5 variants trong 1 file HTML duy nhất với floating picker, ghi Decision Log vào NOTES.md.\n"
                    "- Escalation Checkpoint: Triệu hồi /ccba-issue-tree (Solution How-Tree) để lượng hóa và xếp hạng các phương án đối đầu qua ma trận Giá trị × Độ phức tạp × Rủi ro × KISS."
                )
            else:
                parts.append("Hỏi một danh sách nhiều câu hỏi dồn dập...")
        elif any(k in skill_name.lower() for k in CODING_ARCHETYPE_KEYWORDS) or any(
            k in prompt_l
            for k in [
                "code",
                "bug",
                "diagnos",
                "implement",
                "tdd",
                "design",
                "refactor",
                "unit test",
                "rca",
                "codebase",
                "engineering",
            ]
        ):
            has_hard_lock = (
                "verify-patch" in content
                or "Khóa Cứng Hoàn Tất" in content
                or "Hard Completion Lock" in content
            )
            has_double_pass = "Double-Pass" in content or "Rà Soát Hai Vòng" in content
            has_engineering_rigor = (
                "KISS" in content
                or "Deep Module" in content
                or "seam" in content.lower()
                or "idempotent" in content.lower()
                or "error handling" in content.lower()
            )

            coding_blocks = []
            if has_double_pass or has_engineering_rigor:
                sub_blocks = []
                if has_double_pass:
                    sub_blocks.append(
                        "- Chẩn đoán Root Cause Analysis (RCA) với tham chiếu tệp và dòng cụ thể theo quy luật Double-Pass Review."
                    )
                if has_engineering_rigor:
                    sub_blocks.append(
                        "- Triển khai tái cấu trúc (refactoring) tuân thủ nguyên tắc KISS, Deep Module Seam, và Idempotency Guardrails.\n"
                        "- Bổ sung unit tests đảm bảo test coverage và xử lý ngoại lệ tường minh (explicit error handling)."
                    )
                coding_blocks.append(
                    "Thực thi quy trình kỹ thuật phần mềm chuẩn mực (Codebase Engineering Discipline):\n"
                    + "\n".join(sub_blocks)
                )

            if has_hard_lock:
                coding_blocks.append(
                    "Hard Completion Lock (ADR-0058):\n"
                    "- Bắt buộc thực hiện kiểm chứng tất định qua lệnh:\n"
                    "  python -m ccba_harness verify-patch\n"
                    "- Hoàn tất với exit code 0 trước khi bàn giao kết quả."
                )

            if coding_blocks:
                parts.append("\n\n".join(coding_blocks))
            else:
                parts.append("Thực hiện sửa đổi mã nguồn nhanh không qua kiểm chứng tất định...")
        elif skill_name in ("ccba-skill-repair", "skill-repair", "skill_repair") or any(
            k in prompt_l
            for k in [
                "skill-repair",
                "yaml_parse_error",
                "yaml frontmatter",
                "cổng 0",
                "gate 0",
                "gpi",
                "evaluate-gpi",
                "validate_skills",
                "linter",
                "standalone skill",
                "tiêu chí hoàn thành",
                "sửa chữa",
            ]
        ):
            has_repair_grounding = (
                "ccba-skill-repair" in content
                or "ADR-0057" in content
                or "validate_skills.py" in content
                or "evaluate-gpi" in content
            )
            if has_repair_grounding or "skill-repair" in content.lower():
                parts.append(
                    "Quy trình Phục hồi và Sửa chữa Kỹ năng (CCBA Skill Repair):\n"
                    "- Khảo sát & Chuẩn hóa cú pháp YAML frontmatter: ngăn cách khối metadata bằng cặp thẻ ---, chuẩn hóa 2 spaces.\n"
                    "- Đánh giá Cổng 0 (The Determinism Gate) & Cổng 1 (The Orchestration Gate) theo thể chế ADR-0057 (RES-2026-ARCH-001 v1.2).\n"
                    "- Tính toán chỉ số GPI và vá khối gpi: {s: 4.0, k: 3.0, a: 2.0, p: 1.0} vào frontmatter hợp thức hóa Tier 2B Standalone Kernel Skill.\n"
                    "- Bổ sung tiêu chí hoàn thành (Completion Criterion) cho các bước quy trình, chuẩn hóa liên kết tương đối trỏ về references/ và xử lý script bloat (< 100 LOC).\n"
                    "- Kiểm định bắt buộc: chạy python scripts/validate_skills.py --file <path> --enforce-gpi, python -m ccba_harness.cli evaluate-gpi --file <path> và python scripts/governance/compile_catalog.py bảo đảm pass 100%."
                )
            else:
                parts.append("Sửa lỗi tệp markdown cơ bản...")
        elif any(
            k in prompt_l
            for k in [
                "adr",
                "architecture decision",
                "traceability_matrix",
                "scaffolding",
                "status cascading",
                "ci parity",
            ]
        ):
            has_adr_grounding = (
                "ccba-adr-lifecycle" in content
                or "Quản Trị Vòng Đời Quyết Định Kiến Trúc" in content
                or "docs/adr/" in content
                or "HUB-ADR" in content
            )
            if has_adr_grounding or "adr" in content.lower():
                parts.append(
                    "Quản trị Vòng đời Quyết định Kiến trúc (ADR Lifecycle Governance):\n"
                    "- Scaffolding: Khởi tạo tệp docs/adr/00XX-<slug>.md với đầy đủ YAML Frontmatter (id: HUB-ADR-00XX hoặc SPOKE-ADR-00XX, status: ACCEPTED, pillar) cùng các mục Context, Decision, Consequences, Invariants.\n"
                    "- Status Cascading: Cập nhật status SUPERSEDED cho ADR cũ và bổ sung liên kết hai chiều superseded_by / supersedes.\n"
                    "- Matrix Sync: Quét và cập nhật Living Traceability Matrix docs/adr/TRACEABILITY_MATRIX.md cùng bảng mục lục README.md.\n"
                    "- CI Parity Gate: Kiểm tra tính toàn vẹn và chống lệch pha tài liệu qua python scripts/validate_adr_traceability.py."
                )
            else:
                parts.append("Tạo file markdown ghi chép kiến trúc thông thường...")

        elif item.golden_answer is not None:
            return (
                item.golden_answer
                if isinstance(item.golden_answer, str)
                else json.dumps(item.golden_answer, ensure_ascii=False)
            )
        else:
            has_links = bool(
                re.search(
                    r"\[([^\]]+)\]\(([^)]+)\)|progressive disclosure|references/|tham chiếu",
                    content,
                    re.IGNORECASE,
                )
            )
            if has_links:
                parts.append(
                    "Thực thi quy trình có cấu trúc (Lean Structural Architecture):\n"
                    "- Bộc lộ dần (Progressive Disclosure): Tham chiếu chi tiết tại [Tài liệu hướng dẫn](references/guide.md).\n"
                    "- Cấu trúc tinh gọn và loại bỏ hoàn toàn rác dữ liệu (Anti-Debris Invariant)."
                )
            else:
                parts.append(
                    "Thực thi quy trình chuẩn mực: tham chiếu tài liệu chi tiết tại [Tài liệu hướng dẫn](references/guide.md)."
                )

        if has_xml:
            parts.append(
                "<legal_citation>\nTrích dẫn chính xác Điều khoản và thẩm quyền ban hành.\n</legal_citation>"
            )
            parts.append(
                "<compliance_verdict>\nĐạt chuẩn tuân thủ và không có vi phạm rào chắn.\n</compliance_verdict>"
            )

        if has_progressive_links:
            parts.append("Tham chiếu chi tiết: [Hướng dẫn thực hiện](references/guide.md).")

        return "\n\n".join(parts)

    return mock_agent_task


create_domain_mock_agent_task = build_mock_agent_task

__all__ = ["build_mock_agent_task", "create_domain_mock_agent_task"]
