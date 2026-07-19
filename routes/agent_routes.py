from flask import Blueprint, request, jsonify, render_template
from agent.controller import run_agent
import uuid

agent_bp = Blueprint("agent_bp", __name__)


@agent_bp.route("/")
def home():
    return render_template("index.html")


@agent_bp.route("/agent/chat", methods=["POST"])
def agent_chat():
    data = request.get_json()
    message = data.get("message")
    session_key = data.get("session_key") or str(uuid.uuid4())

    if not message:
        return jsonify({"error": "No message provided"}), 400

    result = run_agent(session_key, message)
    result["session_key"] = session_key

    return jsonify(result)

from models.db_models import AgentMessage
import json

@agent_bp.route("/agent/history/<session_key>")
def agent_history(session_key):
    messages = AgentMessage.query.filter_by(session_key=session_key).order_by(AgentMessage.created_at).all()
    return jsonify({
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "tool_used": m.tool_used,
                "result": json.loads(m.result_json) if m.result_json else None
            }
            for m in messages
        ]
    })