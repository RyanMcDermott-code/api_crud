from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from app.repositories.base import BaseRepository
from app.models.transaction import Transaction, TransactionItem


class TransactionRepository(BaseRepository[Transaction]):
    """Repository for Transaction operations"""

    def __init__(self):
        super().__init__(Transaction)

    def get_by_store(
        self,
        db: Session,
        store_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        """Get all transactions for a store"""
        return self.get_multi_by(
            db,
            skip=skip,
            limit=limit,
            order_by="-created_at",
            store_id=store_id
        )

    def get_by_customer(
        self,
        db: Session,
        customer_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        """Get all transactions for a customer"""
        return self.get_multi_by(
            db,
            skip=skip,
            limit=limit,
            order_by="-created_at",
            customer_id=customer_id
        )

    def get_by_employee(
        self,
        db: Session,
        employee_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        """Get all transactions processed by an employee"""
        return self.get_multi_by(
            db,
            skip=skip,
            limit=limit,
            order_by="-created_at",
            employee_id=employee_id
        )

    def get_by_status(
        self,
        db: Session,
        status: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        """Get transactions by status (pending, completed, refunded, cancelled)"""
        return self.get_multi_by(
            db,
            skip=skip,
            limit=limit,
            order_by="-created_at",
            status=status
        )

    def get_by_date_range(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        *,
        store_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        """Get transactions within a date range"""
        stmt = (
            select(self.model)
            .where(
                self.model.created_at >= start_date,
                self.model.created_at <= end_date
            )
        )
        if store_id:
            stmt = stmt.where(self.model.store_id == store_id)

        stmt = stmt.order_by(self.model.created_at.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def get_total_sales(
        self,
        db: Session,
        *,
        store_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Decimal:
        """Get total sales amount with optional filters"""
        stmt = (
            select(func.coalesce(func.sum(self.model.total_amount), 0))
            .where(self.model.status == 'completed')
        )

        if store_id:
            stmt = stmt.where(self.model.store_id == store_id)
        if start_date:
            stmt = stmt.where(self.model.created_at >= start_date)
        if end_date:
            stmt = stmt.where(self.model.created_at <= end_date)

        result = db.scalar(stmt)
        return Decimal(str(result)) if result else Decimal('0')

    def count_by_status(
        self,
        db: Session,
        status: str,
        *,
        store_id: Optional[UUID] = None
    ) -> int:
        """Count transactions by status"""
        if store_id:
            return self.count(db, status=status, store_id=store_id)
        return self.count(db, status=status)


class TransactionItemRepository(BaseRepository[TransactionItem]):
    """Repository for TransactionItem operations"""

    def __init__(self):
        super().__init__(TransactionItem)

    def get_by_transaction(
        self,
        db: Session,
        transaction_id: UUID
    ) -> List[TransactionItem]:
        """Get all items for a transaction"""
        return self.get_multi_by(db, transaction_id=transaction_id)

    def get_by_product(
        self,
        db: Session,
        product_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransactionItem]:
        """Get all transaction items for a product (sales history)"""
        return self.get_multi_by(
            db,
            skip=skip,
            limit=limit,
            order_by="-created_at",
            product_id=product_id
        )

    def get_total_quantity_sold(
        self,
        db: Session,
        product_id: UUID,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Get total quantity sold for a product"""
        stmt = (
            select(func.coalesce(func.sum(self.model.quantity), 0))
            .where(self.model.product_id == product_id)
        )

        if start_date or end_date:
            stmt = stmt.join(Transaction)
            stmt = stmt.where(Transaction.status == 'completed')
            if start_date:
                stmt = stmt.where(Transaction.created_at >= start_date)
            if end_date:
                stmt = stmt.where(Transaction.created_at <= end_date)

        result = db.scalar(stmt)
        return int(result) if result else 0

    def get_total_revenue_for_product(
        self,
        db: Session,
        product_id: UUID,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Decimal:
        """Get total revenue for a specific product"""
        stmt = (
            select(func.coalesce(func.sum(self.model.quantity * self.model.price), 0))
            .where(self.model.product_id == product_id)
        )

        if start_date or end_date:
            stmt = stmt.join(Transaction)
            stmt = stmt.where(Transaction.status == 'completed')
            if start_date:
                stmt = stmt.where(Transaction.created_at >= start_date)
            if end_date:
                stmt = stmt.where(Transaction.created_at <= end_date)

        result = db.scalar(stmt)
        return Decimal(str(result)) if result else Decimal('0')


transaction = TransactionRepository()
transaction_item = TransactionItemRepository()
