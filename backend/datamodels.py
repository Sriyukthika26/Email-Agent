# /models.py
from typing import TypedDict, List, Literal
from pydantic import BaseModel, Field

# --- Pydantic Models for API Validation ---

class GenerationRequest(BaseModel):
    """Request model for starting a new email generation flow."""
    leadId: str
    userId: str
    user_instructions: str | None = None

class UpdateRequest(BaseModel):
    """Request model for updating a flow with feedback or approval."""
    thread_id: str
    decision: Literal["regenerate", "approve"]
    feedback: str | None = None

# --- LangGraph State Definition ---

class EmailDraft(BaseModel):
    """A generated email draft with a subject and body."""
    subject: str = Field(description="The subject line of the email.")
    body: str = Field(description="The body content of the email, written in a personalized and professional tone.")

class AgentState(TypedDict):
    """Represents the state of our email generation agent."""
    lead_id: str
    user_id: str
    user_instructions: str | None
    db_data: dict
    email_history: List[EmailDraft]
    feedback: str | None
    human_decision: Literal["regenerate", "approve"]| None
    error_message: str | None
