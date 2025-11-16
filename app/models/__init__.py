# SQLAlchemy ORM Models
# Export all models
"""
SQLAlchemy ORM Models for Retail Management System (Type-Safe Version)

This module defines the database schema for a multi-store retail system including:
- Product catalog and pricing
- Inventory management across stores
- Transaction processing
- Customer accounts
- Employee management

All models use UUID primary keys and timezone-aware timestamps.
This version uses SQLAlchemy expression language for type-safe constraints.
"""
from app.database import Base
from app.models.product import Product, ProductPrice
from app.models.customer import Customer, CustomerAccount
from app.models.store import Store
from app.models.employee import Employee
from app.models.inventory import StoreInventory, InventoryMovement
from app.models.transaction import Transaction, TransactionItem

__all__ = [
    "Base",
    "Product",
    "ProductPrice",
    "Customer",
    "CustomerAccount",
    "Store",
    "Employee",
    "StoreInventory",
    "InventoryMovement",
    "Transaction",
    "TransactionItem",
]