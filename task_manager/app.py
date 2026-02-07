"""Main application entry point providing a CLI for the Task Manager."""

import argparse
import sys
from typing import Optional

from task_manager.models.mom import MOMStatus
from task_manager.models.task import TaskPriority, TaskStatus
from task_manager.services.department_service import DepartmentService
from task_manager.services.mom_service import MOMService
from task_manager.services.task_service import TaskService
from task_manager.storage.json_store import JsonStore


class TaskManagerApp:
    """Facade that wires up all services and provides the CLI."""

    def __init__(self, data_dir: str = "data"):
        self.store = JsonStore(data_dir=data_dir)
        self.dept_service = DepartmentService(self.store)
        self.mom_service = MOMService(self.store)
        self.task_service = TaskService(self.store)

    # -- Department commands --

    def cmd_create_department(self, args: argparse.Namespace) -> None:
        dept = self.dept_service.create_department(args.name, args.description or "")
        print(f"Department created: {dept.name} (ID: {dept.id})")

    def cmd_list_departments(self, _args: argparse.Namespace) -> None:
        depts = self.dept_service.list_departments()
        if not depts:
            print("No departments found.")
            return
        for d in depts:
            print(f"  [{d.id[:8]}] {d.name} - {d.description}")

    # -- Meeting commands --

    def cmd_create_meeting(self, args: argparse.Namespace) -> None:
        meeting = self.mom_service.create_meeting(
            title=args.title,
            department_id=args.department_id,
            date=args.date,
            attendees=args.attendees or [],
            location=args.location or "",
        )
        print(f"Meeting created: {meeting.title} (ID: {meeting.id})")

    def cmd_list_meetings(self, args: argparse.Namespace) -> None:
        meetings = self.mom_service.list_meetings(
            department_id=getattr(args, "department_id", None)
        )
        if not meetings:
            print("No meetings found.")
            return
        for m in meetings:
            print(f"  [{m.id[:8]}] {m.date} - {m.title} ({len(m.attendees)} attendees)")

    # -- MOM commands --

    def cmd_create_mom(self, args: argparse.Namespace) -> None:
        mom = self.mom_service.create_mom(
            meeting_id=args.meeting_id,
            prepared_by=args.prepared_by,
            summary=args.summary or "",
        )
        print(f"MOM created (ID: {mom.id}) for meeting {args.meeting_id[:8]}")

    def cmd_add_agenda_item(self, args: argparse.Namespace) -> None:
        mom = self.mom_service.add_agenda_item(
            mom_id=args.mom_id,
            title=args.title,
            discussion=args.discussion or "",
            decisions=args.decisions or "",
        )
        print(f"Agenda item added to MOM {mom.id[:8]}")

    def cmd_submit_mom(self, args: argparse.Namespace) -> None:
        mom = self.mom_service.submit_for_review(args.mom_id)
        print(f"MOM {mom.id[:8]} submitted for review.")

    def cmd_validate_mom(self, args: argparse.Namespace) -> None:
        mom = self.mom_service.validate_mom(args.mom_id, args.validated_by)
        print(f"MOM {mom.id[:8]} validated by {args.validated_by}.")

    def cmd_reject_mom(self, args: argparse.Namespace) -> None:
        mom = self.mom_service.reject_mom(args.mom_id, args.rejected_by, args.reason)
        print(f"MOM {mom.id[:8]} rejected: {args.reason}")

    def cmd_revise_mom(self, args: argparse.Namespace) -> None:
        mom = self.mom_service.revise_mom(args.mom_id)
        print(f"MOM {mom.id[:8]} moved back to draft for revision.")

    def cmd_show_mom(self, args: argparse.Namespace) -> None:
        mom = self.mom_service.get_mom(args.mom_id)
        if not mom:
            print(f"MOM '{args.mom_id}' not found.")
            return
        meeting = self.mom_service.get_meeting(mom.meeting_id)
        meeting_title = meeting.title if meeting else "Unknown"
        print(f"MOM: {mom.id}")
        print(f"  Meeting: {meeting_title}")
        print(f"  Prepared by: {mom.prepared_by}")
        print(f"  Status: {mom.status.value}")
        print(f"  Summary: {mom.summary or '(none)'}")
        if mom.agenda_items:
            print("  Agenda Items:")
            for i, item in enumerate(mom.agenda_items, 1):
                print(f"    {i}. {item.title}")
                if item.discussion:
                    print(f"       Discussion: {item.discussion}")
                if item.decisions:
                    print(f"       Decisions: {item.decisions}")
        if mom.validated_by:
            print(f"  Validated/Rejected by: {mom.validated_by}")
        if mom.rejection_reason:
            print(f"  Rejection reason: {mom.rejection_reason}")

    def cmd_list_moms(self, args: argparse.Namespace) -> None:
        status = MOMStatus(args.status) if args.status else None
        moms = self.mom_service.list_moms(status=status)
        if not moms:
            print("No MOMs found.")
            return
        for mom in moms:
            print(f"  [{mom.id[:8]}] Meeting:{mom.meeting_id[:8]} "
                  f"Status:{mom.status.value} By:{mom.prepared_by}")

    # -- Task commands --

    def cmd_create_task(self, args: argparse.Namespace) -> None:
        priority = TaskPriority(args.priority) if args.priority else TaskPriority.MEDIUM
        task = self.task_service.create_task(
            title=args.title,
            department_id=args.department_id,
            assigned_to=args.assigned_to,
            description=args.description or "",
            mom_id=args.mom_id or None,
            due_date=args.due_date or None,
            priority=priority,
        )
        print(f"Task created: {task.title} (ID: {task.id})")

    def cmd_list_tasks(self, args: argparse.Namespace) -> None:
        status = TaskStatus(args.status) if args.status else None
        tasks = self.task_service.list_tasks(
            department_id=getattr(args, "department_id", None),
            assigned_to=getattr(args, "assigned_to", None),
            status=status,
            mom_id=getattr(args, "mom_id", None),
        )
        if not tasks:
            print("No tasks found.")
            return
        for t in tasks:
            mom_info = f" MOM:{t.mom_id[:8]}" if t.mom_id else ""
            print(f"  [{t.id[:8]}] [{t.priority.value.upper()}] {t.title} "
                  f"-> {t.assigned_to} ({t.status.value}){mom_info}")

    def cmd_start_task(self, args: argparse.Namespace) -> None:
        task = self.task_service.start_task(args.task_id)
        print(f"Task {task.id[:8]} is now in progress.")

    def cmd_complete_task(self, args: argparse.Namespace) -> None:
        task = self.task_service.complete_task(args.task_id)
        print(f"Task {task.id[:8]} marked as completed.")

    def cmd_cancel_task(self, args: argparse.Namespace) -> None:
        task = self.task_service.cancel_task(args.task_id)
        print(f"Task {task.id[:8]} cancelled.")

    def cmd_show_task(self, args: argparse.Namespace) -> None:
        task = self.task_service.get_task(args.task_id)
        if not task:
            print(f"Task '{args.task_id}' not found.")
            return
        print(f"Task: {task.id}")
        print(f"  Title: {task.title}")
        print(f"  Description: {task.description or '(none)'}")
        print(f"  Department: {task.department_id[:8]}")
        print(f"  Assigned to: {task.assigned_to}")
        print(f"  Status: {task.status.value}")
        print(f"  Priority: {task.priority.value}")
        print(f"  Due date: {task.due_date or '(none)'}")
        if task.mom_id:
            print(f"  Linked MOM: {task.mom_id[:8]}")

    def cmd_mom_tasks(self, args: argparse.Namespace) -> None:
        """List all tasks linked to a specific MOM."""
        tasks = self.task_service.get_tasks_for_mom(args.mom_id)
        if not tasks:
            print(f"No tasks linked to MOM {args.mom_id[:8]}.")
            return
        print(f"Tasks for MOM {args.mom_id[:8]}:")
        for t in tasks:
            print(f"  [{t.id[:8]}] [{t.priority.value.upper()}] {t.title} "
                  f"-> {t.assigned_to} ({t.status.value})")


def build_parser(app: TaskManagerApp) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="task-manager",
        description="Task Manager with Minutes of Meeting (MOM) Module",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # -- Department --
    p = subparsers.add_parser("create-dept", help="Create a department")
    p.add_argument("name")
    p.add_argument("--description", "-d", default="")
    p.set_defaults(func=app.cmd_create_department)

    p = subparsers.add_parser("list-depts", help="List departments")
    p.set_defaults(func=app.cmd_list_departments)

    # -- Meeting --
    p = subparsers.add_parser("create-meeting", help="Create a meeting")
    p.add_argument("title")
    p.add_argument("--department-id", required=True)
    p.add_argument("--date", required=True)
    p.add_argument("--attendees", nargs="*", default=[])
    p.add_argument("--location", default="")
    p.set_defaults(func=app.cmd_create_meeting)

    p = subparsers.add_parser("list-meetings", help="List meetings")
    p.add_argument("--department-id", default=None)
    p.set_defaults(func=app.cmd_list_meetings)

    # -- MOM --
    p = subparsers.add_parser("create-mom", help="Create minutes of meeting")
    p.add_argument("--meeting-id", required=True)
    p.add_argument("--prepared-by", required=True)
    p.add_argument("--summary", default="")
    p.set_defaults(func=app.cmd_create_mom)

    p = subparsers.add_parser("add-agenda", help="Add agenda item to a MOM")
    p.add_argument("--mom-id", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--discussion", default="")
    p.add_argument("--decisions", default="")
    p.set_defaults(func=app.cmd_add_agenda_item)

    p = subparsers.add_parser("submit-mom", help="Submit MOM for review")
    p.add_argument("mom_id")
    p.set_defaults(func=app.cmd_submit_mom)

    p = subparsers.add_parser("validate-mom", help="Validate/approve a MOM")
    p.add_argument("mom_id")
    p.add_argument("--validated-by", required=True)
    p.set_defaults(func=app.cmd_validate_mom)

    p = subparsers.add_parser("reject-mom", help="Reject a MOM")
    p.add_argument("mom_id")
    p.add_argument("--rejected-by", required=True)
    p.add_argument("--reason", required=True)
    p.set_defaults(func=app.cmd_reject_mom)

    p = subparsers.add_parser("revise-mom", help="Move rejected MOM back to draft")
    p.add_argument("mom_id")
    p.set_defaults(func=app.cmd_revise_mom)

    p = subparsers.add_parser("show-mom", help="Show MOM details")
    p.add_argument("mom_id")
    p.set_defaults(func=app.cmd_show_mom)

    p = subparsers.add_parser("list-moms", help="List all MOMs")
    p.add_argument("--status", choices=["draft", "pending_review", "validated", "rejected"], default=None)
    p.set_defaults(func=app.cmd_list_moms)

    # -- Task --
    p = subparsers.add_parser("create-task", help="Create a task")
    p.add_argument("title")
    p.add_argument("--department-id", required=True)
    p.add_argument("--assigned-to", required=True)
    p.add_argument("--description", default="")
    p.add_argument("--mom-id", default=None)
    p.add_argument("--due-date", default=None)
    p.add_argument("--priority", choices=["low", "medium", "high", "critical"], default="medium")
    p.set_defaults(func=app.cmd_create_task)

    p = subparsers.add_parser("list-tasks", help="List tasks")
    p.add_argument("--department-id", default=None)
    p.add_argument("--assigned-to", default=None)
    p.add_argument("--status", choices=["open", "in_progress", "completed", "cancelled"], default=None)
    p.add_argument("--mom-id", default=None)
    p.set_defaults(func=app.cmd_list_tasks)

    p = subparsers.add_parser("start-task", help="Start a task")
    p.add_argument("task_id")
    p.set_defaults(func=app.cmd_start_task)

    p = subparsers.add_parser("complete-task", help="Complete a task")
    p.add_argument("task_id")
    p.set_defaults(func=app.cmd_complete_task)

    p = subparsers.add_parser("cancel-task", help="Cancel a task")
    p.add_argument("task_id")
    p.set_defaults(func=app.cmd_cancel_task)

    p = subparsers.add_parser("show-task", help="Show task details")
    p.add_argument("task_id")
    p.set_defaults(func=app.cmd_show_task)

    p = subparsers.add_parser("mom-tasks", help="List tasks linked to a MOM")
    p.add_argument("mom_id")
    p.set_defaults(func=app.cmd_mom_tasks)

    return parser


def main(argv: Optional[list] = None) -> None:
    app = TaskManagerApp()
    parser = build_parser(app)
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        sys.exit(1)
    try:
        args.func(args)
    except (ValueError, Exception) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
