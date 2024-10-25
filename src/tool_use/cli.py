import sys
import argparse
from .scripts import script1, obsidian_plugin, ai_cli


def main():
    parser = argparse.ArgumentParser(description="Run tool-use scripts")
    parser.add_argument(
        "script_name",
        choices=["script1", "make-obsidian-plugin", "cli"],
        help="Name of the script to run",
    )
    parser.add_argument(
        "args", nargs=argparse.REMAINDER, help="Arguments for the script"
    )

    args = parser.parse_args()

    try:
        if args.script_name == "script1":
            script1.main(args.args)
        elif args.script_name == "make-obsidian-plugin":
            obsidian_plugin.main(args.args)
        elif args.script_name == "do":
            ai_cli.main(args.args)
    except Exception as e:
        print(f"Error running {args.script_name}: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
