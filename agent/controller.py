from agent.intent_analysis import analyze_intent
from agent.validator import validate_input
from agent.response_generator import generate_response, generate_plain_response
from tools.tool_registry import get_tool
from logging_module.execution_logger import log_step
from models.db_models import db, ApprovalRequest, AgentMessage
import json


def save_assistant_message(session_key, reply, tool_used=None, result=None):
    db.session.add(AgentMessage(
        session_key=session_key,
        role="assistant",
        content=reply,
        tool_used=tool_used,
        result_json=json.dumps(result) if result else None
    ))
    db.session.commit()


def run_agent(session_key, user_message):
    db.session.add(AgentMessage(session_key=session_key, role="user", content=user_message))
    db.session.commit()

    intent = analyze_intent(user_message)
    log_step(session_key, user_message, "intent_analysis", intent)

    if not intent.get("needs_tool"):
        reply = generate_plain_response(user_message)
        log_step(session_key, user_message, "response_generated", reply)
        save_assistant_message(session_key, reply)
        return {"reply": reply, "tool_used": None}

    tool_name = intent.get("tool_name")
    tool_input = intent.get("tool_input", {})

    tool = get_tool(tool_name)
    if not tool:
        error_msg = f"I don't have a tool called '{tool_name}'."
        log_step(session_key, user_message, "tool_selection_failed", error_msg, status="failed")
        save_assistant_message(session_key, error_msg)
        return {"reply": error_msg, "tool_used": None}

    log_step(session_key, user_message, "tool_selected", tool_name)

    validation = validate_input(tool["schema"], tool_input)
    if not validation["valid"]:
        error_msg = f"I couldn't complete that: {', '.join(validation['errors'])}"
        log_step(session_key, user_message, "validation_failed", validation["errors"], status="failed")
        save_assistant_message(session_key, error_msg, tool_used=tool_name)
        return {"reply": error_msg, "tool_used": tool_name}

    if tool["requires_approval"]:
        approval = ApprovalRequest(
            session_key=session_key,
            tool_name=tool_name,
            tool_input=json.dumps(tool_input),
            status="pending"
        )
        db.session.add(approval)
        db.session.commit()

        log_step(session_key, user_message, "awaiting_approval", tool_input, status="pending_approval")
        reply = f"This action ({tool_name}) needs your approval before I proceed. Please approve or reject it."
        save_assistant_message(session_key, reply, tool_used=tool_name)
        return {
            "reply": reply,
            "tool_used": tool_name,
            "approval_id": approval.id,
            "needs_approval": True
        }

    try:
        result = tool["func"](session_key=session_key, **tool_input)
        log_step(session_key, user_message, "tool_executed", result)
    except Exception as e:
        error_msg = f"Something went wrong while running {tool_name}: {str(e)}"
        log_step(session_key, user_message, "tool_execution_failed", str(e), status="failed")
        save_assistant_message(session_key, error_msg, tool_used=tool_name)
        return {"reply": error_msg, "tool_used": tool_name}

    if not result.get("success"):
        error_msg = f"The action didn't complete successfully: {result.get('error', 'unknown error')}"
        log_step(session_key, user_message, "result_invalid", result, status="failed")
        save_assistant_message(session_key, error_msg, tool_used=tool_name)
        return {"reply": error_msg, "tool_used": tool_name}

    reply = generate_response(user_message, tool_name, result)
    log_step(session_key, user_message, "response_generated", reply)
    save_assistant_message(session_key, reply, tool_used=tool_name, result=result)

    return {"reply": reply, "tool_used": tool_name, "result": result}


def execute_approved_action(approval_id, decision):
    approval = ApprovalRequest.query.get(approval_id)
    if not approval:
        return {"reply": "Approval request not found.", "success": False}

    if approval.status != "pending":
        return {"reply": f"This request was already {approval.status}.", "success": False}

    if decision == "rejected":
        approval.status = "rejected"
        db.session.commit()
        log_step(approval.session_key, "", "approval_rejected", approval.tool_name, status="rejected")
        reply = f"Okay, I won't proceed with {approval.tool_name}."
        save_assistant_message(approval.session_key, reply, tool_used=approval.tool_name)
        return {"reply": reply, "success": True}

    approval.status = "approved"
    db.session.commit()

    tool = get_tool(approval.tool_name)
    tool_input = json.loads(approval.tool_input)

    try:
        result = tool["func"](session_key=approval.session_key, **tool_input)
        log_step(approval.session_key, "", "approved_tool_executed", result)
    except Exception as e:
        log_step(approval.session_key, "", "approved_tool_failed", str(e), status="failed")
        reply = f"Approval granted, but execution failed: {str(e)}"
        save_assistant_message(approval.session_key, reply, tool_used=approval.tool_name)
        return {"reply": reply, "success": False}

    if not result.get("success"):
        reply = f"Action completed but reported an issue: {result.get('error')}"
        save_assistant_message(approval.session_key, reply, tool_used=approval.tool_name)
        return {"reply": reply, "success": False}

    reply = generate_response(f"Approved action: {approval.tool_name}", approval.tool_name, result)
    log_step(approval.session_key, "", "response_generated", reply)
    save_assistant_message(approval.session_key, reply, tool_used=approval.tool_name, result=result)

    return {"reply": reply, "success": True, "result": result}