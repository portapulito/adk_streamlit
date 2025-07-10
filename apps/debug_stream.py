"""
Streamlit con DEBUG per capire dove appare esattamente request_human_approval
"""

import streamlit as st
import requests
import json
import uuid
import time
from typing import Dict, Any, Tuple, Optional

# Set page config
st.set_page_config(
    page_title="🔍 Debug Approval",
    page_icon="🔍",
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
if "debug_events" not in st.session_state:
    st.session_state.debug_events = []

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
            st.session_state.debug_events = []
            return True
        else:
            st.error(f"Errore creazione sessione: {response.text}")
            return False
    except Exception as e:
        st.error(f"Errore connessione: {e}")
        return False

def debug_approval_detection(events):
    """
    🔍 DEBUG: Analizza dove appare esattamente request_human_approval
    """
    approval_found_locations = []
    
    for i, event in enumerate(events):
        event_str = str(event)
        
        # Ricerca grezza (che funziona)
        if "request_human_approval" in event_str.lower():
            approval_found_locations.append({
                "event_index": i,
                "method": "string_search",
                "event_keys": list(event.keys()) if isinstance(event, dict) else "not_dict",
                "event_preview": str(event)[:200] + "..." if len(str(event)) > 200 else str(event)
            })
        
        # Analisi strutturata per debug
        if isinstance(event, dict):
            # Check content.parts
            if "content" in event and "parts" in event.get("content", {}):
                for part in event["content"]["parts"]:
                    if "function_call" in part:
                        approval_found_locations.append({
                            "event_index": i,
                            "method": "content.parts.function_call",
                            "function_name": part["function_call"].get("name"),
                            "event_preview": str(part)[:200]
                        })
            
            # Check actions
            if "actions" in event:
                approval_found_locations.append({
                    "event_index": i,
                    "method": "actions",
                    "actions_content": str(event["actions"])[:200],
                    "event_preview": str(event)[:200]
                })
            
            # Check tool_use
            if "tool_use" in event:
                approval_found_locations.append({
                    "event_index": i,
                    "method": "tool_use",
                    "tool_content": str(event["tool_use"])[:200],
                    "event_preview": str(event)[:200]
                })
            
            # Check long_running_tool_ids
            if "long_running_tool_ids" in event:
                approval_found_locations.append({
                    "event_index": i,
                    "method": "long_running_tool_ids",
                    "tool_ids": event["long_running_tool_ids"],
                    "event_preview": str(event)[:200]
                })
    
    return approval_found_locations

def send_test_message(message: str):
    """Send a test message with FULL DEBUG"""
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
        
        # 🔍 DEBUG: Salva eventi per analisi
        st.session_state.debug_events = events
        
        # 🔍 DEBUG: Analizza dove appare approval
        approval_locations = debug_approval_detection(events)
        
        # Metodo SEMPLICE che funziona
        approval_detected = False
        assistant_message = ""
        
        for event in events:
            # Check for approval request (metodo che FUNZIONA)
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
            
            # DEBUG: Mostra dove è stato trovato
            if approval_locations:
                debug_msg = f"🔍 **DEBUG:** Approval trovato in {len(approval_locations)} location(s)"
                st.session_state.messages.append({
                    "role": "debug",
                    "content": debug_msg
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

st.title("🔍 Debug Approval Detection")
st.caption("Scopriamo dove appare esattamente request_human_approval negli eventi")

# Status
col1, col2 = st.columns(2)
with col1:
    if st.session_state.session_id:
        st.success(f"✅ Sessione: {st.session_state.session_id[-8:]}")
    else:
        st.info("ℹ️ Sessione: Non creata")

with col2:
    if st.session_state.pending_approval:
        st.warning("⏳ Approval Pending")
    else:
        st.success("✅ Pronto")

st.divider()

# Test button
if st.button("🗑️ TEST: Elimina File", type="primary", use_container_width=True):
    send_test_message("Elimina tutti i file")
    st.rerun()

st.divider()

# Chat Messages
st.subheader("💬 Chat")
for msg in st.session_state.messages[-5:]:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])
    elif msg["role"] == "system":
        st.chat_message("assistant").warning(msg["content"])
    elif msg["role"] == "debug":
        st.chat_message("assistant").info(msg["content"])

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

# DEBUG SECTION
st.divider()
st.subheader("🔍 DEBUG INFO")

if st.session_state.debug_events:
    
    # Analizza gli eventi
    approval_locations = debug_approval_detection(st.session_state.debug_events)
    
    if approval_locations:
        st.success(f"✅ Trovato 'request_human_approval' in {len(approval_locations)} location(s):")
        
        for i, location in enumerate(approval_locations):
            with st.expander(f"📍 Location {i+1}: {location['method']}"):
                st.json(location)
    else:
        st.warning("❌ 'request_human_approval' NON trovato negli eventi")
    
    # Eventi completi
    with st.expander("📋 Eventi completi (JSON)"):
        st.json(st.session_state.debug_events)
    
    # Preview eventi
    with st.expander("👀 Preview eventi"):
        for i, event in enumerate(st.session_state.debug_events):
            st.write(f"**Evento {i}:**")
            st.code(str(event)[:500] + "..." if len(str(event)) > 500 else str(event))
            st.divider()

if st.button("🗑️ Pulisci Debug"):
    st.session_state.debug_events = []
    st.session_state.messages = []
    st.session_state.pending_approval = False
    st.rerun()