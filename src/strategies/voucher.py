"""Voucher discount strategy implementation."""

from decimal import Decimal
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from src.strategies.base import DiscountStrategy, DiscountContext
from src.models import ValidationResult, BrandTier, CustomerTier


@dataclass
class VoucherConfig:
    """Configuration for a voucher code."""
    code: str
    discount_percentage: Decimal
    min_cart_value: Optional[Decimal] = None
    excluded_brands: Set[str] = None
    allowed_categories: Optional[Set[str]] = None
    excluded_brand_tiers: Set[BrandTier] = None
    min_customer_tier: Optional[CustomerTier] = None

    def __post_init__(self):
        """Initialize sets if None."""
        if self.excluded_brands is None:
            self.excluded_brands = set()
        if self.excluded_brand_tiers is None:
            self.excluded_brand_tiers = set()


class VoucherDiscountStrategy(DiscountStrategy):
    """
    Handles voucher/coupon code discounts (e.g., "SUPER69" for 69% off).
    Vouchers are applied after brand/category discounts, on the cart total.
    """

    def __init__(self, vouchers: Dict[str, VoucherConfig]):
        """
        Initialize voucher discount strategy.
        
        Args:
            vouchers: Dictionary mapping voucher code to VoucherConfig
        """
        self.vouchers = vouchers

    async def calculate(self, context: DiscountContext) -> Decimal:
        """
        Calculate voucher discount on cart total.
        
        Only calculates if a voucher code is provided and valid.
        
        Returns:
            Total discount amount applied
        """
        if not context.voucher_code:
            return Decimal("0")

        voucher = self.vouchers.get(context.voucher_code)
        if not voucher:
            return Decimal("0")

        # Calculate cart subtotal based on current prices
        cart_total = sum(item.get_subtotal() for item in context.cart_items)

        # Apply voucher percentage
        discount = (cart_total * voucher.discount_percentage / Decimal("100"))
        return discount.quantize(Decimal("0.01"))

    async def validate(self, context: DiscountContext) -> ValidationResult:
        """
        Validate voucher code with comprehensive checks.
        
        Collects all validation errors:
        - Voucher code exists
        - Minimum cart value met
        - No excluded brands in cart
        - Category restrictions met
        - Brand tier restrictions met
        - Customer tier requirements met
        
        Returns:
            ValidationResult with all error messages
        """
        result = ValidationResult(is_valid=True)

        if not context.voucher_code:
            result.add_error("No voucher code provided")
            return result

        voucher = self.vouchers.get(context.voucher_code)
        if not voucher:
            result.add_error(f"Voucher code '{context.voucher_code}' is invalid")
            return result

        # Check minimum cart value
        if voucher.min_cart_value:
            cart_total = sum(item.get_subtotal() for item in context.cart_items)
            if cart_total < voucher.min_cart_value:
                result.add_error(
                    f"Minimum cart value of ₹{voucher.min_cart_value} not met "
                    f"(current: ₹{cart_total})"
                )

        # Check excluded brands
        if voucher.excluded_brands:
            cart_brands = {item.product.brand for item in context.cart_items}
            excluded_in_cart = cart_brands & voucher.excluded_brands
            if excluded_in_cart:
                result.add_error(
                    f"Voucher not valid for brands: {', '.join(excluded_in_cart)}"
                )

        # Check allowed categories
        if voucher.allowed_categories:
            cart_categories = {item.product.category for item in context.cart_items}
            invalid_categories = cart_categories - voucher.allowed_categories
            if invalid_categories:
                result.add_error(
                    f"Voucher only valid for categories: {', '.join(voucher.allowed_categories)}"
                )

        # Check excluded brand tiers
        if voucher.excluded_brand_tiers:
            cart_tiers = {item.product.brand_tier for item in context.cart_items}
            excluded_tiers_in_cart = cart_tiers & voucher.excluded_brand_tiers
            if excluded_tiers_in_cart:
                tier_names = [tier.value for tier in excluded_tiers_in_cart]
                result.add_error(
                    f"Voucher not valid for {', '.join(tier_names)} brand products"
                )

        # Check customer tier requirement
        if voucher.min_customer_tier:
            tier_order = [CustomerTier.NEW, CustomerTier.SILVER, CustomerTier.GOLD, CustomerTier.PLATINUM]
            required_index = tier_order.index(voucher.min_customer_tier)
            customer_index = tier_order.index(context.customer.tier)
            
            if customer_index < required_index:
                result.add_error(
                    f"Voucher requires {voucher.min_customer_tier.value} membership "
                    f"(current: {context.customer.tier.value})"
                )

        return result

    def get_name(self) -> str:
        """Get the display name of this discount."""
        return "Voucher Code"
