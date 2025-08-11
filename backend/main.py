# /main.py
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

# Import from our other modules
from datamodels import GenerationRequest, UpdateRequest
from graph import app_graph
from config import OPENAI_API_KEY

# --- FastAPI Application ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Check for necessary configurations on startup."""
    if not OPENAI_API_KEY or OPENAI_API_KEY == "YOUR_OPENAI_API_KEY":
        print("WARNING: OPENAI_API_KEY is not set. The application will not work.")
    yield

app = FastAPI(
    title="AI Email Agent Backend",
    description="API for orchestrating email generation with a full human-in-the-loop workflow.",
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
async def start_generation(request: GenerationRequest):
    """Starts a new email generation flow and returns the first draft."""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    inputs = {
        "lead_id": request.leadId,
        "user_id": request.userId,
        "user_instructions": request.user_instructions,
        "email_history": [],
    }
    
    final_state = await app_graph.ainvoke(inputs, config=config)

    if final_state.get("error_message"):
        raise HTTPException(status_code=500, detail=final_state["error_message"])
        
    if not final_state or not final_state.get("email_history"):
        raise HTTPException(status_code=500, detail="Failed to generate email.")

    return {
        "thread_id": thread_id,
        "retrievedData": final_state.get("db_data"),
        "email": final_state["email_history"][-1].dict()
    }

@app.post("/update")
async def update_generation(request: UpdateRequest):
    """Resumes a paused graph with human feedback or approval."""
    config = {"configurable": {"thread_id": request.thread_id}}
    
    state_update = {
        "human_decision": request.decision,
        "feedback": request.feedback
    }
    
    final_state = await app_graph.ainvoke(state_update, config=config)
    
    if final_state.get("error_message"):
        raise HTTPException(status_code=500, detail=final_state["error_message"])

    is_done = not app_graph.get_state(config).next
    
    return {
        "thread_id": request.thread_id,
        "email": final_state["email_history"][-1].dict() if not is_done else None,
        "is_done": is_done,
        "message": "Email approved and process finished." if is_done else "Email regenerated."
    }

@app.get("/")
def read_root():
    return {"message": "AI Email Agent Backend is running."}


if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=10000)

