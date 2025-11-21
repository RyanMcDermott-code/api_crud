from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from datetime import datetime, timezone

from app.models.customer import Customer, CustomerAccount
from app.repositories.customer_repository import customer, customer_account
from app.core.exceptions import (
    DuplicateEmailError,
    CustomerNotFoundError,
    InvalidCredentialsError
)


class CustomerService:
    """Business logic for customer management"""

    def create_anonymous_customer(
        self,
        db: Session,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> Customer:
        """
        Create an anonymous customer (no account).
        Used for quick checkouts without registration.
        """
        customer_data = {
            "first_name": first_name,
            "last_name": last_name,
            "is_registered": False,
            "is_active": True
        }
        return customer.create(db, obj_in=customer_data)

    def register_customer(
        self,
        db: Session,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone_number: Optional[str] = None
    ) -> Tuple[Customer, CustomerAccount]:
        """
        Register a new customer with account credentials.

        Args:
            db: Database session
            email: Customer email (must be unique)
            password: Plain text password (will be hashed)
            first_name: Customer first name
            last_name: Customer last name
            phone_number: Optional phone number

        Returns:
            Tuple of (Customer, CustomerAccount)

        Raises:
            DuplicateEmailError: If email already exists
        """
        # Check if email already exists
        if customer_account.email_exists(db, email):
            raise DuplicateEmailError(f"Email {email} is already registered")

        try:
            # Create customer
            customer_data = {
                "first_name": first_name,
                "last_name": last_name,
                "is_registered": True,
                "is_active": True
            }
            new_customer = customer.create(db, obj_in=customer_data)

            # Hash password (TODO: implement proper password hashing)
            from app.core.security import get_password_hash
            hashed_password = get_password_hash(password)

            # Create account
            account_data = {
                "customer_id": new_customer.id,
                "email": email,
                "hashed_password": hashed_password,
                "phone_number": phone_number,
                "is_active": True
            }
            new_account = customer_account.create(db, obj_in=account_data)

            return new_customer, new_account

        except IntegrityError as e:
            db.rollback()
            raise DuplicateEmailError(f"Email {email} is already registered")

    def convert_anonymous_to_registered(
        self,
        db: Session,
        customer_id: UUID,
        email: str,
        password: str,
        phone_number: Optional[str] = None
    ) -> Tuple[Customer, CustomerAccount]:
        """
        Convert an anonymous customer to a registered customer.
        Useful for post-purchase registration.

        Raises:
            CustomerNotFoundError: If customer doesn't exist
            DuplicateEmailError: If email already exists
        """
        existing_customer = customer.get(db, customer_id)
        if not existing_customer:
            raise CustomerNotFoundError(f"Customer {customer_id} not found")

        if existing_customer.is_registered:
            raise ValueError("Customer is already registered")

        if customer_account.email_exists(db, email):
            raise DuplicateEmailError(f"Email {email} is already registered")

        # Update customer status
        customer.update(db, db_obj=existing_customer, obj_in={"is_registered": True})

        # Hash password
        from app.core.security import get_password_hash
        hashed_password = get_password_hash(password)

        # Create account
        account_data = {
            "customer_id": customer_id,
            "email": email,
            "hashed_password": hashed_password,
            "phone_number": phone_number,
            "is_active": True
        }
        new_account = customer_account.create(db, obj_in=account_data)

        return existing_customer, new_account

    def authenticate(
        self,
        db: Session,
        email: str,
        password: str
    ) -> Tuple[Customer, CustomerAccount]:
        """
        Authenticate a customer by email and password.

        Returns:
            Tuple of (Customer, CustomerAccount)

        Raises:
            InvalidCredentialsError: If credentials are invalid
        """
        account = customer_account.get_by_email(db, email)
        if not account or not account.is_active:
            raise InvalidCredentialsError("Invalid email or password")

        # Verify password
        from app.core.security import verify_password
        if not verify_password(password, account.hashed_password):
            raise InvalidCredentialsError("Invalid email or password")

        # Get customer
        cust = customer.get(db, account.customer_id)
        if not cust or not cust.is_active:
            raise InvalidCredentialsError("Customer account is not active")

        return cust, account

    def get_customer_by_email(
        self,
        db: Session,
        email: str
    ) -> Optional[Customer]:
        """Get customer by email address"""
        return customer.get_by_email(db, email)

    def get_customer(
        self,
        db: Session,
        customer_id: UUID
    ) -> Optional[Customer]:
        """Get customer by ID"""
        return customer.get(db, customer_id)

    def update_customer(
        self,
        db: Session,
        customer_id: UUID,
        **update_data
    ) -> Optional[Customer]:
        """Update customer information"""
        existing = customer.get(db, customer_id)
        if not existing:
            raise CustomerNotFoundError(f"Customer {customer_id} not found")
        return customer.update(db, db_obj=existing, obj_in=update_data)

    def update_account(
        self,
        db: Session,
        account_id: UUID,
        **update_data
    ) -> Optional[CustomerAccount]:
        """Update customer account information"""
        existing = customer_account.get(db, account_id)
        if not existing:
            raise CustomerNotFoundError(f"Account {account_id} not found")
        return customer_account.update(db, db_obj=existing, obj_in=update_data)

    def deactivate_customer(
        self,
        db: Session,
        customer_id: UUID
    ) -> Customer:
        """
        Deactivate a customer account (soft delete).
        Customer data is preserved for transaction history.
        """
        existing = customer.get(db, customer_id)
        if not existing:
            raise CustomerNotFoundError(f"Customer {customer_id} not found")

        # Deactivate customer
        customer.soft_delete(db, id=customer_id)

        # Deactivate account if exists
        if existing.account:
            account_obj = existing.account
            account_obj.is_active = False
            account_obj.deleted_at = datetime.now(timezone.utc)
            db.add(account_obj)
            db.commit()

        return existing

    def reactivate_customer(
        self,
        db: Session,
        customer_id: UUID
    ) -> Customer:
        """Reactivate a deactivated customer account"""
        existing = customer.restore(db, id=customer_id)
        if not existing:
            raise CustomerNotFoundError(f"Customer {customer_id} not found")

        # Reactivate account if exists
        if existing.account:
            account_obj = existing.account
            account_obj.is_active = True
            account_obj.deleted_at = None
            db.add(account_obj)
            db.commit()

        return existing

    def list_registered_customers(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Customer]:
        """List all registered customers"""
        return customer.get_registered_customers(db, skip=skip, limit=limit)

    def change_password(
        self,
        db: Session,
        customer_id: UUID,
        old_password: str,
        new_password: str
    ) -> CustomerAccount:
        """
        Change customer password.

        Raises:
            CustomerNotFoundError: If customer/account doesn't exist
            InvalidCredentialsError: If old password is incorrect
        """
        cust = customer.get(db, customer_id)
        if not cust or not cust.account:
            raise CustomerNotFoundError(f"Customer {customer_id} not found")

        account_obj = cust.account

        # Verify old password
        from app.core.security import verify_password, get_password_hash
        if not verify_password(old_password, account_obj.hashed_password):
            raise InvalidCredentialsError("Old password is incorrect")

        # Update password
        new_hashed = get_password_hash(new_password)
        account_obj.hashed_password = new_hashed
        db.add(account_obj)
        db.commit()
        db.refresh(account_obj)

        return account_obj


customer_service = CustomerService()
