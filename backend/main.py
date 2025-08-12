import uuid
import uvicorn
from fastapi import FastAPI, HTTPException, Request # Import Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END 

# Import from our other modules
from datamodels import GenerationRequest, UpdateRequest
from graph import workflow
from config import OPENAI_API_KEY

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application startup and shutdown."""
    checkpointer = MemorySaver()
    app.state.app_graph = workflow.compile(
        checkpointer=checkpointer,
        interrupt_after=["generate_email"],
    )
    print("--- Application startup complete. Graph compiled with MemorySaver. ---")
    yield
    print("--- Application shutdown complete. ---")

app = FastAPI(
    title="AI Email Agent Backend",
    description="API for orchestrating email generation with a human-in-the-loop workflow.",
    lifespan=lifespan,
)
origins = [
    "https://visionary-empanada-0ba1aa.netlify.app"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/generate")
async def start_generation(payload: GenerationRequest, request: Request):
    """Starts a new email generation flow and returns the first draft."""
    app_graph = request.app.state.app_graph
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    inputs = {
        "lead_id": payload.leadId,
        "user_id": payload.userId,
        "user_instructions": payload.user_instructions,
    }
    
    final_state = await app_graph.ainvoke(inputs, config=config)

    if error_message := final_state.get("error_message"):
        raise HTTPException(status_code=500, detail=error_message)
        
    if not final_state or not final_state.get("email_history"):
        raise HTTPException(status_code=500, detail="Failed to generate email.")

    return {
        "thread_id": thread_id,
        "retrievedData": final_state.get("db_data"),
        "email": final_state["email_history"][-1].dict()
    }

@app.post("/update")
async def update_generation(payload: UpdateRequest, request: Request):
    """Resumes a paused graph with human feedback or approval."""
    app_graph = request.app.state.app_graph
    config = {"configurable": {"thread_id": payload.thread_id}}
    
    state_update = {
        "human_decision": payload.decision,
        "feedback": payload.feedback
    }
    
    final_state = await app_graph.ainvoke(state_update, config=config)
    
    if error_message := final_state.get("error_message"):
        raise HTTPException(status_code=500, detail=error_message)

    # The 'approve' decision persists in the state for the "approve" flow,
    # but is cleared by the 'generate_email' node in the "regenerate" flow.
    is_done = final_state.get("human_decision") == "approve"
    
    return {
        "thread_id": payload.thread_id,
        "email": final_state.get("email_history", [])[-1].dict() if not is_done and final_state.get("email_history") else None,
        "is_done": is_done,
        "message": "Email approved and process finished." if is_done else "Email regenerated."
    }

@app.get("/")
def read_root():
    return {"message": "AI Email Agent Backend is running."}

if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=10000)




