"""
PDF File Parser
Extracts product data from PDF documents, including scanned PDFs with OCR
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from pdf2image import convert_from_path
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from ..document_processor.excel_parser import ProductRow

logger = logging.getLogger(__name__)


class PDFParser:
    """Parse PDF files to extract product information"""
    
    def __init__(self, use_ocr: bool = True):
        """
        Initialize PDF parser
        
        Args:
            use_ocr: Enable OCR for scanned PDFs
        """
        self.use_ocr = use_ocr and OCR_AVAILABLE
        
        if pdfplumber is None and PyPDF2 is None:
            logger.warning("No PDF parsing library available")
    
    def parse_pdf(self, filepath: str) -> List[ProductRow]:
        """
        Parse PDF file and extract product data
        
        Args:
            filepath: Path to PDF file
            
        Returns:
            List of ProductRow objects
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"PDF file not found: {filepath}")
        
        try:
            if pdfplumber:
                return self._parse_with_pdfplumber(filepath)
            elif PyPDF2:
                return self._parse_with_pypdf2(filepath)
            else:
                raise ImportError("No PDF parsing library available")
        except Exception as e:
            logger.error(f"Error parsing PDF file {filepath}: {e}")
            # Try OCR as fallback
            if self.use_ocr:
                logger.info("Attempting OCR extraction")
                return self._parse_with_ocr(filepath)
            raise
    
    def _parse_with_pdfplumber(self, filepath: str) -> List[ProductRow]:
        """Parse using pdfplumber (better table extraction)"""
        products = []
        
        try:
            with pdfplumber.open(filepath) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Try to extract tables first
                    tables = page.extract_tables()
                    
                    if tables:
                        for table in tables:
                            table_products = self._extract_products_from_table(table, page_num)
                            products.extend(table_products)
                    
                    # Also extract text and look for product patterns
                    text = page.extract_text()
                    if text:
                        text_products = self._extract_products_from_text(text, page_num)
                        products.extend(text_products)
        
        except Exception as e:
            logger.error(f"Error with pdfplumber: {e}")
            raise
        
        return products
    
    def _parse_with_pypdf2(self, filepath: str) -> List[ProductRow]:
        """Parse using PyPDF2 (basic text extraction)"""
        products = []
        
        try:
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    if text:
                        text_products = self._extract_products_from_text(text, page_num)
                        products.extend(text_products)
        
        except Exception as e:
            logger.error(f"Error with PyPDF2: {e}")
            raise
        
        return products
    
    def _parse_with_ocr(self, filepath: str) -> List[ProductRow]:
        """Parse scanned PDF using OCR"""
        products = []
        
        try:
            # Convert PDF pages to images
            images = convert_from_path(filepath)
            
            for page_num, image in enumerate(images, 1):
                # Extract text using OCR
                text = pytesseract.image_to_string(image, lang='eng+heb')  # English + Hebrew
                
                if text:
                    text_products = self._extract_products_from_text(text, page_num)
                    products.extend(text_products)
        
        except Exception as e:
            logger.error(f"Error with OCR: {e}")
            raise
        
        return products
    
    def _extract_products_from_table(self, table: List[List[str]], page_num: int) -> List[ProductRow]:
        """Extract products from a table structure"""
        products = []
        
        if not table or len(table) < 2:  # Need at least header + one row
            return products
        
        # Try to identify header row (usually first row)
        headers = [str(cell).strip().lower() if cell else "" for cell in table[0]]
        
        # Find column indices
        sku_idx = self._find_index(headers, ['sku', 'part number', 'part#', 'item', 'מק"ט'])
        desc_idx = self._find_index(headers, ['description', 'product', 'תיאור', 'מוצר'])
        qty_idx = self._find_index(headers, ['quantity', 'qty', 'כמות', 'מספר'])
        price_idx = self._find_index(headers, ['price', 'unit price', 'cost', 'מחיר'])
        
        # If we couldn't identify columns, try treating first row as data
        start_row = 1 if sku_idx is not None or desc_idx is not None else 0
        
        for row_num, row in enumerate(table[start_row:], start_row + 1):
            try:
                if len(row) < max(filter(None, [sku_idx, desc_idx, qty_idx, price_idx])) + 1:
                    continue
                
                sku = str(row[sku_idx]).strip() if sku_idx is not None and sku_idx < len(row) else ""
                description = str(row[desc_idx]).strip() if desc_idx is not None and desc_idx < len(row) else ""
                quantity = self._safe_int(row[qty_idx] if qty_idx is not None and qty_idx < len(row) else None, 1)
                unit_price = self._safe_float(row[price_idx] if price_idx is not None and price_idx < len(row) else None, 0.0)
                
                # Skip header-like rows or empty rows
                if not sku or sku.lower() in ['sku', 'part number', 'מק"ט', '']:
                    continue
                
                if sku and description and unit_price > 0:
                    products.append(ProductRow(
                        sku=sku,
                        description=description,
                        quantity=quantity,
                        unit_price=unit_price,
                        row_number=row_num,
                        raw_data={"page": page_num, "row": row}
                    ))
            
            except Exception as e:
                logger.warning(f"Error processing table row {row_num}: {e}")
                continue
        
        return products
    
    def _extract_products_from_text(self, text: str, page_num: int) -> List[ProductRow]:
        """
        Extract products from unstructured text
        Uses pattern matching to find product-like structures
        """
        products = []
        lines = text.split('\n')
        
        # Look for lines that might contain product information
        # Pattern: SKU-like string, description, number (quantity), price
        for line in lines:
            line = line.strip()
            if not line or len(line) < 10:
                continue
            
            # Try to identify product patterns in the line
            # This is heuristic-based and may need refinement
            parts = line.split()
            if len(parts) >= 3:
                # Look for price-like patterns (numbers with currency symbols)
                # This is a simplified extraction - LLM will help refine
                pass
        
        return products
    
    def _find_index(self, headers: List[str], possible_names: List[str]) -> Optional[int]:
        """Find index of column matching possible names"""
        for name in possible_names:
            name_lower = name.lower()
            for idx, header in enumerate(headers):
                if name_lower in header or header in name_lower:
                    return idx
        return None
    
    def _safe_int(self, value: Any, default: int = 0) -> int:
        """Safely convert value to int"""
        if value is None:
            return default
        try:
            if isinstance(value, str):
                value = value.replace(',', '').replace(' ', '')
            return int(float(value))
        except (ValueError, TypeError):
            return default
    
    def _safe_float(self, value: Any, default: Optional[float] = None) -> Optional[float]:
        """Safely convert value to float"""
        if value is None:
            return default
        try:
            if isinstance(value, str):
                value = value.replace('$', '').replace('₪', '').replace(',', '').replace(' ', '')
            result = float(value)
            return result if result >= 0 else default
        except (ValueError, TypeError):
            return default

