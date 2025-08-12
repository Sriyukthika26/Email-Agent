# /graph.py
import requests
import json
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START

# Import from our other modules
from datamodels import AgentState, EmailDraft
from config import CRM_API_KEY, CRM_API_URL, LLM_MODEL
from prompt import EMAIL_GENERATION_PROMPT
from datafetch import datafetch
# --- Graph Nodes (The "workers" of our agent) ---

def fetch_database_info(state: AgentState) -> AgentState:
    """
    Node to fetch the full JSON objects for the lead, its stage, user, 
    and the user's organization.
    """
    print("--- FETCHING DATABASE INFO ---")

    lead_id = state.get("lead_id")
    user_id = state.get("user_id")
    
    headers = { "API-Key": CRM_API_KEY, "Content-Type": "application/json" }

    try:
        db_data = {}
        # 1. Fetch User to get company_id
        print(f"Fetching res_users for id: {user_id}")
        user_query = f"SELECT * FROM res_users WHERE id = {user_id};"
        user_records = datafetch(user_query)

        if not user_records:
            return {**state, "error_message": f"No user found for user_id: {user_id}"}
        
        user_record = user_records[0]
        db_data["res_users"] = user_record
        company_id = user_record.get("company_id")
        partner_id = user_record.get("partner_id")
        if not company_id:
             return {**state,"error_message": f"No company_id found for user_id: {user_id}"}
        
        # 2. Fetch User's Partner record with specific fields
        print(f"Fetching res_partner for id: {partner_id}")
    
        partner_query = f"""
            SELECT 
                create_date, name, title, complete_name, ref, lang, tz, vat, 
                company_registry, website, function, type, street, street2, 
                zip, city, email, phone, mobile, commercial_company_name, 
                company_name, barcode, comment, active, employee, is_company, partner_share,
                contact_address_complete, email_normalized, signup_type, street_name, 
                street_number, street_number2
            FROM res_partner WHERE id = {partner_id};
        """
        partner_records = datafetch(partner_query)

        if not partner_records:
            return {**state, "error_message": f"No partner contact found for partner_id: {partner_id}"}
        db_data["res_partner"] = partner_records[0]

        # 3. Fetch Organization
        print(f"Fetching organization_organization for company_id: {company_id}")
        org_query = f"SELECT * FROM organization_organization WHERE company_id = {company_id};"
        org_records = datafetch(org_query)

        if not org_records:
            return {**state,"error_message": f"No organization found for company_id: {company_id}"}
        db_data["organization"] = org_records[0]

        # 4. Fetch Lead to get stage_id
        print(f"Fetching crm_lead for id: {lead_id}")
        lead_query = f"SELECT * FROM crm_lead WHERE id = {lead_id};"
        lead_records = datafetch(lead_query)

        if not lead_records:
            return {**state,"error_message": f"No lead found for lead_id: {lead_id}"}
        db_data["crm_lead"] = lead_records[0]

        # 5. Fetch Stage using stage_id from the lead
        stage_id = db_data["crm_lead"].get("stage_id")
        if stage_id:
            print(f"Fetching crm_stage for id: {stage_id}")
            stage_query = f"SELECT * FROM crm_stage WHERE id = {stage_id};"
            stage_records = datafetch(stage_query)

            if stage_records:
                db_data["crm_stage"] = stage_records[0]
            else:
                db_data["crm_stage"] = None
                print(f"Warning: No stage found for stage_id: {stage_id}")
        else:
            db_data["crm_stage"] = None
            print("Warning: No stage_id found on the lead record.")

        return {**state,"db_data": db_data, "error_message": None}

    except requests.exceptions.RequestException as e:
        print(f"Error calling CRM API: {e}")
        error_details = e.response.text if e.response else "No response body"
        print(f"Error details: {error_details}")
        return {**state,"error_message": f"API request failed: {e} - {error_details}"}
    except Exception as e:
        error_type = type(e).__name__
        print(f"An unexpected error occurred: {error_type} - {e}")
        return {**state,"error_message": f"An unexpected error occurred ({error_type}): {e}"}
    

def generate_email_draft(state: AgentState) -> AgentState:
    """Generates a personalized email draft based on CRM data and any user feedback."""
    print("--- (RUNNING) GENERATING EMAIL DRAFT ---")
    db_data = state["db_data"]
    feedback = state.get("feedback")
    email_history = state.get("email_history", [])
    user_instructions = state.get("user_instructions", "No specific instructions provided.")

    feedback_section = ""
    if feedback and email_history:
        previous_draft = email_history[-1]
        feedback_section = f"""
        **IMPORTANT HUMAN FEEDBACK ON THE PREVIOUS DRAFT:**
        A human reviewed the last draft and provided this feedback. You MUST apply these changes.
        PREVIOUS DRAFT:
        ---
        Subject: {previous_draft.subject}
        Body: {previous_draft.body}
        ---
        REQUIRED CHANGES: "{feedback}"
        """
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0.5)
    structured_llm = llm.with_structured_output(EmailDraft)
    prompt = ChatPromptTemplate.from_template(EMAIL_GENERATION_PROMPT)
    generation_chain = prompt | structured_llm
    
    email_draft = generation_chain.invoke({
        "lead_data": json.dumps(db_data.get("crm_lead")),
        "partner_data": json.dumps(db_data.get("res_partner")),
        "user_data": json.dumps(db_data.get("res_users")),
        "org_data": json.dumps(db_data.get("organization")),
        "stage_data": json.dumps(db_data.get("crm_stage", {"name": "Unknown"})),
        "stage_name": db_data.get("crm_stage", {}).get("name", "Unknown"),
        "user_instructions": user_instructions,
        "feedback_section": feedback_section,
    })
    
    new_history = email_history + [email_draft]
    return {"email_history": new_history, "feedback": None, "human_decision": None}


def save_approved_email(state: AgentState):
    """A placeholder node for saving the approved email."""
    print("--- (RUNNING) SAVING APPROVED EMAIL ---")
    approved_email = state.get("email_history", [])[-1]
    print(f"Final Approved Email Subject: {approved_email.subject}")
    # In a real application, you would save this to a database.
    return {}

# --- Master Router ---

def route_action(state: AgentState) -> Literal["fetch_data", "generate_email", "end_process"]:
    """The main router. It decides the next action based on the human's decision or the state."""
    print("--- (ROUTING) DECIDING NEXT ACTION ---")
    
    if state.get("human_decision") == "regenerate":
        print("--- Decision: Regenerate. Routing to generate_email. ---")
        return "generate_email"
    
    if state.get("human_decision") == "approve":
        print("--- Decision: Approve. Routing to end_process. ---")
        return "end_process"
    
    # If no decision, it's the first run. Check if data exists.
    if state.get("db_data"):
         print("--- Data found. Routing to generate_email. ---")
         return "generate_email"
    else:
        print("--- No data found. Routing to fetch_data. ---")
        return "fetch_data"

# --- Graph Definition ---

workflow = StateGraph(AgentState)

# Add all the worker nodes to the graph
workflow.add_node("fetch_data", fetch_database_info)
workflow.add_node("generate_email", generate_email_draft)
workflow.add_node("end_process", save_approved_email)

workflow.set_conditional_entry_point(
    route_action,
    {
        "fetch_data": "fetch_data",
        "generate_email": "generate_email",
        "end_process": "end_process",
    }
)

workflow.add_edge("fetch_data", "generate_email")
workflow.add_edge("end_process", END)

# After 'generate_email', the graph will pause (due to interrupt_after in main.py).
# The next invocation will start over at the conditional entry point.
