from typing import Optional, List
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.store import Store
from app.repositories.store_repository import store
from app.core.exceptions import StoreNotFoundError


class StoreService:
    """Business logic for store management"""

    def create_store(
        self,
        db: Session,
        name: str,
        address: Optional[str] = None
    ) -> Store:
        """
        Create a new store.

        Args:
            db: Database session
            name: Store name
            address: Optional store address

        Returns:
            Created Store instance
        """
        store_data = {
            "name": name,
            "address": address,
            "is_active": True
        }
        return store.create(db, obj_in=store_data)

    def get_store(
        self,
        db: Session,
        store_id: UUID
    ) -> Optional[Store]:
        """Get store by ID"""
        return store.get(db, store_id)

    def list_stores(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Store]:
        """List all stores with pagination"""
        if active_only:
            return store.get_multi_active(db, skip=skip, limit=limit)
        return store.get_multi(db, skip=skip, limit=limit)

    def search_by_name(
        self,
        db: Session,
        name: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Store]:
        """Search stores by name (case-insensitive partial match)"""
        return store.search_by_name(db, name, skip=skip, limit=limit)

    def search_by_address(
        self,
        db: Session,
        address: str
    ) -> List[Store]:
        """Search stores by address (case-insensitive partial match)"""
        return store.get_by_address(db, address)

    def get_stores_with_product(
        self,
        db: Session,
        product_id: UUID,
        min_quantity: int = 1
    ) -> List[Store]:
        """
        Get all stores that have a specific product in stock.

        Args:
            db: Database session
            product_id: Product UUID
            min_quantity: Minimum quantity threshold (default 1)

        Returns:
            List of stores with the product in stock
        """
        return store.get_stores_with_product(db, product_id, min_quantity=min_quantity)

    def update_store(
        self,
        db: Session,
        store_id: UUID,
        **update_data
    ) -> Store:
        """
        Update store information.

        Raises:
            StoreNotFoundError: If store doesn't exist
        """
        existing = store.get(db, store_id)
        if not existing:
            raise StoreNotFoundError(f"Store {store_id} not found")

        return store.update(db, db_obj=existing, obj_in=update_data)

    def deactivate_store(
        self,
        db: Session,
        store_id: UUID
    ) -> Store:
        """
        Deactivate a store (soft delete).
        Store data is preserved for transaction history.
        Note: Consider impact on employee assignments and inventory.
        """
        existing = store.soft_delete(db, id=store_id)
        if not existing:
            raise StoreNotFoundError(f"Store {store_id} not found")
        return existing

    def reactivate_store(
        self,
        db: Session,
        store_id: UUID
    ) -> Store:
        """Reactivate a deactivated store"""
        existing = store.restore(db, id=store_id)
        if not existing:
            raise StoreNotFoundError(f"Store {store_id} not found")
        return existing


store_service = StoreService()
