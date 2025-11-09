from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Date, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
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
    inventory_items = relationship('Store_Inventory', back_populates='product')
    transaction_items = relationship('Transaction_Item', back_populates='product')

class ProductPrice(Base):
    __tablename__ = 'product_prices'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    current_price = Column(Numeric(10, 2), nullable=False)
    discount_percent = Column(Numeric(5, 2), nullable=True)
    effective_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    end_date = Column(DateTime, nullable=True)
    
    product = relationship('Product', back_populates='price_history')

class Transaction_Item(Base):
    __tablename__ = 'transaction_items'
    
    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)  # Price at time of purchase
    
    transaction = relationship('Transaction', back_populates='items')
    product = relationship('Product', back_populates='transaction_items')

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)  # Nullable for anonymous customers
    store_id = Column(Integer, ForeignKey('stores.id'), nullable=False)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    date_created = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    items = relationship('Transaction_Item', back_populates='transaction')
    customer = relationship('Customer', back_populates='transactions')
    store = relationship('Store', back_populates='transactions')
    employee = relationship('Employee', back_populates='transactions')

class Customer(Base):
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_registered = Column(Boolean, default=False)
    
    account = relationship('Customer_Account', back_populates='customer', uselist=False)  # uselist=False for 1-to-1
    transactions = relationship('Transaction', back_populates='customer')

class Customer_Account(Base):
    __tablename__ = 'customer_accounts'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    date_created = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    phone_number = Column(String(15), nullable=True)
    
    customer = relationship('Customer', back_populates='account')

class Store(Base):
    __tablename__ = 'stores'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    address = Column(String(500), nullable=True)
    
    inventory = relationship('Store_Inventory', back_populates='store')
    transactions = relationship('Transaction', back_populates='store')

class Store_Inventory(Base):
    __tablename__ = 'store_inventories'
    
    id = Column(Integer, primary_key=True)
    store_id = Column(Integer, ForeignKey('stores.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    current_price = Column(Numeric(10, 2), nullable=True)  # Store-specific price override
    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Composite unique constraint: one row per store-product combination
    __table_args__ = (
        UniqueConstraint('store_id', 'product_id', name='uq_store_product'),
    )
    
    store = relationship('Store', back_populates='inventory')
    product = relationship('Product', back_populates='inventory_items')

class Employee(Base):
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    dob = Column(Date, nullable=True)
    store_id = Column(Integer, ForeignKey('stores.id'), nullable=True)
    hire_date = Column(Date, nullable=True)
    
    transactions = relationship('Transaction', back_populates='employee')
    store = relationship('Store')