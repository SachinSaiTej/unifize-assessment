"""Bank offer discount strategy implementation."""

from decimal import Decimal
from typing import Dict, Optional
from dataclasses import dataclass

from src.strategies.base import DiscountStrategy, DiscountContext
from src.models import ValidationResult


@dataclass
class BankOfferConfig:
    """Configuration for a bank offer."""
    bank_name: str
    discount_percentage: Decimal
    card_type: Optional[str] = None  # None means any card type
    min_transaction_value: Optional[Decimal] = None


class BankOfferStrategy(DiscountStrategy):
    """
    Handles bank card offers (e.g., "10% instant discount on ICICI Bank cards").
    Bank offers are applied last, after all other discounts.
    """

    def __init__(self, bank_offers: Dict[str, BankOfferConfig]):
        """
        Initialize bank offer discount strategy.
        
        Args:
            bank_offers: Dictionary mapping bank name to BankOfferConfig
        """
        self.bank_offers = bank_offers

    async def calculate(self, context: DiscountContext) -> Decimal:
        """
        Calculate bank offer discount on cart total.
        
        Only applies if payment info is provided and matches an offer.
        
        Returns:
            Discount amount applied
        """
        if not context.payment_info or not context.payment_info.bank_name:
            return Decimal("0")

        bank_offer = self.bank_offers.get(context.payment_info.bank_name)
        if not bank_offer:
            return Decimal("0")

        # Validate card type if specified in offer
        if bank_offer.card_type and context.payment_info.card_type != bank_offer.card_type:
            return Decimal("0")

        # Calculate cart subtotal based on current prices
        cart_total = sum(item.get_subtotal() for item in context.cart_items)

        # Check minimum transaction value
        if bank_offer.min_transaction_value and cart_total < bank_offer.min_transaction_value:
            return Decimal("0")

        # Apply bank offer percentage
        discount = (cart_total * bank_offer.discount_percentage / Decimal("100"))
        return discount.quantize(Decimal("0.01"))

    async def validate(self, context: DiscountContext) -> ValidationResult:
        """
        Validate bank offer eligibility.
        
        Returns:
            ValidationResult with error messages if validation fails
        """
        result = ValidationResult(is_valid=True)

        # Can proceed without payment info (offer just won't apply)
        if not context.payment_info:
            return result

        if not context.payment_info.bank_name:
            return result

        bank_offer = self.bank_offers.get(context.payment_info.bank_name)
        if not bank_offer:
            result.add_error(f"No offers available for {context.payment_info.bank_name}")
            return result

        # Check card type requirement
        if bank_offer.card_type and context.payment_info.card_type != bank_offer.card_type:
            result.add_error(
                f"{context.payment_info.bank_name} offer requires {bank_offer.card_type} card "
                f"(provided: {context.payment_info.card_type})"
            )

        # Check minimum transaction value
        if bank_offer.min_transaction_value:
            cart_total = sum(item.get_subtotal() for item in context.cart_items)
            if cart_total < bank_offer.min_transaction_value:
                result.add_error(
                    f"Minimum transaction value of ₹{bank_offer.min_transaction_value} not met "
                    f"(current: ₹{cart_total})"
                )

        return result

    def get_name(self) -> str:
        """Get the display name of this discount."""
        return "Bank Offer"
