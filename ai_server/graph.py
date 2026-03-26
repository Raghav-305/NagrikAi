from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import json
import uuid
from state import CRMState

# text model
text_llm = ChatGroq(temperature=0, model_name="llama-3.1-8b-instant")

# Vision model
vision_llm = ChatGroq(temperature=0, model_name="meta-llama/llama-4-scout-17b-16e-instruct")

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
    """The brain that routes the complaint."""
    text = state.get("citizen_report_text", "")
    location = state.get("location_data", {})
    timestamp = state.get("timestamp", "")
    
    # Check if the Auditor kicked this back
    feedback = state.get("auditor_feedback", "")
    feedback_text = f"\nAUDITOR REJECTION FEEDBACK: {feedback}\nDo not route to the rejected department again!" if feedback else ""

    ORCHESTRATOR_PROMPT = f"""You are the 'City CRM Orchestrator Agent' (The Brain). 
    Your responsibility is to analyze the raw citizen input (Multi-modal Text, Image Analysis, and GPS data) 
    and route it to the CORRECT Specialized Manager Agent.

    Citizen Report Text: "{text}"
    GPS Location: "{location}"
    Submitted Time: "{timestamp}"
    {feedback_text}

    Based on this input, decide which specialized agent needs to handle this:
    - INFRASTRUCTURE: Use for problems with Roads, Bridges, Sidewalks, or Potholes.
    - UTILITY: Use for problems with Water supply, Electricity leakage, Sewerage, or Power lines.
    - PUBLIC_SAFETY: Use for problems with Traffic, Police emergencies, or Hazardous obstructions.
    - ENVIRONMENT: Use for problems with Waste management, Garbage, Sanitation, Parks, or Trees.

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
        # 1. Strip standard markdown
        clean_text = response.content.strip().strip("```json").strip("```")
        
        # 2. Extract ONLY the JSON block if the LLM still added filler text
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
    Do not include conversational filler, introductory text like 'Here is the analysis', or markdown formatting like ```json. 

    You must use this exact schema:
    {{
        "Infrastructure_Problem_Definition": "1-2 sentences defining the exact physical problem.",
        "Severity": "Your assessment of the severity (e.g., Low, Moderate, High, Critical)",
        "Reason": "Your reason for severity",
        "Action_Plan": "A step-by-step plan for the response crew.",
        "Conclusion": "A brief 1-sentence summary of the expected outcome."
    }}
    """

    # Invoke LLM
    if image_base64 and image_base64.strip() != "":
        # MULTI-MODAL PATH
        message = HumanMessage(
            content=[
                {"type": "text", "text": INFRASTRUCTURE_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]
        )
        response = vision_llm.invoke([message])
        llm_source = "Vision Tool"
    else:
        # TEXT-ONLY PATH
        message = HumanMessage(content=INFRASTRUCTURE_PROMPT)
        response = text_llm.invoke([message])
        llm_source = "Text Tool"

    # JSON parser
    try:
        clean_text = response.content.strip().strip("```json").strip("```")
        analysis_data = json.loads(clean_text)
        plan = analysis_data.get("Action_Plan", "Pending detailed assessment.")
        severity = analysis_data.get("Severity", "Moderate")
        
        formatted_analysis = json.dumps(analysis_data, indent=2)

    except json.JSONDecodeError:
        # Fallback if the AI hallucinates bad JSON
        formatted_analysis = f"Failed to parse JSON. Raw output: {response.content}"
        plan = "Manual assessment required. AI failed to generate strict plan."
        severity = "Requires Triage"

    # Generate the final ticket details using the AI's actual data!
    ticket_id = f"INFR-{str(uuid.uuid4())[:8]}"
    
    return {
        "messages": [response], 
        "infrastructure_analysis": formatted_analysis,
        "thought_process": formatted_analysis,
        "final_department_assigned": "Roads & Bridges PWD",
        "final_priority": f"{severity} (via {llm_source})",
        "deadline": get_sla(severity),
        "ticket_id": ticket_id,
        "action_taken": plan,
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
    Do not include conversational filler or markdown formatting like ```json. 

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
        formatted_analysis = json.dumps(analysis_data, indent=2)
    except json.JSONDecodeError:
        formatted_analysis = f"Failed to parse JSON. Raw output: {response.content}"
        plan = "Manual assessment required. AI failed to generate strict plan."
        severity = "Requires Triage"

    ticket_id = f"UTIL-{str(uuid.uuid4())[:8]}"

    return {
        "messages": [response],
        "utility_analysis": formatted_analysis,
        "thought_process": formatted_analysis,
        "final_department_assigned": "Water & Power Board",
        "final_priority": f"{severity} (via {llm_source})",
        "deadline": get_sla(severity),
        "ticket_id": ticket_id,
        "action_taken": plan,
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
    Do not include conversational filler or markdown formatting like ```json. 

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
        formatted_analysis = json.dumps(analysis_data, indent=2)
    except json.JSONDecodeError:
        formatted_analysis = f"Failed to parse JSON. Raw output: {response.content}"
        plan = "Manual assessment required. AI failed to generate strict plan."
        severity = "Requires Triage"

    ticket_id = f"SAFE-{str(uuid.uuid4())[:8]}"

    return {
        "messages": [response], 
        "public_safety_analysis": formatted_analysis,
        "thought_process": formatted_analysis,
        "final_department_assigned": "Traffic & Public Safety",
        "final_priority": f"{severity} (via {llm_source})",
        "deadline": get_sla(severity),
        "ticket_id": ticket_id,
        "action_taken": plan,
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
    Do not include conversational filler or markdown formatting like ```json. 

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
        formatted_analysis = json.dumps(analysis_data, indent=2)
    except json.JSONDecodeError:
        formatted_analysis = f"Failed to parse JSON. Raw output: {response.content}"
        plan = "Manual assessment required. AI failed to generate strict plan."
        severity = "Requires Triage"

    ticket_id = f"ENVR-{str(uuid.uuid4())[:8]}"

    return {
        "messages": [response], 
        "environment_analysis": formatted_analysis,
        "thought_process": formatted_analysis,
        "final_department_assigned": "Sanitation & Parks",
        "final_priority": f"{severity} (via {llm_source})",
        "deadline": get_sla(severity),
        "ticket_id": ticket_id,
        "action_taken": plan,
        "next_node": "AUDITOR"
    }

# Define the Auditor Agent (Quality Control / SLA Check)
def auditor_node(state: CRMState):
    """Quality control check. Rejects tickets if routed to the wrong department."""
    
    citizen_text = state.get("citizen_report_text", "")
    proposed_dept = state.get("final_department_assigned", "Unknown")
    proposed_priority = state.get("final_priority", "Unknown")
    action_plan = state.get("action_taken", "Unknown")
    
    AUDITOR_PROMPT = f"""You are the 'City Operations Auditor' (QA Manager).
    Review the proposed ticket assignment for accuracy.
    
    Original Citizen Complaint: "{citizen_text}"
    Proposed Department: "{proposed_dept}"
    Proposed Priority: "{proposed_priority}"
    Proposed Action Plan: "{action_plan}"
    
    Rules:
    1. Verify the department matches the physical problem (e.g., Water leaks go to Utility, not Roads).
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

    # If rejected, we flag the log and save the feedback for the Orchestrator
    if status == "REJECTED":
        return {
            "messages": [response],
            "auditor_compliance_log": "REJECTED", 
            "auditor_feedback": feedback
        }
    else:
        # If approved, we pass it through cleanly
        return {
            "messages": [response],
            "auditor_compliance_log": "APPROVED",
            "auditor_feedback": ""
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

# Compile the expanded multi-agent graph
crm_app = workflow.compile()