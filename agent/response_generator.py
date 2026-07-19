from services.llm_service import call_llm

def generate_response(user_message, tool_name, tool_result):
    prompt = f"""The user asked: "{user_message}"

A tool named "{tool_name}" was executed with this result:
{tool_result}

Write a short, clear, natural-language response to the user summarizing what happened. Do not mention JSON or technical details. Keep it under 3 sentences."""

    return call_llm(prompt, max_tokens=150)


def generate_plain_response(user_message):
    """Used when no tool is needed - a general conversational reply."""
    prompt = f"""You are a helpful productivity assistant. The user said: "{user_message}"

This request does not require any tool. Respond helpfully and briefly."""
    return call_llm(prompt, max_tokens=150)