# CLAUDE.md

This file provides guidance for AI assistants working with this codebase.

## Project Overview

Python-based Task Manager with an integrated Minutes of Meeting (MOM) management module. It provides a CLI for managing departments, meetings, meeting minutes, and action-item tasks with structured validation workflows. Version 1.0.0.

## Repository Structure

```
task_manager/
  __init__.py              # Package init, version string
  app.py                   # CLI entry point (argparse-based, 30+ subcommands)
  models/
    department.py          # Department dataclass
    meeting.py             # Meeting dataclass
    mom.py                 # MinutesOfMeeting + AgendaItem dataclasses, MOMStatus enum
    task.py                # Task dataclass, TaskStatus + TaskPriority enums
  services/
    department_service.py  # CRUD for departments
    mom_service.py         # Meeting + MOM operations, validation workflow
    task_service.py        # Task CRUD, filtering, lifecycle management
  storage/
    json_store.py          # JSON file-based persistence backend
tests/
  test_models.py           # Model unit tests (status transitions, serialization)
  test_services.py         # Service integration tests
  test_storage.py          # Storage layer persistence tests
```

## Architecture

Three-layer architecture with clear separation:

- **Models** (`task_manager/models/`): Pure Python `@dataclass` classes. Each model has `to_dict()` and `from_dict()` serialization methods. Status fields use `str, Enum` mixins. IDs are UUID v4 strings. Timestamps are ISO-format strings.
- **Services** (`task_manager/services/`): Business logic layer. Each service takes a `JsonStore` instance in its constructor. Services call model methods for state transitions and delegate persistence to the store.
- **Storage** (`task_manager/storage/json_store.py`): Single `JsonStore` class providing collection-based CRUD with an in-memory cache backed by JSON files in a `data/` directory.

## Key Domain Concepts

### Status Workflows

**MOM lifecycle** (defined in `MOMStatus` enum):
```
DRAFT → PENDING_REVIEW → VALIDATED
                       → REJECTED → DRAFT (revision cycle)
```
State transitions are enforced in model methods (`submit_for_review`, `validate`, `reject`, `revise`) which raise `ValueError` on invalid transitions.

**Task lifecycle** (defined in `TaskStatus` enum):
```
OPEN → IN_PROGRESS → COMPLETED
OPEN → COMPLETED (direct)
OPEN/IN_PROGRESS → CANCELLED
```

### Entity Relationships

- Meetings belong to a Department (via `department_id`)
- MOMs belong to a Meeting (via `meeting_id`)
- Tasks belong to a Department and optionally link to a MOM (via `mom_id`)

## Development Setup

### Prerequisites

- Python 3.7+ (uses `dataclasses`, `typing`, and f-strings)
- No external runtime dependencies (stdlib only)

### Install

```bash
pip install -r requirements.txt   # installs pytest
```

### Running the Application

```bash
python -m task_manager.app <subcommand> [args]
```

## Testing

### Running Tests

```bash
python -m pytest tests/ -v
```

There are 56 tests across three files. Tests use `tempfile.mkdtemp()` for isolated data directories, cleaned up with `shutil.rmtree()` in teardown.

### Test Structure

| File | Coverage | Test Count |
|------|----------|------------|
| `test_models.py` | Dataclass construction, status transitions, serialization round-trips, invalid transition errors | ~24 |
| `test_services.py` | Service CRUD, workflow orchestration, filtering, cross-entity operations | ~23 |
| `test_storage.py` | Insert/get/update/delete, find with filters, persistence across reload | 9 |

### Writing Tests

- Place tests in `tests/` with the `test_` prefix convention
- Use pytest fixtures; create a temporary data directory per test class
- Test both the happy path and error cases (especially `ValueError` on invalid state transitions)
- Service tests should instantiate a real `JsonStore` with a temp directory (no mocking)

## Code Conventions

- **Models**: Use `@dataclass` with `field(default_factory=...)` for mutable defaults and auto-generated IDs/timestamps
- **Enums**: Inherit from `(str, Enum)` so values serialize as plain strings
- **Serialization**: Every model implements `to_dict() -> dict` and `@classmethod from_dict(cls, data) -> Self`
- **Error handling**: Raise `ValueError` with descriptive messages for invalid operations (state transitions, duplicate IDs, missing records)
- **Type hints**: All function signatures use type annotations from `typing`
- **Docstrings**: Module-level and class-level docstrings on all files and classes
- **Naming**: snake_case for functions/variables, PascalCase for classes, UPPER_SNAKE_CASE for enum members
- **No external linter/formatter configured**: Follow the existing style (4-space indentation, double quotes for docstrings, consistent trailing commas in multi-line structures)

## Storage Details

- Data is persisted to JSON files at `data/<collection>.json` (gitignored)
- Collections: `departments`, `meetings`, `mom`, `tasks`
- Records are keyed by UUID string in an in-memory dict, flushed to disk on every write
- The `find()` method supports filtering by any field via keyword arguments

## Common Tasks

### Adding a New Model

1. Create a dataclass in `task_manager/models/` with `to_dict`/`from_dict` methods
2. Create a service in `task_manager/services/` accepting `JsonStore`
3. Add CLI subcommands in `app.py`
4. Add tests in `tests/`

### Adding a New Status Transition

1. Add the transition method to the model class
2. Enforce the precondition with a `ValueError` guard
3. Update `updated_at` timestamp
4. Expose through the corresponding service
5. Add tests for both valid and invalid transitions

### Adding a New CLI Command

1. Add a subparser in the `_setup_parser` method of `TaskManagerApp` in `app.py`
2. Add a handler method prefixed with `_handle_`
3. Wire the handler in the `run()` dispatch logic
