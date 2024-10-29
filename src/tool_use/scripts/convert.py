from pathlib import Path
MODEL = "gpt-4o"
AUTO_RUN = True

def main(args=None):
    from interpreter import interpreter

    try:
        interpreter.llm.model = MODEL
        interpreter.auto_run = AUTO_RUN
        interpreter.import_computer_api = True
        
        # Handle args passed from CLI instead of using sys.argv
        if args:
            message = " ".join(args)
            interpreter.messages.append(
                {"role": "user", "type": "message", "content": "Please convert this:" + message}
            )
        
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
    desktop_dir = str(Path.home() / "Desktop")
    interpreter.custom_instructions = f"""IMPORTANT: You are in file conversion mode. The user will specify a file, and a type they want it converted to. Infer the file's current format from the path provided, and convert the file to the specified format set by the user. By default, DO NOT MODIFY THE ORIGINAL FILE. Create a copy and convert this copy into the specified format, saved to the same directory where the original file came from. If a path is not provided, always default to the Desktop dir ({desktop_dir}). Do not modify the file name, only the format. Use any tool you might need like ffmpeg, , and assume it is installed. If it is not, then install it first. ALWAYS assume the tool is installed, just try to use the tool

    If the operation was successful, say 'The file was converted successfully!' If unsuccessful, keep trying until you succeed. If you are absolutely certain you cannot convert it, say 'The file could not be converted'"""

    interpreter.chat()