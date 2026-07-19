from app import app
from models.db_models import db, Task, Note, ExecutionLog, ApprovalRequest, AgentMessage

with app.app_context():
    confirm = input("This will DELETE all tasks, notes, logs, approvals, and chat history. Type 'yes' to confirm: ")

    if confirm.strip().lower() == "yes":
        deleted_tasks = Task.query.delete()
        deleted_notes = Note.query.delete()
        deleted_logs = ExecutionLog.query.delete()
        deleted_approvals = ApprovalRequest.query.delete()
        deleted_messages = AgentMessage.query.delete()

        db.session.commit()

        print(f"\nDeleted:")
        print(f"  {deleted_tasks} tasks")
        print(f"  {deleted_notes} notes")
        print(f"  {deleted_logs} execution logs")
        print(f"  {deleted_approvals} approval requests")
        print(f"  {deleted_messages} chat messages")
        print("\nDatabase is now clean.")
    else:
        print("Cancelled — nothing was deleted.")