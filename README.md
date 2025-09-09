## AgenticCRM — AI Email Agent (Backend + Frontend)

AgenticCRM is a full‑stack application that generates strategic, personalized sales emails from CRM data with a human‑in‑the‑loop workflow. The backend is built with FastAPI, LangChain, LangGraph, and OpenAI; the frontend is a Vite + React app.

### Features
- Fetches CRM records (lead, contact, organization, stage, history/past projects)
- Generates an HTML subject and body using OpenAI via LangChain
- Human‑in‑the‑loop: approve or request regeneration with feedback
- Stateless API with LangGraph checkpointing in memory
- Prompt managed in `backend/prompt.txt`

---

## Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- OpenAI API key

---

## Repository Structure
```
AgenticCRM/
  backend/
    main.py            # FastAPI app
    graph.py           # LangGraph workflow and nodes
    datamodels.py      # Pydantic models / types
    fetchdb.py         # CRM data fetching (concurrent)
    helper_functions.py
    projectsfetch.py   # Past projects API fetcher
    prompt.txt         # The LLM prompt template
    config.py          # Env loading + config
    requirements.txt   # Backend deps
  frontend/
    src/               # React app (Vite)
    package.json

```

---

## Environment Variables
Create a `backend/.env` file with:
```
OPENAI_API_KEY=sk-...
CRM_API_KEY=your_crm_api_key
# Used by backend/projectsfetch.py
API_AUTH=Bearer your-projects-api-token
```

Notes:
- `OPENAI_API_KEY` is required at startup (`config.py` validates it).
- `CRM_API_KEY` is required for `helper_functions.datafetch` requests.
- `API_AUTH` is used to fetch past projects in `projectsfetch.py`.

---

## Backend — Setup & Run

1) Install dependencies
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Run the API
```powershell
uvicorn main:app --host 0.0.0.0 --port 10000 --reload
```

3) Health check
```powershell
curl http://localhost:10000/
```

### Key Backend Files
- `graph.py`
  - Loads the prompt from `prompt.txt`
  - Nodes: `fetch_with_concurrency`, `generate_email_draft`, `save_approved_email`
  - Returns approved subject/body when process ends
- `main.py`
  - FastAPI routes: `/generate`, `/update`, `/state`
  - In‑memory checkpointing via LangGraph `MemorySaver`

### Prompt Editing
Edit `backend/prompt.txt`. It’s a plain text template consumed via `ChatPromptTemplate.from_template(...)`. Keep placeholders such as `{lead_data}`, `{partner_data}`, `{org_data}`, `{user_instructions}`, `{stage_name}`, `{stage_requirements}`, `{feedback_section}`, `{context_section}`.

---

## Frontend — Setup & Run

1) Install dependencies
```powershell
cd frontend
npm install
```

2) Start dev server
```powershell
npm run dev
```

3) Configure API base URL (if needed)
Check `frontend/src/api.js` or any file where the backend URL is referenced. Default backend runs at `http://localhost:10000`.

If deploying the frontend (Netlify/Vercel), ensure CORS in `backend/main.py` allows your deployed origin.

---

## API Usage

Base URL: `http://localhost:10000`

### 1) Start Generation
POST `/generate`
```json
{
  "leadId": 20410,
  "userId": 7,
  "user_instructions": "Keep it concise and friendly."
}
```
Response:
```json
{
  "thread_id": "...",
  "retrievedData": { /* CRM data snapshot */ },
  "email": { "subject": "...", "body": "<p>...</p>" }
}
```

### 2) Update Generation (Approve or Regenerate)
POST `/update`
```json
{
  "thread_id": "...",
  "decision": "approve" | "regenerate",
  "feedback": "Shorten the intro."
}
```
Response when approved:
```json
{
  "thread_id": "...",
  "email": null,
  "is_done": true,
  "message": "Email approved and process finished."
}
```

### 3) Update Only the State (Save & Continue after manual edit)
POST `/state`
```json
{
  "thread_id": "...",
  "email_history": [ { "subject": "...", "body": "<p>...</p>" } ]
}
```
Use this when a user edits the generated email in the UI and clicks "Save & Continue". It persists the edited draft(s) to the thread state without running the graph..

---

## Data Flow Overview
1. `/generate` triggers the graph. If no data, it fetches:
   - `res_partner`, `organization`, `crm_lead`, optionally `crm_stage`
   - either conversation history or past projects
2. `generate_email_draft` builds the prompt context and gets a structured `EmailDraft` from the LLM.
3. User calls `/update`:
   - `regenerate` → draft again with feedback context
   - `approve` → graph routes to `end_process` and `save_approved_email` returns subject/body.

---

## Dependency Management
Backend dependencies are listed in `backend/requirements.txt` (FastAPI, LangChain, LangGraph, OpenAI, etc.). If you update major versions, test the graph and Pydantic model compatibility.

---

## Troubleshooting
- 401/403 from CRM endpoints: verify `CRM_API_KEY` and `API_AUTH`.
- OpenAI errors: ensure `OPENAI_API_KEY` is valid and model `gpt-4o-mini` is available.
- CORS issues: adjust `allow_origins` in `backend/main.py`.
- Empty drafts: confirm `leadId`/`userId` exist in your CRM and the fetch queries return data.
- Windows path issues: run PowerShell as admin if venv activation is blocked (`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`).

---

## Deployment Notes
- Backend: deploy on any ASGI host (e.g., Azure App Service, Render, Fly.io). Run `uvicorn main:app --host 0.0.0.0 --port 10000`.
- Frontend: build with `npm run build` and host the `frontend/dist` folder (Netlify/Vercel/Nginx).
- Configure environment variables in your host and set proper CORS.

---


<img width="1514" height="1063" alt="Screenshot 2025-09-09 114828" src="https://github.com/user-attachments/assets/9a3b625a-c0ea-4706-85fe-c88a1fefeff0" />
