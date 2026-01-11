"""Demo2PDF Backend with LLM-powered description generation"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import json
import uuid
from datetime import datetime
from typing import Optional, List
import os
from dotenv import load_dotenv


# Pydantic models for request bodies
class ReorderRequest(BaseModel):
    new_order: List[int]

class SubStepsRequest(BaseModel):
    sub_steps: List[str]

class SessionMetadataRequest(BaseModel):
    title: Optional[str] = None
    sub_title: Optional[str] = None
    description: Optional[str] = None

# Load environment variables
load_dotenv()

# Import services
from src.services.llm_annotation_service import HybridAnnotationService
from src.services.video_analysis_service import VideoAnalysisService

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
SESSIONS_FILE = STORAGE_PATH / "sessions.json"

# Mount storage directory for serving screenshots
app.mount("/storage", StaticFiles(directory=str(STORAGE_PATH)), name="storage")

# In-memory session storage (persisted to JSON file)
sessions = {}


def load_sessions():
    """Load sessions from JSON file on startup"""
    global sessions
    if SESSIONS_FILE.exists():
        try:
            with open(SESSIONS_FILE, "r") as f:
                sessions = json.load(f)
            print(f"Loaded {len(sessions)} sessions from storage")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading sessions: {e}")
            sessions = {}
    else:
        sessions = {}


def save_sessions():
    """Save sessions to JSON file"""
    try:
        with open(SESSIONS_FILE, "w") as f:
            json.dump(sessions, f, indent=2)
    except IOError as e:
        print(f"Error saving sessions: {e}")


# Load sessions on module import
load_sessions()


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
        "context": context,
        "archived": False
    }

    save_sessions()

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
        "user_edited": False,
        "sub_steps": []
    }

    sessions[session_id]["steps"].append(step)
    save_sessions()

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
        "title": session.get("title", "User Guide"),
        "sub_title": session.get("sub_title"),
        "description": session.get("description"),
        "archived": session.get("archived", False),
        "steps": session["steps"]
    }


@app.put("/api/sessions/{session_id}/metadata")
def update_session_metadata(session_id: str, request: SessionMetadataRequest):
    """
    Update session metadata (title, sub_title, description).

    Args:
        session_id: Session ID
        request: SessionMetadataRequest with title, sub_title, and/or description
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    if request.title is not None:
        sessions[session_id]["title"] = request.title.strip()

    if request.sub_title is not None:
        sessions[session_id]["sub_title"] = request.sub_title.strip() if request.sub_title.strip() else None

    if request.description is not None:
        sessions[session_id]["description"] = request.description.strip() if request.description.strip() else None

    save_sessions()

    return {
        "success": True,
        "title": sessions[session_id].get("title", "User Guide"),
        "sub_title": sessions[session_id].get("sub_title"),
        "description": sessions[session_id].get("description")
    }


@app.get("/api/sessions")
def list_sessions(include_archived: bool = False):
    """List all sessions, optionally including archived ones"""
    filtered_sessions = [
        s for s in sessions.values()
        if include_archived or not s.get("archived", False)
    ]

    return {
        "total": len(filtered_sessions),
        "sessions": [
            {
                "id": s["id"],
                "created_at": s["created_at"],
                "total_steps": len(s["steps"]),
                "title": s.get("title", "User Guide"),
                "sub_title": s.get("sub_title"),
                "description": s.get("description"),
                "archived": s.get("archived", False),
                "config": {k: v for k, v in s["config"].items() if k != "api_key"}
            }
            for s in sorted(filtered_sessions, key=lambda x: x["created_at"], reverse=True)
        ]
    }


@app.put("/api/sessions/{session_id}/archive")
def archive_session(session_id: str, archived: bool = True):
    """Archive or unarchive a session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    sessions[session_id]["archived"] = archived
    save_sessions()

    return {
        "success": True,
        "session_id": session_id,
        "archived": archived
    }


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: str):
    """Permanently delete a session and its screenshots"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete associated screenshots
    session = sessions[session_id]
    for step in session.get("steps", []):
        screenshot_path = step.get("screenshot")
        if screenshot_path:
            try:
                path = Path(screenshot_path)
                if path.exists():
                    path.unlink()
            except Exception as e:
                print(f"Error deleting screenshot {screenshot_path}: {e}")

    # Remove session from storage
    del sessions[session_id]
    save_sessions()

    return {
        "success": True,
        "session_id": session_id,
        "message": "Session permanently deleted"
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
    save_sessions()

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
    if step_index < len(sessions[session_id]["events"]):
        sessions[session_id]["events"].pop(step_index)

    # Renumber remaining steps
    for i, step in enumerate(sessions[session_id]["steps"]):
        step["id"] = i + 1
        if "event" in step:
            step["event"]["step_id"] = i + 1

    save_sessions()

    return {
        "success": True,
        "deleted_step_id": step_id,
        "remaining_steps": len(sessions[session_id]["steps"])
    }


@app.put("/api/sessions/{session_id}/steps/{step_id}/sub-steps")
def update_sub_steps(session_id: str, step_id: int, request: SubStepsRequest):
    """
    Update sub-steps for a step.

    Args:
        session_id: Session ID
        step_id: Step ID
        request: SubStepsRequest with list of sub-step strings
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    step_index = step_id - 1
    if step_index < 0 or step_index >= len(sessions[session_id]["steps"]):
        raise HTTPException(status_code=404, detail="Step not found")

    # Update sub-steps
    sessions[session_id]["steps"][step_index]["sub_steps"] = request.sub_steps
    save_sessions()

    return {
        "success": True,
        "step_id": step_id,
        "sub_steps": request.sub_steps
    }


@app.post("/api/sessions/{session_id}/steps/reorder")
def reorder_steps(session_id: str, request: ReorderRequest):
    """
    Reorder steps in a session.

    Args:
        session_id: Session ID
        new_order: List of step IDs in the new desired order
                   e.g., [3, 1, 2] moves step 3 to position 1
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    new_order = request.new_order
    steps = sessions[session_id]["steps"]
    events = sessions[session_id]["events"]

    # Validate new_order contains all step IDs
    current_ids = set(s["id"] for s in steps)
    new_order_set = set(new_order)

    if current_ids != new_order_set:
        raise HTTPException(
            status_code=400,
            detail=f"new_order must contain all current step IDs. Expected: {sorted(current_ids)}, Got: {sorted(new_order_set)}"
        )

    # Create mapping from old ID to step/event
    step_map = {s["id"]: s for s in steps}
    event_map = {i + 1: events[i] for i in range(len(events))} if events else {}

    # Reorder steps according to new_order
    new_steps = []
    new_events = []

    for new_pos, old_id in enumerate(new_order, start=1):
        step = step_map[old_id].copy()
        step["id"] = new_pos
        if "event" in step:
            step["event"]["step_id"] = new_pos
        new_steps.append(step)

        if old_id in event_map:
            new_events.append(event_map[old_id])

    sessions[session_id]["steps"] = new_steps
    sessions[session_id]["events"] = new_events
    save_sessions()

    return {
        "success": True,
        "new_order": new_order,
        "steps_count": len(new_steps)
    }


@app.post("/api/sessions/{session_id}/steps")
async def insert_step(
    session_id: str,
    description: str = Form(...),
    position: int = Form(...),
    screenshot: UploadFile = File(...)
):
    """
    Insert a new step at a specific position.

    Args:
        session_id: Session ID
        description: Step description
        position: Position to insert (1-indexed). Use -1 or value > current length for end.
        screenshot: Screenshot image file
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    if not description or not description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty")

    steps = sessions[session_id]["steps"]
    events = sessions[session_id]["events"]

    # Determine insertion index (0-indexed)
    if position < 1 or position > len(steps):
        # Insert at end
        insert_index = len(steps)
    else:
        # Insert before the specified position
        insert_index = position - 1

    # Save screenshot
    temp_step_id = len(steps) + 1
    filename = f"{session_id}_step_{temp_step_id:03d}_{datetime.now().strftime('%H%M%S')}.png"
    filepath = STORAGE_PATH / filename

    with open(filepath, "wb") as f:
        content = await screenshot.read()
        f.write(content)

    # Create new step
    new_step = {
        "id": insert_index + 1,  # Will be renumbered
        "event": {
            "action": "manual_insert",
            "timestamp": datetime.now().isoformat(),
            "screenshot_path": str(filepath),
            "step_id": insert_index + 1
        },
        "screenshot": str(filepath),
        "timestamp": datetime.now().isoformat(),
        "template_description": description.strip(),
        "llm_description": None,
        "final_description": description.strip(),
        "user_edited": True,
        "sub_steps": []
    }

    new_event = {
        "action": "manual_insert",
        "timestamp": datetime.now().isoformat(),
        "screenshot_path": str(filepath)
    }

    # Insert at position
    steps.insert(insert_index, new_step)
    events.insert(insert_index, new_event)

    # Renumber all steps
    for i, step in enumerate(steps):
        step["id"] = i + 1
        if "event" in step:
            step["event"]["step_id"] = i + 1

    save_sessions()

    return {
        "success": True,
        "step_id": insert_index + 1,
        "description": description.strip(),
        "screenshot": str(filepath),
        "total_steps": len(steps)
    }


@app.get("/api/sessions/{session_id}/export/pdf")
def export_pdf(session_id: str):
    """
    Generate and download PDF documentation for the session.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]

    if not session["steps"]:
        raise HTTPException(status_code=400, detail="No steps to export")

    try:
        from weasyprint import HTML, CSS
        import base64
    except ImportError:
        raise HTTPException(status_code=500, detail="WeasyPrint not installed")

    # Build HTML with embedded images
    html_parts = ["""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @page {
            size: A4;
            margin: 1.5cm;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            color: #333;
            line-height: 1.6;
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #667eea;
        }
        h1 {
            color: #667eea;
            margin-bottom: 5px;
        }
        h2 {
            color: #764ba2;
            font-size: 18px;
            font-weight: 500;
            margin-bottom: 15px;
        }
        .meta {
            color: #666;
            font-size: 12px;
        }
        .description {
            color: #555;
            font-size: 13px;
            margin-bottom: 8px;
            font-style: italic;
        }
        .step {
            margin-bottom: 30px;
            page-break-inside: avoid;
        }
        .step-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        .step-number {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 12px;
            flex-shrink: 0;
        }
        .step-title {
            font-size: 16px;
            font-weight: 600;
            color: #333;
        }
        .step-screenshot {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
            margin-top: 10px;
        }
        .step-screenshot img {
            width: 100%;
            height: auto;
            display: block;
        }
        .sub-steps {
            margin-top: 15px;
            padding: 12px 15px;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 3px solid #667eea;
        }
        .sub-steps ul {
            margin: 0;
            padding-left: 20px;
        }
        .sub-steps li {
            color: #444;
            font-size: 13px;
            line-height: 1.6;
            margin-bottom: 6px;
        }
        .sub-steps li:last-child {
            margin-bottom: 0;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            text-align: center;
            color: #999;
            font-size: 10px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        {sub_title_html}
        {description_html}
        <div class="meta">
"""]

    # Get custom title or default
    title = session.get("title", "User Guide")
    sub_title = session.get("sub_title")
    description = session.get("description")

    html_parts[0] = html_parts[0].replace("{title}", title)
    html_parts[0] = html_parts[0].replace("{sub_title_html}", f"<h2>{sub_title}</h2>" if sub_title else "")
    html_parts[0] = html_parts[0].replace("{description_html}", f'<div class="description">{description}</div>' if description else "")

    html_parts.append(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    html_parts.append(f"<br>Total Steps: {len(session['steps'])}")
    html_parts.append("</div></div>")

    # Add each step
    for step in session["steps"]:
        html_parts.append('<div class="step">')
        html_parts.append('<div class="step-header">')
        html_parts.append(f'<span class="step-number">{step["id"]}</span>')
        html_parts.append(f'<span class="step-title">{step["final_description"]}</span>')
        html_parts.append('</div>')

        # Embed screenshot as base64 if it exists
        screenshot_path = step.get("screenshot", "")
        if screenshot_path:
            # Handle both relative and absolute paths
            if not screenshot_path.startswith("/"):
                full_path = STORAGE_PATH.parent / screenshot_path
            else:
                full_path = Path(screenshot_path)

            if full_path.exists():
                with open(full_path, "rb") as img_file:
                    img_data = base64.b64encode(img_file.read()).decode("utf-8")
                html_parts.append('<div class="step-screenshot">')
                html_parts.append(f'<img src="data:image/png;base64,{img_data}" alt="Step {step["id"]}">')
                html_parts.append('</div>')

        # Add sub-steps if present
        sub_steps = step.get("sub_steps", [])
        if sub_steps:
            html_parts.append('<div class="sub-steps"><ul>')
            for sub_step in sub_steps:
                html_parts.append(f'<li>{sub_step}</li>')
            html_parts.append('</ul></div>')

        html_parts.append('</div>')

    html_parts.append("""
    <div class="footer">
        Generated by Demo2PDF - AI-Powered Documentation
    </div>
</body>
</html>
""")

    html_content = "".join(html_parts)

    # Generate PDF
    pdf_filename = f"{session_id}_guide.pdf"
    pdf_path = STORAGE_PATH / pdf_filename

    html_doc = HTML(string=html_content)
    html_doc.write_pdf(pdf_path)

    return FileResponse(
        path=pdf_path,
        filename=f"user_guide_{session_id[:8]}.pdf",
        media_type="application/pdf"
    )


@app.get("/api/sessions/{session_id}/export/simple")
def export_simple_json(session_id: str):
    """
    Export session as JSON (legacy endpoint).
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]

    return {
        "total_steps": len(session["steps"]),
        "steps": [
            {
                "id": s["id"],
                "description": s["final_description"],
                "screenshot": s["screenshot"]
            }
            for s in session["steps"]
        ]
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/sessions/{session_id}/video")
async def upload_video(
    session_id: str,
    video: UploadFile = File(...),
    provider: str = "gemini"
):
    """
    Upload a screen recording video for AI analysis.

    The AI will watch the video and generate step-by-step documentation.

    Args:
        session_id: Session ID
        video: Video file (.mov, .mp4)
        provider: AI provider - "anthropic", "openai", or "gemini"
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # Save video to storage
    video_filename = f"{session_id}_recording.mov"
    video_path = STORAGE_PATH / video_filename

    with open(video_path, "wb") as f:
        content = await video.read()
        f.write(content)

    # Create output directory for extracted frames
    frames_dir = STORAGE_PATH / session_id
    frames_dir.mkdir(exist_ok=True)

    # Analyze video with AI
    try:
        service = VideoAnalysisService(
            provider=provider,
            api_key=sessions[session_id]["config"].get("api_key")
        )

        steps = await service.analyze_video(
            video_path=video_path,
            context=sessions[session_id].get("context"),
            output_dir=frames_dir
        )

        # Convert to session steps format
        for step in steps:
            step_data = {
                "id": step.number,
                "event": {
                    "action": "video_capture",
                    "timestamp": step.timestamp,
                    "video_source": str(video_path)
                },
                "screenshot": step.screenshot_path or "",
                "timestamp": step.timestamp,
                "template_description": None,
                "llm_description": step.description,
                "final_description": step.description,
                "user_edited": False,
                "sub_steps": []
            }
            sessions[session_id]["steps"].append(step_data)
            sessions[session_id]["events"].append(step_data["event"])

        # Store video path in session
        sessions[session_id]["video_path"] = str(video_path)

        return {
            "success": True,
            "step_count": len(steps),
            "video_path": str(video_path),
            "steps": [
                {"number": s.number, "timestamp": s.timestamp, "description": s.description}
                for s in steps
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video analysis failed: {str(e)}")


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
