"""
Email Content Extractor
Extracts and structures relevant information from email body for agent understanding
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class EmailContext:
    """Structured email context for agent understanding"""
    # Basic metadata
    from_address: str
    to_addresses: List[str]
    subject: str
    email_chain: List[str] = field(default_factory=list)  # Email conversation chain
    
    # Extracted information
    customer_mentions: List[str] = field(default_factory=list)
    product_descriptions: List[str] = field(default_factory=list)
    special_notes: List[str] = field(default_factory=list)
    quantities_mentioned: List[Dict] = field(default_factory=list)
    prices_mentioned: List[Dict] = field(default_factory=list)
    
    # Structured content
    inline_tables: List[Dict] = field(default_factory=list)
    specifications: List[str] = field(default_factory=list)
    
    # Full text for reference
    full_body_text: str = ""
    full_body_html: Optional[str] = None
    
    # Language
    language: str = "en"


class EmailContentExtractor:
    """Extract and structure email content for agent processing"""
    
    def __init__(self):
        self.specification_patterns = [
            r'\d+\s*[GM]B?\s+(?:RAM|Memory|DDR)',
            r'\d+\s*[GT]B?\s+(?:SSD|HDD|Storage|NVME)',
            r'\d+x\s+\d+[GM]Hz',  # CPU frequencies
            r'\d+U?\s+server',  # Server size
            r'CPU|processor|Xeon|Intel|AMD',
            r'port[s]?|פורטים',
            r'gigabit|10G|25G|100G',
        ]
    
    def extract_context(self, metadata) -> EmailContext:
        """
        Extract structured context from email metadata
        
        Args:
            metadata: EmailMetadata object
            
        Returns:
            EmailContext with structured information
        """
        context = EmailContext(
            from_address=metadata.from_address,
            to_addresses=metadata.to_addresses or [],
            subject=metadata.subject,
            full_body_text=metadata.body_text or "",
            full_body_html=metadata.body_html,
            language=metadata.language
        )
        
        # Extract email chain
        context.email_chain = self._extract_email_chain(metadata.body_text)
        
        # Extract customer/vendor mentions
        context.customer_mentions = self._extract_customer_mentions(metadata.body_text)
        
        # Extract product descriptions
        context.product_descriptions = self._extract_product_descriptions(metadata.body_text)
        
        # Extract special notes (Hebrew/English)
        context.special_notes = self._extract_notes(metadata.body_text)
        
        # Extract specifications
        context.specifications = self._extract_specifications(metadata.body_text)
        
        # Extract quantities and prices mentioned in text
        context.quantities_mentioned = self._extract_quantities(metadata.body_text)
        context.prices_mentioned = self._extract_prices(metadata.body_text)
        
        # Inline tables are already extracted by parser
        # They will be added separately
        
        return context
    
    def _extract_email_chain(self, body_text: str) -> List[str]:
        """Extract email conversation chain"""
        chain = []
        
        # Look for "From:" patterns indicating email chain
        from_pattern = r'From:\s*([^\n]+(?:\n(?!From:)[^\n]+)*)'
        matches = re.finditer(from_pattern, body_text, re.IGNORECASE | re.MULTILINE)
        
        for match in matches:
            chain_segment = match.group(1).strip()
            if len(chain_segment) > 20:  # Filter out very short segments
                chain.append(chain_segment[:500])  # Limit length
        
        return chain
    
    def _extract_customer_mentions(self, body_text: str) -> List[str]:
        """Extract customer/vendor names mentioned in email"""
        mentions = []
        
        # Look for common patterns
        patterns = [
            r'(?:customer|client|vendor|לקוח|ספק)[\s:]+([A-Za-z\s-]{3,30})',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:is|נמצא|הוא)',  # Name patterns
            r'<([^>@]+@[^>]+)>',  # Email addresses with names
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, body_text, re.IGNORECASE)
            for match in matches:
                mention = match.group(1).strip()
                if mention and len(mention) > 3:
                    mentions.append(mention)
        
        return list(set(mentions))  # Remove duplicates
    
    def _extract_product_descriptions(self, body_text: str) -> List[str]:
        """Extract product descriptions from email body"""
        descriptions = []
        
        # Look for product-like sentences
        # Patterns: "X server with...", "Y quantity of Z", product lists
        product_indicators = [
            r'\d+U?\s+server[^\n]{10,200}',
            r'(?:server|storage|network|firewall|gpu)[^\n]{10,150}',
            r'\d+x\s+[A-Z0-9]+[^\n]{5,100}',  # "2x XYZ123..."
            r'CPU|SSD|HDD|RAM[^\n]{5,100}',
        ]
        
        for pattern in product_indicators:
            matches = re.finditer(pattern, body_text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                desc = match.group(0).strip()
                if len(desc) > 10:
                    descriptions.append(desc)
        
        return descriptions
    
    def _extract_notes(self, body_text: str) -> List[str]:
        """Extract special notes, warnings, or important information"""
        notes = []
        
        # Hebrew note patterns
        hebrew_patterns = [
            r'(חשוב|שכחתי|נא|שים\s+לב|הערה)[:;]?\s*([^\n]{10,200})',
            r'(אלון|יוסי|valentina)[^\n]{5,150}',  # Person mentions with context
        ]
        
        # English note patterns
        english_patterns = [
            r'(?:important|note|attention|warning)[:;]?\s*([^\n]{10,200})',
            r'(?:please|remind|forgot)[^\n]{5,150}',
        ]
        
        all_patterns = hebrew_patterns + english_patterns
        
        for pattern in all_patterns:
            matches = re.finditer(pattern, body_text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                note = match.group(0).strip()
                if len(note) > 10:
                    notes.append(note)
        
        return notes
    
    def _extract_specifications(self, body_text: str) -> List[str]:
        """Extract technical specifications"""
        specs = []
        
        for pattern in self.specification_patterns:
            matches = re.finditer(pattern, body_text, re.IGNORECASE)
            for match in matches:
                spec = match.group(0).strip()
                if spec:
                    specs.append(spec)
        
        return list(set(specs))
    
    def _extract_quantities(self, body_text: str) -> List[Dict]:
        """Extract quantities mentioned in text"""
        quantities = []
        
        # Patterns like "2 ports", "200 GB", "1x CPU", etc.
        patterns = [
            (r'(\d+)\s*פורטים?', 'ports'),  # Hebrew
            (r'(\d+)\s+ports?', 'ports'),  # English
            (r'(\d+)\s*[GM]B', 'storage'),
            (r'(\d+)x\s+(\w+)', 'items'),
            (r'(\d+)\s*יחידות?', 'units'),  # Hebrew
        ]
        
        for pattern, unit in patterns:
            matches = re.finditer(pattern, body_text, re.IGNORECASE)
            for match in matches:
                qty = match.group(1)
                item = match.group(2) if len(match.groups()) > 1 else None
                quantities.append({
                    "quantity": int(qty),
                    "unit": unit,
                    "item": item,
                    "text": match.group(0)
                })
        
        return quantities
    
    def _extract_prices(self, body_text: str) -> List[Dict]:
        """Extract prices mentioned in text"""
        prices = []
        
        # Currency patterns
        patterns = [
            (r'[\$₪]?\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)\s*(?:USD|ILS|\$|₪)?', 'unknown'),
            (r'(\d+(?:[,\s]\d{3})*)\s*(?:ש\"ח|דולר)', 'ILS'),
        ]
        
        for pattern, currency in patterns:
            matches = re.finditer(pattern, body_text)
            for match in matches:
                price_text = match.group(1).replace(',', '').replace(' ', '')
                try:
                    price = float(price_text)
                    prices.append({
                        "amount": price,
                        "currency": currency,
                        "text": match.group(0)
                    })
                except ValueError:
                    continue
        
        return prices
    
    def to_structured_string(self, context: EmailContext) -> str:
        """
        Convert EmailContext to structured string for LLM/agent understanding
        
        Args:
            context: EmailContext object
            
        Returns:
            Formatted string with all relevant information
        """
        lines = []
        
        lines.append("=== EMAIL CONTEXT ===")
        lines.append(f"From: {context.from_address}")
        lines.append(f"Subject: {context.subject}")
        lines.append(f"Language: {context.language}")
        lines.append("")
        
        if context.customer_mentions:
            lines.append("=== CUSTOMER/VENDOR MENTIONS ===")
            for mention in context.customer_mentions:
                lines.append(f"- {mention}")
            lines.append("")
        
        if context.special_notes:
            lines.append("=== SPECIAL NOTES/IMPORTANT INFO ===")
            for note in context.special_notes:
                lines.append(f"- {note}")
            lines.append("")
        
        if context.product_descriptions:
            lines.append("=== PRODUCT DESCRIPTIONS ===")
            for desc in context.product_descriptions:
                lines.append(f"- {desc}")
            lines.append("")
        
        if context.specifications:
            lines.append("=== TECHNICAL SPECIFICATIONS ===")
            for spec in context.specifications:
                lines.append(f"- {spec}")
            lines.append("")
        
        if context.quantities_mentioned:
            lines.append("=== QUANTITIES MENTIONED ===")
            for qty in context.quantities_mentioned:
                lines.append(f"- {qty['quantity']} {qty.get('unit', '')} {qty.get('item', '')} ({qty['text']})")
            lines.append("")
        
        if context.email_chain:
            lines.append("=== EMAIL CONVERSATION CONTEXT ===")
            for i, segment in enumerate(context.email_chain[:3], 1):  # Limit to first 3
                lines.append(f"--- Email {i} ---")
                lines.append(segment[:300] + "..." if len(segment) > 300 else segment)
                lines.append("")
        
        lines.append("=== FULL EMAIL BODY (REFERENCE) ===")
        lines.append(context.full_body_text[:2000] + "..." if len(context.full_body_text) > 2000 else context.full_body_text)
        
        return "\n".join(lines)

