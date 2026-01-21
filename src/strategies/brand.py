"""Brand discount strategy implementation."""

from decimal import Decimal
from typing import Dict

from src.strategies.base import DiscountStrategy, DiscountContext
from src.models import ValidationResult, BrandTier


class BrandDiscountStrategy(DiscountStrategy):
    """
    Handles brand-specific discounts (e.g., "Min 40% off on PUMA").
    Brand discounts are applied first and update the product's current_price.
    """

    def __init__(self, brand_discounts: Dict[str, Decimal]):
        """
        Initialize brand discount strategy.
        
        Args:
            brand_discounts: Dictionary mapping brand name to discount percentage
                           (e.g., {"PUMA": Decimal("40"), "NIKE": Decimal("30")})
        """
        self.brand_discounts = brand_discounts

    async def calculate(self, context: DiscountContext) -> Decimal:
        """
        Calculate total brand discount across all cart items.
        
        This method updates the current_price of products in the cart.
        
        Returns:
            Total discount amount applied
        """
        total_discount = Decimal("0")

        for cart_item in context.cart_items:
            brand = cart_item.product.brand
            if brand in self.brand_discounts:
                discount_percentage = self.brand_discounts[brand]
                # Calculate discount on base price
                item_discount = (cart_item.product.base_price * discount_percentage / Decimal("100"))
                item_discount = item_discount.quantize(Decimal("0.01"))
                
                # Update current_price
                cart_item.product.current_price = cart_item.product.base_price - item_discount
                
                # Add to total discount (multiplied by quantity)
                total_discount += item_discount * cart_item.quantity

        return total_discount.quantize(Decimal("0.01"))

    async def validate(self, context: DiscountContext) -> ValidationResult:
        """
        Brand discounts are always valid - they're automatic.
        
        Returns:
            ValidationResult with is_valid=True
        """
        return ValidationResult(is_valid=True)

    def get_name(self) -> str:
        """Get the display name of this discount."""
        return "Brand Discount"
