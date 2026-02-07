"""Minutes of Meeting (MOM) model for recording and validating meeting minutes."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class MOMStatus(str, Enum):
    """Status lifecycle for a Minutes of Meeting document."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    VALIDATED = "validated"
    REJECTED = "rejected"


@dataclass
class AgendaItem:
    """A single agenda item discussed in a meeting."""

    title: str
    discussion: str = ""
    decisions: str = ""

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "discussion": self.discussion,
            "decisions": self.decisions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgendaItem":
        return cls(
            title=data["title"],
            discussion=data.get("discussion", ""),
            decisions=data.get("decisions", ""),
        )


@dataclass
class MinutesOfMeeting:
    """Represents the minutes recorded for a specific meeting."""

    meeting_id: str
    prepared_by: str
    agenda_items: List[AgendaItem] = field(default_factory=list)
    summary: str = ""
    status: MOMStatus = MOMStatus.DRAFT
    validated_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def submit_for_review(self) -> None:
        """Move the MOM from draft to pending review."""
        if self.status != MOMStatus.DRAFT:
            raise ValueError(
                f"Can only submit for review from draft status, current: {self.status}"
            )
        self.status = MOMStatus.PENDING_REVIEW
        self.updated_at = datetime.now().isoformat()

    def validate(self, validated_by: str) -> None:
        """Validate/approve the MOM."""
        if self.status != MOMStatus.PENDING_REVIEW:
            raise ValueError(
                f"Can only validate from pending_review status, current: {self.status}"
            )
        self.status = MOMStatus.VALIDATED
        self.validated_by = validated_by
        self.updated_at = datetime.now().isoformat()

    def reject(self, rejected_by: str, reason: str) -> None:
        """Reject the MOM and send it back for revision."""
        if self.status != MOMStatus.PENDING_REVIEW:
            raise ValueError(
                f"Can only reject from pending_review status, current: {self.status}"
            )
        self.status = MOMStatus.REJECTED
        self.validated_by = rejected_by
        self.rejection_reason = reason
        self.updated_at = datetime.now().isoformat()

    def revise(self) -> None:
        """Move a rejected MOM back to draft for revision."""
        if self.status != MOMStatus.REJECTED:
            raise ValueError(
                f"Can only revise from rejected status, current: {self.status}"
            )
        self.status = MOMStatus.DRAFT
        self.rejection_reason = None
        self.validated_by = None
        self.updated_at = datetime.now().isoformat()

    def add_agenda_item(self, title: str, discussion: str = "", decisions: str = "") -> AgendaItem:
        item = AgendaItem(title=title, discussion=discussion, decisions=decisions)
        self.agenda_items.append(item)
        self.updated_at = datetime.now().isoformat()
        return item

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "meeting_id": self.meeting_id,
            "prepared_by": self.prepared_by,
            "agenda_items": [item.to_dict() for item in self.agenda_items],
            "summary": self.summary,
            "status": self.status.value,
            "validated_by": self.validated_by,
            "rejection_reason": self.rejection_reason,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MinutesOfMeeting":
        return cls(
            id=data["id"],
            meeting_id=data["meeting_id"],
            prepared_by=data["prepared_by"],
            agenda_items=[AgendaItem.from_dict(a) for a in data.get("agenda_items", [])],
            summary=data.get("summary", ""),
            status=MOMStatus(data.get("status", "draft")),
            validated_by=data.get("validated_by"),
            rejection_reason=data.get("rejection_reason"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
        )
