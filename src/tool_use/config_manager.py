import os
import json
from pathlib import Path

DEFAULT_CONFIG = {
    "ai_service": "anthropic",
    "ai_model": None,
    "groq_api_key": None,
    "anthropic_api_key": None,
}


class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / ".tool-use-ai"
        self.config_file = self.config_dir / "config.json"
        self.config = self._load_config()

    def _load_config(self):
        if not self.config_file.exists():
            self._create_default_config()
        with open(self.config_file, "r") as f:
            return json.load(f)

    def _create_default_config(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=2)

    def get_ai_service(self):
        return self.get("ai_service")

    def get_ai_model(self):
        return self.get("ai_model")

    def get_api_key(self, service):
        if service == "groq":
            return self.get("groq_api_key") or os.environ.get("GROQ_API_KEY")
        elif service == "anthropic":
            return self.get("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY")
        else:
            return None


config_manager = ConfigManager()
