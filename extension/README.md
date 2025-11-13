# Demo2PDF Browser Extension

Capture user interactions and automatically generate step descriptions.

## Installation

### For Chrome/Edge

1. Open `chrome://extensions/` in your browser
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `extension` folder
5. Pin the extension to your toolbar (optional but recommended)

### For Firefox

1. Open `about:debugging#/runtime/this-firefox`
2. Click "Load Temporary Add-on"
3. Navigate to the `extension` folder and select `manifest.json`

## Usage

1. **Start Backend**: Make sure the backend server is running at `http://localhost:8000`

2. **Click Extension Icon**: Open the Demo2PDF popup

3. **Configure**:
   - Choose whether to use AI descriptions (requires API key)
   - Select AI provider (OpenAI, Anthropic, or local Ollama)

4. **Start Recording**: Click "Start Recording"

5. **Perform Actions**: Click, type, navigate on the webpage

6. **Stop Recording**: Click "Stop Recording" or click the red indicator on the page

7. **View Results**: Click "View Session" or go to `http://localhost:8000/docs`

## Features

- 🎯 **Automatic Event Capture**: Clicks, inputs, selects, navigation
- 📸 **Screenshot Automation**: Captures screen after each action
- 🤖 **AI Descriptions** (Optional): Natural language step descriptions
- 🎨 **Visual Indicator**: See when recording is active
- ⚡ **Real-time Processing**: Steps generated as you go

## Settings

### Template-Based Mode (Default)
- Fast, free, works offline
- Basic but accurate descriptions
- Example: "Click the 'Submit' button"

### AI-Enhanced Mode
- Natural language descriptions
- Context-aware grouping
- Example: "Submit your login credentials"
- Requires API key

## Troubleshooting

### Extension not working
- Check that backend is running: `http://localhost:8000`
- Open browser DevTools Console for error messages
- Reload the extension after code changes

### Screenshots not capturing
- Make sure you're on a regular webpage (not chrome:// pages)
- Check extension permissions in chrome://extensions/

### API errors
- Verify API key is correct
- Check network connectivity
- Try template mode first (no API key needed)

## Development

### Making Changes

1. Edit files in `extension/src/`
2. Go to `chrome://extensions/`
3. Click the reload icon for Demo2PDF
4. Refresh any open tabs

### Debugging

**Content Script:**
- Open DevTools on any webpage (F12)
- Check Console tab for `[Demo2PDF]` messages

**Background Script:**
- Go to `chrome://extensions/`
- Click "service worker" or "Inspect views: background page"

**Popup:**
- Right-click extension icon → "Inspect popup"

## Icon Note

Placeholder icons are used. To add custom icons:
1. Create PNG files: 16x16, 48x48, 128x128
2. Place in `assets/icons/`
3. Name them: `icon-16.png`, `icon-48.png`, `icon-128.png`

Online icon generators:
- https://realfavicongenerator.net/
- https://www.favicon-generator.org/
