import sys
import argparse
import subprocess
import pkg_resources
from .scripts._script_dependencies import SCRIPT_DEPENDENCIES
from .scripts import ai_cli
from .utils.config_wizard import setup_wizard, SCRIPT_INFO


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
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Configure tool-use settings")
    setup_parser.add_argument(
        "script",
        nargs="?",
        choices=list(SCRIPT_INFO.keys()),
        help="Configure specific script",
    )

    # Script command for backwards compatibility
    script_parser = subparsers.add_parser("script", help="Run a specific script")
    script_parser.add_argument(
        "script_name",
        choices=list(SCRIPT_DEPENDENCIES.keys()),
        help="Name of the script to run",
    )
    script_parser.add_argument(
        "args", nargs=argparse.REMAINDER, help="Arguments for the script"
    )

    # Individual command parsers
    do_parser = subparsers.add_parser("do", help="AI command generation")
    do_parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments for do")

    obsidian_parser = subparsers.add_parser(
        "make-obsidian-plugin", help="Generate Obsidian plugin"
    )
    obsidian_parser.add_argument(
        "args", nargs=argparse.REMAINDER, help="Arguments for make-obsidian-plugin"
    )

    script1_parser = subparsers.add_parser("script1", help="Run script1")
    script1_parser.add_argument(
        "args", nargs=argparse.REMAINDER, help="Arguments for script1"
    )

    scriptomatic_parser = subparsers.add_parser("scriptomatic", help="Run scriptomatic")
    scriptomatic_parser.add_argument(
        "args", nargs=argparse.REMAINDER, help="Arguments for scriptomatic"
    )

    cal_parser = subparsers.add_parser("cal", help="Calendar tool")
    cal_parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments for cal")

    args = parser.parse_args()

    try:
        if args.command == "setup":
            setup_wizard(args.script if hasattr(args, "script") else None)
            return

        if args.command == "script":
            script_name = args.script_name
            script_args = args.args
        else:
            script_name = args.command
            script_args = args.args if hasattr(args, "args") else []

        if script_name not in SCRIPT_DEPENDENCIES:
            parser.print_help()
            sys.exit(1)

        # Try to import dependencies, install if missing
        ensure_dependencies(script_name)

        # Import and run the script
        if script_name == "do":
            ai_cli.main(script_args)
        elif script_name == "make-obsidian-plugin":
            from .scripts import obsidian_plugin

            obsidian_plugin.main(script_args)
        elif script_name == "script1":
            from .scripts import script1

            script1.main(script_args)
        elif script_name == "scriptomatic":
            from .scripts import scriptomatic

            scriptomatic.main(script_args)
        elif script_name == "cal":
            from .scripts import cal

            cal.main(script_args)

    except Exception as e:
        print(f"Error running {args.command}: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
