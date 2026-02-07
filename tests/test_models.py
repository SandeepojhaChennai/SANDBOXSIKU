"""Tests for data models."""

import pytest

from task_manager.models.department import Department
from task_manager.models.meeting import Meeting
from task_manager.models.mom import AgendaItem, MinutesOfMeeting, MOMStatus
from task_manager.models.task import Task, TaskPriority, TaskStatus


class TestDepartment:
    def test_create_department(self):
        dept = Department(name="Engineering", description="Software dept")
        assert dept.name == "Engineering"
        assert dept.description == "Software dept"
        assert dept.id is not None

    def test_serialization(self):
        dept = Department(name="HR", description="Human Resources")
        data = dept.to_dict()
        restored = Department.from_dict(data)
        assert restored.name == dept.name
        assert restored.id == dept.id
        assert restored.description == dept.description


class TestMeeting:
    def test_create_meeting(self):
        meeting = Meeting(
            title="Sprint Planning",
            department_id="dept-1",
            date="2026-02-06",
            attendees=["Alice", "Bob"],
            location="Room A",
        )
        assert meeting.title == "Sprint Planning"
        assert len(meeting.attendees) == 2

    def test_serialization(self):
        meeting = Meeting(
            title="Retro",
            department_id="dept-1",
            date="2026-02-07",
        )
        data = meeting.to_dict()
        restored = Meeting.from_dict(data)
        assert restored.title == meeting.title
        assert restored.id == meeting.id


class TestMinutesOfMeeting:
    def test_create_mom(self):
        mom = MinutesOfMeeting(meeting_id="m-1", prepared_by="Alice")
        assert mom.status == MOMStatus.DRAFT
        assert mom.meeting_id == "m-1"

    def test_add_agenda_item(self):
        mom = MinutesOfMeeting(meeting_id="m-1", prepared_by="Alice")
        item = mom.add_agenda_item("Budget Review", discussion="Discussed Q1 budget")
        assert len(mom.agenda_items) == 1
        assert item.title == "Budget Review"

    def test_status_flow_draft_to_validated(self):
        mom = MinutesOfMeeting(meeting_id="m-1", prepared_by="Alice")
        assert mom.status == MOMStatus.DRAFT

        mom.submit_for_review()
        assert mom.status == MOMStatus.PENDING_REVIEW

        mom.validate("Manager Bob")
        assert mom.status == MOMStatus.VALIDATED
        assert mom.validated_by == "Manager Bob"

    def test_status_flow_draft_to_rejected_to_revised(self):
        mom = MinutesOfMeeting(meeting_id="m-1", prepared_by="Alice")
        mom.submit_for_review()
        mom.reject("Manager Bob", "Missing action items")
        assert mom.status == MOMStatus.REJECTED
        assert mom.rejection_reason == "Missing action items"

        mom.revise()
        assert mom.status == MOMStatus.DRAFT
        assert mom.rejection_reason is None

    def test_cannot_submit_non_draft(self):
        mom = MinutesOfMeeting(meeting_id="m-1", prepared_by="Alice")
        mom.submit_for_review()
        with pytest.raises(ValueError, match="draft"):
            mom.submit_for_review()

    def test_cannot_validate_non_pending(self):
        mom = MinutesOfMeeting(meeting_id="m-1", prepared_by="Alice")
        with pytest.raises(ValueError, match="pending_review"):
            mom.validate("Bob")

    def test_cannot_reject_non_pending(self):
        mom = MinutesOfMeeting(meeting_id="m-1", prepared_by="Alice")
        with pytest.raises(ValueError, match="pending_review"):
            mom.reject("Bob", "reason")

    def test_cannot_revise_non_rejected(self):
        mom = MinutesOfMeeting(meeting_id="m-1", prepared_by="Alice")
        with pytest.raises(ValueError, match="rejected"):
            mom.revise()

    def test_serialization(self):
        mom = MinutesOfMeeting(meeting_id="m-1", prepared_by="Alice", summary="Test")
        mom.add_agenda_item("Item 1", "Discussion 1", "Decision 1")
        mom.submit_for_review()
        data = mom.to_dict()
        restored = MinutesOfMeeting.from_dict(data)
        assert restored.id == mom.id
        assert restored.status == MOMStatus.PENDING_REVIEW
        assert len(restored.agenda_items) == 1
        assert restored.agenda_items[0].title == "Item 1"


class TestTask:
    def test_create_task(self):
        task = Task(
            title="Fix bug",
            department_id="dept-1",
            assigned_to="Alice",
            priority=TaskPriority.HIGH,
        )
        assert task.status == TaskStatus.OPEN
        assert task.priority == TaskPriority.HIGH

    def test_start_task(self):
        task = Task(title="Work", department_id="d1", assigned_to="Bob")
        task.start()
        assert task.status == TaskStatus.IN_PROGRESS

    def test_complete_from_open(self):
        task = Task(title="Work", department_id="d1", assigned_to="Bob")
        task.complete()
        assert task.status == TaskStatus.COMPLETED

    def test_complete_from_in_progress(self):
        task = Task(title="Work", department_id="d1", assigned_to="Bob")
        task.start()
        task.complete()
        assert task.status == TaskStatus.COMPLETED

    def test_cancel_task(self):
        task = Task(title="Work", department_id="d1", assigned_to="Bob")
        task.cancel()
        assert task.status == TaskStatus.CANCELLED

    def test_cannot_start_non_open(self):
        task = Task(title="Work", department_id="d1", assigned_to="Bob")
        task.start()
        with pytest.raises(ValueError, match="open"):
            task.start()

    def test_cannot_complete_cancelled(self):
        task = Task(title="Work", department_id="d1", assigned_to="Bob")
        task.cancel()
        with pytest.raises(ValueError, match="open/in_progress"):
            task.complete()

    def test_cannot_cancel_completed(self):
        task = Task(title="Work", department_id="d1", assigned_to="Bob")
        task.complete()
        with pytest.raises(ValueError, match="Cannot cancel"):
            task.cancel()

    def test_task_with_mom_link(self):
        task = Task(
            title="Follow up",
            department_id="d1",
            assigned_to="Alice",
            mom_id="mom-123",
        )
        assert task.mom_id == "mom-123"

    def test_serialization(self):
        task = Task(
            title="Test",
            department_id="d1",
            assigned_to="Alice",
            mom_id="mom-1",
            priority=TaskPriority.CRITICAL,
        )
        data = task.to_dict()
        restored = Task.from_dict(data)
        assert restored.id == task.id
        assert restored.priority == TaskPriority.CRITICAL
        assert restored.mom_id == "mom-1"
