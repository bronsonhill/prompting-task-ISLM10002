"""
Prompt page for the Chat Application MVP
Handles prompt creation and management
"""
import streamlit as st
from datetime import datetime
from utils.auth import require_authentication, get_current_user_code
from utils.database import save_prompt, get_user_prompts, id_to_display_number
from utils.logging import log_page_visit, log_prompt_creation

def main():
    st.set_page_config(
        page_title="Prompts - Chat Application",
        page_icon="📝",
        layout="wide"
    )
    
    # Require authentication
    require_authentication()
    
    user_code = get_current_user_code()
    if not user_code:
        st.error("User not authenticated")
        return
    
    log_page_visit(user_code, "prompts")
    
    # Page header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("📝 Prompts")
    
    st.markdown("---")
    
    # Main content
    show_prompt_interface(user_code)

def show_prompt_interface(user_code: str):
    """Show the main prompt interface"""
    # Create new prompt section
    st.header("Create New Prompt")
    
    with st.form("create_prompt_form"):
        prompt_content = st.text_area(
            "Prompt Content",
            height=200,
            placeholder="Enter your conversation prompt here...\n\nExample: You are a helpful assistant that explains complex topics in simple terms. Always provide examples when possible.",
            help="This prompt will be used as the system message to initialize conversations with AI."
        )
        
        col1, col2 = st.columns([1, 4])
        
        with col1:
            submitted = st.form_submit_button("💾 Create Prompt", use_container_width=True)
        
        if submitted:
            if not prompt_content.strip():
                st.error("Please enter prompt content.")
            else:
                create_new_prompt(user_code, prompt_content.strip())
    
    st.markdown("---")
    
    # Display existing prompts
    show_existing_prompts(user_code)
    
    # Show statistics if there are prompts
    prompts = get_user_prompts(user_code)
    # if prompts:
        # st.markdown("---")
        # show_prompt_stats(user_code)

def create_new_prompt(user_code: str, content: str):
    """Create a new prompt"""
    try:
        prompt_id = save_prompt(user_code, content)
        
        if prompt_id:
            st.success(f"✅ Prompt created successfully! ID: {id_to_display_number(prompt_id)}")
            log_prompt_creation(user_code, prompt_id, content)
            
            # Clear the form by rerunning
            st.rerun()
        else:
            st.error("❌ Error creating prompt. Please try again.")
            
    except Exception as e:
        st.error(f"❌ Error creating prompt: {str(e)}")

def show_existing_prompts(user_code: str):
    """Display existing prompts"""
    st.header("Your Prompts")
    
    prompts = get_user_prompts(user_code)
    
    if not prompts:
        st.info("📝 No prompts created yet. Create your first prompt above to start chatting!")
        return
    
    st.write(f"**Total Prompts:** {len(prompts)}")
    
    # Display prompts in cards
    for i, prompt in enumerate(prompts):
        with st.container():
            # Create a card-like appearance
            st.markdown(f"""
            <div style="
                border: 1px solid #ddd; 
                border-radius: 10px; 
                padding: 15px; 
                margin: 10px 0; 
                background-color: #f9f9f9;
            ">
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([2, 3, 1])
            
            with col1:
                st.subheader(f"🏷️ {id_to_display_number(prompt['prompt_id'])}")
                st.write(f"**Created:** {prompt['created_at'].strftime('%Y-%m-%d %H:%M')}")
                
                if prompt.get('updated_at') and prompt['updated_at'] != prompt['created_at']:
                    st.write(f"**Updated:** {prompt['updated_at'].strftime('%Y-%m-%d %H:%M')}")
            
            with col2:
                st.write("**Content:**")
                
                # Show content with expand/collapse
                content = prompt['content']
                if len(content) > 200:
                    with st.expander(f"View full content ({len(content)} characters)"):
                        st.write(content)
                    st.write(f"{content[:200]}...")
                else:
                    st.write(content)
            
            with col3:
                # Action buttons
                if st.button("💬 Use for Chat", key=f"use_{prompt['prompt_id']}", use_container_width=True):
                    # Navigate to chat page with this prompt preselected
                    st.session_state.selected_prompt = prompt['prompt_id']
                    st.switch_page("page_modules/chat.py")
            
            st.markdown("---")


def show_prompt_stats(user_code: str):
    """Show prompt statistics"""
    from utils.database import get_user_conversations
    
    prompts = get_user_prompts(user_code)
    conversations = get_user_conversations(user_code)
    
    if not prompts:
        return
    
    st.header("📊 Prompt Usage Statistics")
    
    # Calculate usage stats
    prompt_usage = {}
    for conv in conversations:
        prompt_id = conv.get('prompt_id')
        if prompt_id:
            prompt_usage[prompt_id] = prompt_usage.get(prompt_id, 0) + 1
    
    # Display in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Prompts", len(prompts))
    
    with col2:
        used_prompts = len([p for p in prompts if p['prompt_id'] in prompt_usage])
        st.metric("Used in Conversations", used_prompts)
    
    with col3:
        avg_length = sum(len(p['content']) for p in prompts) // len(prompts) if prompts else 0
        st.metric("Avg. Character Length", avg_length)
    
    # Most used prompts
    if prompt_usage:
        st.subheader("Most Used Prompts")
        sorted_usage = sorted(prompt_usage.items(), key=lambda x: x[1], reverse=True)
        
        for prompt_id, usage_count in sorted_usage[:5]:  # Top 5
            prompt_data = next((p for p in prompts if p['prompt_id'] == prompt_id), None)
            if prompt_data:
                st.write(f"**{id_to_display_number(prompt_id)}** - Used {usage_count} time(s)")
                st.write(f"_{prompt_data['content'][:100]}{'...' if len(prompt_data['content']) > 100 else ''}_")
                st.markdown("---")



if __name__ == "__main__":
    main()