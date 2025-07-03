"""
Admin page for the Chat Application MVP
Simple admin interface for viewing system statistics
"""
import streamlit as st
from datetime import datetime, timedelta
from utils.auth import require_authentication, get_current_user_code
from utils.database import get_database
from utils.logging import log_page_visit

# Define admin codes (you can expand this to use a proper admin system)
ADMIN_CODES = {"ADMIN", "SUPER", "TEST1"}  # Add your admin codes here

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
    if user_code not in ADMIN_CODES:
        st.error("🔒 Access denied. Admin privileges required.")
        return
    
    log_page_visit(user_code, "admin")
    
    # Page header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("⚙️ Admin Dashboard")
    with col2:
        if st.button("← Back to Home"):
            st.switch_page("Home.py")
    
    st.markdown("---")
    
    # Admin interface
    show_admin_interface()

def show_admin_interface():
    """Show admin interface"""
    # Tabs for different admin sections
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Statistics", "👥 Users", "💬 Conversations", "📝 Prompts"])
    
    with tab1:
        show_system_statistics()
    
    with tab2:
        show_user_management()
    
    with tab3:
        show_conversation_stats()
    
    with tab4:
        show_prompt_stats()

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
            with st.expander(f"{conv['conversation_id']} - {conv['user_code']} - {conv['updated_at'].strftime('%Y-%m-%d %H:%M')}"):
                st.write(f"**Prompt ID:** {conv['prompt_id']}")
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
                    with st.expander(f"{prompt_id} - Used {usage_count} times"):
                        st.write(f"**Created by:** {prompt_data['user_code']}")
                        st.write(f"**Created:** {prompt_data['created_at'].strftime('%Y-%m-%d %H:%M')}")
                        st.write(f"**Content:** {prompt_data['content'][:200]}{'...' if len(prompt_data['content']) > 200 else ''}")
        
        # Prompt creation trends
        st.subheader("Recent Prompts")
        recent_prompts = list(db.prompts.find({}).sort("created_at", -1).limit(10))
        
        for prompt in recent_prompts:
            with st.expander(f"{prompt['prompt_id']} - {prompt['user_code']} - {prompt['created_at'].strftime('%Y-%m-%d %H:%M')}"):
                st.write(f"**Content:** {prompt['content']}")
                
                # Check usage
                usage_count = db.conversations.count_documents({"prompt_id": prompt['prompt_id']})
                st.write(f"**Used in conversations:** {usage_count}")
                
    except Exception as e:
        st.error(f"Error loading prompt stats: {str(e)}")

if __name__ == "__main__":
    main()