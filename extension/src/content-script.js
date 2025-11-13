// Content script - Injected into all web pages to capture user interactions

let recording = false;
let sessionId = null;

console.log('[Demo2PDF] Content script loaded');

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'startRecording') {
    recording = true;
    sessionId = message.sessionId;
    console.log('[Demo2PDF] Recording started, session:', sessionId);

    // Show visual indicator
    showRecordingIndicator();

    sendResponse({success: true});
  } else if (message.action === 'stopRecording') {
    recording = false;
    console.log('[Demo2PDF] Recording stopped');

    // Hide visual indicator
    hideRecordingIndicator();

    sendResponse({success: true});
  }
  return true; // Keep message channel open for async response
});

// Capture click events
document.addEventListener('click', async (event) => {
  if (!recording) return;

  const element = event.target;

  console.log('[Demo2PDF] Click captured:', element);

  // Extract element information
  const elementInfo = extractElementInfo(element);

  // Create event data
  const eventData = {
    action: 'click',
    timestamp: new Date().toISOString(),
    url: window.location.href,
    page_title: document.title,
    element: elementInfo,
    coordinates: {
      x: event.clientX,
      y: event.clientY
    }
  };

  // Wait a moment for UI to update
  await sleep(300);

  // Capture and send
  captureAndSend(eventData);

}, true); // Use capture phase to get events before they're handled

// Capture input events (debounced to avoid too many captures)
let inputTimeout;
document.addEventListener('input', (event) => {
  if (!recording) return;

  const element = event.target;

  // Only capture form inputs
  if (!['INPUT', 'TEXTAREA', 'SELECT'].includes(element.tagName)) {
    return;
  }

  // Debounce - wait for user to finish typing
  clearTimeout(inputTimeout);
  inputTimeout = setTimeout(async () => {
    console.log('[Demo2PDF] Input captured:', element);

    const elementInfo = extractElementInfo(element);

    const eventData = {
      action: 'input',
      timestamp: new Date().toISOString(),
      url: window.location.href,
      page_title: document.title,
      element: elementInfo
    };

    await sleep(200);
    captureAndSend(eventData);
  }, 1000); // Wait 1 second after last keystroke

}, true);

// Capture select/dropdown changes
document.addEventListener('change', async (event) => {
  if (!recording) return;

  const element = event.target;

  if (element.tagName === 'SELECT') {
    console.log('[Demo2PDF] Select captured:', element);

    const elementInfo = extractElementInfo(element);

    const eventData = {
      action: 'select',
      timestamp: new Date().toISOString(),
      url: window.location.href,
      page_title: document.title,
      element: elementInfo
    };

    await sleep(200);
    captureAndSend(eventData);
  }
}, true);

// Helper: Extract element information
function extractElementInfo(element) {
  const info = {
    tag: element.tagName,
    id: element.id || null,
    class: element.className || null,
    name: element.name || null,
    type: element.type || null,
    text: element.innerText?.substring(0, 100) || element.value || null,
    value: null,
    placeholder: element.placeholder || null,
    'aria-label': element.getAttribute('aria-label') || null
  };

  // Get associated label for form inputs
  if (['INPUT', 'TEXTAREA', 'SELECT'].includes(element.tagName)) {
    const label = findLabelForElement(element);
    if (label) {
      info.label = label;
    }

    // Get value, but mask passwords
    if (element.type === 'password') {
      info.value = '********';
    } else if (element.value) {
      info.value = element.value.substring(0, 100);
    }
  }

  // For links, get href
  if (element.tagName === 'A') {
    info.href = element.href;
  }

  return info;
}

// Helper: Find label for form element
function findLabelForElement(element) {
  // Try id-based label
  if (element.id) {
    const label = document.querySelector(`label[for="${element.id}"]`);
    if (label) {
      return label.innerText.trim();
    }
  }

  // Try parent label
  const parentLabel = element.closest('label');
  if (parentLabel) {
    return parentLabel.innerText.trim();
  }

  // Try placeholder
  if (element.placeholder) {
    return element.placeholder;
  }

  // Try name attribute
  if (element.name) {
    return element.name.replace(/_/g, ' ').replace(/-/g, ' ');
  }

  return null;
}

// Helper: Capture screenshot and send to backend
async function captureAndSend(eventData) {
  try {
    // Request screenshot from background script
    chrome.runtime.sendMessage({
      action: 'captureScreenshot',
      sessionId: sessionId,
      eventData: eventData
    }, (response) => {
      if (response && response.success) {
        console.log('[Demo2PDF] Event sent successfully');
      } else {
        console.error('[Demo2PDF] Failed to send event:', response);
      }
    });

  } catch (error) {
    console.error('[Demo2PDF] Error capturing:', error);
  }
}

// Helper: Sleep function
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Visual indicator for recording
function showRecordingIndicator() {
  // Remove existing indicator if any
  hideRecordingIndicator();

  const indicator = document.createElement('div');
  indicator.id = 'demo2pdf-indicator';
  indicator.innerHTML = '🔴 Recording';
  indicator.style.cssText = `
    position: fixed;
    top: 10px;
    right: 10px;
    background: rgba(239, 68, 68, 0.95);
    color: white;
    padding: 8px 16px;
    border-radius: 20px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
    font-weight: 600;
    z-index: 999999;
    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    cursor: pointer;
  `;

  indicator.addEventListener('click', () => {
    // Quick stop via indicator
    chrome.runtime.sendMessage({ action: 'stopRecordingFromPage' });
  });

  document.body.appendChild(indicator);

  // Add pulse animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes demo2pdf-pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.7; }
    }
    #demo2pdf-indicator {
      animation: demo2pdf-pulse 2s infinite;
    }
  `;
  document.head.appendChild(style);
}

function hideRecordingIndicator() {
  const indicator = document.getElementById('demo2pdf-indicator');
  if (indicator) {
    indicator.remove();
  }
}

// Check if already recording on page load
chrome.storage.local.get(['recording', 'sessionId'], (data) => {
  if (data.recording && data.sessionId) {
    recording = true;
    sessionId = data.sessionId;
    showRecordingIndicator();
    console.log('[Demo2PDF] Resumed recording session:', sessionId);
  }
});
