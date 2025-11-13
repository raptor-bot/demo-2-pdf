"""LLM-powered annotation service for generating natural language descriptions"""

from typing import Dict, List, Optional
import os
import re


class LLMAnnotationService:
    """Generate step descriptions using LLM APIs"""

    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.provider = provider
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")

        # Initialize client based on provider
        if provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        elif provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
            self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")
        elif provider == "ollama":
            self.model = model or os.getenv("OLLAMA_MODEL", "llama3")
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
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1000"))
        )

        content = response.choices[0].message.content
        return self._parse_steps(content)

    def _generate_anthropic(self, prompt: str) -> List[str]:
        """Generate descriptions using Anthropic Claude API"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1000")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
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
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        from .annotation_service import TemplateAnnotationService

        self.template_service = TemplateAnnotationService()
        self.use_llm = use_llm

        if use_llm:
            self.llm_service = LLMAnnotationService(
                provider=llm_provider,
                api_key=api_key,
                model=model
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
