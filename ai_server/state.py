from typing import Annotated, TypedDict, List, Dict, Any
from langchain_core.messages import BaseMessage
import operator

class CRMState(TypedDict):
    
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Raw input by citizen
    complaint_id: str
    citizen_report_text: str
    image_base64: str
    location_data: dict
    timestamp: str

    # Architecture Internal Data
    current_ticket_id: str
    department_assigned: str
    priority: str
    deadline: str
    action_plan: str
    next_node: str
    ai_analysis: dict
    
    # quality control and compliance check output
    auditor_compliance_log: str
    auditor_feedback: str

    # response from crew
    latest_human_update: str

    # THE PERMANENT LEDGER (The Timeline)
    ticket_history: Annotated[List[Dict[str, Any]], operator.add]