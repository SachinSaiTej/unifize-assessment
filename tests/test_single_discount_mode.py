"""Tests for single discount mode feature."""

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
    NEW_CUSTOMER,
    ICICI_CARD_PAYMENT,
)


@pytest.fixture
def stacking_service():
    """Create discount service with stacking enabled."""
    return DiscountService(
        brand_strategy=get_brand_strategy(),
        category_strategy=get_category_strategy(),
        voucher_strategy=get_voucher_strategy(),
        bank_strategy=get_bank_strategy(),
        allow_discount_stacking=True,
    )


@pytest.fixture
def best_discount_service():
    """Create discount service with stacking disabled (best discount only)."""
    return DiscountService(
        brand_strategy=get_brand_strategy(),
        category_strategy=get_category_strategy(),
        voucher_strategy=get_voucher_strategy(),
        bank_strategy=get_bank_strategy(),
        allow_discount_stacking=False,
    )


class TestSingleDiscountMode:
    """Test single discount mode (best discount only)."""

    @pytest.mark.asyncio
    async def test_best_discount_selects_brand_discount(self, best_discount_service):
        """Test that brand discount (40% = ₹400) is selected as best for PUMA T-shirt."""
        cart = get_multiple_discount_scenario()

        result = await best_discount_service.calculate_cart_discounts(
            cart_items=cart,
            customer=NEW_CUSTOMER,
        )

        # Brand discount (40% of ₹1000 = ₹400) should be chosen
        # over category discount (10% of ₹1000 = ₹100)
        assert result.original_price == Decimal("1000.00")
        assert result.final_price == Decimal("600.00")
        assert len(result.applied_discounts) == 1
        assert "Brand Discount" in result.applied_discounts
        assert result.applied_discounts["Brand Discount"] == Decimal("400.00")
        assert "Best discount applied" in result.message

    @pytest.mark.asyncio
    async def test_best_discount_with_bank_offer(self, best_discount_service):
        """Test best discount selection with bank offer available."""
        cart = get_multiple_discount_scenario()

        result = await best_discount_service.calculate_cart_discounts(
            cart_items=cart,
            customer=NEW_CUSTOMER,
            payment_info=ICICI_CARD_PAYMENT,
        )

        # Brand discount (₹400) is still best
        # Bank offer would only be 10% of ₹1000 = ₹100
        assert result.final_price == Decimal("600.00")
        assert len(result.applied_discounts) == 1
        assert "Brand Discount" in result.applied_discounts

    @pytest.mark.asyncio
    async def test_best_discount_with_voucher(self, best_discount_service):
        """Test best discount selection with voucher."""
        cart = get_multiple_discount_scenario()

        result = await best_discount_service.calculate_cart_discounts(
            cart_items=cart,
            customer=NEW_CUSTOMER,
            voucher_code="SUPER69",  # 69% off
        )

        # SUPER69 (69% of ₹1000 = ₹690) should be selected as best
        assert result.final_price == Decimal("310.00")
        assert len(result.applied_discounts) == 1
        assert "Voucher (SUPER69)" in result.applied_discounts
        assert result.applied_discounts["Voucher (SUPER69)"] == Decimal("690.00")

    @pytest.mark.asyncio
    async def test_comparison_stacking_vs_best_discount(self, stacking_service, best_discount_service):
        """Compare results between stacking and best discount modes."""
        cart = get_multiple_discount_scenario()

        # Stacking mode
        result_stacked = await stacking_service.calculate_cart_discounts(
            cart_items=cart,
            customer=NEW_CUSTOMER,
            payment_info=ICICI_CARD_PAYMENT,
        )

        # Best discount mode
        result_best = await best_discount_service.calculate_cart_discounts(
            cart_items=cart,
            customer=NEW_CUSTOMER,
            payment_info=ICICI_CARD_PAYMENT,
        )

        # Stacking should give better final price (₹486 vs ₹600)
        assert result_stacked.final_price < result_best.final_price
        
        # Stacking applies multiple discounts
        assert len(result_stacked.applied_discounts) > 1
        
        # Best discount applies only one
        assert len(result_best.applied_discounts) == 1

    @pytest.mark.asyncio
    async def test_best_discount_no_discounts_available(self, best_discount_service):
        """Test best discount mode when no discounts are available."""
        from src.data.fake_data import get_no_discount_cart

        cart = get_no_discount_cart()

        result = await best_discount_service.calculate_cart_discounts(
            cart_items=cart,
            customer=NEW_CUSTOMER,
        )

        assert result.original_price == result.final_price
        assert len(result.applied_discounts) == 0
        assert "No discounts applied" in result.message
