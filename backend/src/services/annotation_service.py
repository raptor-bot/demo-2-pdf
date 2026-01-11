"""Template-based annotation service for generating step descriptions"""

from typing import Dict, List, Optional

class TemplateAnnotationService:
    """Generate step descriptions using rule-based templates"""

    def __init__(self):
        self.templates = {
            "click": self._generate_click_description,
            "input": self._generate_input_description,
            "select": self._generate_select_description,
            "navigate": self._generate_navigate_description,
            "scroll": self._generate_scroll_description,
            "start": self._generate_start_description
        }

    def generate_description(self, event: Dict) -> str:
        """Generate description for a single event"""
        action = event.get("action", "unknown")
        generator = self.templates.get(action, self._generate_default)
        return generator(event)

    def generate_batch_descriptions(self, events: List[Dict]) -> List[str]:
        """Generate descriptions for multiple events with context"""
        descriptions = []
        i = 0

        while i < len(events):
            # Check if this is part of a form fill sequence
            if self._is_form_sequence(events, i):
                grouped = self._group_form_inputs(events, i)
                descriptions.append(self._generate_form_description(grouped))
                i += len(grouped)
            else:
                descriptions.append(self.generate_description(events[i]))
                i += 1

        return descriptions

    def _generate_click_description(self, event: Dict) -> str:
        """Generate description for click event"""
        element = event.get("element", {})
        text = element.get("text", "").strip()
        tag = element.get("tag", "").lower()
        element_type = element.get("type", "")
        aria_label = element.get("aria-label", "")

        # Use aria-label if text is empty
        if not text and aria_label:
            text = aria_label

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
        elif text:
            return f"Click '{text}'"
        else:
            return f"Click the {tag or 'element'}"

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
            return f"Enter your email address in the {label} field"
        elif "email" in label.lower():
            return f"Enter your email in the {label} field"
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
            # Extract readable part from URL
            from urllib.parse import urlparse
            parsed = urlparse(url)
            path = parsed.path.strip('/').replace('-', ' ').replace('_', ' ')
            if path:
                return f"Navigate to the {path} page"
            return f"Navigate to {parsed.netloc}"

    def _generate_scroll_description(self, event: Dict) -> str:
        """Generate description for scroll event"""
        scroll_data = event.get("scroll", {})
        direction = scroll_data.get("direction", "down")
        visible_section = scroll_data.get("visibleSection")

        # Use visible section if available
        if visible_section:
            return f"Scroll {direction} to the '{visible_section}' section"

        # Fallback to position-based description
        position = scroll_data.get("position", 0)
        if position < 300:
            location = "to the top of the page"
        elif position < 800:
            location = "to view more content"
        else:
            location = "further down the page"

        return f"Scroll {direction} {location}"

    def _generate_start_description(self, event: Dict) -> str:
        """Generate description for initial page (recording start)"""
        page_title = event.get("page_title", "")
        url = event.get("url", "")

        from urllib.parse import urlparse
        parsed = urlparse(url)

        # Build a rich description with both title and domain context
        if page_title and page_title.strip():
            # Clean up title - remove common suffixes
            clean_title = page_title.strip()
            for suffix in [' - Google Chrome', ' | ', ' - ']:
                if suffix in clean_title:
                    clean_title = clean_title.split(suffix)[0].strip()

            if parsed.netloc:
                # Include domain for context (e.g., "Start on the Dashboard page (app.example.com)")
                return f"Start on the {clean_title} page ({parsed.netloc})"
            return f"Start on the {clean_title} page"
        elif parsed.netloc:
            # No title, use domain and path
            path = parsed.path.strip('/').replace('-', ' ').replace('_', ' ')
            if path:
                return f"Start on {parsed.netloc}/{path}"
            return f"Start on {parsed.netloc}"
        else:
            return "Start recording the demo"

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
                fields.append(f"  - {label}: [your password]")
            else:
                fields.append(f"  - {label}: {value}")

        return "Fill out the form with the following information:\n" + "\n".join(fields)
