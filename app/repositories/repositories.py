from typing import Generic, TypeVar, Type, Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
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
    
    # Read operations
    
    def get(self, db: Session, id: UUID) -> Optional[ModelType]:
        """
        Retrieve a single record by ID.
        
        Args:
            db: Database session
            id: Record UUID
            
        Returns:
            Model instance if found, None otherwise
        """
        return db.get(self.model, id)
    
    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        order_by: str = "created_at"
    ) -> List[ModelType]:
        """
        Retrieve multiple records with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Field to order by (prefix with - for descending)
            
        Returns:
            List of model instances
        """
        stmt = select(self.model)
        
        # Handle ordering
        if order_by.startswith('-'):
            stmt = stmt.order_by(desc(getattr(self.model, order_by[1:])))
        else:
            stmt = stmt.order_by(getattr(self.model, order_by))
        
        stmt = stmt.offset(skip).limit(limit)
        return list(db.scalars(stmt).all())
    
    def get_by(self, db: Session, **filters) -> Optional[ModelType]:
        """
        Get a single record by arbitrary filters.
        
        Args:
            db: Database session
            **filters: Field=value pairs to filter by
            
        Returns:
            First matching model instance or None
        """
        stmt = select(self.model).filter_by(**filters)
        return db.scalars(stmt).first()
    
    def get_multi_by(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "created_at",
        **filters
    ) -> List[ModelType]:
        """
        Get multiple records by arbitrary filters with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Field to order by (prefix with - for descending)
            **filters: Field=value pairs to filter by
            
        Returns:
            List of matching model instances
        """
        stmt = select(self.model).filter_by(**filters)
        
        # Handle ordering
        if order_by.startswith('-'):
            stmt = stmt.order_by(desc(getattr(self.model, order_by[1:])))
        else:
            stmt = stmt.order_by(getattr(self.model, order_by))
        
        stmt = stmt.offset(skip).limit(limit)
        return list(db.scalars(stmt).all())
    
    def exists(self, db: Session, id: UUID) -> bool:
        """
        Check if a record exists by ID.
        
        Args:
            db: Database session
            id: Record UUID
            
        Returns:
            True if record exists, False otherwise
        """
        return db.get(self.model, id) is not None
    
    def count(self, db: Session, **filters) -> int:
        """
        Count records matching filters.
        
        Args:
            db: Database session
            **filters: Field=value pairs to filter by
            
        Returns:
            Number of matching records
        """
        stmt = select(func.count()).select_from(self.model).filter_by(**filters)
        result = db.scalar(stmt)
        return result if result is not None else 0
    
    # Create operations
    
    def create(self, db: Session, *, obj_in: BaseModel | Dict[str, Any]) -> ModelType:
        """
        Create a new record from Pydantic model or dict.
        
        Args:
            db: Database session
            obj_in: Pydantic schema or dict with creation data
            
        Returns:
            Created model instance
        """
        obj_in_data = obj_in.model_dump() if isinstance(obj_in, BaseModel) else obj_in
        
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def create_multi(
        self, 
        db: Session, 
        *, 
        objs_in: List[BaseModel | Dict[str, Any]]
    ) -> List[ModelType]:
        """
        Create multiple records in a single transaction.
        
        Args:
            db: Database session
            objs_in: List of Pydantic schemas or dicts
            
        Returns:
            List of created model instances
        """
        db_objs = []
        for obj_in in objs_in:
            obj_in_data = obj_in.model_dump() if isinstance(obj_in, BaseModel) else obj_in
            db_obj = self.model(**obj_in_data)
            db_objs.append(db_obj)
        
        db.add_all(db_objs)
        db.commit()
        
        for db_obj in db_objs:
            db.refresh(db_obj)
        
        return db_objs
    
    def get_or_create(
        self,
        db: Session,
        *,
        defaults: Optional[Dict[str, Any]] = None,
        **filters
    ) -> Tuple[ModelType, bool]:
        """
        Get an existing record or create a new one.
        
        Args:
            db: Database session
            defaults: Default values for creation if record doesn't exist
            **filters: Field=value pairs to search by
            
        Returns:
            Tuple of (model instance, created flag)
        """
        obj = self.get_by(db, **filters)
        if obj:
            return obj, False
        
        create_data = {**filters, **(defaults or {})}
        obj = self.create(db, obj_in=create_data)
        return obj, True
    
    # Update operations
    
    def update(
        self, 
        db: Session, 
        *, 
        db_obj: ModelType, 
        obj_in: BaseModel | Dict[str, Any]
    ) -> ModelType:
        """
        Update an existing record from Pydantic model or dict.
        
        Args:
            db: Database session
            db_obj: Existing model instance to update
            obj_in: Pydantic schema or dict with update data
            
        Returns:
            Updated model instance
        """
        update_data = (
            obj_in.model_dump(exclude_unset=True) 
            if isinstance(obj_in, BaseModel) 
            else obj_in
        )
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_by_id(
        self,
        db: Session,
        *,
        id: UUID,
        obj_in: BaseModel | Dict[str, Any]
    ) -> Optional[ModelType]:
        """
        Update a record by ID.
        
        Args:
            db: Database session
            id: Record UUID
            obj_in: Pydantic schema or dict with update data
            
        Returns:
            Updated model instance if found, None otherwise
        """
        db_obj = self.get(db, id)
        if not db_obj:
            return None
        return self.update(db, db_obj=db_obj, obj_in=obj_in)
    
    # Delete operations
    
    def delete(self, db: Session, *, id: UUID) -> Optional[ModelType]:
        """
        Hard delete a record by ID.
        
        Args:
            db: Database session
            id: Record UUID to delete
            
        Returns:
            Deleted model instance if found, None otherwise
        """
        obj = db.get(self.model, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
    
    def delete_multi(self, db: Session, *, ids: List[UUID]) -> int:
        """
        Hard delete multiple records by IDs.
        
        Args:
            db: Database session
            ids: List of record UUIDs to delete
            
        Returns:
            Number of records deleted
        """
        objs = [db.get(self.model, id) for id in ids]
        objs = [obj for obj in objs if obj is not None]
        
        for obj in objs:
            db.delete(obj)
        
        db.commit()
        return len(objs)
    
    # Soft delete operations (if model has is_active field)
    
    def soft_delete(self, db: Session, *, id: UUID) -> Optional[ModelType]:
        """
        Soft delete by setting is_active=False.
        
        Args:
            db: Database session
            id: Record UUID to soft delete
            
        Returns:
            Soft deleted model instance if found, None otherwise
        """
        obj = db.get(self.model, id)
        if obj and hasattr(obj, 'is_active'):
            obj.is_active = False
            db.add(obj)
            db.commit()
            db.refresh(obj)
        return obj
    
    def restore(self, db: Session, *, id: UUID) -> Optional[ModelType]:
        """
        Restore a soft-deleted record by setting is_active=True.
        
        Args:
            db: Database session
            id: Record UUID to restore
            
        Returns:
            Restored model instance if found, None otherwise
        """
        obj = db.get(self.model, id)
        if obj and hasattr(obj, 'is_active'):
            obj.is_active = True
            db.add(obj)
            db.commit()
            db.refresh(obj)
        return obj
    
    def get_active(self, db: Session, id: UUID) -> Optional[ModelType]:
        """
        Get record by ID only if active.
        
        Args:
            db: Database session
            id: Record UUID
            
        Returns:
            Model instance if found and active, None otherwise
        """
        obj = db.get(self.model, id)
        if obj and hasattr(obj, 'is_active') and not obj.is_active:
            return None
        return obj
    
    def get_multi_active(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "created_at"
    ) -> List[ModelType]:
        """
        Get multiple active records with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_by: Field to order by (prefix with - for descending)
            
        Returns:
            List of active model instances
        """
        if not hasattr(self.model, 'is_active'):
            return self.get_multi(db, skip=skip, limit=limit, order_by=order_by)
        
        return self.get_multi_by(
            db, 
            skip=skip, 
            limit=limit, 
            order_by=order_by,
            is_active=True
        )