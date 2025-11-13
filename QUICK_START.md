# Quick Start Guide
## Get Demo-to-PDF Running in 15 Minutes

This guide will get you from zero to a working prototype capturing browser actions and generating PDFs.

---

## Step 1: Prerequisites (2 minutes)

Install required tools:

```bash
# Check if already installed
node --version    # Need 18+
python --version  # Need 3.11+
git --version

# Install if missing:
# Node.js: https://nodejs.org/
# Python: https://www.python.org/downloads/
# Git: https://git-scm.com/downloads
```

---

## Step 2: Clone & Setup (3 minutes)

```bash
# Clone repository
git clone <your-repo-url>
cd demo-2-pdf

# Create basic structure
mkdir -p backend/src backend/storage backend/tests
mkdir -p extension/src extension/assets
mkdir -p editor/src
```

---

## Step 3: Backend Minimal Setup (4 minutes)

Create the essential backend files:

### backend/requirements.txt
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
pillow==10.2.0
weasyprint==60.2
jinja2==3.1.3
pydantic==2.5.3
```

### backend/main.py
```python
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import uuid
from datetime import datetime

app = FastAPI(title="Demo2PDF API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STORAGE_PATH = Path("storage")
STORAGE_PATH.mkdir(exist_ok=True)

# In-memory storage (use DB later)
sessions = {}

@app.get("/")
def read_root():
    return {"message": "Demo2PDF API is running", "version": "0.1.0"}

@app.post("/api/sessions")
def create_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "id": session_id,
        "created_at": datetime.now().isoformat(),
        "steps": []
    }
    return sessions[session_id]

@app.get("/api/sessions/{session_id}")
def get_session(session_id: str):
    if session_id not in sessions:
        return {"error": "Session not found"}, 404
    return sessions[session_id]

@app.post("/api/sessions/{session_id}/steps")
async def add_step(session_id: str, screenshot: UploadFile = File(...)):
    if session_id not in sessions:
        return {"error": "Session not found"}, 404

    # Save screenshot
    step_id = len(sessions[session_id]["steps"]) + 1
    filename = f"{session_id}_step_{step_id}.png"
    filepath = STORAGE_PATH / filename

    with open(filepath, "wb") as f:
        content = await screenshot.read()
        f.write(content)

    # Add step
    step = {
        "id": step_id,
        "screenshot": str(filepath),
        "timestamp": datetime.now().isoformat()
    }
    sessions[session_id]["steps"].append(step)

    return step

@app.get("/api/sessions/{session_id}/export")
def export_pdf(session_id: str):
    """Generate PDF (placeholder - implement later)"""
    if session_id not in sessions:
        return {"error": "Session not found"}, 404

    return {"message": "PDF generation coming soon", "steps": len(sessions[session_id]["steps"])}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Install and Run

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
python main.py
```

**✓ Backend should be running at http://localhost:8000**

Test it: Open http://localhost:8000 in your browser

---

## Step 4: Browser Extension Minimal Setup (4 minutes)

Create minimal extension files:

### extension/manifest.json
```json
{
  "manifest_version": 3,
  "name": "Demo2PDF (Dev)",
  "version": "0.1.0",
  "description": "Capture and convert to PDF",
  "permissions": ["activeTab", "storage"],
  "action": {
    "default_popup": "popup.html"
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content-script.js"]
    }
  ],
  "background": {
    "service_worker": "background.js"
  }
}
```

### extension/popup.html
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {
      width: 300px;
      padding: 20px;
      font-family: Arial, sans-serif;
    }
    button {
      width: 100%;
      padding: 10px;
      margin: 5px 0;
      font-size: 14px;
      cursor: pointer;
    }
    .recording { background: #ff4444; color: white; }
    .start { background: #44ff44; }
    .stop { background: #ff4444; color: white; }
    #status {
      padding: 10px;
      margin: 10px 0;
      background: #f0f0f0;
      border-radius: 4px;
    }
  </style>
</head>
<body>
  <h2>Demo2PDF</h2>
  <div id="status">Not recording</div>
  <button id="startBtn" class="start">Start Recording</button>
  <button id="stopBtn" class="stop" style="display:none;">Stop Recording</button>
  <div id="stepCount" style="margin-top: 10px;"></div>
  <script src="popup.js"></script>
</body>
</html>
```

### extension/popup.js
```javascript
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const status = document.getElementById('status');
const stepCount = document.getElementById('stepCount');

// Check recording state on load
chrome.storage.local.get(['recording', 'sessionId', 'stepCount'], (data) => {
  if (data.recording) {
    updateUIRecording(data.sessionId, data.stepCount || 0);
  }
});

startBtn.addEventListener('click', async () => {
  // Create new session
  const response = await fetch('http://localhost:8000/api/sessions', {
    method: 'POST'
  });
  const session = await response.json();

  // Save session ID
  chrome.storage.local.set({
    recording: true,
    sessionId: session.id,
    stepCount: 0
  });

  // Notify content script
  chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
    chrome.tabs.sendMessage(tabs[0].id, {
      action: 'startRecording',
      sessionId: session.id
    });
  });

  updateUIRecording(session.id, 0);
});

stopBtn.addEventListener('click', () => {
  chrome.storage.local.set({ recording: false });

  chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
    chrome.tabs.sendMessage(tabs[0].id, { action: 'stopRecording' });
  });

  updateUIStopped();
});

function updateUIRecording(sessionId, count) {
  status.textContent = `Recording... (Session: ${sessionId.substring(0, 8)})`;
  status.style.background = '#ffeeee';
  startBtn.style.display = 'none';
  stopBtn.style.display = 'block';
  stepCount.textContent = `Steps captured: ${count}`;
}

function updateUIStopped() {
  status.textContent = 'Not recording';
  status.style.background = '#f0f0f0';
  startBtn.style.display = 'block';
  stopBtn.style.display = 'none';
}
```

### extension/content-script.js
```javascript
let recording = false;
let sessionId = null;

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'startRecording') {
    recording = true;
    sessionId = message.sessionId;
    console.log('[Demo2PDF] Recording started');
  } else if (message.action === 'stopRecording') {
    recording = false;
    console.log('[Demo2PDF] Recording stopped');
  }
});

// Capture clicks
document.addEventListener('click', async (event) => {
  if (!recording) return;

  console.log('[Demo2PDF] Click captured:', event.target);

  // Wait a moment for UI to update
  await new Promise(resolve => setTimeout(resolve, 300));

  // Capture screenshot
  captureAndSend();
}, true);

async function captureAndSend() {
  // Get screenshot via background script
  chrome.runtime.sendMessage({
    action: 'captureScreenshot',
    sessionId: sessionId
  });
}
```

### extension/background.js
```javascript
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'captureScreenshot') {
    chrome.tabs.captureVisibleTab(null, { format: 'png' }, async (dataUrl) => {
      // Convert data URL to blob
      const response = await fetch(dataUrl);
      const blob = await response.blob();

      // Send to backend
      const formData = new FormData();
      formData.append('screenshot', blob, 'screenshot.png');

      try {
        await fetch(`http://localhost:8000/api/sessions/${message.sessionId}/steps`, {
          method: 'POST',
          body: formData
        });

        // Update step count
        chrome.storage.local.get(['stepCount'], (data) => {
          const newCount = (data.stepCount || 0) + 1;
          chrome.storage.local.set({ stepCount: newCount });
        });

        console.log('[Demo2PDF] Screenshot sent to backend');
      } catch (error) {
        console.error('[Demo2PDF] Failed to send screenshot:', error);
      }
    });
  }
});
```

### Load Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (top right)
3. Click "Load unpacked"
4. Select the `extension` folder
5. Pin the extension to toolbar

**✓ Extension is now loaded!**

---

## Step 5: Test It! (2 minutes)

1. **Open any website** (e.g., https://example.com)

2. **Click the extension icon** in the toolbar

3. **Click "Start Recording"**

4. **Click around the page** - each click captures a screenshot

5. **Click "Stop Recording"** in the extension popup

6. **Check backend** to see captured data:
   ```bash
   # In a new terminal
   curl http://localhost:8000/api/sessions
   ```

7. **View screenshots**:
   ```bash
   ls backend/storage/
   # You should see PNG files
   ```

**🎉 You now have a working capture system!**

---

## What You've Built

```
✓ Backend API receiving screenshots
✓ Browser extension capturing user clicks
✓ Screenshots saved to disk
✓ Session management
```

---

## Next Steps

### Immediate Enhancements (Next 30 minutes)

1. **Add PDF Export**
   ```python
   # In backend/main.py, replace export_pdf function:
   from weasyprint import HTML

   @app.get("/api/sessions/{session_id}/export")
   def export_pdf(session_id: str):
       if session_id not in sessions:
           return {"error": "Session not found"}, 404

       session = sessions[session_id]

       # Generate simple HTML
       html = "<html><body><h1>Captured Steps</h1>"
       for step in session["steps"]:
           html += f'<div><h2>Step {step["id"]}</h2>'
           html += f'<img src="{step["screenshot"]}" width="800"/></div>'
       html += "</body></html>"

       # Generate PDF
       pdf_path = STORAGE_PATH / f"{session_id}.pdf"
       HTML(string=html).write_pdf(pdf_path)

       return {"pdf_path": str(pdf_path)}
   ```

2. **Add More Event Types**
   - Form inputs
   - Navigation changes
   - Scroll events

3. **Build Simple Editor UI**
   - React app to view and edit steps
   - See PROJECT_STRUCTURE.md for full setup

### Long-term Improvements

- Read FEASIBILITY_ANALYSIS.md for detailed architecture
- Read ARCHITECTURE_RECOMMENDATION.md for production setup
- Implement features from Phase 2-4

---

## Troubleshooting

### "CORS error" in browser console
- Make sure backend is running on port 8000
- Check CORSMiddleware is configured in main.py

### "Extension not capturing clicks"
- Open DevTools (F12) and check Console tab for errors
- Verify extension is enabled in chrome://extensions/
- Reload the extension after code changes

### "Module not found" errors
- Activate virtual environment: `source venv/bin/activate`
- Reinstall requirements: `pip install -r requirements.txt`

### Screenshots not appearing in storage/
- Check backend logs for errors
- Verify storage/ directory exists
- Check file permissions

---

## Development Tips

### Watch backend logs
```bash
cd backend
python main.py
# You'll see requests in real-time
```

### Debug extension
1. Right-click extension icon → "Inspect popup"
2. Go to chrome://extensions/
3. Click "background page" or "service worker" to see logs
4. On any page, open DevTools → Console (for content-script logs)

### Quick restart
```bash
# Backend: Ctrl+C then re-run
python backend/main.py

# Extension: Click reload button in chrome://extensions/
```

---

## Summary

You've built a working MVP that:
- Captures browser interactions
- Takes screenshots automatically
- Saves data to a backend
- Has a basic session management system

**Total time:** ~15 minutes
**Lines of code:** ~200
**Fully functional:** ✓

---

**Ready for more?** Check out:
- ARCHITECTURE_RECOMMENDATION.md - Production architecture
- PROJECT_STRUCTURE.md - Complete project setup
- FEASIBILITY_ANALYSIS.md - Detailed technical analysis

**Happy coding! 🚀**
