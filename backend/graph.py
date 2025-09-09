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
from fetchdb import fetch_with_concurrency

# --- Graph Nodes (The "workers" of our agent) ---

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
        print("--- (RUNNING) FEEDBACK SECTION ---")
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

    context_section = ""
    conversation_history = db_data.get("conversation_history", [])
    past_projects = db_data.get("past_projects", [])

    if conversation_history:
        print("--- (RUNNING) CONVERSATION HISTORY SECTION ---")
        history_json = json.dumps(conversation_history, indent=2)
        context_section = f"""**Instruction:** Review the following conversation history (in JSON format) to draft a logical next-step email. The `id` and `parent_id` fields show the reply chain.
        Do not repeat information that has already been shared.
        **Previous Conversation History:**
        ```json
            {history_json}
        ```"""
    elif past_projects:
        print("--- (RUNNING) PAST PROJECTS SECTION ---")
        context_section = f"""**Instruction:** This is the first email to this lead. To build credibility, subtly reference 1-2 relevant project from the list below.For instance, if the lead's project is residential, mention a similar residential project the company has completed.
        **Company's Past Projects (for reference):**
        {past_projects}
        Emphasize the mentioned projects using `<strong>` or `<em>` tags.
        """

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
    # TODO: In a real application, save this to a database.
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
workflow.add_node("fetch_data", fetch_with_concurrency)
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
