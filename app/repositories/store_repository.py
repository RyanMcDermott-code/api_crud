from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from uuid import UUID
from app.repositories.base import BaseRepository
from app.models.store import Store
from app.models.inventory import StoreInventory


class StoreRepository(BaseRepository[Store]):
    """Repository for Store operations"""

    def __init__(self):
        super().__init__(Store)

    def search_by_name(
        self,
        db: Session,
        name: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Store]:
        """Search stores by name (case-insensitive partial match)"""
        stmt = (
            select(self.model)
            .where(func.lower(self.model.name).contains(name.lower()))
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def get_stores_with_product(
        self,
        db: Session,
        product_id: UUID,
        *,
        min_quantity: int = 1
    ) -> List[Store]:
        """Get stores that have a specific product in stock"""
        stmt = (
            select(self.model)
            .join(StoreInventory)
            .where(
                StoreInventory.product_id == product_id,
                StoreInventory.quantity_balance >= min_quantity,
                self.model.is_active == True
            )
        )
        return list(db.scalars(stmt).all())

    def get_by_address(
        self,
        db: Session,
        address: str
    ) -> List[Store]:
        """Search stores by address (case-insensitive partial match)"""
        stmt = (
            select(self.model)
            .where(
                self.model.address.isnot(None),
                func.lower(self.model.address).contains(address.lower())
            )
        )
        return list(db.scalars(stmt).all())


store = StoreRepository()
