"""
Pricing Engine
Calculates selling prices with margin rules
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging

from ..document_processor.unifier import UnifiedProduct

logger = logging.getLogger(__name__)


@dataclass
class PricingRule:
    """Pricing rule configuration"""
    category: Optional[str] = None  # Product category
    margin_percent: float = 15.0  # Default margin percentage
    min_margin_amount: Optional[float] = None  # Minimum margin in currency
    tier_rules: List[Dict] = field(default_factory=list)  # Quantity-based tiers


@dataclass
class PricedProduct:
    """Product with calculated selling price"""
    # Original product data
    sku: str
    description: str
    quantity: int
    vendor_unit_price: float  # Cost from vendor
    vendor_total: float  # Total cost from vendor
    
    # Calculated pricing
    margin_percent: float
    margin_amount: float  # Margin in currency
    selling_unit_price: float
    selling_total: float
    
    # Metadata
    category: Optional[str] = None
    pricing_rule_applied: Optional[str] = None
    raw_product: Optional[UnifiedProduct] = None


@dataclass
class QuoteSummary:
    """Quote summary totals"""
    total_vendor_cost: float
    total_margin: float
    total_selling_price: float
    margin_percent_avg: float
    product_count: int
    category_breakdown: Dict[str, Dict] = field(default_factory=dict)


class PricingEngine:
    """Calculate selling prices based on vendor costs and margin rules"""
    
    def __init__(self, config: Dict):
        """
        Initialize pricing engine
        
        Args:
            config: Configuration dictionary with pricing rules
        """
        self.config = config
        self.default_margin = config.get('pricing', {}).get('default_margin_percent', 15.0)
        self.rules = self._load_rules(config)
    
    def _load_rules(self, config: Dict) -> Dict[str, PricingRule]:
        """Load pricing rules from configuration"""
        rules = {}
        
        # Default rule
        rules['default'] = PricingRule(
            margin_percent=self.default_margin
        )
        
        # Category-specific rules
        margin_rules = config.get('pricing', {}).get('margin_rules', [])
        for rule_config in margin_rules:
            category = rule_config.get('category')
            if category:
                rules[category] = PricingRule(
                    category=category,
                    margin_percent=rule_config.get('margin', self.default_margin),
                    min_margin_amount=rule_config.get('min_margin_amount'),
                    tier_rules=rule_config.get('tier_rules', [])
                )
        
        return rules
    
    def calculate_prices(self, products: List[UnifiedProduct]) -> List[PricedProduct]:
        """
        Calculate selling prices for all products
        
        Args:
            products: List of UnifiedProduct objects
            
        Returns:
            List of PricedProduct objects with calculated prices
        """
        priced_products = []
        
        for product in products:
            priced = self._calculate_product_price(product)
            priced_products.append(priced)
        
        return priced_products
    
    def _calculate_product_price(self, product: UnifiedProduct) -> PricedProduct:
        """Calculate price for a single product"""
        vendor_unit_price = product.unit_price
        vendor_total = vendor_unit_price * product.quantity
        
        # Determine which rule to apply
        rule = self._get_rule_for_product(product)
        
        # Calculate margin
        margin_percent = rule.margin_percent
        margin_amount_per_unit = vendor_unit_price * (margin_percent / 100)
        
        # Apply minimum margin if specified
        if rule.min_margin_amount and margin_amount_per_unit < rule.min_margin_amount:
            margin_amount_per_unit = rule.min_margin_amount
            margin_percent = (margin_amount_per_unit / vendor_unit_price) * 100
        
        # Check tier rules (quantity-based pricing)
        tier_margin = self._check_tier_rules(rule, product.quantity)
        if tier_margin is not None:
            margin_percent = tier_margin
            margin_amount_per_unit = vendor_unit_price * (margin_percent / 100)
        
        selling_unit_price = vendor_unit_price + margin_amount_per_unit
        selling_total = selling_unit_price * product.quantity
        total_margin = margin_amount_per_unit * product.quantity
        
        return PricedProduct(
            sku=product.sku,
            description=product.description,
            quantity=product.quantity,
            vendor_unit_price=vendor_unit_price,
            vendor_total=vendor_total,
            margin_percent=margin_percent,
            margin_amount=margin_amount_per_unit,
            selling_unit_price=selling_unit_price,
            selling_total=selling_total,
            category=getattr(product, 'category', None),
            pricing_rule_applied=rule.category or 'default',
            raw_product=product
        )
    
    def _get_rule_for_product(self, product: UnifiedProduct) -> PricingRule:
        """Get appropriate pricing rule for product"""
        category = getattr(product, 'category', None) or product.metadata.get('category')
        
        if category and category in self.rules:
            return self.rules[category]
        
        return self.rules['default']
    
    def _check_tier_rules(self, rule: PricingRule, quantity: int) -> Optional[float]:
        """Check if tier-based pricing applies"""
        if not rule.tier_rules:
            return None
        
        for tier in sorted(rule.tier_rules, key=lambda x: x.get('min_quantity', 0), reverse=True):
            min_qty = tier.get('min_quantity', 0)
            if quantity >= min_qty:
                return tier.get('margin_percent')
        
        return None
    
    def generate_summary(self, priced_products: List[PricedProduct]) -> QuoteSummary:
        """Generate quote summary with totals"""
        total_vendor_cost = sum(p.vendor_total for p in priced_products)
        total_selling_price = sum(p.selling_total for p in priced_products)
        total_margin = total_selling_price - total_vendor_cost
        margin_percent_avg = (total_margin / total_vendor_cost * 100) if total_vendor_cost > 0 else 0
        
        # Category breakdown
        category_breakdown = {}
        for product in priced_products:
            cat = product.category or 'uncategorized'
            if cat not in category_breakdown:
                category_breakdown[cat] = {
                    'count': 0,
                    'vendor_total': 0,
                    'selling_total': 0,
                    'margin_total': 0
                }
            
            category_breakdown[cat]['count'] += 1
            category_breakdown[cat]['vendor_total'] += product.vendor_total
            category_breakdown[cat]['selling_total'] += product.selling_total
            category_breakdown[cat]['margin_total'] += (product.selling_total - product.vendor_total)
        
        return QuoteSummary(
            total_vendor_cost=total_vendor_cost,
            total_margin=total_margin,
            total_selling_price=total_selling_price,
            margin_percent_avg=margin_percent_avg,
            product_count=len(priced_products),
            category_breakdown=category_breakdown
        )

