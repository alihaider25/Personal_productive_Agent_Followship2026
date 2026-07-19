from flask import Blueprint, render_template, request
from models.db_models import ExecutionLog

logs_bp = Blueprint("logs_bp", __name__)


@logs_bp.route("/logs")
def logs_page():
    session_filter = request.args.get("session")

    query = ExecutionLog.query
    if session_filter:
        query = query.filter_by(session_key=session_filter)

    logs = query.order_by(ExecutionLog.created_at.desc()).limit(100).all()

    sessions = list({log.session_key for log in ExecutionLog.query.all()})

    return render_template("logs.html", logs=logs, sessions=sessions, current_session=session_filter)