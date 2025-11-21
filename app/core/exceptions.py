"""
Custom exceptions for the application.
"""


class AppException(Exception):
    """Base exception for all application exceptions"""
    pass


# Customer exceptions
class CustomerNotFoundError(AppException):
    """Raised when a customer is not found"""
    pass


class DuplicateEmailError(AppException):
    """Raised when attempting to register with an existing email"""
    pass


class InvalidCredentialsError(AppException):
    """Raised when authentication fails"""
    pass


# Product exceptions
class ProductNotFoundError(AppException):
    """Raised when a product is not found"""
    pass


class DuplicateSKUError(AppException):
    """Raised when attempting to create a product with an existing SKU"""
    pass


class InvalidPriceError(AppException):
    """Raised when a price is invalid"""
    pass


# Employee exceptions
class EmployeeNotFoundError(AppException):
    """Raised when an employee is not found"""
    pass


class InvalidDateError(AppException):
    """Raised when a date is invalid"""
    pass


# Store exceptions
class StoreNotFoundError(AppException):
    """Raised when a store is not found"""
    pass


# Inventory exceptions
class InventoryNotFoundError(AppException):
    """Raised when inventory is not found"""
    pass


class InsufficientStockError(AppException):
    """Raised when there is not enough stock for an operation"""
    pass


class InvalidQuantityError(AppException):
    """Raised when a quantity is invalid"""
    pass


# Transaction exceptions
class TransactionNotFoundError(AppException):
    """Raised when a transaction is not found"""
    pass


class InvalidTransactionError(AppException):
    """Raised when a transaction is invalid"""
    pass
