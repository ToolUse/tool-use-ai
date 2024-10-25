from typing import Optional
from anthropic import Anthropic
from groq import Groq
import ollama
from ..config_manager import config_manager


class AIService:
    DEFAULT_MODELS = {
        "ollama": "llama3.1",
        "groq": "llama-3.1-70b-versatile",
        "anthropic": "claude-3-5-sonnet-20241022",
    }

    def __init__(self, service_type: Optional[str] = None, model: Optional[str] = None):
        self.service_type = service_type.lower() if service_type else "ollama"

        # If no model specified, use the default for the service
        self.model = model if model else self.DEFAULT_MODELS[self.service_type]

        if self.service_type == "groq":
            self.client = Groq(api_key=config_manager.get_api_key("groq"))
        elif self.service_type == "anthropic":
            self.client = Anthropic(api_key=config_manager.get_api_key("anthropic"))
        elif self.service_type == "ollama":
            self.client = ollama

    def query(self, prompt: str, max_tokens: int = 1024) -> str:
        for _ in range(3):  # max_retries
            try:
                if self.service_type == "ollama":
                    return self._query_ollama(prompt)
                elif self.service_type == "groq":
                    return self._query_groq(prompt, max_tokens)
                elif self.service_type == "anthropic":
                    response = self._query_anthropic(prompt, max_tokens)
                    # Get just the text content from the ContentBlock
                    if hasattr(response, "content") and isinstance(
                        response.content, list
                    ):
                        return response.content[0].text if response.content else ""
                    return str(response)
                else:
                    raise ValueError(f"Unsupported service type: {self.service_type}")
            except Exception as e:
                print(f"Error occurred: {e}. Retrying...")
        raise Exception(f"Failed to query {self.service_type} after 3 attempts")

    def _query_ollama(self, prompt: str) -> str:
        response = self.client.chat(
            model=self.model, messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]

    def _query_groq(self, prompt: str, max_tokens: int) -> str:
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        return completion.choices[0].message.content

    def _query_anthropic(self, prompt: str, max_tokens: int) -> str:
        completion = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        # Extract just the text from the Anthropic response
        if hasattr(completion, "content") and isinstance(completion.content, list):
            return completion.content[0].text if completion.content else ""
        return completion.content
