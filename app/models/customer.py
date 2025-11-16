from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Numeric, Date, Boolean,
    UniqueConstraint, CheckConstraint, Index, text, and_, or_
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timezone
import uuid


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