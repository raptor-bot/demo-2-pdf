# LLM Integration Guide
## Automatic Step Description Generation

**Transform captured user interactions into natural, readable documentation steps**

This guide covers implementing LLM-powered automatic description generation for captured user actions.

---

## Overview

The Demo-to-PDF tool captures raw user events (clicks, inputs, navigation) and uses AI to transform them into clear, professional step-by-step instructions.

### What Gets Generated

**Input (Raw Capture):**
```json
[
  {"action": "click", "element": {"text": "Sign In", "tag": "button"}},
  {"action": "input", "element": {"label": "Email", "value": "user@example.com"}},
  {"action": "input", "element": {"label": "Password", "value": "********"}},
  {"action": "click", "element": {"text": "Login", "tag": "button"}}
]
```

**Output (Generated Steps):**
```
1. Click the Sign In button to open the login form
2. Enter your email address (user@example.com) in the Email field
3. Enter your password in the Password field
4. Click the Login button to sign in
```

---

## Architecture

### Three-Tier Approach

```
┌─────────────────────────────────────────────────────┐
│              TEMPLATE-BASED (Tier 1)                │
│  • Rule-based generation                            │
│  • Free, fast, offline                              │
│  • 70-80% quality                                   │
│  • No API key needed                                │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│              LLM-ENHANCED (Tier 2)                  │
│  • GPT-4o-mini / Claude Haiku                       │
│  • Context-aware, natural language                  │
│  • 90-95% quality                                   │
│  • ~$0.0004 per session                             │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│              LOCAL LLM (Tier 3) - Optional          │
│  • Ollama (llama3, mistral)                         │
│  • Fully private, no API costs                      │
│  • Slower, requires local GPU/CPU                   │
│  • 80-85% quality                                   │
└─────────────────────────────────────────────────────┘
```

---

## Implementation

### 1. Template-Based Generation (Default)

#### backend/src/services/annotation_service.py

```python
from typing import Dict, List, Optional
from datetime import datetime

class TemplateAnnotationService:
    """Generate step descriptions using rule-based templates"""

    def __init__(self):
        self.templates = {
            "click": self._generate_click_description,
            "input": self._generate_input_description,
            "select": self._generate_select_description,
            "navigate": self._generate_navigate_description,
            "scroll": self._generate_scroll_description
        }

    def generate_description(self, event: Dict) -> str:
        """Generate description for a single event"""
        action = event.get("action", "unknown")
        generator = self.templates.get(action, self._generate_default)
        return generator(event)

    def generate_batch_descriptions(self, events: List[Dict]) -> List[str]:
        """Generate descriptions for multiple events with context"""
        descriptions = []

        for i, event in enumerate(events):
            # Check if this is part of a form fill sequence
            if self._is_form_sequence(events, i):
                grouped = self._group_form_inputs(events, i)
                descriptions.append(self._generate_form_description(grouped))
                # Skip the events we just grouped
                i += len(grouped) - 1
            else:
                descriptions.append(self.generate_description(event))

        return descriptions

    def _generate_click_description(self, event: Dict) -> str:
        """Generate description for click event"""
        element = event.get("element", {})
        text = element.get("text", "").strip()
        tag = element.get("tag", "").lower()
        element_type = element.get("type", "")

        # Determine what kind of clickable element
        if tag == "button":
            return f"Click the '{text}' button"
        elif tag == "a":
            return f"Click the '{text}' link"
        elif tag == "input" and element_type == "submit":
            return f"Click the '{text or 'Submit'}' button"
        elif tag == "input" and element_type == "checkbox":
            return f"Check the '{text}' checkbox"
        elif tag == "input" and element_type == "radio":
            return f"Select the '{text}' option"
        else:
            return f"Click on '{text or element.get('id', 'the element')}'"

    def _generate_input_description(self, event: Dict) -> str:
        """Generate description for input event"""
        element = event.get("element", {})
        label = element.get("label") or element.get("placeholder") or element.get("name", "field")
        value = element.get("value", "")
        input_type = element.get("type", "text")

        # Mask sensitive fields
        if input_type == "password" or "password" in label.lower():
            return f"Enter your password in the {label} field"
        elif input_type == "email":
            return f"Enter your email address ({value}) in the {label} field"
        elif "email" in label.lower():
            return f"Enter your email ({value}) in the {label} field"
        else:
            return f"Enter '{value}' in the {label} field"

    def _generate_select_description(self, event: Dict) -> str:
        """Generate description for select/dropdown event"""
        element = event.get("element", {})
        label = element.get("label") or element.get("name", "dropdown")
        value = element.get("value", "")

        return f"Select '{value}' from the {label} dropdown"

    def _generate_navigate_description(self, event: Dict) -> str:
        """Generate description for navigation event"""
        url = event.get("url", "")
        page_title = event.get("page_title", "")

        if page_title:
            return f"Navigate to the {page_title} page"
        else:
            return f"Navigate to {url}"

    def _generate_scroll_description(self, event: Dict) -> str:
        """Generate description for scroll event"""
        direction = event.get("direction", "down")
        return f"Scroll {direction} the page"

    def _generate_default(self, event: Dict) -> str:
        """Fallback for unknown event types"""
        action = event.get("action", "unknown action")
        return f"Perform {action}"

    def _is_form_sequence(self, events: List[Dict], start_idx: int) -> bool:
        """Check if current event is start of a form fill sequence"""
        if start_idx >= len(events) - 1:
            return False

        # Check if next few events are also inputs
        input_count = 0
        for i in range(start_idx, min(start_idx + 5, len(events))):
            if events[i].get("action") == "input":
                input_count += 1
            else:
                break

        return input_count >= 3  # 3 or more consecutive inputs = form

    def _group_form_inputs(self, events: List[Dict], start_idx: int) -> List[Dict]:
        """Group consecutive input events"""
        grouped = []
        for i in range(start_idx, len(events)):
            if events[i].get("action") == "input":
                grouped.append(events[i])
            else:
                break
        return grouped

    def _generate_form_description(self, input_events: List[Dict]) -> str:
        """Generate description for grouped form inputs"""
        fields = []
        for event in input_events:
            element = event.get("element", {})
            label = element.get("label") or element.get("name", "field")
            value = element.get("value", "")

            # Mask passwords
            if element.get("type") == "password":
                fields.append(f"  - {label}: [password]")
            else:
                fields.append(f"  - {label}: {value}")

        return "Fill out the form with the following information:\n" + "\n".join(fields)
```

### 2. LLM-Enhanced Generation

#### backend/src/services/llm_annotation_service.py

```python
from typing import Dict, List, Optional
import os
from openai import OpenAI
from anthropic import Anthropic

class LLMAnnotationService:
    """Generate step descriptions using LLM APIs"""

    def __init__(
        self,
        provider: str = "openai",  # "openai", "anthropic", or "ollama"
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.provider = provider
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")

        # Initialize client based on provider
        if provider == "openai":
            self.client = OpenAI(api_key=self.api_key)
            self.model = model or "gpt-4o-mini"
        elif provider == "anthropic":
            self.client = Anthropic(api_key=self.api_key)
            self.model = model or "claude-3-5-haiku-20241022"
        elif provider == "ollama":
            # Local Ollama doesn't need API key
            self.model = model or "llama3"
            self.base_url = "http://localhost:11434"
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def generate_descriptions(
        self,
        events: List[Dict],
        context: Optional[str] = None
    ) -> List[str]:
        """Generate natural language descriptions for captured events"""

        # Format events for LLM
        events_text = self._format_events(events)

        # Build prompt
        prompt = self._build_prompt(events_text, context)

        # Generate descriptions
        if self.provider == "openai":
            return self._generate_openai(prompt)
        elif self.provider == "anthropic":
            return self._generate_anthropic(prompt)
        elif self.provider == "ollama":
            return self._generate_ollama(prompt)

    def _format_events(self, events: List[Dict]) -> str:
        """Format events into readable text for LLM"""
        formatted_events = []

        for i, event in enumerate(events, 1):
            action = event.get("action", "unknown")
            element = event.get("element", {})
            url = event.get("url", "")

            if action == "click":
                text = element.get("text", element.get("id", "element"))
                tag = element.get("tag", "element")
                formatted_events.append(
                    f"{i}. User clicked on {tag} with text '{text}'"
                )

            elif action == "input":
                label = element.get("label") or element.get("name", "field")
                value = element.get("value", "")
                input_type = element.get("type", "text")

                if input_type == "password":
                    formatted_events.append(
                        f"{i}. User entered password into '{label}' field"
                    )
                else:
                    formatted_events.append(
                        f"{i}. User typed '{value}' into '{label}' field"
                    )

            elif action == "select":
                label = element.get("label") or element.get("name", "dropdown")
                value = element.get("value", "")
                formatted_events.append(
                    f"{i}. User selected '{value}' from '{label}' dropdown"
                )

            elif action == "navigate":
                page_title = event.get("page_title", "")
                formatted_events.append(
                    f"{i}. User navigated to: {page_title or url}"
                )

            else:
                formatted_events.append(
                    f"{i}. User performed action: {action}"
                )

        return "\n".join(formatted_events)

    def _build_prompt(self, events_text: str, context: Optional[str]) -> str:
        """Build prompt for LLM"""

        system_context = context or "a web application"

        prompt = f"""You are a technical documentation expert. Your task is to convert captured user interactions into clear, professional step-by-step instructions for a user guide.

Context: The user is documenting {system_context}.

Captured User Actions:
{events_text}

Generate clear, numbered step-by-step instructions following these guidelines:

1. Use active voice and imperative mood (e.g., "Click the Submit button")
2. Be specific but concise
3. Group related actions when appropriate (e.g., multiple form fields)
4. Use natural, user-friendly language
5. Include relevant details (button names, field values) but avoid technical jargon
6. For passwords or sensitive data, just say "Enter your password" without the value
7. Number each step
8. Keep each step to one sentence when possible

Output only the numbered steps, nothing else."""

        return prompt

    def _generate_openai(self, prompt: str) -> List[str]:
        """Generate descriptions using OpenAI API"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a technical documentation expert specializing in creating clear, user-friendly instructions."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,  # Lower temperature for more consistent output
            max_tokens=1000
        )

        content = response.choices[0].message.content
        return self._parse_steps(content)

    def _generate_anthropic(self, prompt: str) -> List[str]:
        """Generate descriptions using Anthropic Claude API"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            temperature=0.3,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = response.content[0].text
        return self._parse_steps(content)

    def _generate_ollama(self, prompt: str) -> List[str]:
        """Generate descriptions using local Ollama"""
        import requests

        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
        )

        if response.status_code == 200:
            content = response.json().get("response", "")
            return self._parse_steps(content)
        else:
            raise Exception(f"Ollama API error: {response.status_code}")

    def _parse_steps(self, content: str) -> List[str]:
        """Parse numbered steps from LLM output"""
        lines = content.strip().split("\n")
        steps = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Remove numbering (e.g., "1.", "1)", "Step 1:", etc.)
            import re
            line = re.sub(r'^\d+[\.):\-]\s*', '', line)
            line = re.sub(r'^Step\s+\d+[\:):\-]\s*', '', line, flags=re.IGNORECASE)

            if line:
                steps.append(line)

        return steps


class HybridAnnotationService:
    """Combine template-based and LLM-based generation"""

    def __init__(
        self,
        use_llm: bool = False,
        llm_provider: str = "openai",
        api_key: Optional[str] = None
    ):
        self.template_service = TemplateAnnotationService()
        self.use_llm = use_llm

        if use_llm:
            self.llm_service = LLMAnnotationService(
                provider=llm_provider,
                api_key=api_key
            )

    def generate_descriptions(
        self,
        events: List[Dict],
        context: Optional[str] = None
    ) -> List[Dict]:
        """Generate descriptions with both template and optional LLM"""

        results = []

        for event in events:
            # Always generate template-based description
            template_desc = self.template_service.generate_description(event)

            result = {
                "event": event,
                "template_description": template_desc,
                "llm_description": None,
                "final_description": template_desc
            }

            results.append(result)

        # If LLM is enabled, enhance descriptions
        if self.use_llm:
            try:
                llm_descriptions = self.llm_service.generate_descriptions(
                    events,
                    context
                )

                # Update results with LLM descriptions
                for i, desc in enumerate(llm_descriptions):
                    if i < len(results):
                        results[i]["llm_description"] = desc
                        results[i]["final_description"] = desc

            except Exception as e:
                # Fall back to template descriptions if LLM fails
                print(f"LLM generation failed, using templates: {e}")

        return results
```

### 3. API Integration

#### backend/main.py (Updated)

```python
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import uuid
from datetime import datetime
from typing import Optional
from src.services.llm_annotation_service import HybridAnnotationService

app = FastAPI(title="Demo2PDF API with LLM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STORAGE_PATH = Path("storage")
STORAGE_PATH.mkdir(exist_ok=True)

sessions = {}

# Initialize annotation service
annotation_service = HybridAnnotationService(
    use_llm=False  # Default to template-based, can be enabled per request
)

@app.post("/api/sessions")
def create_session(
    use_llm: bool = False,
    llm_provider: str = "openai",
    api_key: Optional[str] = None
):
    """Create new capture session with optional LLM configuration"""
    session_id = str(uuid.uuid4())

    # Create session-specific annotation service
    service_config = {
        "use_llm": use_llm,
        "llm_provider": llm_provider
    }

    if api_key:
        service_config["api_key"] = api_key

    sessions[session_id] = {
        "id": session_id,
        "created_at": datetime.now().isoformat(),
        "steps": [],
        "events": [],
        "config": service_config
    }

    return sessions[session_id]

@app.post("/api/sessions/{session_id}/events")
async def add_event(
    session_id: str,
    event_data: str = Form(...),
    screenshot: UploadFile = File(...)
):
    """Add captured event to session"""
    if session_id not in sessions:
        return {"error": "Session not found"}, 404

    # Parse event data
    event = json.loads(event_data)

    # Save screenshot
    step_id = len(sessions[session_id]["events"]) + 1
    filename = f"{session_id}_step_{step_id}.png"
    filepath = STORAGE_PATH / filename

    with open(filepath, "wb") as f:
        content = await screenshot.read()
        f.write(content)

    event["screenshot_path"] = str(filepath)
    event["step_id"] = step_id

    # Add to events
    sessions[session_id]["events"].append(event)

    # Generate description immediately
    config = sessions[session_id]["config"]
    service = HybridAnnotationService(**config)

    descriptions = service.generate_descriptions([event])
    description_result = descriptions[0]

    # Create step with description
    step = {
        "id": step_id,
        "event": event,
        "screenshot": str(filepath),
        "timestamp": event.get("timestamp"),
        "template_description": description_result["template_description"],
        "llm_description": description_result.get("llm_description"),
        "final_description": description_result["final_description"]
    }

    sessions[session_id]["steps"].append(step)

    return step

@app.post("/api/sessions/{session_id}/regenerate")
def regenerate_descriptions(
    session_id: str,
    use_llm: bool = True,
    llm_provider: str = "openai",
    api_key: Optional[str] = None
):
    """Regenerate all descriptions for a session"""
    if session_id not in sessions:
        return {"error": "Session not found"}, 404

    # Create new annotation service with requested config
    service = HybridAnnotationService(
        use_llm=use_llm,
        llm_provider=llm_provider,
        api_key=api_key
    )

    # Get all events
    events = sessions[session_id]["events"]

    # Regenerate descriptions
    descriptions = service.generate_descriptions(events)

    # Update steps
    for i, desc_result in enumerate(descriptions):
        if i < len(sessions[session_id]["steps"]):
            sessions[session_id]["steps"][i].update({
                "template_description": desc_result["template_description"],
                "llm_description": desc_result.get("llm_description"),
                "final_description": desc_result["final_description"]
            })

    return {
        "success": True,
        "steps_updated": len(descriptions),
        "steps": sessions[session_id]["steps"]
    }

@app.get("/api/sessions/{session_id}")
def get_session(session_id: str):
    """Get session with all steps and descriptions"""
    if session_id not in sessions:
        return {"error": "Session not found"}, 404
    return sessions[session_id]
```

---

## Configuration

### Environment Variables

#### backend/.env

```env
# LLM Provider Configuration
ENABLE_LLM_DESCRIPTIONS=false
LLM_PROVIDER=openai  # "openai", "anthropic", or "ollama"

# API Keys
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Model Selection
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_MODEL=claude-3-5-haiku-20241022
OLLAMA_MODEL=llama3

# LLM Parameters
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=1000

# Privacy Settings
MASK_SENSITIVE_DATA=true
SENSITIVE_FIELDS=password,ssn,credit-card,cvv,pin

# Cost Control
MAX_LLM_CALLS_PER_SESSION=100
ENABLE_LLM_CACHING=true
```

---

## Usage Examples

### Example 1: Template-Based (Default)

```python
# Start session without LLM
response = requests.post("http://localhost:8000/api/sessions", json={
    "use_llm": False
})
session = response.json()

# Capture events - descriptions generated with templates
# Fast, free, offline
```

### Example 2: OpenAI GPT-4o-mini

```python
# Start session with OpenAI
response = requests.post("http://localhost:8000/api/sessions", json={
    "use_llm": True,
    "llm_provider": "openai",
    "api_key": "sk-your-key-here"  # Or use env variable
})
session = response.json()

# Capture events - descriptions enhanced by GPT-4o-mini
# Natural language, context-aware
# Cost: ~$0.0004 per session
```

### Example 3: Claude Haiku

```python
# Start session with Anthropic Claude
response = requests.post("http://localhost:8000/api/sessions", json={
    "use_llm": True,
    "llm_provider": "anthropic",
    "api_key": "sk-ant-your-key-here"
})
session = response.json()

# Capture events - descriptions by Claude Haiku
# Excellent quality, slightly different style
# Cost: ~$0.0005 per session
```

### Example 4: Local Ollama (Privacy-First)

```bash
# First, start Ollama locally
ollama serve

# Pull a model
ollama pull llama3
```

```python
# Start session with local Ollama
response = requests.post("http://localhost:8000/api/sessions", json={
    "use_llm": True,
    "llm_provider": "ollama"
    # No API key needed!
})
session = response.json()

# Capture events - descriptions by local LLM
# Fully private, no API costs
# Slower (depends on hardware)
```

### Example 5: Regenerate with Different Provider

```python
# Capture session with templates first (fast)
session_id = "abc-123"

# Later, regenerate with LLM for better quality
response = requests.post(
    f"http://localhost:8000/api/sessions/{session_id}/regenerate",
    json={
        "use_llm": True,
        "llm_provider": "openai",
        "api_key": "sk-your-key-here"
    }
)

# Now all steps have LLM-enhanced descriptions
```

---

## Cost Analysis

### OpenAI GPT-4o-mini Pricing

| Metric | Cost |
|--------|------|
| Input tokens | $0.150 per 1M tokens |
| Output tokens | $0.600 per 1M tokens |

**Typical session (20 steps):**
- Input: ~500 tokens × $0.150/1M = $0.000075
- Output: ~500 tokens × $0.600/1M = $0.000300
- **Total: ~$0.000375 per session**

**Monthly estimates:**
- 10 sessions: $0.004
- 100 sessions: $0.04
- 1,000 sessions: $0.38
- 10,000 sessions: $3.75

### Anthropic Claude Haiku Pricing

| Metric | Cost |
|--------|------|
| Input tokens | $0.25 per 1M tokens |
| Output tokens | $1.25 per 1M tokens |

**Typical session (20 steps):**
- Total: ~$0.000625 per session

**Monthly estimates:**
- 100 sessions: $0.06
- 1,000 sessions: $0.63

### Ollama (Local)

**Cost: $0** (electricity costs negligible)
**Tradeoff:** Requires local hardware, slower than cloud APIs

---

## Best Practices

### 1. Start with Templates, Upgrade Selectively

```python
# Default to template-based
session = create_session(use_llm=False)

# After capturing, let user choose to upgrade
if user_wants_better_quality:
    regenerate_with_llm(session_id)
```

### 2. Batch Processing for Cost Efficiency

```python
# Instead of calling LLM per event, batch all events
events = capture_all_events()  # Capture 20 events

# Single LLM call for all events (more efficient)
descriptions = llm_service.generate_descriptions(events)
```

### 3. Cache Common Patterns

```python
# Cache descriptions for common UI patterns
cache = {
    "click:login:button": "Click the Login button",
    "input:email:field": "Enter your email address",
    # ...
}

# Check cache before calling LLM
cache_key = f"{action}:{element_id}:{element_type}"
if cache_key in cache:
    return cache[cache_key]
else:
    return llm_service.generate(event)
```

### 4. Provide Context for Better Results

```python
# Give LLM context about the application
context = "an e-commerce checkout flow"

descriptions = llm_service.generate_descriptions(
    events,
    context=context
)

# Results in more specific descriptions:
# "Click Continue to Shipping" vs "Click the Continue button"
```

### 5. Let Users Edit After Generation

```python
# Generate descriptions automatically
auto_description = generate_description(event)

# But always allow manual override
step = {
    "auto_description": auto_description,
    "user_description": None,  # User can edit
    "final_description": auto_description  # Use auto unless edited
}
```

---

## Prompt Engineering Tips

### Improve Quality with Better Prompts

#### Basic Prompt (70% quality)
```
Convert these events to steps:
1. Clicked "Login"
2. Typed "user@example.com" in email
```

#### Enhanced Prompt (90% quality)
```
You are a technical writer creating user documentation.

Context: E-commerce checkout process
User persona: Non-technical end user
Tone: Friendly, clear, action-oriented

Convert these interactions into numbered steps:
1. Clicked "Login" button
2. Entered "user@example.com" in "Email Address" field

Guidelines:
- Start each step with an action verb
- Include specific button/field names
- Be concise but clear
- Use consistent terminology
```

### Application-Specific Prompts

```python
def get_prompt_for_app_type(app_type: str) -> str:
    prompts = {
        "ecommerce": "You are documenting an e-commerce platform...",
        "admin": "You are documenting an admin dashboard...",
        "saas": "You are documenting a SaaS application...",
    }
    return prompts.get(app_type, "You are documenting a web application...")
```

---

## Testing

### Unit Tests

```python
# tests/test_annotation_service.py

def test_template_click_description():
    service = TemplateAnnotationService()

    event = {
        "action": "click",
        "element": {"tag": "button", "text": "Submit"}
    }

    desc = service.generate_description(event)
    assert desc == "Click the 'Submit' button"

def test_llm_generation():
    service = LLMAnnotationService(provider="openai")

    events = [
        {"action": "click", "element": {"text": "Login", "tag": "button"}},
        {"action": "input", "element": {"label": "Email", "value": "test@example.com"}}
    ]

    descriptions = service.generate_descriptions(events)

    assert len(descriptions) == 2
    assert "login" in descriptions[0].lower()
    assert "email" in descriptions[1].lower()
```

---

## Troubleshooting

### Issue: LLM calls failing

**Check:**
1. API key is correct and has credits
2. Network connectivity to API endpoint
3. Rate limits not exceeded

**Solution:**
```python
# Add retry logic with exponential backoff
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_with_retry(self, events):
    return self.llm_service.generate_descriptions(events)
```

### Issue: Descriptions not natural enough

**Check:**
1. Event data includes enough context (labels, text, etc.)
2. Prompt is clear and specific
3. Temperature not too high (keep at 0.3)

**Solution:**
- Enhance event capture to include more metadata
- Improve prompt with examples
- Consider using GPT-4 instead of GPT-4o-mini

### Issue: Cost too high

**Solutions:**
1. Use template-based as default, LLM on-demand
2. Batch events into single request
3. Cache common patterns
4. Use local Ollama for development

---

## Next Steps

1. **Test with real applications** - Capture actual user flows
2. **Collect feedback** - Iterate on prompt engineering
3. **Build UI controls** - Let users toggle LLM on/off
4. **Add analytics** - Track which descriptions users edit most
5. **Fine-tune** - Consider fine-tuning a model on your specific domain

---

**Last Updated:** November 13, 2025
**Version:** 1.0
