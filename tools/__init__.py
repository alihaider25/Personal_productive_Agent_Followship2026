from tools.tool_registry import register_tool
from tools.task_tools import create_task, create_tasks_from_text, list_tasks, complete_task
from tools.planning_tools import generate_daily_plan, generate_weekly_plan, generate_productivity_report
from tools.analysis_tools import analyze_priorities, summarize_notes
from tools.notes_tools import save_note, search_notes
from tools.email_tools import draft_email
from tools.task_tools import create_task, create_tasks_from_text, list_tasks, complete_task, delete_task
register_tool(
    name="create_task",
    schema={
        "title": {"type": "string", "required": True},
        "description": {"type": "string", "required": False},
        "due_date": {"type": "string", "required": False, "format": "ISO date, e.g. 2026-07-25"},
        "priority": {"type": "string", "required": False, "options": ["low", "normal", "high"]}
    },
    func=create_task,
    requires_approval=False,
    description="Creates a single new task. Use when the user wants to add ONE specific to-do item or reminder."
)

register_tool(
    name="create_tasks_from_text",
    schema={
        "notes_text": {"type": "string", "required": True}
    },
    func=create_tasks_from_text,
    requires_approval=False,
    description="Extracts and creates MULTIPLE tasks from a block of meeting notes or free-form text. Use when the user provides notes and asks to create tasks from them, or mentions multiple tasks at once."
)

register_tool(
    name="list_tasks",
    schema={
        "status_filter": {"type": "string", "required": False, "options": ["pending", "completed"]},
        "priority_filter": {"type": "string", "required": False, "options": ["low", "normal", "high"]}
    },
    func=list_tasks,
    requires_approval=False,
    description="Lists tasks, optionally filtered by status or priority. Use for 'show me my tasks' or 'show high-priority tasks' requests."
)

register_tool(
    name="complete_task",
    schema={
        "task_id": {"type": "integer", "required": False},
        "task_title": {"type": "string", "required": False}
    },
    func=complete_task,
    requires_approval=True,
    description="Marks a task as completed, identified either by numeric ID or by matching part of its title (e.g. 'the website task')."
)

register_tool(
    name="generate_daily_plan",
    schema={
        "date": {"type": "string", "required": False, "format": "ISO date, defaults to today"}
    },
    func=generate_daily_plan,
    requires_approval=False,
    description="Generates a plan for a single specific day based on tasks due that day."
)

register_tool(
    name="generate_weekly_plan",
    schema={},
    func=generate_weekly_plan,
    requires_approval=False,
    description="Generates a simple task list/plan for the upcoming 7 days. Use for 'plan my week' requests, NOT for report/statistics requests."
)

register_tool(
    name="generate_productivity_report",
    schema={},
    func=generate_productivity_report,
    requires_approval=False,
    description="Generates a productivity report with statistics: completed tasks, pending tasks, overdue count, high-priority count over the past week. Use specifically for 'report', 'productivity report', or 'how am I doing' style requests."
)

register_tool(
    name="analyze_priorities",
    schema={},
    func=analyze_priorities,
    requires_approval=False,
    description="Analyzes tasks to identify what is overdue or urgent, AND provides a specific recommendation of what to work on first. Use for priority, urgency, overdue, or 'what should I work on' requests."
)

register_tool(
    name="summarize_notes",
    schema={
        "notes_text": {"type": "string", "required": True}
    },
    func=summarize_notes,
    requires_approval=False,
    description="Summarizes free-form notes into a summary, decisions made, and action items. Use when the user provides notes and wants them summarized or wants decisions/action items identified."
)

register_tool(
    name="save_note",
    schema={
        "content": {"type": "string", "required": True},
        "title": {"type": "string", "required": False}
    },
    func=save_note,
    requires_approval=False,
    description="Saves a note or piece of text for later retrieval."
)

register_tool(
    name="search_notes",
    schema={
        "query": {"type": "string", "required": True}
    },
    func=search_notes,
    requires_approval=False,
    description="Searches previously saved notes by keyword."
)

register_tool(
    name="draft_email",
    schema={
        "notes_text": {"type": "string", "required": True},
        "recipient_context": {"type": "string", "required": False}
    },
    func=draft_email,
    requires_approval=False,
    description="Drafts a follow-up email based on meeting notes or provided context. Use when the user asks to draft, write, or prepare an email."
)

register_tool(
    name="delete_task",
    schema={
        "task_id": {"type": "integer", "required": False},
        "task_title": {"type": "string", "required": False}
    },
    func=delete_task,
    requires_approval=True,
    description="Permanently deletes a task, identified by ID or title match. Use when the user wants to remove or delete a task entirely (not just mark it complete)."
)