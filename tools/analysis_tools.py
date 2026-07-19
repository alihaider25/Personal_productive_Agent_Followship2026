from models.db_models import Task
from services.llm_service import call_llm


def analyze_priorities(session_key):
    """Analyzes pending tasks, highlights overdue/urgent ones, and recommends what to work on first."""
    from datetime import datetime
    now = datetime.utcnow()

    tasks = Task.query.filter_by(session_key=session_key, status="pending").all()

    overdue = [t for t in tasks if t.due_date and t.due_date < now]
    high_priority = [t for t in tasks if t.priority == "high"]
    upcoming = [t for t in tasks if t.due_date and t.due_date >= now]

    recommendation = None
    if overdue:
        top = sorted(overdue, key=lambda t: t.due_date)[0]
        recommendation = f"'{top.title}' is overdue and should be tackled first."
    elif high_priority:
        recommendation = f"'{high_priority[0].title}' is marked high priority and should be prioritized."
    elif upcoming:
        top = sorted(upcoming, key=lambda t: t.due_date)[0]
        recommendation = f"'{top.title}' is your next upcoming deadline."
    else:
        recommendation = "No urgent items — your task list is currently clear."

    return {
        "success": True,
        "total_pending": len(tasks),
        "overdue_count": len(overdue),
        "overdue": [{"id": t.id, "title": t.title} for t in overdue],
        "high_priority_count": len(high_priority),
        "high_priority": [{"id": t.id, "title": t.title} for t in high_priority],
        "recommendation": recommendation
    }


def summarize_notes(session_key, notes_text):
    """Summarizes notes into decisions and action items, in addition to a general summary."""
    prompt = f"""Analyze the following notes and return your response in exactly this structure:

Summary: (2-3 sentence overview)

Decisions Made:
- (list each decision, or write "None identified")

Action Items:
- (list each action item, or write "None identified")

Notes:
{notes_text}"""

    result = call_llm(prompt, max_tokens=300)

    return {
        "success": True,
        "summary": result
    }