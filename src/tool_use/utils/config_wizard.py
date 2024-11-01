# src/tool_use/utils/config_wizard.py

from typing import Dict, List, Optional
from ..config_manager import config_manager
import os

AVAILABLE_SERVICES = ["anthropic", "groq", "ollama"]

SCRIPT_INFO = {
    "do": {
        "name": "AI Command Generator",
        "configurable": ["ai_service", "ai_model", "write_to_terminal"],
        "description": "Generate and execute terminal commands using AI",
    },
    "make-obsidian-plugin": {
        "name": "Obsidian Plugin Generator",
        "configurable": ["ai_service", "ai_model"],
        "description": "Generate Obsidian plugins using AI",
    },
    "transcribe": {
        "name": "Transcribe",
        "description": "Transcribe and analyze audio using AI",
        "config_keys": {
            "whisperfile_path": {
                "description": "Path to store Whisper models",
                "default": os.path.expanduser("~/.whisperfiles"),
            },
            "vault_path": {
                "description": "Path to Obsidian vault for markdown export",
                "default": os.path.expanduser("~/Documents/ObsidianVault"),
            },
            "default_model": {
                "description": "Default Whisper model to use",
                "default": "tiny.en",
            }
        }
    }
}


def prompt_choice(
    prompt: str, options: List[str], default: Optional[str] = None
) -> str:
    """Present numbered options and get user choice."""
    print(f"\n{prompt}")
    for i, option in enumerate(options, 1):
        default_marker = " (default)" if option == default else ""
        print(f"{i}. {option}{default_marker}")

    while True:
        response = input("> ").strip()
        if not response and default:
            return default
        try:
            idx = int(response) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            if response in options:
                return response
        print("Please enter a valid number or name")


def prompt_yes_no(question: str, default: bool = True) -> bool:
    """Prompt for yes/no response."""
    suffix = " [Y/n]: " if default else " [y/N]: "
    response = input(question + suffix).strip().lower()
    if not response:
        return default
    return response[0] == "y"


def configure_ai_service() -> tuple[str, Optional[str]]:
    """Configure AI service and API key."""
    print("\nLet's configure your default AI service:")
    service = prompt_choice(
        "Which AI service would you like to use?",
        AVAILABLE_SERVICES,
        default="anthropic",
    )

    if service in ["anthropic", "groq"]:
        print(f"\nEnter your {service.title()} API key")
        print("(press Enter to use environment variable)")
        api_key = input("> ").strip() or None
        if api_key:
            config_manager.set(f"{service}_api_key", api_key)

    return service, api_key


def configure_script(script_name: str) -> None:
    """Configure a specific script."""
    if script_name not in SCRIPT_INFO:
        print(f"Script '{script_name}' not found or not configurable")
        return

    script_info = SCRIPT_INFO[script_name]
    print(f"\nConfiguring {script_info['name']} ({script_name})")

    # Allow script-specific AI service
    if "ai_service" in script_info["configurable"]:
        use_different_service = prompt_yes_no(
            "Use different AI service than default?", default=False
        )
        if use_different_service:
            service = prompt_choice(
                "Select AI service:",
                AVAILABLE_SERVICES,
                default=config_manager.get("default_ai_service"),
            )
            config_manager.set(f"tools.{script_name}.ai_service", service)

    # Script-specific configurations
    if script_name == "do" and "write_to_terminal" in script_info["configurable"]:
        write_to_terminal = prompt_yes_no(
            "Write commands to terminal instead of executing?", default=True
        )
        config_manager.set("tools.do.write_to_terminal", write_to_terminal)


def setup_wizard(script_name: Optional[str] = None) -> None:
    """Run the setup wizard for all or specific script."""
    if script_name:
        if script_name not in SCRIPT_INFO:
            print(f"Error: '{script_name}' is not a configurable script")
            return
        configure_script(script_name)
        return

    print("Welcome to tool-use setup!")

    # Configure global AI settings
    service, _ = configure_ai_service()
    config_manager.set("default_ai_service", service)

    # Offer to configure specific scripts
    while True:
        print("\nWould you like to configure a specific script?")
        options = [f"{name} - {info['name']}" for name, info in SCRIPT_INFO.items()]
        options.append("Done")

        choice = prompt_choice("Select a script to configure:", options)
        if choice == "Done":
            break

        script_name = choice.split(" - ")[0]
        configure_script(script_name)

    print("\nConfiguration complete!")
    print("You can run 'ai setup <script>' anytime to update script-specific settings")
    print(f"Or manually edit ~/.tool-use/config.toml")
