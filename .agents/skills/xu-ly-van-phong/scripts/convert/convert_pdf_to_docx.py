import sys


def convert_pdf_to_docx(pdf_file, output_file):
    """Convert PDF file to DOCX using pdf2docx."""
    try:
        from pdf2docx import Converter
    except ImportError as e:
        raise ImportError(
            "The library 'pdf2docx' is required for PDF to DOCX conversion. "
            "Please install it using: pip install pdf2docx"
        ) from e

    print(f"Converting {pdf_file} to {output_file}...")
    cv = Converter(pdf_file)
    cv.convert(output_file, start=0, end=None)
    cv.close()
    print(f"Created: {output_file}")


if __name__ == "__main__":
    if len(sys.argv) > 2:
        convert_pdf_to_docx(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python convert_pdf_to_docx.py <input.pdf> <output.docx>")
