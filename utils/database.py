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
        # Return True if the document was found (matched_count > 0), regardless of whether it was modified
        return result.matched_count > 0
    except Exception as e:
        st.error(f"Error setting data consent: {str(e)}")
        return False

def save_prompt(user_code: str, content: str, documents: List[Dict] = None) -> Optional[str]:
    """Save a new prompt and return its ID"""
    try:
        db = get_database()
        prompts_collection = db.prompts
        
        # Use atomic operation to get and increment the next prompt ID for this user
        # This prevents race conditions when multiple prompts are created simultaneously
        counter_collection = db.counters
        
        # Get the next prompt ID atomically for this specific user
        result = counter_collection.find_one_and_update(
            {"_id": f"prompt_id_{user_code}"},
            {"$inc": {"sequence": 1}},
            upsert=True,
            return_document=True
        )
        
        next_id = f"P{result['sequence']:03d}"
        
        # Count tokens for the prompt
        from utils.token_counter import count_tokens
        prompt_token_count = count_tokens(content)
        
        # Count tokens for documents if provided
        document_token_count = 0
        if documents:
            for doc in documents:
                document_token_count += count_tokens(doc.get('content', ''))
        
        prompt_data = {
            "prompt_id": next_id,
            "user_code": user_code,
            "content": content,
            "documents": documents or [],
            "prompt_token_count": prompt_token_count,
            "document_token_count": document_token_count,
            "total_token_count": prompt_token_count + document_token_count,
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

def get_user_prompts_lightweight(user_code: str) -> List[Dict]:
    """Get prompts without heavy document content for list views"""
    try:
        db = get_database()
        prompts_collection = db.prompts
        
        prompts = list(prompts_collection.find(
            {"user_code": user_code},
            {
                "prompt_id": 1,
                "content": 1,
                "created_at": 1,
                "updated_at": 1,
                "documents.filename": 1,
                "documents.file_type": 1,
                "documents.file_size": 1,
                "documents.uploaded_at": 1,
                "prompt_token_count": 1,
                "document_token_count": 1,
                "total_token_count": 1
            }
        ).sort("created_at", -1))
        
        return prompts
    except Exception as e:
        st.error(f"Error getting user prompts: {str(e)}")
        return []

def get_prompt_documents(prompt_id: str, user_code: str) -> List[Dict]:
    """Load document content only when specifically requested"""
    try:
        db = get_database()
        prompts_collection = db.prompts
        
        prompt = prompts_collection.find_one(
            {"prompt_id": prompt_id, "user_code": user_code},
            {"documents": 1}
        )
        
        return prompt.get("documents", []) if prompt else []
    except Exception as e:
        st.error(f"Error getting prompt documents: {str(e)}")
        return []

def get_prompt_with_documents(prompt_id: str, user_code: str = None) -> Optional[Dict]:
    """Get a specific prompt with full document content (for chat usage)"""
    try:
        db = get_database()
        prompts_collection = db.prompts
        
        # Build query - always filter by prompt_id
        query = {"prompt_id": prompt_id}
        
        # If user_code is provided, also filter by user ownership
        if user_code:
            query["user_code"] = user_code
            
        return prompts_collection.find_one(query)
    except Exception as e:
        st.error(f"Error getting prompt with documents: {str(e)}")
        return None

def get_prompt_by_id(prompt_id: str, user_code: str = None) -> Optional[Dict]:
    """Get a specific prompt by ID, optionally filtered by user"""
    try:
        db = get_database()
        prompts_collection = db.prompts
        
        # Build query - always filter by prompt_id
        query = {"prompt_id": prompt_id}
        
        # If user_code is provided, also filter by user ownership
        if user_code:
            query["user_code"] = user_code
            
        return prompts_collection.find_one(query)
    except Exception as e:
        st.error(f"Error getting prompt: {str(e)}")
        return None

def process_uploaded_document(uploaded_file) -> Optional[Dict]:
    """Process an uploaded document and extract its content"""
    try:
        import io
        
        file_info = {
            "filename": uploaded_file.name,
            "file_type": uploaded_file.type,
            "file_size": uploaded_file.size,
            "uploaded_at": datetime.utcnow()
        }
        
        # Read file content based on type
        if uploaded_file.type == "application/pdf":
            # Handle PDF files
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text() + "\n"
                file_info["content"] = content.strip()
            except ImportError:
                st.error("PyPDF2 is required for PDF processing. Please install it: pip install PyPDF2")
                return None
            
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # Handle DOCX files
            try:
                import docx
                doc = docx.Document(io.BytesIO(uploaded_file.read()))
                content = ""
                for paragraph in doc.paragraphs:
                    content += paragraph.text + "\n"
                file_info["content"] = content.strip()
            except ImportError:
                st.error("python-docx is required for DOCX processing. Please install it: pip install python-docx")
                return None
            
        elif uploaded_file.type == "text/plain":
            # Handle text files
            content = uploaded_file.read().decode("utf-8")
            file_info["content"] = content
            
        else:
            st.error(f"Unsupported file type: {uploaded_file.type}")
            return None
        
        # Validate content
        if not file_info.get("content", "").strip():
            st.warning(f"Warning: Document '{uploaded_file.name}' appears to be empty or could not be read properly.")
        
        return file_info
        
    except Exception as e:
        st.error(f"Error processing document '{uploaded_file.name}': {str(e)}")
        return None

def update_prompt_token_counts():
    """Update all existing prompts with token counts"""
    try:
        db = get_database()
        prompts_collection = db.prompts
        
        # Get all prompts that need token count updates
        prompts_to_update = list(prompts_collection.find({
            "$or": [
                {"token_count": {"$exists": False}},
                {"prompt_token_count": {"$exists": False}},
                {"document_token_count": {"$exists": False}},
                {"total_token_count": {"$exists": False}}
            ]
        }))
        
        if not prompts_to_update:
            return 0
        
        from utils.token_counter import count_tokens
        updated_count = 0
        
        for prompt in prompts_to_update:
            # Calculate prompt token count
            prompt_token_count = count_tokens(prompt['content'])
            
            # Calculate document token count
            document_token_count = 0
            if prompt.get('documents'):
                for doc in prompt['documents']:
                    document_token_count += count_tokens(doc.get('content', ''))
            
            # Calculate total token count
            total_token_count = prompt_token_count + document_token_count
            
            # Update with new token count fields
            set_data = {
                "prompt_token_count": prompt_token_count,
                "document_token_count": document_token_count,
                "total_token_count": total_token_count
            }
            
            # Prepare update operation
            update_operation = {"$set": set_data}
            
            # Remove legacy token_count field if it exists
            if "token_count" in prompt:
                update_operation["$unset"] = {"token_count": ""}
            
            result = prompts_collection.update_one(
                {"_id": prompt['_id']},
                update_operation
            )
            
            if result.modified_count > 0:
                updated_count += 1
        
        return updated_count
        
    except Exception as e:
        st.error(f"Error updating prompt token counts: {str(e)}")
        return 0

def save_conversation(user_code: str, prompt_id: str, messages: List[Dict]) -> Optional[str]:
    """Save a conversation and return its ID"""
    try:
        db = get_database()
        conversations_collection = db.conversations
        
        # Use atomic operation to get and increment the next conversation ID
        # This prevents race conditions when multiple conversations are created simultaneously
        counter_collection = db.counters
        
        # Get the next conversation ID atomically
        result = counter_collection.find_one_and_update(
            {"_id": "conversation_id"},
            {"$inc": {"sequence": 1}},
            upsert=True,
            return_document=True
        )
        
        next_id = f"C{result['sequence']:03d}"
        
        # Calculate token statistics
        from utils.token_counter import count_conversation_tokens
        token_stats = count_conversation_tokens(messages)
        
        # Add token counts to each message
        messages_with_tokens = []
        for i, message in enumerate(messages):
            message_with_tokens = message.copy()
            message_with_tokens["token_count"] = token_stats["message_tokens"][i]["token_count"]
            messages_with_tokens.append(message_with_tokens)
        
        conversation_data = {
            "conversation_id": next_id,
            "user_code": user_code,
            "prompt_id": prompt_id,
            "messages": messages_with_tokens,
            "token_stats": {
                "total_input_tokens": token_stats["total_input_tokens"],
                "total_output_tokens": token_stats["total_output_tokens"]
            },
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

def update_conversation(conversation_id: str, messages: List[Dict], user_code: str = None) -> bool:
    """Update an existing conversation with new messages"""
    try:
        db = get_database()
        conversations_collection = db.conversations
        
        # Calculate token statistics
        from utils.token_counter import count_conversation_tokens
        token_stats = count_conversation_tokens(messages)
        
        # Add token counts to each message
        messages_with_tokens = []
        for i, message in enumerate(messages):
            message_with_tokens = message.copy()
            message_with_tokens["token_count"] = token_stats["message_tokens"][i]["token_count"]
            messages_with_tokens.append(message_with_tokens)
        
        # Build query - always filter by conversation_id and user_code if provided
        query = {"conversation_id": conversation_id}
        if user_code:
            query["user_code"] = user_code
        
        result = conversations_collection.update_one(
            query,
            {
                "$set": {
                    "messages": messages_with_tokens,
                    "token_stats": {
                        "total_input_tokens": token_stats["total_input_tokens"],
                        "total_output_tokens": token_stats["total_output_tokens"]
                    },
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

def get_user_conversations_lightweight(user_code: str, limit: int = 20) -> List[Dict]:
    """Get conversations without full message content for list views"""
    try:
        db = get_database()
        conversations_collection = db.conversations
        
        conversations = list(conversations_collection.find(
            {"user_code": user_code},
            {
                "conversation_id": 1,
                "prompt_id": 1,
                "created_at": 1,
                "updated_at": 1,
                "messages": {"$slice": 1},  # Only get first message (system message)
                "token_stats": 1
            }
        ).sort("updated_at", -1).limit(limit))
        
        return conversations
    except Exception as e:
        st.error(f"Error getting user conversations: {str(e)}")
        return []

def get_conversation_messages(conversation_id: str, user_code: str) -> List[Dict]:
    """Load full message content only when specifically requested"""
    try:
        db = get_database()
        conversations_collection = db.conversations
        
        conversation = conversations_collection.find_one(
            {"conversation_id": conversation_id, "user_code": user_code},
            {"messages": 1}
        )
        
        return conversation.get("messages", []) if conversation else []
    except Exception as e:
        st.error(f"Error getting conversation messages: {str(e)}")
        return []

def get_conversation_by_id(conversation_id: str, user_code: str = None) -> Optional[Dict]:
    """Get a specific conversation by ID, optionally filtered by user"""
    try:
        db = get_database()
        conversations_collection = db.conversations
        
        # Build query - always filter by conversation_id
        query = {"conversation_id": conversation_id}
        
        # If user_code is provided, also filter by user ownership
        if user_code:
            query["user_code"] = user_code
        
        result = conversations_collection.find_one(query)
        return result
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

# Admin code management functions
def add_admin_code(code: str, level: str = "admin", added_by: str = "system") -> bool:
    """Add an admin code to the database"""
    try:
        db = get_database()
        admin_codes_collection = db.admin_codes
        
        # Check if admin code already exists
        if admin_codes_collection.find_one({"code": code.upper()}):
            return False
        
        admin_data = {
            "code": code.upper(),
            "level": level,  # "admin" or "super_admin"
            "added_by": added_by,
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        
        result = admin_codes_collection.insert_one(admin_data)
        return result.inserted_id is not None
        
    except Exception as e:
        st.error(f"Error adding admin code: {str(e)}")
        return False

def remove_admin_code(code: str, removed_by: str = "system") -> bool:
    """Remove an admin code from the database (soft delete)"""
    try:
        db = get_database()
        admin_codes_collection = db.admin_codes
        
        # Soft delete by setting is_active to False
        result = admin_codes_collection.update_one(
            {"code": code.upper()},
            {
                "$set": {
                    "is_active": False,
                    "removed_by": removed_by,
                    "removed_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
        
    except Exception as e:
        st.error(f"Error removing admin code: {str(e)}")
        return False

def get_admin_codes(include_inactive: bool = False) -> List[Dict]:
    """Get all admin codes from the database"""
    try:
        db = get_database()
        admin_codes_collection = db.admin_codes
        
        query = {}
        if not include_inactive:
            query["is_active"] = True
        
        admin_codes = list(admin_codes_collection.find(query).sort("created_at", -1))
        return admin_codes
        
    except Exception as e:
        st.error(f"Error getting admin codes: {str(e)}")
        return []

def is_admin_code(code: str) -> bool:
    """Check if a code is an active admin code"""
    try:
        db = get_database()
        admin_codes_collection = db.admin_codes
        
        admin_data = admin_codes_collection.find_one({
            "code": code.upper(),
            "is_active": True
        })
        
        return admin_data is not None
        
    except Exception as e:
        st.error(f"Error checking admin code: {str(e)}")
        return False

def get_admin_level(code: str) -> Optional[str]:
    """Get the admin level for a given code"""
    try:
        db = get_database()
        admin_codes_collection = db.admin_codes
        
        admin_data = admin_codes_collection.find_one({
            "code": code.upper(),
            "is_active": True
        })
        
        return admin_data.get("level") if admin_data else None
        
    except Exception as e:
        st.error(f"Error getting admin level: {str(e)}")
        return None

def is_super_admin(code: str) -> bool:
    """Check if a code is a super admin"""
    return get_admin_level(code) == "super_admin"

def generate_unique_admin_code(length: int = 5) -> str:
    """Generate a unique admin code"""
    db = get_database()
    admin_codes_collection = db.admin_codes
    
    characters = string.ascii_uppercase + string.digits
    
    while True:
        code = ''.join(random.choices(characters, k=length))
        if not admin_codes_collection.find_one({"code": code}):
            return code

def create_initial_admin_code(level: str = "super_admin", added_by: str = "system") -> Optional[str]:
    """Create the first admin code in the system (for initial setup)"""
    try:
        db = get_database()
        admin_codes_collection = db.admin_codes
        
        # Check if any admin codes already exist
        existing_codes = admin_codes_collection.count_documents({"is_active": True})
        
        if existing_codes > 0:
            print("Admin codes already exist. Use add_admin_code() to add more.")
            return None
        
        # Generate a unique admin code
        code = generate_unique_admin_code()
        
        # Add the admin code
        if add_admin_code(code, level, added_by):
            print(f"✅ Initial admin code created: {code}")
            print(f"⚠️  IMPORTANT: Save this code securely! It cannot be recovered.")
            return code
        else:
            print("❌ Failed to create initial admin code")
            return None
            
    except Exception as e:
        st.error(f"Error creating initial admin code: {str(e)}")
        return None

def initialize_default_admin_codes():
    """Initialize default admin codes if they don't exist - DEPRECATED"""
    print("⚠️  WARNING: initialize_default_admin_codes() is deprecated.")
    print("   Use create_initial_admin_code() for secure admin code creation.")
    print("   Or use the admin management script: python scripts/manage_admin_codes.py --add CODE --level admin")
    return False