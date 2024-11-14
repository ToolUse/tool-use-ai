#!/usr/bin/env python
import argparse
import os
import platform
import subprocess
import sys
import time
from typing import Dict, Optional
from pynput.keyboard import Controller
from rich.console import Console
from ..utils.ai_service import AIService
from ..config_manager import config_manager

console = Console()
keyboard = Controller()


def get_environment_info() -> Dict[str, str]:
    return {
        "current_directory": os.getcwd(),
        "os_info": f"{platform.system()} {platform.release()}",
        "shell": os.getenv("SHELL", "unknown shell"),
    }


def query_ai_service(
    input_text: str, service_type: str, model: Optional[str], env_info: Dict[str, str]
) -> str:
    ai_service = AIService(service_type, model)
    prompt = f"""You are an expert programmer who is a master of the terminal. 
    Your task is to come up with the perfect command to accomplish the following task. 
    Respond with the command only. No comments. No backticks around the command. 
    The command must be able to be run in the terminal verbatim without error.
    Be sure to accomplish the user's task exactly. 
    You must only return one command. I need to execute your response verbatim.
    Current directory: {env_info['current_directory']}
    Operating System: {env_info['os_info']}
    Shell: {env_info['shell']}
    Do not hallucinate.
    Here is the task: {input_text}"""

    try:
        return ai_service.query(prompt).strip()
    except Exception as e:
        console.print(f"[red]Error querying AI service: {e}[/red]", file=sys.stderr)
        sys.exit(1)


def write_to_terminal(command: str) -> None:
    sys.stdout.write("\r" + " " * (len(command) + 1) + "\r")
    sys.stdout.flush()
    time.sleep(0.1)
    keyboard.type(command)


def execute_command(command: str) -> None:
    try:
        result = subprocess.run(
            command, shell=True, check=True, text=True, capture_output=True
        )
        if result.stdout:
            console.print("\nCommand output:", style="green")
            console.print(result.stdout)
        if result.stderr:
            console.print("\nWarning output:", style="yellow")
            console.print(result.stderr)
    except subprocess.CalledProcessError as e:
        console.print(f"\n[red]Command failed with return code: {e.returncode}[/red]")
        if e.stdout:
            console.print("\nCommand output:")
            console.print(e.stdout)
        if e.stderr:
            console.print("\n[red]Error output:[/red]")
            console.print(e.stderr)


def get_command_explanation(command: str, service: str, model: Optional[str]) -> str:
    """Get an explanation of what the command does."""
    ai_service = AIService(service, model)
    prompt = f"""Explain what this shell command does in detail: {command}
    Break down each part and flag. Be concise but thorough."""

    try:
        return ai_service.query(prompt).strip()
    except Exception as e:
        return f"Could not get explanation: {e}"


def get_user_query() -> str:
    """Prompt the user for their natural language query."""
    console.print("\nWhat command would you like me to generate?")
    query = input("> ").strip()
    while not query:
        console.print("[yellow]Query cannot be empty. Please try again:[/yellow]")
        query = input("> ").strip()
    return query


def main(args=None):
    parser = argparse.ArgumentParser(description="AI CLI Tool")
    parser.add_argument(
        "--service",
        choices=["ollama", "groq", "anthropic"],
        help="Override default AI service",
    )
    parser.add_argument("--model", help="Override default AI model")
    parser.add_argument(
        "--debug", action="store_true", help="Show additional debug information"
    )

    # Parse known args first to separate flags from the input text
    known_args, unknown_args = parser.parse_known_args(args)

    # Get tool config
    try:
        tool_config = config_manager.get_tool_config("do")
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        console.print("[yellow]Using default configuration[/yellow]")
        tool_config = {
            "ai_service": "anthropic",
            "ai_model": None,
            "write_to_terminal": True,
        }

    # Command-line args override config
    service = known_args.service or tool_config["ai_service"]
    model = known_args.model or tool_config.get("ai_model")
    write_to_terminal_mode = tool_config.get("write_to_terminal", True)

    # Debug output if requested
    if known_args.debug:
        console.print("\nDebug Information:", style="blue")
        console.print(f"Service: {service}")
        console.print(f"Model: {model}")
        console.print(f"Write to terminal: {write_to_terminal_mode}")
        console.print(f"Environment: {get_environment_info()}")

    # Get the task description from arguments or prompt
    input_text = " ".join(unknown_args) if unknown_args else ""
    if not input_text:
        input_text = get_user_query()

    # Get environment info and query AI
    env_info = get_environment_info()
    command = query_ai_service(input_text, service, model, env_info)

    # Show the command preview
    console.print(f"\n[green]{command}[/green]")

    while True:
        if write_to_terminal_mode:
            prompt = (
                "Press 'Enter' to write to terminal, 'e' to explain, or 'n' to cancel: "
            )
        else:
            prompt = "Press 'Enter' to execute, 'e' to explain, or 'n' to cancel: "

        choice = input(prompt).lower()

        if choice == "e":
            explanation = get_command_explanation(command, service, model)
            console.print("\n[blue]Explanation:[/blue]")
            console.print(explanation)
            console.print()  # Extra newline for readability
            continue

        if choice == "n":
            console.print("[yellow]Operation cancelled.[/yellow]")
            break

        if choice == "":
            if write_to_terminal_mode:
                write_to_terminal(command)
            else:
                execute_command(command)
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]An unexpected error occurred: {e}[/red]")
        sys.exit(1)
