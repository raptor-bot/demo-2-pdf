"""Demo2PDF Backend with LLM-powered description generation"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
import uuid
from datetime import datetime
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import services
from src.services.llm_annotation_service import HybridAnnotationService

app = FastAPI(
    title="Demo2PDF API",
    description="Capture web interactions and convert to PDF documentation",
    version="0.1.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage setup
STORAGE_PATH = Path("storage")
STORAGE_PATH.mkdir(exist_ok=True)

# Mount storage directory for serving screenshots
app.mount("/storage", StaticFiles(directory=str(STORAGE_PATH)), name="storage")

# In-memory session storage (use database in production)
sessions = {}


@app.get("/")
def read_root():
    """API health check"""
    return {
        "message": "Demo2PDF API is running",
        "version": "0.1.0",
        "llm_enabled": os.getenv("ENABLE_LLM_DESCRIPTIONS", "false").lower() == "true"
    }


@app.post("/api/sessions")
def create_session(
    use_llm: bool = False,
    llm_provider: str = "openai",
    api_key: Optional[str] = None,
    context: Optional[str] = None
):
    """
    Create new capture session

    Args:
        use_llm: Enable LLM-powered description generation
        llm_provider: LLM provider ("openai", "anthropic", "ollama")
        api_key: API key for the LLM provider (optional if in .env)
        context: Context about what's being documented (e.g., "e-commerce checkout")
    """
    session_id = str(uuid.uuid4())

    # Get default from environment if not specified
    if use_llm is None:
        use_llm = os.getenv("ENABLE_LLM_DESCRIPTIONS", "false").lower() == "true"

    # Session configuration
    config = {
        "use_llm": use_llm,
        "llm_provider": llm_provider or os.getenv("LLM_PROVIDER", "openai"),
        "api_key": api_key,
        "context": context
    }

    sessions[session_id] = {
        "id": session_id,
        "created_at": datetime.now().isoformat(),
        "steps": [],
        "events": [],
        "config": config,
        "context": context
    }

    return {
        "session_id": session_id,
        "created_at": sessions[session_id]["created_at"],
        "config": {k: v for k, v in config.items() if k != "api_key"}  # Don't return API key
    }


@app.post("/api/sessions/{session_id}/events")
async def add_event(
    session_id: str,
    event_data: str = Form(...),
    screenshot: UploadFile = File(...)
):
    """
    Add captured event to session with screenshot

    Args:
        session_id: Session ID
        event_data: JSON string with event information
        screenshot: Screenshot image file
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # Parse event data
    try:
        event = json.loads(event_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid event data JSON")

    # Save screenshot
    step_id = len(sessions[session_id]["events"]) + 1
    filename = f"{session_id}_step_{step_id:03d}.png"
    filepath = STORAGE_PATH / filename

    with open(filepath, "wb") as f:
        content = await screenshot.read()
        f.write(content)

    event["screenshot_path"] = str(filepath)
    event["step_id"] = step_id

    # Add to events
    sessions[session_id]["events"].append(event)

    # Generate description
    config = sessions[session_id]["config"]
    service = HybridAnnotationService(
        use_llm=config.get("use_llm", False),
        llm_provider=config.get("llm_provider", "openai"),
        api_key=config.get("api_key")
    )

    descriptions = service.generate_descriptions(
        [event],
        context=sessions[session_id].get("context")
    )
    description_result = descriptions[0]

    # Create step with description
    step = {
        "id": step_id,
        "event": event,
        "screenshot": str(filepath),
        "timestamp": event.get("timestamp"),
        "template_description": description_result["template_description"],
        "llm_description": description_result.get("llm_description"),
        "final_description": description_result["final_description"],
        "user_edited": False
    }

    sessions[session_id]["steps"].append(step)

    return {
        "success": True,
        "step_id": step_id,
        "description": step["final_description"]
    }


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str):
    """Get session with all steps and descriptions"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]

    return {
        "id": session["id"],
        "created_at": session["created_at"],
        "total_steps": len(session["steps"]),
        "config": {k: v for k, v in session["config"].items() if k != "api_key"},
        "context": session.get("context"),
        "steps": session["steps"]
    }


@app.get("/api/sessions")
def list_sessions():
    """List all sessions"""
    return {
        "total": len(sessions),
        "sessions": [
            {
                "id": s["id"],
                "created_at": s["created_at"],
                "total_steps": len(s["steps"]),
                "config": {k: v for k, v in s["config"].items() if k != "api_key"}
            }
            for s in sessions.values()
        ]
    }


@app.post("/api/sessions/{session_id}/regenerate")
def regenerate_descriptions(
    session_id: str,
    use_llm: bool = True,
    llm_provider: str = "openai",
    api_key: Optional[str] = None,
    context: Optional[str] = None
):
    """
    Regenerate all descriptions for a session

    Useful for:
    - Upgrading template-based descriptions to LLM-enhanced
    - Trying different LLM providers
    - Adding context after initial capture
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # Create new annotation service with requested config
    service = HybridAnnotationService(
        use_llm=use_llm,
        llm_provider=llm_provider,
        api_key=api_key
    )

    # Get all events
    events = sessions[session_id]["events"]

    # Use provided context or session context
    context = context or sessions[session_id].get("context")

    # Regenerate descriptions
    descriptions = service.generate_descriptions(events, context=context)

    # Update steps
    for i, desc_result in enumerate(descriptions):
        if i < len(sessions[session_id]["steps"]):
            sessions[session_id]["steps"][i].update({
                "template_description": desc_result["template_description"],
                "llm_description": desc_result.get("llm_description"),
                "final_description": desc_result["final_description"]
            })

    # Update session config
    sessions[session_id]["config"].update({
        "use_llm": use_llm,
        "llm_provider": llm_provider,
        "api_key": api_key
    })
    if context:
        sessions[session_id]["context"] = context

    return {
        "success": True,
        "steps_updated": len(descriptions),
        "config": {k: v for k, v in sessions[session_id]["config"].items() if k != "api_key"}
    }


@app.put("/api/sessions/{session_id}/steps/{step_id}")
def update_step(
    session_id: str,
    step_id: int,
    description: str
):
    """
    Update step description manually

    Allows users to edit auto-generated descriptions
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # Find step
    step_index = step_id - 1
    if step_index < 0 or step_index >= len(sessions[session_id]["steps"]):
        raise HTTPException(status_code=404, detail="Step not found")

    # Update description
    sessions[session_id]["steps"][step_index]["final_description"] = description
    sessions[session_id]["steps"][step_index]["user_edited"] = True

    return {
        "success": True,
        "step_id": step_id,
        "description": description
    }


@app.delete("/api/sessions/{session_id}/steps/{step_id}")
def delete_step(session_id: str, step_id: int):
    """Delete a step from session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    step_index = step_id - 1
    if step_index < 0 or step_index >= len(sessions[session_id]["steps"]):
        raise HTTPException(status_code=404, detail="Step not found")

    # Remove step and event
    deleted_step = sessions[session_id]["steps"].pop(step_index)
    sessions[session_id]["events"].pop(step_index)

    # Renumber remaining steps
    for i, step in enumerate(sessions[session_id]["steps"]):
        step["id"] = i + 1
        step["step_id"] = i + 1

    return {
        "success": True,
        "deleted_step_id": step_id
    }


@app.get("/api/sessions/{session_id}/export/simple")
def export_simple_pdf(session_id: str):
    """
    Generate simple PDF (basic implementation)

    Full PDF generation with WeasyPrint coming in next iteration
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]

    # Generate simple HTML
    html = "<html><head><style>"
    html += "body { font-family: Arial, sans-serif; margin: 40px; }"
    html += ".step { margin-bottom: 30px; page-break-inside: avoid; }"
    html += ".step img { max-width: 100%; border: 1px solid #ccc; }"
    html += "h1 { color: #333; }"
    html += "h2 { color: #666; }"
    html += "</style></head><body>"
    html += "<h1>User Guide</h1>"
    html += f"<p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"

    for step in session["steps"]:
        html += f'<div class="step">'
        html += f'<h2>Step {step["id"]}: {step["final_description"]}</h2>'
        html += f'<img src="file://{step["screenshot"]}" alt="Step {step["id"]}">'
        html += '</div>'

    html += "</body></html>"

    # For now, return the steps as JSON
    # Full PDF generation requires WeasyPrint which we'll add next
    return {
        "message": "PDF generation placeholder",
        "total_steps": len(session["steps"]),
        "steps": [
            {
                "id": s["id"],
                "description": s["final_description"],
                "screenshot": s["screenshot"]
            }
            for s in session["steps"]
        ],
        "html_preview": html[:500] + "..."  # Preview
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/viewer", response_class=HTMLResponse)
def session_viewer():
    """Serve the session viewer HTML page"""
    viewer_path = Path(__file__).parent / "viewer.html"

    if not viewer_path.exists():
        raise HTTPException(status_code=404, detail="Viewer page not found")

    with open(viewer_path, "r") as f:
        return HTMLResponse(content=f.read())


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    print(f"""
    ╔══════════════════════════════════════════════╗
    ║         Demo2PDF Backend Server              ║
    ╠══════════════════════════════════════════════╣
    ║  API: http://{host}:{port}              ║
    ║  Docs: http://{host}:{port}/docs        ║
    ║  LLM: {'Enabled' if os.getenv('ENABLE_LLM_DESCRIPTIONS') == 'true' else 'Disabled (template-based)'}                         ║
    ╚══════════════════════════════════════════════╝
    """)

    uvicorn.run(app, host=host, port=port)
