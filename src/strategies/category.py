"""Category discount strategy implementation."""

from decimal import Decimal
from typing import Dict

from src.strategies.base import DiscountStrategy, DiscountContext
from src.models import ValidationResult


class CategoryDiscountStrategy(DiscountStrategy):
    """
    Handles category-specific discounts (e.g., "Extra 10% off on T-shirts").
    Category discounts are applied after brand discounts, on the current_price.
    """

    def __init__(self, category_discounts: Dict[str, Decimal]):
        """
        Initialize category discount strategy.
        
        Args:
            category_discounts: Dictionary mapping category to discount percentage
                              (e.g., {"T-shirts": Decimal("10"), "Shoes": Decimal("15")})
        """
        self.category_discounts = category_discounts

    async def calculate(self, context: DiscountContext) -> Decimal:
        """
        Calculate total category discount across all cart items.
        
        This is applied on current_price (which may already have brand discount).
        
        Returns:
            Total discount amount applied
        """
        total_discount = Decimal("0")

        for cart_item in context.cart_items:
            category = cart_item.product.category
            if category in self.category_discounts:
                discount_percentage = self.category_discounts[category]
                # Calculate discount on current price (after brand discount)
                item_discount = (cart_item.product.current_price * discount_percentage / Decimal("100"))
                item_discount = item_discount.quantize(Decimal("0.01"))
                
                # Update current_price further
                cart_item.product.current_price = cart_item.product.current_price - item_discount
                
                # Add to total discount (multiplied by quantity)
                total_discount += item_discount * cart_item.quantity

        return total_discount.quantize(Decimal("0.01"))

    async def validate(self, context: DiscountContext) -> ValidationResult:
        """
        Category discounts are always valid - they're automatic.
        
        Returns:
            ValidationResult with is_valid=True
        """
        return ValidationResult(is_valid=True)

    def get_name(self) -> str:
        """Get the display name of this discount."""
        return "Category Discount"
