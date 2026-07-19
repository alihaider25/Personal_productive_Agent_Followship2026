def validate_input(schema, tool_input):
    errors = []

    for field, rules in schema.items():
        if rules.get("required") and field not in tool_input:
            errors.append(f"Missing required field: {field}")

        if field in tool_input:
            expected_type = rules.get("type")
            value = tool_input[field]

            if expected_type == "string" and not isinstance(value, str):
                errors.append(f"Field '{field}' should be a string")
            elif expected_type == "integer" and not isinstance(value, int):
                errors.append(f"Field '{field}' should be an integer")

    return {"valid": len(errors) == 0, "errors": errors}