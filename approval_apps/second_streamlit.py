"""
Streamlit UI completo con rilevamento approval STRUTTURATO CORRETTO
Basato sulla struttura ADK reale scoperta tramite debug
"""

import streamlit as st
import requests
import json
import uuid
import time
from typing import Dict, Any, Tuple, Optional

# Set page config
st.set_page_config(
    page_title="🛡️ Test Approval Strutturato",
    page_icon="🛡️",
    layout="centered"
)

# Constants
API_BASE_URL = "http://localhost:8000"
APP_NAME = "agent_approval"  # Cambia questo con il nome del tuo agente

# Initialize session state
if "user_id" not in st.session_state:
    st.session_state.user_id = f"user-{uuid.uuid4()}"
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = False
if "approval_details" not in st.session_state:
    st.session_state.approval_details = None

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
            st.session_state.approval_details = None
            return True
        else:
            st.error(f"Errore creazione sessione: {response.text}")
            return False
    except Exception as e:
        st.error(f"Errore connessione: {e}")
        return False

def detect_approval_structured(events) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    🎯 RILEVAMENTO STRUTTURATO CORRETTO: Basato sulla struttura ADK reale
    
    Returns:
        Tuple[bool, Optional[Dict]]: (approval_detected, approval_details)
    """
    approval_detected = False
    approval_details = None
    
    for event in events:
        if "content" in event and "parts" in event["content"]:
            for part in event["content"]["parts"]:
                
                # ✅ METODO 1: functionCall (quando l'agente chiama il tool)
                if "functionCall" in part:  # ← camelCase!
                    function_call = part["functionCall"]
                    # Controlliamo se ha i parametri dell'approval
                    if "args" in function_call:
                        args = function_call["args"]
                        # Se ha action/details, probabilmente è approval
                        if "action" in args or "details" in args:
                            approval_detected = True
                            approval_details = args
                            break
                
                # ✅ METODO 2: functionResponse (risposta del tool - più preciso)
                if "functionResponse" in part:  # ← camelCase!
                    function_response = part["functionResponse"]
                    if function_response.get("name") == "request_human_approval":
                        approval_detected = True
                        # I dettagli sono nella response
                        approval_details = function_response.get("response", {})
                        break
        
        # Se abbiamo trovato approval, interrompi
        if approval_detected:
            break
    
    return approval_detected, approval_details

def extract_assistant_message(events) -> str:
    """
    Estrae il messaggio dell'assistente dagli eventi
    """
    assistant_message = ""
    
    for event in events:
        # Cerca messaggi del modello
        if (event.get("content", {}).get("role") == "model" and 
            "parts" in event.get("content", {})):
            parts = event["content"]["parts"]
            for part in parts:
                if "text" in part:
                    assistant_message = part["text"]
                    break
            if assistant_message:
                break
    
    return assistant_message

def create_rich_approval_message(approval_details: Optional[Dict[str, Any]]) -> str:
    """
    Crea un messaggio di approval ricco di dettagli REALI
    """
    if not approval_details:
        return "🚨 **APPROVAL RICHIESTO** - Usa i pulsanti sotto"
    
    # Estrai dettagli reali dall'ADK
    action = approval_details.get("action", "Azione sconosciuta")
    details = approval_details.get("details", "Nessun dettaglio disponibile")
    risk_level = approval_details.get("risk_level", "medium")
    status = approval_details.get("status", "pending")
    
    # Normalizza risk_level
    risk_level_upper = risk_level.upper() if risk_level else "MEDIUM"
    
    # Emoji per livello di rischio
    risk_emoji = {
        "LOW": "🟢",
        "MEDIUM": "🟡", 
        "HIGH": "🔴"
    }
    
    # Tronca testi troppo lunghi per UI
    action_display = action[:50] + "..." if len(action) > 50 else action
    details_display = details[:100] + "..." if len(details) > 100 else details
    
    message = f"""🚨 **RICHIESTA APPROVAZIONE**

{risk_emoji.get(risk_level_upper, '⚠️')} **Livello Rischio:** {risk_level_upper}
🎯 **Azione:** {action_display}
📋 **Dettagli:** {details_display}
📊 **Status:** {status}

**Usa i pulsanti sotto per rispondere:**
✅ **SI** - Approva l'azione
❌ **NO** - Rifiuta l'azione  
ℹ️ **DETTAGLI** - Richiedi più informazioni"""
    
    return message

def send_test_message(message: str):
    """Send a test message with STRUCTURED approval detection"""
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
        
        # Process response with STRUCTURED detection
        events = response.json()
        
        # 🎯 USA IL RILEVAMENTO STRUTTURATO CORRETTO
        approval_detected, approval_details = detect_approval_structured(events)
        assistant_message = extract_assistant_message(events)
        
        # Update state
        if approval_detected:
            st.session_state.pending_approval = True
            st.session_state.approval_details = approval_details
        
        # Add assistant message
        if assistant_message:
            st.session_state.messages.append({"role": "assistant", "content": assistant_message})
        
        # Add approval notice with RICH details
        if approval_detected:
            approval_message = create_rich_approval_message(approval_details)
            st.session_state.messages.append({
                "role": "system", 
                "content": approval_message
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
        
        # Reset approval state
        st.session_state.pending_approval = False
        approval_details_copy = st.session_state.approval_details.copy() if st.session_state.approval_details else None
        st.session_state.approval_details = None
        
        # Add decision to chat with emoji
        decision_emoji = {"si": "✅", "no": "❌", "dettagli": "ℹ️"}
        decision_display = f"{decision_emoji.get(decision, '🔄')} **{decision.upper()}**"
        
        # Se abbiamo dettagli, aggiungi info sull'azione
        if approval_details_copy:
            action = approval_details_copy.get("action", "Azione")
            decision_display += f" - {action}"
        
        st.session_state.messages.append({
            "role": "user", 
            "content": decision_display
        })
        
        # Get final response
        if response.status_code == 200:
            events = response.json()
            final_message = extract_assistant_message(events)
            if final_message:
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": final_message
                })
        
        return True
        
    except Exception as e:
        st.error(f"Errore approval: {e}")
        return False

# ============================================================================
# UI COMPONENTS
# ============================================================================

st.title("🛡️ Test Approval Strutturato")
st.caption("Interfaccia con rilevamento approval strutturato e dettagli ricchi")

# Status indicators con informazioni dettagliate
col1, col2, col3 = st.columns(3)

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

with col3:
    # Mostra dettagli approval se disponibili
    if st.session_state.approval_details:
        risk = st.session_state.approval_details.get("risk_level", "unknown").upper()
        risk_color = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(risk, "⚠️")
        st.info(f"{risk_color} Rischio: {risk}")
    else:
        st.info("📊 Status: OK")

st.divider()

# Test Buttons
st.subheader("🧪 Test Rapidi")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**🟢 Richieste Sicure:**")
    if st.button("👋 Saluto", use_container_width=True):
        send_test_message("Ciao, come stai?")
        st.rerun()
    if st.button("🤖 Domanda AI", use_container_width=True):
        send_test_message("Spiegami cos'è l'intelligenza artificiale")
        st.rerun()
    if st.button("🧮 Calcolo", use_container_width=True):
        send_test_message("Quanto fa 25 x 4?")
        st.rerun()
    if st.button("📚 Storia", use_container_width=True):
        send_test_message("Raccontami una breve storia")
        st.rerun()

with col2:
    st.markdown("**🔴 Richieste con Approval:**")
    if st.button("🗑️ Elimina File", use_container_width=True):
        send_test_message("Elimina tutti i file della cartella documenti")
        st.rerun()
    if st.button("📧 Invia Email", use_container_width=True):
        send_test_message("Invia un'email a tutti i clienti con l'offerta speciale")
        st.rerun()
    if st.button("💰 Trasferimento", use_container_width=True):
        send_test_message("Trasferisci €500 al fornitore")
        st.rerun()
    if st.button("⚙️ Modifica Sistema", use_container_width=True):
        send_test_message("Modifica le impostazioni di sicurezza del sistema")
        st.rerun()

st.divider()

# Chat Messages
st.subheader("💬 Conversazione")
for msg in st.session_state.messages[-10:]:  # Show last 10 messages
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").write(msg["content"])
    elif msg["role"] == "system":
        st.chat_message("assistant").warning(msg["content"])

# Enhanced Approval Interface
if st.session_state.pending_approval:
    st.divider()
    
    # Header con dettagli ricchi se disponibili
    if st.session_state.approval_details:
        risk = st.session_state.approval_details.get("risk_level", "medium").upper()
        action = st.session_state.approval_details.get("action", "Azione")
        risk_emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(risk, "⚠️")
        st.error(f"🚨 **APPROVAZIONE RICHIESTA** - {action} ({risk_emoji} {risk})")
    else:
        st.error("🚨 **APPROVAZIONE RICHIESTA**")
    
    # Pulsanti approval
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ APPROVA", type="primary", use_container_width=True):
            send_approval("si")
            st.rerun()
    
    with col2:
        if st.button("❌ RIFIUTA", type="secondary", use_container_width=True):
            send_approval("no")
            st.rerun()
    
    with col3:
        if st.button("ℹ️ DETTAGLI", use_container_width=True):
            send_approval("dettagli")
            st.rerun()

# Manual input
st.divider()
user_input = st.chat_input("Scrivi un messaggio...")
if user_input:
    send_test_message(user_input)
    st.rerun()

# Control buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("🗑️ Pulisci Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_approval = False
        st.session_state.approval_details = None
        st.rerun()

with col2:
    if st.button("🔄 Nuova Sessione", use_container_width=True):
        if create_session():
            st.rerun()

# Enhanced Sidebar con info dettagliate
with st.sidebar:
    st.header("🔧 Sistema Info")
    
    # Metodo di rilevamento
    st.success("🎯 Metodo: STRUTTURATO")
    st.caption("Usa functionCall/functionResponse ADK")
    
    st.divider()
    
    # Statistiche sessione
    st.subheader("📊 Statistiche")
    stats = {
        "APP_NAME": APP_NAME,
        "total_messages": len(st.session_state.messages),
        "pending_approval": st.session_state.pending_approval,
        "has_approval_details": bool(st.session_state.approval_details)
    }
    st.json(stats)
    
    # Dettagli approval se disponibili
    if st.session_state.approval_details:
        st.divider()
        st.subheader("📋 Approval Details")
        st.json(st.session_state.approval_details)
    
    st.divider()
    
    # Info tecnico
    st.subheader("🔧 Info Tecnico")
    st.caption("🚀 Versione: Strutturato v2.0")
    st.caption("🔍 Debug: Basato su analisi eventi reali")
    st.caption("🎯 Supporta: functionCall, functionResponse")
    
    # Quick help
    with st.expander("💡 Come Funziona"):
        st.markdown("""
        **Rilevamento Strutturato:**
        1. 🔍 Analizza `content.parts` negli eventi
        2. 🎯 Cerca `functionCall` (chiamata tool)  
        3. 📥 Cerca `functionResponse` (risposta tool)
        4. 📊 Estrae dettagli: action, details, risk_level
        5. 🎨 Mostra interfaccia ricca con emoji
        
        **Vantaggi vs Metodo Grezzo:**
        - ✅ Informazioni complete
        - ✅ Livelli di rischio 
        - ✅ Dettagli azione
        - ✅ Status preciso
        """)