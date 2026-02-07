"""Seed demo data for the Task Manager web UI."""

from task_manager.models.task import TaskPriority
from task_manager.services.department_service import DepartmentService
from task_manager.services.mom_service import MOMService
from task_manager.services.task_service import TaskService
from task_manager.storage.json_store import JsonStore

store = JsonStore(data_dir="data")
ds = DepartmentService(store)
ms = MOMService(store)
ts = TaskService(store)

# Departments
eng = ds.create_department("Engineering", "Software development team")
mkt = ds.create_department("Marketing", "Brand and campaigns team")
hr = ds.create_department("HR", "Human resources department")

# Meetings
m1 = ms.create_meeting("Sprint Planning - Q1 2026", eng.id, "2026-02-06", ["Alice", "Bob", "Carol", "Dave"], "Conference Room A")
m2 = ms.create_meeting("Architecture Review", eng.id, "2026-02-07", ["Alice", "Eve"], "Virtual - Zoom")
m3 = ms.create_meeting("Campaign Strategy Review", mkt.id, "2026-02-05", ["Frank", "Grace"], "Room B")

# MOM 1 - Validated
mom1 = ms.create_mom(m1.id, "Alice", "Sprint planning session to finalize Q1 deliverables and team assignments")
ms.add_agenda_item(mom1.id, "Q1 Feature Roadmap", "Reviewed priorities: login redesign, API v2, dashboard overhaul", "Login redesign approved for Sprint 1; API v2 for Sprint 2")
ms.add_agenda_item(mom1.id, "Resource Allocation", "Bob and Carol full-time; Dave at 50% capacity", "Bob assigned to API v2; Carol to login redesign")
ms.add_agenda_item(mom1.id, "Testing Strategy", "Current coverage at 62%, target is 80%", "Alice to set up CI/CD pipeline by Feb 10")
ms.submit_for_review(mom1.id)
ms.validate_mom(mom1.id, "Manager Bob")

# MOM 2 - Draft
mom2 = ms.create_mom(m2.id, "Eve", "Architecture review for microservices migration")
ms.add_agenda_item(mom2.id, "Service Boundaries", "Discussed splitting monolith into 4 services", "Auth, Users, Products, Orders services identified")

# MOM 3 - Pending Review
mom3 = ms.create_mom(m3.id, "Grace", "Q1 campaign planning and budget allocation")
ms.add_agenda_item(mom3.id, "Social Media Campaign", "Plan 3-month social media push", "Budget $15k approved for Q1")
ms.add_agenda_item(mom3.id, "Content Calendar", "Monthly content themes discussed", "Frank to prepare calendar by Feb 12")
ms.submit_for_review(mom3.id)

# Tasks linked to MOM 1
t1 = ts.create_task("Implement login redesign UI", eng.id, "Carol", "Redesign the login page per Sprint Planning decision", mom1.id, "2026-02-20", TaskPriority.HIGH)
t2 = ts.create_task("Build API v2 endpoints", eng.id, "Bob", "Develop REST API v2 for mobile clients", mom1.id, "2026-03-01", TaskPriority.CRITICAL)
t3 = ts.create_task("Set up CI/CD pipeline", eng.id, "Alice", "Configure automated testing and deployment", mom1.id, "2026-02-10", TaskPriority.HIGH)
ts.start_task(t3.id)
ts.complete_task(t3.id)
ts.start_task(t2.id)

# Tasks linked to MOM 3
t4 = ts.create_task("Prepare content calendar", mkt.id, "Frank", "Monthly content themes for Q1", mom3.id, "2026-02-12", TaskPriority.MEDIUM)
t5 = ts.create_task("Design social media graphics", mkt.id, "Grace", "Create visuals for social campaign", mom3.id, "2026-02-15", TaskPriority.HIGH)

# Standalone tasks
t6 = ts.create_task("Fix production logging issue", eng.id, "Eve", "Resolve log rotation failure", None, "2026-02-08", TaskPriority.CRITICAL)
ts.start_task(t6.id)
t7 = ts.create_task("Update employee handbook", hr.id, "Diana", "Annual policy updates for 2026", None, "2026-03-15", TaskPriority.LOW)

print("Demo data seeded successfully!")
print(f"  {len(ds.list_departments())} departments")
print(f"  {len(ms.list_meetings())} meetings")
print(f"  {len(ms.list_moms())} MOMs")
print(f"  {len(ts.list_tasks())} tasks")
