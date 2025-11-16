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
