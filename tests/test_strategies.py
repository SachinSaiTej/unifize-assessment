"""Unit tests for individual discount strategies."""

import pytest
from decimal import Decimal
from copy import deepcopy

from src.strategies.brand import BrandDiscountStrategy
from src.strategies.category import CategoryDiscountStrategy
from src.strategies.voucher import VoucherDiscountStrategy, VoucherConfig
from src.strategies.bank import BankOfferStrategy, BankOfferConfig
from src.strategies.base import DiscountContext
from src.models import (
    Product,
    CartItem,
    BrandTier,
    CustomerTier,
    CustomerProfile,
    PaymentInfo,
)


@pytest.fixture
def sample_product():
    """Create a sample product."""
    return Product(
        id="TEST001",
        brand="PUMA",
        brand_tier=BrandTier.REGULAR,
        category="T-shirts",
        base_price=Decimal("1000"),
        current_price=Decimal("1000"),
    )


@pytest.fixture
def sample_customer():
    """Create a sample customer."""
    return CustomerProfile(
        id="CUST001",
        tier=CustomerTier.SILVER,
        total_purchases=Decimal("5000"),
    )


class TestBrandDiscountStrategy:
    """Test brand discount strategy."""

    @pytest.mark.asyncio
    async def test_calculate_brand_discount(self, sample_product, sample_customer):
        """Test brand discount calculation."""
        strategy = BrandDiscountStrategy({"PUMA": Decimal("40")})
        
        cart_item = CartItem(product=deepcopy(sample_product), quantity=1, size="L")
        context = DiscountContext(
            cart_items=[cart_item],
            customer=sample_customer,
        )

        discount = await strategy.calculate(context)

        assert discount == Decimal("400.00")
        # Verify current_price was updated
        assert cart_item.product.current_price == Decimal("600")

    @pytest.mark.asyncio
    async def test_no_brand_discount_for_unlisted_brand(self, sample_customer):
        """Test that unlisted brands get no discount."""
        product = Product(
            id="TEST002",
            brand="UNKNOWN",
            brand_tier=BrandTier.BUDGET,
            category="T-shirts",
            base_price=Decimal("500"),
            current_price=Decimal("500"),
        )
        
        strategy = BrandDiscountStrategy({"PUMA": Decimal("40")})
        cart_item = CartItem(product=product, quantity=1, size="M")
        context = DiscountContext(
            cart_items=[cart_item],
            customer=sample_customer,
        )

        discount = await strategy.calculate(context)

        assert discount == Decimal("0")
        assert product.current_price == Decimal("500")

    @pytest.mark.asyncio
    async def test_validate_always_returns_true(self, sample_product, sample_customer):
        """Test that brand discounts are always valid."""
        strategy = BrandDiscountStrategy({"PUMA": Decimal("40")})
        cart_item = CartItem(product=sample_product, quantity=1, size="L")
        context = DiscountContext(
            cart_items=[cart_item],
            customer=sample_customer,
        )

        result = await strategy.validate(context)

        assert result.is_valid is True
        assert len(result.errors) == 0


class TestCategoryDiscountStrategy:
    """Test category discount strategy."""

    @pytest.mark.asyncio
    async def test_calculate_category_discount(self, sample_product, sample_customer):
        """Test category discount calculation."""
        strategy = CategoryDiscountStrategy({"T-shirts": Decimal("10")})
        
        # Set current_price lower (as if brand discount already applied)
        product = deepcopy(sample_product)
        product.current_price = Decimal("600")
        
        cart_item = CartItem(product=product, quantity=1, size="L")
        context = DiscountContext(
            cart_items=[cart_item],
            customer=sample_customer,
        )

        discount = await strategy.calculate(context)

        # 10% of ₹600 = ₹60
        assert discount == Decimal("60.00")
        assert cart_item.product.current_price == Decimal("540")

    @pytest.mark.asyncio
    async def test_category_discount_with_quantity(self, sample_product, sample_customer):
        """Test category discount with multiple quantities."""
        strategy = CategoryDiscountStrategy({"T-shirts": Decimal("10")})
        
        product = deepcopy(sample_product)
        product.current_price = Decimal("600")
        
        cart_item = CartItem(product=product, quantity=3, size="L")
        context = DiscountContext(
            cart_items=[cart_item],
            customer=sample_customer,
        )

        discount = await strategy.calculate(context)

        # 10% of ₹600 = ₹60 per item × 3 = ₹180
        assert discount == Decimal("180.00")


class TestVoucherDiscountStrategy:
    """Test voucher discount strategy."""

    @pytest.mark.asyncio
    async def test_calculate_voucher_discount(self, sample_product, sample_customer):
        """Test voucher discount calculation."""
        voucher = VoucherConfig(
            code="TEST20",
            discount_percentage=Decimal("20"),
        )
        strategy = VoucherDiscountStrategy({"TEST20": voucher})
        
        product = deepcopy(sample_product)
        product.current_price = Decimal("500")
        
        cart_item = CartItem(product=product, quantity=1, size="L")
        context = DiscountContext(
            cart_items=[cart_item],
            customer=sample_customer,
            voucher_code="TEST20",
        )

        discount = await strategy.calculate(context)

        # 20% of ₹500 = ₹100
        assert discount == Decimal("100.00")

    @pytest.mark.asyncio
    async def test_validate_min_cart_value(self, sample_product, sample_customer):
        """Test voucher validation for minimum cart value."""
        voucher = VoucherConfig(
            code="MIN500",
            discount_percentage=Decimal("10"),
            min_cart_value=Decimal("500"),
        )
        strategy = VoucherDiscountStrategy({"MIN500": voucher})
        
        # Cart with value less than ₹500
        product = deepcopy(sample_product)
        product.current_price = Decimal("300")
        cart_item = CartItem(product=product, quantity=1, size="L")
        context = DiscountContext(
            cart_items=[cart_item],
            customer=sample_customer,
            voucher_code="MIN500",
        )

        result = await strategy.validate(context)

        assert result.is_valid is False
        assert "Minimum cart value" in result.error_message

    @pytest.mark.asyncio
    async def test_validate_excluded_brands(self, sample_customer):
        """Test voucher validation for excluded brands."""
        voucher = VoucherConfig(
            code="NOPUMA",
            discount_percentage=Decimal("30"),
            excluded_brands={"PUMA", "NIKE"},
        )
        strategy = VoucherDiscountStrategy({"NOPUMA": voucher})
        
        product = Product(
            id="TEST001",
            brand="PUMA",
            brand_tier=BrandTier.REGULAR,
            category="T-shirts",
            base_price=Decimal("1000"),
            current_price=Decimal("600"),
        )
        cart_item = CartItem(product=product, quantity=1, size="L")
        context = DiscountContext(
            cart_items=[cart_item],
            customer=sample_customer,
            voucher_code="NOPUMA",
        )

        result = await strategy.validate(context)

        assert result.is_valid is False
        assert "PUMA" in result.error_message


class TestBankOfferStrategy:
    """Test bank offer strategy."""

    @pytest.mark.asyncio
    async def test_calculate_bank_offer(self, sample_product, sample_customer):
        """Test bank offer calculation."""
        offer = BankOfferConfig(
            bank_name="ICICI",
            discount_percentage=Decimal("10"),
        )
        strategy = BankOfferStrategy({"ICICI": offer})
        
        product = deepcopy(sample_product)
        product.current_price = Decimal("500")
        
        cart_item = CartItem(product=product, quantity=1, size="L")
        payment = PaymentInfo(method="CARD", bank_name="ICICI", card_type="DEBIT")
        context = DiscountContext(
            cart_items=[cart_item],
            customer=sample_customer,
            payment_info=payment,
        )

        discount = await strategy.calculate(context)

        # 10% of ₹500 = ₹50
        assert discount == Decimal("50.00")

    @pytest.mark.asyncio
    async def test_no_bank_offer_without_payment_info(self, sample_product, sample_customer):
        """Test that bank offer requires payment info."""
        offer = BankOfferConfig(
            bank_name="ICICI",
            discount_percentage=Decimal("10"),
        )
        strategy = BankOfferStrategy({"ICICI": offer})
        
        cart_item = CartItem(product=sample_product, quantity=1, size="L")
        context = DiscountContext(
            cart_items=[cart_item],
            customer=sample_customer,
        )

        discount = await strategy.calculate(context)

        assert discount == Decimal("0")

    @pytest.mark.asyncio
    async def test_validate_card_type_requirement(self, sample_product, sample_customer):
        """Test bank offer validation for specific card type."""
        offer = BankOfferConfig(
            bank_name="HDFC",
            discount_percentage=Decimal("15"),
            card_type="CREDIT",
        )
        strategy = BankOfferStrategy({"HDFC": offer})
        
        cart_item = CartItem(product=sample_product, quantity=1, size="L")
        
        # Try with debit card
        payment_debit = PaymentInfo(method="CARD", bank_name="HDFC", card_type="DEBIT")
        context = DiscountContext(
            cart_items=[cart_item],
            customer=sample_customer,
            payment_info=payment_debit,
        )

        result = await strategy.validate(context)

        assert result.is_valid is False
        assert "CREDIT" in result.error_message
