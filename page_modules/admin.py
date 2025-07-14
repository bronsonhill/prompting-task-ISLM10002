"""
Admin page for the Chat Application MVP
Simple admin interface for viewing system statistics
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.auth import require_authentication, get_current_user_code, is_admin_user, get_admin_codes_list, add_admin_code_auth, remove_admin_code_auth, is_super_admin_user, get_admin_level_user
from utils.database import get_database, id_to_display_number
from utils.logging import log_page_visit

def create_csv_download(data, filename, display_name=None):
    """Create a CSV download button"""
    if data:
        df = pd.DataFrame(data)
        csv = df.to_csv(index=False)
        button_label = display_name if display_name else f"📥 Download {filename}"
        # Adjust timezone by subtracting 2 hours
        adjusted_time = datetime.now() + timedelta(hours=11)
        st.download_button(
            label=button_label,
            data=csv,
            file_name=f"{filename}_{adjusted_time.strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

def generate_prompts_csv_data():
    """Generate prompts CSV data - shared function to eliminate duplication"""
    try:
        db = get_database()
        if db is None:
            return []
        
        # Get all prompts for CSV export
        all_prompts = list(db.prompts.find({}).sort("created_at", -1))
        prompts_csv_data = []
        
        for prompt in all_prompts:
            # Adjust timezone for database timestamps
            created_at_adjusted = prompt['created_at'] + timedelta(hours=11)
            updated_at_adjusted = prompt['updated_at'] + timedelta(hours=11)
            
            # Get total tokens for this prompt across all conversations
            prompt_token_pipeline = [
                {"$match": {"prompt_id": prompt['prompt_id']}},
                {"$group": {
                    "_id": None,
                    "total_input_tokens": {"$sum": "$token_stats.total_input_tokens"},
                    "total_output_tokens": {"$sum": "$token_stats.total_output_tokens"}
                }}
            ]
            prompt_token_result = list(db.conversations.aggregate(prompt_token_pipeline))
            prompt_total_input_tokens = prompt_token_result[0]["total_input_tokens"] if prompt_token_result else 0
            prompt_total_output_tokens = prompt_token_result[0]["total_output_tokens"] if prompt_token_result else 0
            
            prompts_csv_data.append({
                "Prompt ID": prompt.get('prompt_id', 'Unknown'),
                "User Code": prompt['user_code'],
                "Content": prompt['content'],
                "Token Count": prompt.get('token_count', 0),
                "Total Input Tokens": prompt_total_input_tokens,
                "Total Output Tokens": prompt_total_output_tokens,
                "Total Tokens": prompt_total_input_tokens + prompt_total_output_tokens,
                "Created At": created_at_adjusted.strftime('%Y-%m-%d %H:%M:%S'),
                "Updated At": updated_at_adjusted.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return prompts_csv_data
        
    except Exception as e:
        st.error(f"Error generating prompts CSV data: {str(e)}")
        return []

def show_prompt_token_update_section(key_suffix=""):
    """Show prompt token update section - shared function to eliminate duplication"""
    st.markdown("---")
    st.subheader("🔧 Prompt Token Count Update")
    st.write("If you have existing prompts without token counts, you can update them here.")
    
    button_key = f"update_prompts_{key_suffix}" if key_suffix else "update_prompts_shared"
    
    if st.button("🔄 Update Existing Prompts with Token Counts", key=button_key):
        from utils.database import update_prompt_token_counts
        updated_count = update_prompt_token_counts()
        if updated_count > 0:
            st.success(f"✅ Updated {updated_count} prompts with token counts!")
            st.rerun()
        else:
            st.info("ℹ️ All prompts already have token counts.")

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
    """Show admin interface based on user level"""
    user_code = get_current_user_code()
    
    # Create tabs for different admin functions
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Statistics", "👥 Users", "📝 Prompts", "📋 Logs", "⚙️ Admin Management"])
    
    with tab1:
        show_system_statistics()
    
    with tab2:
        show_user_management()
    
    with tab3:
        show_prompt_statistics()
    
    with tab4:
        show_logs_analytics()
    
    with tab5:
        show_admin_management()

def show_system_statistics():
    """Show system-wide statistics"""
    st.header("📊 System Statistics")
    
    try:
        db = get_database()
        if db is None:
            st.error("Database connection failed")
            return
        
        # Get basic counts
        total_users = db.users.count_documents({})
        total_prompts = db.prompts.count_documents({})
        total_conversations = db.conversations.count_documents({})
        
        # Calculate total messages
        pipeline = [
            {"$project": {"message_count": {"$size": "$messages"}}},
            {"$group": {"_id": None, "total": {"$sum": "$message_count"}}}
        ]
        result = list(db.conversations.aggregate(pipeline))
        total_messages = result[0]["total"] if result else 0
        
        # Calculate total tokens
        token_pipeline = [
            {"$group": {
                "_id": None,
                "total_input_tokens": {"$sum": "$token_stats.total_input_tokens"},
                "total_output_tokens": {"$sum": "$token_stats.total_output_tokens"}
            }}
        ]
        token_result = list(db.conversations.aggregate(token_pipeline))
        total_input_tokens = token_result[0]["total_input_tokens"] if token_result else 0
        total_output_tokens = token_result[0]["total_output_tokens"] if token_result else 0
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users", total_users)
        
        with col2:
            st.metric("Total Prompts", total_prompts)
        
        with col3:
            st.metric("Total Conversations", total_conversations)
        
        with col4:
            st.metric("Total Messages", total_messages)
        
        # Token metrics
        st.markdown("---")
        st.subheader("Token Usage Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Input Tokens", f"{total_input_tokens:,}")
        
        with col2:
            st.metric("Total Output Tokens", f"{total_output_tokens:,}")
        
        with col3:
            total_tokens = total_input_tokens + total_output_tokens
            st.metric("Total Tokens", f"{total_tokens:,}")
        
        st.markdown("---")
        
        # Recent activity
        st.subheader("Recent Activity")
        
        # Get recent users
        recent_users = list(db.users.find({}).sort("created_at", -1).limit(5))
        
        if recent_users:
            st.write("**Recent Users:**")
            for user in recent_users:
                st.write(f"- {user['code']} (Created: {user['created_at'].strftime('%Y-%m-%d %H:%M')})")
        
        # Get recent conversations
        recent_conversations = list(db.conversations.find({}).sort("created_at", -1).limit(5))
        
        if recent_conversations:
            st.write("**Recent Conversations:**")
            for conv in recent_conversations:
                st.write(f"- Conversation {id_to_display_number(str(conv['_id']))} by {conv['user_code']} (Created: {conv['created_at'].strftime('%Y-%m-%d %H:%M')})")
        
        # Data consent statistics
        st.subheader("Data Consent Statistics")
        
        consent_stats = db.users.aggregate([
            {"$group": {
                "_id": "$data_use_consent",
                "count": {"$sum": 1}
            }}
        ])
        
        consent_data = {stat["_id"]: stat["count"] for stat in consent_stats}
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Consent Given", consent_data.get(True, 0))
        
        with col2:
            st.metric("Consent Denied", consent_data.get(False, 0))
        
        with col3:
            st.metric("Consent Pending", consent_data.get(None, 0))
        
        # CSV Download for System Statistics
        st.markdown("---")
        st.subheader("📊 Data Export")
        
        # Prepare data for CSV export
        stats_data = []
        
        # Adjust timezone by subtracting 2 hours
        adjusted_time = datetime.now() + timedelta(hours=11)
        current_timestamp = adjusted_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Add basic counts
        stats_data.append({
            "Metric": "Total Users",
            "Count": total_users,
            "Timestamp": current_timestamp
        })
        stats_data.append({
            "Metric": "Total Prompts", 
            "Count": total_prompts,
            "Timestamp": current_timestamp
        })
        stats_data.append({
            "Metric": "Total Conversations",
            "Count": total_conversations,
            "Timestamp": current_timestamp
        })
        stats_data.append({
            "Metric": "Total Messages",
            "Count": total_messages,
            "Timestamp": current_timestamp
        })
        
        # Add consent data
        stats_data.append({
            "Metric": "Consent Given",
            "Count": consent_data.get(True, 0),
            "Timestamp": current_timestamp
        })
        stats_data.append({
            "Metric": "Consent Denied", 
            "Count": consent_data.get(False, 0),
            "Timestamp": current_timestamp
        })
        stats_data.append({
            "Metric": "Consent Pending",
            "Count": consent_data.get(None, 0),
            "Timestamp": current_timestamp
        })
        
        create_csv_download(stats_data, "system_statistics", "📊 Download System Statistics")
        
        # Get conversations data for CSV export
        all_conversations = list(db.conversations.find({}).sort("created_at", -1))
        conversations_csv_data = []
        
        for conv in all_conversations:
            # Count messages in this conversation
            message_count = len(conv.get('messages', []))
            
            # Format the full conversation as a dialogue
            full_conversation = ""
            if conv.get('messages'):
                for i, message in enumerate(conv['messages']):
                    role = message.get('role', 'unknown')
                    content = message.get('content', '')
                    
                    # Format role names for better readability
                    if role == 'user':
                        role_display = 'User'
                    elif role == 'assistant':
                        role_display = 'Tutor'
                    else:
                        role_display = role.title()
                    
                    full_conversation += f"{role_display}: {content}\n\n"
            else:
                full_conversation = "No messages in this conversation"
            
            # Adjust timezone for database timestamps
            created_at_adjusted = conv['created_at'] + timedelta(hours=11)
            updated_at_adjusted = conv['updated_at'] + timedelta(hours=11)
            
            # Get token statistics
            token_stats = conv.get('token_stats', {})
            total_input_tokens = token_stats.get('total_input_tokens', 0)
            total_output_tokens = token_stats.get('total_output_tokens', 0)
            
            conversations_csv_data.append({
                "Conversation ID": conv.get('conversation_id', 'Unknown'),
                "User Code": conv['user_code'],
                "Prompt ID": conv.get('prompt_id', 'Unknown'),
                "Created At": created_at_adjusted.strftime('%Y-%m-%d %H:%M:%S'),
                "Updated At": updated_at_adjusted.strftime('%Y-%m-%d %H:%M:%S'),
                "Message Count": message_count,
                "Total Input Tokens": total_input_tokens,
                "Total Output Tokens": total_output_tokens,
                "Total Tokens": total_input_tokens + total_output_tokens,
                "Full Conversation": full_conversation.strip()
            })
        
        create_csv_download(conversations_csv_data, "conversations_data", "💬 Download All Conversations")
        
        # Use shared function for prompts CSV export
        prompts_csv_data = generate_prompts_csv_data()
        create_csv_download(prompts_csv_data, "prompts_data", "📝 Download All Prompts")
        
        # Use shared function for prompt token update section
        show_prompt_token_update_section("stats")
        
        # Get logs data for CSV export
        all_logs = list(db.logs.find({}).sort("timestamp", -1))
        logs_csv_data = []
        
        for log in all_logs:
            # Adjust timezone for database timestamps
            timestamp_adjusted = log['timestamp'] + timedelta(hours=11)
            
            # Extract data from log
            data = log.get('data', {})
            
            logs_csv_data.append({
                "Log ID": str(log['_id']),
                "User Code": log['user_code'],
                "Action": log['action'],
                "Timestamp": timestamp_adjusted.strftime('%Y-%m-%d %H:%M:%S'),
                "Prompt ID": data.get('prompt_id', ''),
                "Role": data.get('role', ''),
                "Content": data.get('content', ''),
                "Token Count": data.get('token_count', 0),
                "Message Timestamp": data.get('message_timestamp', ''),
                "Page Name": data.get('page_name', ''),
                "Conversation ID": data.get('conversation_id', ''),
                "Error Type": data.get('error_type', ''),
                "Error Message": data.get('error_message', ''),
                "Content Length": data.get('content_length', 0),
                "Full Data": str(data)
            })
        
        create_csv_download(logs_csv_data, "logs_data", "📋 Download All Logs")
        
    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")

def show_logs_analytics():
    """Show logs analytics and management"""
    st.header("📋 Logs Analytics")
    
    try:
        db = get_database()
        if db is None:
            st.error("Database connection failed")
            return
        
        # Get basic log statistics
        total_logs = db.logs.count_documents({})
        
        # Get logs by action type
        action_pipeline = [
            {"$group": {
                "_id": "$action",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        action_stats = list(db.logs.aggregate(action_pipeline))
        
        # Get recent logs
        recent_logs = list(db.logs.find({}).sort("timestamp", -1).limit(20))
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Logs", total_logs)
        
        with col2:
            chat_logs = db.logs.count_documents({"action": "chat_message"})
            st.metric("Chat Messages", chat_logs)
        
        with col3:
            error_logs = db.logs.count_documents({"action": "error"})
            st.metric("Errors", error_logs)
        
        with col4:
            login_logs = db.logs.count_documents({"action": "login"})
            st.metric("Logins", login_logs)
        
        # Action type breakdown
        st.markdown("---")
        st.subheader("Logs by Action Type")
        
        if action_stats:
            action_data = []
            for stat in action_stats:
                action_data.append({
                    "Action": stat["_id"],
                    "Count": stat["count"],
                    "Percentage": f"{(stat['count'] / total_logs * 100):.1f}%"
                })
            
            # Display as a table
            st.table(action_data)
        
        # Recent logs
        st.markdown("---")
        st.subheader("Recent Logs")
        
        if recent_logs:
            for log in recent_logs:
                with st.expander(f"{log['action']} - {log['user_code']} - {log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Action:** {log['action']}")
                        st.write(f"**User:** {log['user_code']}")
                        st.write(f"**Timestamp:** {log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    with col2:
                        data = log.get('data', {})
                        if data:
                            st.write("**Data:**")
                            for key, value in data.items():
                                if key == 'content' and len(str(value)) > 100:
                                    st.write(f"- {key}: {str(value)[:100]}...")
                                else:
                                    st.write(f"- {key}: {value}")
        
        # Logs export section
        st.markdown("---")
        st.subheader("📊 Logs Export")
        
        # Get all logs for CSV export
        all_logs = list(db.logs.find({}).sort("timestamp", -1))
        logs_csv_data = []
        
        for log in all_logs:
            # Adjust timezone for database timestamps
            timestamp_adjusted = log['timestamp'] + timedelta(hours=11)
            
            # Extract data from log
            data = log.get('data', {})
            
            logs_csv_data.append({
                "Log ID": str(log['_id']),
                "User Code": log['user_code'],
                "Action": log['action'],
                "Timestamp": timestamp_adjusted.strftime('%Y-%m-%d %H:%M:%S'),
                "Prompt ID": data.get('prompt_id', ''),
                "Role": data.get('role', ''),
                "Content": data.get('content', ''),
                "Token Count": data.get('token_count', 0),
                "Message Timestamp": data.get('message_timestamp', ''),
                "Page Name": data.get('page_name', ''),
                "Conversation ID": data.get('conversation_id', ''),
                "Error Type": data.get('error_type', ''),
                "Error Message": data.get('error_message', ''),
                "Content Length": data.get('content_length', 0),
                "Full Data": str(data)
            })
        
        create_csv_download(logs_csv_data, "logs_data", "📋 Download All Logs")
        
        # Token usage from logs
        st.markdown("---")
        st.subheader("Token Usage from Logs")
        
        # Get total tokens from chat message logs
        token_pipeline = [
            {"$match": {"action": "chat_message"}},
            {"$group": {
                "_id": None,
                "total_tokens": {"$sum": "$data.token_count"},
                "total_messages": {"$sum": 1}
            }}
        ]
        token_result = list(db.logs.aggregate(token_pipeline))
        
        if token_result:
            total_log_tokens = token_result[0]["total_tokens"]
            total_log_messages = token_result[0]["total_messages"]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Tokens (from logs)", f"{total_log_tokens:,}")
            
            with col2:
                avg_tokens = total_log_tokens / total_log_messages if total_log_messages > 0 else 0
                st.metric("Average Tokens per Message", f"{avg_tokens:.1f}")
        
    except Exception as e:
        st.error(f"Error loading logs analytics: {str(e)}")

def show_user_management():
    """Show user management interface"""
    st.header("👥 User Management")
    
    try:
        db = get_database()
        if db is None:
            st.error("Database connection failed")
            return
        
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
                        
                        # Get user's token usage
                        user_token_pipeline = [
                            {"$match": {"user_code": user['code']}},
                            {"$group": {
                                "_id": None,
                                "total_input_tokens": {"$sum": "$token_stats.total_input_tokens"},
                                "total_output_tokens": {"$sum": "$token_stats.total_output_tokens"}
                            }}
                        ]
                        user_token_result = list(db.conversations.aggregate(user_token_pipeline))
                        user_input_tokens = user_token_result[0]["total_input_tokens"] if user_token_result else 0
                        user_output_tokens = user_token_result[0]["total_output_tokens"] if user_token_result else 0
                        
                        st.write(f"**Prompts:** {prompt_count}")
                        st.write(f"**Conversations:** {conv_count}")
                        st.write(f"**Input Tokens:** {user_input_tokens:,}")
                        st.write(f"**Output Tokens:** {user_output_tokens:,}")
        else:
            st.info("No users found")
        
        # CSV Download for Users
        st.markdown("---")
        st.subheader("📊 User Data Export")
        
        # Prepare user data for CSV export
        users_csv_data = []
        for user in users:
            # Adjust timezone for database timestamps
            created_at_adjusted = user['created_at'] + timedelta(hours=11)
            last_login_adjusted = user.get('last_login') + timedelta(hours=11) if user.get('last_login') else None
            
            # Get user's token usage
            user_token_pipeline = [
                {"$match": {"user_code": user['code']}},
                {"$group": {
                    "_id": None,
                    "total_input_tokens": {"$sum": "$token_stats.total_input_tokens"},
                    "total_output_tokens": {"$sum": "$token_stats.total_output_tokens"}
                }}
            ]
            user_token_result = list(db.conversations.aggregate(user_token_pipeline))
            user_input_tokens = user_token_result[0]["total_input_tokens"] if user_token_result else 0
            user_output_tokens = user_token_result[0]["total_output_tokens"] if user_token_result else 0
            
            users_csv_data.append({
                "User Code": user['code'],
                "Created At": created_at_adjusted.strftime('%Y-%m-%d %H:%M:%S'),
                "Last Login": last_login_adjusted.strftime('%Y-%m-%d %H:%M:%S') if last_login_adjusted else 'Never',
                "Data Consent": "Given" if user.get('data_use_consent') is True else "Denied" if user.get('data_use_consent') is False else "Pending",
                "Prompts Count": db.prompts.count_documents({"user_code": user['code']}),
                "Conversations Count": db.conversations.count_documents({"user_code": user['code']}),
                "Total Input Tokens": user_input_tokens,
                "Total Output Tokens": user_output_tokens,
                "Total Tokens": user_input_tokens + user_output_tokens
            })
        
        create_csv_download(users_csv_data, "users_data", "👥 Download Users Data")
            
    except Exception as e:
        st.error(f"Error loading user data: {str(e)}")

def show_prompt_statistics():
    """Show prompt statistics and management"""
    st.header("📝 Prompt Statistics")
    
    try:
        db = get_database()
        if db is None:
            st.error("Database connection failed")
            return
        
        # Get prompt statistics
        total_prompts = db.prompts.count_documents({})
        public_prompts = db.prompts.count_documents({"is_public": True})
        private_prompts = total_prompts - public_prompts
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Prompts", total_prompts)
        
        with col2:
            st.metric("Public Prompts", public_prompts)
        
        with col3:
            st.metric("Private Prompts", private_prompts)
        
        # Token statistics for prompts
        st.markdown("---")
        st.subheader("Token Statistics")
        
        # Calculate total tokens across all prompts
        token_pipeline = [
            {"$group": {
                "_id": None,
                "total_tokens": {"$sum": "$token_count"},
                "avg_tokens": {"$avg": "$token_count"},
                "max_tokens": {"$max": "$token_count"},
                "min_tokens": {"$min": "$token_count"}
            }}
        ]
        token_stats = list(db.prompts.aggregate(token_pipeline))
        
        if token_stats:
            stats = token_stats[0]
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Prompt Tokens", f"{stats.get('total_tokens', 0):,}")
            
            with col2:
                st.metric("Average Tokens per Prompt", f"{stats.get('avg_tokens', 0):.1f}")
            
            with col3:
                st.metric("Max Tokens in Prompt", f"{stats.get('max_tokens', 0):,}")
            
            with col4:
                st.metric("Min Tokens in Prompt", f"{stats.get('min_tokens', 0):,}")
        else:
            st.info("No token statistics available. Update prompts with token counts first.")
        
        # Category breakdown
        st.subheader("Prompts by Category")
        
        category_stats = db.prompts.aggregate([
            {"$group": {
                "_id": "$category",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ])
        
        category_data = list(category_stats)
        
        if category_data:
            for cat in category_data:
                st.write(f"**{cat['_id'] or 'Uncategorized'}:** {cat['count']} prompts")
        
        # Recent prompts
        st.subheader("Recent Prompts")
        
        recent_prompts = list(db.prompts.find({}).sort("created_at", -1).limit(10))
        
        if recent_prompts:
            for prompt in recent_prompts:
                with st.expander(f"Prompt {prompt.get('prompt_id', 'Unknown')} - {prompt.get('content', 'No content')[:50]}..."):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**User:** {prompt['user_code']}")
                        st.write(f"**Created:** {prompt['created_at'].strftime('%Y-%m-%d %H:%M')}")
                        st.write(f"**Category:** {prompt.get('category', 'General')}")
                    
                    with col2:
                        st.write(f"**Public:** {'Yes' if prompt.get('is_public', False) else 'No'}")
                        st.write(f"**Updated:** {prompt['updated_at'].strftime('%Y-%m-%d %H:%M')}")
                        st.write(f"**Token Count:** {prompt.get('token_count', 'Not calculated')}")
                    
                    st.write(f"**Content:** {prompt['content'][:200]}..." if len(prompt['content']) > 200 else f"**Content:** {prompt['content']}")
        else:
            st.info("No prompts found")
        
        # CSV Download for Prompts
        st.markdown("---")
        st.subheader("📊 Prompt Data Export")
        
        # Use shared function for prompts CSV export
        prompts_csv_data = generate_prompts_csv_data()
        create_csv_download(prompts_csv_data, "prompts_data", "📝 Download All Prompts")
        
        # Use shared function for prompt token update section
        show_prompt_token_update_section("prompts")
            
    except Exception as e:
        st.error(f"Error loading prompt stats: {str(e)}")

def show_admin_management():
    """Show admin management interface"""
    st.header("⚙️ Admin Management")
    
    user_code = get_current_user_code()
    if not user_code:
        st.error("User not authenticated")
        return
        
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
                        if code_to_remove and remove_admin_code_auth(code_to_remove, user_code):
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