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
        has_xml = "<legal_" in content or "XML" in content
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
                "nghị định 30",
                "nđ 30",
                "thể thức",
                "soạn thảo",
                "times new roman",
                "bố cục",
                "tiêu đề",
                "quốc hiệu",
                "nơi nhận",
                "phông chữ",
                "docx",
                "pptx",
                "slide",
                "trình bày",
                "typography",
                "heading",
                "bảng",
                "mục lục",
                "canh lề",
                "seminar",
                "agenda",
            ]
        ):
            has_office = any(
                k in content.lower()
                for k in [
                    "nghị định 30",
                    "thể thức",
                    "typography",
                    "docx",
                    "pptx",
                    "văn bản",
                    "phông chữ",
                ]
            )
            if has_office or "ccba" in content.lower():
                parts.append(
                    "Thực thi quy chuẩn soạn thảo văn bản và định dạng văn phòng:\n"
                    "- Căn cứ Nghị định 30/2020/NĐ-CP (NĐ 30/2020) về công tác văn thư: Tuân thủ nghiêm ngặt thể thức soạn thảo văn bản hành chính, bố cục tiêu đề, Quốc hiệu, Tiêu ngữ và Nơi nhận.\n"
                    "- Tiêu chuẩn Typography & Phông chữ: Sử dụng phông chữ Times New Roman chuẩn Unicode, canh lề theo quy định, phân cấp heading rõ ràng, tự động sinh mục lục tài liệu và định dạng bảng phụ lục.\n"
                    "- Trình chiếu PowerPoint (.pptx): Bố cục dàn trang slide theo phong cách tối giản, trình bày súc tích và tương phản trực quan.\n"
                    "Chi tiết tham chiếu xem tại [references/](references/)."
                )
            else:
                parts.append("Soạn thảo văn bản thông thường...")
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
