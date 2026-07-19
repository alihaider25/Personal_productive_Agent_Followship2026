import sys, os, uuid
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
import tools
from agent.controller import run_agent
from models.db_models import ApprovalRequest


def run_test(name, user_message, expected_tool=None, expect_approval=False, expect_no_tool=False):
    session_key = f"eval_{uuid.uuid4().hex[:8]}"
    result = run_agent(session_key, user_message)

    passed = True
    reasons = []

    if expect_no_tool:
        if result.get("tool_used") is not None:
            passed = False
            reasons.append(f"Expected no tool, but got '{result.get('tool_used')}'")
    else:
        if result.get("tool_used") != expected_tool:
            passed = False
            reasons.append(f"Expected tool '{expected_tool}', got '{result.get('tool_used')}'")

    if expect_approval and not result.get("needs_approval"):
        passed = False
        reasons.append("Expected this action to require approval, but it executed directly")

    if not expect_approval and result.get("needs_approval"):
        passed = False
        reasons.append("Did not expect approval requirement, but one was triggered")

    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}")
    print(f"    Input: \"{user_message}\"")
    print(f"    Reply: {result.get('reply')[:100]}")
    if reasons:
        for r in reasons:
            print(f"    Reason: {r}")
    print()

    return passed


def run_invalid_input_test():
    """Tests that the agent handles a request with missing required info gracefully."""
    session_key = f"eval_{uuid.uuid4().hex[:8]}"
    result = run_agent(session_key, "Create a task")  # no title given

    # Should either ask for clarification or fail gracefully, not crash
    passed = result.get("reply") is not None and len(result.get("reply", "")) > 0
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] Invalid/incomplete input handling")
    print(f"    Input: \"Create a task\" (no title provided)")
    print(f"    Reply: {result.get('reply')[:150]}")
    print()
    return passed


def run_unknown_request_test():
    """Tests that a request unrelated to any tool doesn't force a tool call."""
    session_key = f"eval_{uuid.uuid4().hex[:8]}"
    result = run_agent(session_key, "What's the capital of France?")

    passed = result.get("tool_used") is None
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] Unrelated request does not trigger a tool")
    print(f"    Input: \"What's the capital of France?\"")
    print(f"    Reply: {result.get('reply')[:100]}")
    print()
    return passed


if __name__ == "__main__":
    with app.app_context():
        results = []

        results.append(run_test(
            "Create task - correct tool selection",
            "Create a task to call the client tomorrow",
            expected_tool="create_task",
            expect_approval=False
        ))

        results.append(run_test(
            "List tasks - correct tool selection",
            "Show me all my pending tasks",
            expected_tool="list_tasks",
            expect_approval=False
        ))

        results.append(run_test(
            "Complete task - requires approval",
            "Mark task 1 as done",
            expected_tool="complete_task",
            expect_approval=True
        ))

        results.append(run_test(
            "Weekly plan - correct tool selection",
            "Give me a plan for this week",
            expected_tool="generate_weekly_plan",
            expect_approval=False
        ))

        results.append(run_test(
            "Priority analysis - correct tool selection",
            "What are my overdue or urgent tasks?",
            expected_tool="analyze_priorities",
            expect_approval=False
        ))

        results.append(run_unknown_request_test())
        results.append(run_invalid_input_test())
        results.append(run_test(
            "Multi-task creation from notes",
            "Create tasks from these notes: Call the vendor, high priority. Send the invoice by Monday.",
            expected_tool="create_tasks_from_text",
            expect_approval=False
        ))

        results.append(run_test(
            "Save note",
            "Save a note: The client meeting is rescheduled to next week.",
            expected_tool="save_note",
            expect_approval=False
        ))

        results.append(run_test(
            "Search notes",
            "Search my notes for information about the client meeting",
            expected_tool="search_notes",
            expect_approval=False
        ))

        results.append(run_test(
            "Draft email",
            "Draft a follow-up email based on these notes: We agreed to extend the deadline to Friday.",
            expected_tool="draft_email",
            expect_approval=False
        ))

        results.append(run_test(
            "Productivity report - correct tool (not weekly plan)",
            "Prepare a weekly productivity report",
            expected_tool="generate_productivity_report",
            expect_approval=False
        ))

        results.append(run_test(
            "Complete task by title (not ID)",
            "Mark the invoice task as complete",
            expected_tool="complete_task",
            expect_approval=True
        ))
        total = len(results)
        passed = sum(results)
        print("=" * 50)
        print(f"RESULTS: {passed}/{total} test cases passed")
        print("=" * 50)