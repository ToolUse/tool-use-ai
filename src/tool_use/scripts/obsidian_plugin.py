from ..utils.ai_service import AIService
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.style import Style
from rich.text import Text
import os
import argparse
import subprocess
import json
import re
import shutil
from typing import Dict, Any
from pathlib import Path

console = Console()

PURPLE_STYLE = Style(color="purple")
LIGHT_PURPLE_STYLE = Style(color="bright_magenta")
ORANGE_STYLE = Style(color="#F67504")

ASCII_ART = """
   ___  _         _     _ _                     
  / _ \| |__  ___(_) __| (_) __ _ _ __          
 | | | | '_ \/ __| |/ _` | |/ _` | '_ \         
 | |_| | |_) \__ \ | (_| | | (_| | | | |        
  \___/|_.__/|___/_|\__,_|_|\__,_|_| |_|        
  ____  _             _                         
 |  _ \| |_   _  __ _(_)_ __                    
 | |_) | | | | |/ _` | | '_ \                   
 |  __/| | |_| | (_| | | | | |                  
 |_|   |_|\__,_|\__, |_|_| |_|                  
   ____         |___/             _             
  / ___| ___ _ __   ___ _ __ __ _| |_ ___  _ __ 
 | |  _ / _ \ '_ \ / _ \ '__/ _` | __/ _ \| '__|
 | |_| |  __/ | | |  __/ | | (_| | || (_) | |   
  \____|\___|_| |_|\___|_|  \__,_|\__\___/|_|   
"""

DEFAULT_OBSIDIAN_VAULT_PATH = os.path.expanduser("~/Documents/ObsidianVault")
SAMPLE_PLUGIN_REPO = "https://github.com/obsidianmd/obsidian-sample-plugin.git"


def read_file(file_path: str) -> str:
    with open(file_path, "r") as f:
        return f.read()


def write_file(file_path: str, content: str) -> None:
    with open(file_path, "w") as f:
        f.write(content)


def get_next_question(
    ai_service: AIService,
    plugin_info: Dict[str, Any],
    conversation_history: str,
    is_final: bool,
) -> str:
    if is_final:
        prompt = f"""
        Based on the following Obsidian plugin idea and conversation history, determine if you have enough information to create a comprehensive plugin. If you do, respond with "SUFFICIENT INFO". If not, ask one final question to gather the most critical information needed.

        Plugin Name: {plugin_info['name']}
        Plugin Description: {plugin_info['description']}

        Conversation History:
        {conversation_history}

        Provide only the question or "SUFFICIENT INFO", without any additional text.
        """
    else:
        prompt = f"""
        Based on the following Obsidian plugin idea and conversation history, determine if more information is needed to create a comprehensive plugin. If more information is needed, ask ONE specific, open-ended question to gather that information. If sufficient information has been gathered, respond with "SUFFICIENT INFO".

        Plugin Name: {plugin_info['name']}
        Plugin Description: {plugin_info['description']}

        Conversation History:
        {conversation_history}

        Provide only the question or "SUFFICIENT INFO", without any additional text.
        """

    return ai_service.query(prompt).strip()


def process_generated_content(content: str) -> str:
    parts = content.split("```", 2)
    if len(parts) >= 3:
        code = parts[1].strip()
        explanation = parts[2].strip()
        code = re.sub(r"^typescript\n", "", code)
        commented_explanation = "/*\n" + explanation + "\n*/"
        return f"{code}\n\n{commented_explanation}"
    return content.strip()


def handle_existing_directory(plugin_dir: str) -> bool:
    console.print(
        f"\n[yellow]WARNING:[/yellow] The directory '{plugin_dir}' already exists."
    )
    while True:
        choice = input("Do you want to (O)verwrite, (R)ename, or (C)ancel? ").lower()
        if choice == "o":
            shutil.rmtree(plugin_dir)
            return True
        elif choice == "r":
            new_name = input("Enter a new name for the plugin: ")
            new_dir = os.path.join(
                os.path.dirname(plugin_dir), new_name.lower().replace(" ", "-")
            )
            if os.path.exists(new_dir):
                print(
                    f"The directory '{new_dir}' also exists. Please choose a different name."
                )
            else:
                return new_dir
        elif choice == "c":
            return False
        print("Invalid choice. Please enter 'O', 'R', or 'C'.")


def get_vault_path() -> str:
    """Interactive prompt for Obsidian vault path"""
    default_path = DEFAULT_OBSIDIAN_VAULT_PATH
    console.print("\n[yellow]Obsidian Vault Location[/yellow]")

    while True:
        vault_path = input(
            f"Enter path to your Obsidian vault ({default_path}): "
        ).strip()
        if not vault_path:
            vault_path = default_path

        # Expand user directory if necessary
        vault_path = os.path.expanduser(vault_path)

        # Validate the path
        if not os.path.exists(vault_path):
            console.print(f"[red]Error:[/red] The path {vault_path} does not exist.")
            if (
                not input("Would you like to try a different path? (y/n): ")
                .lower()
                .startswith("y")
            ):
                raise ValueError("Valid Obsidian vault path required to continue")
            continue

        # Check for .obsidian folder to verify it's an Obsidian vault
        obsidian_dir = os.path.join(vault_path, ".obsidian")
        if not os.path.exists(obsidian_dir):
            console.print(
                f"[yellow]Warning:[/yellow] The path {vault_path} doesn't appear to be an Obsidian vault (.obsidian folder not found)"
            )
            if not input("Continue anyway? (y/n): ").lower().startswith("y"):
                continue

        return vault_path


def create_plugin(ai_service: AIService, plugin_info: Dict[str, Any]) -> None:
    conversation_history = ""

    # Get plugin requirements through conversation
    for i in range(3):
        is_final = i == 2
        next_question = get_next_question(
            ai_service, plugin_info, conversation_history, is_final
        )

        if next_question == "SUFFICIENT INFO":
            break

        console.print(f"\n[dark_magenta]Q: {next_question}[/dark_magenta]")
        answer = input("Your answer: ")
        conversation_history += f"Q: {next_question}\nA: {answer}\n\n"

    # Show spinner during plugin creation
    with console.status(
        "[cyan]Creating your Obsidian plugin...", spinner="dots"
    ) as status:
        plugin_dir = os.path.join(
            plugin_info["vault_path"], ".obsidian", "plugins", plugin_info["id"]
        )

        if os.path.exists(plugin_dir):
            result = handle_existing_directory(plugin_dir)
            if isinstance(result, str):
                plugin_dir = result
                plugin_info["id"] = os.path.basename(plugin_dir)
            elif not result:
                console.print("Plugin creation cancelled.")
                return

        os.makedirs(plugin_dir, exist_ok=True)

        # Clone sample plugin
        try:
            status.update("[cyan]Cloning sample plugin...")
            subprocess.run(
                ["git", "clone", SAMPLE_PLUGIN_REPO, plugin_dir],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(["rm", "-rf", os.path.join(plugin_dir, ".git")], check=True)
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error cloning the sample plugin: {e}[/red]")
            console.print(
                "[yellow]Please make sure you have git installed and have internet access.[/yellow]"
            )
            return

        main_ts_path = os.path.join(plugin_dir, "main.ts")
        existing_code = read_file(main_ts_path)

        # Generate plugin code
        status.update("[cyan]Generating plugin code...")
        prompt = f"""You are a TypeScript code generator for Obsidian plugins. Generate the complete content for main.ts.
Do not include any explanation or markdown formatting. The response should be exactly what goes in main.ts.

The plugin named "{plugin_info['name']}" should: {plugin_info['description']}

Additional context from our conversation:
{conversation_history}

Remember:
- Use TypeScript and Obsidian plugin best practices
- Include proper error handling
- Use async/await for asynchronous operations
- Add clear comments
- Implement settings if needed
"""

        try:
            generated_content = ai_service.query(prompt, max_tokens=4000)
            # Ensure the content starts with import or code
            generated_content = re.sub(
                r"^.*?import", "import", generated_content, flags=re.DOTALL
            )
            write_file(main_ts_path, generated_content)
        except Exception as e:
            console.print(f"[red]Error generating plugin code: {str(e)}[/red]")
            console.print("[yellow]Using default sample plugin code.[/yellow]")
            write_file(main_ts_path, existing_code)

        # Update manifest and package.json
        status.update("[cyan]Updating plugin configuration...")
        for file in ["manifest.json", "package.json"]:
            file_path = os.path.join(plugin_dir, file)
            with open(file_path, "r+") as f:
                data = json.load(f)
                data["name"] = plugin_info["name"]
                data["id"] = plugin_info["id"]
                data["description"] = plugin_info["description"]
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()

    # Show success message and next steps
    success_message = Text(
        f"Plugin '{plugin_info['name']}' created successfully in {plugin_dir}",
        style=ORANGE_STYLE,
    )
    console.print(Panel(success_message, expand=False, border_style=ORANGE_STYLE))

    next_steps = Table(show_header=False, box=None)
    next_steps.add_column(style=LIGHT_PURPLE_STYLE, no_wrap=True)
    next_steps.add_row(
        "1. Run 'npm install' in the plugin directory to install dependencies."
    )
    next_steps.add_row(
        "2. Review the main.ts file and make any necessary adjustments or fixes."
    )
    next_steps.add_row(
        "3. Run 'npm run dev' to compile the plugin and start development."
    )
    next_steps.add_row("4. Enable the plugin in Obsidian Community plugin settings.")
    next_steps.add_row("5. Test your plugin in Obsidian and adjust as needed.")
    next_steps.add_row(
        "6. When ready, run 'npm run build' to create the release version."
    )

    console.print(
        Panel(
            next_steps,
            expand=False,
            border_style=PURPLE_STYLE,
            title="Next Steps",
            title_align="center",
        )
    )


def main(args=None):
    if args is None:
        args = []

    parser = argparse.ArgumentParser(description="Obsidian Plugin Generator")
    parser.add_argument("name", help="Name of the plugin")
    parser.add_argument(
        "--vault-path",
        help="Path to Obsidian vault",
    )
    args = parser.parse_args(args)

    ascii_text = Text(ASCII_ART)
    ascii_text.stylize("purple", 0, 380)
    ascii_text.stylize("dark_magenta", 380, 600)
    ascii_text.stylize("bright_magenta", 600, 796)
    console.print(ascii_text)

    # Get vault path interactively if not provided via command line
    vault_path = args.vault_path if args.vault_path else get_vault_path()

    ai_service = AIService()

    plugin_info = {
        "name": args.name,
        "id": args.name.lower().replace(" ", "-"),
        "description": input(
            "Enter a general description of what your plugin will do: "
        ),
        "vault_path": vault_path,
    }

    create_plugin(ai_service, plugin_info)
