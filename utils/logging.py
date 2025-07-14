"""
Logging utilities for the chat application MVP
"""
from .database import log_action
from datetime import datetime
from typing import Dict, Any, Optional

def log_chat_message(user_code: str, prompt_id: str, role: str, content: str) -> bool:
    """Log a chat message"""
    from .token_counter import count_message_tokens
    
    token_count = count_message_tokens(role, content)
    
    data = {
        "prompt_id": prompt_id,
        "role": role,
        "content": content,
        "token_count": token_count,
        "message_timestamp": datetime.utcnow().isoformat()
    }
    return log_action(user_code, "chat_message", data)

def log_prompt_creation(user_code: str, prompt_id: str, content: str) -> bool:
    """Log prompt creation"""
    data = {
        "prompt_id": prompt_id,
        "content": content,
        "content_length": len(content)
    }
    return log_action(user_code, "prompt_create", data)

def log_conversation_start(user_code: str, conversation_id: str, prompt_id: str) -> bool:
    """Log the start of a new conversation"""
    data = {
        "conversation_id": conversation_id,
        "prompt_id": prompt_id
    }
    return log_action(user_code, "conversation_start", data)

def log_conversation_continue(user_code: str, conversation_id: str) -> bool:
    """Log continuing an existing conversation"""
    data = {
        "conversation_id": conversation_id
    }
    return log_action(user_code, "conversation_continue", data)

def log_page_visit(user_code: str, page_name: str) -> bool:
    """Log page visit"""
    data = {
        "page_name": page_name
    }
    return log_action(user_code, "page_visit", data)

def log_prompt_selection(user_code: str, prompt_id: str) -> bool:
    """Log prompt selection for chat"""
    data = {
        "prompt_id": prompt_id
    }
    return log_action(user_code, "prompt_selection", data)

def log_error(user_code: str, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None) -> bool:
    """Log an error"""
    data = {
        "error_type": error_type,
        "error_message": error_message,
        "context": context or {}
    }
    return log_action(user_code, "error", data)

def log_user_action(user_code: str, action_type: str, details: Optional[Dict[str, Any]] = None) -> bool:
    """Generic function to log any user action"""
    data = details or {}
    return log_action(user_code, action_type, data)