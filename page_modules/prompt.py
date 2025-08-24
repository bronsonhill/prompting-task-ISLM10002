"""
Prompt page for the Chat Application MVP
Handles prompt creation and management
"""
import streamlit as st
from datetime import datetime
from typing import List, Dict
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
        
        # Document upload section
        st.subheader("📎 Attach Documents (Optional)")
        st.markdown("Upload documents to provide context for your prompt. These will be included when the prompt is used in chat.")
        
        uploaded_files = st.file_uploader(
            "Choose files",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            help="Supported formats: PDF, DOCX, TXT. Multiple files can be uploaded."
        )
        
        # Show uploaded files preview
        if uploaded_files:
            st.write("**Uploaded Documents:**")
            for i, file in enumerate(uploaded_files):
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"📄 {file.name}")
                with col2:
                    st.write(f"Size: {file.size} bytes")
                with col3:
                    st.write(f"Type: {file.type}")
        
        col1, col2 = st.columns([1, 4])
        
        with col1:
            submitted = st.form_submit_button("💾 Create Prompt", use_container_width=True)
        
        if submitted:
            if not prompt_content.strip():
                st.error("Please enter prompt content.")
            else:
                # Process uploaded documents
                documents = []
                if uploaded_files:
                    from utils.database import process_uploaded_document
                    for file in uploaded_files:
                        doc_info = process_uploaded_document(file)
                        if doc_info:
                            documents.append(doc_info)
                        else:
                            st.error(f"Failed to process document: {file.name}")
                            return
                
                create_new_prompt(user_code, prompt_content.strip(), documents)
    
    st.markdown("---")
    
    # Display existing prompts
    show_existing_prompts(user_code)
    
    # Show statistics if there are prompts
    prompts = get_user_prompts(user_code)
    # if prompts:
        # st.markdown("---")
        # show_prompt_stats(user_code)

def create_new_prompt(user_code: str, content: str, documents: List[Dict] = []):
    """Create a new prompt"""
    try:
        prompt_id = save_prompt(user_code, content, documents)
        
        if prompt_id:
            st.success(f"✅ Prompt created successfully! ID: {id_to_display_number(prompt_id)}")
            
            # Get the created prompt to show token counts
            from utils.database import get_prompt_by_id
            created_prompt = get_prompt_by_id(prompt_id, user_code)
            if created_prompt:
                if created_prompt.get('prompt_token_count') is not None:
                    st.info(f"📝 Prompt tokens: {created_prompt['prompt_token_count']}")
                if created_prompt.get('document_token_count') is not None and created_prompt['document_token_count'] > 0:
                    st.info(f"📎 Document tokens: {created_prompt['document_token_count']}")
                if created_prompt.get('total_token_count') is not None:
                    st.info(f"🔢 Total tokens: {created_prompt['total_token_count']}")
            
            if documents:
                st.success(f"📎 Attached {len(documents)} document(s)")
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
                
                # Display token counts
                if prompt.get('prompt_token_count') is not None:
                    st.write(f"**Prompt Tokens:** {prompt['prompt_token_count']}")
                if prompt.get('document_token_count') is not None and prompt['document_token_count'] > 0:
                    st.write(f"**Document Tokens:** {prompt['document_token_count']}")
                if prompt.get('total_token_count') is not None:
                    st.write(f"**Total Tokens:** {prompt['total_token_count']}")
            
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
                
                # Show attached documents if any
                if prompt.get('documents'):
                    st.write("**📎 Attached Documents:**")
                    for doc in prompt['documents']:
                        st.write(f"• {doc['filename']} ({doc['file_type']})")
                        if len(doc.get('content', '')) > 100:
                            with st.expander(f"View {doc['filename']} content"):
                                st.write(doc['content'])
                        else:
                            st.write(f"_{doc.get('content', '')[:100]}..._")
            
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
        # Calculate average token counts
        total_prompt_tokens = sum(p.get('prompt_token_count', 0) for p in prompts)
        total_document_tokens = sum(p.get('document_token_count', 0) for p in prompts)
        avg_prompt_tokens = total_prompt_tokens // len(prompts) if prompts else 0
        avg_document_tokens = total_document_tokens // len(prompts) if prompts else 0
        
        st.metric("Avg. Prompt Tokens", avg_prompt_tokens)
        st.metric("Avg. Document Tokens", avg_document_tokens)
    
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