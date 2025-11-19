from app.repositories.base import BaseRepository
from app.models.inventory import InventoryMovement, StoreInventory


class InventoryMovementRepository(BaseRepository[InventoryMovement]):
    """Repository for InventoryMovement operations"""

    def __init__(self):
        super().__init__(InventoryMovement)


class StoreInventoryRepository(BaseRepository[StoreInventory]):
    """Repository for StoreInventory operations"""

    def __init__(self):
        super().__init__(StoreInventory)


inventory_movement = InventoryMovementRepository()
store_inventory = StoreInventoryRepository()