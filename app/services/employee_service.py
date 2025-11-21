from typing import Optional, List
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date

from app.models.employee import Employee
from app.repositories.employee_repository import employee
from app.repositories.store_repository import store
from app.core.exceptions import (
    EmployeeNotFoundError,
    StoreNotFoundError,
    InvalidDateError
)


class EmployeeService:
    """Business logic for employee management"""

    def create_employee(
        self,
        db: Session,
        first_name: str,
        last_name: str,
        store_id: Optional[UUID] = None,
        dob: Optional[date] = None,
        hire_date: Optional[date] = None
    ) -> Employee:
        """
        Create a new employee.

        Args:
            db: Database session
            first_name: Employee first name
            last_name: Employee last name
            store_id: Optional store assignment
            dob: Optional date of birth
            hire_date: Optional hire date

        Returns:
            Created Employee instance

        Raises:
            StoreNotFoundError: If store_id is provided but doesn't exist
            InvalidDateError: If dates are invalid
        """
        # Validate store exists
        if store_id is not None:
            existing_store = store.get(db, store_id)
            if not existing_store:
                raise StoreNotFoundError(f"Store {store_id} not found")

        # Validate dates
        if dob and dob >= date.today():
            raise InvalidDateError("Date of birth must be in the past")

        if dob and hire_date and hire_date < dob:
            raise InvalidDateError("Hire date cannot be before date of birth")

        employee_data = {
            "first_name": first_name,
            "last_name": last_name,
            "store_id": store_id,
            "dob": dob,
            "hire_date": hire_date,
            "is_active": True
        }
        return employee.create(db, obj_in=employee_data)

    def get_employee(
        self,
        db: Session,
        employee_id: UUID
    ) -> Optional[Employee]:
        """Get employee by ID"""
        return employee.get(db, employee_id)

    def list_employees(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Employee]:
        """List all employees with pagination"""
        if active_only:
            return employee.get_multi_active(db, skip=skip, limit=limit)
        return employee.get_multi(db, skip=skip, limit=limit)

    def search_by_name(
        self,
        db: Session,
        name: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Employee]:
        """Search employees by first or last name"""
        return employee.search_by_name(db, name, skip=skip, limit=limit)

    def get_employees_by_store(
        self,
        db: Session,
        store_id: UUID,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Employee]:
        """Get all employees assigned to a specific store"""
        return employee.get_by_store(
            db,
            store_id,
            skip=skip,
            limit=limit,
            active_only=active_only
        )

    def get_unassigned_employees(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Employee]:
        """Get employees not assigned to any store"""
        return employee.get_unassigned(db, skip=skip, limit=limit)

    def get_by_hire_date_range(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        skip: int = 0,
        limit: int = 100
    ) -> List[Employee]:
        """Get employees hired within a date range"""
        if start_date > end_date:
            raise InvalidDateError("Start date must be before end date")
        return employee.get_by_hire_date_range(
            db,
            start_date,
            end_date,
            skip=skip,
            limit=limit
        )

    def update_employee(
        self,
        db: Session,
        employee_id: UUID,
        **update_data
    ) -> Employee:
        """
        Update employee information.

        Raises:
            EmployeeNotFoundError: If employee doesn't exist
            StoreNotFoundError: If store_id is provided but doesn't exist
            InvalidDateError: If dates are invalid
        """
        existing = employee.get(db, employee_id)
        if not existing:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found")

        # Validate store if being updated
        if "store_id" in update_data and update_data["store_id"] is not None:
            existing_store = store.get(db, update_data["store_id"])
            if not existing_store:
                raise StoreNotFoundError(f"Store {update_data['store_id']} not found")

        # Validate dates if being updated
        new_dob = update_data.get("dob", existing.dob)
        new_hire_date = update_data.get("hire_date", existing.hire_date)

        if new_dob and new_dob >= date.today():
            raise InvalidDateError("Date of birth must be in the past")

        if new_dob and new_hire_date and new_hire_date < new_dob:
            raise InvalidDateError("Hire date cannot be before date of birth")

        return employee.update(db, db_obj=existing, obj_in=update_data)

    def assign_to_store(
        self,
        db: Session,
        employee_id: UUID,
        store_id: UUID
    ) -> Employee:
        """
        Assign an employee to a store.

        Raises:
            EmployeeNotFoundError: If employee doesn't exist
            StoreNotFoundError: If store doesn't exist
        """
        existing_employee = employee.get(db, employee_id)
        if not existing_employee:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found")

        existing_store = store.get(db, store_id)
        if not existing_store:
            raise StoreNotFoundError(f"Store {store_id} not found")

        return employee.update(db, db_obj=existing_employee, obj_in={"store_id": store_id})

    def unassign_from_store(
        self,
        db: Session,
        employee_id: UUID
    ) -> Employee:
        """
        Remove employee's store assignment.

        Raises:
            EmployeeNotFoundError: If employee doesn't exist
        """
        existing = employee.get(db, employee_id)
        if not existing:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found")

        return employee.update(db, db_obj=existing, obj_in={"store_id": None})

    def deactivate_employee(
        self,
        db: Session,
        employee_id: UUID
    ) -> Employee:
        """
        Deactivate an employee (soft delete).
        Employee data is preserved for transaction history.
        """
        existing = employee.soft_delete(db, id=employee_id)
        if not existing:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found")
        return existing

    def reactivate_employee(
        self,
        db: Session,
        employee_id: UUID
    ) -> Employee:
        """Reactivate a deactivated employee"""
        existing = employee.restore(db, id=employee_id)
        if not existing:
            raise EmployeeNotFoundError(f"Employee {employee_id} not found")
        return existing

    def count_employees_by_store(
        self,
        db: Session,
        store_id: UUID
    ) -> int:
        """Count active employees at a store"""
        return employee.count_by_store(db, store_id)


employee_service = EmployeeService()
