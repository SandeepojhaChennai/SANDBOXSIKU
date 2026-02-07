"""Meeting model representing a scheduled or completed meeting."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class Meeting:
    """Represents a meeting held by a department."""

    title: str
    department_id: str
    date: str
    attendees: List[str] = field(default_factory=list)
    location: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "department_id": self.department_id,
            "date": self.date,
            "attendees": self.attendees,
            "location": self.location,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Meeting":
        return cls(
            id=data["id"],
            title=data["title"],
            department_id=data["department_id"],
            date=data["date"],
            attendees=data.get("attendees", []),
            location=data.get("location", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )
