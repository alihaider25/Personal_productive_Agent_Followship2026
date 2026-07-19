import json
from services.llm_service import call_llm
from tools.tool_registry import list_tools

def analyze_intent(user_message):
    tools_description = json.dumps(list_tools(), indent=2)

    prompt = f"""You are an AI agent's reasoning module. Given a user's request, decide which tool to use, if any.

Available tools and their input schemas:
{tools_description}

User request: "{user_message}"

Respond ONLY with valid JSON in this exact format, nothing else:
{{
    "needs_tool": true or false,
    "tool_name": "exact_tool_name or null",
    "tool_input": {{"field": "value"}} or {{}},
    "reasoning": "short explanation of why this tool/action was chosen"
}}

If no tool is needed (e.g. the user is just chatting or asking something unrelated to tasks/planning), set needs_tool to false.
Today's date is {__import__('datetime').date.today().isoformat()}, use this to resolve relative dates like "tomorrow" into ISO format (YYYY-MM-DD)."""

    raw_response = call_llm(prompt, max_tokens=300)

    # Clean up in case the model wraps it in markdown code fences
    cleaned = raw_response.strip().replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "needs_tool": False,
            "tool_name": None,
            "tool_input": {},
            "reasoning": "Failed to parse intent - treating as general query"
        }