from models.db_models import db, Note


def save_note(session_key, content, title=""):
    note = Note(session_key=session_key, title=title or content[:50], content=content)
    db.session.add(note)
    db.session.commit()

    return {"success": True, "note_id": note.id, "title": note.title}


def search_notes(session_key, query):
    """Simple keyword search across saved notes."""
    notes = Note.query.filter(
        Note.session_key == session_key,
        Note.content.ilike(f"%{query}%")
    ).order_by(Note.created_at.desc()).all()

    return {
        "success": True,
        "count": len(notes),
        "notes": [{"id": n.id, "title": n.title, "content": n.content[:200]} for n in notes]
    }