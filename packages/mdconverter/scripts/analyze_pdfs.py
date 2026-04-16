"""
PDF Analysis Script — survey real-world PDFs to design auto-selection.

Analyzes PDF files in a directory to categorize them as:
- text_rich: digitally created, has extractable text
- scanned: image-only pages, needs OCR
- hybrid: mix of text and scanned pages
- drawing: CAD/engineering drawings (large page size, few text)

Outputs a summary table with recommendations for converter selection.
"""

import json
import sys
from pathlib import Path

import fitz  # PyMuPDF


def analyze_pdf(pdf_path: Path) -> dict:
    """Analyze a single PDF file."""
    result = {
        "file": pdf_path.name,
        "path": str(pdf_path),
        "size_mb": round(pdf_path.stat().st_size / (1024 * 1024), 2),
        "pages": 0,
        "text_pages": 0,
        "image_pages": 0,
        "drawing_pages": 0,
        "total_text_chars": 0,
        "total_images": 0,
        "avg_text_density": 0.0,  # chars per page
        "has_text_layer": False,
        "page_sizes": [],  # (w, h) in mm
        "is_oversized": False,  # A3+ (engineering drawings)
        "category": "unknown",
        "recommended_tool": "auto",
        "error": None,
    }

    try:
        doc = fitz.open(str(pdf_path))
        result["pages"] = len(doc)

        if len(doc) == 0:
            result["category"] = "empty"
            result["recommended_tool"] = "skip"
            doc.close()
            return result

        text_chars_per_page = []
        image_count_per_page = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Page size in mm
            rect = page.rect
            w_mm = round(rect.width * 25.4 / 72, 1)
            h_mm = round(rect.height * 25.4 / 72, 1)
            if page_num == 0:
                result["page_sizes"].append(f"{w_mm}x{h_mm}mm")

            # Check if oversized (A3+ = > 350mm in any dimension)
            if w_mm > 350 or h_mm > 350:
                result["is_oversized"] = True
                result["drawing_pages"] += 1

            # Extract text
            text = page.get_text("text")
            char_count = len(text.strip())
            text_chars_per_page.append(char_count)
            result["total_text_chars"] += char_count

            # Count images
            image_list = page.get_images(full=True)
            num_images = len(image_list)
            image_count_per_page.append(num_images)
            result["total_images"] += num_images

            # Classify page
            if char_count > 50:
                result["text_pages"] += 1
            elif num_images > 0:
                result["image_pages"] += 1

        doc.close()

        # Compute averages
        if result["pages"] > 0:
            result["avg_text_density"] = round(
                result["total_text_chars"] / result["pages"], 1
            )

        result["has_text_layer"] = result["total_text_chars"] > 100

        # Categorize
        text_ratio = result["text_pages"] / max(result["pages"], 1)
        image_ratio = result["image_pages"] / max(result["pages"], 1)
        drawing_ratio = result["drawing_pages"] / max(result["pages"], 1)

        if drawing_ratio > 0.5:
            result["category"] = "drawing"
            result["recommended_tool"] = "llm/ocr-primary"
        elif text_ratio > 0.8:
            result["category"] = "text_rich"
            result["recommended_tool"] = "llm/qwen3.5-35b"
        elif image_ratio > 0.8:
            result["category"] = "scanned"
            result["recommended_tool"] = "llm/ocr-primary"
        elif text_ratio > 0 and image_ratio > 0:
            result["category"] = "hybrid"
            result["recommended_tool"] = "llm/ocr-primary"
        else:
            result["category"] = "minimal_content"
            result["recommended_tool"] = "llm/gemini-3-flash"

    except Exception as e:
        result["error"] = str(e)
        result["category"] = "error"

    return result


def main(directory: str) -> None:
    """Analyze all PDFs in directory and output summary."""
    dir_path = Path(directory)
    if not dir_path.exists():
        print(f"Directory not found: {directory}")
        sys.exit(1)

    pdf_files = sorted(dir_path.rglob("*.pdf"))
    print(f"\nFound {len(pdf_files)} PDF files in {directory}\n")
    print("=" * 120)

    results = []
    categories = {"text_rich": 0, "scanned": 0, "hybrid": 0, "drawing": 0, "minimal_content": 0, "empty": 0, "error": 0}

    for pdf in pdf_files:
        r = analyze_pdf(pdf)
        results.append(r)
        categories[r["category"]] = categories.get(r["category"], 0) + 1

    # Print detailed results
    print(f"{'File':<45} {'Size':>7} {'Pages':>5} {'Txt/Img/Drw':>12} {'TextDen':>8} {'Category':<15} {'Tool'}")
    print("-" * 120)

    for r in results:
        if r["error"]:
            print(f"{r['file'][:44]:<45} {r['size_mb']:>6}M {'ERR':>5} {'':>12} {'':>8} {'ERROR':<15} -")
            continue
        tip = f"{r['text_pages']}/{r['image_pages']}/{r['drawing_pages']}"
        print(
            f"{r['file'][:44]:<45} {r['size_mb']:>6}M {r['pages']:>5} {tip:>12} "
            f"{r['avg_text_density']:>7.0f} {r['category']:<15} {r['recommended_tool']}"
        )

    # Summary
    print("\n" + "=" * 120)
    print("\n📊 CATEGORY SUMMARY:")
    total = len(results)
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        if count > 0:
            pct = round(count / total * 100, 1)
            print(f"  {cat:<20} {count:>4} files ({pct}%)")

    # Size stats
    sizes = [r["size_mb"] for r in results if not r["error"]]
    if sizes:
        print("\n📦 SIZE STATS:")
        print(f"  Total:   {sum(sizes):.1f} MB")
        print(f"  Min:     {min(sizes):.2f} MB")
        print(f"  Max:     {max(sizes):.2f} MB")
        print(f"  Average: {sum(sizes)/len(sizes):.2f} MB")

    # Page stats
    pages = [r["pages"] for r in results if not r["error"]]
    if pages:
        print("\n📄 PAGE STATS:")
        print(f"  Total:   {sum(pages)} pages")
        print(f"  Min:     {min(pages)} pages")
        print(f"  Max:     {max(pages)} pages")
        print(f"  Average: {sum(pages)/len(pages):.1f} pages")

    # Export JSON
    output_path = Path(__file__).parent / "pdf_analysis_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Full results exported to: {output_path}")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else r"D:\OneDrive - IBST BIM\00 CCBA\Thiet ke\2024-04 Ban DD HCM - BV NTP"
    main(target)
