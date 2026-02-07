# Task Manager with MOM Module

A task management system with an integrated Minutes of Meeting (MOM) management module. Departments can create, track, and validate meeting minutes and their associated tasks within a single system.

## Features

- **Department Management** - Create and manage organizational departments
- **Meeting Tracking** - Record meetings with attendees, dates, and locations
- **Minutes of Meeting (MOM)** - Create structured meeting minutes with agenda items, discussions, and decisions
- **MOM Validation Workflow** - Draft -> Pending Review -> Validated/Rejected -> Revision cycle
- **Task Management** - Create, assign, and track tasks with priority levels
- **MOM-Task Linking** - Link tasks directly to meeting minutes for traceability

## Project Structure

```
task_manager/
  models/         # Data models (Department, Meeting, MOM, Task)
  services/       # Business logic (MOMService, TaskService, DepartmentService)
  storage/        # JSON file-based persistence
  app.py          # CLI entry point
tests/            # Unit tests (56 tests)
```

## Usage

```bash
# Department management
python -m task_manager.app create-dept "Engineering" -d "Software team"
python -m task_manager.app list-depts

# Meeting management
python -m task_manager.app create-meeting "Sprint Planning" --department-id <DEPT_ID> --date 2026-02-06
python -m task_manager.app list-meetings

# MOM management
python -m task_manager.app create-mom --meeting-id <MEETING_ID> --prepared-by "Alice"
python -m task_manager.app add-agenda --mom-id <MOM_ID> --title "Budget Review" --discussion "Reviewed Q1"
python -m task_manager.app submit-mom <MOM_ID>
python -m task_manager.app validate-mom <MOM_ID> --validated-by "Manager"
python -m task_manager.app show-mom <MOM_ID>

# Task management
python -m task_manager.app create-task "Fix login bug" --department-id <DEPT_ID> --assigned-to "Bob" --priority high
python -m task_manager.app create-task "Follow up" --department-id <DEPT_ID> --assigned-to "Alice" --mom-id <MOM_ID>
python -m task_manager.app start-task <TASK_ID>
python -m task_manager.app complete-task <TASK_ID>
python -m task_manager.app mom-tasks <MOM_ID>
```

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```
