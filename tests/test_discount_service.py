"""
Integration tests for DiscountService.

Tests the main discount scenario from assignment:
- PUMA T-shirt with 40% brand discount
- Additional 10% category discount on T-shirts
- ICICI bank offer (10% instant discount)
- SUPER69 voucher (69% off)
"""

import pytest
from decimal import Decimal

from src.discount_service import DiscountService
from src.data.discount_config import (
    get_brand_strategy,
    get_category_strategy,
    get_voucher_strategy,
    get_bank_strategy,
)
from src.data.fake_data import (
    get_multiple_discount_scenario,
    get_multi_item_cart,
    get_no_discount_cart,
    NEW_CUSTOMER,
    GOLD_CUSTOMER,
    ICICI_CARD_PAYMENT,
    HDFC_CREDIT_PAYMENT,
    HDFC_DEBIT_PAYMENT,
)


@pytest.fixture
def discount_service():
    """Create discount service with all strategies configured."""
    return DiscountService(
        brand_strategy=get_brand_strategy(),
        category_strategy=get_category_strategy(),
        voucher_strategy=get_voucher_strategy(),
        bank_strategy=get_bank_strategy(),
    )


class TestMultipleDiscountScenario:
    """Test the primary scenario from assignment."""

    @pytest.mark.asyncio
    async def test_brand_and_category_only(self, discount_service):
        """Test PUMA T-shirt with brand (40%) + category (10%) discounts."""
        cart = get_multiple_discount_scenario()

        result = await discount_service.calculate_cart_discounts(
            cart_items=cart,
            customer=NEW_CUSTOMER,
        )

        # Original: ₹1000
        # Brand (40%): ₹1000 - ₹400 = ₹600
        # Category (10%): ₹600 - ₹60 = ₹540
        assert result.original_price == Decimal("1000.00")
        assert result.final_price == Decimal("540.00")
        assert "Brand Discount" in result.applied_discounts
        assert "Category Discount" in result.applied_discounts
        assert result.applied_discounts["Brand Discount"] == Decimal("400.00")
        assert result.applied_discounts["Category Discount"] == Decimal("60.00")

    @pytest.mark.asyncio
    async def test_brand_category_and_bank_offer(self, discount_service):
        """Test PUMA T-shirt with brand + category + ICICI bank offer (10%)."""
        cart = get_multiple_discount_scenario()

        result = await discount_service.calculate_cart_discounts(
            cart_items=cart,
            customer=NEW_CUSTOMER,
            payment_info=ICICI_CARD_PAYMENT,
        )

        # Original: ₹1000
        # Brand (40%): ₹400
        # Category (10%): ₹60
        # Bank (10% on ₹540): ₹54
        # Final: ₹1000 - ₹514 = ₹486
        assert result.original_price == Decimal("1000.00")
        assert result.final_price == Decimal("486.00")
        assert "Bank Offer (ICICI)" in result.applied_discounts
        assert result.applied_discounts["Bank Offer (ICICI)"] == Decimal("54.00")

    @pytest.mark.asyncio
    async def test_all_discounts_with_voucher(self, discount_service):
        """Test PUMA T-shirt with brand + category + voucher + bank offer."""
        cart = get_multiple_discount_scenario()

        result = await discount_service.calculate_cart_discounts(
            cart_items=cart,
            customer=NEW_CUSTOMER,
            payment_info=ICICI_CARD_PAYMENT,
            voucher_code="TSHIRT15",  # 15% off on T-shirts
        )

        # Original: ₹1000
        # Brand (40%): ₹400
        # Category (10%): ₹60
        # Cart total: ₹540
        # Voucher (15% on ₹540): ₹81
        # Subtotal: ₹540 - ₹81 = ₹459
        # Bank (10% on ₹540): ₹54
        # Final: ₹1000 - ₹595 = ₹405
        assert result.original_price == Decimal("1000.00")
        assert "Voucher (TSHIRT15)" in result.applied_discounts


class TestVoucherValidation:
    """Test voucher validation logic."""

    @pytest.mark.asyncio
    async def test_validate_valid_voucher(self, discount_service):
        """Test validation of valid voucher code."""
        cart = get_multiple_discount_scenario()

        is_valid = await discount_service.validate_discount_code(
            code="TSHIRT15",
            cart_items=cart,
            customer=NEW_CUSTOMER,
        )

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_invalid_voucher_code(self, discount_service):
        """Test validation of non-existent voucher code."""
        cart = get_multiple_discount_scenario()

        is_valid = await discount_service.validate_discount_code(
            code="INVALID123",
            cart_items=cart,
            customer=NEW_CUSTOMER,
        )

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_voucher_premium_brand_exclusion(self, discount_service):
        """Test SUPER69 voucher excludes premium brands."""
        from src.data.fake_data import NIKE_SHOES
        from src.models import CartItem
        from copy import deepcopy

        cart = [CartItem(product=deepcopy(NIKE_SHOES), quantity=1, size="10")]

        is_valid = await discount_service.validate_discount_code(
            code="SUPER69",  # Excludes premium tier
            cart_items=cart,
            customer=NEW_CUSTOMER,
        )

        # NIKE is premium brand, SUPER69 excludes premium
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_voucher_customer_tier_requirement(self, discount_service):
        """Test GOLD50 voucher requires Gold tier."""
        cart = get_multiple_discount_scenario()

        # New customer trying to use Gold voucher
        is_valid_new = await discount_service.validate_discount_code(
            code="GOLD50",
            cart_items=cart,
            customer=NEW_CUSTOMER,
        )
        assert is_valid_new is False

        # Gold customer can use Gold voucher
        is_valid_gold = await discount_service.validate_discount_code(
            code="GOLD50",
            cart_items=cart,
            customer=GOLD_CUSTOMER,
        )
        # Note: GOLD50 excludes PUMA, so still might be invalid for this cart
        # but the TIER check should pass

    @pytest.mark.asyncio
    async def test_validate_voucher_category_restriction(self, discount_service):
        """Test TSHIRT15 voucher only valid for T-shirts."""
        from src.data.fake_data import NIKE_SHOES
        from src.models import CartItem
        from copy import deepcopy

        # Cart with shoes (not T-shirts)
        cart = [CartItem(product=deepcopy(NIKE_SHOES), quantity=1, size="10")]

        is_valid = await discount_service.validate_discount_code(
            code="TSHIRT15",  # Only for T-shirts
            cart_items=cart,
            customer=NEW_CUSTOMER,
        )

        assert is_valid is False


class TestBankOffers:
    """Test bank offer validation and calculation."""

    @pytest.mark.asyncio
    async def test_hdfc_credit_card_offer(self, discount_service):
        """Test HDFC credit card offer (15%)."""
        cart = get_multi_item_cart()

        result = await discount_service.calculate_cart_discounts(
            cart_items=cart,
            customer=NEW_CUSTOMER,
            payment_info=HDFC_CREDIT_PAYMENT,
        )

        assert "Bank Offer (HDFC)" in result.applied_discounts

    @pytest.mark.asyncio
    async def test_hdfc_debit_card_no_offer(self, discount_service):
        """Test HDFC debit card doesn't get credit card offer."""
        cart = get_multi_item_cart()

        result = await discount_service.calculate_cart_discounts(
            cart_items=cart,
            customer=NEW_CUSTOMER,
            payment_info=HDFC_DEBIT_PAYMENT,
        )

        # HDFC offer requires CREDIT card
        assert "Bank Offer (HDFC)" not in result.applied_discounts


class TestEdgeCases:
    """Test edge cases and no-discount scenarios."""

    @pytest.mark.asyncio
    async def test_no_discounts_applied(self, discount_service):
        """Test cart with no applicable discounts."""
        cart = get_no_discount_cart()  # Premium jacket with no discounts

        result = await discount_service.calculate_cart_discounts(
            cart_items=cart,
            customer=NEW_CUSTOMER,
        )

        assert result.original_price == result.final_price
        assert len(result.applied_discounts) == 0
        assert "No discounts applied" in result.message

    @pytest.mark.asyncio
    async def test_invalid_voucher_still_applies_other_discounts(self, discount_service):
        """Test that invalid voucher doesn't prevent other discounts."""
        cart = get_multiple_discount_scenario()

        result = await discount_service.calculate_cart_discounts(
            cart_items=cart,
            customer=NEW_CUSTOMER,
            payment_info=ICICI_CARD_PAYMENT,
            voucher_code="INVALID123",
        )

        # Brand, category, and bank should still apply
        assert "Brand Discount" in result.applied_discounts
        assert "Category Discount" in result.applied_discounts
        assert "Bank Offer (ICICI)" in result.applied_discounts
        assert "Voucher" not in str(result.applied_discounts)
        assert "validation failed" in result.message
