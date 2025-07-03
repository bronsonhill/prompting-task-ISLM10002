"""
Database operations for the chat application MVP
"""
import streamlit as st
from pymongo import MongoClient
from datetime import datetime
from typing import Dict, List, Optional
import string
import random

# Global MongoDB client
_client = None
_db = None

def connect_mongodb():
    """Initialize MongoDB connection using Streamlit secrets"""
    global _client, _db
    
    if _client is None:
        try:
            connection_string = st.secrets["mongodb"]["connection_string"]
            database_name = st.secrets["mongodb"]["database_name"]
            
            _client = MongoClient(connection_string)
            _db = _client[database_name]
            
            # Test connection
            _client.admin.command('ping')
            print(f"Successfully connected to MongoDB database: {database_name}")
            
        except Exception as e:
            st.error(f"Failed to connect to MongoDB: {str(e)}")
            raise e
    
    return _db

def get_database():
    """Get the database instance"""
    if _db is None:
        return connect_mongodb()
    return _db

def create_user(code: str, data_use_consent: Optional[bool] = None) -> bool:
    """Create a new user with the given code"""
    try:
        db = get_database()
        users_collection = db.users
        
        # Check if user already exists
        if users_collection.find_one({"code": code}):
            return False
        
        user_data = {
            "code": code,
            "data_use_consent": data_use_consent,
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow()
        }
        
        result = users_collection.insert_one(user_data)
        return result.inserted_id is not None
        
    except Exception as e:
        st.error(f"Error creating user: {str(e)}")
        return False

def get_user_data(code: str) -> Optional[Dict]:
    """Get user data by code"""
    try:
        db = get_database()
        users_collection = db.users
        return users_collection.find_one({"code": code})
    except Exception as e:
        st.error(f"Error getting user data: {str(e)}")
        return None

def update_last_login(code: str) -> bool:
    """Update user's last login timestamp"""
    try:
        db = get_database()
        users_collection = db.users
        
        result = users_collection.update_one(
            {"code": code},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        return result.modified_count > 0
    except Exception as e:
        st.error(f"Error updating last login: {str(e)}")
        return False

def set_data_consent(code: str, consent: bool) -> bool:
    """Set data use consent for a user"""
    try:
        db = get_database()
        users_collection = db.users
        
        result = users_collection.update_one(
            {"code": code},
            {"$set": {"data_use_consent": consent}}
        )
        return result.modified_count > 0
    except Exception as e:
        st.error(f"Error setting data consent: {str(e)}")
        return False

def save_prompt(user_code: str, content: str) -> Optional[str]:
    """Save a new prompt and return its ID"""
    try:
        db = get_database()
        prompts_collection = db.prompts
        
        # Generate next prompt ID
        latest_prompt = prompts_collection.find().sort("prompt_id", -1).limit(1)
        latest_prompt = list(latest_prompt)
        
        if latest_prompt:
            latest_id = int(latest_prompt[0]["prompt_id"][1:])  # Remove 'P' prefix
            next_id = f"P{latest_id + 1:03d}"
        else:
            next_id = "P001"
        
        prompt_data = {
            "prompt_id": next_id,
            "user_code": user_code,
            "content": content,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = prompts_collection.insert_one(prompt_data)
        if result.inserted_id:
            return next_id
        return None
        
    except Exception as e:
        st.error(f"Error saving prompt: {str(e)}")
        return None

def get_user_prompts(user_code: str) -> List[Dict]:
    """Get all prompts for a user"""
    try:
        db = get_database()
        prompts_collection = db.prompts
        
        prompts = list(prompts_collection.find(
            {"user_code": user_code}
        ).sort("created_at", -1))
        
        return prompts
    except Exception as e:
        st.error(f"Error getting user prompts: {str(e)}")
        return []

def get_prompt_by_id(prompt_id: str) -> Optional[Dict]:
    """Get a specific prompt by ID"""
    try:
        db = get_database()
        prompts_collection = db.prompts
        return prompts_collection.find_one({"prompt_id": prompt_id})
    except Exception as e:
        st.error(f"Error getting prompt: {str(e)}")
        return None

def save_conversation(user_code: str, prompt_id: str, messages: List[Dict]) -> Optional[str]:
    """Save a conversation and return its ID"""
    try:
        db = get_database()
        conversations_collection = db.conversations
        
        # Generate next conversation ID
        latest_conversation = conversations_collection.find().sort("conversation_id", -1).limit(1)
        latest_conversation = list(latest_conversation)
        
        if latest_conversation:
            latest_id = int(latest_conversation[0]["conversation_id"][1:])  # Remove 'C' prefix
            next_id = f"C{latest_id + 1:03d}"
        else:
            next_id = "C001"
        
        conversation_data = {
            "conversation_id": next_id,
            "user_code": user_code,
            "prompt_id": prompt_id,
            "messages": messages,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = conversations_collection.insert_one(conversation_data)
        if result.inserted_id:
            return next_id
        return None
        
    except Exception as e:
        st.error(f"Error saving conversation: {str(e)}")
        return None

def update_conversation(conversation_id: str, messages: List[Dict]) -> bool:
    """Update an existing conversation with new messages"""
    try:
        db = get_database()
        conversations_collection = db.conversations
        
        result = conversations_collection.update_one(
            {"conversation_id": conversation_id},
            {
                "$set": {
                    "messages": messages,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    except Exception as e:
        st.error(f"Error updating conversation: {str(e)}")
        return False

def get_user_conversations(user_code: str) -> List[Dict]:
    """Get all conversations for a user"""
    try:
        db = get_database()
        conversations_collection = db.conversations
        
        conversations = list(conversations_collection.find(
            {"user_code": user_code}
        ).sort("updated_at", -1))
        
        return conversations
    except Exception as e:
        st.error(f"Error getting user conversations: {str(e)}")
        return []

def get_conversation_by_id(conversation_id: str) -> Optional[Dict]:
    """Get a specific conversation by ID"""
    try:
        db = get_database()
        conversations_collection = db.conversations
        return conversations_collection.find_one({"conversation_id": conversation_id})
    except Exception as e:
        st.error(f"Error getting conversation: {str(e)}")
        return None

def log_action(user_code: str, action: str, data: Dict) -> bool:
    """Log user action"""
    try:
        db = get_database()
        logs_collection = db.logs
        
        log_data = {
            "user_code": user_code,
            "action": action,
            "data": data,
            "timestamp": datetime.utcnow()
        }
        
        result = logs_collection.insert_one(log_data)
        return result.inserted_id is not None
        
    except Exception as e:
        print(f"Error logging action: {str(e)}")  # Don't show to user, just print
        return False

def generate_unique_code(length: int = 5) -> str:
    """Generate a unique user code"""
    db = get_database()
    users_collection = db.users
    
    characters = string.ascii_uppercase + string.digits
    
    while True:
        code = ''.join(random.choices(characters, k=length))
        if not users_collection.find_one({"code": code}):
            return code

def id_to_display_number(id_string: str) -> int:
    """Convert a string ID (like 'P001' or 'C001') to an integer for display"""
    if not id_string:
        return 0
    
    # Remove prefix and convert to integer
    if id_string.startswith('P') or id_string.startswith('C'):
        try:
            return int(id_string[1:])
        except ValueError:
            return 0
    
    # If it's already a number, try to convert directly
    try:
        return int(id_string)
    except ValueError:
        return 0