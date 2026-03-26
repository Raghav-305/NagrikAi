from typing import Annotated, TypedDict, List
from langchain_core.messages import BaseMessage
import operator

class CRMState(TypedDict):
    
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Raw input by citizen
    citizen_report_text: str
    image_base64: str
    location_data: dict
    timestamp: str

    # Architecture Internal Data
    ticket_id: str
    final_department_assigned: str
    final_priority: str
    deadline: str
    action_taken: str
    next_node: str
    thought_process: str
    
    # agent-specific analyses and tool outputs
    infrastructure_analysis: str # roads, bridges
    utility_analysis: str        # water, electricity
    public_safety_analysis: str  # police, traffic
    environment_analysis: str    # waste, parks
    
    # quality control and compliance check output
    auditor_compliance_log: str
    auditor_feedback: str