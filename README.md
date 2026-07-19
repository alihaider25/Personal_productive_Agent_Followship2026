# Productivity & Task Execution Agent

An AI agent (not a chatbot) that reasons about user requests, selects and executes tools, manages state, requires human approval for sensitive actions, and logs every step of its decision-making process. Built as a Week 3 project extending a Week 2 RAG application into an agentic system.

## What Makes This an Agent, Not a Chatbot

Unlike a standard chatbot that only generates text, this system:
- Interprets user intent and decides **whether** a tool is needed
- Selects the correct tool from a registry of 12+ available actions
- Validates tool inputs before execution
- Pauses and requests **human approval** before performing sensitive actions (completing or deleting tasks)
- Executes tools against a real MySQL database
- Logs every decision step for full traceability
- Is evaluated using automated test cases, not just manual testing

## Features

- **Task management** — create single or multiple tasks (extracted from unstructured notes), list, filter by status/priority, complete, delete
- **Planning** — daily plans with suggested time slots, weekly plans, both saved as historical records
- **Analysis** — priority analysis with specific recommendations, productivity reports with statistics
- **Notes** — save and search free-text notes
- **Email drafting** — generate follow-up emails from meeting notes
- **Human-in-the-loop approval** — sensitive actions (complete/delete task) pause for explicit approval or rejection
- **Execution logging** — full step-by-step trace of every agent decision, viewable in-app
- **Task board** — filterable card view (All / In Progress / Completed / Rejected)
- **Plans history** — every generated daily/weekly plan and report is saved and browsable

## Tech Stack

- **Backend:** Python, Flask
- **Database:** MySQL (via SQLAlchemy + PyMySQL)
- **LLM:** Claude (via OpenRouter API) — used for intent reasoning, task extraction, summarization, and email drafting
- **Frontend:** HTML, CSS, Bootstrap 5, vanilla JavaScript

## Project Structure
agent_project/
├── app.py                    # Flask app factory
├── config.py                 # Environment/config loader
│
├── agent/
│   ├── controller.py          # Orchestrates the full reasoning pipeline
│   ├── intent_analysis.py     # LLM-based intent + tool selection
│   ├── validator.py           # Validates tool inputs against schema
│   └── response_generator.py  # Converts tool results into natural language
│
├── tools/
│   ├── tool_registry.py       # Central tool registration system
│   ├── task_tools.py          # create/list/complete/delete tasks
│   ├── planning_tools.py      # daily/weekly plans, productivity reports
│   ├── analysis_tools.py      # priority analysis, note summarization
│   ├── notes_tools.py         # save/search notes
│   └── email_tools.py         # email drafting
│
├── models/
│   └── db_models.py           # Task, Note, Plan, ExecutionLog, ApprovalRequest, AgentMessage
│
├── services/
│   └── llm_service.py         # OpenRouter API client
│
├── logging_module/
│   └── execution_logger.py    # Writes structured logs to MySQL
│
├── evaluation/
│   └── test_cases.py          # Automated agent evaluation suite
│
├── routes/
│   ├── agent_routes.py        # /agent/chat, /agent/history
│   ├── approval_routes.py     # /approve, /reject, /approvals
│   ├── tasks_routes.py        # /tasks (filterable board)
│   ├── plans_routes.py        # /plans (plan history)
│   └── logs_routes.py         # /logs (execution trace viewer)
│
├── static/
│   ├── css/style.css
│   └── js/ (agent.js, approvals.js, toast.js, badge.js)
│
├── templates/
│   ├── base.html, index.html, tasks.html, plans.html, approvals.html, logs.html
│
└── reset_data.py               # Utility script to clear all data for a fresh demo

## Architecture

User → Frontend → Agent Controller → Intent & Task Analysis → Tool Selection
→ Human Approval (if required) → Tool Execution → Result Validation
→ Response Generation → Execution Log
## Available Tools

| Tool | Requires Approval | Description |
|---|---|---|
| `create_task` | No | Creates a single task |
| `create_tasks_from_text` | No | Extracts multiple tasks from notes |
| `list_tasks` | No | Lists tasks, filterable by status/priority |
| `complete_task` | **Yes** | Marks a task complete (by ID or title) |
| `delete_task` | **Yes** | Permanently deletes a task |
| `generate_daily_plan` | No | Daily plan with suggested time slots |
| `generate_weekly_plan` | No | 7-day task plan |
| `generate_productivity_report` | No | Weekly statistics report |
| `analyze_priorities` | No | Identifies overdue/urgent tasks with a recommendation |
| `summarize_notes` | No | Summarizes notes into decisions/action items |
| `save_note` | No | Saves a note for later retrieval |
| `search_notes` | No | Searches saved notes by keyword |
| `draft_email` | No | Drafts a follow-up email from notes |

## Setup Instructions

### Prerequisites
- Python 3.10+
- MySQL Server running

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment variables
Create a `.env` file in the project root:

DB_USER=root
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=3307
DB_NAME=agent_db
OPENROUTER_API_KEY=your-openrouter-key-here
SECRET_KEY=any-random-string

### 3. Create the database
```sql
CREATE DATABASE agent_db;
```
Tables are created automatically on first run.

### 4. Run the app
```bash
python app.py
```
Visit `http://127.0.0.1:5000`

## Usage

1. **Agent Chat** — type natural-language requests (e.g., "Create a task to submit my report by Friday")
2. **Tasks** — view all tasks as filterable cards (All / In Progress / Completed / Rejected)
3. **Plans** — browse historical daily/weekly plans and productivity reports
4. **Approvals** — review and approve/reject pending sensitive actions
5. **Logs** — inspect the full step-by-step execution trace of every agent decision

## Evaluation

Run the automated test suite:
```bash
python evaluation/test_cases.py
```

Tests verify correct tool selection, approval-gating on sensitive actions, graceful handling of invalid/incomplete input, and that unrelated queries don't trigger unnecessary tool calls.

## Reset for a Clean Demo

```bash
python reset_data.py
```
Clears all tasks, notes, plans, logs, and approvals. Also clear `localStorage.removeItem("agent_session_key")` in the browser console to start a fresh session.

## Known Limitations

- No authentication — single-user/demo setup, sessions are browser-scoped via localStorage
- Fuzzy task title matching may request clarification when multiple tasks share similar titles
- Not deployed to a public host — runs on localhost

## Author

Built as a Week 3 AI Engineering internship project, stateful, human-supervised AI agent.