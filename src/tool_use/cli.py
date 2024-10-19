# src/tool_use/cli.py
import sys
import argparse
from .scripts import script1, script2  # Import your scripts here

def main():
    parser = argparse.ArgumentParser(description="Run AI scripts.")
    parser.add_argument('script_name', help="Name of the script to run")
    parser.add_argument('script_args', nargs=argparse.REMAINDER, help="Arguments for the script")
    args = parser.parse_args()

    if args.script_name == 'script1':
        script1.main(args.script_args)
    elif args.script_name == 'script2':
        script2.main(args.script_args)
    else:
        print(f"Unknown script: {args.script_name}")
        sys.exit(1)