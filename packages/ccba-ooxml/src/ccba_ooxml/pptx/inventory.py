#!/usr/bin/env python3
"""Extract structured text content from PowerPoint presentations.

Thin public facade preserving all exports and CLI entrypoints while delegating
models, shape metrics, and geometry logic to cohesive private submodules.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any

from pptx import Presentation

from ._inventory_geometry import (
    calculate_overlap,
    collect_shapes_with_absolute_positions,
    detect_overlaps,
    is_valid_shape,
    sort_shapes_by_position,
)
from ._inventory_metrics import ShapeData
from ._inventory_models import (
    InventoryData,
    InventoryDict,
    JsonValue,
    ParagraphData,
    ParagraphDict,
    PresentationInventory,
    ShapeDict,
    ShapeWithPosition,
)


def _build_inventory_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser for PPTX text inventory extraction."""
    parser = argparse.ArgumentParser(
        description="Extract text inventory from PowerPoint with proper GroupShape support.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python inventory.py presentation.pptx inventory.json
    Extracts text inventory with correct absolute positions for grouped shapes

  python inventory.py presentation.pptx inventory.json --issues-only
    Extracts only text shapes that have overflow or overlap issues
        """,
    )
    parser.add_argument("input", help="Input PowerPoint file (.pptx)")
    parser.add_argument("output", help="Output JSON file for inventory")
    parser.add_argument(
        "--issues-only",
        action="store_true",
        help="Include only text shapes that have overflow or overlap issues",
    )
    return parser


def _run_inventory_cli(args: argparse.Namespace) -> None:
    """Execute inventory extraction and save JSON output from parsed CLI args."""
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)
    if input_path.suffix.lower() != ".pptx":
        print("Error: Input must be a PowerPoint file (.pptx)")
        sys.exit(1)
    try:
        print(f"Extracting text inventory from: {args.input}")
        if args.issues_only:
            print("Filtering to include only text shapes with issues (overflow/overlap)")
        inventory = extract_text_inventory(input_path, issues_only=args.issues_only)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_inventory(inventory, output_path)
        print(f"Output saved to: {args.output}")
        _print_inventory_summary(inventory, issues_only=args.issues_only)
    except Exception as exc:
        print(f"Error processing presentation: {exc}")
        traceback.print_exc()
        sys.exit(1)


def _print_inventory_summary(inventory: InventoryData, issues_only: bool) -> None:
    """Print slide and text element statistics after CLI extraction."""
    total_slides = len(inventory)
    total_shapes = sum(len(shapes) for shapes in inventory.values())
    if issues_only:
        if total_shapes > 0:
            print(f"Found {total_shapes} text elements with issues in {total_slides} slides")
        else:
            print("No issues discovered")
    else:
        print(f"Found text in {total_slides} slides with {total_shapes} text elements")


def main() -> None:
    """Main entry point for command-line usage."""
    parser = _build_inventory_parser()
    args = parser.parse_args()
    _run_inventory_cli(args)


def _extract_slide_inventory(slide: Any, issues_only: bool) -> dict[str, ShapeData] | None:
    """Extract sorted ShapeData dictionary for a single slide, or None if empty."""
    shapes_with_positions: list[ShapeWithPosition] = []
    for shape in slide.shapes:
        shapes_with_positions.extend(collect_shapes_with_absolute_positions(shape))
    if not shapes_with_positions:
        return None
    shape_data_list = [
        ShapeData(swp.shape, swp.absolute_left, swp.absolute_top, slide)
        for swp in shapes_with_positions
    ]
    sorted_shapes = sort_shapes_by_position(shape_data_list)
    for idx, shape_data in enumerate(sorted_shapes):
        shape_data.shape_id = f"shape-{idx}"
    if len(sorted_shapes) > 1:
        detect_overlaps(sorted_shapes)
    if issues_only:
        sorted_shapes = [sd for sd in sorted_shapes if sd.has_any_issues]
    if not sorted_shapes:
        return None
    return {shape_data.shape_id: shape_data for shape_data in sorted_shapes}


def extract_text_inventory(
    pptx_path: Path, prs: Any | None = None, issues_only: bool = False
) -> InventoryData:
    """Extract text content from all slides in a PowerPoint presentation."""
    if prs is None:
        prs = Presentation(str(pptx_path))
    inventory: InventoryData = {}
    for slide_idx, slide in enumerate(prs.slides):
        slide_shapes = _extract_slide_inventory(slide, issues_only=issues_only)
        if slide_shapes is not None:
            inventory[f"slide-{slide_idx}"] = slide_shapes
    return inventory


def get_inventory_as_dict(pptx_path: Path, issues_only: bool = False) -> InventoryDict:
    """Extract text inventory and return as JSON-serializable dictionaries."""
    inventory = extract_text_inventory(pptx_path, issues_only=issues_only)
    dict_inventory: InventoryDict = {}
    for slide_key, shapes in inventory.items():
        dict_inventory[slide_key] = {
            shape_key: shape_data.to_dict() for shape_key, shape_data in shapes.items()
        }
    return dict_inventory


def save_inventory(inventory: InventoryData, output_path: Path) -> None:
    """Save inventory to JSON file with proper formatting."""
    json_inventory: InventoryDict = {}
    for slide_key, shapes in inventory.items():
        json_inventory[slide_key] = {
            shape_key: shape_data.to_dict() for shape_key, shape_data in shapes.items()
        }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_inventory, f, indent=2, ensure_ascii=False)


def pptx_inventory(pptx_path: Path | str) -> PresentationInventory:
    """Extract complete geometric and structural shape inventory from a presentation."""
    p_path = Path(pptx_path)
    prs = Presentation(str(p_path))
    w_obj = getattr(prs, "slide_width", None)
    slide_w_pt = float(getattr(w_obj, "pt", float(w_obj) / 12700.0 if w_obj is not None else 720.0))
    h_obj = getattr(prs, "slide_height", None)
    slide_h_pt = float(getattr(h_obj, "pt", float(h_obj) / 12700.0 if h_obj is not None else 540.0))
    inventory_data = extract_text_inventory(p_path, prs=prs)
    slides_list: list[dict[str, Any]] = []
    for slide_key, shapes in inventory_data.items():
        slide_shapes = [sd.to_dict() for sd in shapes.values()]
        slides_list.append(
            {
                "slide_id": slide_key,
                "shape_count": len(slide_shapes),
                "shapes": slide_shapes,
            }
        )
    return PresentationInventory(
        total_slides=len(prs.slides),
        slide_width_pt=float(slide_w_pt),
        slide_height_pt=float(slide_h_pt),
        slides=slides_list,
    )


__all__ = [
    "InventoryData",
    "InventoryDict",
    "JsonValue",
    "ParagraphData",
    "ParagraphDict",
    "PresentationInventory",
    "ShapeData",
    "ShapeDict",
    "ShapeWithPosition",
    "calculate_overlap",
    "collect_shapes_with_absolute_positions",
    "detect_overlaps",
    "extract_text_inventory",
    "get_inventory_as_dict",
    "is_valid_shape",
    "main",
    "pptx_inventory",
    "save_inventory",
    "sort_shapes_by_position",
]


if __name__ == "__main__":
    main()
