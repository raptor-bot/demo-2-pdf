# Fix for OpenAI SDK Version Compatibility Error

## Problem

Getting this error when clicking "Enhance with AI":
```
TypeError: Client.__init__() got an unexpected keyword argument 'proxies'
```

## Root Cause

Version incompatibility between OpenAI SDK and httpx library. The older OpenAI version (1.12.0) doesn't work well with newer httpx versions.

## Solution

### 1. Updated requirements.txt

Changed:
```txt
openai==1.12.0      # Old version
anthropic==0.18.1   # Old version
```

To:
```txt
openai==1.54.0      # Latest stable version
anthropic==0.39.0   # Latest stable version
httpx==0.27.0       # Explicit version for compatibility
```

### 2. Added Better Error Handling

Updated `llm_annotation_service.py` to:
- Wrap SDK initialization in try-catch
- Provide clear error messages
- Help users troubleshoot issues

## How to Fix

### Method 1: Reinstall Dependencies (Recommended)

```bash
cd backend

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows

# Upgrade packages
pip install --upgrade openai anthropic httpx

# Or reinstall all
pip install -r requirements.txt --upgrade
```

### Method 2: Fresh Virtual Environment

If you still have issues:

```bash
cd backend

# Remove old venv
rm -rf venv

# Create new one
python3 -m venv venv
source venv/bin/activate

# Install fresh
pip install -r requirements.txt
```

### Method 3: Use Ollama Instead (No OpenAI Needed)

If you want to avoid API keys entirely:

```bash
# Install Ollama
# macOS: brew install ollama
# Linux: curl https://ollama.ai/install.sh | sh
# Windows: https://ollama.ai/download

# Start Ollama
ollama serve

# Pull model (in another terminal)
ollama pull llama3

# Now use Ollama in the extension
# Select "Ollama (Local)" from dropdown
# No API key needed!
```

## Testing After Fix

```bash
# 1. Restart backend
cd backend
source venv/bin/activate
python main.py

# 2. Test API directly
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "use_llm": true,
    "llm_provider": "openai",
    "api_key": "your-key-here"
  }'

# Should return session ID without errors
```

## Alternative: Skip AI Enhancement for Now

If you just want to test the core functionality:

1. **Capture with templates** (default, no API key needed)
2. **View in beautiful viewer**
3. **Test AI enhancement later** when dependencies are fixed

Templates still give you 70-80% quality descriptions!

## Expected Behavior After Fix

### Before Fix ❌
```
Click "Enhance with AI"
→ TypeError: unexpected keyword argument 'proxies'
→ 500 Server Error
```

### After Fix ✅
```
Click "Enhance with AI"
→ Enter API key (or use .env)
→ Descriptions regenerate successfully
→ Page reloads with AI-enhanced descriptions
```

## Verification

After updating, you should be able to:

1. ✅ Start backend without errors
2. ✅ Create sessions with `use_llm=true`
3. ✅ Click "Enhance with AI" in viewer
4. ✅ See regenerated descriptions

## Quick Test Script

```python
# test_llm.py
from openai import OpenAI

try:
    client = OpenAI(api_key="your-key-here")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=10
    )
    print("✅ OpenAI SDK working!")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"❌ Error: {e}")
```

Run:
```bash
cd backend
source venv/bin/activate
python test_llm.py
```

## Need More Help?

If you're still having issues:

1. **Check Python version:** `python --version` (should be 3.11+)
2. **Check pip version:** `pip --version`
3. **Clear pip cache:** `pip cache purge`
4. **Try a different provider:** Use Anthropic or Ollama instead

---

**Status:** Fixed in latest commit
**Version:** Added explicit httpx==0.27.0 for compatibility
