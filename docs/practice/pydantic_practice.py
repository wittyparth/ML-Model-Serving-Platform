# Pydantic Comprehensive Exercise: E-commerce Order Management System
# 
# OBJECTIVE: Build a complete order management system that uses ALL Pydantic concepts
# 
# REQUIREMENTS:
# 1. Create models with proper validation
# 2. Use nested models
# 3. Implement custom validators
# 4. Use Field() with constraints
# 5. Handle optional fields and defaults
# 6. Create methods for serialization
# 7. Implement a complete workflow

from pydantic import BaseModel, Field, EmailStr, field_validator, HttpUrl, model_validator
from typing import List, Optional
from datetime import datetime
from enum import Enum
import re

# TODO 1: Create an enum for OrderStatus
# Should include: PENDING, CONFIRMED, SHIPPED, DELIVERED, CANCELLED
class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# TODO 2: Create a Product model with:
# - product_id: int
# - name: str (min 1, max 100 chars)
# - price: float (must be > 0)
# - category: str
# - stock_quantity: int (must be >= 0)
# - description: Optional[str]
class Product(BaseModel):
    product_id : int
    name : str = Field(...,min_length=1,max_length=100)
    price : float = Field(...,gt=0)
    category : str
    stock_quantity : int = Field(...,ge=0)
    description : Optional[str] = None


# TODO 3: Create an OrderItem model with:
# - product: Product (nested model)
# - quantity: int (must be > 0)
# - Add a custom validator to check if quantity <= product.stock_quantity
# - Add a method calculate_subtotal() that returns price * quantity
class OrderItem(BaseModel):
    product : Product
    quantity : int = Field(...,gt=0)
    @model_validator(mode='after')
    def check_stock(self):
        """Validates after all fields are set"""
        if self.quantity > self.product.stock_quantity:
            raise ValueError(
                f'Only {self.product.stock_quantity} items in stock'
            )
        return self
    
    def calculate_subtotal(self):
        return self.quantity * self.product.price


# TODO 4: Create an Address model with:
# - street: str
# - city: str
# - state: str (exactly 2 uppercase letters)
# - zip_code: str (5 digits)
# - country: str (default "USA")
# - Add a validator for state format
# - Add a validator for zip_code format
class Address(BaseModel):
    street : str
    city : str
    state : str
    zip_code : str
    country : str = "USA"
    @field_validator("state")
    def state_validator(cls,v):
            if len(v)!=2:
                raise ValueError(f'State must be exactly 2 characters')
            elif v != v.upper():
                raise ValueError(f'State must be uppercase')
    @field_validator("zip_code")
    def zip_code_validator(cls,v):
            if len(v.strip())!=5:
                raise ValueError(f"Length of zip code must be exactly 5 characters")


# TODO 5: Create a Customer model with:
# - customer_id: int
# - name: str (min 2 chars)
# - email: EmailStr
# - phone: str (format: XXX-XXX-XXXX)
# - address: Address (nested)
# - Add a validator for phone format
class Customer(BaseModel):
    customer_id : int
    name : str = Field(...,min_length=2)
    email : EmailStr
    phone : str
    address : Address
    
    @field_validator("phone")
    def validate_phone(cls,v):
            pattern = r"^\d{3}-\d{3}-\d{4}$"
            if not re.search(pattern,v):
                raise ValueError(f"Enter a valid phone number")


# TODO 6: Create a PaymentInfo model with:
# - card_number: str (last 4 digits only, format: ****1234)
# - payment_method: str (only "credit_card", "debit_card", or "paypal")
# - transaction_id: str
# - Add validators for card_number format and payment_method

class PaymentInfo(BaseModel):
    card_number : str
    payment_method : str
    transaction_id : str
    
    @field_validator("card_number")
    def validate_card_number(cls,v):
            pattern = r"^\*{4}\d{4}$"
            if not re.search(pattern,v):
                raise valueError(f"Enter a valid card number")
    
    @field_validator("payment_method")
    def validate_payment_method(cls,v):
            valid_method = ["paypal","credit_card","debit_card"]
            if v not in valid_method:
                raise ValueError("Please enter a valid payment method")
            


# TODO 7: Create an Order model with:
# - order_id: int
# - customer: Customer (nested)
# - items: List[OrderItem] (min 1 item)
# - status: OrderStatus (default PENDING)
# - payment_info: Optional[PaymentInfo]
# - created_at: datetime (default to now)
# - shipping_address: Optional[Address] (if None, use customer.address)
# - Add a method calculate_total() that sums all item subtotals
# - Add a method calculate_tax(tax_rate: float) that returns total * tax_rate
# - Add a method get_order_summary() that returns a formatted string
# - Add config to strip whitespace and validate on assignment
class Order(BaseModel):
    model_config = {"str_strip_whitespace": True, "validate_assignment": True}
    order_id : int
    customer : Customer
    items : List[OrderItem] = Field(...,min_lengt=1)
    status : OrderStatus = "PENDING"
    payment_info : Optional[PaymentInfo]
    created_at : datetime = datetime.now()
    shipping_address : Optional[Address] = None
    def calculate_total(self):
        return sum([item.calculate_subtotal() for item in self.items])
    def calculate_tax(self,tax_rate : float):
        return self.calculate_total() * tax_rate
    def get_order_summary(self):
        return f"Formatted string of the order do it yourself"

# TODO 8: Implement helper functions

def create_order_from_dict(order_data: dict) -> Order:
    """
    Create an Order instance from a dictionary
    Handle validation errors gracefully
    """
    return Order(**order_data)


def update_order_status(order: Order, new_status: OrderStatus) -> Order:
    """
    Update order status and validate the change
    Return updated order
    """
    order.status = new_status
    return order


def export_order_to_json(order: Order, filename: str) -> None:
    """
    Export order to a JSON file
    """
    order.model_dump_json()


# TODO 9: Test your implementation with this sample data
def test_system():
    """
    Test the complete system with sample data
    """
    
    # Sample product data
    product1_data = {
        "product_id": 1,
        "name": "Laptop",
        "price": 999.99,
        "category": "Electronics",
        "stock_quantity": 10,
        "description": "High-performance laptop"
    }
    
    product2_data = {
        "product_id": 2,
        "name": "Mouse",
        "price": 29.99,
        "category": "Accessories",
        "stock_quantity": 50
    }
    
    # Sample order data
    order_data = {
        "order_id": 1001,
        "customer": {
            "customer_id": 501,
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "555-123-4567",
            "address": {
                "street": "123 Main St",
                "city": "Boston",
                "state": "MA",
                "zip_code": "02101"
            }
        },
        "items": [
            {
                "product": product1_data,
                "quantity": 1
            },
            {
                "product": product2_data,
                "quantity": 2
            }
        ],
        "payment_info": {
            "card_number": "****1234",
            "payment_method": "credit_card",
            "transaction_id": "TXN123456789"
        }
    }
    
    try:
        # Test 1: Create order
        print("Test 1: Creating order...")
        order = create_order_from_dict(order_data)
        print(f"✓ Order created: {order.order_id}")
        
        # Test 2: Calculate totals
        print(f"\nTest 2: Calculating totals...")
        total = order.calculate_total()
        tax = order.calculate_tax(0.08)
        print(f"✓ Total: ${total:.2f}")
        print(f"✓ Tax (8%): ${tax:.2f}")
        print(f"✓ Grand Total: ${total + tax:.2f}")
        
        # Test 3: Get summary
        print(f"\nTest 3: Order summary...")
        print(order.get_order_summary())
        
        # Test 4: Update status
        print(f"\nTest 4: Updating status...")
        order = update_order_status(order, OrderStatus.CONFIRMED)
        print(f"✓ Status updated to: {order.status.value}")
        
        # Test 5: Export to JSON
        print(f"\nTest 5: Exporting to JSON...")
        export_order_to_json(order, "order_1001.json")
        print(f"✓ Exported to order_1001.json")
        
        # Test 6: Serialization
        print(f"\nTest 6: Testing serialization...")
        order_dict = order.model_dump()
        order_json = order.model_dump_json(indent=2)
        print(f"✓ Converted to dict and JSON")
        
        # Test 7: Invalid data (should raise validation errors)
        print(f"\nTest 7: Testing validation...")
        invalid_data = order_data.copy()
        invalid_data["items"][0]["quantity"] = 0  # Invalid: quantity must be > 0
        
        try:
            invalid_order = create_order_from_dict(invalid_data)
            print("✗ Validation failed to catch invalid quantity")
        except Exception as e:
            print(f"✓ Validation caught error: {type(e).__name__}")
        
        print("\n" + "="*50)
        print("ALL TESTS PASSED! 🎉")
        print("="*50)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


# BONUS CHALLENGES:
# 1. Add a discount_code field to Order with validation (format: [A-Z]{4}\d{4})
# 2. Add a method to apply discount to the order
# 3. Create a validator that checks if all products have sufficient stock
# 4. Add a method to generate an invoice in a formatted string
# 5. Implement order history tracking (list of status changes with timestamps)

if __name__ == "__main__":
    print("Pydantic E-commerce Exercise")
    print("="*50)
    print("Complete all TODOs and run test_system()")
    print("="*50)
    
    # Uncomment when you're ready to test:
    test_system()