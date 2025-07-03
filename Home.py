"""
Main page for the Chat Application MVP
Handles user login and data consent
"""
import streamlit as st
from utils.auth import (
    initialize_session, 
    login_user, 
    logout_user, 
    is_authenticated,
    validate_user_code,
    is_first_time_user,
    handle_first_time_user,
    update_user_consent
)
from utils.logging import log_page_visit, log_user_action

def main():
    st.set_page_config(
        page_title="Chat Application",
        page_icon="💬",
        layout="wide"
    )
    
    # Initialize session
    initialize_session()
    
    # If user is already authenticated, show main navigation
    if is_authenticated():
        show_main_interface()
    else:
        show_login_page()

def show_login_page():
    """Display login form for unauthenticated users"""
    st.title("💬 Chat Application")
    st.markdown("---")
    
    # Handle consent flow for users who need to set consent
    if st.session_state.get("needs_consent", False):
        show_consent_form()
        return
    
    # Login form
    st.header("Welcome")
    st.markdown("Please enter your 5-character access code to continue.")
    
    with st.form("login_form"):
        user_code = st.text_input(
            "Access Code",
            max_chars=5,
            placeholder="Enter your 5-character code",
            help="Enter the unique code provided to you"
        ).upper().strip()
        
        submitted = st.form_submit_button("Login", use_container_width=True)
        
        if submitted:
            if not user_code:
                st.error("Please enter your access code.")
                return
            
            if not validate_user_code(user_code):
                st.error("Invalid code format. Please enter a 5-character alphanumeric code.")
                return
            
            # Try to login
            if login_user(user_code):
                st.success("Login successful!")
                st.rerun()
            elif st.session_state.get("needs_consent", False):
                # User needs consent - will show consent form on rerun
                st.rerun()
            else:
                st.error("Invalid access code. Please check your code and try again.")

def show_consent_form():
    """Show data consent form for users who need to set consent"""
    st.header("Welcome - Data Consent Review Required")
    st.markdown("---")
    
    temp_code = st.session_state.get("temp_code", "")
    
    # Check if this is a new user or existing user
    from utils.database import get_user_data
    user_data = get_user_data(temp_code)
    is_new_user = user_data is None
    
    if is_new_user:
        st.info(f"Welcome! We see this is your first time using the code: **{temp_code}**")
    else:
        st.info(f"Welcome back! We need you to reconsider your data consent preferences for code: **{temp_code}**")
    
    st.markdown("""
    ### Data Collection Notice
    
    This application collects and stores the following data for research purposes:
    - Your chat conversations and messages
    - Prompts you create
    - Usage patterns and timestamps
    - System interactions and logs
    
    **Important:** Data is collected regardless of your consent choice below. 
    Your consent only affects how the data may be used for research purposes.
    """)
    
    with st.form("consent_form"):
        data_consent = st.checkbox(
            "I consent to the use of my data for research purposes",
            help="This consent affects data usage, not collection. Data is logged regardless of this choice."
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("Continue", use_container_width=True):
                success = False
                
                if is_new_user:
                    # Create new user
                    success = handle_first_time_user(temp_code, data_consent)
                else:
                    # Update existing user's consent
                    success = update_user_consent(temp_code, data_consent)
                
                if success:
                    st.session_state.authenticated = True
                    st.session_state.user_code = temp_code
                    st.session_state.needs_consent = False
                    if "temp_code" in st.session_state:
                        del st.session_state.temp_code
                    
                    action_type = "consent_given" if is_new_user else "consent_updated"
                    log_user_action(temp_code, action_type, {"consent": data_consent})
                    
                    if is_new_user:
                        st.success("Account created successfully!")
                    else:
                        st.success("Consent preferences updated successfully!")
                    st.rerun()
                else:
                    if is_new_user:
                        st.error("Error creating account. Please try again.")
                    else:
                        st.error("Error updating consent preferences. Please try again.")
        
        with col2:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.session_state.needs_consent = False
                if "temp_code" in st.session_state:
                    del st.session_state.temp_code
                st.rerun()

def show_main_interface():
    """Show main interface for authenticated users"""
    user_code = st.session_state.user_code
    log_page_visit(user_code, "main")
    
    # Header with user info and logout
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.title("💬 Chat Application")
    
    with col2:
        st.markdown(f"**User:** {user_code}")
    
    with col3:
        if st.button("Logout", use_container_width=True):
            logout_user()
            st.rerun()
    
    st.markdown("---")
    
    # Navigation to main features
    st.header("Welcome! What would you like to do?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💬 Chat")
        st.markdown("Start conversations using your prompts")
        if st.button("Go to Chat", use_container_width=True, key="nav_chat"):
            st.switch_page("pages/1_Chat.py")
    
    with col2:
        st.subheader("📝 Prompts")
        st.markdown("Create and manage your conversation prompts")
        if st.button("Go to Prompts", use_container_width=True, key="nav_prompts"):
            st.switch_page("pages/2_Prompt.py")
    
    # Quick stats
    st.markdown("---")
    show_user_stats()

def show_user_stats():
    """Display user statistics"""
    from utils.database import get_user_prompts, get_user_conversations
    
    user_code = st.session_state.user_code
    
    try:
        prompts = get_user_prompts(user_code)
        conversations = get_user_conversations(user_code)
        
        st.subheader("Your Activity")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Prompts", len(prompts))
        
        with col2:
            st.metric("Total Conversations", len(conversations))
        
        with col3:
            total_messages = sum(len(conv.get("messages", [])) for conv in conversations)
            st.metric("Total Messages", total_messages)
        
        # Recent activity
        if conversations:
            st.subheader("Recent Conversations")
            for conv in conversations[:3]:  # Show last 3 conversations
                with st.expander(f"Conversation {conv['conversation_id']} - {conv['updated_at'].strftime('%Y-%m-%d %H:%M')}"):
                    st.write(f"**Prompt:** {conv['prompt_id']}")
                    st.write(f"**Messages:** {len(conv.get('messages', []))}")
                    if st.button(f"Continue", key=f"continue_{conv['conversation_id']}"):
                        st.session_state.selected_conversation = conv['conversation_id']
                        st.switch_page("pages/1_Chat.py")
                        
    except Exception as e:
        st.error(f"Error loading user statistics: {str(e)}")

if __name__ == "__main__":
    main()