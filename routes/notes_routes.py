from flask import Blueprint, render_template
from models.db_models import Note

notes_bp = Blueprint("notes_bp", __name__)


@notes_bp.route("/notes")
def notes_page():
    notes = Note.query.order_by(Note.created_at.desc()).all()
    return render_template("notes.html", notes=notes)