from sqlalchemy import (
    String, Integer, Float, Boolean, Text, DateTime, Date, Time,
    DECIMAL, JSON, LargeBinary, Enum, ForeignKey, CheckConstraint,
    Index, UniqueConstraint,create_engine,Numeric, select
)
from sqlalchemy.orm import Session,DeclarativeBase,Mapped,mapped_column,validates,relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
from typing import List
import enum
from sqlalchemy import event

# Connect to your Docker PostgreSQL
engine = create_engine('sqlite:///mydb.db',echo=True)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id : Mapped[int] = mapped_column(primary_key=True,autoincrement=True,index=True)
    username : Mapped[String] = mapped_column(String(50),unique=True,nullable=False)
    created_at : Mapped[datetime] = mapped_column(default=datetime.now)
    is_active : Mapped[bool] = mapped_column(default=True)

    orders : Mapped[List["Order"]] = relationship(back_populates="user")

class ProductCategory(enum.Enum):
    ELECTRONICS = "ELECTRONICS"
    FASHION = "FASHION"
    FOOD = "FOOD"
    BOOKS = "BOOKS"

class Product(Base):
    __tablename__ = "products"
    
    id : Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    name : Mapped[str] = mapped_column(index=True)
    price : Mapped[float] = mapped_column(Numeric(10,2),nullable=False)
    stock : Mapped[int] = mapped_column(nullable=False)
    category : Mapped[ProductCategory] = mapped_column(Enum(ProductCategory),default=ProductCategory.ELECTRONICS)

    order_item : Mapped[List["OrderItem"]] = relationship(back_populates="product")


    @validates("price")
    def validate_price(self,key,value):
        if value <= 0:
            raise ValueError("Price must be greater than zero")
        return value
    
class Status(enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"

class Order(Base):
    __tablename__ = "orders"

    id : Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    user_id : Mapped[int] = mapped_column(ForeignKey("users.id",ondelete="CASCADE"))
    status : Mapped[Status] = mapped_column(Enum(Status))
    created_at : Mapped[datetime] = mapped_column(DateTime,default=datetime.now)


    user : Mapped["User"] = relationship(back_populates="orders")


class OrderItem(Base):
    __tablename__ = "order_items"
    id : Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    order_id : Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id : Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity : Mapped[int] = mapped_column(nullable=False)

    product : Mapped["Product"] = relationship(back_populates="order_item")
    
    @hybrid_property
    def total_price(self):
        return self.product.price * self.quantity


class PaymentMethod(enum.Enum):
    UPI = "UPI"
    COD = "COD"
    CARD = "CARD"
class Payment(Base):
    __tablename__ = "payments"

    id : Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    order_id : Mapped[int] = mapped_column(ForeignKey("orders.id"),unique=True)
    payment_method : Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod))
    paid_at : Mapped[datetime] = mapped_column(DateTime,default=datetime.now)

class InventoryLog(Base):
    __tablename__ = "inventory_logs"

    id : Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    product_id : Mapped[int] = mapped_column(ForeignKey("products.id"))
    change : Mapped[int] = mapped_column(nullable=False)
    reason : Mapped[str] = mapped_column(Text,nullable=True)
    created_at : Mapped[datetime] = mapped_column(DateTime,default=datetime.now)

    # @event.listens_for("InventoryLog.change", "get")
    # def log_inventory_change(target, value, oldvalue, initiator):
    #     if value  > oldvalue:
    #         print(f"Inventory increased by {value - oldvalue}")
    #     elif value < oldvalue:
    #         print(f"Inventory decreased by {oldvalue - value}")
        
Base.metadata.create_all(engine)
with Session(engine) as session:
#     users = [
#     User(username="john_doe"),
#     User(username="alice_smith"),
#     User(username="mike_jordan"),
#     User(username="sara_connor"),
# ]
#     session.add_all(users)
#     products = [
#     Product(name="Laptop", price=89999.99, stock=10, category=ProductCategory.ELECTRONICS),
#     Product(name="Headphones", price=2999.50, stock=50, category=ProductCategory.ELECTRONICS),
#     Product(name="Jeans", price=1499.99, stock=40, category=ProductCategory.FASHION),
#     Product(name="Pizza", price=499.00, stock=25, category=ProductCategory.FOOD),
#     Product(name="Novel", price=299.00, stock=100, category=ProductCategory.BOOKS),
# ]
#     session.add_all(products)
#     orders = [
#     Order(user=users[0], status=Status.PENDING),
#     Order(user=users[1], status=Status.CONFIRMED),
#     Order(user=users[2], status=Status.SHIPPED),
#     Order(user=users[3], status=Status.CANCELLED),
# ]

#     session.add_all(orders)
#     session.flush()
#     order_items = [
#     OrderItem(order_id=1, product_id=1, quantity=1),  # Laptop
#     OrderItem(order_id=1, product_id=2, quantity=2),  # Headphones
#     OrderItem(order_id=2, product_id=3, quantity=1),  # Jeans
#     OrderItem(order_id=2, product_id=5, quantity=3),  # Novel
#     OrderItem(order_id=3, product_id=4, quantity=2),  # Pizza
# ]
#     session.add_all(order_items)

#     payments = [
#     Payment(order_id=1, payment_method=PaymentMethod.CARD, paid_at=datetime.now()),
#     Payment(order_id=2, payment_method=PaymentMethod.UPI, paid_at=datetime.now()),
#     Payment(order_id=3, payment_method=PaymentMethod.COD, paid_at=datetime.now()),
# ]
#     session.add_all(payments)
#     session.flush()
#     inventory_logs = [
#     InventoryLog(product_id=1, change=-1, reason="Order #1"),
#     InventoryLog(product_id=2, change=-2, reason="Order #1"),
#     InventoryLog(product_id=3, change=-1, reason="Order #2"),
#     InventoryLog(product_id=5, change=-3, reason="Order #2"),
#     InventoryLog(product_id=4, change=-2, reason="Order #3"),
# ]
#     session.add_all(inventory_logs)
    stmt = select(User)
    users = session.scalars(stmt).all()
    for user in users:
        print(user.id,user.username)
    session.commit()



# Use it exactly like any PostgreSQL database
# Your SQLAlchemy code remains the same!