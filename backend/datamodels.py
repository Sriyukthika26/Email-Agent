# /datamodels.py
from typing import TypedDict, List, Literal
from pydantic import BaseModel, Field

class EmailDraft(BaseModel):
    """A generated email draft with a subject and body."""
    subject: str = Field(description="The subject line of the email.")
    body: str = Field(description="The body content of the email, written in a personalized and professional tone.")

class GenerationRequest(BaseModel):
    """Request model for starting a new email generation flow."""
    leadId: int
    userId: int
    user_instructions: str | None = None

class UpdateRequest(BaseModel):
    """Request model for updating a flow with feedback or approval."""
    thread_id: str
    decision: Literal["regenerate", "approve"]
    feedback: str | None = None

class StateUpdateRequest(BaseModel):
    thread_id: str
    email_history: List[EmailDraft]

class AgentState(TypedDict):
    """Represents the state of our email generation agent."""
    lead_id: int
    user_id: int
    user_instructions: str
    db_data: dict
    email_history: List[EmailDraft]
    feedback: str
    human_decision: Literal["regenerate", "approve"]
    error_message: str