from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Numeric, CheckConstraint, Index, text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timezone
import uuid


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