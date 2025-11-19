from app.repositories.base import BaseRepository
from app.models.employee import Employee


class EmployeeRepository(BaseRepository[Employee]):
    """Repository for Employee operations"""

    def __init__(self):
        super().__init__(Employee)


employee = EmployeeRepository()
