from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Numeric, Boolean,
    UniqueConstraint, CheckConstraint, Index, text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timezone
import uuid

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
