from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Numeric, Date, Boolean,
    UniqueConstraint, CheckConstraint, Index, text, and_, or_
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timezone
import uuid


class Product(Base):
    """
    Product master table containing SKU, name, and base pricing information.
    
    Relationships:
        - price_history: Historical and current pricing records
        - inventory_items: Stock levels across all stores
        - transaction_items: Sales history
        - inventory_movements: Stock movement tracking
    """
    
    __tablename__ = 'products'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Required fields
    sku = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    base_price = Column(Numeric(10, 2), nullable=False)
    
    # Status fields
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Constraints
    __table_args__ = (
        CheckConstraint(text('base_price > 0'), name='check_product_base_price_positive'),
    )
    
    # Relationships
    price_history = relationship('ProductPrice', back_populates='product', cascade='all, delete-orphan')
    inventory_items = relationship('StoreInventory', back_populates='product')
    transaction_items = relationship('TransactionItem', back_populates='product')
    inventory_movements = relationship('InventoryMovement', back_populates='product')
    
    def __repr__(self) -> str:
        return f"<Product(id={self.id}, sku='{self.sku}', name='{self.name}')>"


class ProductPrice(Base):
    """
    Historical and current pricing records for products.
    Supports discount tracking and effective date ranges.
    """
    
    __tablename__ = 'product_prices'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id', ondelete='CASCADE'), 
                       nullable=False, index=True)
    
    # Required fields
    current_price = Column(Numeric(10, 2), nullable=False)
    effective_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Optional fields
    discount_percent = Column(Numeric(5, 2), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Constraints
    __table_args__ = (
        CheckConstraint(text('current_price > 0'), name='check_price_positive'),
        CheckConstraint(text('discount_percent >= 0 AND discount_percent <= 100'), 
                       name='check_discount_percent_range'),
        CheckConstraint(text('end_date IS NULL OR end_date > effective_date'), 
                       name='check_price_date_range'),
        Index('idx_product_price_effective', 'product_id', 'effective_date'),
    )
    
    # Relationships
    product = relationship('Product', back_populates='price_history')
    
    def __repr__(self) -> str:
        return f"<ProductPrice(id={self.id}, product_id={self.product_id}, price={self.current_price})>"


class Customer(Base):
    """
    Customer records supporting both registered and anonymous customers.
    
    Relationships:
        - account: One-to-one with CustomerAccount for registered users
        - transactions: Purchase history
    """
    
    __tablename__ = 'customers'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Optional fields (nullable for anonymous customers)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    
    # Status fields
    is_registered = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    account = relationship('CustomerAccount', back_populates='customer', uselist=False, 
                          cascade='all, delete-orphan')
    transactions = relationship('Transaction', back_populates='customer')
    
    def __repr__(self) -> str:
        name = f"{self.first_name} {self.last_name}" if self.first_name is not None else "Anonymous"
        return f"<Customer(id={self.id}, name='{name}', registered={self.is_registered})>"


class CustomerAccount(Base):
    """
    Authentication and contact information for registered customers.
    One-to-one relationship with Customer.
    """
    
    __tablename__ = 'customer_accounts'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id', ondelete='CASCADE'), 
                        unique=True, nullable=False)
    
    # Required fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Optional fields
    phone_number = Column(String(15), nullable=True)
    
    # Status fields
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Constraints
    __table_args__ = (
        CheckConstraint(text("email LIKE '%@%'"), name='check_email_format'),
    )
    
    # Relationships
    customer = relationship('Customer', back_populates='account')
    
    def __repr__(self) -> str:
        return f"<CustomerAccount(id={self.id}, email='{self.email}', active={self.is_active})>"


class Store(Base):
    """
    Physical store locations.
    
    Relationships:
        - inventory: Products stocked at this store
        - transactions: Sales processed at this store
        - employees: Staff assigned to this store
        - inventory_movements: Stock movements for this store
    """
    
    __tablename__ = 'stores'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Required fields
    name = Column(String(255), nullable=False)
    
    # Optional fields
    address = Column(String(500), nullable=True)
    
    # Status fields
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    inventory = relationship('StoreInventory', back_populates='store', cascade='all, delete-orphan')
    transactions = relationship('Transaction', back_populates='store')
    employees = relationship('Employee', back_populates='store')
    inventory_movements = relationship('InventoryMovement', back_populates='store')
    
    def __repr__(self) -> str:
        return f"<Store(id={self.id}, name='{self.name}', active={self.is_active})>"


class StoreInventory(Base):
    """
    Current inventory levels for products at each store.
    Tracks quantity, costs, and optional store-specific pricing.
    """
    
    __tablename__ = 'store_inventories'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id', ondelete='CASCADE'), 
                     nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id', ondelete='RESTRICT'), 
                       nullable=False, index=True)
    
    # Required fields
    quantity_balance = Column(Integer, nullable=False, default=0)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    total_cost = Column(Numeric(10, 2), nullable=False)
    
    # Optional fields
    current_price = Column(Numeric(10, 2), nullable=True)  # Store-specific price override
    
    # Timestamps
    last_updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                            onupdate=lambda: datetime.now(timezone.utc))
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('store_id', 'product_id', name='uq_store_product'),
        CheckConstraint(text('quantity_balance >= 0'), name='check_inventory_quantity_non_negative'),
        CheckConstraint(text('current_price IS NULL OR current_price > 0'), 
                       name='check_inventory_price_positive'),
        CheckConstraint(text('unit_cost > 0'), name='check_unit_cost_positive'),
        CheckConstraint(text('total_cost >= 0'), name='check_total_cost_non_negative'),
        Index('idx_store_inventory_product', 'product_id', 'store_id'),
    )
    
    # Relationships
    store = relationship('Store', back_populates='inventory')
    product = relationship('Product', back_populates='inventory_items')
    
    def __repr__(self) -> str:
        return f"<StoreInventory(store_id={self.store_id}, product_id={self.product_id}, quantity={self.quantity_balance})>"


class InventoryMovement(Base):
    """
    Audit trail for all inventory changes.
    Tracks purchases, sales, adjustments, returns, and transfers.
    """
    
    __tablename__ = 'inventory_movements'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id', ondelete='RESTRICT'), 
                     nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id', ondelete='RESTRICT'), 
                       nullable=False)
    
    # Required fields
    quantity_change = Column(Integer, nullable=False)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    movement_type = Column(String(50), nullable=False)
    
    # Optional fields
    reference_id = Column(UUID(as_uuid=True), nullable=True)  # Link to transaction_id if applicable
    notes = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Constraints
    __table_args__ = (
        CheckConstraint(text('quantity_change != 0'), name='check_quantity_change_not_zero'),
        CheckConstraint(text('unit_cost > 0'), name='check_movement_unit_cost_positive'),
        CheckConstraint(
            text("movement_type IN ('purchase', 'sale', 'adjustment', 'return', 'transfer')"),
            name='check_valid_movement_type'
        ),
        Index('idx_inventory_movement_store_product', 'store_id', 'product_id'),
        Index('idx_inventory_movement_created', 'created_at'),
        Index('idx_inventory_movement_reference', 'reference_id'),
    )
    
    # Relationships
    store = relationship('Store', back_populates='inventory_movements')
    product = relationship('Product', back_populates='inventory_movements')
    
    def __repr__(self) -> str:
        return f"<InventoryMovement(id={self.id}, type='{self.movement_type}', quantity={self.quantity_change})>"


class Employee(Base):
    """
    Employee records with store assignment and employment dates.
    
    Relationships:
        - store: Store where employee is assigned
        - transactions: Transactions processed by this employee
    """
    
    __tablename__ = 'employees'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Required fields
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    
    # Optional fields
    dob = Column(Date, nullable=True)
    hire_date = Column(Date, nullable=True)
    
    # Foreign keys
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id', ondelete='SET NULL'), 
                     nullable=True, index=True)
    
    # Status fields
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Constraints - using text() to avoid Pylance type checking issues
    __table_args__ = (
        CheckConstraint(
            text('hire_date IS NULL OR dob IS NULL OR hire_date >= dob'),
            name='check_hire_after_birth'
        ),
        CheckConstraint(
            text('dob IS NULL OR dob < CURRENT_DATE'),
            name='check_dob_in_past'
        ),
    )
    
    # Relationships
    store = relationship('Store', back_populates='employees')
    transactions = relationship('Transaction', back_populates='employee')
    
    def __repr__(self) -> str:
        return f"<Employee(id={self.id}, name='{self.first_name} {self.last_name}', active={self.is_active})>"


class Transaction(Base):
    """
    Sales transactions processed at stores.
    
    Relationships:
        - items: Line items (products and quantities)
        - customer: Customer who made the purchase (optional for anonymous)
        - store: Store where transaction occurred
        - employee: Employee who processed the transaction
    """
    
    __tablename__ = 'transactions'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id', ondelete='SET NULL'), 
                        nullable=True, index=True)  # Nullable for anonymous customers
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id', ondelete='RESTRICT'), 
                     nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id', ondelete='RESTRICT'), 
                        nullable=False, index=True)
    
    # Required fields
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), default='completed', nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Constraints
    __table_args__ = (
        CheckConstraint(text('total_amount >= 0'), name='check_total_amount_non_negative'),
        CheckConstraint(
            text("status IN ('pending', 'completed', 'refunded', 'cancelled')"),
            name='check_valid_status'
        ),
        Index('idx_transaction_store_date', 'store_id', 'created_at'),
        Index('idx_transaction_customer_date', 'customer_id', 'created_at'),
    )
    
    # Relationships
    items = relationship('TransactionItem', back_populates='transaction', cascade='all, delete-orphan')
    customer = relationship('Customer', back_populates='transactions')
    store = relationship('Store', back_populates='transactions')
    employee = relationship('Employee', back_populates='transactions')
    
    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, total={self.total_amount}, status='{self.status}')>"


class TransactionItem(Base):
    """
    Line items for transactions.
    Captures product, quantity, and price at time of sale.
    """
    
    __tablename__ = 'transaction_items'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    transaction_id = Column(UUID(as_uuid=True), ForeignKey('transactions.id', ondelete='CASCADE'), 
                           nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id', ondelete='RESTRICT'), 
                       nullable=False, index=True)
    
    # Required fields
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)  # Price at time of purchase
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Constraints
    __table_args__ = (
        CheckConstraint(text('quantity > 0'), name='check_transaction_item_quantity_positive'),
        CheckConstraint(text('price > 0'), name='check_transaction_item_price_positive'),
        Index('idx_transaction_item_product', 'product_id', 'transaction_id'),
    )
    
    # Relationships
    transaction = relationship('Transaction', back_populates='items')
    product = relationship('Product', back_populates='transaction_items')
    
    def __repr__(self) -> str:
        return f"<TransactionItem(id={self.id}, product_id={self.product_id}, quantity={self.quantity}, price={self.price})>"
