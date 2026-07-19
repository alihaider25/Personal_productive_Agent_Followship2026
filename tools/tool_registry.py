TOOL_REGISTRY = {}

def register_tool(name, schema, func, requires_approval=False, description=""):
    TOOL_REGISTRY[name] = {
        "schema": schema,
        "func": func,
        "requires_approval": requires_approval,
        "description": description
    }

def get_tool(name):
    return TOOL_REGISTRY.get(name)

def list_tools():
    return {
        name: {"description": data["description"], "schema": data["schema"]}
        for name, data in TOOL_REGISTRY.items()
    }