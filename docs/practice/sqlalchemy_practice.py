from sqlalchemy import (
    String, Integer, Float, Boolean, Text, DateTime, Date, Time,
    DECIMAL, JSON, LargeBinary, Enum, ForeignKey, CheckConstraint,
    Index, UniqueConstraint,create_engine,Numeric
)
from sqlalchemy.orm import Session,DeclarativeBase,Mapped,mapped_column,validates,Relationship
from datetime import datetime
from typing import List
import enum

# Connect to your Docker PostgreSQL
engine = create_engine('postgresql://myuser:password123@localhost:5432/learning_db',echo=True)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id : Mapped[int] = mapped_column(primary_key=True,autoincremnt=True,index=True)
    username : Mapped[String] = mapped_column(String(50),unique=True,nullable=False)
    created_at : Mapped[datetime] = mapped_column(default=datetime.now)
    is_active : Mapped[bool] = mapped_column(default=True)

    orders : Mapped[List["Order"]] = Relationship(back_populates="user")

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
    user_id : Mapped[int] = mapped_column(ForeignKey("User.id",ondelete="CASCADE"))
    status : Mapped[Status] = mapped_column(Enum(Status))
    created_at : Mapped[datetime] = mapped_column(DateTime,default=datetime.now)


    user : Mapped["User"] = Relationship(back_populates="user")


class OrderItem(Base):
    id : Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    order_id : Mapped[int] = mapped_column(ForeignKey("Order.id"))
    product_id : Mapped[int] = mapped_column(ForeignKey("Product.id"))
    quantity : Mapped[int] = mapped_column(nullable=False)

    product : Mapped["Product"] = Relationship(back_populates="order_item")
    
    @hybrid_property
    def total_price(self):
        return 
    
with Session(engine) as session:


    session.commit()



# Use it exactly like any PostgreSQL database
# Your SQLAlchemy code remains the same!