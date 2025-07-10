import asyncio
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

# Tool semplice per l'agente ADK - Calcolatrice
# Basato sulla documentazione ADK: https://google.github.io/adk-docs/tools/function-tools/

def calcola_operazione(operazione: str, numero1: float, numero2: float) -> dict:
    """Esegue operazioni matematiche di base.
    
    Args:
        operazione (str): Tipo di operazione ("addizione", "sottrazione", "moltiplicazione", "divisione")
        numero1 (float): Primo numero
        numero2 (float): Secondo numero
        
    Returns:
        dict: Risultato dell'operazione con status e risultato
    """
    operazioni_valide = {
        "addizione": "+",
        "sottrazione": "-", 
        "moltiplicazione": "*",
        "divisione": "/"
    }
    
    if operazione.lower() not in operazioni_valide:
        return {
            "status": "error",
            "error_message": f"Operazione '{operazione}' non supportata. Usa: addizione, sottrazione, moltiplicazione, divisione"
        }
    
    try:
        if operazione.lower() == "divisione" and numero2 == 0:
            return {
                "status": "error", 
                "error_message": "Impossibile dividere per zero"
            }
            
        if operazione.lower() == "addizione":
            risultato = numero1 + numero2
        elif operazione.lower() == "sottrazione":
            risultato = numero1 - numero2
        elif operazione.lower() == "moltiplicazione":
            risultato = numero1 * numero2
        elif operazione.lower() == "divisione":
            risultato = numero1 / numero2
            
        return {
            "status": "success",
            "operazione": f"{numero1} {operazioni_valide[operazione.lower()]} {numero2}",
            "risultato": risultato,
            "spiegazione": f"Il risultato di {numero1} {operazioni_valide[operazione.lower()]} {numero2} è {risultato}"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Errore nel calcolo: {str(e)}"
        }










root_agent = Agent(
    model="gemini-2.0-flash",
    name="simple",
    description="I am a simple agent",
    instruction="You are a helpful assistant.",
    tools=[calcola_operazione]


)
