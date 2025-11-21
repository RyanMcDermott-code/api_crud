from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from app.models.transaction import Transaction, TransactionItem
from app.repositories.transaction_repository import transaction, transaction_item
from app.repositories.customer_repository import customer
from app.repositories.store_repository import store
from app.repositories.employee_repository import employee
from app.repositories.product_repository import product, product_price
from app.services.inventory_service import inventory_service
from app.core.exceptions import (
    TransactionNotFoundError,
    CustomerNotFoundError,
    StoreNotFoundError,
    EmployeeNotFoundError,
    ProductNotFoundError,
    InsufficientStockError,
    InvalidTransactionError
)


class TransactionService:
    """Business logic for transaction management"""

    def create_transaction(
        self,
        db: Session,
        store_id: UUID,
        employee_id: UUID,
        items: List[Dict],
        customer_id: Optional[UUID] = None
    ) -> Transaction:
        """
        Create a new transaction with items.

        Args:
            db: Database session
            store_id: Store where transaction occurs
            employee_id: Employee processing the transaction
            items: List of dicts with keys: product_id, quantity, price (optional)
            customer_id: Optional customer ID (None for anonymous)

        Returns:
            Created Transaction instance

        Raises:
            StoreNotFoundError: If store doesn't exist
            EmployeeNotFoundError: If employee doesn't exist
            CustomerNotFoundError: If customer_id provided but doesn't exist
            ProductNotFoundError: If any product doesn't exist
            InsufficientStockError: If not enough stock for any item
            InvalidTransactionError: If transaction data is invalid
        """
        # Validate store, employee, customer
        if not store.get(db, store_id):
            raise StoreNotFoundError(f"Store {store_id} not found")

        if not employee.get(db, employee_id):
            raise EmployeeNotFoundError(f"Employee {employee_id} not found")

        if customer_id and not customer.get(db, customer_id):
            raise CustomerNotFoundError(f"Customer {customer_id} not found")

        if not items or len(items) == 0:
            raise InvalidTransactionError("Transaction must have at least one item")

        # Validate all items and calculate total
        total_amount = Decimal("0")
        validated_items = []

        for item in items:
            product_id = item.get("product_id")
            quantity = item.get("quantity")
            item_price = item.get("price")

            if not product_id or not quantity:
                raise InvalidTransactionError("Each item must have product_id and quantity")

            if quantity <= 0:
                raise InvalidTransactionError("Item quantity must be greater than 0")

            # Validate product exists
            prod = product.get(db, product_id)
            if not prod:
                raise ProductNotFoundError(f"Product {product_id} not found")

            # Get current price if not provided
            if item_price is None:
                current_price = product_price.get_current_price(db, product_id)
                if not current_price:
                    raise InvalidTransactionError(f"No price found for product {product_id}")
                item_price = current_price.current_price
            else:
                item_price = Decimal(str(item_price))

            # Check inventory availability
            inventory_record = inventory_service.get_inventory(db, store_id, product_id)
            if not inventory_record:
                raise InsufficientStockError(
                    f"Product {product_id} not available at store {store_id}"
                )
            if inventory_record.quantity_balance < quantity:
                raise InsufficientStockError(
                    f"Insufficient stock for product {product_id}. "
                    f"Available: {inventory_record.quantity_balance}, Requested: {quantity}"
                )

            validated_items.append({
                "product_id": product_id,
                "quantity": quantity,
                "price": item_price
            })
            total_amount += item_price * Decimal(quantity)

        # Create transaction
        transaction_data = {
            "customer_id": customer_id,
            "store_id": store_id,
            "employee_id": employee_id,
            "total_amount": total_amount,
            "status": "pending"
        }
        new_transaction = transaction.create(db, obj_in=transaction_data)

        # Create transaction items
        for item in validated_items:
            item_data = {
                "transaction_id": new_transaction.id,
                "product_id": item["product_id"],
                "quantity": item["quantity"],
                "price": item["price"]
            }
            transaction_item.create(db, obj_in=item_data)

        return new_transaction

    def complete_transaction(
        self,
        db: Session,
        transaction_id: UUID
    ) -> Transaction:
        """
        Complete a pending transaction.
        Updates inventory for all items in the transaction.

        Raises:
            TransactionNotFoundError: If transaction doesn't exist
            InvalidTransactionError: If transaction is not pending
            InsufficientStockError: If inventory check fails
        """
        trans = transaction.get(db, transaction_id)
        if not trans:
            raise TransactionNotFoundError(f"Transaction {transaction_id} not found")

        if trans.status != "pending":
            raise InvalidTransactionError(
                f"Cannot complete transaction with status '{trans.status}'"
            )

        # Update inventory for each item
        items = transaction_item.get_by_transaction(db, transaction_id)
        for item in items:
            inventory_service.record_sale(
                db,
                trans.store_id,
                item.product_id,
                item.quantity,
                transaction_id=transaction_id,
                notes=f"Sale from transaction {transaction_id}"
            )

        # Update transaction status
        updated_trans = transaction.update(
            db,
            db_obj=trans,
            obj_in={"status": "completed"}
        )

        return updated_trans

    def cancel_transaction(
        self,
        db: Session,
        transaction_id: UUID,
        reason: Optional[str] = None
    ) -> Transaction:
        """
        Cancel a transaction.
        If transaction was completed, inventory is NOT automatically restored.
        Use refund_transaction for that.

        Raises:
            TransactionNotFoundError: If transaction doesn't exist
            InvalidTransactionError: If transaction is already cancelled or refunded
        """
        trans = transaction.get(db, transaction_id)
        if not trans:
            raise TransactionNotFoundError(f"Transaction {transaction_id} not found")

        if trans.status in ["cancelled", "refunded"]:
            raise InvalidTransactionError(
                f"Cannot cancel transaction with status '{trans.status}'"
            )

        updated_trans = transaction.update(
            db,
            db_obj=trans,
            obj_in={"status": "cancelled"}
        )

        return updated_trans

    def refund_transaction(
        self,
        db: Session,
        transaction_id: UUID,
        restore_inventory: bool = True
    ) -> Transaction:
        """
        Refund a completed transaction.
        Optionally restores inventory.

        Raises:
            TransactionNotFoundError: If transaction doesn't exist
            InvalidTransactionError: If transaction is not completed
        """
        trans = transaction.get(db, transaction_id)
        if not trans:
            raise TransactionNotFoundError(f"Transaction {transaction_id} not found")

        if trans.status != "completed":
            raise InvalidTransactionError(
                f"Can only refund completed transactions. Current status: '{trans.status}'"
            )

        # Restore inventory if requested
        if restore_inventory:
            items = transaction_item.get_by_transaction(db, transaction_id)
            for item in items:
                inventory_service.record_return(
                    db,
                    trans.store_id,
                    item.product_id,
                    item.quantity,
                    transaction_id=transaction_id,
                    notes=f"Refund for transaction {transaction_id}"
                )

        # Update transaction status
        updated_trans = transaction.update(
            db,
            db_obj=trans,
            obj_in={"status": "refunded"}
        )

        return updated_trans

    def get_transaction(
        self,
        db: Session,
        transaction_id: UUID
    ) -> Optional[Transaction]:
        """Get transaction by ID"""
        return transaction.get(db, transaction_id)

    def get_transaction_items(
        self,
        db: Session,
        transaction_id: UUID
    ) -> List[TransactionItem]:
        """Get all items for a transaction"""
        return transaction_item.get_by_transaction(db, transaction_id)

    def list_transactions(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        """List all transactions with pagination"""
        return transaction.get_multi(db, skip=skip, limit=limit, order_by="-created_at")

    def get_transactions_by_store(
        self,
        db: Session,
        store_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        """Get all transactions for a store"""
        return transaction.get_by_store(db, store_id, skip=skip, limit=limit)

    def get_transactions_by_customer(
        self,
        db: Session,
        customer_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        """Get all transactions for a customer"""
        return transaction.get_by_customer(db, customer_id, skip=skip, limit=limit)

    def get_transactions_by_employee(
        self,
        db: Session,
        employee_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        """Get all transactions processed by an employee"""
        return transaction.get_by_employee(db, employee_id, skip=skip, limit=limit)

    def get_transactions_by_status(
        self,
        db: Session,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        """Get transactions by status"""
        valid_statuses = ["pending", "completed", "refunded", "cancelled"]
        if status not in valid_statuses:
            raise InvalidTransactionError(
                f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}"
            )
        return transaction.get_by_status(db, status, skip=skip, limit=limit)

    def get_transactions_by_date_range(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        store_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        """Get transactions within a date range"""
        return transaction.get_by_date_range(
            db,
            start_date,
            end_date,
            store_id=store_id,
            skip=skip,
            limit=limit
        )

    def get_total_sales(
        self,
        db: Session,
        store_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Decimal:
        """
        Get total sales amount with optional filters.
        Only includes completed transactions.
        """
        return transaction.get_total_sales(
            db,
            store_id=store_id,
            start_date=start_date,
            end_date=end_date
        )

    def get_sales_statistics(
        self,
        db: Session,
        store_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Get sales statistics with optional filters.

        Returns:
            Dict with keys: total_sales, transaction_count, average_sale
        """
        total_sales = transaction.get_total_sales(
            db,
            store_id=store_id,
            start_date=start_date,
            end_date=end_date
        )

        count = transaction.count_by_status(db, "completed", store_id=store_id)

        average_sale = total_sales / Decimal(count) if count > 0 else Decimal("0")

        return {
            "total_sales": total_sales,
            "transaction_count": count,
            "average_sale": average_sale
        }

    def get_product_sales_report(
        self,
        db: Session,
        product_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Get sales report for a specific product.

        Returns:
            Dict with keys: total_quantity_sold, total_revenue
        """
        total_quantity = transaction_item.get_total_quantity_sold(
            db,
            product_id,
            start_date=start_date,
            end_date=end_date
        )

        total_revenue = transaction_item.get_total_revenue_for_product(
            db,
            product_id,
            start_date=start_date,
            end_date=end_date
        )

        return {
            "product_id": product_id,
            "total_quantity_sold": total_quantity,
            "total_revenue": total_revenue
        }


transaction_service = TransactionService()
