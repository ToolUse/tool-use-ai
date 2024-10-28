import os
from pathlib import Path
import tomli
import tomli_w

DEFAULT_CONFIG = {
    "default_ai_service": "anthropic",
    "default_ai_model": "",  # Empty string instead of None
    "groq_api_key": "",  # Empty string instead of None
    "anthropic_api_key": "",  # Empty string instead of None
    "tools": {
        "do": {
            "write_to_terminal": True,
            "ai_service": "",  # Empty string instead of None
            "ai_model": "",  # Empty string instead of None
        },
        "make-obsidian-plugin": {
            "ai_service": "",
            "ai_model": "",
        },
    },
}


class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / ".tool-use"
        self.config_file = self.config_dir / "config.toml"
        self.config = self._load_config()

    def _load_config(self):
        if not self.config_file.exists():
            self._create_default_config()
        with open(self.config_file, "rb") as f:
            return tomli.load(f)

    def _create_default_config(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "wb") as f:
            tomli_w.dump(DEFAULT_CONFIG, f)

    def get(self, key, default=None):
        # Support nested keys with dot notation
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        # Convert empty strings to None when retrieving
        return None if value == "" else value

    def set(self, key, value):
        # Support nested keys with dot notation
        keys = key.split(".")
        config = self.config
        for k in keys[:-1]:
            config = config.setdefault(k, {})
        # Convert None to empty string when storing
        config[keys[-1]] = "" if value is None else value

        with open(self.config_file, "wb") as f:
            tomli_w.dump(self.config, f)

    def get_tool_config(self, tool_name):
        """Get config for a specific tool, including AI service settings"""
        tool_config = self.get(f"tools.{tool_name}", {})

        # Get AI service settings with fallback to defaults
        ai_service = tool_config.get("ai_service") or self.get("default_ai_service")
        ai_model = tool_config.get("ai_model") or self.get("default_ai_model")

        return {**tool_config, "ai_service": ai_service, "ai_model": ai_model}

    def get_api_key(self, service):
        """Get API key with environment variable fallback"""
        if service == "groq":
            return self.get("groq_api_key") or os.environ.get("GROQ_API_KEY")
        elif service == "anthropic":
            return self.get("anthropic_api_key") or os.environ.get("ANTHROPIC_API_KEY")
        else:
            return None


config_manager = ConfigManager()
