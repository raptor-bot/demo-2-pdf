// Background service worker - Handles screenshot capture and API communication

const API_URL = 'http://localhost:8000';

console.log('[Demo2PDF] Background service worker loaded');

// Listen for messages from content script and popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'captureScreenshot') {
    handleCaptureScreenshot(message, sender, sendResponse);
    return true; // Keep channel open for async response
  }

  if (message.action === 'stopRecordingFromPage') {
    // Stop recording from content script
    chrome.storage.local.set({ recording: false });
    sendResponse({success: true});
  }

  return true;
});

// Handle screenshot capture and upload
async function handleCaptureScreenshot(message, sender, sendResponse) {
  try {
    const { sessionId, eventData } = message;

    // Capture visible tab
    const tabId = sender.tab.id;

    chrome.tabs.captureVisibleTab(
      null,
      { format: 'png' },
      async (dataUrl) => {
        if (chrome.runtime.lastError) {
          console.error('[Demo2PDF] Screenshot error:', chrome.runtime.lastError);
          sendResponse({ success: false, error: chrome.runtime.lastError.message });
          return;
        }

        try {
          // Convert data URL to blob
          const response = await fetch(dataUrl);
          const blob = await response.blob();

          // Send to backend
          const formData = new FormData();
          formData.append('screenshot', blob, 'screenshot.png');
          formData.append('event_data', JSON.stringify(eventData));

          const apiResponse = await fetch(
            `${API_URL}/api/sessions/${sessionId}/events`,
            {
              method: 'POST',
              body: formData
            }
          );

          if (apiResponse.ok) {
            const result = await apiResponse.json();

            // Update step count
            chrome.storage.local.get(['stepCount'], (data) => {
              const newCount = (data.stepCount || 0) + 1;
              chrome.storage.local.set({ stepCount: newCount });
            });

            console.log('[Demo2PDF] Event saved:', result);

            sendResponse({
              success: true,
              stepId: result.step_id,
              description: result.description
            });

          } else {
            const errorText = await apiResponse.text();
            console.error('[Demo2PDF] API error:', errorText);
            sendResponse({
              success: false,
              error: `API error: ${apiResponse.status}`
            });
          }

        } catch (error) {
          console.error('[Demo2PDF] Upload error:', error);
          sendResponse({ success: false, error: error.message });
        }
      }
    );

  } catch (error) {
    console.error('[Demo2PDF] Error in handleCaptureScreenshot:', error);
    sendResponse({ success: false, error: error.message });
  }
}

// Install event
chrome.runtime.onInstalled.addListener((details) => {
  if (details.reason === 'install') {
    console.log('[Demo2PDF] Extension installed');

    // Open welcome page
    chrome.tabs.create({
      url: `${API_URL}/docs`
    });
  }
});
