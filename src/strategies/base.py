"""Base strategy interface for discount calculations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from decimal import Decimal

from src.models import CartItem, CustomerProfile, PaymentInfo, ValidationResult


@dataclass
class DiscountContext:
    """Context object containing all information needed for discount calculation."""
    cart_items: List[CartItem]
    customer: CustomerProfile
    payment_info: Optional[PaymentInfo] = None
    voucher_code: Optional[str] = None


class DiscountStrategy(ABC):
    """Abstract base class for all discount strategies."""

    @abstractmethod
    async def calculate(self, context: DiscountContext) -> Decimal:
        """
        Calculate discount amount for the given context.
        
        Args:
            context: DiscountContext containing cart, customer, and payment info
            
        Returns:
            Decimal: The discount amount (positive value)
        """
        pass

    @abstractmethod
    async def validate(self, context: DiscountContext) -> ValidationResult:
        """
        Validate if this discount can be applied.
        
        Args:
            context: DiscountContext containing cart, customer, and payment info
            
        Returns:
            ValidationResult: Contains is_valid flag and list of error messages
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the display name of this discount strategy."""
        pass
