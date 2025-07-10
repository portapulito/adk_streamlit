"""
agent.py - Versione per Streamlit (SENZA input())
"""

from google.adk.agents import Agent
from google.adk.tools import LongRunningFunctionTool
from typing import Dict, Any

def request_human_approval(action: str, details: str, risk_level: str = "medium") -> Dict[str, Any]:
    """
    Richiede approvazione umana per un'azione importante.
    VERSIONE STREAMLIT: Non usa input(), restituisce richiesta di approvazione
    """
    print(f"\n🚨 RICHIESTA APPROVAZIONE UMANA")
    print(f"Azione: {action}")
    print(f"Dettagli: {details}")
    print(f"Livello rischio: {risk_level}")
    print("=" * 50)
    print("⏳ In attesa di approvazione da interfaccia Streamlit...")
    
    # NON usiamo input() - restituiamo immediatamente una richiesta di approvazione
    return {
        'status': 'pending_approval',
        'action': action,
        'details': details,
        'risk_level': risk_level,
        'message': f"🚨 Richiesta approvazione per: {action}",
        'needs_human_approval': True,
        'pending': True,
        'timestamp': 'now'
    }

# Creazione tool
approval_tool = LongRunningFunctionTool(func=request_human_approval)

# IMPORTANTE: La variabile DEVE chiamarsi 'root_agent'
root_agent = Agent(
    model="gemini-2.0-flash",
    name="human_approval_agent",
    description="Agente che richiede approvazione umana per azioni importanti",
    instruction="""
    Sei un assistente intelligente che aiuta gli utenti con varie richieste, 
    ma richiede sempre approvazione umana per azioni importanti o rischiose.
    
    PROCESSO:
    1. Analizza ogni richiesta dell'utente
    2. Determina se l'azione è rischiosa o importante
    3. Per azioni a rischio MEDIO o ALTO, usa SEMPRE request_human_approval
    4. Per azioni a basso rischio, procedi normalmente
    
    AZIONI CHE RICHIEDONO APPROVAZIONE:
    - Eliminare/cancellare qualcosa
    - Modificare impostazioni importanti  
    - Trasferire denaro o fare pagamenti
    - Inviare comunicazioni a molte persone
    - Pubblicare contenuti pubblicamente
    - Installare/scaricare software
    - Creare account o registrazioni
    
    AZIONI SICURE (no approvazione):
    - Rispondere a domande generali
    - Fornire informazioni
    - Spiegare concetti
    - Fare calcoli semplici
    - Raccontare storie
    
    FORMATO APPROVAZIONE:
    Quando usi request_human_approval, specifica:
    - action: Breve descrizione dell'azione
    - details: Spiegazione dettagliata di cosa faresti
    - risk_level: "low", "medium", o "high"
    
    Quando chiami request_human_approval, attendi che l'utente risponda tramite l'interfaccia.
    Dopo aver ricevuto la risposta (si/no/dettagli), procedi di conseguenza:
    - Se "si": esegui l'azione richiesta
    - Se "no": annulla l'azione e spiega che è stata annullata
    - Se "dettagli": fornisci più informazioni sull'azione
    """,
    tools=[approval_tool]
)