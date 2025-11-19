from typing import Optional, List
from sqlalchemy.orm import Session
from uuid import UUID
from app.models.customer import Customer, CustomerAccount
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    """Repository for Customer operations"""

    def __init__(self):
        super().__init__(Customer)

    def get_by_email(self, db: Session, email: str) -> Optional[Customer]:
        """Get customer by account email"""
        return (
            db.query(self.model)
            .join(CustomerAccount)
            .filter(CustomerAccount.email == email)
            .first()
        )

    def get_registered_customers(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Customer]:
        """Get only registered customers"""
        return self.get_multi_by(
            db,
            skip=skip,
            limit=limit,
            is_registered=True
        )


class CustomerAccountRepository(BaseRepository[CustomerAccount]):
    """Repository for CustomerAccount operations"""

    def __init__(self):
        super().__init__(CustomerAccount)

    def get_by_email(self, db: Session, email: str) -> Optional[CustomerAccount]:
        """Get account by email"""
        return self.get_by(db, email=email)

    def email_exists(self, db: Session, email: str) -> bool:
        """Check if email already exists"""
        return self.get_by(db, email=email) is not None


customer = CustomerRepository()
customer_account = CustomerAccountRepository()