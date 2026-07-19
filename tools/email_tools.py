def draft_email(session_key, notes_text, recipient_context=""):
    """Drafts a follow-up email based on meeting notes or context provided."""
    from services.llm_service import call_llm

    prompt = f"""Draft a professional follow-up email based on these notes.
{f"Context about the recipient: {recipient_context}" if recipient_context else ""}

Notes:
{notes_text}

Write the email with a clear subject line and body. Keep it concise and professional. 
Format as:
Subject: ...

Body:
..."""

    draft = call_llm(prompt, max_tokens=350)

    return {
        "success": True,
        "draft": draft
    }