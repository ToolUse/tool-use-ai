import sys
import argparse
import subprocess
import pkg_resources
from .scripts._script_dependencies import SCRIPT_DEPENDENCIES
from .scripts import ai_cli


def ensure_dependencies(script_name):
    if script_name not in SCRIPT_DEPENDENCIES:
        return
        
    for package in SCRIPT_DEPENDENCIES[script_name]:
        try:
            pkg_resources.require(package)
        except pkg_resources.DistributionNotFound:
            print(f"Installing required dependency: {package}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def main():
    parser = argparse.ArgumentParser(description="Run tool-use scripts")
    parser.add_argument(
        "script_name",
        choices=list(SCRIPT_DEPENDENCIES.keys()),  # Dynamically get script choices
        help="Name of the script to run",
    )
    parser.add_argument(
        "args", nargs=argparse.REMAINDER, help="Arguments for the script"
    )

    args = parser.parse_args()

    try:
        # Try to import dependencies, install if missing
        ensure_dependencies(args.script_name)
        
        # Only import after ensuring dependencies
        from .utils.ai_service import AIService  # Move this import here
        
        # Import and run the script
        if args.script_name == "cal":
            from .scripts import cal
            cal.main(args.args)
        elif args.script_name == "make-obsidian-plugin":
            from .scripts import obsidian_plugin
            obsidian_plugin.main(args.args)
        elif args.script_name == "script1":
            from .scripts import script1
            script1.main(args.args)
        elif args.script_name == "scriptomatic":
            from .scripts import scriptomatic
            scriptomatic.main(args.args)
        
        elif args.script_name == "do":
            ai_cli.main(args.args)
    except Exception as e:
        print(f"Error running {args.script_name}: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
