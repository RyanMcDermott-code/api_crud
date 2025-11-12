from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, Select, func, and_
from pydantic import BaseModel
from uuid import UUID
from app.database import Base

ModelType = TypeVar('ModelType', bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository providing CRUD and query operations for SQLAlchemy models.
    
    Type Parameters:
        ModelType: SQLAlchemy model class
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Initialize repository with a SQLAlchemy model.
        
        Args:
            model: The SQLAlchemy model class this repository manages
        """
        self.model = model
    
    # Basic CRUD
    
    def get(self, db: Session, id: UUID) -> Optional[ModelType]:
        """Retrieve a single record by ID."""
        return db.get(self.model, id)
    
    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ModelType]:
        """Retrieve multiple records with pagination."""
        stmt = select(self.model).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())
    
    def create(self, db: Session, *, obj_in: BaseModel | Dict[str, Any]) -> ModelType:
        """Create a new record from Pydantic model or dict."""
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
        else:
            obj_in_data = obj_in.model_dump()
        
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, 
        db: Session, 
        *, 
        db_obj: ModelType, 
        obj_in: BaseModel | Dict[str, Any]
    ) -> ModelType:
        """Update an existing record from Pydantic model or dict."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, id: UUID) -> Optional[ModelType]:
        """Hard delete a record by ID."""
        obj = db.get(self.model, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
    
    # Query helpers
    
    def get_by(self, db: Session, **filters) -> Optional[ModelType]:
        """Get a single record by arbitrary filters."""
        stmt = select(self.model).filter_by(**filters)
        return db.scalars(stmt).first()
    
    def get_multi_by(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[ModelType]:
        """Get multiple records by arbitrary filters."""
        stmt = select(self.model).filter_by(**filters).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())
    
    def exists(self, db: Session, id: UUID) -> bool:
        """Check if a record exists by ID."""
        stmt = select(func.count()).select_from(self.model).where(self.model.id == id)
        return db.scalar(stmt) > 0
    
    def count(self, db: Session, **filters) -> int:
        """Count records matching filters."""
        stmt = select(func.count()).select_from(self.model).filter_by(**filters)
        return db.scalar(stmt) or 0
    
    # Soft delete support (if model has is_active field)
    
    def soft_delete(self, db: Session, *, id: UUID) -> Optional[ModelType]:
        """Soft delete by setting is_active=False."""
        obj = db.get(self.model, id)
        if obj and hasattr(obj, 'is_active'):
            obj.is_active = False
            db.add(obj)
            db.commit()
            db.refresh(obj)
        return obj
    
    def get_active(self, db: Session, id: UUID) -> Optional[ModelType]:
        """Get record by ID only if active."""
        obj = db.get(self.model, id)
        if obj and hasattr(obj, 'is_active') and not obj.is_active:
            return None
        return obj