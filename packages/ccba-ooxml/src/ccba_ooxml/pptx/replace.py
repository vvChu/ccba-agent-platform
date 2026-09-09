#!/usr/bin/env python3
"""Apply text replacements to PowerPoint presentation.

Usage:
    python replace.py <input.pptx> <replacements.json> <output.pptx>

The replacements JSON should have the structure output by inventory.py.
ALL text shapes identified by inventory.py will have their text cleared
unless "paragraphs" is specified in the replacements for that shape.
"""

import json
import sys
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_THEME_COLOR
from pptx.enum.text import PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Pt

from .inventory import InventoryData, extract_text_inventory


def clear_paragraph_bullets(paragraph):
    """Clear bullet formatting from a paragraph."""
    pPr = paragraph._element.get_or_add_pPr()

    # Remove existing bullet elements
    for child in list(pPr):
        if (
            child.tag.endswith("buChar")
            or child.tag.endswith("buNone")
            or child.tag.endswith("buAutoNum")
            or child.tag.endswith("buFont")
        ):
            pPr.remove(child)

    return pPr


def apply_paragraph_properties(paragraph, para_data: dict[str, Any]):
    """Apply formatting properties to a paragraph."""
    # Get the text but don't set it on paragraph directly yet
    text = para_data.get("text", "")

    # Get or create paragraph properties
    pPr = clear_paragraph_bullets(paragraph)

    # Handle bullet formatting
    if para_data.get("bullet", False):
        level = para_data.get("level", 0)
        paragraph.level = level

        # Calculate font-proportional indentation
        font_size = para_data.get("font_size", 18.0)
        level_indent_emu = int((font_size * (1.6 + level * 1.6)) * 12700)
        hanging_indent_emu = int(-font_size * 0.8 * 12700)

        # Set indentation
        pPr.attrib["marL"] = str(level_indent_emu)
        pPr.attrib["indent"] = str(hanging_indent_emu)

        # Add bullet character
        buChar = OxmlElement("a:buChar")
        buChar.set("char", "•")
        pPr.append(buChar)

        # Default to left alignment for bullets if not specified
        if "alignment" not in para_data:
            paragraph.alignment = PP_ALIGN.LEFT
    else:
        # Remove indentation for non-bullet text
        pPr.attrib["marL"] = "0"
        pPr.attrib["indent"] = "0"

        # Add buNone element
        buNone = OxmlElement("a:buNone")
        pPr.insert(0, buNone)

    # Apply alignment
    if "alignment" in para_data:
        alignment_map = {
            "LEFT": PP_ALIGN.LEFT,
            "CENTER": PP_ALIGN.CENTER,
            "RIGHT": PP_ALIGN.RIGHT,
            "JUSTIFY": PP_ALIGN.JUSTIFY,
        }
        if para_data["alignment"] in alignment_map:
            paragraph.alignment = alignment_map[para_data["alignment"]]

    # Apply spacing
    if "space_before" in para_data:
        paragraph.space_before = Pt(para_data["space_before"])
    if "space_after" in para_data:
        paragraph.space_after = Pt(para_data["space_after"])
    if "line_spacing" in para_data:
        paragraph.line_spacing = Pt(para_data["line_spacing"])

    # Apply run-level formatting
    if not paragraph.runs:
        run = paragraph.add_run()
        run.text = text
    else:
        run = paragraph.runs[0]
        run.text = text

    # Apply font properties
    apply_font_properties(run, para_data)


def apply_font_properties(run, para_data: dict[str, Any]):
    """Apply font properties to a text run."""
    if "bold" in para_data:
        run.font.bold = para_data["bold"]
    if "italic" in para_data:
        run.font.italic = para_data["italic"]
    if "underline" in para_data:
        run.font.underline = para_data["underline"]
    if "font_size" in para_data:
        run.font.size = Pt(para_data["font_size"])
    if "font_name" in para_data:
        run.font.name = para_data["font_name"]

    # Apply color - prefer RGB, fall back to theme_color
    if "color" in para_data:
        color_hex = para_data["color"].lstrip("#")
        if len(color_hex) == 6:
            r = int(color_hex[0:2], 16)
            g = int(color_hex[2:4], 16)
            b = int(color_hex[4:6], 16)
            run.font.color.rgb = RGBColor(r, g, b)
    elif "theme_color" in para_data:
        # Get theme color by name (e.g., "DARK_1", "ACCENT_1")
        theme_name = para_data["theme_color"]
        try:
            run.font.color.theme_color = getattr(MSO_THEME_COLOR, theme_name)
        except AttributeError:
            print(f"  WARNING: Unknown theme color name '{theme_name}'")


def detect_frame_overflow(inventory: InventoryData) -> dict[str, dict[str, float]]:
    """Detect text overflow in shapes (text exceeding shape bounds).

    Returns dict of slide_key -> shape_key -> overflow_inches.
    Only includes shapes that have text overflow.
    """
    overflow_map = {}

    for slide_key, shapes_dict in inventory.items():
        for shape_key, shape_data in shapes_dict.items():
            # Check for frame overflow (text exceeding shape bounds)
            if shape_data.frame_overflow_bottom is not None:
                if slide_key not in overflow_map:
                    overflow_map[slide_key] = {}
                overflow_map[slide_key][shape_key] = shape_data.frame_overflow_bottom

    return overflow_map


def validate_replacements(inventory: InventoryData, replacements: dict) -> list[str]:
    """Validate that all shapes in replacements exist in inventory.

    Returns list of error messages.
    """
    errors = []

    for slide_key, shapes_data in replacements.items():
        if not slide_key.startswith("slide-"):
            continue

        # Check if slide exists
        if slide_key not in inventory:
            errors.append(f"Slide '{slide_key}' not found in inventory")
            continue

        # Check each shape
        for shape_key in shapes_data.keys():
            if shape_key not in inventory[slide_key]:
                # Find shapes without replacements defined and show their content
                unused_with_content = []
                for k in inventory[slide_key].keys():
                    if k not in shapes_data:
                        shape_data = inventory[slide_key][k]
                        # Get text from paragraphs as preview
                        paragraphs = shape_data.paragraphs
                        if paragraphs and paragraphs[0].text:
                            first_text = paragraphs[0].text[:50]
                            if len(paragraphs[0].text) > 50:
                                first_text += "..."
                            unused_with_content.append(f"{k} ('{first_text}')")
                        else:
                            unused_with_content.append(k)

                errors.append(
                    f"Shape '{shape_key}' not found on '{slide_key}'. "
                    f"Shapes without replacements: {', '.join(sorted(unused_with_content)) if unused_with_content else 'none'}"
                )

    return errors


def check_duplicate_keys(pairs):
    """Check for duplicate keys when loading JSON."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate key found in JSON: '{key}'")
        result[key] = value
    return result


def apply_replacements(pptx_file: str, json_file: str, output_file: str):
    """Apply text replacements from JSON to PowerPoint presentation."""

    # Load presentation
    prs = Presentation(pptx_file)

    # Get inventory of all text shapes (returns ShapeData objects)
    # Pass prs to use same Presentation instance
    inventory = extract_text_inventory(Path(pptx_file), prs)

    # Detect text overflow in original presentation
    original_overflow = detect_frame_overflow(inventory)

    # Load replacement data with duplicate key detection
    with open(json_file) as f:
        replacements = json.load(f, object_pairs_hook=check_duplicate_keys)

    # Validate replacements
    errors = validate_replacements(inventory, replacements)
    if errors:
        print("ERROR: Invalid shapes in replacement JSON:")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease check the inventory and update your replacement JSON.")
        print(
            "You can regenerate the inventory with: python inventory.py <input.pptx> <output.json>"
        )
        raise ValueError(f"Found {len(errors)} validation error(s)")

    # Track statistics
    shapes_processed = 0
    shapes_cleared = 0
    shapes_replaced = 0

    # Process each slide from inventory
    for slide_key, shapes_dict in inventory.items():
        if not slide_key.startswith("slide-"):
            continue

        slide_index = int(slide_key.split("-")[1])

        if slide_index >= len(prs.slides):
            print(f"Warning: Slide {slide_index} not found")
            continue

        # Process each shape from inventory
        for shape_key, shape_data in shapes_dict.items():
            shapes_processed += 1

            # Get the shape directly from ShapeData
            shape = shape_data.shape
            if not shape:
                print(f"Warning: {shape_key} has no shape reference")
                continue

            # ShapeData already validates text_frame in __init__
            text_frame = shape.text_frame  # type: ignore

            text_frame.clear()  # type: ignore
            shapes_cleared += 1

            # Check for replacement paragraphs
            replacement_shape_data = replacements.get(slide_key, {}).get(shape_key, {})
            if "paragraphs" not in replacement_shape_data:
                continue

            shapes_replaced += 1

            # Add replacement paragraphs
            for i, para_data in enumerate(replacement_shape_data["paragraphs"]):
                if i == 0:
                    p = text_frame.paragraphs[0]  # type: ignore
                else:
                    p = text_frame.add_paragraph()  # type: ignore

                apply_paragraph_properties(p, para_data)

    # Check for issues after replacements
    # Save to a temporary file and reload to avoid modifying the presentation during inventory
    # (extract_text_inventory accesses font.color which adds empty <a:solidFill/> elements)
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        prs.save(str(tmp_path))

    try:
        updated_inventory = extract_text_inventory(tmp_path)
        updated_overflow = detect_frame_overflow(updated_inventory)
    finally:
        tmp_path.unlink()  # Clean up temp file

    # Check if any text overflow got worse
    overflow_errors = []
    for slide_key, shape_overflows in updated_overflow.items():
        for shape_key, new_overflow in shape_overflows.items():
            # Get original overflow (0 if there was no overflow before)
            original = original_overflow.get(slide_key, {}).get(shape_key, 0.0)

            # Error if overflow increased
            if new_overflow > original + 0.01:  # Small tolerance for rounding
                increase = new_overflow - original
                overflow_errors.append(
                    f'{slide_key}/{shape_key}: overflow worsened by {increase:.2f}" '
                    f'(was {original:.2f}", now {new_overflow:.2f}")'
                )

    # Collect warnings from updated shapes
    warnings = []
    for slide_key, shapes_dict in updated_inventory.items():
        for shape_key, shape_data in shapes_dict.items():
            if shape_data.warnings:
                for warning in shape_data.warnings:
                    warnings.append(f"{slide_key}/{shape_key}: {warning}")

    # Fail if there are any issues
    if overflow_errors or warnings:
        print("\nERROR: Issues detected in replacement output:")
        if overflow_errors:
            print("\nText overflow worsened:")
            for error in overflow_errors:
                print(f"  - {error}")
        if warnings:
            print("\nFormatting warnings:")
            for warning in warnings:
                print(f"  - {warning}")
        print("\nPlease fix these issues before saving.")
        raise ValueError(
            f"Found {len(overflow_errors)} overflow error(s) and {len(warnings)} warning(s)"
        )

    # Save the presentation
    prs.save(output_file)

    # Report results
    print(f"Saved updated presentation to: {output_file}")
    print(f"Processed {len(prs.slides)} slides")
    print(f"  - Shapes processed: {shapes_processed}")
    print(f"  - Shapes cleared: {shapes_cleared}")
    print(f"  - Shapes replaced: {shapes_replaced}")


def pptx_replace_text(
    pptx_path: Path | str,
    replacements: dict[str, str] | dict[str, Any] | Path | str,
    output_path: Path | str | None = None,
    match_font_style: bool = True,
) -> Path:
    """Perform text search-and-replace across slides while preserving typography.

    Args:
        pptx_path: Path to source presentation (.pptx)
        replacements: Either a dict mapping search string to replacement string,
                      or a structured inventory dict/path from inventory.py.
        output_path: Destination PPTX file path (defaults to overwriting pptx_path).
        match_font_style: If True, preserves existing font styles when replacing.

    Returns:
        Path to output presentation file.
    """
    in_file = Path(pptx_path)
    out_file = Path(output_path) if output_path is not None else in_file

    if isinstance(replacements, (str, Path)):
        apply_replacements(str(in_file), str(replacements), str(out_file))
        return out_file

    if isinstance(replacements, dict):
        is_inventory_dict = any(
            isinstance(v, dict) and any(isinstance(sv, (dict, list)) for sv in v.values())
            for v in replacements.values()
        )
        if is_inventory_dict:
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8"
            ) as tf:
                json.dump(replacements, tf)
                temp_json = tf.name
            try:
                apply_replacements(str(in_file), temp_json, str(out_file))
            finally:
                Path(temp_json).unlink(missing_ok=True)
            return out_file

        def _replace_in_text_frame(tf: Any) -> None:
            for paragraph in tf.paragraphs:
                for run in paragraph.runs:
                    for find_str, repl_str in replacements.items():
                        if str(find_str) in run.text:
                            run.text = run.text.replace(str(find_str), str(repl_str))

        def _replace_in_shape(sp: Any) -> None:
            if getattr(sp, "has_text_frame", False):
                _replace_in_text_frame(sp.text_frame)
            if getattr(sp, "has_table", False):
                for row in sp.table.rows:
                    for cell in row.cells:
                        if cell.text_frame:
                            _replace_in_text_frame(cell.text_frame)
            # Recursively handle GroupShape child shapes
            group_shapes = getattr(sp, "shapes", None)
            if group_shapes is not None:
                for child in group_shapes:
                    _replace_in_shape(child)

        prs = Presentation(str(in_file))
        for slide in prs.slides:
            for shape in slide.shapes:
                _replace_in_shape(shape)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        prs.save(str(out_file))
        return out_file

    raise TypeError(f"Unsupported replacements type: {type(replacements)}")


def main():
    """Main entry point for command-line usage."""
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)

    input_pptx = Path(sys.argv[1])
    replacements_json = Path(sys.argv[2])
    output_pptx = Path(sys.argv[3])

    if not input_pptx.exists():
        print(f"Error: Input file '{input_pptx}' not found")
        sys.exit(1)

    if not replacements_json.exists():
        print(f"Error: Replacements JSON file '{replacements_json}' not found")
        sys.exit(1)

    try:
        apply_replacements(str(input_pptx), str(replacements_json), str(output_pptx))
    except Exception as e:
        print(f"Error applying replacements: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
