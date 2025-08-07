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
        # OPTIMIZATION: Select only the necessary fields from res_partner
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
    """Node to generate a personalized, stage-aware email by interpreting full JSON objects."""
    print("--- GENERATING EMAIL DRAFT ---")
    db_data = state.get("db_data")
    feedback = state.get("feedback")
    email_history = state.get("email_history", [])

    llm = ChatOpenAI(model=LLM_MODEL, temperature=0.5)
    structured_llm = llm.with_structured_output(EmailDraft)

    sales_stages = """
    - New: Initial point of contact. Goal is to qualify the lead.
    - Contacted: First contact has been made. Goal is to get a response and confirm needs.
    - Qualified: The lead is a good fit. Goal is to present a solution or send a quote.
    - Quote Sent: A formal quote has been delivered. Goal is to follow up and enter negotiation.
    - Negotiation: Discussing terms, pricing, etc. Goal is to reach an agreement and get confirmation.
    - Order Confirmed: The lead has agreed to the deal. Goal is to begin the delivery process.
    - Delivered: The product/service has been delivered. Goal is to ensure satisfaction.
    - Closed - Won: The deal is successfully completed and paid.
    - Closed - Lost: The lead is no longer a viable opportunity.
    """

    prompt_template = """
    You are a world-class sales strategist and copywriter. Your task is to draft a strategic, personalized email to advance a lead to the next stage of the sales process, based on raw CRM data.

    **The Sales Process Funnel:**
    {sales_stages}

    **CRM Data Objects:**
    1.  **Lead Data (`crm_lead`):** {lead_data}
    2.  **Sender's Contact Details (`res_partner`):** {partner_data}
    3.  **Sender's Company Data (`organization_organization`):** {org_data}
    4.  **Lead's Current Stage Data (`crm_stage`):** {stage_data}
    5.  **Sender's User Account (`res_users`):** {user_data}

    **Chain of Thought - Follow these steps before writing:**
    1.  **Identify Sender:** Who is sending this email? Use the `name` and `email` from the `res_partner` object. This is the most reliable source.
    2.  **Identify Recipient:** Who is the email for? Use `applicant_name` and `applicant_email` from the `crm_lead` object as the primary contact.
    3.  **Analyze Current Position:** What is the lead's current stage? Look at the `name` field in the `crm_stage` object.
    4.  **Define the Goal:** Based on the current stage, what is the single most important next step? Refer to the Sales Process Funnel. For example, if the current stage is "Qualified," the goal is to move to "Quote Sent."
    5.  **Synthesize Key Information:**
        - What is the lead's specific need? (from `crm_lead.project_description`).
        - What is the sender's relevant solution? (from `organization_organization.service_offered`).
    6.  **Strategize the Message:** How can I craft a message that directly addresses the lead's need with the company's solution to achieve the goal defined in step 4? The message must be concise, valuable, and have a clear call-to-action.

    **Primary Goal & Email Drafting Instructions:**
    The lead's current stage is **"{stage_name}"**. Your email's primary purpose is to move them to the NEXT logical stage.

    - **If Stage is "New" or "Contacted":** Your goal is to qualify them. The email should be a friendly introduction that references their project (`project_description`) and asks a specific question to confirm their needs and see if they are the right person to talk to.
    - **If Stage is "Qualified":** The lead is a good fit. The email should summarize your understanding of their needs and propose a concrete next step, like "I've reviewed your project for a new 4plex construction and can put together a formal quote. Are you free for a brief 15-minute call tomorrow to confirm the details?"
    - **If Stage is "Quote Sent":** The goal is to follow up. The email should be a polite check-in, asking if they've had a chance to review the quote and if they have any questions. Avoid being pushy.
    - **If Stage is "Negotiation":** The goal is to close the deal. The email should address any known sticking points, reiterate the value, and create a sense of urgency or provide a final piece of information to get them to confirm the order.

    **General Rules:**
    - **Personalize:** Always use the recipient's name. Reference their specific project details.
    - **Be Clear & Concise:** Get to the point quickly.
    - **Single Call-to-Action (CTA):** End with one clear, easy-to-answer question or proposed next step.
    
    {feedback_section}
    
    Now, generate the email draft with a 'subject' and 'body'.
    """
    
    feedback_prompt_section = ""
    if feedback:
        feedback_prompt_section = f"""
        **IMPORTANT HUMAN FEEDBACK:**
        The user has provided the following feedback on the previous draft. You MUST incorporate these changes: "{feedback}"
        """

    prompt = ChatPromptTemplate.from_template(prompt_template)
    generation_chain = prompt | structured_llm

    email_draft = generation_chain.invoke({
        "sales_stages": sales_stages,
        "lead_data": json.dumps(db_data.get("crm_lead")),
        "partner_data": json.dumps(db_data.get("res_partner")),
        "user_data": json.dumps(db_data.get("res_users")),
        "org_data": json.dumps(db_data.get("organization")),
        "stage_data": json.dumps(db_data.get("crm_stage", {"name": "Unknown"})),
        "stage_name": db_data.get("crm_stage", {}).get("name", "Unknown"),
        "feedback_section": feedback_prompt_section
    })
    
    new_history = email_history + [email_draft]
    return {**state,"email_history": new_history, "feedback": None, "human_decision": ""}

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