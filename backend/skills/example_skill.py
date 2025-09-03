"""
Example skill that demonstrates the skill interface.
This skill processes messages by converting them to uppercase.
"""

def run(message: str) -> dict:
    """
    Example skill that converts messages to uppercase
    
    Args:
        message: The user message to process
        
    Returns:
        Dictionary with success status and result
    """
    try:
        if not message or not isinstance(message, str):
            return {
                "success": False,
                "error": "Invalid message input",
                "skill_name": "example_skill"
            }
        
        processed = message.upper()
        
        return {
            "success": True,
            "result": f"EXAMPLE SKILL OUTPUT: {processed}",
            "skill_name": "example_skill"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "skill_name": "example_skill"
        }