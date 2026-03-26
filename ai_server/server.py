import os
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from graph import crm_app
from state import CRMState

app = FastAPI(title="Smart City AI Orchestration Engine")

INTERNAL_SECRET_TOKEN = os.getenv("INTERNAL_SECRET_TOKEN")

def verify_token(x_api_token: str = Header(...)):
    if x_api_token != INTERNAL_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized access to AI Server")

# Data Schema: What we expect frontend to send us
class ComplaintRequest(BaseModel):
    text: str
    image_base64: str = "" 
    location_text: str = ""
    timestamp: str = ""

# The Docker Health Check
@app.get("/health")
def health_check():
    """A simple endpoint for Docker/Hugging Face to check if the server is healthy."""
    return {"status": "healthy", "model": "LangGraph Multi-Agent Orchestrator Active"}

# The Main AI Endpoint
@app.post("/api/process-ticket")
def process_ticket(request: ComplaintRequest, token: None = Depends(verify_token)):
    """Receives multi-modal data, runs the Orchestrator, routes to Managers, and returns final QC'd data."""
    
    # Package the multi-modal incoming data into our CRMState structure
    initial_state = CRMState(
        citizen_report_text=request.text,
        image_base64=request.image_base64,
        location_data={"reported_address": request.location_text},
        timestamp=request.timestamp,
        messages=[],
        ticket_id="",
        final_department_assigned="",
        final_priority="",
        deadline="",
        action_taken="",
        next_node="",
        thought_process="",
        infrastructure_analysis="",
        utility_analysis="",
        public_safety_analysis="",
        environment_analysis="",
        auditor_compliance_log="",
        auditor_feedback=""
    )
    
    # Run the multi-agent LangGraph architecture
    final_state = crm_app.invoke(initial_state)

    message_log = []
    for msg in final_state.get("messages", []):
        # Check if the message is a standard string
        if isinstance(msg.content, str):
            message_log.append(f"{msg.type.upper()}: {msg.content}")
        # Check if it's our massive multi-modal list (we hide the base64 string so it doesn't lag your browser)
        elif isinstance(msg.content, list):
            message_log.append(f"{msg.type.upper()}: [Multi-modal Package containing Text and Base64 Image]")
    
    # Return clean JSON that matches the architecture's visual output
    return {
        "ticket_id": final_state.get("ticket_id", "TICKET-GEN-PENDING"),
        "final_department": final_state.get("final_department_assigned", "Triage Required"),
        "final_priority": final_state.get("final_priority", "Standard Triage"),
        "deadline": final_state.get("deadline", "3 days"),
        "action_plan": final_state.get("action_taken", "Internal work order pending detailed assessment."),
        "auditor_log": final_state.get("auditor_compliance_log", "Quality control check pending."),
        "raw_analysis": final_state.get("thought_process", "No analysis generated."),
        "message_history": message_log
    }