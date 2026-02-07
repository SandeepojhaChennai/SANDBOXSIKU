"""Flask web server providing REST API and serving the web UI."""

import os
from flask import Flask, jsonify, request, render_template

from task_manager.models.mom import MOMStatus
from task_manager.models.task import TaskPriority, TaskStatus
from task_manager.services.department_service import DepartmentService
from task_manager.services.mom_service import MOMService
from task_manager.services.task_service import TaskService
from task_manager.storage.json_store import JsonStore

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
)

store = JsonStore(data_dir="data")
dept_service = DepartmentService(store)
mom_service = MOMService(store)
task_service = TaskService(store)


# ── Page routes ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── Department API ───────────────────────────────────────────────────────────

@app.route("/api/departments", methods=["GET"])
def list_departments():
    depts = dept_service.list_departments()
    return jsonify([d.to_dict() for d in depts])


@app.route("/api/departments", methods=["POST"])
def create_department():
    data = request.get_json()
    dept = dept_service.create_department(
        name=data["name"],
        description=data.get("description", ""),
    )
    return jsonify(dept.to_dict()), 201


@app.route("/api/departments/<dept_id>", methods=["DELETE"])
def delete_department(dept_id):
    if dept_service.delete_department(dept_id):
        return jsonify({"deleted": True})
    return jsonify({"error": "Not found"}), 404


# ── Meeting API ──────────────────────────────────────────────────────────────

@app.route("/api/meetings", methods=["GET"])
def list_meetings():
    dept_id = request.args.get("department_id")
    meetings = mom_service.list_meetings(department_id=dept_id)
    return jsonify([m.to_dict() for m in meetings])


@app.route("/api/meetings", methods=["POST"])
def create_meeting():
    data = request.get_json()
    meeting = mom_service.create_meeting(
        title=data["title"],
        department_id=data["department_id"],
        date=data["date"],
        attendees=data.get("attendees", []),
        location=data.get("location", ""),
    )
    return jsonify(meeting.to_dict()), 201


@app.route("/api/meetings/<meeting_id>", methods=["GET"])
def get_meeting(meeting_id):
    meeting = mom_service.get_meeting(meeting_id)
    if not meeting:
        return jsonify({"error": "Not found"}), 404
    return jsonify(meeting.to_dict())


# ── MOM API ──────────────────────────────────────────────────────────────────

@app.route("/api/moms", methods=["GET"])
def list_moms():
    status = request.args.get("status")
    mom_status = MOMStatus(status) if status else None
    moms = mom_service.list_moms(status=mom_status)
    result = []
    for m in moms:
        d = m.to_dict()
        meeting = mom_service.get_meeting(m.meeting_id)
        d["meeting_title"] = meeting.title if meeting else "Unknown"
        result.append(d)
    return jsonify(result)


@app.route("/api/moms", methods=["POST"])
def create_mom():
    data = request.get_json()
    try:
        mom = mom_service.create_mom(
            meeting_id=data["meeting_id"],
            prepared_by=data["prepared_by"],
            summary=data.get("summary", ""),
        )
        return jsonify(mom.to_dict()), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/moms/<mom_id>", methods=["GET"])
def get_mom(mom_id):
    mom = mom_service.get_mom(mom_id)
    if not mom:
        return jsonify({"error": "Not found"}), 404
    d = mom.to_dict()
    meeting = mom_service.get_meeting(mom.meeting_id)
    d["meeting_title"] = meeting.title if meeting else "Unknown"
    tasks = task_service.get_tasks_for_mom(mom_id)
    d["tasks"] = [t.to_dict() for t in tasks]
    return jsonify(d)


@app.route("/api/moms/<mom_id>/agenda", methods=["POST"])
def add_agenda_item(mom_id):
    data = request.get_json()
    try:
        mom = mom_service.add_agenda_item(
            mom_id=mom_id,
            title=data["title"],
            discussion=data.get("discussion", ""),
            decisions=data.get("decisions", ""),
        )
        return jsonify(mom.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/moms/<mom_id>/submit", methods=["POST"])
def submit_mom(mom_id):
    try:
        mom = mom_service.submit_for_review(mom_id)
        return jsonify(mom.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/moms/<mom_id>/validate", methods=["POST"])
def validate_mom(mom_id):
    data = request.get_json()
    try:
        mom = mom_service.validate_mom(mom_id, data["validated_by"])
        return jsonify(mom.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/moms/<mom_id>/reject", methods=["POST"])
def reject_mom(mom_id):
    data = request.get_json()
    try:
        mom = mom_service.reject_mom(mom_id, data["rejected_by"], data["reason"])
        return jsonify(mom.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/moms/<mom_id>/revise", methods=["POST"])
def revise_mom(mom_id):
    try:
        mom = mom_service.revise_mom(mom_id)
        return jsonify(mom.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# ── Task API ─────────────────────────────────────────────────────────────────

@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    filters = {}
    for key in ("department_id", "assigned_to", "mom_id"):
        val = request.args.get(key)
        if val:
            filters[key] = val
    status = request.args.get("status")
    task_status = TaskStatus(status) if status else None
    tasks = task_service.list_tasks(
        department_id=filters.get("department_id"),
        assigned_to=filters.get("assigned_to"),
        status=task_status,
        mom_id=filters.get("mom_id"),
    )
    return jsonify([t.to_dict() for t in tasks])


@app.route("/api/tasks", methods=["POST"])
def create_task():
    data = request.get_json()
    priority = TaskPriority(data.get("priority", "medium"))
    task = task_service.create_task(
        title=data["title"],
        department_id=data["department_id"],
        assigned_to=data["assigned_to"],
        description=data.get("description", ""),
        mom_id=data.get("mom_id") or None,
        due_date=data.get("due_date") or None,
        priority=priority,
    )
    return jsonify(task.to_dict()), 201


@app.route("/api/tasks/<task_id>", methods=["GET"])
def get_task(task_id):
    task = task_service.get_task(task_id)
    if not task:
        return jsonify({"error": "Not found"}), 404
    return jsonify(task.to_dict())


@app.route("/api/tasks/<task_id>/start", methods=["POST"])
def start_task(task_id):
    try:
        task = task_service.start_task(task_id)
        return jsonify(task.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/tasks/<task_id>/complete", methods=["POST"])
def complete_task(task_id):
    try:
        task = task_service.complete_task(task_id)
        return jsonify(task.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/tasks/<task_id>/cancel", methods=["POST"])
def cancel_task(task_id):
    try:
        task = task_service.cancel_task(task_id)
        return jsonify(task.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    if task_service.delete_task(task_id):
        return jsonify({"deleted": True})
    return jsonify({"error": "Not found"}), 404


# ── Dashboard stats ──────────────────────────────────────────────────────────

@app.route("/api/dashboard", methods=["GET"])
def dashboard_stats():
    depts = dept_service.list_departments()
    meetings = mom_service.list_meetings()
    moms = mom_service.list_moms()
    tasks = task_service.list_tasks()

    task_by_status = {}
    for t in tasks:
        s = t.status.value
        task_by_status[s] = task_by_status.get(s, 0) + 1

    mom_by_status = {}
    for m in moms:
        s = m.status.value
        mom_by_status[s] = mom_by_status.get(s, 0) + 1

    task_by_priority = {}
    for t in tasks:
        p = t.priority.value
        task_by_priority[p] = task_by_priority.get(p, 0) + 1

    return jsonify({
        "total_departments": len(depts),
        "total_meetings": len(meetings),
        "total_moms": len(moms),
        "total_tasks": len(tasks),
        "tasks_by_status": task_by_status,
        "moms_by_status": mom_by_status,
        "tasks_by_priority": task_by_priority,
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
