"""
Chat page for the Chat Application MVP
Handles conversation management and OpenAI chat interface
"""
import streamlit as st
from openai import OpenAI
from datetime import datetime
from utils.auth import require_authentication, get_current_user_code
from utils.database import (
    get_user_prompts, 
    get_prompt_by_id, 
    get_user_conversations,
    get_conversation_by_id,
    save_conversation,
    update_conversation
)
from utils.logging import (
    log_page_visit, 
    log_chat_message, 
    log_conversation_start,
    log_conversation_continue,
    log_prompt_selection,
    log_error
)

def main():
    st.set_page_config(
        page_title="Chat - Chat Application",
        page_icon="💬",
        layout="wide"
    )
    
    # Require authentication
    require_authentication()
    
    user_code = get_current_user_code()
    if not user_code:
        st.error("User not authenticated")
        return
    
    log_page_visit(user_code, "chat")
    
    # Initialize OpenAI client
    try:
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        st.session_state.openai_client = client
    except KeyError:
        st.error("OpenAI API key not configured. Please check your secrets.toml file.")
        return
    except Exception as e:
        st.error(f"Error initializing OpenAI client: {str(e)}")
        return
    
    # Page header
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("💬 Chat")
    with col2:
        if st.button("← Back to Home"):
            st.switch_page("Home.py")
    
    st.markdown("---")
    
    # Initialize session state for chat
    if "current_conversation" not in st.session_state:
        st.session_state.current_conversation = None
    if "current_prompt" not in st.session_state:
        st.session_state.current_prompt = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Check if we need to load a specific conversation (from main page)
    if "selected_conversation" in st.session_state:
        load_conversation(st.session_state.selected_conversation, user_code)
        del st.session_state.selected_conversation
    
    # Sidebar for conversation management
    with st.sidebar:
        show_conversation_sidebar(user_code)
    
    # Main chat area
    show_chat_interface(user_code)

def show_conversation_sidebar(user_code: str):
    """Show conversation management in sidebar"""
    st.header("Conversations")
    
    # New chat button
    if st.button("📝 New Chat", use_container_width=True):
        show_prompt_selection_modal(user_code)
    
    st.markdown("---")
    
    # Current conversation info
    if st.session_state.current_conversation:
        st.subheader("Current Conversation")
        st.write(f"**ID:** {st.session_state.current_conversation}")
        if st.session_state.current_prompt:
            prompt_data = get_prompt_by_id(st.session_state.current_prompt)
            if prompt_data:
                st.write(f"**Prompt:** {st.session_state.current_prompt}")
                with st.expander("View Prompt"):
                    st.write(prompt_data["content"])
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            clear_current_chat()
    
    st.markdown("---")
    
    # Conversation history
    st.subheader("Chat History")
    conversations = get_user_conversations(user_code)
    
    if conversations:
        for conv in conversations:
            conv_label = f"{conv['conversation_id']}"
            if conv.get('messages'):
                last_msg = conv['messages'][-1]['content'][:30] + "..." if len(conv['messages'][-1]['content']) > 30 else conv['messages'][-1]['content']
                conv_label += f" - {last_msg}"
            
            if st.button(conv_label, key=f"conv_{conv['conversation_id']}", use_container_width=True):
                load_conversation(conv['conversation_id'], user_code)
    else:
        st.write("No conversations yet. Start a new chat!")

def show_prompt_selection_modal(user_code: str):
    """Show prompt selection interface"""
    prompts = get_user_prompts(user_code)
    
    if not prompts:
        st.error("No prompts found. Please create a prompt first on the Prompts page.")
        return
    
    st.subheader("Select a Prompt for New Conversation")
    
    # Create prompt options
    prompt_options = {}
    for prompt in prompts:
        label = f"{prompt['prompt_id']} - {prompt['content'][:50]}{'...' if len(prompt['content']) > 50 else ''}"
        prompt_options[label] = prompt['prompt_id']
    
    selected_prompt_label = st.selectbox(
        "Choose a prompt:",
        options=list(prompt_options.keys()),
        key="prompt_selector"
    )
    
    if selected_prompt_label:
        selected_prompt_id = prompt_options[selected_prompt_label]
        prompt_data = get_prompt_by_id(selected_prompt_id)
        
        if prompt_data:
            st.write("**Selected Prompt:**")
            st.info(prompt_data["content"])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Start Chat", use_container_width=True):
                    start_new_conversation(selected_prompt_id, user_code)
            with col2:
                if st.button("Cancel", use_container_width=True):
                    st.rerun()

def start_new_conversation(prompt_id: str, user_code: str):
    """Start a new conversation with selected prompt"""
    # Get prompt content
    prompt_data = get_prompt_by_id(prompt_id)
    if not prompt_data:
        st.error("Error loading prompt data.")
        return
    
    # Initialize conversation with system message
    messages = [{
        "role": "system",
        "content": prompt_data["content"],
        "timestamp": datetime.utcnow()
    }]
    
    # Save conversation to database
    conversation_id = save_conversation(user_code, prompt_id, messages)
    
    if conversation_id:
        st.session_state.current_conversation = conversation_id
        st.session_state.current_prompt = prompt_id
        st.session_state.messages = messages
        
        log_conversation_start(user_code, conversation_id, prompt_id)
        log_prompt_selection(user_code, prompt_id)
        
        st.success(f"Started new conversation: {conversation_id}")
        st.rerun()
    else:
        st.error("Error creating conversation.")

def load_conversation(conversation_id: str, user_code: str):
    """Load an existing conversation"""
    conversation = get_conversation_by_id(conversation_id)
    if conversation and conversation["user_code"] == user_code:
        st.session_state.current_conversation = conversation_id
        st.session_state.current_prompt = conversation["prompt_id"]
        st.session_state.messages = conversation["messages"]
        
        log_conversation_continue(user_code, conversation_id)
        st.rerun()
    else:
        st.error("Conversation not found or access denied.")

def clear_current_chat():
    """Clear current chat session"""
    st.session_state.current_conversation = None
    st.session_state.current_prompt = None
    st.session_state.messages = []
    st.rerun()

def show_chat_interface(user_code: str):
    """Show the main chat interface"""
    if not st.session_state.current_conversation:
        st.info("Select 'New Chat' from the sidebar to start a conversation with a prompt.")
        return
    
    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] == "system":
            continue  # Don't display system messages
            
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message..."):
        handle_user_message(prompt, user_code)

def handle_user_message(user_input: str, user_code: str):
    """Handle user message and get AI response"""
    # Add user message
    user_message = {
        "role": "user",
        "content": user_input,
        "timestamp": datetime.utcnow()
    }
    
    st.session_state.messages.append(user_message)
    
    # Display user message
    with st.chat_message("user"):
        st.write(user_input)
    
    # Log user message
    log_chat_message(user_code, st.session_state.current_prompt, "user", user_input)
    
    # Get AI response
    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Prepare messages for OpenAI (exclude timestamp)
                openai_messages = []
                for msg in st.session_state.messages:
                    openai_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
                
                # Call OpenAI API
                client = st.session_state.openai_client
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=openai_messages,
                    max_tokens=1000,
                    temperature=0.7
                )
                
                assistant_response = response.choices[0].message.content
                st.write(assistant_response)
                
                # Add assistant message
                assistant_message = {
                    "role": "assistant",
                    "content": assistant_response,
                    "timestamp": datetime.utcnow()
                }
                
                st.session_state.messages.append(assistant_message)
                
                # Log assistant message
                log_chat_message(user_code, st.session_state.current_prompt, "assistant", assistant_response)
                
                # Update conversation in database
                update_conversation(st.session_state.current_conversation, st.session_state.messages)
                
    except Exception as e:
        st.error(f"Error getting AI response: {str(e)}")
        log_error(user_code, "openai_error", str(e), {"prompt_id": st.session_state.current_prompt})

if __name__ == "__main__":
    main()