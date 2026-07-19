from models.db_models import db, ExecutionLog

def log_step(session_key, user_request, step, detail, status="success"):
    entry = ExecutionLog(
        session_key=session_key,
        user_request=user_request,
        step=step,
        detail=str(detail),
        status=status
    )
    db.session.add(entry)
    db.session.commit()