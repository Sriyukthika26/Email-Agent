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
from projectsfetch import fetch_projects

def filter_id_fields(data: dict) -> dict:
    """Removes keys from a dictionary that end with 'id'."""
    if not isinstance(data, dict):
        return data
    return {k: v for k, v in data.items() if not k.endswith('id')}

# --- Graph Nodes (The "workers" of our agent) ---

def fetch_database_info(state: AgentState) -> AgentState:
    """
    Node to fetch specific, required data from the CRM to build the email context.
    """
    print("--- FETCHING DATABASE INFO ---")

    lead_id = state.get("lead_id")
    user_id = state.get("user_id")

    try:
        db_data = {}
        # 1. Fetch only company_id and partner_id from res_users
        print(f"Fetching IDs from res_users for id: {user_id}")
        user_query = f"SELECT company_id, partner_id FROM res_users WHERE id = {user_id};"
        user_records = datafetch(user_query)

        if not user_records:
            return {**state, "error_message": f"No user found for user_id: {user_id}"}
        
        user_record = user_records[0]
        company_id = user_record.get("company_id")
        partner_id = user_record.get("partner_id")
        
        if not company_id or not partner_id:
            return {**state, "error_message": f"Missing company_id or partner_id for user: {user_id}"}

        # 2. Fetch User's Partner record (Contact Details)
        print(f"Fetching res_partner for id: {partner_id}")
        partner_query = f"""
            SELECT 
                name, title, complete_name, ref, tz, vat, company_registry, 
                website, function, type, street, street2, zip, city, email, 
                phone, mobile, commercial_company_name, company_name, barcode, 
                comment, active, employee, contact_address_complete, 
                email_normalized, street_name, street_number, street_number2
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
            return {**state, "error_message": f"No organization found for company_id: {company_id}"}
        db_data["organization"] = filter_id_fields(org_records[0])

        # 4. Fetch Lead to get stage_id
        print(f"Fetching crm_lead for id: {lead_id}")

        lead_query = f"""
            SELECT 
                name, address, city, region, project_class, project_status, project_type, project_description, builder_name,
                builder_email, owner_company, owner_phone, owner_name, owner_email, applicant_name, applicant_company, applicant_phone, applicant_email, 
                contact_name, partner_name, email_from,email_domain_criterion, email_cc, type, priority, phone, mobile, website, street, street2, zip, city, date_deadline,
                lead_properties, description, expected_revenue, prorated_revenue, recurring_revenue, recurring_revenue_monthly, recurring_revenue_monthly_prorated, 
                recurring_revenue_prorated, day_open, day_close, probability, automated_probability, won_status, days_to_convert, days_exceeding_closing, 
                month_started, permit_issue_date, cost_of_construction, additional_info, project_year, is_lead_lost, lost_feedback, stage_id  
            FROM crm_lead WHERE id = {lead_id};
        """

        lead_records = datafetch(lead_query)
        if not lead_records:
            return {**state, "error_message": f"No lead found for lead_id: {lead_id}"}
        
        stage_id  = lead_records[0].get("stage_id")
        db_data["crm_lead"] = lead_records[0]

        # 5. Fetch only name and requirements from crm_stage
        
        if stage_id:
            print(f"Fetching specific fields from crm_stage for id: {stage_id}")
            stage_query = f"SELECT name, requirements FROM crm_stage WHERE id = {stage_id};"
            stage_records = datafetch(stage_query)
            if stage_records:
                db_data["crm_stage"] = stage_records[0]
            else:
                db_data["crm_stage"] = None
                print(f"Warning: No stage found for stage_id: {stage_id}")
        else:
            db_data["crm_stage"] = None
            print("Warning: No stage_id found on the lead record.")

        # 6. Conditional Fetch Logic
        # First, check the latest message for the lead
        latest_message_query = f"SELECT parent_id FROM mail_message WHERE model = 'crm.lead' AND res_id = {lead_id} ORDER BY date DESC LIMIT 1;"
        latest_message = datafetch(latest_message_query)

        # If there's no message or the parent_id is null, it's a new lead.
        if not latest_message or not latest_message[0].get("parent_id"):
            print(f"New lead detected. Fetching past projects for company_id: {company_id}")
            past_projects_data = fetch_projects(company_id=company_id, limit=20)
            raw_projects = past_projects_data.get("data", {}).get("projects", []) if past_projects_data else []
            essential_projects = []
            if raw_projects:
                for project in raw_projects:
                    essential_info = {
                        "projectName": project.get("projectName"),
                        "serviceType": project.get("serviceType"),
                        "projectType": project.get("projectType"),
                        "builderName": project.get("builderName"),
                        "builderEmail": project.get("builderEmail"),
                        "projectAddress": project.get("projectAddress"), # Will be None if not present
                        "city": project.get("city"),
                        "country": project.get("country"),
                        "region": project.get("region")
                    }
                    essential_projects.append(essential_info)
            
            db_data["past_projects"] = essential_projects
            db_data["conversation_history"] = []

        else:
            # It's an existing conversation. Fetch the history.
            print(f"Existing lead detected. Fetching conversation history for lead_id: {lead_id}")
            history_query = f"""
                SELECT id, parent_id, email_from, subject, body, date
                FROM mail_message
                WHERE model = 'crm.lead' AND res_id = {lead_id} AND subtype_id = 1 AND message_type = 'comment'
                ORDER BY date DESC
                LIMIT 5;
            """
            conversation_records = datafetch(history_query)
            db_data["conversation_history"] = conversation_records if conversation_records else []
            db_data["past_projects"] = [] # Ensure projects are empty

        return {"db_data": db_data, "error_message": None}

    except Exception as e:
        error_type = type(e).__name__
        print(f"An unexpected error occurred in fetch_database_info: {error_type} - {e}")
        return {"db_data": None, "error_message": f"An unexpected error occurred ({error_type}): {e}"}

def generate_email_draft(state: AgentState) -> AgentState:
    """Generates a personalized email draft based on CRM data and any user feedback."""
    print("--- (RUNNING) GENERATING EMAIL DRAFT ---")

    if state.get("db_data") is None:
        print("--- ERROR: db_data is missing, cannot generate email. ---")
        return {"error_message": state.get("error_message", "Unknown error: db_data was not found.")}

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

    # Dynamically build the context section with explicit instructions
    context_section = ""
    conversation_history = db_data.get("conversation_history", [])
    past_projects = db_data.get("past_projects", [])

    if conversation_history:
        history_json = json.dumps(conversation_history, indent=2)
        context_section = f"""**Instruction:** Review the following conversation history (in JSON format) to draft a logical next-step email. The `id` and `parent_id` fields show the reply chain. Avoid repetition.
        **Previous Conversation History:**
        ```json
            {history_json}
        ```"""
    elif past_projects:
        context_section = f"""**Instruction:** This is the first email to this lead. To build credibility, subtly reference 1-2 relevant project from the list below.For instance, if the lead's project is residential, mention a similar residential project the company has completed.
        **Company's Past Projects (for reference):**
        {past_projects}"""

    llm = ChatOpenAI(model=LLM_MODEL, temperature=0.5)
    structured_llm = llm.with_structured_output(EmailDraft)
    prompt = ChatPromptTemplate.from_template(EMAIL_GENERATION_PROMPT)
    generation_chain = prompt | structured_llm
    
    email_draft = generation_chain.invoke({
        "lead_data": json.dumps(db_data.get("crm_lead")),
        "partner_data": json.dumps(db_data.get("res_partner")),
        "org_data": json.dumps(db_data.get("organization")),
        "stage_requirements": db_data.get("crm_stage", {}).get("requirements", "Unknown"),
        "stage_name": db_data.get("crm_stage", {}).get("name", "Unknown"),
        "user_instructions": user_instructions,
        "feedback_section": feedback_section,
        "context_section": context_section,
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
