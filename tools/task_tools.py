from models.db_models import db, Task
from datetime import datetime

def delete_task(session_key, task_id=None, task_title=None):
    task = None

    if task_id:
        task = Task.query.filter_by(id=task_id, session_key=session_key).first()
    elif task_title:
        matches = _find_task_by_title(session_key, task_title)
        if len(matches) == 1:
            task = matches[0]
        elif len(matches) > 1:
            options = ", ".join([f"#{t.id} (due {t.due_date.date() if t.due_date else 'no date'})" for t in matches])
            return {"success": False, "error": f"Multiple matching tasks found: {options}. Please specify the task ID."}

    if not task:
        return {"success": False, "error": "Task not found"}

    title = task.title
    db.session.delete(task)
    db.session.commit()

    return {"success": True, "deleted_title": title}
def create_task(session_key, title, description="", due_date=None, priority="normal"):
    parsed_due = None
    if due_date:
        try:
            parsed_due = datetime.fromisoformat(due_date)
        except ValueError:
            parsed_due = None

    task = Task(
        session_key=session_key,
        title=title,
        description=description,
        due_date=parsed_due,
        priority=priority if priority in ["low", "normal", "high"] else "normal",
        status="pending"
    )
    db.session.add(task)
    db.session.commit()

    return {
        "success": True,
        "task_id": task.id,
        "title": task.title,
        "priority": task.priority,
        "due_date": str(task.due_date) if task.due_date else None
    }


def create_tasks_from_text(session_key, notes_text):
    """Extracts multiple actionable tasks from a block of unstructured notes text using the LLM, then creates them all."""
    from services.llm_service import call_llm
    from datetime import date
    import json

    today = date.today().isoformat()

    prompt = f"""Extract actionable tasks from the following notes. Return ONLY a JSON array, nothing else.
Each item must have: "title" (short, clear), "priority" ("low", "normal", or "high" based on urgency language), and "due_date" (ISO date string if mentioned, otherwise null).

Today's date is {today}. Resolve relative dates like "Friday", "next Monday", or "tomorrow" into actual ISO dates (YYYY-MM-DD) based on today's date.

Notes:
{notes_text}

Example format:
[{{"title": "Follow up with client", "priority": "high", "due_date": null}}]"""

    raw = call_llm(prompt, max_tokens=400)
    cleaned = raw.strip().replace("```json", "").replace("```", "").strip()

    try:
        extracted_tasks = json.loads(cleaned)
    except json.JSONDecodeError:
        return {"success": False, "error": "Could not extract tasks from the provided text"}

    created = []
    for t in extracted_tasks:
        result = create_task(
            session_key=session_key,
            title=t.get("title", "Untitled task"),
            priority=t.get("priority", "normal"),
            due_date=t.get("due_date")
        )
        created.append(result)

    return {
        "success": True,
        "count": len(created),
        "tasks": created
    }


def list_tasks(session_key, status_filter=None, priority_filter=None):
    query = Task.query.filter_by(session_key=session_key)
    if status_filter:
        query = query.filter_by(status=status_filter)
    if priority_filter:
        query = query.filter_by(priority=priority_filter)
    tasks = query.order_by(Task.created_at.desc()).all()

    return {
        "success": True,
        "count": len(tasks),
        "tasks": [
            {"id": t.id, "title": t.title, "status": t.status, "priority": t.priority,
             "due_date": str(t.due_date) if t.due_date else None}
            for t in tasks
        ]
    }

def _find_task_by_title(session_key, task_title):
    """Finds tasks where ALL words in task_title appear in the task's title, regardless of order."""
    all_pending = Task.query.filter_by(session_key=session_key, status="pending").all()
    words = [w.lower() for w in task_title.split() if len(w) > 2]  # skip tiny words like "the"

    matches = [
        t for t in all_pending
        if all(w in t.title.lower() for w in words)
    ]
    return matches

def complete_task(session_key, task_id=None, task_title=None):
    task = None

    if task_id:
        task = Task.query.filter_by(id=task_id, session_key=session_key).first()
    elif task_title:
        matches = _find_task_by_title(session_key, task_title)
        if len(matches) == 1:
            task = matches[0]
        elif len(matches) > 1:
            options = ", ".join([f"#{t.id} (due {t.due_date.date() if t.due_date else 'no date'})" for t in matches])
            return {"success": False, "error": f"Multiple matching tasks found: {options}. Please specify the task ID."}

    if not task:
        return {"success": False, "error": "Task not found"}

    task.status = "completed"
    db.session.commit()

    return {"success": True, "task_id": task.id, "title": task.title, "status": task.status}
