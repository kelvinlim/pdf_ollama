import fitz  # pymupdf
import logging
from typing import List

logger = logging.getLogger(__name__)

def clean_text_heuristics(pages_text: List[str]) -> str:
    """
    Remove identical headers and footers that appear on consecutive pages.
    """
    if not pages_text:
        return ""
    
    # A simple way to find common headers/footers is to compare the first/last lines
    # of consecutive pages. However, academic papers often have page numbers that change.
    # For now, we'll implement a basic version that looks for exact line matches 
    # at the very top or bottom across the majority of pages.
    
    # Split each page into lines
    pages_lines = [p.strip().split('\n') for p in pages_text]
    
    # Identify lines that appear at the same position (index) in many pages
    # This is a bit complex for a "heuristic", so let's start with 
    # removing exact matches of the first and last lines if they repeat.
    
    num_pages = len(pages_lines)
    if num_pages < 2:
        return "\n".join(pages_text)

    # Clean headers (top lines)
    header_lines_to_remove = set()
    first_lines = [lines[0] if lines else "" for lines in pages_lines]
    for line in set(first_lines):
        if line and first_lines.count(line) > (num_pages // 2):
            header_lines_to_remove.add(line)

    # Clean footers (bottom lines)
    footer_lines_to_remove = set()
    last_lines = [lines[-1] if lines else "" for lines in pages_lines]
    for line in set(last_lines):
        if line and last_lines.count(line) > (num_pages // 2):
            footer_lines_to_remove.add(line)

    if header_lines_to_remove or footer_lines_to_remove:
        logger.debug(f"Removing {len(header_lines_to_remove)} header patterns and {len(footer_lines_to_remove)} footer patterns.")

    cleaned_pages = []
    for lines in pages_lines:
        if not lines:
            continue
        filtered_lines = [l for i, l in enumerate(lines) if not (
            (i == 0 and l in header_lines_to_remove) or 
            (i == len(lines) - 1 and l in footer_lines_to_remove)
        )]
        cleaned_pages.append("\n".join(filtered_lines))

    return "\n\n".join(cleaned_pages)

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Read PDF and return cleaned text.
    """
    logger.debug(f"Opening PDF: {pdf_path}")
    doc = fitz.open(pdf_path)
    pages_text = []
    num_pages = len(doc)
    for i, page in enumerate(doc):
        if (i + 1) % 10 == 0 or i == 0 or i == num_pages - 1:
            logger.debug(f"Extracting page {i+1}/{num_pages}")
        pages_text.append(page.get_text())
    
    doc.close()
    return clean_text_heuristics(pages_text)
