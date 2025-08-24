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
    update_conversation,
    id_to_display_number
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
    
    st.markdown("---")
    
    # Initialize session state for chat
    if "current_conversation" not in st.session_state:
        st.session_state.current_conversation = None
    if "current_prompt" not in st.session_state:
        st.session_state.current_prompt = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "show_prompt_selector" not in st.session_state:
        st.session_state.show_prompt_selector = False
    
    # Check if we need to load a specific conversation (from main page)
    if "selected_conversation" in st.session_state:
        conversation_id = st.session_state.selected_conversation
        load_conversation(conversation_id, user_code)
        del st.session_state.selected_conversation
    
    # Check if we need to start a new conversation with a selected prompt (from prompt page)
    if "selected_prompt" in st.session_state:
        prompt_id = st.session_state.selected_prompt
        start_new_conversation(prompt_id, user_code)
        del st.session_state.selected_prompt
        return
    
    # Sidebar for conversation management
    with st.sidebar:
        show_conversation_sidebar(user_code)
    
    # Main chat area
    if st.session_state.show_prompt_selector:
        show_prompt_selection_modal(user_code)
    else:
        show_chat_interface(user_code)

def show_conversation_sidebar(user_code: str):
    """Show conversation management in sidebar"""
    st.header("Conversations")
    
    # New chat button
    if st.button("📝 New Chat", use_container_width=True):
        st.session_state.show_prompt_selector = True
    
    st.markdown("---")
    
    # Current conversation info
    if st.session_state.current_conversation:
        st.subheader("Current Conversation")
        st.write(f"**Conversation No.** {id_to_display_number(st.session_state.current_conversation)}")
        if st.session_state.current_prompt:
            prompt_data = get_prompt_by_id(st.session_state.current_prompt, user_code)
            if prompt_data:
                st.write(f"**Prompt No.** {id_to_display_number(st.session_state.current_prompt)}")
                with st.expander("View Prompt"):
                    st.write(prompt_data["content"])
                    
                    # Show document information if available
                    if prompt_data.get('documents'):
                        st.write("**📎 Attached Documents:**")
                        for doc in prompt_data['documents']:
                            st.write(f"• {doc['filename']}")
                            if len(doc.get('content', '')) > 100:
                                with st.expander(f"View {doc['filename']}"):
                                    st.write(doc['content'])
                            else:
                                st.write(f"_{doc.get('content', '')}_")
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            clear_current_chat()
    
    st.markdown("---")
    
    # Conversation history
    st.subheader("Chat History")
    conversations = get_user_conversations(user_code)
    
    if conversations:
        for conv in conversations:
            conv_label = f"{id_to_display_number(conv['conversation_id'])}"
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
        display_number = id_to_display_number(prompt['prompt_id'])
        label = f"{display_number} - {prompt['content'][:50]}{'...' if len(prompt['content']) > 50 else ''}"
        prompt_options[label] = prompt['prompt_id']
    
    selected_prompt_label = st.selectbox(
        "Choose a prompt:",
        options=list(prompt_options.keys()),
        key="prompt_selector"
    )
    
    if selected_prompt_label:
        selected_prompt_id = prompt_options[selected_prompt_label]
        
        # Validate that we have a valid prompt ID
        if not selected_prompt_id:
            st.error("Error: Invalid prompt selection. Please try again.")
            return
            
        prompt_data = get_prompt_by_id(selected_prompt_id, user_code)
        
        if prompt_data:
            st.write("**Selected Prompt:**")
            st.info(prompt_data["content"])
            
            # Debug information (can be removed in production)
            with st.expander("Debug Info"):
                st.write(f"**Prompt ID:** {selected_prompt_id}")
                st.write(f"**Display Number:** {id_to_display_number(selected_prompt_id)}")
                st.write(f"**User Code:** {user_code}")
            
            # Show document information if available
            if prompt_data.get('documents'):
                st.write("**📎 Attached Documents:**")
                for doc in prompt_data['documents']:
                    st.write(f"• {doc['filename']} ({doc['file_type']})")
                    if len(doc.get('content', '')) > 200:
                        with st.expander(f"Preview {doc['filename']}"):
                            st.write(doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content'])
                    else:
                        st.write(f"_{doc.get('content', '')}_")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Start Chat", use_container_width=True):
                    start_new_conversation(selected_prompt_id, user_code)
            with col2:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.show_prompt_selector = False
                    st.rerun()

def start_new_conversation(prompt_id: str, user_code: str):
    """Start a new conversation with selected prompt"""
    # Validate prompt_id format
    if not prompt_id or not isinstance(prompt_id, str):
        st.error("Error: Invalid prompt ID format.")
        return
        
    # Get prompt content
    prompt_data = get_prompt_by_id(prompt_id, user_code)
    if not prompt_data:
        st.error(f"Error loading prompt data for ID: {prompt_id}")
        return
    
    # Build system message with prompt content and documents
    system_content = prompt_data["content"]
    
    # Add document content if available
    if prompt_data.get('documents'):
        system_content += "\n\n**Reference Documents:**\n"
        for i, doc in enumerate(prompt_data['documents'], 1):
            system_content += f"\n--- Document {i}: {doc['filename']} ---\n"
            system_content += doc.get('content', '')
            system_content += "\n"
    
    # Initialize conversation with system message
    messages = [{
        "role": "system",
        "content": system_content,
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
        
        st.session_state.show_prompt_selector = False
        st.success(f"Started new conversation: {id_to_display_number(conversation_id)}")
        if prompt_data.get('documents'):
            st.success(f"📎 Loaded {len(prompt_data['documents'])} document(s) for context")
        st.rerun()
    else:
        st.error("Error creating conversation.")

def load_conversation(conversation_id: str, user_code: str):
    """Load an existing conversation"""
    try:
        conversation = get_conversation_by_id(conversation_id, user_code)
        
        if not conversation:
            st.error(f"Conversation {conversation_id} not found.")
            return False
            
        # Set session state
        st.session_state.current_conversation = conversation_id
        st.session_state.current_prompt = conversation["prompt_id"]
        st.session_state.messages = conversation.get("messages", [])
        
        log_conversation_continue(user_code, conversation_id)
        return True
        
    except Exception as e:
        st.error(f"Error loading conversation: {str(e)}")
        log_error(user_code, "conversation_load_error", str(e), {"conversation_id": conversation_id})
        return False

def clear_current_chat():
    """Clear current chat session"""
    st.session_state.current_conversation = None
    st.session_state.current_prompt = None
    st.session_state.messages = []
    st.session_state.show_prompt_selector = False
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
    
    # Get AI response with streaming
    try:
        with st.chat_message("assistant"):
            # Prepare messages for OpenAI (exclude timestamp)
            openai_messages = []
            for msg in st.session_state.messages:
                openai_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Call OpenAI API with streaming
            client = st.session_state.openai_client
            stream = client.chat.completions.create(
                model="gpt-4o",
                messages=openai_messages,
                max_completion_tokens=1000,
                stream=True  # Enable streaming
            )
            
            # Stream the response using st.write_stream()
            def stream_response():
                full_response = ""
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        yield content
                return full_response
            
            # Use st.write_stream to display the streaming response
            # We need to collect the full response separately since st.write_stream returns a generator
            full_response = ""
            message_placeholder = st.empty()
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    message_placeholder.markdown(full_response + "▌")
            
            # Display the final response
            message_placeholder.markdown(full_response)
            
            assistant_response = full_response
            
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