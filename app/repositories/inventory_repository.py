from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from datetime import datetime
from uuid import UUID
from app.repositories.base import BaseRepository
from app.models.inventory import InventoryMovement, StoreInventory


class InventoryMovementRepository(BaseRepository[InventoryMovement]):
    """Repository for InventoryMovement operations"""

    def __init__(self):
        super().__init__(InventoryMovement)

    def get_by_store(
        self,
        db: Session,
        store_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[InventoryMovement]:
        """Get all inventory movements for a store"""
        return self.get_multi_by(
            db,
            skip=skip,
            limit=limit,
            order_by="-created_at",
            store_id=store_id
        )

    def get_by_product(
        self,
        db: Session,
        product_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[InventoryMovement]:
        """Get all inventory movements for a product"""
        return self.get_multi_by(
            db,
            skip=skip,
            limit=limit,
            order_by="-created_at",
            product_id=product_id
        )

    def get_by_store_and_product(
        self,
        db: Session,
        store_id: UUID,
        product_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[InventoryMovement]:
        """Get inventory movements for a specific product at a specific store"""
        return self.get_multi_by(
            db,
            skip=skip,
            limit=limit,
            order_by="-created_at",
            store_id=store_id,
            product_id=product_id
        )

    def get_by_type(
        self,
        db: Session,
        movement_type: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[InventoryMovement]:
        """Get inventory movements by type (purchase, sale, adjustment, return, transfer)"""
        return self.get_multi_by(
            db,
            skip=skip,
            limit=limit,
            order_by="-created_at",
            movement_type=movement_type
        )

    def get_by_reference(
        self,
        db: Session,
        reference_id: UUID
    ) -> List[InventoryMovement]:
        """Get inventory movements linked to a specific reference (e.g., transaction)"""
        return self.get_multi_by(db, reference_id=reference_id)

    def get_by_date_range(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        *,
        store_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[InventoryMovement]:
        """Get inventory movements within a date range"""
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


class StoreInventoryRepository(BaseRepository[StoreInventory]):
    """Repository for StoreInventory operations"""

    def __init__(self):
        super().__init__(StoreInventory)

    def get_by_store_and_product(
        self,
        db: Session,
        store_id: UUID,
        product_id: UUID
    ) -> Optional[StoreInventory]:
        """Get inventory record for a specific product at a specific store"""
        return self.get_by(db, store_id=store_id, product_id=product_id)

    def get_by_store(
        self,
        db: Session,
        store_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[StoreInventory]:
        """Get all inventory for a store"""
        return self.get_multi_by(
            db,
            skip=skip,
            limit=limit,
            order_by="-last_updated_at",
            store_id=store_id
        )

    def get_by_product(
        self,
        db: Session,
        product_id: UUID
    ) -> List[StoreInventory]:
        """Get inventory for a product across all stores"""
        return self.get_multi_by(db, product_id=product_id)

    def get_low_stock(
        self,
        db: Session,
        threshold: int = 10,
        *,
        store_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[StoreInventory]:
        """Get inventory items below a quantity threshold"""
        stmt = select(self.model).where(self.model.quantity_balance <= threshold)

        if store_id:
            stmt = stmt.where(self.model.store_id == store_id)

        stmt = stmt.order_by(self.model.quantity_balance).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def get_out_of_stock(
        self,
        db: Session,
        *,
        store_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[StoreInventory]:
        """Get inventory items with zero quantity"""
        return self.get_low_stock(db, threshold=0, store_id=store_id, skip=skip, limit=limit)

    def get_total_quantity_for_product(
        self,
        db: Session,
        product_id: UUID
    ) -> int:
        """Get total quantity of a product across all stores"""
        from sqlalchemy import func
        stmt = (
            select(func.coalesce(func.sum(self.model.quantity_balance), 0))
            .where(self.model.product_id == product_id)
        )
        result = db.scalar(stmt)
        return int(result) if result else 0


inventory_movement = InventoryMovementRepository()
store_inventory = StoreInventoryRepository()
