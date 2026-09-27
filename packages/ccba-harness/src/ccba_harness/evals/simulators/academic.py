"""academic.py - Academic Writing & Scientific Paper Domain Simulator.

Simulates responses for academic writing skills (e.g. ccba-academic-writing),
including CARS 3-Move Blueprint, Yale Academic Style, Materials & Methods,
Discussion Zoom-out, and APA 7th / BibTeX citation formatting.
"""

from __future__ import annotations

from ..models import EvalItem
from .base import BaseDomainSimulator, SimulationContext


class AcademicDomainSimulator(BaseDomainSimulator):
    """Simulator for academic and scientific paper drafting."""

    archetype_name = "academic"

    def can_handle(self, item: EvalItem, ctx: SimulationContext) -> bool:
        prompt = str(item.input_prompt)
        return (
            "CARS" in prompt
            or "Introduction" in prompt
            or "Materials & Methods" in prompt
            or "passive voice" in prompt
            or "Discussion" in prompt
            or "Zoom-out" in prompt
            or "Hiệu đính văn phong" in prompt
            or "nominalizations" in prompt
            or "APA" in prompt
            or "BibTeX" in prompt
            or "Swales" in prompt
        )

    def simulate(self, item: EvalItem, ctx: SimulationContext) -> str | None:
        prompt = str(item.input_prompt)

        # 1. CARS / Introduction
        if "CARS" in prompt or "Introduction" in prompt:
            if ctx.has_cars_stems or ctx.has_academic_grounding:
                return ctx.wrap_response(
                    "Biên soạn phần Introduction theo mô hình CARS (John Swales, 1990):\n"
                    "- Move 1 (Establish Territory): Recent advances in digital engineering have heightened the need for robust quality control (has been widely studied).\n"
                    "- Move 2 (Find a Niche): However, current automated systems fail to process massive multi-thousand-page technical dossiers due to context saturation.\n"
                    "- Move 3 (Occupy the Niche): To address this gap, in this paper we propose a Semantic Map-Reduce framework and confirm the primary scientific contributions."
                )
            return "Viết mở bài giới thiệu chung không theo mô hình CARS..."

        # 2. Materials & Methods / passive voice
        if "Materials & Methods" in prompt or "passive voice" in prompt:
            if ctx.has_academic_grounding:
                return ctx.wrap_response(
                    "Section: Materials & Methods (Yale Academic Style Guidelines):\n"
                    "A dataset comprising 507 project transcript files was extracted using safe directory traversal protocols. "
                    "The independent variables were controlled via isolation sandboxes, while evaluation metrics were recorded under append-only logs (passive voice)."
                )
            return "Chúng tôi đã lấy 507 file..."

        # 3. Discussion / Zoom-out
        if "Discussion" in prompt or "Zoom-out" in prompt:
            if ctx.has_academic_grounding:
                return ctx.wrap_response(
                    "Section: Discussion (Zoom-out Mirroring Framework):\n"
                    "- Move 1 (Major Findings): The Karpathy Git-Ratchet optimization framework achieved 100% convergence without manual intervention.\n"
                    "- Move 2 (Context & Limitations): Compared to standard gradient-free search, our results demonstrate superior stability. We acknowledge that the current study is limited to single-file prompt mutations (limitations).\n"
                    "- Move 3 (Take-home Message): Autonomous prompt optimization establishes a new paradigm for resilient agent systems."
                )
            return "Thảo luận: kết quả đạt được rất tốt..."

        # 4. Hiệu đính văn phong / nominalizations
        if "Hiệu đính văn phong" in prompt or "nominalizations" in prompt:
            if ctx.has_academic_grounding:
                return ctx.wrap_response(
                    "Bản hiệu đính văn phong học thuật (Chuẩn Elena Kallestinova, 2011, Yale Style):\n"
                    "- Loại bỏ từ ngữ cảm tính ('clearly', 'obviously', 'very', 'basically').\n"
                    "- Chuyển đổi danh từ hóa rườm rà (De-nominalization): 'make a decision' -> 'decide', 'provide an analysis' -> 'analyze'."
                )
            return "Văn bản đã được chỉnh sửa cơ bản..."

        # 5. APA / BibTeX / Swales
        if "APA" in prompt or "BibTeX" in prompt or "Swales" in prompt:
            if ctx.has_academic_bibtex:
                return ctx.wrap_response(
                    "References (APA 7th & BibTeX):\n"
                    "- Swales, J. M. (1990). Genre Analysis: English in Academic and Research Settings. Cambridge University Press.\n"
                    "- Kallestinova, E. D. (2011). How to write your first research paper. Yale Journal of Biology and Medicine, 84(3), 181-190.\n"
                    "```bibtex\n@article{kallestinova2011,\n  author = {Kallestinova, Elena D.},\n  title = {How to Write Your First Research Paper},\n  journal = {Yale Journal of Biology and Medicine},\n  year = {2011}\n}\n```"
                )
            return "Tài liệu tham khảo chung: Swales 1990, Kallestinova 2011."

        return ctx.wrap_response(
            "Biên soạn tài liệu học thuật theo cấu trúc IMRAD, quy chuẩn văn phong khoa học và trích dẫn chuẩn hóa."
        )
