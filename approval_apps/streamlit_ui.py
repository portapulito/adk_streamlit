"""
Test semplice per Human-in-the-Loop Approval
Focus solo sui test di approvazione
"""

import streamlit as st
import requests
import json
import uuid
import time

# Set page config
st.set_page_config(
    page_title="🛡️ Test Approval",
    page_icon="🛡️",
    layout="centered"
)

# Constants
API_BASE_URL = "http://localhost:8000"
APP_NAME = "agent_approval"

# Initialize session state
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user-{uuid.uuid4()}"
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = False

def create_session():
    """Create a new session"""
    session_id = f"session-{int(time.time())}"
    try:
        response = requests.post(
            f"{API_BASE_URL}/apps/{APP_NAME}/users/{st.session_state.user_id}/sessions/{session_id}",
            headers={"Content-Type": "application/json"},
            data=json.dumps({})
        )
        if response.status_code == 200:
            st.session_state.session_id = session_id
            st.session_state.messages = []
            st.session_state.pending_approval = False
            return True
        else:
            st.error(f"Errore creazione sessione: {response.text}")
            return False
    except Exception as e:
        st.error(f"Errore connessione: {e}")
        return False

def send_test_message(message: str):
    """Send a test message"""
    # Auto-create session
    if not st.session_state.session_id:
        if not create_session():
            return False
    
    # Add to chat
    st.session_state.messages.append({"role": "user", "content": message})
    
    try:
        # Send to API
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
            st.error(f"Errore API: {response.text}")
            return False
        
        # Process response
        events = response.json()
        approval_detected = False
        assistant_message = ""
        
        for event in events:
            # Check for approval request
            if "request_human_approval" in str(event).lower():
                approval_detected = True
                st.session_state.pending_approval = True
            
            # Get assistant message
            if event.get("content", {}).get("role") == "model":
                parts = event.get("content", {}).get("parts", [])
                if parts and "text" in parts[0]:
                    assistant_message = parts[0]["text"]
        
        # Add assistant message
        if assistant_message:
            st.session_state.messages.append({"role": "assistant", "content": assistant_message})
        
        # Add approval notice
        if approval_detected:
            st.session_state.messages.append({
                "role": "system", 
                "content": "🚨 **APPROVAL RICHIESTO** - Usa i pulsanti sotto"
            })
        
        return True
        
    except Exception as e:
        st.error(f"Errore: {e}")
        return False

def send_approval(decision: str):
    """Send approval decision"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/run",
            headers={"Content-Type": "application/json"},
            data=json.dumps({
                "app_name": APP_NAME,
                "user_id": st.session_state.user_id,
                "session_id": st.session_state.session_id,
                "new_message": {
                    "role": "user",
                    "parts": [{"text": decision}]
                }
            })
        )
        
        st.session_state.pending_approval = False
        
        # Add decision to chat
        decision_emoji = {"si": "✅", "no": "❌", "dettagli": "ℹ️"}
        st.session_state.messages.append({
            "role": "user", 
            "content": f"{decision_emoji.get(decision, '🔄')} **{decision.upper()}**"
        })
        
        # Get final response
        if response.status_code == 200:
            events = response.json()
            for event in events:
                if event.get("content", {}).get("role") == "model":
                    parts = event.get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        final_message = parts[0]["text"]
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": final_message
                        })
        
        return True
        
    except Exception as e:
        st.error(f"Errore approval: {e}")
        return False

# ============================================================================
# UI
# ============================================================================

st.title("🛡️ Test Approval")
st.caption("Testa il meccanismo di approvazione dell'agente")

# Status
col1, col2 = st.columns(2)
with col1:
    if st.session_state.session_id:
        st.success(f"✅ Sessione: {st.session_state.session_id[-8:]}")
    else:
        st.info("ℹ️ Sessione: Non creata")

with col2:
    if st.session_state.pending_approval:
        st.warning("⏳ In attesa di approval")
    else:
        st.success("✅ Pronto")

st.divider()

# Test Buttons
st.subheader("🧪 Test Rapidi")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**🟢 Richieste Sicure:**")
    if st.button("Saluto", use_container_width=True):
        send_test_message("Ciao!")
        st.rerun()
    if st.button("Domanda", use_container_width=True):
        send_test_message("Che cos'è l'AI?")
        st.rerun()
    if st.button("Calcolo", use_container_width=True):
        send_test_message("Quanto fa 2+2?")
        st.rerun()

with col2:
    st.markdown("**🔴 Richieste con Approval:**")
    if st.button("Elimina File", use_container_width=True):
        send_test_message("Elimina tutti i file")
        st.rerun()
    if st.button("Invia Email", use_container_width=True):
        send_test_message("Invia email a tutti")
        st.rerun()
    if st.button("Trasferisci Denaro", use_container_width=True):
        send_test_message("Trasferisci €1000")
        st.rerun()

st.divider()

# Chat Messages
st.subheader("💬 Chat")
for msg in st.session_state.messages[-5:]:  # Show only last 5 messages
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])
    elif msg["role"] == "system":
        st.chat_message("assistant").warning(msg["content"])

# Approval Buttons
if st.session_state.pending_approval:
    st.divider()
    st.warning("🚨 **RICHIESTA APPROVAZIONE**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ SI", type="primary", use_container_width=True):
            send_approval("si")
            st.rerun()
    
    with col2:
        if st.button("❌ NO", type="secondary", use_container_width=True):
            send_approval("no")
            st.rerun()
    
    with col3:
        if st.button("ℹ️ DETTAGLI", use_container_width=True):
            send_approval("dettagli")
            st.rerun()

# Manual input
st.divider()
user_input = st.chat_input("Messaggio manuale...")
if user_input:
    send_test_message(user_input)
    st.rerun()

# Clear chat
if st.button("🗑️ Pulisci Chat"):
    st.session_state.messages = []
    st.session_state.pending_approval = False
    st.rerun()