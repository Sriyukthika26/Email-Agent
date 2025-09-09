# /datamodels.py
from typing import TypedDict, List, Literal
from pydantic import BaseModel, Field

class EmailDraft(BaseModel):
    """A generated email draft with a subject and body."""
    subject: str = Field(description="The subject line of the email.")
    body: str = Field(description="The body content of the email, written in a personalized and professional tone.")

class GenerationRequest(BaseModel):
    """Request model for starting a new email generation flow.
    
    This model contains the necessary information to initiate an email generation
    process for a specific lead and user. It includes optional user instructions
    that can guide the AI agent in crafting the email content.
    """
    leadId: int = Field(description="The unique identifier of the lead for whom the email is being generated")
    userId: int = Field(description="The unique identifier of the user requesting the email generation")
    user_instructions: str | None = Field(default=None, description="Optional instructions from the user to guide email generation")

class UpdateRequest(BaseModel):
    """Request model for updating a flow with feedback or approval.
    
    This model is used when a user provides feedback on a generated email or
    makes a decision to either regenerate the email or approve it for sending.
    The thread_id links this update to the specific email generation session.
    """
    thread_id: str = Field(description="Unique identifier for the email generation thread/session")
    decision: Literal["regenerate", "approve"] = Field(description="User's decision: either regenerate the email or approve it")
    feedback: str | None = Field(default=None, description="Optional feedback from the user to improve the email generation")

class StateUpdateRequest(BaseModel):
    """Request model for updating the agent state with email history.
    
    This model is used to update the current state of an email generation agent
    by providing the complete email history for a specific thread. This allows
    the system to maintain context across multiple interactions.
    """
    thread_id: str = Field(description="Unique identifier for the email generation thread/session")
    email_history: List[EmailDraft] = Field(description="Complete history of email drafts generated for this thread")

class AgentState(TypedDict):
    """Represents the complete state of an email generation agent.
    
    This TypedDict defines the structure for maintaining the state of an email
    generation agent throughout its lifecycle. It includes all necessary context
    about the lead, user, database information, email history, and user feedback
    to enable continuous and context-aware email generation.
    """
    lead_id: int = Field(description="Unique identifier of the lead being targeted")
    user_id: int = Field(description="Unique identifier of the user managing this email generation")
    user_instructions: str = Field(description="Instructions provided by the user to guide email generation")
    db_data: dict = Field(description="Database information about the lead and related entities")
    email_history: List[EmailDraft] = Field(description="History of all email drafts generated in this session")
    feedback: str = Field(description="Latest feedback provided by the user")
    human_decision: Literal["regenerate", "approve"] = Field(description="User's latest decision on the email generation")
    error_message: str = Field(description="Any error messages encountered during the generation process")