// Extension popup logic

const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const viewBtn = document.getElementById('viewBtn');
const status = document.getElementById('status');
const stepCount = document.getElementById('stepCount');
const countElement = document.getElementById('count');
const useLLMCheckbox = document.getElementById('useLLM');
const llmProviderSelect = document.getElementById('llmProvider');
const llmProviderRow = document.getElementById('llmProviderRow');

// Backend API URL
const API_URL = 'http://localhost:8000';

// Toggle LLM provider visibility
useLLMCheckbox.addEventListener('change', () => {
  llmProviderRow.style.display = useLLMCheckbox.checked ? 'block' : 'none';
});

// Load recording state on popup open
chrome.storage.local.get(['recording', 'sessionId', 'stepCount', 'useLLM', 'llmProvider'], (data) => {
  if (data.recording) {
    updateUIRecording(data.sessionId, data.stepCount || 0);
  }

  // Load settings
  if (data.useLLM) {
    useLLMCheckbox.checked = true;
    llmProviderRow.style.display = 'block';
  }
  if (data.llmProvider) {
    llmProviderSelect.value = data.llmProvider;
  }
});

// Start recording
startBtn.addEventListener('click', async () => {
  try {
    const useLLM = useLLMCheckbox.checked;
    const llmProvider = llmProviderSelect.value;

    // Save settings
    chrome.storage.local.set({ useLLM, llmProvider });

    // Create new session
    const response = await fetch(`${API_URL}/api/sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        use_llm: useLLM,
        llm_provider: llmProvider
      })
    });

    if (!response.ok) {
      throw new Error('Failed to create session');
    }

    const session = await response.json();

    // Save session info
    chrome.storage.local.set({
      recording: true,
      sessionId: session.session_id,
      stepCount: 0,
      useLLM,
      llmProvider
    });

    // Notify content script
    chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id, {
          action: 'startRecording',
          sessionId: session.session_id
        });
      }
    });

    updateUIRecording(session.session_id, 0);

  } catch (error) {
    console.error('Error starting recording:', error);
    status.textContent = '❌ Error: Make sure backend is running at localhost:8000';
    status.style.background = '#fee2e2';
  }
});

// Stop recording
stopBtn.addEventListener('click', () => {
  chrome.storage.local.get(['sessionId'], (data) => {
    const sessionId = data.sessionId;

    chrome.storage.local.set({
      recording: false,
      lastSessionId: sessionId
    });

    // Notify content script
    chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id, { action: 'stopRecording' });
      }
    });

    updateUIStopped(sessionId);
  });
});

// View session
viewBtn.addEventListener('click', () => {
  chrome.storage.local.get(['lastSessionId'], (data) => {
    if (data.lastSessionId) {
      // Open API docs page with session data
      chrome.tabs.create({
        url: `${API_URL}/docs#/default/get_session_api_sessions__session_id__get`
      });
    }
  });
});

function updateUIRecording(sessionId, count) {
  status.textContent = `🔴 Recording... (ID: ${sessionId.substring(0, 8)})`;
  status.className = 'recording';

  startBtn.style.display = 'none';
  stopBtn.style.display = 'block';
  viewBtn.style.display = 'none';

  stepCount.style.display = 'block';
  countElement.textContent = count;
}

function updateUIStopped(sessionId) {
  status.textContent = '✅ Recording stopped';
  status.style.background = '#d1fae5';
  status.style.color = '#065f46';
  status.style.borderLeft = '3px solid #10b981';

  startBtn.style.display = 'block';
  stopBtn.style.display = 'none';
  viewBtn.style.display = 'block';

  stepCount.style.display = 'block';
}

// Update step count in real-time
chrome.storage.onChanged.addListener((changes, namespace) => {
  if (namespace === 'local' && changes.stepCount) {
    countElement.textContent = changes.stepCount.newValue || 0;
  }
});
