"""
Example usage demonstrating the discount service.

This example shows the primary scenario from the assignment:
- PUMA T-shirt with 40% brand discount
- Additional 10% category discount on T-shirts
- ICICI bank offer (10% instant discount)
- Optional SUPER69 voucher (69% off)
"""

import asyncio
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


async def main():
    """Run example discount calculations."""
    
    # Initialize the discount service
    service = DiscountService(
        brand_strategy=get_brand_strategy(),
        category_strategy=get_category_strategy(),
        voucher_strategy=get_voucher_strategy(),
        bank_strategy=get_bank_strategy(),
    )
    
    # Get cart with PUMA T-shirt (₹1000)
    cart = get_multiple_discount_scenario()
    
    print("=" * 70)
    print("DISCOUNT SERVICE DEMONSTRATION")
    print("=" * 70)
    print()
    
    # Scenario 1: Just brand + category discounts
    print("SCENARIO 1: Brand + Category Discounts")
    print("-" * 70)
    result1 = await service.calculate_cart_discounts(
        cart_items=get_multiple_discount_scenario(),
        customer=NEW_CUSTOMER,
    )
    print(f"Original Price: ₹{result1.original_price}")
    print(f"Final Price:    ₹{result1.final_price}")
    print(f"Total Savings:  ₹{result1.original_price - result1.final_price}")
    print(f"Applied Discounts:")
    for name, amount in result1.applied_discounts.items():
        print(f"  - {name}: ₹{amount}")
    print()
    
    # Scenario 2: Brand + Category + Bank Offer
    print("SCENARIO 2: Brand + Category + Bank Offer (ICICI)")
    print("-" * 70)
    result2 = await service.calculate_cart_discounts(
        cart_items=get_multiple_discount_scenario(),
        customer=NEW_CUSTOMER,
        payment_info=ICICI_CARD_PAYMENT,
    )
    print(f"Original Price: ₹{result2.original_price}")
    print(f"Final Price:    ₹{result2.final_price}")
    print(f"Total Savings:  ₹{result2.original_price - result2.final_price}")
    print(f"Applied Discounts:")
    for name, amount in result2.applied_discounts.items():
        print(f"  - {name}: ₹{amount}")
    print()
    
    # Scenario 3: Brand + Category + Voucher + Bank Offer
    print("SCENARIO 3: All Discounts (Brand + Category + Voucher + Bank)")
    print("-" * 70)
    result3 = await service.calculate_cart_discounts(
        cart_items=get_multiple_discount_scenario(),
        customer=NEW_CUSTOMER,
        payment_info=ICICI_CARD_PAYMENT,
        voucher_code="TSHIRT15",
    )
    print(f"Original Price: ₹{result3.original_price}")
    print(f"Final Price:    ₹{result3.final_price}")
    print(f"Total Savings:  ₹{result3.original_price - result3.final_price}")
    print(f"Applied Discounts:")
    for name, amount in result3.applied_discounts.items():
        print(f"  - {name}: ₹{amount}")
    print()
    
    # Scenario 4: Test voucher validation
    print("SCENARIO 4: Voucher Validation")
    print("-" * 70)
    
    # Valid voucher
    is_valid_tshirt = await service.validate_discount_code(
        code="TSHIRT15",
        cart_items=get_multiple_discount_scenario(),
        customer=NEW_CUSTOMER,
    )
    print(f"TSHIRT15 voucher valid: {is_valid_tshirt}")
    
    # Invalid voucher (SUPER69 excludes premium brands, PUMA is regular so should be OK)
    is_valid_super = await service.validate_discount_code(
        code="SUPER69",
        cart_items=get_multiple_discount_scenario(),
        customer=NEW_CUSTOMER,
    )
    print(f"SUPER69 voucher valid:  {is_valid_super}")
    
    # Invalid code
    is_valid_fake = await service.validate_discount_code(
        code="INVALID123",
        cart_items=get_multiple_discount_scenario(),
        customer=NEW_CUSTOMER,
    )
    print(f"INVALID123 voucher valid: {is_valid_fake}")
    
    print()
    print("=" * 70)
    print("CALCULATION BREAKDOWN (Scenario 2)")
    print("=" * 70)
    print("PUMA T-shirt Base Price:           ₹1,000.00")
    print("After Brand Discount (40%):        ₹600.00 (saved ₹400)")
    print("After Category Discount (10%):     ₹540.00 (saved ₹60)")
    print("After Bank Offer (10%):            ₹486.00 (saved ₹54)")
    print()
    print(f"Total discount: ₹{result2.original_price - result2.final_price}")
    print(f"Savings: {((result2.original_price - result2.final_price) / result2.original_price * 100):.1f}%")
    print("=" * 70)
    print()
    
    # Scenario 5: Single Discount Mode (Best Discount Only)
    print("=" * 70)
    print("SCENARIO 5: SINGLE DISCOUNT MODE (Best Discount Only)")
    print("=" * 70)
    print()
    
    # Initialize service with stacking disabled
    best_discount_service = DiscountService(
        brand_strategy=get_brand_strategy(),
        category_strategy=get_category_strategy(),
        voucher_strategy=get_voucher_strategy(),
        bank_strategy=get_bank_strategy(),
        allow_discount_stacking=False,  # Only apply best discount
    )
    
    print("With allow_discount_stacking=False, only the BEST discount is applied:")
    print()
    
    # Test 1: Without voucher
    print("Test 1: Brand (40%) vs Category (10%) vs Bank (10%)")
    print("-" * 70)
    result_best1 = await best_discount_service.calculate_cart_discounts(
        cart_items=get_multiple_discount_scenario(),
        customer=NEW_CUSTOMER,
        payment_info=ICICI_CARD_PAYMENT,
    )
    print(f"Original Price: ₹{result_best1.original_price}")
    print(f"Final Price:    ₹{result_best1.final_price}")
    print(f"Total Savings:  ₹{result_best1.original_price - result_best1.final_price}")
    print(f"Applied Discount:")
    for name, amount in result_best1.applied_discounts.items():
        print(f"  - {name}: ₹{amount}")
    print(f"Message: {result_best1.message}")
    print()
    
    # Test 2: With SUPER69 voucher
    print("Test 2: Brand (40%) vs SUPER69 Voucher (69%)")
    print("-" * 70)
    result_best2 = await best_discount_service.calculate_cart_discounts(
        cart_items=get_multiple_discount_scenario(),
        customer=NEW_CUSTOMER,
        voucher_code="SUPER69",
    )
    print(f"Original Price: ₹{result_best2.original_price}")
    print(f"Final Price:    ₹{result_best2.final_price}")
    print(f"Total Savings:  ₹{result_best2.original_price - result_best2.final_price}")
    print(f"Applied Discount:")
    for name, amount in result_best2.applied_discounts.items():
        print(f"  - {name}: ₹{amount}")
    print(f"Message: {result_best2.message}")
    print()
    
    # Comparison
    print("COMPARISON: Stacking vs Best Discount")
    print("-" * 70)
    print(f"Stacking Mode (Scenario 2):      ₹{result2.final_price} ({len(result2.applied_discounts)} discounts)")
    print(f"Best Discount Mode (Test 1):     ₹{result_best1.final_price} ({len(result_best1.applied_discounts)} discount)")
    print()
    print("Stacking mode gives better deal when multiple discounts can combine!")
    print("Best discount mode is simpler and easier to understand for customers.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
