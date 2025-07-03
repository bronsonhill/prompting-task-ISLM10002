"""
Admin page for the Chat Application MVP
Simple admin interface for viewing system statistics
"""
import streamlit as st
from datetime import datetime, timedelta
from utils.auth import require_authentication, get_current_user_code, is_admin_user, get_admin_codes_list, add_admin_code_auth, remove_admin_code_auth, is_super_admin_user, get_admin_level_user
from utils.database import get_database, id_to_display_number
from utils.logging import log_page_visit

def main():
    st.set_page_config(
        page_title="Admin - Chat Application",
        page_icon="⚙️",
        layout="wide"
    )
    
    # Require authentication
    require_authentication()
    
    user_code = get_current_user_code()
    if not user_code:
        st.error("User not authenticated")
        return
    
    # Check if user is admin
    if not is_admin_user(user_code):
        st.error("🔒 Access denied. Admin privileges required.")
        st.info("If you believe you should have admin access, please contact the system administrator.")
        return
    
    log_page_visit(user_code, "admin")
    
    # Page header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("⚙️ Admin Dashboard")
        # Show admin level
        admin_level = get_admin_level_user(user_code)
        if admin_level == "super_admin":
            st.caption("👑 Super Administrator")
        else:
            st.caption("🔧 Administrator")
    with col2:
        if st.button("← Back to Home"):
            st.switch_page("Home.py")
    
    st.markdown("---")
    
    # Admin interface
    show_admin_interface()

def show_admin_interface():
    """Show admin interface"""
    # Tabs for different admin sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Statistics", "👥 Users", "💬 Conversations", "📝 Prompts", "⚙️ Admin Management"])
    
    with tab1:
        show_system_statistics()
    
    with tab2:
        show_user_management()
    
    with tab3:
        show_conversation_stats()
    
    with tab4:
        show_prompt_stats()
    
    with tab5:
        show_admin_management()

def show_system_statistics():
    """Show system-wide statistics"""
    st.header("📊 System Statistics")
    
    try:
        db = get_database()
        
        # Get collection counts
        users_count = db.users.count_documents({})
        prompts_count = db.prompts.count_documents({})
        conversations_count = db.conversations.count_documents({})
        logs_count = db.logs.count_documents({})
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users", users_count)
        
        with col2:
            st.metric("Total Prompts", prompts_count)
        
        with col3:
            st.metric("Total Conversations", conversations_count)
        
        with col4:
            st.metric("Total Log Entries", logs_count)
        
        # Recent activity
        st.subheader("Recent Activity (Last 24 Hours)")
        
        # Calculate 24 hours ago
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        
        recent_users = db.users.count_documents({"created_at": {"$gte": twenty_four_hours_ago}})
        recent_conversations = db.conversations.count_documents({"created_at": {"$gte": twenty_four_hours_ago}})
        recent_prompts = db.prompts.count_documents({"created_at": {"$gte": twenty_four_hours_ago}})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("New Users", recent_users)
        
        with col2:
            st.metric("New Conversations", recent_conversations)
        
        with col3:
            st.metric("New Prompts", recent_prompts)
        
        # Data consent stats
        st.subheader("Data Consent Statistics")
        
        consent_true = db.users.count_documents({"data_use_consent": True})
        consent_false = db.users.count_documents({"data_use_consent": False})
        consent_null = db.users.count_documents({"data_use_consent": None})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Consent Given", consent_true)
        
        with col2:
            st.metric("Consent Denied", consent_false)
        
        with col3:
            st.metric("Consent Pending", consent_null)
            
    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")

def show_user_management():
    """Show user management interface"""
    st.header("👥 User Management")
    
    try:
        db = get_database()
        
        # Search users
        search_term = st.text_input("Search users (by code):", placeholder="Enter user code")
        
        if search_term:
            users = list(db.users.find({"code": {"$regex": search_term.upper(), "$options": "i"}}).sort("created_at", -1))
        else:
            # Show recent users
            users = list(db.users.find({}).sort("created_at", -1).limit(50))
        
        st.write(f"Showing {len(users)} users")
        
        # Display users in a table
        if users:
            for user in users:
                with st.expander(f"User: {user['code']} - Created: {user['created_at'].strftime('%Y-%m-%d %H:%M')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Code:** {user['code']}")
                        st.write(f"**Created:** {user['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                        st.write(f"**Last Login:** {user.get('last_login', 'Never').strftime('%Y-%m-%d %H:%M:%S') if user.get('last_login') else 'Never'}")
                    
                    with col2:
                        consent = user.get('data_use_consent')
                        consent_text = "✅ Given" if consent is True else "❌ Denied" if consent is False else "❓ Pending"
                        st.write(f"**Data Consent:** {consent_text}")
                        
                        # Get user's activity
                        prompt_count = db.prompts.count_documents({"user_code": user['code']})
                        conv_count = db.conversations.count_documents({"user_code": user['code']})
                        
                        st.write(f"**Prompts:** {prompt_count}")
                        st.write(f"**Conversations:** {conv_count}")
        else:
            st.info("No users found")
            
    except Exception as e:
        st.error(f"Error loading users: {str(e)}")

def show_conversation_stats():
    """Show conversation statistics"""
    st.header("💬 Conversation Analytics")
    
    try:
        db = get_database()
        
        # Top users by conversation count
        pipeline = [
            {"$group": {"_id": "$user_code", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        top_users = list(db.conversations.aggregate(pipeline))
        
        if top_users:
            st.subheader("Top 10 Users by Conversation Count")
            for user in top_users:
                st.write(f"**{user['_id']}:** {user['count']} conversations")
        
        # Message statistics
        st.subheader("Message Statistics")
        
        conversations = list(db.conversations.find({}))
        if conversations:
            total_messages = sum(len(conv.get('messages', [])) for conv in conversations)
            avg_messages = total_messages / len(conversations) if conversations else 0
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Messages", total_messages)
            with col2:
                st.metric("Avg Messages per Conversation", f"{avg_messages:.1f}")
        
        # Recent conversations
        st.subheader("Recent Conversations")
        recent_conversations = list(db.conversations.find({}).sort("updated_at", -1).limit(10))
        
        for conv in recent_conversations:
            with st.expander(f"{id_to_display_number(conv['conversation_id'])} - {conv['user_code']} - {conv['updated_at'].strftime('%Y-%m-%d %H:%M')}"):
                st.write(f"**Prompt ID:** {id_to_display_number(conv['prompt_id'])}")
                st.write(f"**Messages:** {len(conv.get('messages', []))}")
                st.write(f"**Created:** {conv['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                st.write(f"**Last Updated:** {conv['updated_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                
    except Exception as e:
        st.error(f"Error loading conversation stats: {str(e)}")

def show_prompt_stats():
    """Show prompt statistics"""
    st.header("📝 Prompt Analytics")
    
    try:
        db = get_database()
        
        # Prompt usage statistics
        pipeline = [
            {"$group": {"_id": "$prompt_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        prompt_usage = list(db.conversations.aggregate(pipeline))
        
        if prompt_usage:
            st.subheader("Most Used Prompts")
            for prompt_stat in prompt_usage:
                prompt_id = prompt_stat['_id']
                usage_count = prompt_stat['count']
                
                # Get prompt details
                prompt_data = db.prompts.find_one({"prompt_id": prompt_id})
                if prompt_data:
                    with st.expander(f"{id_to_display_number(prompt_id)} - Used {usage_count} times"):
                        st.write(f"**Created by:** {prompt_data['user_code']}")
                        st.write(f"**Created:** {prompt_data['created_at'].strftime('%Y-%m-%d %H:%M')}")
                        st.write(f"**Content:** {prompt_data['content'][:200]}{'...' if len(prompt_data['content']) > 200 else ''}")
        
        # Prompt creation trends
        st.subheader("Recent Prompts")
        recent_prompts = list(db.prompts.find({}).sort("created_at", -1).limit(10))
        
        for prompt in recent_prompts:
            with st.expander(f"{id_to_display_number(prompt['prompt_id'])} - {prompt['user_code']} - {prompt['created_at'].strftime('%Y-%m-%d %H:%M')}"):
                st.write(f"**Content:** {prompt['content']}")
                
                # Check usage
                usage_count = db.conversations.count_documents({"prompt_id": prompt['prompt_id']})
                st.write(f"**Used in conversations:** {usage_count}")
                
    except Exception as e:
        st.error(f"Error loading prompt stats: {str(e)}")

def show_admin_management():
    """Show admin management interface"""
    st.header("⚙️ Admin Management")
    
    user_code = get_current_user_code()
    admin_codes = get_admin_codes_list()
    
    # Show current admin status
    st.subheader("Current Admin Status")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Your Code:** {user_code}")
        admin_level = get_admin_level_user(user_code)
        admin_status = f"✅ {admin_level.replace('_', ' ').title()}" if admin_level else "❌ Not Admin"
        st.write(f"**Admin Status:** {admin_status}")
    
    with col2:
        active_codes = [code["code"] for code in admin_codes if code.get("is_active", True)]
        st.write(f"**Total Admin Codes:** {len(active_codes)}")
        st.write(f"**Admin Codes:** {', '.join(sorted(active_codes))}")
    
    st.markdown("---")
    
    # Admin code management (only for super admins)
    if is_super_admin_user(user_code):
        st.subheader("Admin Code Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Add New Admin Code**")
            with st.form("add_admin_form"):
                new_admin_code = st.text_input(
                    "New Admin Code",
                    max_chars=5,
                    placeholder="Enter 5-character code",
                    help="Enter a 5-character alphanumeric code"
                ).upper().strip()
                
                admin_level = st.selectbox(
                    "Admin Level",
                    options=["admin", "super_admin"],
                    help="Select the admin level for this code"
                )
                
                if st.form_submit_button("Add Admin Code"):
                    if new_admin_code and len(new_admin_code) == 5 and new_admin_code.isalnum():
                        if add_admin_code_auth(new_admin_code, admin_level, user_code):
                            st.success(f"✅ Admin code '{new_admin_code}' added successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to add admin code.")
                    else:
                        st.error("❌ Invalid code format. Must be 5 alphanumeric characters.")
        
        with col2:
            st.write("**Remove Admin Code**")
            with st.form("remove_admin_form"):
                # Get codes that can be removed (not super admins)
                removable_codes = []
                for code_data in admin_codes:
                    if code_data.get("is_active", True) and code_data.get("level") != "super_admin":
                        removable_codes.append(code_data["code"])
                
                if removable_codes:
                    code_to_remove = st.selectbox(
                        "Select Admin Code to Remove",
                        options=removable_codes,
                        help="Select an admin code to remove (Super admins cannot be removed)"
                    )
                    
                    if st.form_submit_button("Remove Admin Code"):
                        if remove_admin_code_auth(code_to_remove, user_code):
                            st.success(f"✅ Admin code '{code_to_remove}' removed successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to remove admin code.")
                else:
                    st.info("No removable admin codes available.")
    else:
        st.info("🔒 Admin code management is restricted to super administrators.")
    
    st.markdown("---")
    
    # System information
    st.subheader("System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Application Version:** 1.0.0")
        st.write("**Database:** MongoDB")
        st.write("**Framework:** Streamlit")
    
    with col2:
        st.write("**Admin Access:** Dynamic")
        st.write("**Authentication:** User Code Based")
        st.write("**Data Collection:** Consent Based")

if __name__ == "__main__":
    main()