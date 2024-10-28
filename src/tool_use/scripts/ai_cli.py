#!/usr/bin/env python
import argparse
import os
import platform
import subprocess
import sys
from typing import Dict, Optional
from ..utils.ai_service import AIService
from ..config_manager import config_manager


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
        print(f"Error querying AI service: {e}", file=sys.stderr)
        sys.exit(1)


def get_command_explanation(
    command: str, service_type: str, model: Optional[str]
) -> str:
    ai_service = AIService(service_type, model)
    explanation_prompt = f"""Explain this command in clear, concise terms:
{command}

Explain:
1. What each part does
2. Any important flags/options used
3. Any potential gotchas or limitations

Keep the explanation brief but informative."""

    try:
        return ai_service.query(explanation_prompt).strip()
    except Exception as e:
        print(f"Error getting explanation: {e}", file=sys.stderr)
        return "Unable to get explanation"


def write_to_terminal(command: str) -> None:
    # Note: This is a simplistic version - might need adjustment based on terminal type
    sys.stdout.write(command)
    sys.stdout.flush()


def execute_command(command: str) -> None:
    try:
        result = subprocess.run(
            command, shell=True, check=True, text=True, capture_output=True
        )
        print(f"\nCommand output:\n{result.stdout}")
        if result.stderr:
            print(f"Error output:\n{result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code: {e.returncode}", file=sys.stderr)
        if e.stdout:
            print(f"Command output:\n{e.stdout}")
        if e.stderr:
            print(f"Error output:\n{e.stderr}")


def main(args=None):
    parser = argparse.ArgumentParser(description="AI CLI Tool")
    parser.add_argument(
        "--service",
        choices=["ollama", "groq", "anthropic"],
        help="Override default AI service",
    )
    parser.add_argument("--model", help="Override default AI model")

    # Parse known args first to separate flags from the input text
    known_args, unknown_args = parser.parse_known_args(args)

    # Get tool config
    tool_config = config_manager.get_tool_config("do")

    # Command-line args override config
    service = known_args.service or tool_config["ai_service"]
    model = known_args.model or tool_config["ai_model"]
    write_to_terminal_mode = tool_config.get("write_to_terminal", True)

    # Get the task description
    input_text = " ".join(unknown_args) if unknown_args else ""
    if not input_text:
        parser.print_help()
        sys.exit(1)

    # Get environment info and query AI
    env_info = get_environment_info()
    command = query_ai_service(input_text, service, model, env_info)

    # Show the command
    print(f"\n\033[92m{command}\033[0m")

    while True:
        if write_to_terminal_mode:
            prompt = (
                "Press 'Enter' to write to terminal, 'e' to explain, or 'n' to cancel: "
            )
        else:
            prompt = "Press 'Enter' to execute, 'e' to explain, or 'n' to cancel: "

        choice = input(prompt).lower()

        if choice == "e":
            print("\nExplanation:")
            explanation = get_command_explanation(command, service, model)
            print(explanation)
            print()  # Extra newline for readability
            continue

        if choice == "n":
            print("Operation cancelled.")
            break

        if choice == "":
            if write_to_terminal_mode:
                write_to_terminal(command)
            else:
                execute_command(command)
            break


if __name__ == "__main__":
    main()
