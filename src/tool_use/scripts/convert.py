import argparse
import os
import sys
import time
from pathlib import Path

MODEL="gpt-4o"
AUTO_RUN=True



def main(args=None):
    from interpreter import interpreter

    try:
        interpreter.llm.model = MODEL
        interpreter.auto_run = AUTO_RUN
        interpreter.import_computer_api = True
        start_terminal_interface(interpreter)
    except KeyboardInterrupt:
        try:
            interpreter.computer.terminate()

        except KeyboardInterrupt:
            pass
    finally:
        interpreter.computer.terminate()




def start_terminal_interface(interpreter):
    """
    Meant to be used from the command line. Parses arguments, starts OI's terminal interface.
    """
    
    # cv shortcut
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        message = " ".join(sys.argv[1:])
        interpreter.messages.append(
            {"role": "user", "type": "message", "content": "Please convert this:" + message}
        )
        sys.argv = sys.argv[:1]
        
        
        
        

        desktop_dir = str(Path.home() / "Desktop")
        interpreter.custom_instructions = f"""IMPORTANT: You are in file conversion mode. The user will specify a file, and a type they want it converted to. Infer the file's current format from the path provided, and convert the file to the specified format set by the user. By default, DO NOT MODIFY THE ORIGINAL FILE. Create a copy and convert this copy into the specified format, saved to the same directory where the original file came from. If a path is not provided, always default to the Desktop dir ({desktop_dir}). Do not modify the file name, only the format. Use any tool you might need like ffmpeg, , and assume it is installed. If it is not, then install it first. ALWAYS assume the tool is installed, just try to use the tool
        
        If the operation was successful, say 'The file was converted successfully!' If unsuccessful, keep trying until you succeed. If you are absolutely certain you cannot convert it, say 'The file could not be converted'"""



        # If the operation was successful, say 'The file was converted successfully.', then run `computer.terminate()` immediately after to exit. If unsuccessful, keep trying until you succeed. If you are absolutely certain you cannot convert it, say 'The file could not be converted', then exit. BE SURE TO ALWAYS EXIT AFTER IT HAS BEEN CONVERTED."""


    ### Set some helpful settings we know are likely to be true

    if interpreter.llm.model == "gpt-4" or interpreter.llm.model == "openai/gpt-4":
        if interpreter.llm.context_window is None:
            interpreter.llm.context_window = 6500
        if interpreter.llm.max_tokens is None:
            interpreter.llm.max_tokens = 4096
        if interpreter.llm.supports_functions is None:
            interpreter.llm.supports_functions = (
                False if "vision" in interpreter.llm.model else True
            )

    elif interpreter.llm.model.startswith("gpt-4") or interpreter.llm.model.startswith(
        "openai/gpt-4"
    ):
        if interpreter.llm.context_window is None:
            interpreter.llm.context_window = 123000
        if interpreter.llm.max_tokens is None:
            interpreter.llm.max_tokens = 4096
        if interpreter.llm.supports_functions is None:
            interpreter.llm.supports_functions = (
                False if "vision" in interpreter.llm.model else True
            )

    if interpreter.llm.model.startswith(
        "gpt-3.5-turbo"
    ) or interpreter.llm.model.startswith("openai/gpt-3.5-turbo"):
        if interpreter.llm.context_window is None:
            interpreter.llm.context_window = 16000
        if interpreter.llm.max_tokens is None:
            interpreter.llm.max_tokens = 4096
        if interpreter.llm.supports_functions is None:
            interpreter.llm.supports_functions = True

    if interpreter.llm.api_base:
        if (
            not interpreter.llm.model.lower().startswith("openai/")
            and not interpreter.llm.model.lower().startswith("azure/")
            and not interpreter.llm.model.lower().startswith("ollama")
            and not interpreter.llm.model.lower().startswith("jan")
            and not interpreter.llm.model.lower().startswith("local")
        ):
            interpreter.llm.model = "openai/" + interpreter.llm.model
        elif interpreter.llm.model.lower().startswith("jan/"):
            # Strip jan/ from the model name
            interpreter.llm.model = interpreter.llm.model[4:]
    interpreter.in_terminal_interface = True
    interpreter.chat()
