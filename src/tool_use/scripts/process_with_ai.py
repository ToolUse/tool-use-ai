from ..utils.ai_service import AIService
from ..config_manager import config_manager
import argparse
import sys


def process_with_ai(text: str) -> str:
    """Internal function that uses AI to process text."""
    ai = AIService()
    prompt = f"Please analyze this text and provide key insights: {text}"
    result = ai.query(prompt)

    # If result is a list, process each item
    if isinstance(result, list):
        return "\n".join(
            item.text if hasattr(item, "text") else str(item) for item in result
        )

    # If it's a single ContentBlock, return its text
    if hasattr(result, "text"):
        return result.text

    # If it's already a string, return it directly
    if isinstance(result, str):
        return result

    # If it's any other type, convert to string
    return str(result)


def main(args):
    parser = argparse.ArgumentParser(description="Process text files")
    parser.add_argument("input_file", help="Path to the input file")
    parser.add_argument("--output", help="Path to output file (optional)")

    parsed_args = parser.parse_args(args)

    try:
        # Read the input file
        with open(parsed_args.input_file, "r") as f:
            content = f.read()

        # Process the content using AI internally
        results = process_with_ai(content)

        # Handle the output
        if parsed_args.output:
            with open(parsed_args.output, "w") as f:
                f.write(results)
        else:
            print(results)

    except FileNotFoundError:
        print(f"Error: Could not find file {parsed_args.input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        sys.exit(1)
