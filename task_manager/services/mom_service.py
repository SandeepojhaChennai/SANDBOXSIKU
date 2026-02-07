"""Service layer for managing Minutes of Meeting (MOM) operations."""

from typing import List, Optional

from task_manager.models.meeting import Meeting
from task_manager.models.mom import AgendaItem, MinutesOfMeeting, MOMStatus
from task_manager.storage.json_store import JsonStore


class MOMService:
    """Handles creation, tracking, and validation of meeting minutes."""

    MEETINGS_COLLECTION = "meetings"
    MOM_COLLECTION = "mom"

    def __init__(self, store: JsonStore):
        self.store = store

    # -- Meeting operations --

    def create_meeting(
        self,
        title: str,
        department_id: str,
        date: str,
        attendees: Optional[List[str]] = None,
        location: str = "",
    ) -> Meeting:
        """Create and persist a new meeting."""
        meeting = Meeting(
            title=title,
            department_id=department_id,
            date=date,
            attendees=attendees or [],
            location=location,
        )
        self.store.insert(self.MEETINGS_COLLECTION, meeting.id, meeting.to_dict())
        return meeting

    def get_meeting(self, meeting_id: str) -> Optional[Meeting]:
        data = self.store.get(self.MEETINGS_COLLECTION, meeting_id)
        return Meeting.from_dict(data) if data else None

    def list_meetings(self, department_id: Optional[str] = None) -> List[Meeting]:
        if department_id:
            records = self.store.find(self.MEETINGS_COLLECTION, department_id=department_id)
        else:
            records = self.store.get_all(self.MEETINGS_COLLECTION)
        return [Meeting.from_dict(r) for r in records]

    # -- MOM operations --

    def create_mom(
        self,
        meeting_id: str,
        prepared_by: str,
        summary: str = "",
    ) -> MinutesOfMeeting:
        """Create minutes for an existing meeting."""
        meeting = self.get_meeting(meeting_id)
        if not meeting:
            raise ValueError(f"Meeting '{meeting_id}' not found")
        mom = MinutesOfMeeting(
            meeting_id=meeting_id,
            prepared_by=prepared_by,
            summary=summary,
        )
        self.store.insert(self.MOM_COLLECTION, mom.id, mom.to_dict())
        return mom

    def get_mom(self, mom_id: str) -> Optional[MinutesOfMeeting]:
        data = self.store.get(self.MOM_COLLECTION, mom_id)
        return MinutesOfMeeting.from_dict(data) if data else None

    def get_mom_by_meeting(self, meeting_id: str) -> Optional[MinutesOfMeeting]:
        """Retrieve the MOM for a specific meeting."""
        records = self.store.find(self.MOM_COLLECTION, meeting_id=meeting_id)
        return MinutesOfMeeting.from_dict(records[0]) if records else None

    def list_moms(
        self, status: Optional[MOMStatus] = None
    ) -> List[MinutesOfMeeting]:
        if status:
            records = self.store.find(self.MOM_COLLECTION, status=status.value)
        else:
            records = self.store.get_all(self.MOM_COLLECTION)
        return [MinutesOfMeeting.from_dict(r) for r in records]

    def add_agenda_item(
        self,
        mom_id: str,
        title: str,
        discussion: str = "",
        decisions: str = "",
    ) -> MinutesOfMeeting:
        """Add an agenda item to an existing MOM."""
        mom = self.get_mom(mom_id)
        if not mom:
            raise ValueError(f"MOM '{mom_id}' not found")
        mom.add_agenda_item(title=title, discussion=discussion, decisions=decisions)
        self.store.update(self.MOM_COLLECTION, mom.id, mom.to_dict())
        return mom

    def submit_for_review(self, mom_id: str) -> MinutesOfMeeting:
        """Submit a draft MOM for review."""
        mom = self.get_mom(mom_id)
        if not mom:
            raise ValueError(f"MOM '{mom_id}' not found")
        mom.submit_for_review()
        self.store.update(self.MOM_COLLECTION, mom.id, mom.to_dict())
        return mom

    def validate_mom(self, mom_id: str, validated_by: str) -> MinutesOfMeeting:
        """Validate/approve a MOM that is pending review."""
        mom = self.get_mom(mom_id)
        if not mom:
            raise ValueError(f"MOM '{mom_id}' not found")
        mom.validate(validated_by)
        self.store.update(self.MOM_COLLECTION, mom.id, mom.to_dict())
        return mom

    def reject_mom(
        self, mom_id: str, rejected_by: str, reason: str
    ) -> MinutesOfMeeting:
        """Reject a MOM that is pending review."""
        mom = self.get_mom(mom_id)
        if not mom:
            raise ValueError(f"MOM '{mom_id}' not found")
        mom.reject(rejected_by, reason)
        self.store.update(self.MOM_COLLECTION, mom.id, mom.to_dict())
        return mom

    def revise_mom(self, mom_id: str) -> MinutesOfMeeting:
        """Move a rejected MOM back to draft for revision."""
        mom = self.get_mom(mom_id)
        if not mom:
            raise ValueError(f"MOM '{mom_id}' not found")
        mom.revise()
        self.store.update(self.MOM_COLLECTION, mom.id, mom.to_dict())
        return mom

    def update_summary(self, mom_id: str, summary: str) -> MinutesOfMeeting:
        """Update the summary of a MOM (only allowed in draft status)."""
        mom = self.get_mom(mom_id)
        if not mom:
            raise ValueError(f"MOM '{mom_id}' not found")
        if mom.status != MOMStatus.DRAFT:
            raise ValueError("Can only update summary while MOM is in draft status")
        mom.summary = summary
        self.store.update(self.MOM_COLLECTION, mom.id, mom.to_dict())
        return mom
