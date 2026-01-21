"""Discount configuration and rules."""

from decimal import Decimal
from typing import Dict

from src.strategies.brand import BrandDiscountStrategy
from src.strategies.category import CategoryDiscountStrategy
from src.strategies.voucher import VoucherDiscountStrategy, VoucherConfig
from src.strategies.bank import BankOfferStrategy, BankOfferConfig
from src.models import BrandTier, CustomerTier


# Brand discount configurations
# Maps brand name to discount percentage
BRAND_DISCOUNTS: Dict[str, Decimal] = {
    "PUMA": Decimal("40"),  # 40% off on PUMA
    "NIKE": Decimal("30"),  # 30% off on NIKE
    "ADIDAS": Decimal("35"),  # 35% off on ADIDAS
}

# Category discount configurations
# Maps category to discount percentage
CATEGORY_DISCOUNTS: Dict[str, Decimal] = {
    "T-shirts": Decimal("10"),  # Extra 10% off on T-shirts
    "Shoes": Decimal("15"),     # Extra 15% off on Shoes
    "Jeans": Decimal("20"),     # Extra 20% off on Jeans
}

# Voucher configurations
VOUCHERS: Dict[str, VoucherConfig] = {
    "SUPER69": VoucherConfig(
        code="SUPER69",
        discount_percentage=Decimal("69"),
        min_cart_value=Decimal("100"),
        excluded_brands=set(),
        allowed_categories=None,  # All categories allowed
        excluded_brand_tiers={BrandTier.PREMIUM},  # Not valid for premium brands
        min_customer_tier=None,
    ),
    "NEWUSER20": VoucherConfig(
        code="NEWUSER20",
        discount_percentage=Decimal("20"),
        min_cart_value=Decimal("500"),
        excluded_brands=set(),
        allowed_categories=None,
        excluded_brand_tiers=set(),
        min_customer_tier=CustomerTier.NEW,
    ),
    "TSHIRT15": VoucherConfig(
        code="TSHIRT15",
        discount_percentage=Decimal("15"),
        min_cart_value=None,
        excluded_brands=set(),
        allowed_categories={"T-shirts"},  # Only for T-shirts
        excluded_brand_tiers=set(),
        min_customer_tier=None,
    ),
    "GOLD50": VoucherConfig(
        code="GOLD50",
        discount_percentage=Decimal("50"),
        min_cart_value=Decimal("1000"),
        excluded_brands={"PUMA", "NIKE"},  # Not valid for PUMA and NIKE
        allowed_categories=None,
        excluded_brand_tiers=set(),
        min_customer_tier=CustomerTier.GOLD,  # Requires Gold membership
    ),
}

# Bank offer configurations
BANK_OFFERS: Dict[str, BankOfferConfig] = {
    "ICICI": BankOfferConfig(
        bank_name="ICICI",
        discount_percentage=Decimal("10"),
        card_type=None,  # Any card type
        min_transaction_value=Decimal("100"),
    ),
    "HDFC": BankOfferConfig(
        bank_name="HDFC",
        discount_percentage=Decimal("15"),
        card_type="CREDIT",  # Only credit cards
        min_transaction_value=Decimal("500"),
    ),
    "SBI": BankOfferConfig(
        bank_name="SBI",
        discount_percentage=Decimal("5"),
        card_type=None,
        min_transaction_value=None,
    ),
}


def get_brand_strategy() -> BrandDiscountStrategy:
    """Get configured brand discount strategy."""
    return BrandDiscountStrategy(BRAND_DISCOUNTS)


def get_category_strategy() -> CategoryDiscountStrategy:
    """Get configured category discount strategy."""
    return CategoryDiscountStrategy(CATEGORY_DISCOUNTS)


def get_voucher_strategy() -> VoucherDiscountStrategy:
    """Get configured voucher discount strategy."""
    return VoucherDiscountStrategy(VOUCHERS)


def get_bank_strategy() -> BankOfferStrategy:
    """Get configured bank offer strategy."""
    return BankOfferStrategy(BANK_OFFERS)
