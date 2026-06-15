def handle_error(operation: str, error: Exception) -> str:
    error_msg = str(error)
    if "404" in error_msg:
        return f"Error: Resource not found during {operation}. Please check the ID is correct."
    elif "403" in error_msg or "unauthorized" in error_msg.lower():
        return f"Error: Permission denied during {operation}. Check your API keys."
    elif "429" in error_msg:
        return f"Error: Rate limit exceeded during {operation}. Please wait and try again."
    elif "timeout" in error_msg.lower():
        return f"Error: Request timed out during {operation}. Please try again."
    return f"Error during {operation}: {error_msg}"
