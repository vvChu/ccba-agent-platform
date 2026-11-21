# PPTX Design Palettes, Visual Patterns & Template Inventory Schema

Level 3 reference for `ccba-pptx`, containing curated color palettes, layout/typography detail options, template JSON inventory structures, and thumbnail/PDF conversion examples.

## 1. Curated Color Palettes (18 Presets)

1. **Classic Blue**: `#1C2833`, `#2E4053`, `#AAB7B8`, `#F4F6F6`
2. **Teal & Coral**: `#5EA8A7`, `#277884`, `#FE4447`, `#FFFFFF`
3. **Bold Red**: `#C0392B`, `#E74C3C`, `#F39C12`, `#F1C40F`, `#2ECC71`
4. **Warm Blush**: `#A49393`, `#EED6D3`, `#E8B4B8`, `#FAF7F2`
5. **Burgundy Luxury**: `#5D1D2E`, `#951233`, `#C15937`, `#997929`
6. **Deep Purple & Emerald**: `#B165FB`, `#181B24`, `#40695B`, `#FFFFFF`
7. **Cream & Forest Green**: `#FFE1C7`, `#40695B`, `#FCFCFC`
8. **Pink & Purple**: `#F8275B`, `#FF574A`, `#FF737D`, `#3D2F68`
9. **Lime & Plum**: `#C5DE82`, `#7C3A5F`, `#FD8C6E`, `#98ACB5`
10. **Black & Gold**: `#BF9A4A`, `#000000`, `#F4F6F6`
11. **Sage & Terracotta**: `#87A96B`, `#E07A5F`, `#F4F1DE`, `#2C2C2C`
12. **Charcoal & Red**: `#292929`, `#E33737`, `#CCCBCB`
13. **Vibrant Orange**: `#F96D00`, `#F2F2F2`, `#222831`
14. **Forest Green**: `#191A19`, `#4E9F3D`, `#1E5128`, `#FFFFFF`
15. **Retro Rainbow**: `#722880`, `#D72D51`, `#EB5C18`, `#F08800`, `#DEB600`
16. **Vintage Earthy**: `#E3B448`, `#CBD18F`, `#3A6B35`, `#F4F1DE`
17. **Coastal Rose**: `#AD7670`, `#B49886`, `#F3ECDC`, `#BFD5BE`
18. **Orange & Turquoise**: `#FC993E`, `#667C6F`, `#FCFCFC`

## 2. Visual Detail & Styling Options

- **Geometric Patterns:** Diagonal dividers, asymmetric columns (`30/70`, `40/60`, `25/75`), rotated text (`90°`/`270°`), circular/hexagonal image frames, corner accent triangles, overlapping shapes.
- **Borders & Frames:** Single-side thick bar (`10-20pt`), double-line borders, corner brackets, L-shaped borders, `3-5pt` header underlines.
- **Typography:** Extreme scale contrast (`72pt` vs `11pt`), wide-tracked all-caps headers, oversized section numbers, monospace (`Courier New`) for metrics, condensed fonts for dense tables.
- **Charts & Backgrounds:** Monochrome charts with 1 accent color, horizontal bars/dot plots, direct data labels (no legends), `40-60%` color blocks, split diagonal/vertical fills.

## 3. Template Inventory (`template-inventory.md`) & `outline.md`

```markdown
# Template Inventory Analysis
**Total Slides: [count]**
**IMPORTANT: Slides are 0-indexed (first slide = 0, last slide = count-1)**

## [Category Name]
- Slide 0: [Layout code] - Description/purpose
```

Example `outline.md` mapping:

```python
template_mapping = [0, 34, 34, 50, 54]
```

## 4. `inventory.py` Output Schema & `replacement-text.json`

```json
{
  "slide-0": {
    "shape-0": {
      "placeholder_type": "TITLE",
      "left": 1.5, "top": 2.0, "width": 7.5, "height": 1.2,
      "paragraphs": [
        {
          "text": "Paragraph text",
          "bullet": true,
          "level": 0,
          "alignment": "CENTER",
          "space_before": 10.0,
          "space_after": 6.0,
          "line_spacing": 22.4,
          "font_name": "Arial",
          "font_size": 14.0,
          "bold": true,
          "color": "FF0000"
        }
      ]
    }
  }
}
```

- Slides are `"slide-0"`, `"slide-1"`, ...; shapes ordered top-to-bottom, left-to-right as `"shape-0"`, ... (`SLIDE_NUMBER` filtered out).
- `replace.py` clears **all** inventory shapes unless `"paragraphs"` is provided in `replacement-text.json`.
- When `"bullet": true`, always pass `"level": 0` (or nesting depth), omit literal bullet characters (`•`, `-`, `*`), and do **not** set `"alignment"`.
- Validation errors report missing slide/shape IDs and exact overflow deltas (e.g., `overflow worsened by 1.25"`).

## 5. Thumbnail Grids & PDF-to-JPEG Inspection Options

- `python scripts/thumbnail.py template.pptx my-grid --cols 4` (`3` cols = `12` slides per grid, `4` = `20`, `5` = `30`, `6` = `42`).
- `soffice --headless --convert-to pdf template.pptx && pdftoppm -jpeg -r 150 -f 2 -l 5 template.pdf slide` (`-png` optional).
