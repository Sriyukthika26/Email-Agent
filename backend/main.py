import uuid
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END
from datamodels import GenerationRequest, UpdateRequest, StateUpdateRequest
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
    """Starts a new email generation flow."""
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
    """Resumes a paused graph with feedback or approval."""
    app_graph = request.app.state.app_graph
    config = {"configurable": {"thread_id": payload.thread_id}}
    
    updates = {
        "human_decision": payload.decision,
        "feedback": payload.feedback,
    }

    await app_graph.ainvoke(updates, config=config)
    
    final_state_values = await app_graph.aget_state(config)
    
    if error_message := final_state_values.values.get("error_message"):
        raise HTTPException(status_code=500, detail=error_message)

    is_done = final_state_values.values.get("human_decision") == "approve"
    
    return {
        "thread_id": payload.thread_id,
        "email": final_state_values.values.get("email_history", [])[-1].dict() if not is_done and final_state_values.values.get("email_history") else None,
        "is_done": is_done,
        "message": "Email approved and process finished." if is_done else "Email regenerated."
    }


@app.post("/state")
async def update_state(payload: StateUpdateRequest, request: Request):
    """Explicitly updates the state for a given thread without running the graph."""
    app_graph = request.app.state.app_graph
    config = {"configurable": {"thread_id": payload.thread_id}}
    
    try:
        await app_graph.aupdate_state(config, {"email_history": payload.email_history})
        print(f"--- State updated for thread {payload.thread_id}. Last subject: {payload.email_history[-1].subject} ---")
        return {"status": "ok", "message": "State updated successfully."}
    except Exception as e:
        print(f"Error updating state: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update state: {e}")

@app.get("/")
def read_root():
    return {"message": "AI Email Agent Backend is running."}

if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=10000)




