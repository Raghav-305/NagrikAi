from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import json
import uuid
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from state import CRMState
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# text model
text_llm = ChatGroq(temperature=0, model_name="llama-3.1-8b-instant", api_key=GROQ_API_KEY)

# Vision model
vision_llm = ChatGroq(temperature=0, model_name="meta-llama/llama-4-scout-17b-16e-instruct", api_key=GROQ_API_KEY)

def get_sla(priority):
    if priority == "Critical":
        return "4 hours"
    if priority == "High":
        return "24 hours"
    elif priority == "Moderate":
        return "3 days"
    else:
        return "7 days"
    
# Define Node Functions for each Agent (Managers)

def orchestrator_node(state: CRMState):
    """The brain that routes the complaint, and reacts to human crew updates."""
    text = state.get("citizen_report_text", "")
    location = state.get("location_data", {})
    timestamp = state.get("timestamp", "")
    
    # Grab the update AND the department that just did the work
    human_update = state.get("latest_human_update", "")
    current_dept = state.get("department_assigned", "None") 
    
    # Check if the Auditor kicked this back (The Rejection Loop)
    feedback = state.get("auditor_feedback", "")
    feedback_text = f"\nAUDITOR REJECTION FEEDBACK: {feedback}\nDo not route to the rejected department again!" if feedback else ""

    # DYNAMIC CONTEXT: Change the prompt entirely based on the timeline phase
    if human_update:
        context_block = f"""
        --- STATUS: POST-WORK REVIEW ---
        Original Citizen Report: "{text}"
        Department That Just Finished: "{current_dept}"
        Human Crew Field Note: "{human_update}"
        
        TASK: The {current_dept} crew has completed their part of the job and left a note. 
        Read their note to determine if ANOTHER department needs to step in to finish related repairs (e.g., repairing a road after a pipe is fixed). 
        If another department is needed, output their node name. 
        If the entire situation is fully resolved and no further action is needed by the city, output "END".
        """
    else:
        context_block = f"""
        --- STATUS: NEW TICKET TRIAGE ---
        Original Citizen Report: "{text}"
        GPS Location: "{location}"
        Submitted Time: "{timestamp}"
        {feedback_text}
        
        TASK: Analyze the raw citizen input and route it to the CORRECT Specialized Manager Agent to handle the primary issue.
        """

    # 3. The Master Prompt
    ORCHESTRATOR_PROMPT = f"""You are the 'City CRM Orchestrator Agent' (The Brain). 
    
    {context_block}

    ROUTING OPTIONS:
    - INFRASTRUCTURE: Roads, Bridges, Sidewalks, or Potholes.
    - UTILITY: Water supply, Electricity leakage, Sewerage, or Power lines.
    - PUBLIC_SAFETY: Traffic, Police emergencies, or Hazardous obstructions.
    - ENVIRONMENT: Waste management, Garbage, Sanitation, Parks, or Trees.
    - END: Use this ONLY if there is a 'Human Crew Field Note' stating the problem is 100% resolved.

    CRITICAL INSTRUCTION: You must output your decision STRICTLY as a valid JSON object.
    Do not try to solve the problem yourself. Your only job is to provide the 'next_node' for routing.
    
    You must use this exact schema:
    {{
        "next_node": "INFRASTRUCTURE"
    }}
    """
    
    # invoke LLM to get routing decision
    response = text_llm.invoke([HumanMessage(content=ORCHESTRATOR_PROMPT)])
    
    # JSON parser
    try:
        clean_text = response.content.strip().strip("```json").strip("```")
        if "{" in clean_text and "}" in clean_text:
            clean_text = clean_text[clean_text.find("{"):clean_text.rfind("}")+1]
            
        data = json.loads(clean_text)
        next_node = data.get("next_node", END).upper()
        
    except json.JSONDecodeError:
        print(f"🚨 ORCHESTRATOR JSON PARSE FAILED: {response.content}")
        next_node = END
        
    return {"messages": [response], "next_node": next_node}

def infrastructure_node(state: CRMState):
    """Handles Roads & Bridges complaints using the Vision Model if an image is present."""
    location = state.get("location_data", {})
    timestamp = state.get("timestamp", "")
    image_base64 = state.get("image_base64", "")
    citizen_text = state.get("citizen_report_text", "")
    
    INFRASTRUCTURE_PROMPT = f"""You are the 'City Infrastructure Manager'.
    Analyze the citizen's complaint regarding Roads or Bridges.
    Reported Text: "{citizen_text}"
    Reported Location: "{location}"
    Time: "{timestamp}"
    
    1. Define the infrastructure problem.
    2. Estimate the severity. If an image is provided, use it to verify the text.
    3. Draft the Action Plan for the Physical Response Crew.
    CRITICAL INSTRUCTION: You must output your analysis STRICTLY as a valid JSON object. 
    Do not include conversational filler. 

    You must use this exact schema:
    {{
        "Infrastructure_Problem_Definition": "1-2 sentences defining the exact physical problem.",
        "Severity": "Your assessment of the severity (e.g., Low, Moderate, High, Critical)",
        "Reason": "Your reason for severity",
        "Action_Plan": "A step-by-step plan for the response crew.",
        "Conclusion": "A brief 1-sentence summary of the expected outcome."
    }}
    """

    if image_base64 and image_base64.strip() != "":
        message = HumanMessage(
            content=[
                {"type": "text", "text": INFRASTRUCTURE_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]
        )
        response = vision_llm.invoke([message])
        llm_source = "Vision Tool"
    else:
        message = HumanMessage(content=INFRASTRUCTURE_PROMPT)
        response = text_llm.invoke([message])
        llm_source = "Text Tool"

    try:
        clean_text = response.content.strip().strip("```json").strip("```")
        analysis_data = json.loads(clean_text)
        plan = analysis_data.get("Action_Plan", "Pending detailed assessment.")
        severity = analysis_data.get("Severity", "Moderate")
    except json.JSONDecodeError:
        analysis_data = {"error": f"Failed to parse JSON. Raw output: {response.content}"}
        plan = "Manual assessment required. AI failed to generate strict plan."
        severity = "Requires Triage"

    ticket_id = f"INFR-{str(uuid.uuid4())[:8]}"
    
    return {
        "messages": [response], 
        "ai_analysis": analysis_data, # Saved as a clean dict!
        "department_assigned": "Roads & Bridges PWD",
        "priority": f"{severity} (via {llm_source})",
        "deadline": get_sla(severity),
        "current_ticket_id": ticket_id,
        "action_plan": plan,
        "next_node": "AUDITOR"
    }

def utility_node(state: CRMState):
    """Handles Water, Electricity, and Sewer complaints."""
    location = state.get("location_data", {})
    timestamp = state.get("timestamp", "")
    image_base64 = state.get("image_base64", "")
    citizen_text = state.get("citizen_report_text", "")
    
    UTILITY_PROMPT = f"""You are the 'City Utility Manager'.
    Analyze this complaint regarding Water, Power, or Sewers.
    Report: "{citizen_text}" | Location: "{location}" | Time: "{timestamp}"
    
    1. Define the utility hazard.
    2. Estimate severity (check for live wires, flooding, etc.). If an image is provided, use it to verify.
    3. Draft the Action Plan for the Utility Crew.
    
    CRITICAL INSTRUCTION: You must output your analysis STRICTLY as a valid JSON object. 

    You must use this exact schema:
    {{
        "Utility_Problem_Definition": "1-2 sentences defining the exact physical problem.",
        "Severity": "Your assessment of the severity (e.g., Low, Moderate, High, Critical)",
        "Reason": "Your reason for severity",
        "Action_Plan": "A step-by-step plan for the response crew.",
        "Conclusion": "A brief 1-sentence summary of the expected outcome."
    }}
    """

    if image_base64 and image_base64.strip() != "":
        message = HumanMessage(content=[
            {"type": "text", "text": UTILITY_PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
        ])
        response = vision_llm.invoke([message])
        llm_source = "Vision Tool"
    else:
        response = text_llm.invoke([HumanMessage(content=UTILITY_PROMPT)])
        llm_source = "Text Tool"

    try:
        clean_text = response.content.strip().strip("```json").strip("```")
        analysis_data = json.loads(clean_text)
        plan = analysis_data.get("Action_Plan", "Pending detailed utility assessment.")
        severity = analysis_data.get("Severity", "Moderate")
    except json.JSONDecodeError:
        analysis_data = {"error": f"Failed to parse JSON. Raw output: {response.content}"}
        plan = "Manual assessment required. AI failed to generate strict plan."
        severity = "Requires Triage"

    ticket_id = f"UTIL-{str(uuid.uuid4())[:8]}"

    return {
        "messages": [response],
        "ai_analysis": analysis_data, # Saved as a clean dict!
        "department_assigned": "Water & Power Board",
        "priority": f"{severity} (via {llm_source})",
        "deadline": get_sla(severity),
        "current_ticket_id": ticket_id,
        "action_plan": plan,
        "next_node": "AUDITOR"
    }

def public_safety_node(state: CRMState):
    """Handles Traffic Lights, Hazards, and Police matters."""
    location = state.get("location_data", {})
    timestamp = state.get("timestamp", "")
    image_base64 = state.get("image_base64", "")
    citizen_text = state.get("citizen_report_text", "")
    
    PUBLIC_SAFETY_PROMPT = f"""You are the 'Public Safety Manager'.
    Analyze this complaint regarding Traffic, Road Hazards, or Crime.
    Report: "{citizen_text}" | Location: "{location}" | Time: "{timestamp}"
    
    1. Assess the immediate danger to human life or traffic flow.
    2. Draft an emergency response plan. If an image is provided, use it to verify.
    
    CRITICAL INSTRUCTION: You must output your analysis STRICTLY as a valid JSON object. 

    You must use this exact schema:
    {{
        "Safety_Problem_Definition": "1-2 sentences defining the exact physical problem.",
        "Severity": "Your assessment of the severity (e.g., Low, Moderate, High, Critical)",
        "Reason": "Your reason for severity",
        "Action_Plan": "A step-by-step plan for the response crew.",
        "Conclusion": "A brief 1-sentence summary of the expected outcome."
    }}
    """

    if image_base64 and image_base64.strip() != "":
        message = HumanMessage(content=[
            {"type": "text", "text": PUBLIC_SAFETY_PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
        ])
        response = vision_llm.invoke([message])
        llm_source = "Vision Tool"
    else:
        response = text_llm.invoke([HumanMessage(content=PUBLIC_SAFETY_PROMPT)])
        llm_source = "Text Tool"

    try:
        clean_text = response.content.strip().strip("```json").strip("```")
        analysis_data = json.loads(clean_text)
        plan = analysis_data.get("Action_Plan", "Pending safety patrol assessment.")
        severity = analysis_data.get("Severity", "Moderate")
    except json.JSONDecodeError:
        analysis_data = {"error": f"Failed to parse JSON. Raw output: {response.content}"}
        plan = "Manual assessment required. AI failed to generate strict plan."
        severity = "Requires Triage"

    ticket_id = f"SAFE-{str(uuid.uuid4())[:8]}"

    return {
        "messages": [response],
        "ai_analysis": analysis_data, # Saved as a clean dict!
        "department_assigned": "Traffic & Public Safety",
        "priority": f"{severity} (via {llm_source})",
        "deadline": get_sla(severity),
        "current_ticket_id": ticket_id,
        "action_plan": plan,
        "next_node": "AUDITOR"
    }

def environment_node(state: CRMState):
    """Handles Waste Management, Parks, and Fallen Trees."""
    location = state.get("location_data", {})
    timestamp = state.get("timestamp", "")
    image_base64 = state.get("image_base64", "")
    citizen_text = state.get("citizen_report_text", "")
    
    ENVIRONMENT_PROMPT = f"""You are the 'Environment & Sanitation Manager'.
    Analyze this complaint regarding Garbage, Parks, or Fallen Trees.
    Report: "{citizen_text}" | Location: "{location}" | Time: "{timestamp}"
    
    1. Assess the environmental impact or cleanup requirement.
    2. Draft a remediation plan. If an image is provided, use it to verify.
    
    CRITICAL INSTRUCTION: You must output your analysis STRICTLY as a valid JSON object. 

    You must use this exact schema:
    {{
        "Environmental_Problem_Definition": "1-2 sentences defining the exact physical problem.",
        "Severity": "Your assessment of the severity (e.g., Low, Moderate, High, Critical)",
        "Reason": "Your reason for severity",
        "Action_Plan": "A step-by-step plan for the response crew.",
        "Conclusion": "A brief 1-sentence summary of the expected outcome."
    }}
    """

    if image_base64 and image_base64.strip() != "":
        message = HumanMessage(content=[
            {"type": "text", "text": ENVIRONMENT_PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
        ])
        response = vision_llm.invoke([message])
        llm_source = "Vision Tool"
    else:
        response = text_llm.invoke([HumanMessage(content=ENVIRONMENT_PROMPT)])
        llm_source = "Text Tool"

    try:
        clean_text = response.content.strip().strip("```json").strip("```")
        analysis_data = json.loads(clean_text)
        plan = analysis_data.get("Action_Plan", "Pending sanitation assessment.")
        severity = analysis_data.get("Severity", "Moderate")
    except json.JSONDecodeError:
        analysis_data = {"error": f"Failed to parse JSON. Raw output: {response.content}"}
        plan = "Manual assessment required. AI failed to generate strict plan."
        severity = "Requires Triage"

    ticket_id = f"ENVR-{str(uuid.uuid4())[:8]}"

    return {
        "messages": [response],
        "ai_analysis": analysis_data, # Saved as a clean dict!
        "department_assigned": "Sanitation & Parks",
        "priority": f"{severity} (via {llm_source})",
        "deadline": get_sla(severity),
        "current_ticket_id": ticket_id,
        "action_plan": plan,
        "next_node": "AUDITOR"
    }

# Define the Auditor Agent (Quality Control / SLA Check)
def auditor_node(state: CRMState):
    """Quality control check. Approves or Rejects tickets."""
    
    citizen_text = state.get("citizen_report_text", "")
    proposed_dept = state.get("department_assigned", "Unknown")
    proposed_priority = state.get("priority", "Unknown")
    action_plan = state.get("action_plan", "Unknown")
    human_update = state.get("latest_human_update", "") # Grab the crew note!
    
    # DYNAMIC CONTEXT: Make sure the Auditor knows the timeline!
    if human_update:
        context_block = f"""
        --- STATUS: POST-WORK REVIEW ---
        Original Complaint: "{citizen_text}"
        LATEST FIELD CREW NOTE: "{human_update}"
        
        Context: The original issue was handled. You are auditing the NEXT step based purely on the FIELD CREW NOTE.
        """
    else:
        context_block = f"""
        --- STATUS: NEW TICKET TRIAGE ---
        Original Complaint: "{citizen_text}"
        """

    AUDITOR_PROMPT = f"""You are the 'City Operations Auditor' (QA Manager).
    Review the proposed ticket assignment for accuracy.
    
    {context_block}
    
    Proposed Department: "{proposed_dept}"
    Proposed Priority: "{proposed_priority}"
    Proposed Action Plan: "{action_plan}"
    
    Rules:
    1. Verify the department matches the CURRENT physical problem that needs solving.
    2. If the department is WRONG, you must REJECT the ticket. 
    
    CRITICAL INSTRUCTION: Output STRICTLY as a valid JSON object.
    
    {{
        "Status": "APPROVED or REJECTED",
        "Feedback": "If REJECTED, explain why and state which department the Orchestrator SHOULD route this to. If APPROVED, write 'None'."
    }}
    """
    
    message = HumanMessage(content=AUDITOR_PROMPT)
    response = text_llm.invoke([message])
    
    try:
        clean_text = response.content.strip().strip("```json").strip("```")
        audit_data = json.loads(clean_text)
        
        status = audit_data.get("Status", "APPROVED").upper()
        feedback = audit_data.get("Feedback", "")
        
    except json.JSONDecodeError:
        status = "APPROVED"
        feedback = "JSON Parse Error in Auditor."

    if status == "REJECTED":
        return {
            "messages": [response],
            "auditor_compliance_log": "REJECTED", 
            "auditor_feedback": feedback
        }
    else:
        # THE LEDGER APPEND
        finished_ticket_record = {
            "ticket_id": state.get("current_ticket_id"),
            "department": proposed_dept,
            "priority": proposed_priority,
            "deadline": state.get("deadline"),
            "action_plan": action_plan,
            "ai_logic": state.get("ai_analysis"), 
            "human_notes_that_triggered_this": state.get("latest_human_update", "Initial Report")
        }
        
        return {
            "messages": [response],
            "auditor_compliance_log": "APPROVED",
            "auditor_feedback": "",
            "ticket_history": [finished_ticket_record], 
            "next_node": END 
        }

# Initialize StateGraph and Add Nodes (The Managers Layer)
workflow = StateGraph(CRMState)

workflow.add_node("ORCHESTRATOR", orchestrator_node)
workflow.add_node("INFRASTRUCTURE", infrastructure_node)
workflow.add_node("UTILITY", utility_node)
workflow.add_node("PUBLIC_SAFETY", public_safety_node)
workflow.add_node("ENVIRONMENT", environment_node)
workflow.add_node("AUDITOR", auditor_node)

# Define Routing Edges (Conditional Edge for Orchestrator)
def router_logic(state: CRMState):
    """Conditional Edge - returns next node name to travel to."""
    return state.get("next_node", END)

# starting point
workflow.set_entry_point("ORCHESTRATOR")

# dynamic routing from orchestrator based on thought process
workflow.add_conditional_edges(
    "ORCHESTRATOR", 
    router_logic,
    {
        "INFRASTRUCTURE": "INFRASTRUCTURE",
        "UTILITY": "UTILITY",
        "PUBLIC_SAFETY": "PUBLIC_SAFETY",
        "ENVIRONMENT": "ENVIRONMENT",
        END: END
    }
)

# default routing for specialized agents (always go to auditor)
workflow.add_edge("INFRASTRUCTURE", "AUDITOR")
workflow.add_edge("UTILITY", "AUDITOR")
workflow.add_edge("PUBLIC_SAFETY", "AUDITOR")
workflow.add_edge("ENVIRONMENT", "AUDITOR")

def auditor_router_logic(state: CRMState):
    """Checks if the auditor approved or rejected the ticket."""
    status_log = state.get("auditor_compliance_log", "")
    
    if status_log == "REJECTED":
        print("🚨 LOOP TRIGGERED: Auditor rejected ticket, sending back to Orchestrator!")
        return "ORCHESTRATOR"
    else:
        return END

# Conditional edge for passed or rejected analysis
workflow.add_conditional_edges(
    "AUDITOR",
    auditor_router_logic,
    {
        "ORCHESTRATOR": "ORCHESTRATOR",
        END: END
    }
)

# --- NEW: ADDING THE SQLITE MEMORY ---
# 1. Connect to a local file called 'prototype_memory.sqlite'
# (check_same_thread=False is needed for web servers like FastAPI)
conn = sqlite3.connect("prototype_memory.sqlite", check_same_thread=False)
memory = SqliteSaver(conn)

# 2. Compile the expanded multi-agent graph with memory!
crm_app = workflow.compile(checkpointer=memory)