"""
Token counting utilities for the chat application MVP
"""
import tiktoken
from typing import Dict, List, Optional, Union, Any

_encoding = None

def get_encoding():
    """Get the tiktoken encoding for GPT-4o / GPT-4o-mini"""
    global _encoding
    if _encoding is None:
        _encoding = tiktoken.get_encoding("o200k_base")
    return _encoding

def count_tokens(text: str) -> int:
    """Count the number of tokens in a text string"""
    if not text:
        return 0
    
    encoding = get_encoding()
    return len(encoding.encode(text))

def count_message_tokens(role: str, content: str) -> int:
    """Count tokens for a single message (including role formatting)"""
    if not content:
        return 0
    
    # For OpenAI API, messages are formatted as:
    # {"role": "user", "content": "Hello"}
    # The role adds some overhead tokens
    encoding = get_encoding()
    
    # Count content tokens
    content_tokens = len(encoding.encode(content))
    
    # Add overhead for role formatting (approximately 4 tokens per message)
    # This is a rough estimate based on OpenAI's token counting
    role_overhead = 4
    
    return content_tokens + role_overhead

def count_conversation_tokens(messages: List[Dict]) -> Dict[str, Any]:
    """Count total tokens for a conversation"""
    total_input_tokens = 0
    total_output_tokens = 0
    message_tokens = []
    
    for message in messages:
        role = message.get("role", "")
        content = message.get("content", "")
        
        token_count = count_message_tokens(role, content)
        
        # Track tokens by role
        if role == "user":
            total_input_tokens += token_count
        elif role == "assistant":
            total_output_tokens += token_count
        elif role == "system":
            total_input_tokens += token_count
        
        # Store token count for this message
        message_tokens.append({
            "role": role,
            "content": content,
            "token_count": token_count
        })
    
    return {
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "message_tokens": message_tokens
    }

def estimate_api_tokens(messages: List[Dict]) -> Dict[str, int]:
    """Estimate tokens for OpenAI API call (including system overhead)"""
    # Count tokens in messages
    conversation_tokens = count_conversation_tokens(messages)
    
    # Add system overhead (approximately 3 tokens per message)
    system_overhead = len(messages) * 3
    
    return {
        "input_tokens": conversation_tokens["total_input_tokens"] + system_overhead,
        "output_tokens": conversation_tokens["total_output_tokens"]
    } 