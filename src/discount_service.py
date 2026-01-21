"""Core discount service orchestrator."""

from typing import List, Optional, Dict
from decimal import Decimal
from copy import deepcopy

from src.models import (
    CartItem,
    CustomerProfile,
    PaymentInfo,
    DiscountedPrice,
    ValidationResult,
)
from src.strategies.base import DiscountContext
from src.strategies.brand import BrandDiscountStrategy
from src.strategies.category import CategoryDiscountStrategy
from src.strategies.voucher import VoucherDiscountStrategy
from src.strategies.bank import BankOfferStrategy


class DiscountService:
    """
    Main discount service that orchestrates discount calculations.
    
    Applies discounts in the correct order:
    1. Brand discounts (updates product current_price)
    2. Category discounts (updates product current_price)
    3. Voucher codes (applied on cart total)
    4. Bank offers (applied on final amount)
    """

    def __init__(
        self,
        brand_strategy: BrandDiscountStrategy,
        category_strategy: CategoryDiscountStrategy,
        voucher_strategy: VoucherDiscountStrategy,
        bank_strategy: BankOfferStrategy,
        allow_discount_stacking: bool = True,
    ):
        """
        Initialize discount service with all strategies.
        
        Args:
            brand_strategy: Strategy for brand discounts
            category_strategy: Strategy for category discounts
            voucher_strategy: Strategy for voucher codes
            bank_strategy: Strategy for bank offers
            allow_discount_stacking: If True, stack all applicable discounts.
                                    If False, apply only the best single discount.
        """
        self.brand_strategy = brand_strategy
        self.category_strategy = category_strategy
        self.voucher_strategy = voucher_strategy
        self.bank_strategy = bank_strategy
        self.allow_discount_stacking = allow_discount_stacking

    async def calculate_cart_discounts(
        self,
        cart_items: List[CartItem],
        customer: CustomerProfile,
        payment_info: Optional[PaymentInfo] = None,
        voucher_code: Optional[str] = None,
    ) -> DiscountedPrice:
        """
        Calculate final price after applying all applicable discounts.
        
        Discount application depends on allow_discount_stacking:
        - If True: Apply discounts sequentially (Brand → Category → Voucher → Bank)
        - If False: Calculate all discounts independently and apply only the best one
        
        Args:
            cart_items: List of items in the cart
            customer: Customer profile for eligibility checks
            payment_info: Optional payment information for bank offers
            voucher_code: Optional voucher code to apply
            
        Returns:
            DiscountedPrice with original price, final price, and applied discounts
        """
        if self.allow_discount_stacking:
            return await self._calculate_stacked_discounts(
                cart_items, customer, payment_info, voucher_code
            )
        else:
            return await self._calculate_best_discount(
                cart_items, customer, payment_info, voucher_code
            )

    async def _calculate_stacked_discounts(
        self,
        cart_items: List[CartItem],
        customer: CustomerProfile,
        payment_info: Optional[PaymentInfo],
        voucher_code: Optional[str],
    ) -> DiscountedPrice:
        """
        Original stacking logic: Apply all discounts sequentially.
        
        Discount application order:
        1. Brand discounts (automatic)
        2. Category discounts (automatic)
        3. Voucher codes (if provided and valid)
        4. Bank offers (if payment info provided and valid)
        """
        # Make a deep copy to avoid modifying original cart items
        cart_items_copy = deepcopy(cart_items)
        
        # Calculate original cart total (based on base prices)
        original_total = sum(
            item.product.base_price * item.quantity
            for item in cart_items_copy
        )

        # Track applied discounts
        applied_discounts: Dict[str, Decimal] = {}
        messages: List[str] = []

        # Create context for discount calculations
        context = DiscountContext(
            cart_items=cart_items_copy,
            customer=customer,
            payment_info=payment_info,
            voucher_code=voucher_code,
        )

        # 1. Apply brand discounts (automatic, updates current_price)
        brand_discount = await self.brand_strategy.calculate(context)
        if brand_discount > Decimal("0"):
            applied_discounts["Brand Discount"] = brand_discount
            messages.append(f"Brand discount: ₹{brand_discount}")

        # 2. Apply category discounts (automatic, updates current_price)
        category_discount = await self.category_strategy.calculate(context)
        if category_discount > Decimal("0"):
            applied_discounts["Category Discount"] = category_discount
            messages.append(f"Category discount: ₹{category_discount}")

        # 3. Apply voucher code (if provided and valid)
        if voucher_code:
            voucher_validation = await self.voucher_strategy.validate(context)
            if voucher_validation.is_valid:
                voucher_discount = await self.voucher_strategy.calculate(context)
                if voucher_discount > Decimal("0"):
                    applied_discounts[f"Voucher ({voucher_code})"] = voucher_discount
                    messages.append(f"Voucher '{voucher_code}' applied: ₹{voucher_discount}")
            else:
                messages.append(f"Voucher validation failed: {voucher_validation.error_message}")

        # Calculate current cart total (after brand/category/voucher)
        current_cart_total = sum(
            item.product.current_price * item.quantity
            for item in cart_items_copy
        )

        # Subtract voucher if applied (vouchers reduce the cart total)
        voucher_discount = applied_discounts.get(f"Voucher ({voucher_code})", Decimal("0"))
        current_cart_total -= voucher_discount

        # 4. Apply bank offer (if payment info provided and valid)
        if payment_info:
            bank_validation = await self.bank_strategy.validate(context)
            if bank_validation.is_valid:
                bank_discount = await self.bank_strategy.calculate(context)
                if bank_discount > Decimal("0"):
                    applied_discounts[f"Bank Offer ({payment_info.bank_name})"] = bank_discount
                    messages.append(f"Bank offer applied: ₹{bank_discount}")
            else:
                if bank_validation.errors:
                    messages.append(f"Bank offer validation failed: {bank_validation.error_message}")

        # Calculate final price
        total_discount = sum(applied_discounts.values())
        final_price = (original_total - total_discount).quantize(Decimal("0.01"))

        # Ensure final price doesn't go negative
        if final_price < Decimal("0"):
            final_price = Decimal("0")

        # Create result message
        if not messages:
            result_message = "No discounts applied"
        else:
            result_message = " | ".join(messages)

        return DiscountedPrice(
            original_price=original_total.quantize(Decimal("0.01")),
            final_price=final_price,
            applied_discounts=applied_discounts,
            message=result_message,
        )

    async def _calculate_best_discount(
        self,
        cart_items: List[CartItem],
        customer: CustomerProfile,
        payment_info: Optional[PaymentInfo],
        voucher_code: Optional[str],
    ) -> DiscountedPrice:
        """
        Best discount logic: Calculate all discounts independently and apply the best one.
        
        Each discount is calculated on the original price independently,
        then the highest discount is selected and applied.
        """
        # Calculate original cart total (based on base prices)
        original_total = sum(
            item.product.base_price * item.quantity
            for item in cart_items
        )

        # Dictionary to store all calculated discounts
        discount_candidates: Dict[str, Decimal] = {}

        # 1. Calculate brand discount
        cart_items_brand = deepcopy(cart_items)
        context_brand = DiscountContext(
            cart_items=cart_items_brand,
            customer=customer,
        )
        brand_discount = await self.brand_strategy.calculate(context_brand)
        if brand_discount > Decimal("0"):
            discount_candidates["Brand Discount"] = brand_discount

        # 2. Calculate category discount (on original prices)
        cart_items_category = deepcopy(cart_items)
        context_category = DiscountContext(
            cart_items=cart_items_category,
            customer=customer,
        )
        category_discount = await self.category_strategy.calculate(context_category)
        if category_discount > Decimal("0"):
            discount_candidates["Category Discount"] = category_discount

        # 3. Calculate voucher discount (if provided and valid)
        if voucher_code:
            cart_items_voucher = deepcopy(cart_items)
            context_voucher = DiscountContext(
                cart_items=cart_items_voucher,
                customer=customer,
                voucher_code=voucher_code,
            )
            voucher_validation = await self.voucher_strategy.validate(context_voucher)
            if voucher_validation.is_valid:
                voucher_discount = await self.voucher_strategy.calculate(context_voucher)
                if voucher_discount > Decimal("0"):
                    discount_candidates[f"Voucher ({voucher_code})"] = voucher_discount

        # 4. Calculate bank offer (if payment info provided and valid)
        if payment_info:
            cart_items_bank = deepcopy(cart_items)
            context_bank = DiscountContext(
                cart_items=cart_items_bank,
                customer=customer,
                payment_info=payment_info,
            )
            bank_validation = await self.bank_strategy.validate(context_bank)
            if bank_validation.is_valid:
                bank_discount = await self.bank_strategy.calculate(context_bank)
                if bank_discount > Decimal("0"):
                    discount_candidates[f"Bank Offer ({payment_info.bank_name})"] = bank_discount

        # Select the best discount (highest amount)
        applied_discounts: Dict[str, Decimal] = {}
        message = ""

        if discount_candidates:
            best_discount_name = max(discount_candidates.items(), key=lambda x: x[1])[0]
            best_discount_amount = discount_candidates[best_discount_name]
            applied_discounts[best_discount_name] = best_discount_amount
            message = f"Best discount applied: {best_discount_name} - ₹{best_discount_amount}"
        else:
            message = "No discounts applied"

        # Calculate final price
        total_discount = sum(applied_discounts.values())
        final_price = (original_total - total_discount).quantize(Decimal("0.01"))

        # Ensure final price doesn't go negative
        if final_price < Decimal("0"):
            final_price = Decimal("0")

        return DiscountedPrice(
            original_price=original_total.quantize(Decimal("0.01")),
            final_price=final_price,
            applied_discounts=applied_discounts,
            message=message,
        )

    async def validate_discount_code(
        self,
        code: str,
        cart_items: List[CartItem],
        customer: CustomerProfile,
    ) -> bool:
        """
        Validate if a discount code can be applied.
        
        Handles voucher-specific validation cases:
        - Brand exclusions
        - Category restrictions
        - Customer tier requirements
        - Minimum cart value
        - Brand tier exclusions
        
        Args:
            code: The voucher/discount code to validate
            cart_items: Current cart items
            customer: Customer profile
            
        Returns:
            True if the discount code is valid and can be applied, False otherwise
        """
        context = DiscountContext(
            cart_items=cart_items,
            customer=customer,
            voucher_code=code,
        )

        validation_result = await self.voucher_strategy.validate(context)
        return validation_result.is_valid
