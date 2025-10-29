"""
Excel File Parser
Extracts product data from Excel spreadsheets with support for multiple formats
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass

try:
    import openpyxl
    from openpyxl import load_workbook
except ImportError:
    openpyxl = None

try:
    import pandas as pd
except ImportError:
    pd = None

logger = logging.getLogger(__name__)


@dataclass
class ProductRow:
    """Single product row extracted from Excel"""
    sku: str
    description: str
    quantity: int
    unit_price: float
    total_price: Optional[float] = None
    category: Optional[str] = None
    row_number: int = 0
    raw_data: Dict[str, Any] = None


@dataclass
class ExcelSheetData:
    """Data extracted from a single Excel sheet"""
    sheet_name: str
    headers: List[str]
    products: List[ProductRow]
    raw_data: List[Dict]


class ExcelParser:
    """Parse Excel files to extract product information"""
    
    def __init__(self):
        if openpyxl is None and pd is None:
            logger.warning("No Excel parsing library available")
    
    def parse_excel(self, filepath: str, sheet_names: Optional[List[str]] = None) -> Dict[str, ExcelSheetData]:
        """
        Parse Excel file and extract product data
        
        Args:
            filepath: Path to Excel file
            sheet_names: Specific sheets to parse (None = all sheets)
            
        Returns:
            Dictionary mapping sheet names to ExcelSheetData
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Excel file not found: {filepath}")
        
        try:
            if pd:
                return self._parse_with_pandas(filepath, sheet_names)
            elif openpyxl:
                return self._parse_with_openpyxl(filepath, sheet_names)
            else:
                raise ImportError("No Excel parsing library available")
        except Exception as e:
            logger.error(f"Error parsing Excel file {filepath}: {e}")
            raise
    
    def _parse_with_pandas(self, filepath: str, sheet_names: Optional[List[str]] = None) -> Dict[str, ExcelSheetData]:
        """Parse using pandas (handles .xlsx and .xls)"""
        all_sheets = {}
        
        try:
            excel_file = pd.ExcelFile(filepath)
            sheets_to_process = sheet_names if sheet_names else excel_file.sheet_names
            
            for sheet_name in sheets_to_process:
                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    sheet_data = self._extract_products_from_dataframe(df, sheet_name)
                    all_sheets[sheet_name] = sheet_data
                except Exception as e:
                    logger.warning(f"Error processing sheet {sheet_name}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            raise
        
        return all_sheets
    
    def _parse_with_openpyxl(self, filepath: str, sheet_names: Optional[List[str]] = None) -> Dict[str, ExcelSheetData]:
        """Parse using openpyxl (handles .xlsx only)"""
        all_sheets = {}
        
        try:
            workbook = load_workbook(filepath, data_only=True)
            sheets_to_process = sheet_names if sheet_names else workbook.sheetnames
            
            for sheet_name in sheets_to_process:
                try:
                    worksheet = workbook[sheet_name]
                    df = pd.DataFrame(worksheet.values)
                    
                    # Set first row as headers
                    if len(df) > 0:
                        df.columns = df.iloc[0]
                        df = df[1:].reset_index(drop=True)
                    
                    sheet_data = self._extract_products_from_dataframe(df, sheet_name)
                    all_sheets[sheet_name] = sheet_data
                except Exception as e:
                    logger.warning(f"Error processing sheet {sheet_name}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            raise
        
        return all_sheets
    
    def _extract_products_from_dataframe(self, df: pd.DataFrame, sheet_name: str) -> ExcelSheetData:
        """
        Extract product data from pandas DataFrame
        
        Attempts to identify columns containing SKU, description, quantity, price
        """
        if df.empty:
            return ExcelSheetData(
                sheet_name=sheet_name,
                headers=[],
                products=[],
                raw_data=[]
            )
        
        headers = list(df.columns)
        products = []
        raw_data = df.to_dict('records')
        
        # Try to identify relevant columns
        sku_col = self._find_column(df, ['sku', 'part number', 'part#', 'item', 'product code', 'מק"ט'])
        desc_col = self._find_column(df, ['description', 'product', 'item description', 'תיאור', 'מוצר'])
        qty_col = self._find_column(df, ['quantity', 'qty', 'amount', 'כמות', 'מספר'])
        price_col = self._find_column(df, ['price', 'unit price', 'cost', 'מחיר', 'מחיר יחידה'])
        total_col = self._find_column(df, ['total', 'line total', 'total price', 'סה"כ', 'סה"כ שורה'])
        
        if not all([sku_col, desc_col, qty_col, price_col]):
            logger.warning(f"Could not identify all required columns in sheet {sheet_name}")
            logger.info(f"Found columns: SKU={sku_col}, Desc={desc_col}, Qty={qty_col}, Price={price_col}")
        
        # Extract product rows
        for idx, row in df.iterrows():
            try:
                sku = str(row[sku_col]).strip() if sku_col and sku_col in row else ""
                description = str(row[desc_col]).strip() if desc_col and desc_col in row else ""
                
                # Skip header rows or empty rows
                if not sku or sku.lower() in ['sku', 'part number', 'מק"ט', '']:
                    continue
                
                # Parse quantity
                quantity = self._safe_int(row.get(qty_col) if qty_col else None, 1)
                
                # Parse prices
                unit_price = self._safe_float(row.get(price_col) if price_col else None, 0.0)
                total_price = self._safe_float(row.get(total_col) if total_col else None, None)
                
                # Calculate total if not provided
                if total_price is None and unit_price and quantity:
                    total_price = unit_price * quantity
                
                if sku and description and unit_price > 0:
                    products.append(ProductRow(
                        sku=sku,
                        description=description,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=total_price,
                        row_number=idx + 2,  # +1 for 0-index, +1 for header
                        raw_data=row.to_dict()
                    ))
            
            except Exception as e:
                logger.warning(f"Error processing row {idx} in sheet {sheet_name}: {e}")
                continue
        
        return ExcelSheetData(
            sheet_name=sheet_name,
            headers=headers,
            products=products,
            raw_data=raw_data
        )
    
    def _find_column(self, df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
        """Find column by matching possible names (case-insensitive)"""
        columns_lower = {col.lower(): col for col in df.columns}
        
        for name in possible_names:
            name_lower = name.lower()
            # Exact match
            if name_lower in columns_lower:
                return columns_lower[name_lower]
            # Partial match
            for col in df.columns:
                if name_lower in col.lower() or col.lower() in name_lower:
                    return col
        
        return None
    
    def _safe_int(self, value: Any, default: int = 0) -> int:
        """Safely convert value to int"""
        if value is None:
            return default
        try:
            if isinstance(value, str):
                # Remove commas, spaces
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
                # Remove currency symbols, commas
                value = value.replace('$', '').replace('₪', '').replace(',', '').replace(' ', '')
            result = float(value)
            return result if result >= 0 else default
        except (ValueError, TypeError):
            return default
    
    def merge_sheets(self, sheets_data: Dict[str, ExcelSheetData]) -> List[ProductRow]:
        """
        Merge products from multiple sheets into single list
        
        Args:
            sheets_data: Dictionary of sheet data
            
        Returns:
            Combined list of ProductRow objects
        """
        all_products = []
        
        for sheet_data in sheets_data.values():
            all_products.extend(sheet_data.products)
        
        return all_products

