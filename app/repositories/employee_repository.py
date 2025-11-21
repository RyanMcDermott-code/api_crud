from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import date
from uuid import UUID
from app.repositories.base import BaseRepository
from app.models.employee import Employee


class EmployeeRepository(BaseRepository[Employee]):
    """Repository for Employee operations"""

    def __init__(self):
        super().__init__(Employee)

    def get_by_store(
        self,
        db: Session,
        store_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[Employee]:
        """Get employees assigned to a specific store"""
        filters = {"store_id": store_id}
        if active_only:
            filters["is_active"] = True
        return self.get_multi_by(db, skip=skip, limit=limit, **filters)

    def search_by_name(
        self,
        db: Session,
        name: str,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Employee]:
        """Search employees by first or last name (case-insensitive partial match)"""
        name_lower = name.lower()
        stmt = (
            select(self.model)
            .where(
                (func.lower(self.model.first_name).contains(name_lower)) |
                (func.lower(self.model.last_name).contains(name_lower))
            )
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def get_by_hire_date_range(
        self,
        db: Session,
        start_date: date,
        end_date: date,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Employee]:
        """Get employees hired within a date range"""
        stmt = (
            select(self.model)
            .where(
                self.model.hire_date.isnot(None),
                self.model.hire_date >= start_date,
                self.model.hire_date <= end_date
            )
            .order_by(self.model.hire_date)
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def get_unassigned(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Employee]:
        """Get employees not assigned to any store"""
        stmt = (
            select(self.model)
            .where(
                self.model.store_id.is_(None),
                self.model.is_active == True
            )
            .offset(skip)
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def count_by_store(self, db: Session, store_id: UUID) -> int:
        """Count active employees at a store"""
        return self.count(db, store_id=store_id, is_active=True)


employee = EmployeeRepository()
