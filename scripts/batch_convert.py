
import asyncio
import sys
import os
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mdconverter.config import settings
from chunked_convert import chunked_convert

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("batch_convert.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def process_directory(directory: Path):
    """Recursively process all PDFs in a directory."""
    
    pdf_files = list(directory.rglob("*.pdf"))
    total_files = len(pdf_files)
    
    logger.info(f"Found {total_files} PDF files in {directory}")
    
    for i, pdf_path in enumerate(pdf_files, 1):
        try:
            # Output MD file in the same directory
            output_path = pdf_path.with_suffix(".md")
            
            # Skip if already exists
            if output_path.exists():
                logger.info(f"[{i}/{total_files}] Skipping {pdf_path.name} (Markdown exists)")
                continue
                
            logger.info(f"[{i}/{total_files}] Processing {pdf_path.name}...")
            
            # Run chunked conversion (using imported function)
            # Default to 15 pages per chunk as verified in previous task
            await chunked_convert(pdf_path, output_path=output_path, pages_per_chunk=15)
            
            logger.info(f"[{i}/{total_files}] Successfully converted {pdf_path.name}")
            
        except Exception as e:
            logger.error(f"[{i}/{total_files}] Failed to convert {pdf_path.name}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python batch_convert.py <directory_path>")
        sys.exit(1)
        
    target_dir = Path(sys.argv[1])
    
    if not target_dir.exists():
        print(f"Error: Directory not found: {target_dir}")
        sys.exit(1)
        
    print(f"Starting batch conversion for: {target_dir}")
    asyncio.run(process_directory(target_dir))
