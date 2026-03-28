def auditor_node(state: CRMState):
    """Quality control check. Approves or Rejects tickets."""
    
    citizen_text = state.get("citizen_report_text", "")
    proposed_dept = state.get("department_assigned", "Unknown")
    proposed_priority = state.get("priority", "Unknown")
    action_plan = state.get("action_plan", "Unknown")
    human_update = state.get("latest_human_update", "")
    
    # 1. BULLETPROOF CONTEXT FOR SMALL MODELS
    if human_update:
        context_block = f"""
        --- STATUS: POST-WORK REVIEW ---
        Original Complaint: "{citizen_text}" (IGNORE THIS. IT IS ALREADY FIXED.)
        LATEST FIELD CREW NOTE: "{human_update}" (FOCUS ONLY ON THIS!)
        
        Context: The original issue is resolved. You are auditing the NEW department assigned to handle the FIELD CREW NOTE.
        """
    else:
        context_block = f"""
        --- STATUS: NEW TICKET TRIAGE ---
        Original Complaint: "{citizen_text}"
        """

    # 2. THE LENIENT PROMPT
    AUDITOR_PROMPT = f"""You are the 'City Operations Auditor'.
    Review the proposed ticket assignment.
    
    {context_block}
    
    Proposed Department: "{proposed_dept}"
    Proposed Action Plan: "{action_plan}"
    
    CRITICAL RULES:
    1. Does the Proposed Department make logical sense for the current problem?
    2. You must heavily bias towards "APPROVED". ONLY reject if it is a massive, obvious mistake (like sending Police to fix a pipe).
    
    Output STRICTLY as a valid JSON object:
    {{
        "Status": "APPROVED or REJECTED",
        "Feedback": "If REJECTED, explain why. If APPROVED, write 'None'."
    }}
    """
    
    message = HumanMessage(content=AUDITOR_PROMPT)
    response = text_llm.invoke([message])
    
    # 3. BULLETPROOF JSON PARSER
    try:
        clean_text = response.content.strip().strip("```json").strip("```")
        # Extra safety just in case the AI adds filler text outside the JSON brackets
        if "{" in clean_text and "}" in clean_text:
            clean_text = clean_text[clean_text.find("{"):clean_text.rfind("}")+1]
            
        audit_data = json.loads(clean_text)
        status = audit_data.get("Status", "APPROVED").upper()
        feedback = audit_data.get("Feedback", "")
        
    except json.JSONDecodeError:
        # Failsafe for the live demo!
        status = "APPROVED"
        feedback = "JSON Parse Error. Auto-approving to prevent system crash."

    # 4. TERMINAL DEBUGGING & ROUTING
    if status == "REJECTED":
        # THIS WILL TELL YOU EXACTLY WHY IT IS MAD!
        print(f"\n🚨 AUDITOR REJECTED! Reason given by AI: {feedback}\n")
        return {
            "messages": [response],
            "auditor_compliance_log": "REJECTED", 
            "auditor_feedback": feedback
        }
    else:
        print(f"\n✅ AUDITOR APPROVED the ticket for {proposed_dept}!\n")
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
    





    # 3. The Master Prompt
    ORCHESTRATOR_PROMPT = f"""You are the 'City CRM Orchestrator Agent' (The Brain). 
    
    {context_block}

    ROUTING OPTIONS:
    - INFRASTRUCTURE: Roads, Bridges, Sidewalks, or Potholes.
    - UTILITY: Water supply, Electricity leakage, Sewerage, or Power lines.
    - PUBLIC_SAFETY: Traffic, Police emergencies, or Hazardous obstructions.
    - ENVIRONMENT: Waste management, Garbage, Sanitation, Parks, or Trees.
    - END: Use this ONLY if there is a 'Human Crew Field Note' stating the problem is 100% resolved.

    CRITICAL TRIAGE RULE:
    If a report contains multiple issues (e.g., a burst water pipe that destroys a road), you MUST route to the department that handles the ACTIVE HAZARD or ROOT CAUSE first. 
    (Example: Route to UTILITY to shut off the water BEFORE routing to INFRASTRUCTURE to fix the road).

    CRITICAL INSTRUCTION: You must output your decision STRICTLY as a valid JSON object.
    Do not try to solve the problem yourself. Your only job is to provide the 'next_node' for routing.
    
    You must use this exact schema:
    {{
        "next_node": "UTILITY" 
    }}
    """




    # Set the thread ID AND a hard limit of 10 steps so it never loops infinitely
    config = {
        "configurable": {"thread_id": master_complaint_id},
        "recursion_limit": 10
    }