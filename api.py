"""FastAPI wrapper for the Multi-Agent Research System.

Provides endpoints for a chatbot that acts as a research assistant using Gemini.
- /chat: conversational endpoint powered by Gemini; will refuse non-research queries
- /research: start a research run using the existing workflow (can stream progress)
- /status: model status
- /download_report: download generated DOCX reports

Run with: python -m api or uvicorn api:app --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import time
import json
import os
from types import SimpleNamespace
from fastapi.middleware.cors import CORSMiddleware
from agents import WordAgent  # <--- IMPORT ADDED

# Lazy imports for heavy dependencies (done inside endpoints) to keep module import lightweight

app = FastAPI(title="MARS Research Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","*"],
    allow_origin_regex=r"^https?://localhost:\d{4}$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store: {session_id: [ {role: 'user'|'assistant'|'system', 'content': str}, ... ] }
SESSIONS: Dict[str, List[Dict[str, str]]] = {}
OUTPUTS_DIR = "outputs"  # Directory where WordAgent saves files

# Ensure output directory exists
if not os.path.exists(OUTPUTS_DIR):
    os.makedirs(OUTPUTS_DIR)

# System instruction: strictly act as a research assistant and refuse unrelated queries
RESEARCH_SYSTEM_PROMPT = (
    "You are a specialized research assistant. Only answer queries that are explicitly about AI ML computer science research tasks, collecting, summarizing, or analyzing information. "
    "If the user's query is not related to research, respond with reply like 'I can only help with research-related requests.' and ask the user to rephrase as a research request. "
    "If user talks like 'hi' or 'hello' or 'how are you', respond with 'Hello! How can I assist you with your research today?' "
    "When asked to perform research, call the research workflow backend and return results when available. Keep answers concise and cite sources when available."
)


class ChatRequest(BaseModel):
    session_id: Optional[str]
    message: str
    temperature: Optional[float] = None
    # If true and a research intent is detected, stream research progress/results
    stream: Optional[bool] = False


class ResearchRequest(BaseModel):
    session_id: Optional[str]
    topic: str
    stream: Optional[bool] = False
    generate_docx: Optional[bool] = True  # <--- FIELD ADDED


def ensure_session(session_id: Optional[str]) -> str:
    if session_id and session_id in SESSIONS:
        return session_id
    new_id = str(uuid.uuid4())
    # Initialize with system prompt
    SESSIONS[new_id] = [{"role": "system", "content": RESEARCH_SYSTEM_PROMPT}]
    return new_id


# Simple heuristic keywords to detect research intent quickly
RESEARCH_KEYWORDS = [
    "research",
    "find",
    "search",
    "summar",
    "paper",
    "papers",
    "literature",
    "sources",
    "cite",
    "citations",
    "evidence",
    "survey",
    "review",
    "analyze",
    "investigate",
    "collect",
    "provide references",
]


def detect_research_intent(message: str, use_model_fallback: bool = True) -> bool:
    """Return True if message likely requests research.

    First use a lightweight keyword heuristic. If nothing decisive and use_model_fallback=True,
    ask the Gemini client to classify the intent (YES/NO) as a fallback.
    """
    text = (message or "").lower()
    # quick keyword heuristic
    for kw in RESEARCH_KEYWORDS:
        if kw in text:
            return True

    if not use_model_fallback:
        return False

    # Fallback: few-shot classification using Gemini for higher precision
    try:
        from gemini_client import gemini_client

        system_prompt = (
            "You are a strict classifier. Answer with a single word: YES or NO. "
            "YES means the user's message requests a research task (examples: find papers, summarize literature, collect evidence, provide citations, analyze studies). "
            "NO means the message is not a research request. Reply only with YES or NO and nothing else."
        )

        # Few-shot examples to guide the classifier
        few_shot_examples = [
            ("Find recent papers about transformer neural networks and summarize their evaluation methods.", "YES"),
            ("Collect citations supporting the claim that larger models generalize better.", "YES"),
            ("Provide a literature review on transformer-based architectures for NLP.", "YES"),
            ("Tell me a joke about transformers.", "NO"),
            ("What's the weather in Delhi today?", "NO"),
            ("Help me write a birthday message.", "NO"),
        ]

        examples_text = "\n".join([f"Message: {ex}\nLabel: {lbl}" for ex, lbl in few_shot_examples])

        user_prompt = f"{examples_text}\n\nMessage: {message}\nLabel:"

        resp = gemini_client.generate_response(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.0)
        if not resp:
            return False
        r = resp.strip().lower()
        if r.startswith("yes"):
            return True
        return False
    except Exception:
        # If model call fails, default to False
        return False


def generate_docx_for_result(result: dict) -> str:
    """Helper to run WordAgent on a workflow result dictionary."""
    try:
        wa = WordAgent()
        # Create a state proxy from the result dict
        state_proxy = SimpleNamespace(
            final_report=result.get('final_report'),
            draft_report=result.get('draft_report'),
            user_topic=result.get('user_topic', 'Research Report')
        )
        wa_output = wa.convert_to_word(state_proxy)
        return wa_output.get("filename") # Return just the filename for the URL
    except Exception as e:
        print(f"Error generating DOCX: {e}")
        return None


@app.post("/chat")
async def chat(req: ChatRequest):
    """Conversational endpoint using Gemini but constrained to research-only behavior."""
    session_id = ensure_session(req.session_id)
    history = SESSIONS[session_id]

    # Append user message
    history.append({"role": "user", "content": req.message})
    # Detect research intent
    is_research = detect_research_intent(req.message)

    if is_research:
        # If user requested research, trigger the workflow. Support streaming if requested.
        from workflow import MultiAgentResearchWorkflow
        workflow = MultiAgentResearchWorkflow()

        # Stream via SSE if requested
        if req.stream:
            def progress_generator():
                def callback(msg: str):
                    payload = json.dumps({"type": "progress", "message": msg})
                    nonlocal last_yield
                    last_yield = f"data: {payload}\n\n"

                last_yield = ""
                try:
                    result = workflow.run_with_callback(req.message, callback)
                    payload = json.dumps({"type": "result", "result": result})
                    yield f"data: {payload}\n\n"
                except Exception as e:
                    payload = json.dumps({"type": "error", "error": str(e)})
                    yield f"data: {payload}\n\n"

            return StreamingResponse(progress_generator(), media_type="text/event-stream")

        # Non-streaming: run synchronously
        try:
            result = workflow.run(req.message)
            assistant_text = result.get('final_report') or result.get('draft_report') or "Research completed"
            history.append({"role": "assistant", "content": assistant_text})
            return JSONResponse({"session_id": session_id, "reply": assistant_text, "result": result})
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Otherwise, normal conversational flow via Gemini
    try:
        from gemini_client import gemini_client

        response_text = gemini_client.generate_response(
            system_prompt=RESEARCH_SYSTEM_PROMPT,
            user_prompt=req.message,
            temperature=req.temperature,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Normalize refusals
    refusal_phrases = ["I can only help with research-related requests", "I can only help with research"]
    if any(p.lower() in response_text.lower() for p in refusal_phrases):
        history.append({"role": "assistant", "content": response_text})
        return JSONResponse({"session_id": session_id, "reply": response_text, "refusal": True})

    history.append({"role": "assistant", "content": response_text})
    return JSONResponse({"session_id": session_id, "reply": response_text, "refusal": False})


@app.post("/research")
async def research(req: ResearchRequest):
    """Trigger the research workflow. If stream=True, stream progress via SSE; else run and return final report JSON."""
    session_id = ensure_session(req.session_id)
    # Lazy import workflow to avoid heavy imports at module import time
    from workflow import MultiAgentResearchWorkflow
    workflow = MultiAgentResearchWorkflow()

    def progress_generator():
        # Streaming generator for Server-Sent Events
        # Callback style: yield progress messages as they come from the workflow
        def callback(msg: str):
            payload = json.dumps({"type": "progress", "message": msg})
            # SSE format: data: <json>\n\n
            nonlocal last_yield
            last_yield = f"data: {payload}\n\n"

        last_yield = ""

        try:
            # Start research with callback
            result = workflow.run_with_callback(req.topic, callback)
            
            # --- DOCX Generation Logic for Stream ---
            if req.generate_docx:
                yield f"data: {json.dumps({'type': 'progress', 'message': 'Generating Word Document...'})}\n\n"
                docx_filename = generate_docx_for_result(result)
                if docx_filename:
                    result['docx_filename'] = docx_filename
                    result['download_url'] = f"/download_report/{docx_filename}"
                    yield f"data: {json.dumps({'type': 'progress', 'message': f'Document ready: {docx_filename}'})}\n\n"
            # ----------------------------------------

            # After completion, send final report
            payload = json.dumps({"type": "result", "result": result})
            yield f"data: {payload}\n\n"
        except Exception as e:
            payload = json.dumps({"type": "error", "error": str(e)})
            yield f"data: {payload}\n\n"

    if req.stream:
        return StreamingResponse(progress_generator(), media_type="text/event-stream")

    # Non-streaming: run synchronously
    try:
        result = workflow.run(req.topic)
        
        # --- DOCX Generation Logic for Non-Stream ---
        if req.generate_docx:
            docx_filename = generate_docx_for_result(result)
            if docx_filename:
                result['docx_filename'] = docx_filename
                result['download_url'] = f"/download_report/{docx_filename}"
        # --------------------------------------------
        
        # Save to session history as assistant message
        SESSIONS[session_id].append({"role": "assistant", "content": result.get('final_report', '')})
        return JSONResponse({"session_id": session_id, "result": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download_report/{filename}")
async def download_report(filename: str):
    """Endpoint to retrieve the generated DOCX file."""
    # Security check: ensure filename doesn't have directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
        
    file_path = os.path.join(OUTPUTS_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(
        path=file_path, 
        filename=filename, 
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )


@app.get("/status")
async def status():
    from gemini_client import gemini_client
    return gemini_client.get_model_status()

@app.get("/")
def root():
    return {"message": "MARS Research Assistant API is running."}

# Simple uvicorn runner convenience
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)