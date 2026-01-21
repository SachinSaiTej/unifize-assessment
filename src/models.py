"""Core data models for the discount service."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
from decimal import Decimal
from enum import Enum


class BrandTier(Enum):
    """Brand tier classification for discount eligibility."""
    PREMIUM = "premium"
    REGULAR = "regular"
    BUDGET = "budget"


class CustomerTier(Enum):
    """Customer tier for loyalty-based discount eligibility."""
    NEW = "new"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


@dataclass
class Product:
    """Product information with pricing details."""
    id: str
    brand: str
    brand_tier: BrandTier
    category: str
    base_price: Decimal
    current_price: Decimal  # After brand/category discount

    def __post_init__(self):
        """Ensure prices are Decimal type."""
        if not isinstance(self.base_price, Decimal):
            self.base_price = Decimal(str(self.base_price))
        if not isinstance(self.current_price, Decimal):
            self.current_price = Decimal(str(self.current_price))


@dataclass
class CartItem:
    """Individual item in shopping cart."""
    product: Product
    quantity: int
    size: str

    def get_subtotal(self) -> Decimal:
        """Calculate subtotal for this cart item."""
        return self.product.current_price * self.quantity


@dataclass
class PaymentInfo:
    """Payment method details for bank offer calculations."""
    method: str  # CARD, UPI, etc
    bank_name: Optional[str] = None
    card_type: Optional[str] = None  # CREDIT, DEBIT


@dataclass
class CustomerProfile:
    """Customer information for discount eligibility."""
    id: str
    tier: CustomerTier
    total_purchases: Decimal = Decimal("0")

    def __post_init__(self):
        """Ensure total_purchases is Decimal type."""
        if not isinstance(self.total_purchases, Decimal):
            self.total_purchases = Decimal(str(self.total_purchases))


@dataclass
class DiscountedPrice:
    """Final pricing details with applied discounts."""
    original_price: Decimal
    final_price: Decimal
    applied_discounts: Dict[str, Decimal]  # discount_name -> amount
    message: str

    def __post_init__(self):
        """Ensure prices are Decimal type."""
        if not isinstance(self.original_price, Decimal):
            self.original_price = Decimal(str(self.original_price))
        if not isinstance(self.final_price, Decimal):
            self.final_price = Decimal(str(self.final_price))


@dataclass
class ValidationResult:
    """Result of discount validation with detailed error messages."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        """Add a validation error."""
        self.is_valid = False
        self.errors.append(error)

    @property
    def error_message(self) -> str:
        """Get formatted error message."""
        if not self.errors:
            return ""
        return "; ".join(self.errors)
