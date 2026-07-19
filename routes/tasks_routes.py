from flask import Blueprint, render_template, request
from models.db_models import Task, ApprovalRequest
import json

tasks_bp = Blueprint("tasks_bp", __name__)


@tasks_bp.route("/tasks")
def tasks_page():
    filter_type = request.args.get("filter", "all")

    if filter_type == "completed":
        tasks = Task.query.filter_by(status="completed").order_by(Task.created_at.desc()).all()
    elif filter_type == "pending":
        tasks = Task.query.filter_by(status="pending").order_by(Task.created_at.desc()).all()
    elif filter_type == "rejected":
        # Tasks whose completion or deletion was rejected via the approval flow
        rejected_approvals = ApprovalRequest.query.filter_by(status="rejected").all()
        task_ids = []
        for a in rejected_approvals:
            try:
                data = json.loads(a.tool_input)
                if data.get("task_id"):
                    task_ids.append(data["task_id"])
            except (json.JSONDecodeError, TypeError):
                continue
        tasks = Task.query.filter(Task.id.in_(task_ids)).order_by(Task.created_at.desc()).all() if task_ids else []
    else:
        tasks = Task.query.order_by(Task.created_at.desc()).all()

    counts = {
        "all": Task.query.count(),
        "pending": Task.query.filter_by(status="pending").count(),
        "completed": Task.query.filter_by(status="completed").count(),
        "rejected": len(set(task_ids)) if filter_type == "rejected" else _count_rejected()
    }

    return render_template("tasks.html", tasks=tasks, filter_type=filter_type, counts=counts)


def _count_rejected():
    rejected_approvals = ApprovalRequest.query.filter_by(status="rejected").all()
    task_ids = set()
    for a in rejected_approvals:
        try:
            data = json.loads(a.tool_input)
            if data.get("task_id"):
                task_ids.add(data["task_id"])
        except (json.JSONDecodeError, TypeError):
            continue
    return len(task_ids)