from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timezone
from uuid import UUID
from decimal import Decimal
from app.models.product import Product, ProductPrice
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """Repository for Product operations"""

    def __init__(self):
        super().__init__(Product)

    def get_by_sku(self, db: Session, sku: str) -> Optional[Product]:
        """Get product by SKU"""
        return self.get_by(db, sku=sku)

    def search_by_name(
        self,
        db: Session,
        name: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """Search products by name (case-insensitive partial match)"""
        from sqlalchemy import select, func

        stmt = (
            select(self.model)
            .where(func.lower(self.model.name).contains(name.lower()))
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())


class ProductPriceRepository(BaseRepository[ProductPrice]):
    """Repository for ProductPrice operations"""

    def __init__(self):
        super().__init__(ProductPrice)

    def get_current_price(
        self,
        db: Session,
        product_id: UUID
    ) -> Optional[ProductPrice]:
        """Get current effective price for a product"""
        now = datetime.now(timezone.utc)
        from sqlalchemy import select

        stmt = (
            select(self.model)
            .where(
                and_(
                    self.model.product_id == product_id,
                    self.model.effective_date <= now,
                    (self.model.end_date.is_(None)) | (self.model.end_date > now)
                )
            )
            .order_by(self.model.effective_date.desc())
        )
        return db.scalars(stmt).first()

    def get_price_history(
        self,
        db: Session,
        product_id: UUID
    ) -> List[ProductPrice]:
        """Get all price history for a product"""
        return self.get_multi_by(
            db,
            product_id=product_id,
            order_by="-effective_date"
        )


product = ProductRepository()
product_price = ProductPriceRepository()