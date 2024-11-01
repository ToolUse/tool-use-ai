#!/usr/bin/env python
import argparse
import sys
from pathlib import Path
from ..utils.shallowgram import Shallowgram, check_ffmpeg
from ..config_manager import config_manager
from rich.console import Console

console = Console()

def main(args=None):
    if not check_ffmpeg():
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Transcribe and analyze audio files")
    parser.add_argument("file", nargs="?", help="Path to the audio file to transcribe")
    parser.add_argument("--output", "-o", help="Output file path (optional)")
    parser.add_argument("--full", "-f", action="store_true", help="Perform full analysis")
    
    args = parser.parse_args(args)
    
    # Get tool config
    tool_config = config_manager.get_tool_config("transcribe")
    whisperfile_path = tool_config.get("whisperfile_path")
    vault_path = tool_config.get("vault_path")
    
    if args.file:
        input_path = Path(args.file)
        if not input_path.exists():
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
    else:
        # Record mode
        from ..utils.shallowgram import record_audio
        print("Recording mode - press Enter to stop recording")
        input_path = Path("recording.wav")
        record_audio(str(input_path), verbose=False)
        
    try:
        client = Shallowgram(whisperfile_path=whisperfile_path, vault_path=vault_path)
        result = client.transcribe(str(input_path), full_analysis=args.full)
        
        if args.full:
            from ..utils.shallowgram import display_rich_output
            display_rich_output(
                result['text'],
                result['summary'],
                result['sentiment'],
                result['intent'],
                result['topics']
            )
        else:
            if args.output:
                output_path = Path(args.output)
                output_path.write_text(result['text'])
                print(f"Transcription saved to: {output_path}")
            else:
                print("\nTranscription:")
                print(result['text'])
            
    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        sys.exit(1)
    finally:
        # Cleanup recording if we created it
        if not args.file and input_path.exists():
            input_path.unlink()

if __name__ == "__main__":
    main() 