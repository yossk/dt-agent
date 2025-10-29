"""
Email Parser for Outlook .msg files and email content extraction
Supports Hebrew and English content
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

try:
    import extract_msg
except ImportError:
    extract_msg = None

try:
    from mailparser import parse_from_file
except ImportError:
    parse_from_file = None

logger = logging.getLogger(__name__)


@dataclass
class EmailMetadata:
    """Email metadata structure"""
    from_address: str
    to_addresses: List[str]
    subject: str
    date: datetime
    message_id: str
    body_text: str
    body_html: Optional[str] = None
    attachments: List[Dict] = None
    language: str = "en"  # "en" or "he"


@dataclass
class AttachmentInfo:
    """Attachment information"""
    filename: str
    filepath: str
    content_type: str
    size: int


class EmailParser:
    """Parse Outlook .msg files and extract content"""
    
    def __init__(self):
        if extract_msg is None:
            logger.warning("extract_msg not available. Install with: pip install extract-msg")
    
    def parse_msg_file(self, filepath: str) -> EmailMetadata:
        """
        Parse Outlook .msg file
        
        Args:
            filepath: Path to .msg file
            
        Returns:
            EmailMetadata object with parsed email data
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Email file not found: {filepath}")
        
        try:
            if extract_msg:
                return self._parse_with_extract_msg(filepath)
            elif parse_from_file:
                return self._parse_with_mailparser(filepath)
            else:
                raise ImportError("No email parsing library available")
        except Exception as e:
            logger.error(f"Error parsing email file {filepath}: {e}")
            raise
    
    def _parse_with_extract_msg(self, filepath: str) -> EmailMetadata:
        """Parse using extract_msg library"""
        msg = extract_msg.Message(filepath)
        
        # Extract attachments
        attachments = []
        if msg.attachments:
            for att in msg.attachments:
                attachments.append({
                    "filename": att.longFilename or att.shortFilename,
                    "data": att.data,
                    "content_type": att.contentType or "application/octet-stream"
                })
        
        # Extract body
        body_html = msg.htmlBody if hasattr(msg, 'htmlBody') else None
        body_text = msg.body or msg.htmlBody or ""
        
        # Detect language
        language = self._detect_language(body_text)
        
        metadata = EmailMetadata(
            from_address=msg.sender or "",
            to_addresses=msg.to or [],
            subject=msg.subject or "",
            date=msg.date if hasattr(msg, 'date') else datetime.now(),
            message_id=msg.messageId if hasattr(msg, 'messageId') else "",
            body_text=body_text,
            body_html=body_html,
            attachments=attachments,
            language=language
        )
        
        msg.close()
        return metadata
    
    def _parse_with_mailparser(self, filepath: str) -> EmailMetadata:
        """Parse using mailparser library (alternative method)"""
        mail = parse_from_file(filepath)
        
        attachments = []
        if mail.attachments:
            for att in mail.attachments:
                attachments.append({
                    "filename": att.get('filename', 'unknown'),
                    "data": att.get('payload'),
                    "content_type": att.get('mail_content_type', 'application/octet-stream')
                })
        
        body_text = mail.text_plain[0] if mail.text_plain else (
            mail.text_html[0] if mail.text_html else ""
        )
        language = self._detect_language(body_text)
        
        return EmailMetadata(
            from_address=mail.from_[0] if mail.from_ else "",
            to_addresses=mail.to if mail.to else [],
            subject=mail.subject or "",
            date=mail.date if mail.date else datetime.now(),
            message_id=mail.message_id or "",
            body_text=body_text,
            body_html=mail.text_html[0] if mail.text_html else None,
            attachments=attachments,
            language=language
        )
    
    def extract_attachments(self, metadata: EmailMetadata, output_dir: str) -> List[AttachmentInfo]:
        """
        Extract attachments from email metadata to files
        
        Args:
            metadata: EmailMetadata object
            output_dir: Directory to save attachments
            
        Returns:
            List of AttachmentInfo objects
        """
        os.makedirs(output_dir, exist_ok=True)
        attachment_infos = []
        
        for i, att in enumerate(metadata.attachments or []):
            filename = att.get("filename", f"attachment_{i}")
            filepath = os.path.join(output_dir, filename)
            
            # Save attachment data
            with open(filepath, 'wb') as f:
                if isinstance(att.get("data"), bytes):
                    f.write(att["data"])
                else:
                    logger.warning(f"Could not extract attachment {filename}")
                    continue
            
            attachment_infos.append(AttachmentInfo(
                filename=filename,
                filepath=filepath,
                content_type=att.get("content_type", "application/octet-stream"),
                size=os.path.getsize(filepath)
            ))
        
        return attachment_infos
    
    def _detect_language(self, text: str) -> str:
        """
        Detect if text is Hebrew or English
        
        Args:
            text: Text to analyze
            
        Returns:
            "he" for Hebrew, "en" for English (default)
        """
        if not text:
            return "en"
        
        # Simple heuristic: check for Hebrew characters
        # Hebrew Unicode range: U+0590 to U+05FF
        hebrew_chars = sum(1 for char in text if '\u0590' <= char <= '\u05FF')
        total_chars = sum(1 for char in text if char.isalpha())
        
        if total_chars > 0 and hebrew_chars / total_chars > 0.1:
            return "he"
        
        return "en"
    
    def extract_inline_tables(self, metadata: EmailMetadata) -> List[Dict]:
        """
        Extract inline tables from email body (HTML or text)
        
        Args:
            metadata: EmailMetadata object
            
        Returns:
            List of table dictionaries with extracted data
        """
        tables = []
        
        # Try HTML first
        if metadata.body_html:
            tables.extend(self._extract_html_tables(metadata.body_html))
        
        # Also check text body for table-like structures
        if metadata.body_text:
            tables.extend(self._extract_text_tables(metadata.body_text))
        
        return tables
    
    def _extract_html_tables(self, html: str) -> List[Dict]:
        """Extract tables from HTML content"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.warning("BeautifulSoup not available for HTML parsing")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        tables = []
        
        for table in soup.find_all('table'):
            rows = []
            for tr in table.find_all('tr'):
                cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)
            
            if rows:
                tables.append({
                    "type": "html_table",
                    "data": rows,
                    "headers": rows[0] if rows else []
                })
        
        return tables
    
    def _extract_text_tables(self, text: str) -> List[Dict]:
        """
        Extract table-like structures from plain text
        Looks for tab-separated or space-aligned columns
        """
        lines = text.split('\n')
        tables = []
        current_table = []
        
        for line in lines:
            # Look for lines with multiple columns (tabs or multiple spaces)
            if '\t' in line or line.count('  ') >= 2:
                parts = [p.strip() for p in line.split('\t') if p.strip()]
                if len(parts) >= 2:  # At least 2 columns
                    current_table.append(parts)
            elif current_table:
                # End of table
                if len(current_table) > 1:
                    tables.append({
                        "type": "text_table",
                        "data": current_table,
                        "headers": current_table[0] if current_table else []
                    })
                current_table = []
        
        # Handle last table
        if current_table and len(current_table) > 1:
            tables.append({
                "type": "text_table",
                "data": current_table,
                "headers": current_table[0] if current_table else []
            })
        
        return tables

