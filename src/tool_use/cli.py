import sys
import argparse
import subprocess
from importlib.metadata import version, PackageNotFoundError
from .scripts._script_dependencies import SCRIPT_DEPENDENCIES
from .utils.config_wizard import setup_wizard, SCRIPT_INFO


def ensure_dependencies(script_name):
    if script_name not in SCRIPT_DEPENDENCIES:
        return

    for package in SCRIPT_DEPENDENCIES[script_name]:
        try:
            version(package)
        except PackageNotFoundError:
            print(f"Installing required dependency: {package}")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--upgrade", package]
            )


def main():
    parser = argparse.ArgumentParser(description="Run tool-use scripts")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Configure tool-use settings")
    setup_parser.add_argument(
        "script",
        nargs="?",
        choices=list(SCRIPT_INFO.keys()),
        help="Configure specific script",
    )

    # Add all script commands
    all_scripts = {
        "do": "AI command generation",
        "make-obsidian-plugin": "Generate Obsidian plugin",
        "cal": "Calendar tool",
        "convert": "Convert anything to anything",
        "transcribe": "Transcribe and analyze audio",
        "prioritize": "Brain dump and prioritize tasks",
        "log": "Track your activities",
        "marketing-plan": "Use a marketing agency of AI agents to create a marketing plan",
        "posture": "Use the webcam and a tiny vision model to analyze your posture and focus",
    }

    for name, help_text in all_scripts.items():
        script_parser = subparsers.add_parser(name, help=help_text)
        script_parser.add_argument(
            "args", nargs=argparse.REMAINDER, help=f"Arguments for {name}"
        )

    args = parser.parse_args()

    try:
        if args.command == "setup":
            setup_wizard(args.script if hasattr(args, "script") else None)
            return

        script_name = args.command
        script_args = args.args if hasattr(args, "args") else []

        if script_name not in SCRIPT_DEPENDENCIES:
            parser.print_help()
            sys.exit(1)

        # Try to import dependencies, install if missing
        ensure_dependencies(script_name)
        
        # Map script names to their module paths
        script_modules = {
            "do": "ai_cli",
            "make-obsidian-plugin": "obsidian_plugin",
            "cal": "cal",
            "convert": "convert",
            "transcribe": "transcribe",
            "prioritize": "prioritize",
            "log": "activity_tracker",
            "marketing-plan": "marketing_agency",
            "posture": "posture",
        }

        # Dynamic import of only the needed module
        if script_name in script_modules:
            module_name = script_modules[script_name]
            module = __import__(f"tool_use.scripts.{module_name}", fromlist=["main"])
            module.main(script_args)
        else:
            print(f"Unknown script: {script_name}")
            sys.exit(1)

    except Exception as e:
        print(f"Error running {args.command}: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
