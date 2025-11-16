from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Numeric,
    CheckConstraint, Index, text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timezone
import uuid


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
