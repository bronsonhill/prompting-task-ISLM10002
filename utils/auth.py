"""
Authentication utilities for the chat application MVP
"""
import streamlit as st
from .database import (
    get_user_data, create_user, update_last_login, set_data_consent, log_action,
    is_admin_code, get_admin_level, is_super_admin, get_admin_codes, add_admin_code, remove_admin_code
)
from typing import Optional

def validate_user_code(code: str) -> bool:
    """Validate a 5-character user code"""
    if not code or len(code) != 5:
        return False
    
    # Check if code contains only alphanumeric characters
    if not code.isalnum():
        return False
    
    return True

def is_admin_user(code: str) -> bool:
    """Check if user code has admin privileges"""
    return is_admin_code(code)

def get_admin_codes_list() -> list:
    """Get the list of admin codes from database"""
    return get_admin_codes()

def add_admin_code_auth(code: str, level: str = "admin", added_by: str = "system") -> bool:
    """Add a new admin code (for super admins)"""
    if code and len(code) == 5 and code.isalnum():
        return add_admin_code(code, level, added_by)
    return False

def remove_admin_code_auth(code: str, removed_by: str = "system") -> bool:
    """Remove an admin code (for super admins)"""
    return remove_admin_code(code, removed_by)

def is_super_admin_user(code: str) -> bool:
    """Check if user code has super admin privileges"""
    return is_super_admin(code)

def get_admin_level_user(code: str) -> Optional[str]:
    """Get the admin level for a user code"""
    return get_admin_level(code)

def authenticate_user(code: str) -> bool:
    """Authenticate user and handle login"""
    if not validate_user_code(code):
        return False
    
    user_data = get_user_data(code)
    
    if user_data:
        # Existing user - update last login
        update_last_login(code)
        log_action(code, "login", {"timestamp": user_data.get("last_login")})
        return True
    
    return False

def get_user_session_data(code: str) -> Optional[dict]:
    """Get user data for session management"""
    return get_user_data(code)

def is_first_time_user(code: str) -> bool:
    """Check if user exists in database"""
    user_data = get_user_data(code)
    return user_data is None

def handle_first_time_user(code: str, data_consent: bool) -> bool:
    """Handle first-time user registration"""
    if create_user(code, data_consent):
        log_action(code, "user_created", {"data_consent": data_consent})
        return True
    return False

def update_user_consent(code: str, consent: bool) -> bool:
    """Update user's data consent"""
    if set_data_consent(code, consent):
        log_action(code, "consent_updated", {"data_consent": consent})
        return True
    return False

def has_consent_set(code: str) -> bool:
    """Check if user has set data consent"""
    user_data = get_user_data(code)
    if user_data:
        return user_data.get("data_use_consent") is not None
    return False

def initialize_session():
    """Initialize session state variables"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_code" not in st.session_state:
        st.session_state.user_code = None
    if "user_data" not in st.session_state:
        st.session_state.user_data = None

def login_user(code: str) -> bool:
    """Login user and set session state"""
    code = code.upper().strip()
    
    # Check if user exists
    user_data = get_user_data(code)
    
    if user_data is None:
        # New user - needs consent
        st.session_state.needs_consent = True
        st.session_state.temp_code = code
        return False
    
    # User exists - check if consent is explicitly denied
    if user_data.get("data_use_consent") is False:
        # Existing user with denied consent - needs to reconsider
        st.session_state.needs_consent = True
        st.session_state.temp_code = code
        return False
    
    # User exists and has consent set - proceed with login
    if authenticate_user(code):
        st.session_state.authenticated = True
        st.session_state.user_code = code
        st.session_state.user_data = get_user_session_data(code)
        st.session_state.needs_consent = False
        update_session_admin_status()  # Set admin status
        return True
    
    return False

def logout_user():
    """Logout user and clear session state"""
    if st.session_state.get("user_code"):
        log_action(st.session_state.user_code, "logout", {})
    
    st.session_state.authenticated = False
    st.session_state.user_code = None
    st.session_state.user_data = None
    st.session_state.needs_consent = False
    st.session_state.is_admin = False
    if "temp_code" in st.session_state:
        del st.session_state.temp_code

def require_authentication():
    """Decorator-like function to require authentication"""
    if not st.session_state.get("authenticated", False):
        st.warning("Please log in to access this page.")
        st.stop()

def get_current_user_code() -> Optional[str]:
    """Get the current authenticated user's code"""
    return st.session_state.get("user_code")

def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get("authenticated", False)

def get_current_user_admin_status() -> bool:
    """Get the current user's admin status from session state"""
    user_code = st.session_state.get("user_code")
    if user_code:
        return is_admin_user(user_code)
    return False

def update_session_admin_status():
    """Update admin status in session state"""
    user_code = st.session_state.get("user_code")
    if user_code:
        st.session_state.is_admin = is_admin_user(user_code)
    else:
        st.session_state.is_admin = False