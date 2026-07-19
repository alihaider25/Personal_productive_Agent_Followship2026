from models.db_models import db, Task, Plan
from datetime import datetime, timedelta
import json


def _save_plan(session_key, plan_type, date_range, tasks):
    # Check the most recent plan of this type for this session
    last_plan = Plan.query.filter_by(
        session_key=session_key, plan_type=plan_type
    ).order_by(Plan.created_at.desc()).first()

    new_snapshot = json.dumps(tasks)

    if last_plan and last_plan.tasks_snapshot == new_snapshot and last_plan.date_range == date_range:
        # Identical to the last plan of this type — don't create a duplicate, just return the existing one
        return last_plan.id

    plan = Plan(
        session_key=session_key,
        plan_type=plan_type,
        date_range=date_range,
        task_count=len(tasks),
        tasks_snapshot=new_snapshot
    )
    db.session.add(plan)
    db.session.commit()
    return plan.id


def generate_daily_plan(session_key, date=None, available_hours=8):
    """
    Generates an ordered daily schedule.
    available_hours: how many working hours the user has today (default 8).
    """
    target_date_str = date or datetime.utcnow().date().isoformat()

    try:
        target = datetime.fromisoformat(target_date_str).date()
    except ValueError:
        return {"success": False, "error": "Invalid date format"}

    all_pending = Task.query.filter_by(session_key=session_key, status="pending").all()

    if not all_pending:
        _save_plan(session_key, "daily", target_date_str, [])
        return {
            "success": True, "date": target_date_str, "task_count": 0,
            "tasks": [], "deferred": [], "focus_areas": [], "risk_warnings": []
        }

    due_today = [t for t in all_pending if t.due_date and t.due_date.date() == target]
    overdue = [t for t in all_pending if t.due_date and t.due_date.date() < target]
    upcoming = [t for t in all_pending if t.due_date and t.due_date.date() > target]
    no_date = [t for t in all_pending if not t.due_date]

    candidate_tasks = overdue + due_today
    if not candidate_tasks:
        upcoming_sorted = sorted(upcoming, key=lambda t: t.due_date)
        candidate_tasks = upcoming_sorted[:3] + no_date

    # Sort by priority (high first), matching how much time we realistically have
    priority_order = {"high": 0, "normal": 1, "low": 2}
    candidate_tasks = sorted(candidate_tasks, key=lambda t: priority_order.get(t.priority, 1))

    # Assume ~90 minutes per task; fit as many as available_hours allows
    minutes_per_task = 90
    max_tasks_that_fit = max(1, (available_hours * 60) // minutes_per_task)

    scheduled = candidate_tasks[:max_tasks_that_fit]
    deferred = candidate_tasks[max_tasks_that_fit:]

    scheduled_with_times = _assign_time_slots(scheduled)

    # Focus areas: summarize by priority makeup
    high_count = sum(1 for t in scheduled if t.priority == "high")
    focus_areas = []
    if high_count > 0:
        focus_areas.append(f"{high_count} high-priority task(s) scheduled first")
    if overdue:
        focus_areas.append(f"Clearing {len(overdue)} overdue item(s)")
    if not focus_areas:
        focus_areas.append("Steady progress on upcoming deadlines")

    # Risk warnings
    risk_warnings = []
    if len(overdue) > 0:
        risk_warnings.append(f"{len(overdue)} task(s) are already overdue.")
    if len(deferred) > 0:
        risk_warnings.append(f"{len(deferred)} task(s) don't fit in your {available_hours}-hour day and were deferred.")
    high_priority_deferred = [t for t in deferred if t.priority == "high"]
    if high_priority_deferred:
        risk_warnings.append(f"{len(high_priority_deferred)} high-priority task(s) were deferred — consider freeing up more time.")

    task_data = [
        {"id": t["id"], "title": t["title"], "priority": t["priority"],
         "due_date": t["due_date"], "suggested_time": t["suggested_time"]}
        for t in scheduled_with_times
    ]
    deferred_data = [
        {"id": t.id, "title": t.title, "priority": t.priority}
        for t in deferred
    ]

    plan_id = _save_plan(session_key, "daily", target_date_str, task_data)

    return {
        "success": True,
        "plan_id": plan_id,
        "date": target_date_str,
        "available_hours": available_hours,
        "task_count": len(task_data),
        "tasks": task_data,
        "deferred": deferred_data,
        "focus_areas": focus_areas,
        "risk_warnings": risk_warnings
    }


def _assign_time_slots(scheduled_tasks):
    """Assigns suggested time slots across a working day starting 9 AM, skipping lunch (1-2 PM)."""
    if not scheduled_tasks:
        return []

    start_hour = 9
    slot_minutes = 90
    result = []

    for i, task in enumerate(scheduled_tasks):
        slot_start_minutes = start_hour * 60 + (i * slot_minutes)
        if 13 * 60 <= slot_start_minutes < 14 * 60:
            slot_start_minutes += 60

        hour = slot_start_minutes // 60
        minute = slot_start_minutes % 60

        if hour >= 18:
            time_label = "Later this week"
        else:
            period = "AM" if hour < 12 else "PM"
            display_hour = hour if hour <= 12 else hour - 12
            display_hour = 12 if display_hour == 0 else display_hour
            time_label = f"{display_hour}:{minute:02d} {period}"

        result.append({
            "id": task.id,
            "title": task.title,
            "priority": task.priority,
            "due_date": str(task.due_date) if task.due_date else None,
            "suggested_time": time_label
        })

    return result
def generate_weekly_plan(session_key):
    today = datetime.utcnow().date()
    week_end = today + timedelta(days=7)
    date_range = f"{today} to {week_end}"

    all_pending = Task.query.filter_by(session_key=session_key, status="pending").all()

    in_range = [t for t in all_pending if t.due_date and today <= t.due_date.date() <= week_end]
    overdue = [t for t in all_pending if t.due_date and t.due_date.date() < today]
    no_date = [t for t in all_pending if not t.due_date]

    relevant_tasks = overdue + in_range + no_date

    task_data = [
        {"id": t.id, "title": t.title, "priority": t.priority, "due_date": str(t.due_date) if t.due_date else None}
        for t in relevant_tasks
    ]

    plan_id = _save_plan(session_key, "weekly", date_range, task_data)

    return {
        "success": True,
        "plan_id": plan_id,
        "range": date_range,
        "task_count": len(task_data),
        "tasks": task_data
    }


def generate_productivity_report(session_key):
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    date_range = f"{week_ago.date()} to {now.date()}"

    all_tasks = Task.query.filter_by(session_key=session_key).all()
    completed_this_week = [t for t in all_tasks if t.status == "completed" and t.created_at >= week_ago]
    pending = [t for t in all_tasks if t.status == "pending"]
    overdue = [t for t in pending if t.due_date and t.due_date < now]
    high_priority_pending = [t for t in pending if t.priority == "high"]

    report_data = {
        "completed_count": len(completed_this_week),
        "pending_count": len(pending),
        "overdue_count": len(overdue),
        "high_priority_pending_count": len(high_priority_pending),
        "completed_tasks": [{"id": t.id, "title": t.title} for t in completed_this_week],
        "overdue_tasks": [{"id": t.id, "title": t.title} for t in overdue]
    }

    plan_id = _save_plan(session_key, "productivity_report", date_range, [report_data])

    return {
        "success": True,
        "plan_id": plan_id,
        "period": date_range,
        **report_data
    }