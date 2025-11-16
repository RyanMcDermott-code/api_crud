from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Numeric, Boolean,
    CheckConstraint, Index, text
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