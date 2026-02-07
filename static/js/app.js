/* ── Helpers ───────────────────────────────────────────────────────────── */
const $ = (s, p = document) => p.querySelector(s);
const $$ = (s, p = document) => [...p.querySelectorAll(s)];

async function api(path, opts = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json", ...opts.headers },
    ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

function toast(msg, type = "success") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = msg;
  $("#toastContainer").appendChild(el);
  setTimeout(() => { el.style.opacity = "0"; setTimeout(() => el.remove(), 300); }, 3000);
}

function shortId(id) { return id ? id.substring(0, 8) : "-"; }

function badge(text, prefix) {
  const cls = prefix ? `badge-${text}` : `badge-${text}`;
  return `<span class="badge ${cls}">${text.replace("_", " ")}</span>`;
}

/* ── Modal ─────────────────────────────────────────────────────────────── */
function openModal(title, bodyHtml) {
  $("#modalTitle").textContent = title;
  $("#modalBody").innerHTML = bodyHtml;
  $("#modalOverlay").classList.add("active");
}
function closeModal() { $("#modalOverlay").classList.remove("active"); }
$("#modalClose").onclick = closeModal;
$("#modalOverlay").addEventListener("click", e => { if (e.target === $("#modalOverlay")) closeModal(); });

/* ── Navigation ───────────────────────────────────────────────────────── */
const pages = { dashboard: renderDashboard, departments: renderDepartments, meetings: renderMeetings, moms: renderMoms, tasks: renderTasks };
let currentPage = "dashboard";

$$(".nav-item").forEach(item => {
  item.addEventListener("click", e => {
    e.preventDefault();
    navigate(item.dataset.page);
    $("#sidebar").classList.remove("open");
  });
});
$("#menuToggle").onclick = () => $("#sidebar").classList.toggle("open");

function navigate(page) {
  currentPage = page;
  $$(".nav-item").forEach(n => n.classList.toggle("active", n.dataset.page === page));
  $("#pageTitle").textContent = { dashboard: "Dashboard", departments: "Departments", meetings: "Meetings", moms: "Minutes of Meeting", tasks: "Tasks" }[page];
  pages[page]();
}

/* ── Dashboard ────────────────────────────────────────────────────────── */
async function renderDashboard() {
  const d = await api("/dashboard");
  const area = $("#contentArea");

  area.innerHTML = `
    <div class="stat-grid">
      <div class="stat-card"><div class="stat-icon blue">&#x1f3e2;</div><div><div class="stat-value">${d.total_departments}</div><div class="stat-label">Departments</div></div></div>
      <div class="stat-card"><div class="stat-icon purple">&#x1f4c5;</div><div><div class="stat-value">${d.total_meetings}</div><div class="stat-label">Meetings</div></div></div>
      <div class="stat-card"><div class="stat-icon orange">&#x1f4cb;</div><div><div class="stat-value">${d.total_moms}</div><div class="stat-label">Minutes (MOM)</div></div></div>
      <div class="stat-card"><div class="stat-icon green">&#x2705;</div><div><div class="stat-value">${d.total_tasks}</div><div class="stat-label">Tasks</div></div></div>
    </div>
    <div class="chart-grid">
      <div class="card">
        <div class="card-header"><h3>Tasks by Status</h3></div>
        <div class="card-body">${barChart(d.tasks_by_status, d.total_tasks)}</div>
      </div>
      <div class="card">
        <div class="card-header"><h3>Tasks by Priority</h3></div>
        <div class="card-body">${barChart(d.tasks_by_priority, d.total_tasks)}</div>
      </div>
      <div class="card">
        <div class="card-header"><h3>MOM by Status</h3></div>
        <div class="card-body">${barChart(d.moms_by_status, d.total_moms)}</div>
      </div>
    </div>
  `;
}

function barChart(data, total) {
  if (!total) return '<div class="empty-state"><p>No data yet</p></div>';
  return '<div class="bar-chart">' + Object.entries(data).map(([k, v]) => {
    const pct = Math.max(Math.round(v / total * 100), 8);
    return `<div class="bar-row"><span class="bar-label">${k.replace("_"," ")}</span><div class="bar-track"><div class="bar-fill ${k}" style="width:${pct}%">${v}</div></div></div>`;
  }).join("") + "</div>";
}

/* ── Departments ──────────────────────────────────────────────────────── */
async function renderDepartments() {
  const depts = await api("/departments");
  const area = $("#contentArea");
  area.innerHTML = `
    <div class="card">
      <div class="card-header"><h3>All Departments</h3><button class="btn btn-primary" onclick="showCreateDept()">+ New Department</button></div>
      <div class="card-body"><div class="table-wrap">
        ${depts.length ? `<table><thead><tr><th>ID</th><th>Name</th><th>Description</th><th>Created</th><th></th></tr></thead><tbody>
          ${depts.map(d => `<tr><td><code>${shortId(d.id)}</code></td><td><strong>${esc(d.name)}</strong></td><td>${esc(d.description) || "<em style='color:var(--text-muted)'>-</em>"}</td><td>${fmtDate(d.created_at)}</td><td><button class="btn-icon" title="Delete" onclick="deleteDept('${d.id}')"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="var(--danger)" stroke-width="2"><polyline points="3,6 5,6 21,6"/><path d="M19,6V20a2,2,0,0,1-2,2H7a2,2,0,0,1-2-2V6M8,6V4a2,2,0,0,1,2-2h4a2,2,0,0,1,2,2V6"/></svg></button></td></tr>`).join("")}
        </tbody></table>` : emptyState("No departments yet. Create one to get started.")}
      </div></div>
    </div>`;
}

window.showCreateDept = () => {
  openModal("New Department", `
    <div class="form-group"><label>Name *</label><input id="fDeptName" placeholder="e.g. Engineering"></div>
    <div class="form-group"><label>Description</label><input id="fDeptDesc" placeholder="Optional description"></div>
    <div class="modal-actions"><button class="btn btn-outline" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="createDept()">Create</button></div>
  `);
};
window.createDept = async () => {
  const name = $("#fDeptName").value.trim();
  if (!name) return toast("Name is required", "error");
  await api("/departments", { method: "POST", body: { name, description: $("#fDeptDesc").value.trim() } });
  closeModal(); toast("Department created"); renderDepartments();
};
window.deleteDept = async (id) => {
  if (!confirm("Delete this department?")) return;
  await api(`/departments/${id}`, { method: "DELETE" });
  toast("Department deleted"); renderDepartments();
};

/* ── Meetings ─────────────────────────────────────────────────────────── */
async function renderMeetings() {
  const [meetings, depts] = await Promise.all([api("/meetings"), api("/departments")]);
  const deptMap = Object.fromEntries(depts.map(d => [d.id, d.name]));
  const area = $("#contentArea");
  area.innerHTML = `
    <div class="card">
      <div class="card-header"><h3>All Meetings</h3><button class="btn btn-primary" onclick="showCreateMeeting()">+ New Meeting</button></div>
      <div class="card-body"><div class="table-wrap">
        ${meetings.length ? `<table><thead><tr><th>ID</th><th>Title</th><th>Department</th><th>Date</th><th>Attendees</th><th>Location</th></tr></thead><tbody>
          ${meetings.map(m => `<tr><td><code>${shortId(m.id)}</code></td><td><strong>${esc(m.title)}</strong></td><td>${esc(deptMap[m.department_id] || shortId(m.department_id))}</td><td>${m.date}</td><td>${m.attendees.length ? m.attendees.join(", ") : "-"}</td><td>${esc(m.location) || "-"}</td></tr>`).join("")}
        </tbody></table>` : emptyState("No meetings yet.")}
      </div></div>
    </div>`;
}

window.showCreateMeeting = async () => {
  const depts = await api("/departments");
  if (!depts.length) { toast("Create a department first", "error"); return; }
  openModal("New Meeting", `
    <div class="form-group"><label>Title *</label><input id="fMeetTitle" placeholder="e.g. Sprint Planning"></div>
    <div class="form-row">
      <div class="form-group"><label>Department *</label><select id="fMeetDept">${depts.map(d => `<option value="${d.id}">${esc(d.name)}</option>`).join("")}</select></div>
      <div class="form-group"><label>Date *</label><input id="fMeetDate" type="date"></div>
    </div>
    <div class="form-group"><label>Attendees (comma-separated)</label><input id="fMeetAttendees" placeholder="Alice, Bob, Carol"></div>
    <div class="form-group"><label>Location</label><input id="fMeetLocation" placeholder="e.g. Room A / Virtual"></div>
    <div class="modal-actions"><button class="btn btn-outline" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="createMeeting()">Create</button></div>
  `);
};
window.createMeeting = async () => {
  const title = $("#fMeetTitle").value.trim();
  const date = $("#fMeetDate").value;
  if (!title || !date) return toast("Title and date are required", "error");
  const attendees = $("#fMeetAttendees").value.split(",").map(s => s.trim()).filter(Boolean);
  await api("/meetings", { method: "POST", body: { title, department_id: $("#fMeetDept").value, date, attendees, location: $("#fMeetLocation").value.trim() } });
  closeModal(); toast("Meeting created"); renderMeetings();
};

/* ── MOMs ─────────────────────────────────────────────────────────────── */
async function renderMoms() {
  const moms = await api("/moms");
  const area = $("#contentArea");
  area.innerHTML = `
    <div class="card">
      <div class="card-header"><h3>All Minutes of Meeting</h3><button class="btn btn-primary" onclick="showCreateMom()">+ New MOM</button></div>
      <div class="card-body"><div class="table-wrap">
        ${moms.length ? `<table><thead><tr><th>ID</th><th>Meeting</th><th>Prepared By</th><th>Status</th><th>Created</th><th>Actions</th></tr></thead><tbody>
          ${moms.map(m => `<tr>
            <td><code>${shortId(m.id)}</code></td>
            <td><a href="#" onclick="viewMom('${m.id}');return false" style="color:var(--primary);font-weight:600">${esc(m.meeting_title)}</a></td>
            <td>${esc(m.prepared_by)}</td>
            <td>${badge(m.status)}</td>
            <td>${fmtDate(m.created_at)}</td>
            <td><div class="action-btns">${momActions(m)}</div></td>
          </tr>`).join("")}
        </tbody></table>` : emptyState("No minutes of meeting yet. Create one from a meeting.")}
      </div></div>
    </div>`;
}

function momActions(m) {
  let btns = `<button class="btn btn-sm btn-outline" onclick="viewMom('${m.id}')">View</button>`;
  if (m.status === "draft") {
    btns += `<button class="btn btn-sm btn-primary" onclick="showAddAgenda('${m.id}')">+ Agenda</button>`;
    btns += `<button class="btn btn-sm btn-warning" onclick="submitMom('${m.id}')">Submit</button>`;
  }
  if (m.status === "pending_review") {
    btns += `<button class="btn btn-sm btn-success" onclick="showValidateMom('${m.id}')">Validate</button>`;
    btns += `<button class="btn btn-sm btn-danger" onclick="showRejectMom('${m.id}')">Reject</button>`;
  }
  if (m.status === "rejected") {
    btns += `<button class="btn btn-sm btn-primary" onclick="reviseMom('${m.id}')">Revise</button>`;
  }
  return btns;
}

window.showCreateMom = async () => {
  const meetings = await api("/meetings");
  if (!meetings.length) { toast("Create a meeting first", "error"); return; }
  openModal("New Minutes of Meeting", `
    <div class="form-group"><label>Meeting *</label><select id="fMomMeeting">${meetings.map(m => `<option value="${m.id}">${esc(m.title)} (${m.date})</option>`).join("")}</select></div>
    <div class="form-group"><label>Prepared By *</label><input id="fMomBy" placeholder="e.g. Alice"></div>
    <div class="form-group"><label>Summary</label><textarea id="fMomSummary" placeholder="Brief summary of the meeting"></textarea></div>
    <div class="modal-actions"><button class="btn btn-outline" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="createMom()">Create</button></div>
  `);
};
window.createMom = async () => {
  const prepared_by = $("#fMomBy").value.trim();
  if (!prepared_by) return toast("Prepared by is required", "error");
  await api("/moms", { method: "POST", body: { meeting_id: $("#fMomMeeting").value, prepared_by, summary: $("#fMomSummary").value.trim() } });
  closeModal(); toast("MOM created"); renderMoms();
};
window.showAddAgenda = (momId) => {
  openModal("Add Agenda Item", `
    <div class="form-group"><label>Title *</label><input id="fAgTitle" placeholder="e.g. Budget Review"></div>
    <div class="form-group"><label>Discussion</label><textarea id="fAgDisc" placeholder="What was discussed"></textarea></div>
    <div class="form-group"><label>Decisions</label><textarea id="fAgDec" placeholder="What was decided"></textarea></div>
    <div class="modal-actions"><button class="btn btn-outline" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="addAgenda('${momId}')">Add</button></div>
  `);
};
window.addAgenda = async (momId) => {
  const title = $("#fAgTitle").value.trim();
  if (!title) return toast("Title is required", "error");
  await api(`/moms/${momId}/agenda`, { method: "POST", body: { title, discussion: $("#fAgDisc").value.trim(), decisions: $("#fAgDec").value.trim() } });
  closeModal(); toast("Agenda item added");
  if (currentPage === "moms") renderMoms(); else viewMom(momId);
};
window.submitMom = async (id) => {
  await api(`/moms/${id}/submit`, { method: "POST" });
  toast("MOM submitted for review"); renderMoms();
};
window.showValidateMom = (id) => {
  openModal("Validate MOM", `
    <div class="form-group"><label>Validated By *</label><input id="fValBy" placeholder="e.g. Manager Bob"></div>
    <div class="modal-actions"><button class="btn btn-outline" onclick="closeModal()">Cancel</button><button class="btn btn-success" onclick="validateMom('${id}')">Validate</button></div>
  `);
};
window.validateMom = async (id) => {
  const by = $("#fValBy").value.trim();
  if (!by) return toast("Name is required", "error");
  await api(`/moms/${id}/validate`, { method: "POST", body: { validated_by: by } });
  closeModal(); toast("MOM validated!"); renderMoms();
};
window.showRejectMom = (id) => {
  openModal("Reject MOM", `
    <div class="form-group"><label>Rejected By *</label><input id="fRejBy" placeholder="e.g. Manager Bob"></div>
    <div class="form-group"><label>Reason *</label><textarea id="fRejReason" placeholder="Why is this being rejected?"></textarea></div>
    <div class="modal-actions"><button class="btn btn-outline" onclick="closeModal()">Cancel</button><button class="btn btn-danger" onclick="rejectMom('${id}')">Reject</button></div>
  `);
};
window.rejectMom = async (id) => {
  const by = $("#fRejBy").value.trim(), reason = $("#fRejReason").value.trim();
  if (!by || !reason) return toast("All fields required", "error");
  await api(`/moms/${id}/reject`, { method: "POST", body: { rejected_by: by, reason } });
  closeModal(); toast("MOM rejected"); renderMoms();
};
window.reviseMom = async (id) => {
  await api(`/moms/${id}/revise`, { method: "POST" });
  toast("MOM moved back to draft"); renderMoms();
};

/* ── MOM Detail View ──────────────────────────────────────────────────── */
window.viewMom = async (id) => {
  const m = await api(`/moms/${id}`);
  const area = $("#contentArea");
  const steps = ["draft", "pending_review", "validated"];
  const isRejected = m.status === "rejected";

  area.innerHTML = `
    <div class="detail-header">
      <button class="back-btn" onclick="renderMoms()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15,18 9,12 15,6"/></svg></button>
      <span class="detail-title">${esc(m.meeting_title)} &mdash; Minutes</span>
    </div>

    <div class="workflow-bar">
      ${steps.map(s => {
        const idx = steps.indexOf(s), curIdx = steps.indexOf(m.status);
        let cls = "";
        if (isRejected && s === "pending_review") cls = "rejected-step";
        else if (idx < curIdx) cls = "done";
        else if (s === m.status) cls = "current";
        return `<div class="workflow-step ${cls}">${s.replace("_"," ")}</div>`;
      }).join("")}
    </div>

    <div class="detail-meta">
      <div class="meta-item"><span class="meta-label">Prepared By</span><span class="meta-value">${esc(m.prepared_by)}</span></div>
      <div class="meta-item"><span class="meta-label">Status</span><span class="meta-value">${badge(m.status)}</span></div>
      <div class="meta-item"><span class="meta-label">Created</span><span class="meta-value">${fmtDate(m.created_at)}</span></div>
      ${m.validated_by ? `<div class="meta-item"><span class="meta-label">${m.status === "rejected" ? "Rejected" : "Validated"} By</span><span class="meta-value">${esc(m.validated_by)}</span></div>` : ""}
      ${m.rejection_reason ? `<div class="meta-item"><span class="meta-label">Rejection Reason</span><span class="meta-value" style="color:var(--danger)">${esc(m.rejection_reason)}</span></div>` : ""}
    </div>

    ${m.summary ? `<div class="card"><div class="card-header"><h3>Summary</h3></div><div class="card-body"><p>${esc(m.summary)}</p></div></div>` : ""}

    <div class="card">
      <div class="card-header"><h3>Agenda Items (${m.agenda_items.length})</h3>
        ${m.status === "draft" ? `<button class="btn btn-sm btn-primary" onclick="showAddAgenda('${m.id}')">+ Add Item</button>` : ""}
      </div>
      <div class="card-body">
        ${m.agenda_items.length ? `<div class="agenda-list">${m.agenda_items.map((a, i) => `
          <div class="agenda-item">
            <h4>${i + 1}. ${esc(a.title)}</h4>
            ${a.discussion ? `<div class="agenda-section"><strong>Discussion:</strong> ${esc(a.discussion)}</div>` : ""}
            ${a.decisions ? `<div class="agenda-section"><strong>Decisions:</strong> ${esc(a.decisions)}</div>` : ""}
          </div>`).join("")}</div>` : '<div class="empty-state"><p>No agenda items yet</p></div>'}
      </div>
    </div>

    <div class="card">
      <div class="card-header"><h3>Linked Tasks (${m.tasks.length})</h3>
        <button class="btn btn-sm btn-primary" onclick="showCreateTaskForMom('${m.id}','${m.meeting_id}')">+ Add Task</button>
      </div>
      <div class="card-body"><div class="table-wrap">
        ${m.tasks.length ? `<table><thead><tr><th>Title</th><th>Assigned To</th><th>Priority</th><th>Status</th><th>Due</th><th>Actions</th></tr></thead><tbody>
          ${m.tasks.map(t => `<tr>
            <td><strong>${esc(t.title)}</strong></td>
            <td>${esc(t.assigned_to)}</td>
            <td>${badge(t.priority)}</td>
            <td>${badge(t.status)}</td>
            <td>${t.due_date || "-"}</td>
            <td><div class="action-btns">${taskInlineActions(t)}</div></td>
          </tr>`).join("")}
        </tbody></table>` : '<div class="empty-state"><p>No tasks linked to this MOM</p></div>'}
      </div></div>
    </div>

    <div style="margin-top:16px">
      <div class="action-btns">
        ${m.status === "draft" ? `<button class="btn btn-warning" onclick="submitMomAndReload('${m.id}')">Submit for Review</button>` : ""}
        ${m.status === "pending_review" ? `<button class="btn btn-success" onclick="showValidateMomDetail('${m.id}')">Validate</button><button class="btn btn-danger" onclick="showRejectMomDetail('${m.id}')">Reject</button>` : ""}
        ${m.status === "rejected" ? `<button class="btn btn-primary" onclick="reviseMomAndReload('${m.id}')">Revise (Back to Draft)</button>` : ""}
      </div>
    </div>
  `;
};

window.showCreateTaskForMom = async (momId, meetingId) => {
  const meeting = await api(`/meetings/${meetingId}`);
  const deptId = meeting.department_id;
  openModal("Add Task from MOM", `
    <div class="form-group"><label>Title *</label><input id="fTaskTitle" placeholder="e.g. Implement login redesign"></div>
    <div class="form-group"><label>Description</label><textarea id="fTaskDesc"></textarea></div>
    <div class="form-row">
      <div class="form-group"><label>Assigned To *</label><input id="fTaskAssign" placeholder="e.g. Alice"></div>
      <div class="form-group"><label>Due Date</label><input id="fTaskDue" type="date"></div>
    </div>
    <div class="form-group"><label>Priority</label><select id="fTaskPri"><option value="low">Low</option><option value="medium" selected>Medium</option><option value="high">High</option><option value="critical">Critical</option></select></div>
    <div class="modal-actions"><button class="btn btn-outline" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="createTaskForMom('${momId}','${deptId}')">Create</button></div>
  `);
};
window.createTaskForMom = async (momId, deptId) => {
  const title = $("#fTaskTitle").value.trim(), assigned = $("#fTaskAssign").value.trim();
  if (!title || !assigned) return toast("Title and assignee required", "error");
  await api("/tasks", { method: "POST", body: { title, department_id: deptId, assigned_to: assigned, description: $("#fTaskDesc").value.trim(), mom_id: momId, due_date: $("#fTaskDue").value || null, priority: $("#fTaskPri").value } });
  closeModal(); toast("Task created"); viewMom(momId);
};
window.submitMomAndReload = async (id) => { await api(`/moms/${id}/submit`, { method: "POST" }); toast("Submitted for review"); viewMom(id); };
window.showValidateMomDetail = (id) => { window.showValidateMom(id); };
window.showRejectMomDetail = (id) => { window.showRejectMom(id); };
window.reviseMomAndReload = async (id) => { await api(`/moms/${id}/revise`, { method: "POST" }); toast("Back to draft"); viewMom(id); };

/* ── Tasks ─────────────────────────────────────────────────────────────── */
async function renderTasks() {
  const tasks = await api("/tasks");
  const area = $("#contentArea");
  area.innerHTML = `
    <div class="card">
      <div class="card-header"><h3>All Tasks</h3><button class="btn btn-primary" onclick="showCreateTask()">+ New Task</button></div>
      <div class="card-body"><div class="table-wrap">
        ${tasks.length ? `<table><thead><tr><th>ID</th><th>Title</th><th>Assigned To</th><th>Priority</th><th>Status</th><th>Due Date</th><th>MOM</th><th>Actions</th></tr></thead><tbody>
          ${tasks.map(t => `<tr>
            <td><code>${shortId(t.id)}</code></td>
            <td><strong>${esc(t.title)}</strong>${t.description ? `<br><small style="color:var(--text-muted)">${esc(t.description).substring(0, 60)}</small>` : ""}</td>
            <td>${esc(t.assigned_to)}</td>
            <td>${badge(t.priority)}</td>
            <td>${badge(t.status)}</td>
            <td>${t.due_date || "-"}</td>
            <td>${t.mom_id ? `<a href="#" onclick="viewMom('${t.mom_id}');return false" style="color:var(--primary)">${shortId(t.mom_id)}</a>` : "-"}</td>
            <td><div class="action-btns">${taskInlineActions(t)}</div></td>
          </tr>`).join("")}
        </tbody></table>` : emptyState("No tasks yet.")}
      </div></div>
    </div>`;
}

function taskInlineActions(t) {
  let b = "";
  if (t.status === "open") b += `<button class="btn btn-sm btn-warning" onclick="startTask('${t.id}')">Start</button>`;
  if (t.status === "open" || t.status === "in_progress") b += `<button class="btn btn-sm btn-success" onclick="completeTask('${t.id}')">Complete</button>`;
  if (t.status !== "completed" && t.status !== "cancelled") b += `<button class="btn btn-sm btn-outline" onclick="cancelTask('${t.id}')">Cancel</button>`;
  return b;
}

window.startTask = async (id) => { await api(`/tasks/${id}/start`, { method: "POST" }); toast("Task started"); refreshCurrent(); };
window.completeTask = async (id) => { await api(`/tasks/${id}/complete`, { method: "POST" }); toast("Task completed!"); refreshCurrent(); };
window.cancelTask = async (id) => { if (!confirm("Cancel this task?")) return; await api(`/tasks/${id}/cancel`, { method: "POST" }); toast("Task cancelled"); refreshCurrent(); };

window.showCreateTask = async () => {
  const depts = await api("/departments");
  const moms = await api("/moms");
  if (!depts.length) { toast("Create a department first", "error"); return; }
  openModal("New Task", `
    <div class="form-group"><label>Title *</label><input id="fTaskTitle" placeholder="e.g. Fix login bug"></div>
    <div class="form-group"><label>Description</label><textarea id="fTaskDesc"></textarea></div>
    <div class="form-row">
      <div class="form-group"><label>Department *</label><select id="fTaskDept">${depts.map(d => `<option value="${d.id}">${esc(d.name)}</option>`).join("")}</select></div>
      <div class="form-group"><label>Assigned To *</label><input id="fTaskAssign" placeholder="e.g. Alice"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label>Due Date</label><input id="fTaskDue" type="date"></div>
      <div class="form-group"><label>Priority</label><select id="fTaskPri"><option value="low">Low</option><option value="medium" selected>Medium</option><option value="high">High</option><option value="critical">Critical</option></select></div>
    </div>
    <div class="form-group"><label>Link to MOM (optional)</label><select id="fTaskMom"><option value="">-- None --</option>${moms.map(m => `<option value="${m.id}">${esc(m.meeting_title)} (${m.status})</option>`).join("")}</select></div>
    <div class="modal-actions"><button class="btn btn-outline" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="createTask()">Create</button></div>
  `);
};
window.createTask = async () => {
  const title = $("#fTaskTitle").value.trim(), assigned = $("#fTaskAssign").value.trim();
  if (!title || !assigned) return toast("Title and assignee required", "error");
  await api("/tasks", { method: "POST", body: { title, department_id: $("#fTaskDept").value, assigned_to: assigned, description: $("#fTaskDesc").value.trim(), due_date: $("#fTaskDue").value || null, priority: $("#fTaskPri").value, mom_id: $("#fTaskMom").value || null } });
  closeModal(); toast("Task created"); renderTasks();
};

/* ── Utility ──────────────────────────────────────────────────────────── */
function refreshCurrent() { pages[currentPage](); }
function esc(s) { const d = document.createElement("div"); d.textContent = s || ""; return d.innerHTML; }
function fmtDate(iso) { if (!iso) return "-"; return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }); }
function emptyState(msg) { return `<div class="empty-state"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M8 15h8M9 9h.01M15 9h.01"/></svg><p>${msg}</p></div>`; }

/* ── Init ─────────────────────────────────────────────────────────────── */
navigate("dashboard");
