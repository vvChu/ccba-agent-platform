# CCBA PDF Preprocessor

> Tối ưu hóa PDF cho LLM: Phân đoạn (Segmenting), Chia nhỏ (Chunking) và Tiling cho AI Vision.

## Cài đặt

```bash
pip install -e "D:\GitHubProjects\ccba-agent-platform\packages\ccba-pdf-prep"
```

## CLI

```bash
# Phân tích PDF
ccba-pdf analyze path/to/file.pdf
ccba-pdf analyze path/to/folder --recursive --detail

# Xẻ bản vẽ thành tiles
ccba-pdf tile drawing.pdf --page 0 --dpi 300 --tile-size 1024

# Chia nhỏ PDF lớn
ccba-pdf split large_doc.pdf --chunk-size 20
```

## Python API

### Phân tích PDF

```python
from ccba_pdf_prep import PDFAnalyzer

analyzer = PDFAnalyzer()
report = analyzer.analyze("path/to/document.pdf")

print(report.category)       # text_rich | scanned | hybrid | drawing
print(report.pages)          # Số trang
print(report.recommended_model)  # Model AI gợi ý
```

### Chia nhỏ PDF

```python
from ccba_pdf_prep import split_pdf, get_blind_chunks
from pathlib import Path

ranges = get_blind_chunks(total_pages=100, chunk_size=20)
chunks = split_pdf(Path("large.pdf"), ranges, Path("./temp"))
```

### Vision Tiling

```python
from ccba_pdf_prep import VisionOptimizer
from pathlib import Path

tiles = VisionOptimizer.tile_page(
    pdf_path=Path("drawing.pdf"),
    page_num=0,
    output_dir=Path("./tiles"),
    dpi=300,
    tile_size_px=1024,
)
```

## Dependencies

- `pymupdf` (fitz) — PDF rendering and analysis
- `pypdf` — PDF splitting
- `typer` + `rich` — CLI
- `Pillow` — Image processing (Phase 2+)
