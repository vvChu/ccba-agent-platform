"""bim_rase.py - BIGBIM RASE & IFC4X3 Property Mapping Domain Simulator.

Simulates responses for RASE skills (e.g. bigbim-rase),
including Requirement, Applicability, Selection (IfcPropertySet, IfcRelDefinesByProperties),
Exception, and Quantity Take-Off (Qto) integration.
"""

from __future__ import annotations

from ..models import EvalItem
from .base import BaseDomainSimulator, SimulationContext


class BimRaseDomainSimulator(BaseDomainSimulator):
    """Simulator for BIGBIM RASE analysis and IFC4X3 property mapping."""

    archetype_name = "bim_rase"

    def can_handle(self, item: EvalItem, ctx: SimulationContext) -> bool:
        prompt_l = str(item.input_prompt).lower()
        return "rase" in ctx.skill_name.lower() or any(
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
        )

    def simulate(self, item: EvalItem, ctx: SimulationContext) -> str | None:
        content = ctx.content
        has_rase_grounding = (
            "rase" in content.lower()
            or "ifc4x3" in content.lower()
            or "ifcreldefinesbyproperties" in content.lower()
            or "pset" in content.lower()
        )
        if has_rase_grounding or "bigbim" in content.lower():
            return ctx.wrap_response(
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
        return ctx.wrap_response("Phân tích RASE thông thường...")
