"""Tests for service layer."""

import os
import shutil
import tempfile

import pytest

from task_manager.models.mom import MOMStatus
from task_manager.models.task import TaskPriority, TaskStatus
from task_manager.services.department_service import DepartmentService
from task_manager.services.mom_service import MOMService
from task_manager.services.task_service import TaskService
from task_manager.storage.json_store import JsonStore


@pytest.fixture
def store():
    """Create a temporary data directory for test isolation."""
    tmp_dir = tempfile.mkdtemp()
    s = JsonStore(data_dir=tmp_dir)
    yield s
    shutil.rmtree(tmp_dir)


@pytest.fixture
def dept_service(store):
    return DepartmentService(store)


@pytest.fixture
def mom_service(store):
    return MOMService(store)


@pytest.fixture
def task_service(store):
    return TaskService(store)


class TestDepartmentService:
    def test_create_and_list(self, dept_service):
        dept = dept_service.create_department("Engineering", "Dev team")
        depts = dept_service.list_departments()
        assert len(depts) == 1
        assert depts[0].name == "Engineering"

    def test_get_department(self, dept_service):
        dept = dept_service.create_department("HR")
        found = dept_service.get_department(dept.id)
        assert found is not None
        assert found.name == "HR"

    def test_delete_department(self, dept_service):
        dept = dept_service.create_department("Temp")
        assert dept_service.delete_department(dept.id) is True
        assert dept_service.get_department(dept.id) is None


class TestMOMService:
    def _create_meeting(self, mom_service, dept_id="dept-1"):
        return mom_service.create_meeting(
            title="Sprint Planning",
            department_id=dept_id,
            date="2026-02-06",
            attendees=["Alice", "Bob"],
        )

    def test_create_meeting_and_mom(self, mom_service):
        meeting = self._create_meeting(mom_service)
        mom = mom_service.create_mom(meeting.id, prepared_by="Alice", summary="Sprint plan")
        assert mom.meeting_id == meeting.id
        assert mom.status == MOMStatus.DRAFT

    def test_create_mom_for_nonexistent_meeting(self, mom_service):
        with pytest.raises(ValueError, match="not found"):
            mom_service.create_mom("nonexistent", prepared_by="Alice")

    def test_add_agenda_item(self, mom_service):
        meeting = self._create_meeting(mom_service)
        mom = mom_service.create_mom(meeting.id, prepared_by="Alice")
        updated = mom_service.add_agenda_item(
            mom.id, title="Budget", discussion="Reviewed costs", decisions="Approved"
        )
        assert len(updated.agenda_items) == 1
        assert updated.agenda_items[0].title == "Budget"

    def test_full_validation_flow(self, mom_service):
        meeting = self._create_meeting(mom_service)
        mom = mom_service.create_mom(meeting.id, prepared_by="Alice")
        mom_service.add_agenda_item(mom.id, title="Agenda 1")

        submitted = mom_service.submit_for_review(mom.id)
        assert submitted.status == MOMStatus.PENDING_REVIEW

        validated = mom_service.validate_mom(mom.id, "Manager")
        assert validated.status == MOMStatus.VALIDATED

    def test_rejection_and_revision_flow(self, mom_service):
        meeting = self._create_meeting(mom_service)
        mom = mom_service.create_mom(meeting.id, prepared_by="Alice")
        mom_service.submit_for_review(mom.id)

        rejected = mom_service.reject_mom(mom.id, "Manager", "Incomplete")
        assert rejected.status == MOMStatus.REJECTED

        revised = mom_service.revise_mom(mom.id)
        assert revised.status == MOMStatus.DRAFT

    def test_list_moms_by_status(self, mom_service):
        m1 = self._create_meeting(mom_service)
        m2 = mom_service.create_meeting("Retro", "dept-1", "2026-02-07")
        mom1 = mom_service.create_mom(m1.id, prepared_by="Alice")
        mom2 = mom_service.create_mom(m2.id, prepared_by="Bob")
        mom_service.submit_for_review(mom1.id)

        drafts = mom_service.list_moms(status=MOMStatus.DRAFT)
        pending = mom_service.list_moms(status=MOMStatus.PENDING_REVIEW)
        assert len(drafts) == 1
        assert len(pending) == 1

    def test_get_mom_by_meeting(self, mom_service):
        meeting = self._create_meeting(mom_service)
        mom = mom_service.create_mom(meeting.id, prepared_by="Alice")
        found = mom_service.get_mom_by_meeting(meeting.id)
        assert found is not None
        assert found.id == mom.id

    def test_update_summary(self, mom_service):
        meeting = self._create_meeting(mom_service)
        mom = mom_service.create_mom(meeting.id, prepared_by="Alice")
        updated = mom_service.update_summary(mom.id, "New summary")
        assert updated.summary == "New summary"

    def test_cannot_update_summary_after_submit(self, mom_service):
        meeting = self._create_meeting(mom_service)
        mom = mom_service.create_mom(meeting.id, prepared_by="Alice")
        mom_service.submit_for_review(mom.id)
        with pytest.raises(ValueError, match="draft"):
            mom_service.update_summary(mom.id, "Late update")

    def test_list_meetings_by_department(self, mom_service):
        mom_service.create_meeting("M1", "dept-1", "2026-02-06")
        mom_service.create_meeting("M2", "dept-2", "2026-02-07")
        meetings = mom_service.list_meetings(department_id="dept-1")
        assert len(meetings) == 1
        assert meetings[0].title == "M1"


class TestTaskService:
    def test_create_and_list_tasks(self, task_service):
        task = task_service.create_task(
            title="Fix bug",
            department_id="dept-1",
            assigned_to="Alice",
        )
        tasks = task_service.list_tasks()
        assert len(tasks) == 1
        assert tasks[0].title == "Fix bug"

    def test_create_task_linked_to_mom(self, task_service):
        task = task_service.create_task(
            title="Follow up on action item",
            department_id="dept-1",
            assigned_to="Bob",
            mom_id="mom-123",
        )
        assert task.mom_id == "mom-123"

    def test_get_tasks_for_mom(self, task_service):
        task_service.create_task("T1", "d1", "Alice", mom_id="mom-1")
        task_service.create_task("T2", "d1", "Bob", mom_id="mom-1")
        task_service.create_task("T3", "d1", "Carol", mom_id="mom-2")
        mom_tasks = task_service.get_tasks_for_mom("mom-1")
        assert len(mom_tasks) == 2

    def test_task_lifecycle(self, task_service):
        task = task_service.create_task("Work", "d1", "Alice")
        assert task.status == TaskStatus.OPEN

        started = task_service.start_task(task.id)
        assert started.status == TaskStatus.IN_PROGRESS

        completed = task_service.complete_task(task.id)
        assert completed.status == TaskStatus.COMPLETED

    def test_cancel_task(self, task_service):
        task = task_service.create_task("Work", "d1", "Alice")
        cancelled = task_service.cancel_task(task.id)
        assert cancelled.status == TaskStatus.CANCELLED

    def test_update_task(self, task_service):
        task = task_service.create_task("Old title", "d1", "Alice")
        updated = task_service.update_task(
            task.id,
            title="New title",
            priority=TaskPriority.HIGH,
        )
        assert updated.title == "New title"
        assert updated.priority == TaskPriority.HIGH

    def test_cannot_update_completed_task(self, task_service):
        task = task_service.create_task("Work", "d1", "Alice")
        task_service.complete_task(task.id)
        with pytest.raises(ValueError, match="Cannot update"):
            task_service.update_task(task.id, title="New")

    def test_delete_task(self, task_service):
        task = task_service.create_task("Temp", "d1", "Alice")
        assert task_service.delete_task(task.id) is True
        assert task_service.get_task(task.id) is None

    def test_filter_tasks_by_status(self, task_service):
        t1 = task_service.create_task("T1", "d1", "Alice")
        t2 = task_service.create_task("T2", "d1", "Bob")
        task_service.start_task(t1.id)
        open_tasks = task_service.list_tasks(status=TaskStatus.OPEN)
        in_progress = task_service.list_tasks(status=TaskStatus.IN_PROGRESS)
        assert len(open_tasks) == 1
        assert len(in_progress) == 1

    def test_filter_tasks_by_assignee(self, task_service):
        task_service.create_task("T1", "d1", "Alice")
        task_service.create_task("T2", "d1", "Bob")
        alice_tasks = task_service.list_tasks(assigned_to="Alice")
        assert len(alice_tasks) == 1
        assert alice_tasks[0].assigned_to == "Alice"
