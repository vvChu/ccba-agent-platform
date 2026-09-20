#!/usr/bin/env python3
"""compile_uniclass_flat_index.py - Autonomous Compiler for Uniclass 200 & ISO 12006-2 Flat Index (TICKET-005).

Extracts Uniclass 200 codes, ISO 12006-2 object layers, classification tables (Co, En, SL, EF, Ss, Pr, PM),
naming conventions (ISO 19650 Room Naming, IFC Alignment Linear Naming), and redteam anti-trap rules
into a lightweight flat index packaged directly within ccba-harness for CI parity.
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("compile_uniclass_flat_index")

DEFAULT_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUTPUT_PATH = (
    DEFAULT_ROOT_DIR
    / "packages"
    / "ccba-harness"
    / "src"
    / "ccba_harness"
    / "evals"
    / "datasets"
    / "uniclass_tables_flat.json"
)

# Uniclass Table metadata mapping to ISO 12006-2 layers
TABLE_DEFINITIONS: dict[str, dict[str, str]] = {
    "Co": {
        "name_en": "Complexes",
        "name_vi": "Tổ hợp công trình",
        "iso_12006_layer": "Result (Complexes)",
        "description": "Tập hợp các thực thể công trình và không gian có mục đích sử dụng chung.",
    },
    "En": {
        "name_en": "Entities",
        "name_vi": "Thực thể công trình",
        "iso_12006_layer": "Result (Entities)",
        "description": "Một công trình độc lập hoặc một tòa nhà trong tổ hợp.",
    },
    "SL": {
        "name_en": "Spaces/locations",
        "name_vi": "Không gian và Vị trí",
        "iso_12006_layer": "Result (Spaces)",
        "description": "Khu vực hoặc phòng chức năng 3 chiều phục vụ hoạt động của con người hoặc thiết bị.",
    },
    "EF": {
        "name_en": "Elements/functions",
        "name_vi": "Cấu kiện và Chức năng",
        "iso_12006_layer": "Result (Elements)",
        "description": "Bộ phận cấu trúc chính hoàn chỉnh của công trình (cột, dầm, tường, móng).",
    },
    "Ss": {
        "name_en": "Systems",
        "name_vi": "Hệ thống kỹ thuật",
        "iso_12006_layer": "Result (Systems)",
        "description": "Tập hợp các sản phẩm liên kết hoạt động cùng nhau (hệ thống HVAC, PCCC, điện).",
    },
    "Pr": {
        "name_en": "Products",
        "name_vi": "Sản phẩm / Vật tư",
        "iso_12006_layer": "Resource (Products)",
        "description": "Vật tư, thiết bị riêng lẻ được sản xuất hoặc mua sắm phục vụ lắp đặt (BOQ procurement).",
    },
    "PM": {
        "name_en": "Project Management",
        "name_vi": "Quản lý Dự án",
        "iso_12006_layer": "Process (Management)",
        "description": "Các hoạt động, giai đoạn và thông tin quản trị vòng đời dự án.",
    },
}

# Red-team Anti-Trap rules and misconceptions
ANTI_TRAP_RULES: dict[str, dict[str, Any]] = {
    "redteam_trap_01_hybrid_shaft": {
        "name": "Hybrid Enclosure / Hộp Kỹ Thuật",
        "correct_code": "EF_25_10",
        "correct_layer": "Result (Elements)",
        "rule": "Phân loại vỏ hộp bao che là EF_25_10 (Kiến trúc Result), chứa các hệ thống MEP con Ss bên trong.",
        "forbidden_patterns": [
            r"Ss_.*chỉ\s*hộp",
            r"Pr_.*hộp\s*kỹ\s*thuật\s*là\s*vật\s*tư\s*chính",
            r"hộp\s*kỹ\s*thuật.*(?:là|thuộc)\s*(?:Ss_|Pr_)",
            r"hộp\s*kỹ\s*thuật.*phân\s*loại.*(?:Ss_|Pr_)",
        ],
    },
    "redteam_trap_02_slang_normalization": {
        "name": "Slang Normalization / Viết tắt Tiếng Việt",
        "correct_code": "EF_20_20",
        "correct_layer": "Result (Elements)",
        "rule": "Tự động chuẩn hóa btct -> Bê tông cốt thép, san T3 -> L03, dam D1 -> EF_20_20-D1.",
        "slang_mappings": {
            "btct": "Bê tông cốt thép",
            "san t3": "L03",
            "dam d1": "D1",
            "mc d800": "Móng cọc D800",
        },
    },
    "redteam_trap_03_element_vs_product": {
        "name": "Result vs Resource / Đối tượng BIM vs Vật tư BOQ",
        "bim_object_code": "EF_25_30",
        "bim_object_layer": "Result (Elements)",
        "boq_material_code": "Pr_30_59_24",
        "boq_material_layer": "Resource (Products)",
        "rule": "Bóc tách rõ EF_25_30 (Mô hình BIM Object Result) vs Pr_30_59_24 (Mua sắm BOQ Resource) bảo tồn Trí Nhớ Số.",
        "forbidden_patterns": [
            r"gán\s*Pr_30_59_24\s*cho\s*mô\s*hình\s*trần\s*Revit",
            r"bóc\s*tách.*EF_25_30.*(?:là|thành)\s*Pr_30_59_24",
            r"mô\s*hình\s*BIM.*gán\s*mã\s*Pr_",
        ],
    },
    "redteam_trap_04_curved_alignment_infra": {
        "name": "Linear Infrastructure / Tuyến Hạ tầng IFC Alignment",
        "correct_code": "EF_10_10",
        "correct_layer": "Result (Elements)",
        "rule": "Đoạn đường cong hạ tầng yêu cầu định danh 2 mốc lý trình bắt đầu và kết thúc.",
        "naming_syntax_pattern": r"CT05-KM\d+_\d+_KM\d+_\d+-EF_10_10",
    },
    "redteam_trap_05_phantom_fire_airlock": {
        "name": "Fire Airlock Buffer / Khoang Đệm Ngăn Cháy",
        "correct_code": "SL_25_30_70",
        "correct_layer": "Result (Spaces)",
        "rule": "Khoang đệm ngăn cháy bắt buộc phân loại là SL_25_30_70 (Không gian đệm an toàn/Air-lock).",
        "forbidden_patterns": [
            r"SL_90_10",
            r"SL_20_15",
            r"khoang\s*đệm.*phòng\s*thông\s*thường",
            r"air-lock.*phòng\s*thông\s*thường",
        ],
    },
}


def compile_uniclass_flat_index(
    root_dir: Path,
    output_file: Path,
    compact: bool = False,
) -> dict[str, Any]:
    """Compiles Uniclass 200 dataset into a standalone flat index."""
    test_cases_dir = root_dir / ".agents" / "skills" / "ccba-eval-gate" / "test_cases"
    target_files = [
        test_cases_dir / "eval_bigbim_classification_100.json",
        test_cases_dir / "eval_bigbim_classification.json",
        test_cases_dir / "eval_bigbim_classification_redteam.json",
        test_cases_dir / "eval_bigbim_risk.json",
    ]

    codes_dict: dict[str, dict[str, Any]] = {}

    for tf in target_files:
        if not tf.exists():
            logger.warning(f"File không tồn tại: {tf}")
            continue
        try:
            with open(tf, encoding="utf-8") as f:
                items = json.load(f)
            if isinstance(items, list):
                for it in items:
                    if not isinstance(it, dict):
                        continue
                    ga = it.get("golden_answer")
                    if isinstance(ga, dict) and ga.get("uniclass_code"):
                        code = str(ga["uniclass_code"]).strip()
                        table_prefix = code.split("_")[0].upper()
                        table_info = TABLE_DEFINITIONS.get(table_prefix, {})

                        iso_layer = ga.get("iso_12006_layer") or table_info.get(
                            "iso_12006_layer", "Result"
                        )
                        title_vi = ga.get("title_vi") or it.get("input_prompt", "")[:60]
                        naming = ga.get("iso_19650_naming") or ga.get("ifc_alignment_naming")

                        entry = codes_dict.setdefault(
                            code,
                            {
                                "code": code,
                                "table": table_prefix,
                                "table_name": table_info.get("name_en", table_prefix),
                                "table_name_vi": table_info.get("name_vi", table_prefix),
                                "iso_12006_layer": iso_layer,
                                "title_vi": title_vi,
                                "title_en": code.replace("_", " "),
                                "example_naming": naming,
                                "sources": [],
                            },
                        )
                        entry["sources"].append(it.get("id"))
                        if naming and not entry.get("example_naming"):
                            entry["example_naming"] = naming
                        if ga.get("title_vi") and entry.get("title_vi", "").startswith("Xác định"):
                            entry["title_vi"] = ga["title_vi"]
        except Exception as e:
            logger.error(f"Lỗi đọc {tf}: {e}")

    # Add canonical Uniclass foundation codes if missing
    foundation_codes: list[dict[str, Any]] = [
        {
            "code": "Co_25_10_55",
            "table": "Co",
            "title_vi": "Tổ hợp thương mại dịch vụ hỗn hợp",
            "iso_12006_layer": "Result (Complexes)",
        },
        {
            "code": "En_25_70_47",
            "table": "En",
            "title_vi": "Nhà chung cư cao tầng",
            "iso_12006_layer": "Result (Entities)",
        },
        {
            "code": "En_30_20_36",
            "table": "En",
            "title_vi": "Khách sạn nghỉ dưỡng",
            "iso_12006_layer": "Result (Entities)",
        },
        {
            "code": "SL_25_10_72",
            "table": "SL",
            "title_vi": "Phòng đọc sách đa phương tiện",
            "iso_12006_layer": "Result (Spaces)",
        },
        {
            "code": "SL_25_30_70",
            "table": "SL",
            "title_vi": "Khoang đệm ngăn cháy / Air-lock",
            "iso_12006_layer": "Result (Spaces)",
        },
        {
            "code": "SL_25_30_80",
            "table": "SL",
            "title_vi": "Bể bơi vô cực trên cao",
            "iso_12006_layer": "Result (Spaces)",
        },
        {
            "code": "SL_30_20_58",
            "table": "SL",
            "title_vi": "Phòng phẫu thuật áp lực âm",
            "iso_12006_layer": "Result (Spaces)",
        },
        {
            "code": "SL_70_20_88",
            "table": "SL",
            "title_vi": "Kho tiền an ninh cao ngân hàng",
            "iso_12006_layer": "Result (Spaces)",
        },
        {
            "code": "EF_20_05_70",
            "table": "EF",
            "title_vi": "Tường vây tầng hầm Barrette",
            "iso_12006_layer": "Result (Elements)",
        },
        {
            "code": "EF_20_10_15",
            "table": "EF",
            "title_vi": "Cột chịu lực bê tông cốt thép",
            "iso_12006_layer": "Result (Elements)",
        },
        {
            "code": "EF_20_20",
            "table": "EF",
            "title_vi": "Dầm và sàn bê tông cốt thép",
            "iso_12006_layer": "Result (Elements)",
        },
        {
            "code": "EF_25_10",
            "table": "EF",
            "title_vi": "Vách ngăn bao che / Vách hộp kỹ thuật",
            "iso_12006_layer": "Result (Elements)",
        },
        {
            "code": "EF_25_30",
            "table": "EF",
            "title_vi": "Hệ trần hoàn thiện kiến trúc",
            "iso_12006_layer": "Result (Elements)",
        },
        {
            "code": "EF_25_50",
            "table": "EF",
            "title_vi": "Thang máy và lối thoát nạn đứng",
            "iso_12006_layer": "Result (Elements)",
        },
        {
            "code": "EF_30_10",
            "table": "EF",
            "title_vi": "Vách kính mặt dựng Curtain wall",
            "iso_12006_layer": "Result (Elements)",
        },
        {
            "code": "Ss_60_40_36",
            "table": "Ss",
            "title_vi": "Hệ thống điều hòa không khí VRF/VRV",
            "iso_12006_layer": "Result (Systems)",
        },
        {
            "code": "Ss_55_30_30",
            "table": "Ss",
            "title_vi": "Hệ thống camera giám sát an ninh IP",
            "iso_12006_layer": "Result (Systems)",
        },
        {
            "code": "Ss_70_10_70",
            "table": "Ss",
            "title_vi": "Hệ thống máy phát điện dự phòng sự cố",
            "iso_12006_layer": "Result (Systems)",
        },
        {
            "code": "Ss_65_40_33",
            "table": "Ss",
            "title_vi": "Hệ thống phân phối khí y tế trung tâm",
            "iso_12006_layer": "Result (Systems)",
        },
        {
            "code": "Pr_60_65_62",
            "table": "Pr",
            "title_vi": "Bơm ly tâm trục đứng hai cửa hút",
            "iso_12006_layer": "Resource (Products)",
        },
        {
            "code": "Pr_65_70_11",
            "table": "Pr",
            "title_vi": "Cáp đồng cách điện XLPE chống cháy",
            "iso_12006_layer": "Resource (Products)",
        },
        {
            "code": "Pr_60_70_23",
            "table": "Pr",
            "title_vi": "Van chặn lửa và ngăn khói động cơ điện",
            "iso_12006_layer": "Resource (Products)",
        },
        {
            "code": "Pr_30_59_24",
            "table": "Pr",
            "title_vi": "Tấm thạch cao tiêu âm đục lỗ",
            "iso_12006_layer": "Resource (Products)",
        },
        {
            "code": "Pr_25_71_36",
            "table": "Pr",
            "title_vi": "Bó cáp thép dự ứng lực kéo sau",
            "iso_12006_layer": "Resource (Products)",
        },
        {
            "code": "Pr_60_60_15",
            "table": "Pr",
            "title_vi": "Sơn phồng nở chống cháy kết cấu thép",
            "iso_12006_layer": "Resource (Products)",
        },
        {
            "code": "PM_40_20",
            "table": "PM",
            "title_vi": "Bảng tiên lượng mời thầu (BOQ)",
            "iso_12006_layer": "Process (Management)",
        },
        {
            "code": "PM_80_10",
            "table": "PM",
            "title_vi": "Quản lý vận hành và bảo trì tài sản",
            "iso_12006_layer": "Process (Management)",
        },
    ]

    for fc in foundation_codes:
        code = fc["code"]
        entry = codes_dict.setdefault(
            code,
            {
                "code": code,
                "table": fc["table"],
                "table_name": TABLE_DEFINITIONS[fc["table"]]["name_en"],
                "table_name_vi": TABLE_DEFINITIONS[fc["table"]]["name_vi"],
                "iso_12006_layer": fc["iso_12006_layer"],
                "title_vi": fc["title_vi"],
                "title_en": code.replace("_", " "),
                "sources": ["foundation"],
            },
        )
        if not entry.get("title_vi") or entry.get("title_vi", "").startswith("Xác định"):
            entry["title_vi"] = fc["title_vi"]

    manifest: dict[str, Any] = {
        "metadata": {
            "schema_version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_codes": len(codes_dict),
            "standards": [
                "Uniclass 200",
                "ISO 12006-2:2015",
                "ISO 22274:2013",
                "ISO 21511:2021",
                "ISO 19650",
                "IFC4X3",
            ],
            "description": "Chỉ mục phẳng mã phân loại Uniclass 200 và cấu trúc ISO 12006-2 cho BIGBIM.",
        },
        "tables": TABLE_DEFINITIONS,
        "anti_traps": ANTI_TRAP_RULES,
        "codes": codes_dict,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        if compact:
            json.dump(manifest, f, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

    logger.info(
        f"✅ Biên dịch thành công Uniclass Flat Index: {len(codes_dict)} mã Uniclass -> {output_file}"
    )
    return manifest


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Compile Uniclass 200 & ISO 12006-2 flat index for CCBA Evals."
    )
    parser.add_argument(
        "--root-dir",
        type=Path,
        default=DEFAULT_ROOT_DIR,
        help="Root directory of ccba-agent-platform",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Target path for uniclass_tables_flat.json",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Output pretty indented JSON (default is compact)",
    )
    args = parser.parse_args()

    compile_uniclass_flat_index(
        root_dir=args.root_dir,
        output_file=args.output,
        compact=not args.pretty,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
