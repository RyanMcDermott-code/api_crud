from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Numeric, Date, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from datetime import datetime, timezone


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    sku = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    base_price = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    price_history = relationship('ProductPrice', back_populates='product')


class ProductPrice(Base):
    __tablename__ = 'product_prices'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    current_price = Column(Numeric(10, 2))
    discount_percent = Column(Numeric(5, 2), nullable=True)
    effective_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    end_date = Column(DateTime, nullable=True)

    product = relationship('Product', back_populates='price_history')


class Transaction_Item(Base):
    __tablename__ = 'transaction_items'

    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer)
    price = Column(Numeric(10, 2))

    transaction = relationship('Transaction', back_populates='items')


class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    store_id = Column(Integer, ForeignKey('stores.id'))
    employee_id = Column(Integer, ForeignKey('employees.id'))
    date_created = Column(DateTime)

    items = relationship('Transaction_Item', back_populates='transaction')


class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_registered = Column(Boolean)


class Customer_Account(Base):
    __tablename__ = 'customer_accounts'

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), unique=True)
    email = Column(String(255), unique=True)
    hashed_password = Column(String(255))
    date_created = Column(DateTime)
    phone_number = Column(String(10))


class Store(Base):
    __tablename__ = 'stores'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)


class Store_Inventory(Base):
    __tablename__ = 'store_inventories'

    id = Column(Integer, primary_key=True)
    store_id = Column(Integer, ForeignKey('stores.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    current_price = Column(Numeric(10, 2))
    last_updated = Column(DateTime, nullable=True)
    

class Employee(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    dob = Column(Date)
