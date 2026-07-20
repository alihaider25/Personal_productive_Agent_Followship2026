# Tool Specification — Productivity & Task Execution Agent

This document specifies every tool in the agent's tool registry in enough
detail to implement independently of the reference source code. All tools
are invoked by the agent controller after intent analysis selects a tool
name and the LLM (or the controller) produces arguments matching the input
schema below. `validator.py` checks arguments against the **Required
fields** before the tool executes.

## Conventions used throughout

- All timestamps are ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`); all dates are
  `YYYY-MM-DD`.
- Every tool returns a JSON object with a top-level `success: boolean`.
  On failure, the shape is always:
  ```json
  { "success": false, "error_code": "TASK_NOT_FOUND", "message": "Human-readable explanation" }
  ```
- `Task`, `Note`, and `Plan` are shared object shapes, defined once here:

**Task**
```json
{
  "id": 12,
  "title": "Submit quarterly report",
  "description": "Include Q3 revenue breakdown",
  "priority": "high",          // "low" | "medium" | "high"
  "status": "pending",         // "pending" | "in_progress" | "completed" | "rejected"
  "due_date": "2026-07-25",
  "created_at": "2026-07-18T09:12:00Z",
  "updated_at": "2026-07-18T09:12:00Z"
}
```

**Note**
```json
{
  "id": 7,
  "content": "Client wants revised pricing by Friday.",
  "tags": ["client", "pricing"],
  "created_at": "2026-07-19T14:02:00Z"
}
```

**Plan**
```json
{
  "id": 4,
  "type": "daily",              // "daily" | "weekly" | "report"
  "period": "2026-07-20",
  "content": { },                // shape varies by plan type — see each tool
  "created_at": "2026-07-20T07:00:00Z"
}
```

- **Common errors** (apply to every tool unless overridden): `VALIDATION_ERROR`
  (a required field is missing or the wrong type), `DB_CONNECTION_ERROR`
  (MySQL unreachable), `INTERNAL_ERROR` (unhandled exception — always
  logged to `ExecutionLog` with a stack trace, never surfaced raw to the
  user).

---

## Summary table

| Tool | Purpose | Operation | Approval |
|---|---|---|---|
| `create_task` | Create a single task | Write | No |
| `create_tasks_from_text` | Extract & create multiple tasks from free text | Write | No |
| `list_tasks` | List/filter tasks | Read | No |
| `complete_task` | Mark a task complete | Write | **Yes** |
| `delete_task` | Permanently delete a task | Write | **Yes** |
| `generate_daily_plan` | Build a daily schedule | Read + Write | No |
| `generate_weekly_plan` | Build a 7-day plan | Read + Write | No |
| `generate_productivity_report` | Weekly stats report | Read + Write | No |
| `analyze_priorities` | Flag overdue/urgent tasks | Read | No |
| `summarize_notes` | Summarize notes into decisions/action items | Read | No |
| `save_note` | Save a free-text note | Write | No |
| `search_notes` | Keyword search over notes | Read | No |
| `draft_email` | Draft a follow-up email from notes | Read | No |

---

## 1. `create_task`

**Purpose:** Creates a single task.

**Input schema**
```json
{ "title": "string", "description": "string", "priority": "low|medium|high", "due_date": "YYYY-MM-DD" }
```
- **Required:** `title`
- **Optional:** `description` (default `null`), `priority` (default `"medium"`), `due_date` (default `null`)

**Output schema**
```json
{ "success": true, "task": Task }
```

**Operation:** Write
**Approval required:** No

**Possible errors**
| Code | Cause |
|---|---|
| `EMPTY_TITLE` | `title` is empty or whitespace-only |
| `INVALID_PRIORITY` | `priority` not one of `low`/`medium`/`high` |
| `INVALID_DATE_FORMAT` | `due_date` not parseable as `YYYY-MM-DD` |
| `DB_WRITE_ERROR` | Insert failed |

**Example call**
```json
{ "tool": "create_task", "args": { "title": "Submit quarterly report", "priority": "high", "due_date": "2026-07-25" } }
```

**Example result**
```json
{
  "success": true,
  "task": {
    "id": 12, "title": "Submit quarterly report", "description": null,
    "priority": "high", "status": "pending", "due_date": "2026-07-25",
    "created_at": "2026-07-20T10:00:00Z", "updated_at": "2026-07-20T10:00:00Z"
  }
}
```

---

## 2. `create_tasks_from_text`

**Purpose:** Sends unstructured text (e.g. meeting notes) to the LLM, extracts a list of discrete tasks, and inserts each as a `Task`.

**Input schema**
```json
{ "text": "string", "default_priority": "low|medium|high" }
```
- **Required:** `text`
- **Optional:** `default_priority` (applied to any extracted task the LLM doesn't assign a priority to; default `"medium"`)

**Output schema**
```json
{ "success": true, "tasks_created": 3, "tasks": [Task, Task, Task] }
```

**Operation:** Write
**Approval required:** No

**Possible errors**
| Code | Cause |
|---|---|
| `EMPTY_TEXT` | `text` is empty |
| `NO_TASKS_FOUND` | LLM extraction returned zero candidate tasks |
| `LLM_EXTRACTION_FAILED` | LLM call errored or returned unparseable output |
| `DB_WRITE_ERROR` | One or more inserts failed (partial success is rolled back) |

**Example call**
```json
{ "tool": "create_tasks_from_text", "args": { "text": "Meeting notes: need to email the vendor, book the venue by Friday, and follow up with legal on the contract." } }
```

**Example result**
```json
{
  "success": true,
  "tasks_created": 3,
  "tasks": [
    { "id": 13, "title": "Email the vendor", "priority": "medium", "status": "pending", "due_date": null, "description": null, "created_at": "2026-07-20T10:01:00Z", "updated_at": "2026-07-20T10:01:00Z" },
    { "id": 14, "title": "Book the venue", "priority": "medium", "status": "pending", "due_date": "2026-07-24", "description": null, "created_at": "2026-07-20T10:01:00Z", "updated_at": "2026-07-20T10:01:00Z" },
    { "id": 15, "title": "Follow up with legal on the contract", "priority": "medium", "status": "pending", "due_date": null, "description": null, "created_at": "2026-07-20T10:01:00Z", "updated_at": "2026-07-20T10:01:00Z" }
  ]
}
```

---

## 3. `list_tasks`

**Purpose:** Lists tasks, optionally filtered by status and/or priority.

**Input schema**
```json
{ "status": "pending|in_progress|completed|rejected", "priority": "low|medium|high", "limit": "integer" }
```
- **Required:** none
- **Optional:** `status`, `priority`, `limit` (default `50`, max `200`)

**Output schema**
```json
{ "success": true, "count": 2, "tasks": [Task, Task] }
```

**Operation:** Read
**Approval required:** No

**Possible errors**
| Code | Cause |
|---|---|
| `INVALID_STATUS_FILTER` | `status` not a recognized value |
| `INVALID_PRIORITY_FILTER` | `priority` not a recognized value |
| `DB_READ_ERROR` | Query failed |

**Example call**
```json
{ "tool": "list_tasks", "args": { "status": "pending", "priority": "high" } }
```

**Example result**
```json
{
  "success": true,
  "count": 1,
  "tasks": [
    { "id": 12, "title": "Submit quarterly report", "description": null, "priority": "high", "status": "pending", "due_date": "2026-07-25", "created_at": "2026-07-20T10:00:00Z", "updated_at": "2026-07-20T10:00:00Z" }
  ]
}
```

---

## 4. `complete_task`

**Purpose:** Marks a task as completed. Sensitive — gated behind human approval.

**Input schema**
```json
{ "task_id": "integer", "task_title": "string" }
```
- **Required:** at least one of `task_id` or `task_title` (prefer `task_id` when both are given)
- **Optional:** n/a

**Output schema (two-phase, see Approval flow below)**

Phase 1 — approval requested:
```json
{ "success": true, "status": "pending_approval", "approval_id": 21 }
```
Phase 2 — after approval is granted:
```json
{ "success": true, "task": Task }
```
Phase 2 — after approval is rejected:
```json
{ "success": false, "error_code": "APPROVAL_REJECTED", "message": "Task completion was rejected by the user." }
```

**Operation:** Write (gated)
**Approval required:** Yes

**Approval flow:** the tool does not touch the database on first call. It
creates an `ApprovalRequest` row (`tool_name: "complete_task"`, `payload`:
the resolved `task_id`, `status: "pending"`) and returns immediately. The
frontend surfaces this on the Approvals page. A separate call to
`/approve` or `/reject` (routed through `approval_routes.py`, not this
tool) resolves the request; on approval, the controller re-invokes the
underlying task-completion logic directly against the stored `task_id`.

**Possible errors**
| Code | Cause |
|---|---|
| `TASK_NOT_FOUND` | No task matches `task_id`, or no task title matches `task_title` |
| `AMBIGUOUS_TITLE_MATCH` | `task_title` fuzzy-matches more than one task; response includes `candidates: Task[]` for clarification |
| `TASK_ALREADY_COMPLETED` | Target task's `status` is already `completed` |
| `APPROVAL_REJECTED` | User rejected the pending approval |
| `DB_WRITE_ERROR` | Update failed after approval |

**Example call**
```json
{ "tool": "complete_task", "args": { "task_id": 12 } }
```

**Example result (phase 1)**
```json
{ "success": true, "status": "pending_approval", "approval_id": 21 }
```

**Example result (phase 2, after approval)**
```json
{
  "success": true,
  "task": {
    "id": 12, "title": "Submit quarterly report", "description": null,
    "priority": "high", "status": "completed", "due_date": "2026-07-25",
    "created_at": "2026-07-20T10:00:00Z", "updated_at": "2026-07-20T15:30:00Z"
  }
}
```

---

## 5. `delete_task`

**Purpose:** Permanently deletes a task. Sensitive — gated behind human approval.

**Input schema**
```json
{ "task_id": "integer", "task_title": "string" }
```
- **Required:** at least one of `task_id` or `task_title`
- **Optional:** n/a

**Output schema**

Phase 1:
```json
{ "success": true, "status": "pending_approval", "approval_id": 22 }
```
Phase 2 (approved):
```json
{ "success": true, "deleted_task_id": 14 }
```
Phase 2 (rejected):
```json
{ "success": false, "error_code": "APPROVAL_REJECTED", "message": "Task deletion was rejected by the user." }
```

**Operation:** Write (gated)
**Approval required:** Yes

**Possible errors**
| Code | Cause |
|---|---|
| `TASK_NOT_FOUND` | No matching task |
| `AMBIGUOUS_TITLE_MATCH` | Multiple candidates match `task_title` |
| `APPROVAL_REJECTED` | User rejected the request |
| `DB_WRITE_ERROR` | Delete failed after approval |

**Example call**
```json
{ "tool": "delete_task", "args": { "task_title": "Book the venue" } }
```

**Example result (phase 1)**
```json
{ "success": true, "status": "pending_approval", "approval_id": 22 }
```

**Example result (phase 2, after approval)**
```json
{ "success": true, "deleted_task_id": 14 }
```

---

## 6. `generate_daily_plan`

**Purpose:** Builds a schedule for a given day, assigning suggested time slots to pending tasks, and persists the result as a `Plan`.

**Input schema**
```json
{ "date": "YYYY-MM-DD" }
```
- **Required:** none
- **Optional:** `date` (default: today)

**Output schema**
```json
{
  "success": true,
  "plan": {
    "id": 4, "type": "daily", "period": "2026-07-20",
    "content": {
      "slots": [
        { "task_id": 12, "title": "Submit quarterly report", "suggested_start": "09:00", "suggested_end": "10:30" }
      ]
    },
    "created_at": "2026-07-20T07:00:00Z"
  }
}
```

**Operation:** Read (pending tasks) + Write (persists the `Plan` record)
**Approval required:** No

**Possible errors**
| Code | Cause |
|---|---|
| `NO_PENDING_TASKS` | No tasks with `status: "pending"` exist for scheduling |
| `INVALID_DATE_FORMAT` | `date` not parseable |
| `LLM_GENERATION_FAILED` | LLM call for slot suggestion errored |
| `DB_WRITE_ERROR` | Failed to persist the plan |

**Example call**
```json
{ "tool": "generate_daily_plan", "args": { "date": "2026-07-20" } }
```

**Example result**
```json
{
  "success": true,
  "plan": {
    "id": 4, "type": "daily", "period": "2026-07-20",
    "content": { "slots": [
      { "task_id": 12, "title": "Submit quarterly report", "suggested_start": "09:00", "suggested_end": "10:30" },
      { "task_id": 13, "title": "Email the vendor", "suggested_start": "10:30", "suggested_end": "11:00" }
    ] },
    "created_at": "2026-07-20T07:00:00Z"
  }
}
```

---

## 7. `generate_weekly_plan`

**Purpose:** Builds a 7-day plan distributing pending tasks across days, persisted as a `Plan`.

**Input schema**
```json
{ "week_start": "YYYY-MM-DD" }
```
- **Required:** none
- **Optional:** `week_start` (default: the upcoming Monday)

**Output schema**
```json
{
  "success": true,
  "plan": {
    "id": 5, "type": "weekly", "period": "2026-07-20/2026-07-26",
    "content": {
      "days": [
        { "date": "2026-07-20", "tasks": [12, 13] },
        { "date": "2026-07-21", "tasks": [14] }
      ]
    },
    "created_at": "2026-07-20T07:05:00Z"
  }
}
```

**Operation:** Read + Write
**Approval required:** No

**Possible errors**
| Code | Cause |
|---|---|
| `NO_PENDING_TASKS` | Nothing to distribute across the week |
| `INVALID_DATE_FORMAT` | `week_start` not parseable |
| `LLM_GENERATION_FAILED` | LLM call errored |
| `DB_WRITE_ERROR` | Failed to persist the plan |

**Example call**
```json
{ "tool": "generate_weekly_plan", "args": {} }
```

**Example result**
```json
{
  "success": true,
  "plan": {
    "id": 5, "type": "weekly", "period": "2026-07-20/2026-07-26",
    "content": { "days": [
      { "date": "2026-07-20", "tasks": [12, 13] },
      { "date": "2026-07-21", "tasks": [14] },
      { "date": "2026-07-22", "tasks": [] }
    ] },
    "created_at": "2026-07-20T07:05:00Z"
  }
}
```

---

## 8. `generate_productivity_report`

**Purpose:** Produces weekly statistics (completion rate, task breakdown by priority/status) with a short narrative summary, persisted as a `Plan` of type `"report"`.

**Input schema**
```json
{ "week_start": "YYYY-MM-DD" }
```
- **Required:** none
- **Optional:** `week_start` (default: start of current week)

**Output schema**
```json
{
  "success": true,
  "report": {
    "id": 6, "type": "report", "period": "2026-07-13/2026-07-19",
    "content": {
      "stats": { "completed": 8, "pending": 3, "overdue": 1, "completion_rate": 0.73 },
      "summary": "string"
    },
    "created_at": "2026-07-20T07:10:00Z"
  }
}
```

**Operation:** Read + Write
**Approval required:** No

**Possible errors**
| Code | Cause |
|---|---|
| `NO_DATA_FOR_PERIOD` | No tasks exist within the requested week |
| `DB_READ_ERROR` | Query failed |
| `LLM_SUMMARY_FAILED` | LLM narrative generation errored (stats are still returned without `summary`) |

**Example call**
```json
{ "tool": "generate_productivity_report", "args": { "week_start": "2026-07-13" } }
```

**Example result**
```json
{
  "success": true,
  "report": {
    "id": 6, "type": "report", "period": "2026-07-13/2026-07-19",
    "content": {
      "stats": { "completed": 8, "pending": 3, "overdue": 1, "completion_rate": 0.73 },
      "summary": "A productive week with most high-priority items closed out; one overdue task needs attention."
    },
    "created_at": "2026-07-20T07:10:00Z"
  }
}
```

---

## 9. `analyze_priorities`

**Purpose:** Identifies overdue and urgent tasks and returns a concrete recommendation for what to tackle next.

**Input schema**
```json
{ "as_of_date": "YYYY-MM-DD" }
```
- **Required:** none
- **Optional:** `as_of_date` (default: today)

**Output schema**
```json
{
  "success": true,
  "overdue_tasks": [Task],
  "urgent_tasks": [Task],
  "recommendation": "string"
}
```

**Operation:** Read
**Approval required:** No

**Possible errors**
| Code | Cause |
|---|---|
| `NO_TASKS_FOUND` | No non-completed tasks exist to analyze |
| `LLM_ANALYSIS_FAILED` | LLM call for the recommendation text errored (task lists are still returned) |

**Example call**
```json
{ "tool": "analyze_priorities", "args": {} }
```

**Example result**
```json
{
  "success": true,
  "overdue_tasks": [
    { "id": 9, "title": "Renew software license", "priority": "high", "status": "pending", "due_date": "2026-07-15", "description": null, "created_at": "2026-07-10T08:00:00Z", "updated_at": "2026-07-10T08:00:00Z" }
  ],
  "urgent_tasks": [
    { "id": 12, "title": "Submit quarterly report", "priority": "high", "status": "pending", "due_date": "2026-07-25", "description": null, "created_at": "2026-07-20T10:00:00Z", "updated_at": "2026-07-20T10:00:00Z" }
  ],
  "recommendation": "The software license renewal is overdue by 5 days and should be handled first, before starting the quarterly report."
}
```

---

## 10. `summarize_notes`

**Purpose:** Summarizes a set of notes into decisions made and action items identified.

**Input schema**
```json
{ "note_ids": ["integer"], "keyword": "string" }
```
- **Required:** none — if neither `note_ids` nor `keyword` is given, summarizes the most recent 20 notes
- **Optional:** `note_ids` (explicit subset), `keyword` (filter notes by keyword before summarizing)

**Output schema**
```json
{
  "success": true,
  "summary": { "decisions": ["string"], "action_items": ["string"] },
  "source_note_ids": [7, 8]
}
```

**Operation:** Read
**Approval required:** No

**Possible errors**
| Code | Cause |
|---|---|
| `NO_NOTES_FOUND` | No notes match `note_ids` / `keyword`, or none exist |
| `LLM_SUMMARY_FAILED` | LLM call errored |

**Example call**
```json
{ "tool": "summarize_notes", "args": { "keyword": "client" } }
```

**Example result**
```json
{
  "success": true,
  "summary": {
    "decisions": ["Revised pricing will be sent to the client by Friday."],
    "action_items": ["Prepare updated pricing sheet", "Schedule call with client to review"]
  },
  "source_note_ids": [7]
}
```

---

## 11. `save_note`

**Purpose:** Saves a free-text note for later retrieval.

**Input schema**
```json
{ "content": "string", "tags": ["string"] }
```
- **Required:** `content`
- **Optional:** `tags` (default `[]`)

**Output schema**
```json
{ "success": true, "note": Note }
```

**Operation:** Write
**Approval required:** No

**Possible errors**
| Code | Cause |
|---|---|
| `EMPTY_CONTENT` | `content` is empty or whitespace-only |
| `DB_WRITE_ERROR` | Insert failed |

**Example call**
```json
{ "tool": "save_note", "args": { "content": "Client wants revised pricing by Friday.", "tags": ["client", "pricing"] } }
```

**Example result**
```json
{
  "success": true,
  "note": { "id": 7, "content": "Client wants revised pricing by Friday.", "tags": ["client", "pricing"], "created_at": "2026-07-19T14:02:00Z" }
}
```

---

## 12. `search_notes`

**Purpose:** Searches saved notes by keyword.

**Input schema**
```json
{ "keyword": "string", "limit": "integer" }
```
- **Required:** `keyword`
- **Optional:** `limit` (default `20`, max `100`)

**Output schema**
```json
{ "success": true, "count": 1, "notes": [Note] }
```

**Operation:** Read
**Approval required:** No

**Possible errors**
| Code | Cause |
|---|---|
| `EMPTY_KEYWORD` | `keyword` is empty |
| `DB_READ_ERROR` | Query failed |

**Example call**
```json
{ "tool": "search_notes", "args": { "keyword": "pricing" } }
```

**Example result**
```json
{
  "success": true,
  "count": 1,
  "notes": [ { "id": 7, "content": "Client wants revised pricing by Friday.", "tags": ["client", "pricing"], "created_at": "2026-07-19T14:02:00Z" } ]
}
```

---

## 13. `draft_email`

**Purpose:** Generates a follow-up email (subject + body) from meeting notes or supplied context.

**Input schema**
```json
{ "note_ids": ["integer"], "context": "string", "recipient_name": "string" }
```
- **Required:** at least one of `note_ids` or `context`
- **Optional:** `recipient_name` (used for the greeting; default `"there"`)

**Output schema**
```json
{ "success": true, "email": { "subject": "string", "body": "string" } }
```

**Operation:** Read (fetches notes if `note_ids` given; no DB write)
**Approval required:** No

**Possible errors**
| Code | Cause |
|---|---|
| `NO_SOURCE_CONTENT` | Neither `note_ids` nor `context` resolved to any usable text |
| `LLM_DRAFTING_FAILED` | LLM call errored |

**Example call**
```json
{ "tool": "draft_email", "args": { "note_ids": [7], "recipient_name": "Alex" } }
```

**Example result**
```json
{
  "success": true,
  "email": {
    "subject": "Updated pricing — following up",
    "body": "Hi Alex,\n\nFollowing up on our conversation — we'll have the revised pricing over to you by Friday.\n\nBest,\n"
  }
}
```