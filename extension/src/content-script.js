// Content script - Injected into all web pages to capture user interactions

let recording = false;
let sessionId = null;
let lastClickTime = 0;

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

    // Clear all pending timeouts to prevent memory leaks
    clearAllPendingTimeouts();

    // Hide visual indicator
    hideRecordingIndicator();

    sendResponse({success: true});
  } else if (message.action === 'captureInitialPage') {
    // Capture the initial page state when recording starts
    console.log('[Demo2PDF] Capturing initial page state');
    captureInitialPage();
    sendResponse({success: true});
  }
  return true; // Keep message channel open for async response
});

// Capture click events - use mousedown to capture BEFORE the click action
document.addEventListener('mousedown', async (event) => {
  if (!recording) return;

  // Only capture left clicks
  if (event.button !== 0) return;

  const element = event.target;

  console.log('[Demo2PDF] Click captured:', element);

  // Extract element information
  const elementInfo = extractElementInfo(element);

  // Check if this is a navigation link
  const linkElement = element.closest('a');
  const isNavigationLink = linkElement && linkElement.href &&
    !linkElement.href.startsWith('javascript:') &&
    !linkElement.href.startsWith('#') &&
    linkElement.target !== '_blank';

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

  // Track click time for SPA navigation deduplication
  lastClickTime = Date.now();

  // Add visual highlight to clicked element before capturing screenshot
  // This ensures the clicked element is visually identifiable in the screenshot
  const highlightElement = (el) => {
    const originalOutline = el.style.outline;
    const originalOutlineOffset = el.style.outlineOffset;
    el.style.outline = '3px solid #3b82f6';
    el.style.outlineOffset = '2px';
    return () => {
      el.style.outline = originalOutline;
      el.style.outlineOffset = originalOutlineOffset;
    };
  };

  const removeHighlight = highlightElement(element);

  // Wait for visual highlight to render, then capture
  setTimeout(() => {
    captureAndSend(eventData);
    // Remove highlight after capture (with small delay to ensure screenshot captured)
    setTimeout(removeHighlight, 100);
  }, 80);

}, true); // Use capture phase to get events before they're handled

// Capture input events (debounced per-element to avoid missing inputs)
const inputTimeouts = new Map();

document.addEventListener('input', (event) => {
  if (!recording) return;

  const element = event.target;

  // Only capture form inputs
  if (!['INPUT', 'TEXTAREA', 'SELECT'].includes(element.tagName)) {
    return;
  }

  // Get unique key for this element (robust identification)
  const getElementPath = (el) => {
    const parts = [];
    let current = el;
    while (current && current !== document.body && parts.length < 5) {
      const tag = current.tagName.toLowerCase();
      const idx = current.parentNode ? Array.from(current.parentNode.children).filter(c => c.tagName === current.tagName).indexOf(current) : 0;
      parts.unshift(`${tag}[${idx}]`);
      current = current.parentNode;
    }
    return parts.join('>');
  };
  const elementKey = element.id || element.name || getElementPath(element);

  // Clear existing timeout for THIS element only
  if (inputTimeouts.has(elementKey)) {
    clearTimeout(inputTimeouts.get(elementKey));
  }

  // Debounce per element - wait for user to finish typing in this field
  const timeout = setTimeout(async () => {
    console.log('[Demo2PDF] Input captured:', element);
    inputTimeouts.delete(elementKey);

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
  }, 800); // Wait 800ms after last keystroke in this field

  inputTimeouts.set(elementKey, timeout);

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

// Capture scroll events (debounced to avoid too many captures)
let scrollTimeout;
let lastScrollY = window.scrollY;
const SCROLL_THRESHOLD = 300; // Minimum scroll distance to capture

document.addEventListener('scroll', () => {
  if (!recording) return;

  clearTimeout(scrollTimeout);
  scrollTimeout = setTimeout(() => {
    const currentScrollY = window.scrollY;
    const scrollDistance = Math.abs(currentScrollY - lastScrollY);

    // Only capture significant scrolls
    if (scrollDistance >= SCROLL_THRESHOLD) {
      const direction = currentScrollY > lastScrollY ? 'down' : 'up';
      console.log('[Demo2PDF] Scroll captured:', direction, scrollDistance, 'px');

      // Find visible heading or section to describe scroll destination
      const visibleSection = findVisibleSection();

      const eventData = {
        action: 'scroll',
        timestamp: new Date().toISOString(),
        url: window.location.href,
        page_title: document.title,
        element: {
          tag: 'PAGE',
          text: visibleSection || `Scrolled ${direction}`
        },
        scroll: {
          direction: direction,
          distance: scrollDistance,
          position: currentScrollY,
          visibleSection: visibleSection
        }
      };

      lastScrollY = currentScrollY;
      captureAndSend(eventData);
    }
  }, 500); // Wait for scroll to settle
}, true);

// Helper: Find a visible heading or section name
function findVisibleSection() {
  // Priority order: h1 > h2 > h3 > other headings > sections
  const selectors = [
    'h1', 'h2', 'h3', 'h4',
    '[role="heading"]',
    'section[aria-label]', 'section[id]',
    '[data-section]', 'article h1', 'article h2'
  ];

  let bestMatch = null;
  let bestScore = -1;

  for (const selector of selectors) {
    const elements = document.querySelectorAll(selector);
    for (const el of elements) {
      const rect = el.getBoundingClientRect();

      // Check if element is visible in viewport (top 60%)
      if (rect.top >= -50 && rect.top < window.innerHeight * 0.6 && rect.height > 0) {
        // Get text from element directly (not nested content)
        let text = el.getAttribute('aria-label') ||
                   el.getAttribute('data-section') ||
                   (el.childNodes.length > 0 && el.childNodes[0].nodeType === Node.TEXT_NODE
                     ? el.childNodes[0].textContent
                     : el.textContent);

        text = text?.trim().substring(0, 50);

        if (text && text.length > 2) {
          // Score based on: visibility (closer to top = better) and heading level
          const levelScore = selector.startsWith('h') ? (5 - parseInt(selector[1])) : 0;
          const positionScore = Math.max(0, 100 - rect.top);
          const score = levelScore * 20 + positionScore;

          if (score > bestScore) {
            bestScore = score;
            bestMatch = text;
          }
        }
      }
    }
  }

  return bestMatch;
}

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

// Helper: Clear all pending timeouts to prevent memory leaks
function clearAllPendingTimeouts() {
  // Clear all input debounce timeouts
  inputTimeouts.forEach(timeout => clearTimeout(timeout));
  inputTimeouts.clear();
  console.log('[Demo2PDF] Cleared input timeouts');

  // Clear scroll timeout
  if (scrollTimeout) {
    clearTimeout(scrollTimeout);
    scrollTimeout = null;
    console.log('[Demo2PDF] Cleared scroll timeout');
  }
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

  // Add pulse animation (with ID for cleanup)
  const style = document.createElement('style');
  style.id = 'demo2pdf-indicator-style';
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
  // Remove the indicator div
  const indicator = document.getElementById('demo2pdf-indicator');
  if (indicator) {
    indicator.remove();
  }

  // Remove the pulse animation style element to prevent accumulation
  const style = document.getElementById('demo2pdf-indicator-style');
  if (style) {
    style.remove();
  }
}

// Check if already recording on page load
chrome.storage.local.get(['recording', 'sessionId'], (data) => {
  if (data.recording && data.sessionId) {
    recording = true;
    sessionId = data.sessionId;
    showRecordingIndicator();
    console.log('[Demo2PDF] Resumed recording session:', sessionId);
    // Note: We don't auto-capture navigation here because:
    // - Link clicks are already captured by mousedown handler
    // - This avoids duplicate "Navigate to..." steps
    // - SPA navigation is still captured via pushState/popstate handlers
  }
});

// Capture initial page state (when recording starts)
function captureInitialPage() {
  if (!recording || !sessionId) return;

  console.log('[Demo2PDF] Capturing initial page:', window.location.href);

  const eventData = {
    action: 'start',
    timestamp: new Date().toISOString(),
    url: window.location.href,
    page_title: document.title,
    element: {
      tag: 'PAGE',
      text: document.title
    }
  };

  captureAndSend(eventData);
}

// Capture page navigation event
function captureNavigation() {
  if (!recording || !sessionId) return;

  console.log('[Demo2PDF] Capturing navigation to:', window.location.href);

  const eventData = {
    action: 'navigate',
    timestamp: new Date().toISOString(),
    url: window.location.href,
    page_title: document.title,
    element: {
      tag: 'PAGE',
      text: document.title
    }
  };

  captureAndSend(eventData);
}

// Track URL for SPA navigation detection
let lastUrl = window.location.href;
const CLICK_NAV_THRESHOLD = 1000; // Ignore navigation within 1 second of a click

// Detect SPA navigation (pushState/replaceState)
const originalPushState = history.pushState;
const originalReplaceState = history.replaceState;

history.pushState = function(...args) {
  originalPushState.apply(this, args);
  handleUrlChange();
};

history.replaceState = function(...args) {
  originalReplaceState.apply(this, args);
  handleUrlChange();
};

// Detect back/forward navigation
window.addEventListener('popstate', handleUrlChange);

function handleUrlChange() {
  if (!recording || !sessionId) return;

  const currentUrl = window.location.href;
  if (currentUrl !== lastUrl) {
    const timeSinceClick = Date.now() - lastClickTime;

    // Skip if this navigation was likely caused by a recent click (already captured)
    if (timeSinceClick < CLICK_NAV_THRESHOLD) {
      console.log('[Demo2PDF] Skipping SPA nav (recent click captured it)');
      lastUrl = currentUrl;
      return;
    }

    console.log('[Demo2PDF] SPA navigation detected:', lastUrl, '->', currentUrl);
    lastUrl = currentUrl;

    // Wait for page content to update, then capture
    setTimeout(() => {
      captureNavigation();
    }, 500);
  }
}
