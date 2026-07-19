from flask import Blueprint, render_template, request
from models.db_models import Plan
import json

plans_bp = Blueprint("plans_bp", __name__)


@plans_bp.route("/plans")
def plans_page():
    filter_type = request.args.get("filter", "all")

    query = Plan.query
    if filter_type != "all":
        query = query.filter_by(plan_type=filter_type)

    plans = query.order_by(Plan.created_at.desc()).all()

    for p in plans:
        try:
            p.parsed_tasks = json.loads(p.tasks_snapshot)
        except (json.JSONDecodeError, TypeError):
            p.parsed_tasks = []

    counts = {
        "all": Plan.query.count(),
        "daily": Plan.query.filter_by(plan_type="daily").count(),
        "weekly": Plan.query.filter_by(plan_type="weekly").count(),
        "productivity_report": Plan.query.filter_by(plan_type="productivity_report").count(),
    }

    return render_template("plans.html", plans=plans, filter_type=filter_type, counts=counts)