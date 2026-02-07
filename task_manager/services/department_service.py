"""Service layer for managing departments."""

from typing import List, Optional

from task_manager.models.department import Department
from task_manager.storage.json_store import JsonStore


class DepartmentService:
    """Handles creation and retrieval of departments."""

    COLLECTION = "departments"

    def __init__(self, store: JsonStore):
        self.store = store

    def create_department(self, name: str, description: str = "") -> Department:
        """Create and persist a new department."""
        dept = Department(name=name, description=description)
        self.store.insert(self.COLLECTION, dept.id, dept.to_dict())
        return dept

    def get_department(self, department_id: str) -> Optional[Department]:
        data = self.store.get(self.COLLECTION, department_id)
        return Department.from_dict(data) if data else None

    def list_departments(self) -> List[Department]:
        records = self.store.get_all(self.COLLECTION)
        return [Department.from_dict(r) for r in records]

    def delete_department(self, department_id: str) -> bool:
        return self.store.delete(self.COLLECTION, department_id)
