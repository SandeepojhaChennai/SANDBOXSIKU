"""Service layer for managing tasks, including those linked to MOMs."""

from typing import List, Optional

from task_manager.models.task import Task, TaskPriority, TaskStatus
from task_manager.storage.json_store import JsonStore


class TaskService:
    """Handles creation, assignment, and tracking of tasks."""

    TASKS_COLLECTION = "tasks"

    def __init__(self, store: JsonStore):
        self.store = store

    def create_task(
        self,
        title: str,
        department_id: str,
        assigned_to: str,
        description: str = "",
        mom_id: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
    ) -> Task:
        """Create and persist a new task, optionally linked to a MOM."""
        task = Task(
            title=title,
            department_id=department_id,
            assigned_to=assigned_to,
            description=description,
            mom_id=mom_id,
            due_date=due_date,
            priority=priority,
        )
        self.store.insert(self.TASKS_COLLECTION, task.id, task.to_dict())
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        data = self.store.get(self.TASKS_COLLECTION, task_id)
        return Task.from_dict(data) if data else None

    def list_tasks(
        self,
        department_id: Optional[str] = None,
        assigned_to: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        mom_id: Optional[str] = None,
    ) -> List[Task]:
        """List tasks with optional filters."""
        filters = {}
        if department_id:
            filters["department_id"] = department_id
        if assigned_to:
            filters["assigned_to"] = assigned_to
        if status:
            filters["status"] = status.value
        if mom_id:
            filters["mom_id"] = mom_id

        if filters:
            records = self.store.find(self.TASKS_COLLECTION, **filters)
        else:
            records = self.store.get_all(self.TASKS_COLLECTION)
        return [Task.from_dict(r) for r in records]

    def get_tasks_for_mom(self, mom_id: str) -> List[Task]:
        """Get all tasks linked to a specific MOM."""
        records = self.store.find(self.TASKS_COLLECTION, mom_id=mom_id)
        return [Task.from_dict(r) for r in records]

    def start_task(self, task_id: str) -> Task:
        """Mark a task as in-progress."""
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task '{task_id}' not found")
        task.start()
        self.store.update(self.TASKS_COLLECTION, task.id, task.to_dict())
        return task

    def complete_task(self, task_id: str) -> Task:
        """Mark a task as completed."""
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task '{task_id}' not found")
        task.complete()
        self.store.update(self.TASKS_COLLECTION, task.id, task.to_dict())
        return task

    def cancel_task(self, task_id: str) -> Task:
        """Cancel a task."""
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task '{task_id}' not found")
        task.cancel()
        self.store.update(self.TASKS_COLLECTION, task.id, task.to_dict())
        return task

    def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        assigned_to: Optional[str] = None,
        due_date: Optional[str] = None,
        priority: Optional[TaskPriority] = None,
    ) -> Task:
        """Update mutable fields of a task."""
        task = self.get_task(task_id)
        if not task:
            raise ValueError(f"Task '{task_id}' not found")
        if task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
            raise ValueError(f"Cannot update a task with status '{task.status.value}'")
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if assigned_to is not None:
            task.assigned_to = assigned_to
        if due_date is not None:
            task.due_date = due_date
        if priority is not None:
            task.priority = priority
        self.store.update(self.TASKS_COLLECTION, task.id, task.to_dict())
        return task

    def delete_task(self, task_id: str) -> bool:
        """Delete a task by ID."""
        return self.store.delete(self.TASKS_COLLECTION, task_id)
