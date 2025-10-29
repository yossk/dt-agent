"""
File Organizer
Creates organized folder structure for quotes and saves files
"""

import os
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import logging
import shutil
import json

logger = logging.getLogger(__name__)


class FileOrganizer:
    """Organize files according to customer/quotes/year/product/costs structure"""
    
    def __init__(self, config: Dict):
        """
        Initialize file organizer
        
        Args:
            config: Configuration dictionary with path settings
        """
        self.config = config
        self.base_path = config.get('paths', {}).get('base', '/data/quotes')
        self.structure_template = config.get('paths', {}).get('structure', '{customer}/{quotes}/{year}/{product}/{costs}')
        
        # Ensure base path exists
        os.makedirs(self.base_path, exist_ok=True)
    
    def build_path(self, customer: str, product: str, year: Optional[int] = None) -> str:
        """
        Build organized path for quote files
        
        Args:
            customer: Customer name
            product: Product or project name
            year: Year (defaults to current year)
            
        Returns:
            Full path string
        """
        if year is None:
            year = datetime.now().year
        
        # Replace template variables
        path = self.structure_template.format(
            customer=customer,
            quotes="quotes",
            year=str(year),
            product=product,
            costs="costs"
        )
        
        full_path = os.path.join(self.base_path, path)
        os.makedirs(full_path, exist_ok=True)
        
        return full_path
    
    def save_email(self, filepath: str, dest_folder: str, filename: Optional[str] = None) -> str:
        """
        Save original email file
        
        Args:
            filepath: Source email file path
            dest_folder: Destination folder (from build_path)
            filename: Optional custom filename
            
        Returns:
            Path to saved file
        """
        if filename is None:
            filename = f"original_email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.msg"
        
        dest_path = os.path.join(dest_folder, filename)
        shutil.copy2(filepath, dest_path)
        
        logger.info(f"Saved email to {dest_path}")
        return dest_path
    
    def save_vendor_quote(self, filepath: str, dest_folder: str, file_type: str = "excel") -> str:
        """
        Save vendor quote (Excel/PDF)
        
        Args:
            filepath: Source file path
            dest_folder: Destination folder
            file_type: "excel" or "pdf"
            
        Returns:
            Path to saved file
        """
        ext = ".xlsx" if file_type == "excel" else ".pdf"
        filename = f"vendor_quote_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        
        dest_path = os.path.join(dest_folder, filename)
        shutil.copy2(filepath, dest_path)
        
        logger.info(f"Saved vendor quote to {dest_path}")
        return dest_path
    
    def save_extracted_data(self, data: Dict, dest_folder: str) -> str:
        """
        Save extracted product data as JSON
        
        Args:
            data: Dictionary with extracted data
            dest_folder: Destination folder
            
        Returns:
            Path to saved JSON file
        """
        filename = f"extracted_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        dest_path = os.path.join(dest_folder, filename)
        
        with open(dest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Saved extracted data to {dest_path}")
        return dest_path
    
    def save_final_quote(self, filepath: str, dest_folder: str, quote_id: Optional[str] = None) -> str:
        """
        Save final generated quote
        
        Args:
            filepath: Source quote file path
            dest_folder: Destination folder
            quote_id: Optional quote identifier
            
        Returns:
            Path to saved file
        """
        if quote_id:
            filename = f"final_quote_{quote_id}.xlsx"
        else:
            filename = f"final_quote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        dest_path = os.path.join(dest_folder, filename)
        shutil.copy2(filepath, dest_path)
        
        logger.info(f"Saved final quote to {dest_path}")
        return dest_path
    
    def save_metadata(self, metadata: Dict, dest_folder: str) -> str:
        """
        Save processing metadata
        
        Args:
            metadata: Metadata dictionary
            dest_folder: Destination folder
            
        Returns:
            Path to saved metadata file
        """
        filename = f"metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        dest_path = os.path.join(dest_folder, filename)
        
        with open(dest_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2, default=str)
        
        return dest_path
    
    def create_summary(self, dest_folder: str) -> Dict:
        """
        Create summary of all files in destination folder
        
        Args:
            dest_folder: Folder to summarize
            
        Returns:
            Dictionary with file listing and metadata
        """
        if not os.path.exists(dest_folder):
            return {}
        
        files = []
        for filename in os.listdir(dest_folder):
            filepath = os.path.join(dest_folder, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                files.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "type": self._get_file_type(filename)
                })
        
        return {
            "folder": dest_folder,
            "file_count": len(files),
            "files": files,
            "created": datetime.now().isoformat()
        }
    
    def _get_file_type(self, filename: str) -> str:
        """Determine file type from extension"""
        ext = Path(filename).suffix.lower()
        type_map = {
            '.msg': 'email',
            '.xlsx': 'excel',
            '.xls': 'excel',
            '.pdf': 'pdf',
            '.json': 'data',
            '.html': 'html',
            '.txt': 'text'
        }
        return type_map.get(ext, 'unknown')

