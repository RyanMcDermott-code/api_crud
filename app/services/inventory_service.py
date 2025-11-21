from typing import Optional, List
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from app.models.inventory import InventoryMovement, StoreInventory
from app.repositories.inventory_repository import inventory_movement, store_inventory
from app.repositories.product_repository import product
from app.repositories.store_repository import store
from app.core.exceptions import (
    InventoryNotFoundError,
    InsufficientStockError,
    ProductNotFoundError,
    StoreNotFoundError,
    InvalidQuantityError
)


class InventoryService:
    """Business logic for inventory management"""

    def initialize_inventory(
        self,
        db: Session,
        store_id: UUID,
        product_id: UUID,
        quantity: int,
        unit_cost: Decimal
    ) -> StoreInventory:
        """
        Initialize inventory for a product at a store.

        Args:
            db: Database session
            store_id: Store UUID
            product_id: Product UUID
            quantity: Initial quantity
            unit_cost: Cost per unit

        Returns:
            Created StoreInventory instance

        Raises:
            StoreNotFoundError: If store doesn't exist
            ProductNotFoundError: If product doesn't exist
            InvalidQuantityError: If quantity or cost is invalid
        """
        # Validate store and product exist
        if not store.get(db, store_id):
            raise StoreNotFoundError(f"Store {store_id} not found")

        if not product.get(db, product_id):
            raise ProductNotFoundError(f"Product {product_id} not found")

        if quantity < 0:
            raise InvalidQuantityError("Quantity cannot be negative")

        if unit_cost <= 0:
            raise InvalidQuantityError("Unit cost must be greater than 0")

        # Check if inventory already exists
        existing = store_inventory.get_by_store_and_product(db, store_id, product_id)
        if existing:
            raise ValueError(f"Inventory already exists for product {product_id} at store {store_id}")

        # Create inventory record
        total_cost = Decimal(quantity) * unit_cost
        inventory_data = {
            "store_id": store_id,
            "product_id": product_id,
            "quantity_balance": quantity,
            "unit_cost": unit_cost,
            "total_cost": total_cost
        }
        inventory_record = store_inventory.create(db, obj_in=inventory_data)

        # Create initial movement record if quantity > 0
        if quantity > 0:
            movement_data = {
                "store_id": store_id,
                "product_id": product_id,
                "quantity_change": quantity,
                "unit_cost": unit_cost,
                "movement_type": "purchase",
                "notes": "Initial inventory"
            }
            inventory_movement.create(db, obj_in=movement_data)

        return inventory_record

    def record_purchase(
        self,
        db: Session,
        store_id: UUID,
        product_id: UUID,
        quantity: int,
        unit_cost: Decimal,
        notes: Optional[str] = None
    ) -> StoreInventory:
        """
        Record a product purchase (adds to inventory).

        Raises:
            StoreNotFoundError: If store doesn't exist
            ProductNotFoundError: If product doesn't exist
            InvalidQuantityError: If quantity or cost is invalid
        """
        if quantity <= 0:
            raise InvalidQuantityError("Purchase quantity must be greater than 0")

        if unit_cost <= 0:
            raise InvalidQuantityError("Unit cost must be greater than 0")

        # Get or create inventory record
        inventory_record = store_inventory.get_by_store_and_product(db, store_id, product_id)
        if not inventory_record:
            # Initialize if doesn't exist
            return self.initialize_inventory(db, store_id, product_id, quantity, unit_cost)

        # Update inventory using weighted average cost
        new_quantity = inventory_record.quantity_balance + quantity
        new_total_cost = inventory_record.total_cost + (Decimal(quantity) * unit_cost)
        new_unit_cost = new_total_cost / Decimal(new_quantity) if new_quantity > 0 else unit_cost

        updated_inventory = store_inventory.update(
            db,
            db_obj=inventory_record,
            obj_in={
                "quantity_balance": new_quantity,
                "unit_cost": new_unit_cost,
                "total_cost": new_total_cost
            }
        )

        # Record movement
        movement_data = {
            "store_id": store_id,
            "product_id": product_id,
            "quantity_change": quantity,
            "unit_cost": unit_cost,
            "movement_type": "purchase",
            "notes": notes
        }
        inventory_movement.create(db, obj_in=movement_data)

        return updated_inventory

    def record_sale(
        self,
        db: Session,
        store_id: UUID,
        product_id: UUID,
        quantity: int,
        transaction_id: Optional[UUID] = None,
        notes: Optional[str] = None
    ) -> StoreInventory:
        """
        Record a product sale (reduces inventory).

        Raises:
            InventoryNotFoundError: If inventory doesn't exist
            InsufficientStockError: If not enough stock available
            InvalidQuantityError: If quantity is invalid
        """
        if quantity <= 0:
            raise InvalidQuantityError("Sale quantity must be greater than 0")

        inventory_record = store_inventory.get_by_store_and_product(db, store_id, product_id)
        if not inventory_record:
            raise InventoryNotFoundError(
                f"No inventory found for product {product_id} at store {store_id}"
            )

        if inventory_record.quantity_balance < quantity:
            raise InsufficientStockError(
                f"Insufficient stock. Available: {inventory_record.quantity_balance}, Requested: {quantity}"
            )

        # Update inventory
        new_quantity = inventory_record.quantity_balance - quantity
        new_total_cost = inventory_record.unit_cost * Decimal(new_quantity)

        updated_inventory = store_inventory.update(
            db,
            db_obj=inventory_record,
            obj_in={
                "quantity_balance": new_quantity,
                "total_cost": new_total_cost
            }
        )

        # Record movement
        movement_data = {
            "store_id": store_id,
            "product_id": product_id,
            "quantity_change": -quantity,
            "unit_cost": inventory_record.unit_cost,
            "movement_type": "sale",
            "reference_id": transaction_id,
            "notes": notes
        }
        inventory_movement.create(db, obj_in=movement_data)

        return updated_inventory

    def record_adjustment(
        self,
        db: Session,
        store_id: UUID,
        product_id: UUID,
        quantity_change: int,
        notes: Optional[str] = None
    ) -> StoreInventory:
        """
        Record an inventory adjustment (positive or negative).
        Used for corrections, damages, theft, etc.

        Raises:
            InventoryNotFoundError: If inventory doesn't exist
            InsufficientStockError: If negative adjustment exceeds stock
        """
        if quantity_change == 0:
            raise InvalidQuantityError("Adjustment quantity cannot be zero")

        inventory_record = store_inventory.get_by_store_and_product(db, store_id, product_id)
        if not inventory_record:
            raise InventoryNotFoundError(
                f"No inventory found for product {product_id} at store {store_id}"
            )

        new_quantity = inventory_record.quantity_balance + quantity_change
        if new_quantity < 0:
            raise InsufficientStockError(
                f"Adjustment would result in negative inventory. Current: {inventory_record.quantity_balance}"
            )

        # Update inventory
        new_total_cost = inventory_record.unit_cost * Decimal(new_quantity)

        updated_inventory = store_inventory.update(
            db,
            db_obj=inventory_record,
            obj_in={
                "quantity_balance": new_quantity,
                "total_cost": new_total_cost
            }
        )

        # Record movement
        movement_data = {
            "store_id": store_id,
            "product_id": product_id,
            "quantity_change": quantity_change,
            "unit_cost": inventory_record.unit_cost,
            "movement_type": "adjustment",
            "notes": notes
        }
        inventory_movement.create(db, obj_in=movement_data)

        return updated_inventory

    def record_return(
        self,
        db: Session,
        store_id: UUID,
        product_id: UUID,
        quantity: int,
        transaction_id: Optional[UUID] = None,
        notes: Optional[str] = None
    ) -> StoreInventory:
        """
        Record a product return (adds to inventory).

        Raises:
            InventoryNotFoundError: If inventory doesn't exist
            InvalidQuantityError: If quantity is invalid
        """
        if quantity <= 0:
            raise InvalidQuantityError("Return quantity must be greater than 0")

        inventory_record = store_inventory.get_by_store_and_product(db, store_id, product_id)
        if not inventory_record:
            raise InventoryNotFoundError(
                f"No inventory found for product {product_id} at store {store_id}"
            )

        # Update inventory
        new_quantity = inventory_record.quantity_balance + quantity
        new_total_cost = inventory_record.unit_cost * Decimal(new_quantity)

        updated_inventory = store_inventory.update(
            db,
            db_obj=inventory_record,
            obj_in={
                "quantity_balance": new_quantity,
                "total_cost": new_total_cost
            }
        )

        # Record movement
        movement_data = {
            "store_id": store_id,
            "product_id": product_id,
            "quantity_change": quantity,
            "unit_cost": inventory_record.unit_cost,
            "movement_type": "return",
            "reference_id": transaction_id,
            "notes": notes
        }
        inventory_movement.create(db, obj_in=movement_data)

        return updated_inventory

    def transfer_inventory(
        self,
        db: Session,
        from_store_id: UUID,
        to_store_id: UUID,
        product_id: UUID,
        quantity: int,
        notes: Optional[str] = None
    ) -> tuple[StoreInventory, StoreInventory]:
        """
        Transfer inventory between stores.

        Returns:
            Tuple of (from_store_inventory, to_store_inventory)

        Raises:
            InsufficientStockError: If not enough stock at source store
        """
        if quantity <= 0:
            raise InvalidQuantityError("Transfer quantity must be greater than 0")

        # Remove from source store
        from_inventory = self.record_adjustment(
            db,
            from_store_id,
            product_id,
            -quantity,
            notes=f"Transfer to store {to_store_id}: {notes or ''}"
        )

        # Add to destination store
        to_inventory_record = store_inventory.get_by_store_and_product(db, to_store_id, product_id)
        if not to_inventory_record:
            # Initialize if doesn't exist
            to_inventory = self.initialize_inventory(
                db,
                to_store_id,
                product_id,
                quantity,
                from_inventory.unit_cost
            )
        else:
            to_inventory = self.record_adjustment(
                db,
                to_store_id,
                product_id,
                quantity,
                notes=f"Transfer from store {from_store_id}: {notes or ''}"
            )

        # Record transfer movements
        movement_data_from = {
            "store_id": from_store_id,
            "product_id": product_id,
            "quantity_change": -quantity,
            "unit_cost": from_inventory.unit_cost,
            "movement_type": "transfer",
            "notes": f"Transfer to store {to_store_id}"
        }
        inventory_movement.create(db, obj_in=movement_data_from)

        movement_data_to = {
            "store_id": to_store_id,
            "product_id": product_id,
            "quantity_change": quantity,
            "unit_cost": from_inventory.unit_cost,
            "movement_type": "transfer",
            "notes": f"Transfer from store {from_store_id}"
        }
        inventory_movement.create(db, obj_in=movement_data_to)

        return from_inventory, to_inventory

    def get_inventory(
        self,
        db: Session,
        store_id: UUID,
        product_id: UUID
    ) -> Optional[StoreInventory]:
        """Get inventory for a specific product at a store"""
        return store_inventory.get_by_store_and_product(db, store_id, product_id)

    def get_store_inventory(
        self,
        db: Session,
        store_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StoreInventory]:
        """Get all inventory for a store"""
        return store_inventory.get_by_store(db, store_id, skip=skip, limit=limit)

    def get_product_inventory(
        self,
        db: Session,
        product_id: UUID
    ) -> List[StoreInventory]:
        """Get inventory for a product across all stores"""
        return store_inventory.get_by_product(db, product_id)

    def get_low_stock_items(
        self,
        db: Session,
        threshold: int = 10,
        store_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[StoreInventory]:
        """Get inventory items below a quantity threshold"""
        return store_inventory.get_low_stock(
            db,
            threshold=threshold,
            store_id=store_id,
            skip=skip,
            limit=limit
        )

    def get_out_of_stock_items(
        self,
        db: Session,
        store_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[StoreInventory]:
        """Get inventory items with zero quantity"""
        return store_inventory.get_out_of_stock(
            db,
            store_id=store_id,
            skip=skip,
            limit=limit
        )

    def get_total_inventory_value(
        self,
        db: Session,
        store_id: Optional[UUID] = None
    ) -> Decimal:
        """
        Calculate total inventory value.
        If store_id is provided, calculate for that store only.
        """
        if store_id:
            inventory_items = store_inventory.get_by_store(db, store_id)
        else:
            inventory_items = store_inventory.get_multi(db, limit=10000)

        total_value = sum(item.total_cost for item in inventory_items)
        return Decimal(str(total_value))

    def get_movement_history(
        self,
        db: Session,
        store_id: Optional[UUID] = None,
        product_id: Optional[UUID] = None,
        movement_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[InventoryMovement]:
        """Get inventory movement history with filters"""
        if start_date and end_date:
            return inventory_movement.get_by_date_range(
                db,
                start_date,
                end_date,
                store_id=store_id,
                skip=skip,
                limit=limit
            )
        elif store_id and product_id:
            return inventory_movement.get_by_store_and_product(
                db,
                store_id,
                product_id,
                skip=skip,
                limit=limit
            )
        elif store_id:
            return inventory_movement.get_by_store(db, store_id, skip=skip, limit=limit)
        elif product_id:
            return inventory_movement.get_by_product(db, product_id, skip=skip, limit=limit)
        elif movement_type:
            return inventory_movement.get_by_type(db, movement_type, skip=skip, limit=limit)
        else:
            return inventory_movement.get_multi(db, skip=skip, limit=limit)


inventory_service = InventoryService()
