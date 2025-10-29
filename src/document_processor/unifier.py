"""
Data Unifier
Normalizes product data from different sources (Excel, PDF, inline tables)
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import logging

from .excel_parser import ProductRow

logger = logging.getLogger(__name__)


@dataclass
class UnifiedProduct:
    """Unified product structure from all sources"""
    sku: str
    description: str
    quantity: int
    unit_price: float
    total_price: Optional[float] = None
    source: str = "unknown"  # "excel", "pdf", "inline_table", "email_text"
    source_file: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0  # Confidence in extraction (0-1)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataUnifier:
    """Unify product data from multiple sources"""
    
    def __init__(self):
        pass
    
    def unify_products(self, sources: Dict[str, List[ProductRow]]) -> List[UnifiedProduct]:
        """
        Unify products from multiple sources
        
        Args:
            sources: Dictionary mapping source type to list of ProductRow objects
                    e.g., {"excel": [...], "pdf": [...], "inline_table": [...]}
        
        Returns:
            List of UnifiedProduct objects
        """
        unified = []
        
        for source_type, products in sources.items():
            for product in products:
                unified_product = UnifiedProduct(
                    sku=product.sku,
                    description=product.description,
                    quantity=product.quantity,
                    unit_price=product.unit_price,
                    total_price=product.total_price,
                    source=source_type,
                    source_file=getattr(product, 'source_file', None),
                    raw_data=product.raw_data or {},
                    confidence=1.0,
                    metadata={
                        "row_number": product.row_number,
                        "category": getattr(product, 'category', None)
                    }
                )
                unified.append(unified_product)
        
        return unified
    
    def deduplicate_products(self, products: List[UnifiedProduct]) -> List[UnifiedProduct]:
        """
        Deduplicate products based on SKU
        
        Args:
            products: List of UnifiedProduct objects
            
        Returns:
            Deduplicated list with quantities merged where appropriate
        """
        sku_map: Dict[str, UnifiedProduct] = {}
        
        for product in products:
            sku_normalized = self._normalize_sku(product.sku)
            
            if sku_normalized in sku_map:
                # Merge duplicate - combine quantities, use better data
                existing = sku_map[sku_normalized]
                
                # Preserve price - if current product has price and existing doesn't, use current
                # Or if both have prices, prefer the one with higher confidence or the latest non-zero price
                should_update_price = False
                if product.unit_price > 0 and existing.unit_price == 0:
                    should_update_price = True
                elif product.unit_price > 0 and product.confidence >= existing.confidence:
                    should_update_price = True
                
                if should_update_price:
                    existing.unit_price = product.unit_price
                
                # Add quantity to existing
                existing.quantity += product.quantity
                
                # Recalculate total price
                if existing.unit_price and existing.unit_price > 0:
                    existing.total_price = existing.unit_price * existing.quantity
                elif product.total_price:
                    # If we have a total price but no unit price, try to derive it
                    total_quantity = existing.quantity
                    if total_quantity > 0:
                        existing.unit_price = product.total_price / total_quantity
                        existing.total_price = product.total_price
                
                # Merge sources
                if product.source not in existing.metadata.get('sources', []):
                    if 'sources' not in existing.metadata:
                        existing.metadata['sources'] = []
                    existing.metadata['sources'].append(product.source)
            else:
                sku_map[sku_normalized] = product
        
        return list(sku_map.values())
    
    def _normalize_sku(self, sku: str) -> str:
        """
        Normalize SKU for comparison
        Removes spaces, converts to uppercase, removes special chars
        """
        if not sku:
            return ""
        return sku.strip().upper().replace(' ', '').replace('-', '').replace('_', '')
    
    def merge_duplicate_skus(self, products: List[UnifiedProduct], threshold: float = 0.9) -> List[UnifiedProduct]:
        """
        Merge products with similar (not identical) SKUs
        Uses similarity matching - for now, relies on LLM later
        
        Args:
            products: List of UnifiedProduct objects
            threshold: Similarity threshold (0-1)
        
        Returns:
            Merged list
        """
        # For now, just deduplicate exact matches
        # Advanced similarity matching will be done by LLM module
        return self.deduplicate_products(products)
    
    def validate_products(self, products: List[UnifiedProduct]) -> tuple[List[UnifiedProduct], List[Dict]]:
        """
        Validate product data
        
        Returns:
            Tuple of (valid products, validation errors)
        """
        valid = []
        errors = []
        
        for product in products:
            errors_for_product = []
            
            # Validate SKU
            if not product.sku or len(product.sku.strip()) == 0:
                errors_for_product.append("Missing SKU")
            
            # Validate description
            if not product.description or len(product.description.strip()) < 3:
                errors_for_product.append("Missing or too short description")
            
            # Validate quantity
            if product.quantity <= 0:
                errors_for_product.append(f"Invalid quantity: {product.quantity}")
            
            # Validate price (optional - may be extracted from email or added later)
            if product.unit_price < 0:  # Allow 0.0 (price unknown) but reject negatives
                errors_for_product.append(f"Invalid unit price: {product.unit_price}")
            
            if errors_for_product:
                errors.append({
                    "product": product.sku,
                    "errors": errors_for_product,
                    "source": product.source
                })
            else:
                valid.append(product)
        
        return valid, errors

