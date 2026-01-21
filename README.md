# E-Commerce Discount Service

A flexible, maintainable discount calculation service for fashion e-commerce platforms, designed to handle multiple discount types with proper stacking logic.

## 📋 Table of Contents
- [Overview](#overview)
- [Technical Approach](#technical-approach)
- [Architecture](#architecture)
- [Discount Logic](#discount-logic)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Running Tests](#running-tests)
- [Assumptions & Decisions](#assumptions--decisions)

## Overview

This service implements a discount calculation engine that handles:
- **Brand-specific discounts** (e.g., "Min 40% off on PUMA")
- **Category-specific deals** (e.g., "Extra 10% off on T-shirts")
- **Voucher codes** (e.g., "SUPER69" for 69% off)
- **Bank card offers** (e.g., "10% instant discount on ICICI Bank cards")

## Technical Approach

### Core Philosophy
1. **Separation of Concerns**: Discount validation and calculation logic are separated
2. **Extensibility**: Easy to add new discount types without modifying existing code
3. **Type Safety**: Comprehensive type hints throughout
4. **Testability**: Pure functions and dependency injection for easy testing

### Technology Stack
- **Python 3.11+**: For modern type hints and performance
- **dataclasses**: For clean data modeling
- **pytest**: For comprehensive testing
- **Decimal**: For precise financial calculations

## Architecture

### 1. **Discount Strategy Pattern**
Each discount type implements a common interface:
```python
class DiscountStrategy(ABC):
    @abstractmethod
    async def calculate(self, context: DiscountContext) -> Decimal:
        pass
    
    @abstractmethod
    async def validate(self, context: DiscountContext) -> ValidationResult:
        pass
```

**Discount Types**:
- `BrandDiscountStrategy`: Handles brand-tier based discounts
- `CategoryDiscountStrategy`: Handles category-level discounts  
- `VoucherDiscountStrategy`: Handles voucher/coupon codes
- `BankOfferStrategy`: Handles payment method-based discounts

### 2. **Discount Service Orchestrator**
The `DiscountService` class orchestrates the discount application:
- Validates each discount type
- Applies discounts in the correct order
- Tracks which discounts were applied
- Calculates final prices

### 3. **Data Layer**
- `fake_data.py`: Contains dummy discount configurations
- `models.py`: Core data models (provided in assignment)
- `discount_config.py`: Discount rule definitions

## Discount Logic

### Stacking Order (Sequential Application)
```
Original Price
    ↓
1. Brand Discount (updates product.current_price)
    ↓
2. Category Discount (further reduces price)
    ↓
3. Voucher Code (applied on top of above)
    ↓
4. Bank Offer (final discount)
    ↓
Final Price
```

### Calculation Method
- **Brand/Category Discounts**: Applied first, update `current_price`
- **Vouchers**: Percentage/fixed discount on current cart value
- **Bank Offers**: Final discount on payment amount

### Example Calculation
```
PUMA T-shirt (Base: ₹1000)
├─ Brand Discount (40%): ₹1000 - ₹400 = ₹600
├─ Category Discount (10%): ₹600 - ₹60 = ₹540
├─ Voucher (SUPER69 - 69%): ₹540 - ₹372.6 = ₹167.4
└─ Bank Offer (10% ICICI): ₹167.4 - ₹16.74 = ₹150.66
```

## Project Structure

```
unifize-assessment/
├── README.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── models.py              # Data models (provided)
│   ├── discount_service.py    # Core service implementation
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base.py           # Abstract base strategy
│   │   ├── brand.py          # Brand discount logic
│   │   ├── category.py       # Category discount logic
│   │   ├── voucher.py        # Voucher logic
│   │   └── bank.py           # Bank offer logic
│   ├── validators/
│   │   ├── __init__.py
│   │   └── discount_validator.py
│   └── data/
│       ├── __init__.py
│       ├── fake_data.py      # Dummy data
│       └── discount_config.py
├── tests/
│   ├── __init__.py
│   ├── test_discount_service.py
│   ├── test_strategies.py
│   └── test_validators.py
└── .gitignore
```

## Setup & Installation

### Prerequisites
- Python 3.11 or higher
- pip

### Installation Steps

```bash
# Clone the repository
git clone <repository-url>
cd unifize-assessment

# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Code

### Run Example Demonstration

```bash
python3 example.py
```

This will demonstrate:
- Brand + Category discounts
- Brand + Category + Bank offer
- All discounts combined (Brand + Category + Voucher + Bank)
- Voucher validation examples

### Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_discount_service.py -v
```

### Expected Output

When running `python3 example.py`, you should see:

```
SCENARIO 2: Brand + Category + Bank Offer (ICICI)
Original Price: ₹1000.00
Final Price:    ₹486.00
Total Savings:  ₹514.00
Applied Discounts:
  - Brand Discount: ₹400.00
  - Category Discount: ₹60.00
  - Bank Offer (ICICI): ₹54.00
```

All 23 tests should pass when running `pytest`.

## Usage

### Discount Stacking Modes

The service supports two modes controlled by the `allow_discount_stacking` parameter:

#### 1. **Stacking Mode** (default: `allow_discount_stacking=True`)
Applies all eligible discounts sequentially for maximum savings:

```python
service = DiscountService(
    brand_strategy=get_brand_strategy(),
    category_strategy=get_category_strategy(),
    voucher_strategy=get_voucher_strategy(),
    bank_strategy=get_bank_strategy(),
    allow_discount_stacking=True,  # Default
)

# Result: Multiple discounts stacked
# Brand (40%) → Category (10%) → Bank (10%)
# ₹1000 → ₹486 (51.4% total savings)
```

#### 2. **Best Discount Mode** (`allow_discount_stacking=False`)
Calculates all discounts independently and applies only the highest one:

```python
service = DiscountService(
    brand_strategy=get_brand_strategy(),
    category_strategy=get_category_strategy(),
    voucher_strategy=get_voucher_strategy(),
    bank_strategy=get_bank_strategy(),
    allow_discount_stacking=False,  # Only best discount
)

# Result: Only the best single discount applied
# Compares: Brand (40%), Category (10%), Bank (10%)
# Applies: Brand (40%) as it's highest
# ₹1000 → ₹600 (40% savings)
```

**When to use each mode:**
- **Stacking Mode**: E-commerce platforms wanting to reward customers with maximum savings
- **Best Discount Mode**: Simpler pricing, easier for customers to understand, better for business margins


## Assumptions & Decisions

### 1. **Discount Stacking Rules**
- **Assumption**: Discounts are applied sequentially, not combined multiplicatively
- **Reasoning**: Clearer for customers and easier to debug
- **Example**: 40% + 10% means first apply 40%, then 10% on remaining amount

### 2. **Price Update Flow**
- **Assumption**: `current_price` reflects brand/category discounts already applied
- **Reasoning**: Aligns with typical e-commerce display (strikethrough price)
- **Impact**: Vouchers and bank offers work on `current_price`, not `base_price`

### 3. **Voucher Restrictions**
- **Assumption**: Vouchers can have:
  - Brand exclusions (e.g., not valid on premium brands)
  - Category restrictions (e.g., only on T-shirts)
  - Minimum cart value requirements
  - Customer tier requirements
- **Reasoning**: Matches real-world e-commerce behavior

### 4. **Bank Offers**
- **Assumption**: Applied only when `payment_info` is provided
- **Reasoning**: Bank offers are confirmed at payment time
- **Impact**: Final price may change when payment method is selected

### 5. **CustomerProfile**
- **Assumption**: Added `CustomerProfile` model with tier information
- **Reasoning**: Needed for voucher validation (mentioned in interface)
- **Fields**: `id`, `tier`, `total_purchases`

### 6. **Error Handling**
- **Decision**: Return detailed validation messages instead of raising exceptions
- **Reasoning**: Better UX - show users why discount failed
- **Example**: "Voucher SUPER69 not valid for PREMIUM brand products"

### 7. **Decimal Precision**
- **Decision**: Use Python's `Decimal` type for all monetary calculations
- **Reasoning**: Avoid floating-point precision errors
- **Rounding**: Round to 2 decimal places for final prices

### 8. **Async/Await**
- **Decision**: Implement async methods as specified in interface
- **Reasoning**: Future-proof for database/API calls
- **Note**: Current implementation doesn't require async, but structure supports it

### 9. **Test Scenarios**
- **Coverage**:
  - Multiple discount stacking (PUMA T-shirt scenario)
  - Voucher validation failures
  - Bank offer application
  - Edge cases (zero discounts, invalid codes)

### 10. **Dummy Data Scope**
- **Included**:
  - 3-5 products across different brands/categories
  - 2-3 voucher codes with varying restrictions
  - 2 bank offers
  - Sample customer profiles
- **Reasoning**: Sufficient to demonstrate all discount types and validations

## Future Enhancements

1. **Single Discount Mode**: Add a feature flag (`allow_discount_stacking`) that when disabled, applies only the best single discount instead of stacking multiple discounts. The service would calculate all eligible discounts and automatically select the one offering maximum savings. This provides flexibility for different business models:
   - `allow_discount_stacking=True` (current): Apply all eligible discounts sequentially (Brand → Category → Voucher → Bank)
   - `allow_discount_stacking=False` (new): Calculate each discount independently and apply only the highest one
2. **Database Integration**: PostgreSQL with SQLAlchemy
3. **Caching**: Redis for frequently accessed discount rules
4. **Admin Interface**: Manage discount rules dynamically
5. **Analytics**: Track discount usage and effectiveness
6. **A/B Testing**: Framework for testing discount strategies
7. **Real-time Inventory**: Check stock before applying discounts
8. **Scheduled Discounts**: Time-based discount activation

## Design Decisions Trade-offs

| Decision | Pros | Cons | Chosen Approach |
|----------|------|------|-----------------|
| Strategy Pattern | Extensible, testable | More files | ✅ Use it |
| Async Interface | Future-proof | Overhead for simple ops | ✅ Use it |
| Decimal vs Float | Precision | Slightly slower | ✅ Use Decimal |
| Validation in Strategy | Cohesive | Tight coupling | ✅ Separate validators |

## Contact & Questions

For any questions or clarifications, please reach out or raise an issue.

---

**Last Updated**: January 2026  
**Version**: 1.0.0
