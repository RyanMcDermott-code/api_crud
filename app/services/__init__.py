"""
Business Logic Layer (BLL)

This module exports all service classes that contain business logic
for the application. Services encapsulate complex business rules,
coordinate between repositories, and ensure data consistency.
"""

from app.services.customer_service import customer_service, CustomerService
from app.services.product_service import product_service, ProductService
from app.services.employee_service import employee_service, EmployeeService
from app.services.store_service import store_service, StoreService
from app.services.inventory_service import inventory_service, InventoryService
from app.services.transaction_service import transaction_service, TransactionService

__all__ = [
    # Service instances (ready to use)
    "customer_service",
    "product_service",
    "employee_service",
    "store_service",
    "inventory_service",
    "transaction_service",

    # Service classes (for type hints or custom instantiation)
    "CustomerService",
    "ProductService",
    "EmployeeService",
    "StoreService",
    "InventoryService",
    "TransactionService",
]
