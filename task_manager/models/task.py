"""Task model for tracking action items arising from meetings."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class TaskStatus(str, Enum):
    """Status lifecycle for a task."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Priority levels for tasks."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Task:
    """Represents an actionable task, optionally linked to a MOM."""

    title: str
    department_id: str
    assigned_to: str
    description: str = ""
    mom_id: Optional[str] = None
    due_date: Optional[str] = None
    status: TaskStatus = TaskStatus.OPEN
    priority: TaskPriority = TaskPriority.MEDIUM
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def start(self) -> None:
        """Mark the task as in progress."""
        if self.status != TaskStatus.OPEN:
            raise ValueError(
                f"Can only start a task from open status, current: {self.status}"
            )
        self.status = TaskStatus.IN_PROGRESS
        self.updated_at = datetime.now().isoformat()

    def complete(self) -> None:
        """Mark the task as completed."""
        if self.status not in (TaskStatus.OPEN, TaskStatus.IN_PROGRESS):
            raise ValueError(
                f"Can only complete a task from open/in_progress status, current: {self.status}"
            )
        self.status = TaskStatus.COMPLETED
        self.updated_at = datetime.now().isoformat()

    def cancel(self) -> None:
        """Cancel the task."""
        if self.status == TaskStatus.COMPLETED:
            raise ValueError("Cannot cancel a completed task")
        self.status = TaskStatus.CANCELLED
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "department_id": self.department_id,
            "assigned_to": self.assigned_to,
            "mom_id": self.mom_id,
            "due_date": self.due_date,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            department_id=data["department_id"],
            assigned_to=data["assigned_to"],
            mom_id=data.get("mom_id"),
            due_date=data.get("due_date"),
            status=TaskStatus(data.get("status", "open")),
            priority=TaskPriority(data.get("priority", "medium")),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
        )
