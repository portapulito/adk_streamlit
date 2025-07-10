import streamlit as st
import requests
import json
import uuid
import time

# Set page config
st.set_page_config(
    page_title="Simple Agent Chat",
    page_icon="💬",
    layout="centered"
)

# Constants
API_BASE_URL = "http://localhost:8000"
APP_NAME = "agent"

# Initialize session state variables
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user-{uuid.uuid4()}"
    
if "session_id" not in st.session_state:
    st.session_state.session_id = None
    
if "messages" not in st.session_state:
    st.session_state.messages = []

def create_session():
    """
    Create a new session with the simple agent.
    
    This function:
    1. Generates a unique session ID based on timestamp
    2. Sends a POST request to the ADK API to create a session
    3. Updates the session state variables if successful
    
    Returns:
        bool: True if session was created successfully, False otherwise
    
    API Endpoint:
        POST /apps/{app_name}/users/{user_id}/sessions/{session_id}
    """
    session_id = f"session-{int(time.time())}"
    response = requests.post(
        f"{API_BASE_URL}/apps/{APP_NAME}/users/{st.session_state.user_id}/sessions/{session_id}",
        headers={"Content-Type": "application/json"},
        data=json.dumps({})
    )
    
    if response.status_code == 200:
        st.session_state.session_id = session_id
        st.session_state.messages = []
        return True
    else:
        st.error(f"Failed to create session: {response.text}")
        return False

def send_message(message):
    """
    Send a message to the simple agent and process the response.
    
    MODIFICATO: Ora crea automaticamente una sessione se non esiste!
    
    This function:
    1. Creates a session automatically if none exists
    2. Adds the user message to the chat history
    3. Sends the message to the ADK API
    4. Processes the response to extract text information
    5. Updates the chat history with the assistant's response
    
    Args:
        message (str): The user's message to send to the agent
        
    Returns:
        bool: True if message was sent and processed successfully, False otherwise
    
    API Endpoint:
        POST /run
        
    Response Processing:
        - Parses the ADK event structure to extract text responses
        - Adds text information to the chat history
    """
    # 🎯 AUTO-CREATE SESSION: Se non esiste una sessione, creala automaticamente
    if not st.session_state.session_id:
        st.info("🔄 Creazione automatica sessione...")
        if not create_session():
            st.error("Impossibile creare la sessione automaticamente.")
            return False
        st.success("✅ Sessione creata automaticamente!")
    
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": message})
    
    # Send message to API
    response = requests.post(
        f"{API_BASE_URL}/run",
        headers={"Content-Type": "application/json"},
        data=json.dumps({
            "app_name": APP_NAME,
            "user_id": st.session_state.user_id,
            "session_id": st.session_state.session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": message}]
            }
        })
    )
    
    if response.status_code != 200:
        st.error(f"Error: {response.text}")
        return False
    
    # Process the response
    events = response.json()
    
    # Extract assistant's text response
    assistant_message = None
    
    for event in events:
        # Look for the final text response from the model
        if event.get("content", {}).get("role") == "model" and "text" in event.get("content", {}).get("parts", [{}])[0]:
            assistant_message = event["content"]["parts"][0]["text"]
    
    # Add assistant response to chat
    if assistant_message:
        st.session_state.messages.append({"role": "assistant", "content": assistant_message})
    
    return True

# UI Components
st.title("💬 Simple Agent Chat")

# Sidebar for session management
with st.sidebar:
    st.header("Session Management")
    
    if st.session_state.session_id:
        st.success(f"Active session: {st.session_state.session_id}")
        if st.button("➕ New Session"):
            create_session()
    else:
        st.info("La sessione verrà creata automaticamente quando inizierai a chattare")
        # OPZIONALE: Mantieni il pulsante per creare manualmente
        if st.button("➕ Create Session Now"):
            create_session()
    
    st.divider()
    st.caption("This app interacts with the Simple Agent via the ADK API Server.")
    st.caption("Make sure the ADK API Server is running on port 8000.")

# Chat interface
st.subheader("Conversation")

# Display messages
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        st.chat_message("assistant").write(msg["content"])

# MODIFICA PRINCIPALE: Input sempre disponibile, sessione creata al volo
user_input = st.chat_input("Type your message...")
if user_input:
    send_message(user_input)
    st.rerun()  # Rerun to update the UI with new messages