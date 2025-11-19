from app.repositories.base import BaseRepository
from app.models.store import Store


class StoreRepository(BaseRepository[Store]):
    """Repository for Store operations"""

    def __init__(self):
        super().__init__(Store)


store = StoreRepository()
