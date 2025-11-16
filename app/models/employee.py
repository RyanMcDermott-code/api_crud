from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Date, Boolean, CheckConstraint, text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timezone
import uuid


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