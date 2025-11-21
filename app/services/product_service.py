from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal

from app.models.product import Product, ProductPrice
from app.repositories.product_repository import product, product_price
from app.core.exceptions import (
    DuplicateSKUError,
    ProductNotFoundError,
    InvalidPriceError
)


class ProductService:
    """Business logic for product management"""

    def create_product(
        self,
        db: Session,
        sku: str,
        name: str,
        base_price: Decimal,
        current_price: Optional[Decimal] = None,
        discount_percent: Optional[Decimal] = None
    ) -> Product:
        """
        Create a new product with initial pricing.

        Args:
            db: Database session
            sku: Unique product SKU
            name: Product name
            base_price: Base price (must be positive)
            current_price: Optional current price (defaults to base_price)
            discount_percent: Optional discount percentage (0-100)

        Returns:
            Created Product instance

        Raises:
            DuplicateSKUError: If SKU already exists
            InvalidPriceError: If price is invalid
        """
        if base_price <= 0:
            raise InvalidPriceError("Base price must be greater than 0")

        # Check for duplicate SKU
        if product.get_by_sku(db, sku):
            raise DuplicateSKUError(f"SKU {sku} already exists")

        try:
            # Create product
            product_data = {
                "sku": sku,
                "name": name,
                "base_price": base_price,
                "is_active": True
            }
            new_product = product.create(db, obj_in=product_data)

            # Create initial price record
            effective_price = current_price if current_price is not None else base_price
            if effective_price <= 0:
                raise InvalidPriceError("Current price must be greater than 0")

            if discount_percent is not None and (discount_percent < 0 or discount_percent > 100):
                raise InvalidPriceError("Discount percent must be between 0 and 100")

            price_data = {
                "product_id": new_product.id,
                "current_price": effective_price,
                "discount_percent": discount_percent,
                "effective_date": datetime.now(timezone.utc)
            }
            product_price.create(db, obj_in=price_data)

            return new_product

        except IntegrityError:
            db.rollback()
            raise DuplicateSKUError(f"SKU {sku} already exists")

    def get_product(
        self,
        db: Session,
        product_id: UUID
    ) -> Optional[Product]:
        """Get product by ID"""
        return product.get(db, product_id)

    def get_product_by_sku(
        self,
        db: Session,
        sku: str
    ) -> Optional[Product]:
        """Get product by SKU"""
        return product.get_by_sku(db, sku)

    def search_products(
        self,
        db: Session,
        name: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """Search products by name (case-insensitive partial match)"""
        return product.search_by_name(db, name, skip=skip, limit=limit)

    def list_products(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Product]:
        """List all products with pagination"""
        if active_only:
            return product.get_multi_active(db, skip=skip, limit=limit)
        return product.get_multi(db, skip=skip, limit=limit)

    def update_product(
        self,
        db: Session,
        product_id: UUID,
        **update_data
    ) -> Product:
        """
        Update product information.

        Raises:
            ProductNotFoundError: If product doesn't exist
            InvalidPriceError: If base_price is invalid
        """
        existing = product.get(db, product_id)
        if not existing:
            raise ProductNotFoundError(f"Product {product_id} not found")

        # Validate base_price if being updated
        if "base_price" in update_data:
            if update_data["base_price"] <= 0:
                raise InvalidPriceError("Base price must be greater than 0")

        return product.update(db, db_obj=existing, obj_in=update_data)

    def deactivate_product(
        self,
        db: Session,
        product_id: UUID
    ) -> Product:
        """
        Deactivate a product (soft delete).
        Product data is preserved for transaction history.
        """
        existing = product.soft_delete(db, id=product_id)
        if not existing:
            raise ProductNotFoundError(f"Product {product_id} not found")
        return existing

    def reactivate_product(
        self,
        db: Session,
        product_id: UUID
    ) -> Product:
        """Reactivate a deactivated product"""
        existing = product.restore(db, id=product_id)
        if not existing:
            raise ProductNotFoundError(f"Product {product_id} not found")
        return existing

    def get_current_price(
        self,
        db: Session,
        product_id: UUID
    ) -> Optional[ProductPrice]:
        """Get the current effective price for a product"""
        return product_price.get_current_price(db, product_id)

    def update_price(
        self,
        db: Session,
        product_id: UUID,
        new_price: Decimal,
        discount_percent: Optional[Decimal] = None,
        effective_date: Optional[datetime] = None,
        end_current_price: bool = True
    ) -> ProductPrice:
        """
        Update product price by creating a new price record.

        Args:
            db: Database session
            product_id: Product UUID
            new_price: New price (must be positive)
            discount_percent: Optional discount percentage
            effective_date: When the new price takes effect (defaults to now)
            end_current_price: Whether to end the current price record

        Returns:
            New ProductPrice instance

        Raises:
            ProductNotFoundError: If product doesn't exist
            InvalidPriceError: If price is invalid
        """
        # Verify product exists
        prod = product.get(db, product_id)
        if not prod:
            raise ProductNotFoundError(f"Product {product_id} not found")

        if new_price <= 0:
            raise InvalidPriceError("Price must be greater than 0")

        if discount_percent is not None and (discount_percent < 0 or discount_percent > 100):
            raise InvalidPriceError("Discount percent must be between 0 and 100")

        # End current price if requested
        if end_current_price:
            current = product_price.get_current_price(db, product_id)
            if current:
                end_date = effective_date or datetime.now(timezone.utc)
                product_price.update(db, db_obj=current, obj_in={"end_date": end_date})

        # Create new price record
        price_data = {
            "product_id": product_id,
            "current_price": new_price,
            "discount_percent": discount_percent,
            "effective_date": effective_date or datetime.now(timezone.utc)
        }
        return product_price.create(db, obj_in=price_data)

    def get_price_history(
        self,
        db: Session,
        product_id: UUID
    ) -> List[ProductPrice]:
        """Get all price history for a product"""
        return product_price.get_price_history(db, product_id)

    def apply_discount(
        self,
        db: Session,
        product_id: UUID,
        discount_percent: Decimal,
        effective_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ProductPrice:
        """
        Apply a temporary discount to a product.

        Args:
            db: Database session
            product_id: Product UUID
            discount_percent: Discount percentage (0-100)
            effective_date: When discount starts (defaults to now)
            end_date: When discount ends (optional)

        Returns:
            New ProductPrice instance with discount

        Raises:
            ProductNotFoundError: If product doesn't exist
            InvalidPriceError: If discount is invalid
        """
        # Get product and current price
        prod = product.get(db, product_id)
        if not prod:
            raise ProductNotFoundError(f"Product {product_id} not found")

        if discount_percent < 0 or discount_percent > 100:
            raise InvalidPriceError("Discount percent must be between 0 and 100")

        current = product_price.get_current_price(db, product_id)
        if not current:
            raise InvalidPriceError(f"No current price found for product {product_id}")

        # Calculate discounted price
        discounted_price = current.current_price * (Decimal("1") - discount_percent / Decimal("100"))

        # Create new price record with discount
        price_data = {
            "product_id": product_id,
            "current_price": discounted_price,
            "discount_percent": discount_percent,
            "effective_date": effective_date or datetime.now(timezone.utc),
            "end_date": end_date
        }
        return product_price.create(db, obj_in=price_data)

    def remove_discount(
        self,
        db: Session,
        product_id: UUID
    ) -> ProductPrice:
        """
        Remove current discount and revert to base price.

        Raises:
            ProductNotFoundError: If product doesn't exist
        """
        prod = product.get(db, product_id)
        if not prod:
            raise ProductNotFoundError(f"Product {product_id} not found")

        # End current discounted price
        current = product_price.get_current_price(db, product_id)
        if current:
            product_price.update(db, db_obj=current, obj_in={"end_date": datetime.now(timezone.utc)})

        # Create new price record at base price
        price_data = {
            "product_id": product_id,
            "current_price": prod.base_price,
            "discount_percent": None,
            "effective_date": datetime.now(timezone.utc)
        }
        return product_price.create(db, obj_in=price_data)


product_service = ProductService()
