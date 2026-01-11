# Demo2PDF Chrome Extension - Test Plan

## Overview

This document provides a comprehensive test plan for the Demo2PDF Chrome extension recording functionality. The extension captures user interactions (clicks, inputs, scrolls, navigation) and takes screenshots to generate step-by-step documentation.

## Prerequisites

Before testing, ensure:
1. Backend server is running at `http://localhost:8000`
2. Chrome extension is installed and enabled
3. Chrome DevTools console is open (F12) to monitor `[Demo2PDF]` log messages
4. A test page with various interactive elements is available

## Test Environment Setup

### Recommended Test Pages
- A form-heavy page (e.g., a registration form)
- A page with multiple sections and headings (for scroll testing)
- A single-page application (SPA) with client-side routing
- A standard multi-page website

---

## 1. Click Capture Scenarios

### TC-CLK-001: Basic Button Click
**Objective**: Verify that clicking a standard button is captured correctly.

**Steps**:
1. Start recording via the extension popup
2. Verify the red "Recording" indicator appears
3. Click a standard `<button>` element on the page
4. Wait 1 second for the capture to complete
5. Check the DevTools console for `[Demo2PDF] Click captured:` log
6. Stop recording
7. View the session to verify the click was recorded with a screenshot

**Expected Result**:
- Console shows click captured with button element details
- Session contains one click event with correct element info (tag: BUTTON, text content)
- Screenshot shows the page at the moment of click

---

### TC-CLK-002: Link Click (Standard Navigation)
**Objective**: Verify that clicking a navigation link captures the click before navigation occurs.

**Steps**:
1. Start recording on a page with internal links
2. Click a link that navigates to another page on the same domain
3. Wait for the new page to load
4. Verify the recording indicator persists on the new page
5. Stop recording
6. View the session

**Expected Result**:
- Click event is captured with element info showing `tag: A` and `href` attribute
- Screenshot shows the original page (before navigation)
- No duplicate navigation events (click already captured the action)

---

### TC-CLK-003: External Link Click (target="_blank")
**Objective**: Verify that clicking external links (new tab) is captured correctly.

**Steps**:
1. Start recording
2. Click a link with `target="_blank"` attribute
3. Switch back to the original tab
4. Stop recording
5. View the session

**Expected Result**:
- Click event is captured
- Element info includes `href` to external URL
- Recording continues on the original tab

---

### TC-CLK-004: Nested Element Click
**Objective**: Verify that clicks on nested elements (icon inside button) capture the correct target.

**Steps**:
1. Start recording
2. Find a button containing an icon or nested span
3. Click directly on the icon/nested element
4. Check console logs
5. Stop recording and view session

**Expected Result**:
- Click is captured on the actual clicked element (icon/span)
- Element extraction includes parent context if available
- Screenshot clearly shows the clicked area

---

### TC-CLK-005: Right-Click Ignored
**Objective**: Verify that right-clicks are not captured.

**Steps**:
1. Start recording
2. Right-click on any element
3. Dismiss the context menu
4. Check console logs
5. Stop recording

**Expected Result**:
- No `[Demo2PDF] Click captured:` log appears
- Session shows no events for the right-click

---

### TC-CLK-006: Rapid Multiple Clicks
**Objective**: Verify behavior when user clicks rapidly on multiple elements.

**Steps**:
1. Start recording
2. Quickly click 5 different buttons in succession (about 200ms apart)
3. Wait 2 seconds
4. Stop recording
5. View session

**Expected Result**:
- All 5 clicks are captured
- Each click has its own screenshot
- Timestamps are sequential and accurate

---

## 2. Form Input Scenarios

### TC-INP-001: Single Text Input Field
**Objective**: Verify that typing in a text input is captured with debouncing.

**Steps**:
1. Start recording
2. Click into a text input field
3. Type "Hello World" at normal typing speed
4. Wait 1 second after typing stops
5. Check console for `[Demo2PDF] Input captured:` log
6. Stop recording
7. View session

**Expected Result**:
- Only ONE input event is captured (debounced)
- Event shows the complete value "Hello World"
- Element info includes label if available
- 800ms debounce respected (capture occurs ~800ms after last keystroke)

---

### TC-INP-002: Multiple Form Fields (Tab Between)
**Objective**: Verify that each field captures its own input event when tabbing between fields.

**Steps**:
1. Start recording
2. Click into first name field, type "John"
3. Press Tab to move to last name field
4. Type "Doe"
5. Press Tab to move to email field
6. Type "john@example.com"
7. Wait 1 second
8. Stop recording
9. View session

**Expected Result**:
- Three separate input events are captured
- Each event corresponds to its respective field
- Debouncing is per-element (changing fields triggers capture of previous field)
- Labels are correctly associated with each field

---

### TC-INP-003: Fast Typing (Stress Test)
**Objective**: Verify that very fast typing is handled correctly.

**Steps**:
1. Start recording
2. Click into a text input
3. Type rapidly (as fast as possible): "abcdefghijklmnopqrstuvwxyz"
4. Wait 1 second
5. Check console
6. Stop recording

**Expected Result**:
- Only ONE input event is captured with the complete value
- No characters are lost
- Debounce timer properly resets with each keystroke

---

### TC-INP-004: Password Field Masking
**Objective**: Verify that password values are masked in captured events.

**Steps**:
1. Start recording
2. Click into a password field
3. Type "secretpassword123"
4. Wait 1 second
5. Stop recording
6. View session and check event data

**Expected Result**:
- Input event is captured
- Value shows "********" instead of actual password
- Field is identified as `type: password`

---

### TC-INP-005: Textarea Input
**Objective**: Verify that textarea (multi-line) input is captured.

**Steps**:
1. Start recording
2. Click into a textarea
3. Type multiple lines of text:
   ```
   Line 1
   Line 2
   Line 3
   ```
4. Wait 1 second
5. Stop recording
6. View session

**Expected Result**:
- Input event is captured
- Multi-line value is preserved (with newlines)
- Element shows `tag: TEXTAREA`

---

### TC-INP-006: Select/Dropdown Change
**Objective**: Verify that dropdown selection changes are captured.

**Steps**:
1. Start recording
2. Click on a select dropdown
3. Select a different option
4. Wait 1 second
5. Stop recording
6. View session

**Expected Result**:
- Select event is captured (action: "select")
- Value shows the selected option
- Element shows `tag: SELECT`

---

### TC-INP-007: Input in Quick Succession Across Fields
**Objective**: Verify that rapidly changing between fields captures all inputs.

**Steps**:
1. Start recording
2. Type "A" in field 1, immediately click field 2
3. Type "B" in field 2, immediately click field 3
4. Type "C" in field 3
5. Wait 2 seconds
6. Stop recording
7. View session

**Expected Result**:
- All three inputs are captured
- Each field's value is correctly recorded
- Per-element debouncing ensures no data loss

---

## 3. Scroll Scenarios

### TC-SCR-001: Small Scroll (Below Threshold)
**Objective**: Verify that small scrolls below 300px threshold are not captured.

**Steps**:
1. Start recording
2. Scroll down slowly by approximately 100-200 pixels
3. Wait 1 second
4. Check console logs
5. Stop recording

**Expected Result**:
- No scroll event is captured
- Console shows no `[Demo2PDF] Scroll captured:` log

---

### TC-SCR-002: Large Scroll (Above Threshold)
**Objective**: Verify that scrolls exceeding 300px are captured.

**Steps**:
1. Start recording
2. Scroll down quickly by at least 400 pixels
3. Wait for scroll to settle (500ms debounce)
4. Check console for scroll log
5. Stop recording
6. View session

**Expected Result**:
- Scroll event is captured
- Direction shows "down"
- Distance shows actual scroll amount (400+ pixels)
- Screenshot shows new viewport position

---

### TC-SCR-003: Scroll to Section with Heading
**Objective**: Verify that visible section/heading is detected after scroll.

**Steps**:
1. Start recording on a page with multiple h1/h2/h3 headings
2. Scroll down to a section with a visible heading
3. Wait for capture
4. Stop recording
5. View session

**Expected Result**:
- Scroll event includes `visibleSection` with heading text
- Element text shows the section name (e.g., "About Us", "Features")
- Helps identify where user scrolled to

---

### TC-SCR-004: Scroll Up
**Objective**: Verify that upward scrolling is captured correctly.

**Steps**:
1. Start recording
2. First scroll down significantly
3. Wait for capture
4. Then scroll back up by at least 400 pixels
5. Wait for capture
6. Stop recording
7. View session

**Expected Result**:
- Two scroll events captured
- First shows direction: "down"
- Second shows direction: "up"
- Both have appropriate distance values

---

### TC-SCR-005: Continuous Scrolling
**Objective**: Verify that continuous scrolling captures discrete events.

**Steps**:
1. Start recording
2. Scroll continuously for 3 seconds (smooth scrolling)
3. Stop scrolling
4. Wait 1 second
5. Stop recording

**Expected Result**:
- Multiple scroll events may be captured (one every ~500ms during scrolling)
- Each event has appropriate distance and direction
- Events are not duplicated or lost

---

## 4. Navigation Scenarios

### TC-NAV-001: Standard Link Navigation
**Objective**: Verify that clicking a link and navigating is captured without duplication.

**Steps**:
1. Start recording
2. Click a standard internal link
3. Wait for new page to load
4. Verify recording indicator appears on new page
5. Stop recording
6. View session

**Expected Result**:
- ONE event captured (the click)
- No duplicate "navigate" event (click-to-navigation deduplication active)
- Recording persists across page navigation

---

### TC-NAV-002: SPA Navigation (pushState)
**Objective**: Verify that SPA client-side navigation is detected.

**Steps**:
1. Start recording on a React/Vue/Angular SPA
2. Wait 2 seconds (to ensure no recent click)
3. Trigger programmatic navigation (e.g., through app state)
4. Wait for URL to change
5. Stop recording
6. View session

**Expected Result**:
- Navigation event is captured (action: "navigate")
- New URL and page title are recorded
- Screenshot shows new page content

---

### TC-NAV-003: Browser Back/Forward
**Objective**: Verify that using browser back/forward buttons triggers navigation capture.

**Steps**:
1. Start recording
2. Click a link to navigate to a new page
3. Wait 2 seconds
4. Click browser back button
5. Wait for page to load
6. Stop recording
7. View session

**Expected Result**:
- Initial click is captured
- popstate navigation (back button) is captured as navigate event
- Both pages have screenshots

---

### TC-NAV-004: Hash Navigation (#anchor)
**Objective**: Verify that hash/anchor navigation is NOT captured as navigation.

**Steps**:
1. Start recording
2. Click a link that goes to `#section` on the same page
3. Wait 1 second
4. Check console logs
5. Stop recording

**Expected Result**:
- Click event IS captured (mousedown)
- No separate navigation event (hash links don't change page)
- JavaScript anchor links are handled appropriately

---

### TC-NAV-005: Click-to-Navigation Deduplication
**Objective**: Verify that clicking a link doesn't create duplicate events.

**Steps**:
1. Start recording
2. Click a standard navigation link
3. Observe the console logs closely
4. Stop recording
5. View session

**Expected Result**:
- Only ONE event in the session (the click)
- Console may show "Skipping SPA nav (recent click captured it)" message
- No duplicate click + navigate events

---

## 5. Edge Cases and Stress Tests

### TC-EDGE-001: Rapid Clicks During Navigation
**Objective**: Verify behavior when user clicks multiple times during page load.

**Steps**:
1. Start recording
2. Click a navigation link
3. Immediately click another link (before page fully loads)
4. Wait for navigation to complete
5. Stop recording
6. View session

**Expected Result**:
- First click is captured
- Second click may or may not be captured (depending on timing)
- No crashes or errors
- Recording state is maintained

---

### TC-EDGE-002: Scroll During Input
**Objective**: Verify that scrolling while typing doesn't interfere with input capture.

**Steps**:
1. Start recording
2. Click into a text input
3. Start typing "Hello"
4. While still typing, scroll the page
5. Continue typing " World"
6. Wait 1 second
7. Stop recording
8. View session

**Expected Result**:
- Input event captures complete value "Hello World"
- Scroll event(s) may be captured if threshold met
- Events don't interfere with each other

---

### TC-EDGE-003: Click During Navigation
**Objective**: Verify that clicks immediately after navigation are captured.

**Steps**:
1. Start recording
2. Click a link to navigate
3. As soon as new page loads, click a button
4. Wait 1 second
5. Stop recording
6. View session

**Expected Result**:
- Navigation click is captured
- Button click on new page is captured
- Recording seamlessly continues

---

### TC-EDGE-004: Very Long Input Value
**Objective**: Verify that very long input values are truncated appropriately.

**Steps**:
1. Start recording
2. Click into a textarea
3. Paste or type a very long text (500+ characters)
4. Wait 1 second
5. Stop recording
6. View session event data

**Expected Result**:
- Input is captured
- Value is truncated to 100 characters (per extractElementInfo)
- No errors or crashes

---

### TC-EDGE-005: Multiple Tabs Recording
**Objective**: Verify behavior when recording and switching tabs.

**Steps**:
1. Start recording on Tab A
2. Open a new tab (Tab B)
3. Perform some clicks on Tab B
4. Switch back to Tab A
5. Perform some clicks on Tab A
6. Stop recording
7. View session

**Expected Result**:
- Only clicks on Tab A (original recording tab) are captured
- Tab B clicks may or may not be captured (depends on extension scope)
- Recording state is maintained correctly

---

### TC-EDGE-006: Start Recording on Page with No Interactive Elements
**Objective**: Verify that recording starts correctly even with minimal page content.

**Steps**:
1. Navigate to a mostly blank page
2. Start recording
3. Verify recording indicator appears
4. Stop recording
5. View session

**Expected Result**:
- Initial page capture (action: "start") is recorded
- Recording indicator shows correctly
- Session is created without errors

---

### TC-EDGE-007: Stop Recording via Indicator Click
**Objective**: Verify that clicking the recording indicator stops recording.

**Steps**:
1. Start recording
2. Click the red "Recording" indicator badge in the corner
3. Check if recording stops
4. Verify indicator disappears

**Expected Result**:
- Recording stops when indicator is clicked
- Indicator is removed from page
- Storage shows `recording: false`

---

### TC-EDGE-008: Backend Unavailable
**Objective**: Verify graceful handling when backend is not running.

**Steps**:
1. Stop the backend server
2. Try to start recording
3. Check error handling

**Expected Result**:
- Error message appears in popup: "Make sure backend is running at localhost:8000"
- Extension doesn't crash
- User can retry after backend is started

---

## 6. Recording Persistence Scenarios

### TC-PERS-001: Recording Survives Page Refresh
**Objective**: Verify that recording continues after page refresh.

**Steps**:
1. Start recording
2. Capture a few events
3. Refresh the page (F5)
4. Verify recording indicator reappears
5. Capture more events
6. Stop recording
7. View session

**Expected Result**:
- Recording state is restored from chrome.storage.local
- Indicator shows after refresh
- All events (before and after refresh) are in the session

---

### TC-PERS-002: Recording Survives Tab Close and Reopen
**Objective**: Verify recording state after closing/reopening extension popup.

**Steps**:
1. Start recording
2. Close the extension popup
3. Capture some events on the page
4. Reopen the extension popup
5. Verify popup shows recording state
6. Stop recording

**Expected Result**:
- Popup loads with correct recording state
- Step count is accurate
- Stop button is visible (not Start button)

---

## 7. LLM Integration Scenarios

### TC-LLM-001: Recording with LLM Enabled
**Objective**: Verify that enabling LLM option affects session creation.

**Steps**:
1. Check the "Use LLM for descriptions" checkbox
2. Select a provider (Claude/OpenAI/Ollama)
3. Start recording
4. Capture a few events
5. Stop recording
6. View session

**Expected Result**:
- Session is created with `use_llm: true`
- Provider preference is stored
- (Backend behavior with LLM is out of scope for extension testing)

---

### TC-LLM-002: LLM Settings Persistence
**Objective**: Verify that LLM settings are saved and restored.

**Steps**:
1. Enable LLM checkbox and select "openai" provider
2. Close popup
3. Reopen popup
4. Check settings state

**Expected Result**:
- Checkbox remains checked
- Provider dropdown shows "openai"
- Settings are loaded from chrome.storage.local

---

## Test Results Summary Template

| Test ID | Test Name | Status | Notes |
|---------|-----------|--------|-------|
| TC-CLK-001 | Basic Button Click | | |
| TC-CLK-002 | Link Click Navigation | | |
| TC-CLK-003 | External Link Click | | |
| TC-CLK-004 | Nested Element Click | | |
| TC-CLK-005 | Right-Click Ignored | | |
| TC-CLK-006 | Rapid Multiple Clicks | | |
| TC-INP-001 | Single Text Input | | |
| TC-INP-002 | Multiple Form Fields | | |
| TC-INP-003 | Fast Typing | | |
| TC-INP-004 | Password Masking | | |
| TC-INP-005 | Textarea Input | | |
| TC-INP-006 | Select/Dropdown | | |
| TC-INP-007 | Quick Field Switching | | |
| TC-SCR-001 | Small Scroll | | |
| TC-SCR-002 | Large Scroll | | |
| TC-SCR-003 | Scroll to Section | | |
| TC-SCR-004 | Scroll Up | | |
| TC-SCR-005 | Continuous Scrolling | | |
| TC-NAV-001 | Standard Link Nav | | |
| TC-NAV-002 | SPA Navigation | | |
| TC-NAV-003 | Back/Forward | | |
| TC-NAV-004 | Hash Navigation | | |
| TC-NAV-005 | Deduplication | | |
| TC-EDGE-001 | Rapid Clicks Nav | | |
| TC-EDGE-002 | Scroll During Input | | |
| TC-EDGE-003 | Click During Nav | | |
| TC-EDGE-004 | Long Input Value | | |
| TC-EDGE-005 | Multiple Tabs | | |
| TC-EDGE-006 | Blank Page | | |
| TC-EDGE-007 | Indicator Click Stop | | |
| TC-EDGE-008 | Backend Unavailable | | |
| TC-PERS-001 | Page Refresh | | |
| TC-PERS-002 | Popup Close/Reopen | | |
| TC-LLM-001 | LLM Enabled | | |
| TC-LLM-002 | LLM Settings | | |

---

## Key Implementation Details (Reference)

### Event Capture Timing
- **Clicks**: Captured on `mousedown` (before action), with 50ms delay for visual state
- **Inputs**: Debounced at 800ms per-element
- **Scrolls**: Debounced at 500ms, threshold of 300px
- **Navigation**: 1000ms deduplication window after clicks

### Element Information Captured
- Tag name, ID, class, name, type
- Text content (first 100 characters)
- Value (masked for passwords)
- Associated label
- Placeholder, aria-label
- href (for links)

### Storage Keys
- `recording`: boolean
- `sessionId`: string
- `stepCount`: number
- `lastSessionId`: string
- `useLLM`: boolean
- `llmProvider`: string

---

## Appendix: Console Log Messages

| Log Message | Meaning |
|-------------|---------|
| `[Demo2PDF] Content script loaded` | Extension injected successfully |
| `[Demo2PDF] Recording started, session: xxx` | Recording began |
| `[Demo2PDF] Recording stopped` | Recording ended |
| `[Demo2PDF] Click captured: <element>` | Click event detected |
| `[Demo2PDF] Input captured: <element>` | Input event captured after debounce |
| `[Demo2PDF] Scroll captured: down/up Xpx` | Scroll event detected |
| `[Demo2PDF] Capturing initial page: <url>` | First page screenshot |
| `[Demo2PDF] SPA navigation detected` | Client-side routing detected |
| `[Demo2PDF] Skipping SPA nav (recent click)` | Deduplication active |
| `[Demo2PDF] Event sent successfully` | Backend received event |
