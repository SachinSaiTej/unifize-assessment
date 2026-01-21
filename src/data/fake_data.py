"""Fake data for testing discount scenarios."""

from decimal import Decimal
from typing import List

from src.models import (
    Product,
    CartItem,
    CustomerProfile,
    PaymentInfo,
    BrandTier,
    CustomerTier,
)


# ============================================================================
# PRODUCTS
# ============================================================================

# PUMA T-shirt - 40% brand discount + 10% category discount eligible
PUMA_TSHIRT = Product(
    id="P001",
    brand="PUMA",
    brand_tier=BrandTier.REGULAR,
    category="T-shirts",
    base_price=Decimal("1000"),
    current_price=Decimal("1000"),  # Will be updated by service
)

# NIKE Shoes - 30% brand discount + 15% category discount eligible
NIKE_SHOES = Product(
    id="P002",
    brand="NIKE",
    brand_tier=BrandTier.PREMIUM,
    category="Shoes",
    base_price=Decimal("5000"),
    current_price=Decimal("5000"),
)

# ADIDAS Jeans - 35% brand discount + 20% category discount eligible
ADIDAS_JEANS = Product(
    id="P003",
    brand="ADIDAS",
    brand_tier=BrandTier.REGULAR,
    category="Jeans",
    base_price=Decimal("2500"),
    current_price=Decimal("2500"),
)

# Budget brand T-shirt - No brand discount, but 10% category discount
BUDGET_TSHIRT = Product(
    id="P004",
    brand="LOCAL_BRAND",
    brand_tier=BrandTier.BUDGET,
    category="T-shirts",
    base_price=Decimal("500"),
    current_price=Decimal("500"),
)

# Premium brand jacket - No discounts
PREMIUM_JACKET = Product(
    id="P005",
    brand="GUCCI",
    brand_tier=BrandTier.PREMIUM,
    category="Jackets",
    base_price=Decimal("15000"),
    current_price=Decimal("15000"),
)


# ============================================================================
# CUSTOMER PROFILES
# ============================================================================

NEW_CUSTOMER = CustomerProfile(
    id="C001",
    tier=CustomerTier.NEW,
    total_purchases=Decimal("0"),
)

SILVER_CUSTOMER = CustomerProfile(
    id="C002",
    tier=CustomerTier.SILVER,
    total_purchases=Decimal("5000"),
)

GOLD_CUSTOMER = CustomerProfile(
    id="C003",
    tier=CustomerTier.GOLD,
    total_purchases=Decimal("25000"),
)

PLATINUM_CUSTOMER = CustomerProfile(
    id="C004",
    tier=CustomerTier.PLATINUM,
    total_purchases=Decimal("100000"),
)


# ============================================================================
# PAYMENT METHODS
# ============================================================================

ICICI_CARD_PAYMENT = PaymentInfo(
    method="CARD",
    bank_name="ICICI",
    card_type="DEBIT",
)

HDFC_CREDIT_PAYMENT = PaymentInfo(
    method="CARD",
    bank_name="HDFC",
    card_type="CREDIT",
)

HDFC_DEBIT_PAYMENT = PaymentInfo(
    method="CARD",
    bank_name="HDFC",
    card_type="DEBIT",
)

SBI_CARD_PAYMENT = PaymentInfo(
    method="CARD",
    bank_name="SBI",
    card_type="CREDIT",
)

UPI_PAYMENT = PaymentInfo(
    method="UPI",
    bank_name=None,
    card_type=None,
)


# ============================================================================
# TEST SCENARIOS
# ============================================================================

def get_multiple_discount_scenario() -> List[CartItem]:
    """
    Primary test scenario from assignment:
    - PUMA T-shirt with "Min 40% off" (brand)
    - Additional 10% off on T-shirts category
    - ICICI bank offer of 10% instant discount
    - Optional SUPER69 voucher for 69% off
    
    Expected calculation (without voucher):
    Base: ₹1000
    After brand (40%): ₹1000 - ₹400 = ₹600
    After category (10%): ₹600 - ₹60 = ₹540
    After bank (10%): ₹540 - ₹54 = ₹486
    
    With SUPER69 voucher (69% off):
    Base: ₹1000
    After brand (40%): ₹600
    After category (10%): ₹540
    After voucher (69%): ₹540 - ₹372.60 = ₹167.40
    After bank (10%): ₹167.40 - ₹16.74 = ₹150.66
    """
    from copy import deepcopy
    return [
        CartItem(
            product=deepcopy(PUMA_TSHIRT),
            quantity=1,
            size="L",
        )
    ]


def get_multi_item_cart() -> List[CartItem]:
    """
    Cart with multiple items for complex discount scenarios.
    """
    from copy import deepcopy
    return [
        CartItem(product=deepcopy(PUMA_TSHIRT), quantity=2, size="L"),
        CartItem(product=deepcopy(NIKE_SHOES), quantity=1, size="10"),
        CartItem(product=deepcopy(BUDGET_TSHIRT), quantity=1, size="M"),
    ]


def get_no_discount_cart() -> List[CartItem]:
    """
    Cart with items that don't qualify for automatic discounts.
    """
    from copy import deepcopy
    return [
        CartItem(product=deepcopy(PREMIUM_JACKET), quantity=1, size="M"),
    ]
