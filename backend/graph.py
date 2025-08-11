# /graph.py
import requests
import json
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Import from our other modules
from datamodels import AgentState, EmailDraft
from config import CRM_API_KEY, CRM_API_URL, LLM_MODEL
from prompt import EMAIL_GENERATION_PROMPT

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
        print(f"Executing query: {user_query}")
        user_payload = {"query": user_query}
        user_response = requests.post(CRM_API_URL, headers=headers, data=json.dumps(user_payload))
        
        user_data = user_response.json()

        user_records = user_data["result"]["data"]
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
        partner_payload = {"query": partner_query}
        partner_response = requests.post(CRM_API_URL, headers=headers, data=json.dumps(partner_payload))
        partner_response.raise_for_status()
        partner_json = partner_response.json()
        partner_records = partner_json.get("result", {}).get("data", [])
        if not partner_records:
            return {**state, "error_message": f"No partner contact found for partner_id: {partner_id}"}
        db_data["res_partner"] = partner_records[0]

        # 3. Fetch Organization
        print(f"Fetching organization_organization for company_id: {company_id}")
        org_query = f"SELECT * FROM organization_organization WHERE company_id = {company_id};"
        org_payload = {"query": org_query}
        org_response = requests.post(CRM_API_URL, headers=headers, data=json.dumps(org_payload))
        org_json = org_response.json()
        org_records = org_json.get("result", {}).get("data", [])
        if not org_records:
            return {**state,"error_message": f"No organization found for company_id: {company_id}"}
        db_data["organization"] = org_records[0]

        # 4. Fetch Lead to get stage_id
        print(f"Fetching crm_lead for id: {lead_id}")
        lead_query = f"SELECT * FROM crm_lead WHERE id = {lead_id};"
        lead_payload = {"query": lead_query}
        lead_response = requests.post(CRM_API_URL, headers=headers, data=json.dumps(lead_payload))
        lead_response.raise_for_status()
        lead_json = lead_response.json()
        lead_records = lead_json.get("result", {}).get("data", [])
        if not lead_records:
            return {**state,"error_message": f"No lead found for lead_id: {lead_id}"}
        db_data["crm_lead"] = lead_records[0]

        # 5. Fetch Stage using stage_id from the lead
        stage_id = db_data["crm_lead"].get("stage_id")
        if stage_id:
            print(f"Fetching crm_stage for id: {stage_id}")
            stage_query = f"SELECT * FROM crm_stage WHERE id = {stage_id};"
            stage_payload = {"query": stage_query}
            stage_response = requests.post(CRM_API_URL, headers=headers, data=json.dumps(stage_payload))
            stage_response.raise_for_status()
            stage_json = stage_response.json()
            stage_records = stage_json.get("result", {}).get("data", [])
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
    """
    Generates a personalized email draft based on CRM data and any user feedback.
    """
    print("--- GENERATING EMAIL DRAFT ---")

    # 1. Unpack the required data from the current state
    db_data = state.get("db_data")
    user_instructions = state.get("user_instructions", "No specific instructions provided.")
    feedback = state.get("feedback")
    email_history = state.get("email_history", [])

    # 2. Construct the feedback section for the prompt
    feedback_section = ""
    if feedback and email_history:
        previous_draft = email_history[-1]
        feedback_section = f"""
        **IMPORTANT HUMAN FEEDBACK ON THE PREVIOUS DRAFT:**
        A human reviewed the last draft you generated and provided this feedback. 
        You MUST apply these changes to generate a new, improved version.

        PREVIOUS DRAFT:
        ---
        Subject: {previous_draft.subject}
        Body: {previous_draft.body}
        ---

        REQUIRED CHANGES: "{feedback}"
        """

    # 3. Set up the LangChain components
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0.5)
    structured_llm = llm.with_structured_output(EmailDraft)
    prompt = ChatPromptTemplate.from_template(EMAIL_GENERATION_PROMPT)
    generation_chain = prompt | structured_llm

    # 4. Invoke the generation chain with all the necessary data
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
    
    # 5. Update the state for the next step in the graph
    new_history = email_history + [email_draft]
    return {
        **state,
        "email_history": new_history,
        "feedback": None,  # Clear feedback after it has been used
        "human_decision": "",  # Clear the human decision
    }
def route_human_choice(state: AgentState) -> Literal["generate_email", "end_process"]:
    """Node to decide the next step based on human input."""
    print(f"--- ROUTING HUMAN DECISION: {state.get('human_decision')} ---")
    if state.get("human_decision") == "regenerate":
        return "generate_email"
    else: # approve
        return "end_process"

def save_approved_email(state: AgentState):
    """node for saving the approved email."""
    print("--- SAVING APPROVED EMAIL ---")
    approved_email = state.get("email_history", [])[-1]
    print(f"Subject: {approved_email.subject}")
    print(f"Body: {approved_email.body}")
    # TODO: save this is in database
    print("--- PROCESS COMPLETE ---")
    return {}


# --- Graph Definition ---

checkpointer = MemorySaver()
workflow = StateGraph(AgentState)

workflow.add_node("fetch_data", fetch_database_info)
workflow.add_node("generate_email", generate_email_draft)
workflow.add_node("end_process", save_approved_email)
workflow.add_edge("fetch_data", "generate_email")
workflow.add_conditional_edges(
    "generate_email",
    route_human_choice,
    {
        "generate_email": "generate_email",
        "end_process": "end_process",
    }
)
workflow.add_edge("end_process", END)
workflow.set_entry_point("fetch_data")

# By adding an interrupt, the graph will pause at the 'generate_email' node
# AFTER it has executed, waiting for us to resume it.
app_graph = workflow.compile(checkpointer=checkpointer, interrupt_after=["generate_email"])