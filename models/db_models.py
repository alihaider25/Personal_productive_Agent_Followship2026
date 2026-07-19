from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    session_key = db.Column(db.String(100))
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime, nullable=True)
    priority = db.Column(db.String(20), default="normal")   # NEW: low, normal, high
    status = db.Column(db.String(50), default="pending")     # pending, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Note(db.Model):
    __tablename__ = "notes"
    id = db.Column(db.Integer, primary_key=True)
    session_key = db.Column(db.String(100))
    title = db.Column(db.String(255))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ExecutionLog(db.Model):
    __tablename__ = "execution_logs"
    id = db.Column(db.Integer, primary_key=True)
    session_key = db.Column(db.String(100))
    user_request = db.Column(db.Text)
    step = db.Column(db.String(100))
    detail = db.Column(db.Text)
    status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ApprovalRequest(db.Model):
    __tablename__ = "approval_requests"
    id = db.Column(db.Integer, primary_key=True)
    session_key = db.Column(db.String(100))
    tool_name = db.Column(db.String(100))
    tool_input = db.Column(db.Text)
    status = db.Column(db.String(50), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AgentMessage(db.Model):
    __tablename__ = "agent_messages"
    id = db.Column(db.Integer, primary_key=True)
    session_key = db.Column(db.String(100))
    role = db.Column(db.String(20))          # 'user' or 'assistant'
    content = db.Column(db.Text)
    tool_used = db.Column(db.String(100), nullable=True)
    result_json = db.Column(db.Text, nullable=True)   # store structured result as JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Plan(db.Model):
    __tablename__ = "plans"
    id = db.Column(db.Integer, primary_key=True)
    session_key = db.Column(db.String(100))
    plan_type = db.Column(db.String(20))       # 'daily', 'weekly', 'productivity_report'
    date_range = db.Column(db.String(100))      # e.g. "2026-07-19" or "2026-07-19 to 2026-07-26"
    task_count = db.Column(db.Integer, default=0)
    tasks_snapshot = db.Column(db.Text)          # JSON string of the tasks included at generation time
    created_at = db.Column(db.DateTime, default=datetime.utcnow)