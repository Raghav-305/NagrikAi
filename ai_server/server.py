import os
import uuid
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langchain_core.messages import messages_to_dict

# Import your compiled graph and state
from graph import crm_app
from state import CRMState

app = FastAPI(title="Smart City AI Orchestration Engine")

INTERNAL_SECRET_TOKEN = os.getenv("INTERNAL_SECRET_TOKEN")

def verify_token(x_api_token: str = Header(...)):
    if x_api_token != INTERNAL_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized access to AI Server")

# --- Data Schemas ---
class ComplaintRequest(BaseModel):
    text: str
    image_base64: str = "" 
    location_text: str = ""
    timestamp: str = ""

class HumanUpdateRequest(BaseModel):
    complaint_id: str 
    crew_note: str

# --- Endpoints ---

@app.get("/health")
def health_check():
    """A simple endpoint for Docker to check if the server is healthy."""
    return {"status": "healthy", "model": "LangGraph Multi-Agent Orchestrator Active"}


@app.post("/api/process-ticket")
def process_ticket(request: ComplaintRequest, token: None = Depends(verify_token)):
    """Receives new citizen data, runs the Orchestrator, and starts the memory thread, routes to Managers, and returns final QC'd data."""
    
    # 1. Create the Master Epic ID AND the First Task ID
    master_complaint_id = f"COMP-{str(uuid.uuid4())[:8]}"
    first_ticket_id = f"TICKET-GEN-{str(uuid.uuid4())[:8]}" # Will be overwritten by specific Dept ID

    initial_state = CRMState(
        complaint_id=master_complaint_id,
        citizen_report_text=request.text,
        image_base64=request.image_base64,
        location_data={"reported_address": request.location_text},
        timestamp=request.timestamp,
        messages=[],
        current_ticket_id=first_ticket_id,
        department_assigned="",
        priority="",
        deadline="",
        action_plan="",
        next_node="",
        ai_analysis={},
        auditor_compliance_log="",
        auditor_feedback="",
        latest_human_update="",
        ticket_history=[]
    )
    
    # 3. CRITICAL: Tell SQLite to save this under the MASTER Complaint ID!
    config = {"configurable": {"thread_id": master_complaint_id}}
    
    # 4. Run the AI Graph
    final_state = crm_app.invoke(initial_state, config=config)
    
    # 5. Extract the safe, serialized LangChain messages (Optional, for your Central Backend logs)
    serializable_messages = messages_to_dict(final_state.get("messages", []))

    # 6. Return the perfectly slim DTO payload
    return {
        "success": True,
        "status": "AWAITING_FIELD_CREW",
        "complaint_id": final_state.get("complaint_id"),
        "current_ticket_id": final_state.get("current_ticket_id"),
        "department_assigned": final_state.get("department_assigned"),
        "priority": final_state.get("priority"),
        "deadline": final_state.get("deadline"),
        "action_plan": final_state.get("action_plan"),
        "ai_analysis": final_state.get("ai_analysis"),
        "ai_message_log": serializable_messages # Central DB can save this if it wants to track tokens
    }


@app.post("/api/human-update")
def process_human_update(request: HumanUpdateRequest, token: None = Depends(verify_token)):
    """Receives a note from a field crew, wakes up the AI, and generates the next ticket."""
    
    # 1. Tell LangGraph exactly which memory thread to wake up from the SQLite database
    config = {"configurable": {"thread_id": request.complaint_id}}
    
    # 2. We ONLY pass the new information! LangGraph will automatically fetch 
    # the old images, text, and ticket_history from SQLite and merge them.
    update_state = {
        "latest_human_update": request.crew_note
    }

    # 3. Wake up the graph!
    updated_state = crm_app.invoke(update_state, config=config)

    # 4. Extract the updated message history
    serializable_messages = messages_to_dict(updated_state.get("messages", []))

    # 5. Check if the AI decided to close the ticket
    if updated_state.get("next_node") == "END":
        current_status = "FULLY_RESOLVED"
    else:
        current_status = "AWAITING_FIELD_CREW"

    # 6. Return the newly adjusted plan to the Central Backend
    return {
        "success": True,
        "status": current_status,
        "complaint_id": updated_state.get("complaint_id"),
        "current_ticket_id": updated_state.get("current_ticket_id"), # This will be the NEW ticket ID!
        "new_department_assigned": updated_state.get("department_assigned"), 
        "priority": updated_state.get("priority"),
        "revised_action_plan": updated_state.get("action_plan"),
        "ai_analysis": updated_state.get("ai_analysis"),
        "full_ticket_history": updated_state.get("ticket_history"), # Sends the full timeline!
        "ai_message_log": serializable_messages
    }