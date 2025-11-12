from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional, List, Generic, TypeVar, Type
from . import models

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    """Base repository with shared CRUD operations"""

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get a single record by ID"""
        return self.db.query(self.model).filter(self.model.id == id).first()