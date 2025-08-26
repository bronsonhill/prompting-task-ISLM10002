"""
Main page for the Chat Application MVP
Handles user login, data consent, and dynamic navigation
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
    update_user_consent,
    is_admin_user,
    get_current_user_admin_status,
    get_current_user_code
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
    
    # Check for admin codes (but don't create hardcoded ones)
    try:
        from utils.database import get_admin_codes
        admin_codes = get_admin_codes()
        if not admin_codes:
            st.warning("⚠️ **No admin codes found in database.**")
            st.info("To create your first admin code, run: `python scripts/manage_admin_codes.py --add YOUR_CODE --level super_admin`")
            st.info("Or use the secure initial setup: `python scripts/manage_admin_codes.py --init-secure`")
    except Exception as e:
        st.error(f"Error checking admin codes: {str(e)}")
    
    # Handle navigation based on authentication status
    if is_authenticated():
        setup_authenticated_navigation()
    else:
        setup_unauthenticated_navigation()

def login_page():
    """Login page function for st.navigation"""
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

def home_page():
    """Main home page for authenticated users"""
    user_code = st.session_state.user_code
    log_page_visit(user_code, "main")
    
    # Header with user info and logout
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.title("💬 Chat Application")
    
    with col2:
        # Check if user is admin and show status
        is_admin = get_current_user_admin_status()
        admin_badge = "👑 **Admin**" if is_admin else ""
        st.markdown(f"**User:** {user_code} {admin_badge}")
    
    with col3:
        if st.button("Logout", use_container_width=True):
            logout_user()
            st.rerun()
    
    st.markdown("---")
    
    # Welcome message and navigation instructions
    st.header("Welcome! Navigate using the sidebar.")
    
    # Quick stats
    st.markdown("---")
    show_user_stats()

def logout_page():
    """Logout page function for st.navigation"""
    logout_user()
    st.rerun()

def setup_unauthenticated_navigation():
    """Setup navigation for unauthenticated users"""
    # Only show login page
    pg = st.navigation([
        st.Page(login_page, title="Login", icon="🔐")
    ])
    pg.run()

def setup_authenticated_navigation():
    """Setup navigation for authenticated users with role-based access"""
    user_code = get_current_user_code()
    is_admin = get_current_user_admin_status()
    
    # Define all pages
    home = st.Page(home_page, title="Home", icon="🏠", default=True)
    logout = st.Page(logout_page, title="Logout", icon="🚪")
    
    # Core pages available to all users
    prompt = st.Page("page_modules/prompt.py", title="Prompts", icon="📝")
    chat = st.Page("page_modules/chat.py", title="Chat", icon="💬")
    
    # Admin-only page
    admin = st.Page("page_modules/admin.py", title="Admin", icon="⚙️")
    
    # Build navigation structure based on user role
    page_dict = {
        "Account": [home, logout],
        "Main": [prompt, chat]
    }
    
    # Add admin section only for admin users
    if is_admin:
        page_dict["Administration"] = [admin]
    
    # Create navigation
    pg = st.navigation(page_dict)
    pg.run()

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
        st.info(f"Welcome back! We need you to consider your data consent preferences for code: **{temp_code}**")
    
    st.markdown("""
        Welcome to the Socratic Chatbot Application! This is the tool you will use to design your own Socratic Chatbots to learn about topics relevant to Islam in the Modern World.  
        How students use the tool and whether it is helpful will be studied after the subject is concluded. Please indicate your consent preferences below:
    """)
    
    with st.form("consent_form"):
        data_consent = st.checkbox(
            "I consent to the use of my anonymised data for the purposes of research.",
            help="Please note: Data is collected regardless of your consent indication. Your consent only affects how the data may be used for research purposes."
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
                    
                    # Update admin status in session
                    from utils.auth import update_session_admin_status
                    update_session_admin_status()
                    
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

def show_user_stats():
    """Display user statistics"""
    from utils.database import get_user_prompts, get_user_conversations, id_to_display_number
    
    user_code = st.session_state.user_code
    
    try:
        prompts = get_user_prompts(user_code)
        conversations = get_user_conversations(user_code)
        
        st.subheader("Your Activity")
        
        # Check if user is admin
        is_admin = get_current_user_admin_status()
        
        if is_admin:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Prompts", len(prompts))
            
            with col2:
                st.metric("Total Conversations", len(conversations))
            
            with col3:
                total_messages = sum(len(conv.get("messages", [])) for conv in conversations)
                st.metric("Total Messages", total_messages)
            
            with col4:
                st.metric("Admin Status", "👑 Active")
        else:
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
            # Remove potential duplicates based on conversation_id
            seen_ids = set()
            unique_conversations = []
            for conv in conversations[:3]:  # Show last 3 conversations
                if conv['conversation_id'] not in seen_ids:
                    seen_ids.add(conv['conversation_id'])
                    unique_conversations.append(conv)
            
            for i, conv in enumerate(unique_conversations):
                with st.expander(f"Conversation {id_to_display_number(conv['conversation_id'])} - {conv['updated_at'].strftime('%Y-%m-%d %H:%M')}"):
                    st.write(f"**Prompt:** {id_to_display_number(conv['prompt_id'])}")
                    st.write(f"**Messages:** {len(conv.get('messages', []))}")
                    if st.button(f"Continue", key=f"continue_{conv['conversation_id']}_{i}"):
                        st.session_state.selected_conversation = conv['conversation_id']
                        st.switch_page("page_modules/chat.py")
                        
    except Exception as e:
        st.error(f"Error loading user statistics: {str(e)}")

if __name__ == "__main__":
    main()