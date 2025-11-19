from app.repositories.base import BaseRepository
from app.models.transaction import Transaction, TransactionItem


class TransactionRepository(BaseRepository[Transaction]):
    """Repository for Transaction operations"""

    def __init__(self):
        super().__init__(Transaction)


class TransactionItemRepository(BaseRepository[TransactionItem]):
    """Repository for TransactionItem operations"""

    def __init__(self):
        super().__init__(TransactionItem)


transaction = TransactionRepository()
transaction_item = TransactionItemRepository()
