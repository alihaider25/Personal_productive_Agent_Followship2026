from flask import Blueprint, jsonify, render_template
from models.db_models import ApprovalRequest
from agent.controller import execute_approved_action

approval_bp = Blueprint("approval_bp", __name__)


@approval_bp.route("/approvals")
def approvals_page():
    pending = ApprovalRequest.query.filter_by(status="pending").order_by(ApprovalRequest.created_at.desc()).all()
    return render_template("approvals.html", approvals=pending)


@approval_bp.route("/approve/<int:approval_id>", methods=["POST"])
def approve(approval_id):
    result = execute_approved_action(approval_id, "approved")
    return jsonify(result)


@approval_bp.route("/reject/<int:approval_id>", methods=["POST"])
def reject(approval_id):
    result = execute_approved_action(approval_id, "rejected")
    return jsonify(result)

@approval_bp.route("/approvals/count")
def approvals_count():
    count = ApprovalRequest.query.filter_by(status="pending").count()
    return jsonify({"count": count})