from typing import Optional
from anthropic import Anthropic
from groq import Groq
import ollama
from ..config_manager import config_manager


class AIService:
    def __init__(self, service_type: Optional[str] = None, model: Optional[str] = None):
        self.service_type = (
            service_type.lower() if service_type else config_manager.get_ai_service()
        )
        self.model = model if model else config_manager.get_ai_model()
        if self.service_type == "groq":
            self.client = Groq(api_key=config_manager.get_api_key("groq"))
        elif self.service_type == "anthropic":
            self.client = Anthropic(api_key=config_manager.get_api_key("anthropic"))
        elif self.service_type == "ollama":
            self.client = ollama

    def query(self, prompt: str, max_retries: int = 3) -> str:
        for _ in range(max_retries):
            try:
                if self.service_type == "ollama":
                    return self._query_ollama(prompt)
                elif self.service_type == "groq":
                    return self._query_groq(prompt)
                elif self.service_type == "anthropic":
                    return self._query_anthropic(prompt)
                else:
                    raise ValueError(f"Unsupported service type: {self.service_type}")
            except Exception as e:
                print(f"Error occurred: {e}. Retrying...")
        raise Exception(
            f"Failed to query {self.service_type} after {max_retries} attempts"
        )

    def _query_ollama(self, prompt: str) -> str:
        response = self.client.generate(model=self.model or "llama3.1", prompt=prompt)
        return response["message"]["content"]

    def _query_groq(self, prompt: str) -> str:
        completion = self.client.chat.completions.create(
            model=self.model or "llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
        )
        return completion.choices[0].message.content

    def _query_anthropic(self, prompt: str) -> str:
        completion = self.client.messages.create(
            model=self.model or "claude-3-5-sonnet-20241022",
            max_tokens=1024,  # Adjust as needed
            messages=[{"role": "user", "content": prompt}],
        )
        return completion.content
