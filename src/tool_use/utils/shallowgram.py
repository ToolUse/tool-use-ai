#!/usr/bin/env python
import argparse
import subprocess
import os
import time
import pyaudio
import wave
from pydub import AudioSegment
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box
import select
import sys
from ..utils.ai_service import AIService
from urllib.request import urlretrieve

console = Console()

OLLAMA_MODEL = "llama3.1"
DEFAULT_WHISPER_MODEL = "tiny.en"
WHISPER_BASE_URL = "https://huggingface.co/Mozilla/whisperfile/resolve/main/"

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

ASCII_ART = """
  ____  _           _ _                                        
 / ___|| |__   __ _| | | _____      ____ _ _ __ __ _ _ __ ___  
 \___ \| '_ \ / _` | | |/ _ \ \ /\ / / _` | '__/ _` | '_ ` _ \ 
  ___) | | | | (_| | | | (_) \ V  V / (_| | | | (_| | | | | | |
 |____/|_| |_|\__,_|_|_|\___/ \_/\_/ \__, |_|  \__,_|_| |_| |_|
                                     |___/
"""

def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        console.print("[red]Error: FFmpeg is not installed.[/red]")
        console.print("[yellow]Please install FFmpeg using:[/yellow]")
        console.print("  brew install ffmpeg")
        return False

def install_whisper_model(model_name, whisperfile_path):
    full_model_name = f"whisper-{model_name}.llamafile"
    url = f"{WHISPER_BASE_URL}{full_model_name}"
    output_path = os.path.join(whisperfile_path, full_model_name)
    
    # Create the directory if it doesn't exist
    os.makedirs(whisperfile_path, exist_ok=True)
    
    console.print(f"[yellow]Downloading {full_model_name}...[/yellow]")
    try:
        urlretrieve(url, output_path)
        os.chmod(output_path, 0o755)
        console.print(f"[green]{full_model_name} installed successfully.[/green]")
    except Exception as e:
        console.print(f"[red]Error downloading model: {str(e)}[/red]")
        raise

def get_whisper_model_path(model_name, whisperfile_path, verbose):
    full_model_name = f"whisper-{model_name}.llamafile"
    model_path = os.path.join(whisperfile_path, full_model_name)
    if verbose:
        console.print(f"[yellow]Constructed model path: {model_path}[/yellow]")
    if not os.path.exists(model_path):
        console.print(f"[yellow]Whisper model {full_model_name} not found.[/yellow]")
        if input("Do you want to install it? (y/n): ").lower() == "y":
            install_whisper_model(model_name, whisperfile_path)
        else:
            raise FileNotFoundError(f"Whisper model {full_model_name} not found.")
    return model_path

def record_audio(output_file, verbose=False):
    p = pyaudio.PyAudio()

    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    console.print("[yellow]Recording... Press Enter to stop.[/yellow]")

    frames = []

    try:
        while True:
            if select.select([sys.stdin], [], [], 0.0)[0]:
                if sys.stdin.readline().strip() == "":
                    break
            data = stream.read(CHUNK)
            frames.append(data)
    except KeyboardInterrupt:
        pass

    console.print("[green]Finished recording.[/green]")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(output_file, "wb")
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b"".join(frames))
    wf.close()

    if verbose:
        console.print(f"[yellow]Audio file size: {os.path.getsize(output_file)} bytes[/yellow]")

def transcribe_audio(model_name, whisperfile_path, audio_file, verbose):
    model_path = get_whisper_model_path(model_name, whisperfile_path, verbose)
    command = f"{model_path} -f {audio_file} --gpu auto"

    if verbose:
        console.print(f"[yellow]Attempting to run command: {command}[/yellow]")

    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    stdout, stderr = process.communicate()

    if process.returncode != 0:
        console.print(f"[red]Command failed with return code {process.returncode}[/red]")
        console.print(f"[red]Error output: {stderr}[/red]")
        raise Exception(f"Transcription failed: {stderr}")

    if verbose:
        console.print(f"[green]Transcription output:[/green]\n{stdout}")

    return stdout

def summarize(text):
    ai_service = AIService()
    prompt = f"Summarize the following text. Just provide the summary, no preamble. Text:\n\n{text}"
    return ai_service.query(prompt)

def analyze_sentiment(text):
    ai_service = AIService()
    prompt = f"Analyze the sentiment of the following text and respond with ONLY ONE WORD - either 'positive', 'neutral', or 'negative':\n\n{text}"
    sentiment = ai_service.query(prompt).strip().lower()
    return sentiment if sentiment in ["positive", "neutral", "negative"] else "neutral"

def detect_intent(text):
    ai_service = AIService()
    prompt = f"Detect the intent in the following text. Respond with ONLY 2-4 words. Do not return any preamble, only the intent. Text: \n\n{text}"
    return ai_service.query(prompt)

def detect_topics(text):
    ai_service = AIService()
    prompt = f"Please identify the main topics in the following text. Return the topics as a comma-separated list, with no preamble or additional text. Text:\n\n{text}"
    return ai_service.query(prompt)

def export_to_markdown(content, vault_path, filename):
    os.makedirs(vault_path, exist_ok=True)
    file_path = os.path.join(vault_path, f"{filename}.md")
    with open(file_path, "w") as f:
        f.write(content)
    console.print(f"[green]Exported to {file_path}[/green]")

def convert_to_wav(input_file, output_file):
    audio = AudioSegment.from_file(input_file)
    audio.export(output_file, format="wav")

def get_sentiment_color(sentiment):
    return {
        "positive": "green3",
        "neutral": "gold1",
        "negative": "red1"
    }.get(sentiment, "white")

def display_rich_output(transcript, summary, sentiment, intent, topics):
    # Print the ASCII art directly without a border
    console.print(Text(ASCII_ART, style="bold blue"))

    # Clean the transcript text
    transcript_clean = "\n".join(
        line.partition("]")[2].strip()
        for line in transcript.split("\n")
        if line.strip()
    )

    # Create panels using Panel with expand=True
    transcript_panel = Panel(
        transcript_clean,
        title="Transcript",
        border_style="cyan",
        padding=(1, 2),
        expand=True,
    )

    summary_panel = Panel(
        summary,
        title="Summary",
        border_style="cyan",
        padding=(1, 2),
        expand=True,
    )

    # Analysis Results Table
    analysis_table = Table(show_header=False, box=box.SIMPLE, expand=True)
    analysis_table.add_column(style="bold", width=12)
    analysis_table.add_column()
    analysis_table.add_row(
        "Sentiment:",
        Text(sentiment.capitalize(), style=get_sentiment_color(sentiment)),
    )
    analysis_table.add_row("Intent:", Text(intent))
    analysis_table.add_row("Topics:", Text(topics))

    analysis_panel = Panel(
        analysis_table,
        title="Analysis Results",
        border_style="cyan",
        padding=(1, 2),
        expand=True,
    )

    # Print panels sequentially
    panels = [
        transcript_panel,
        summary_panel,
        analysis_panel,
    ]

    for panel in panels:
        console.print(panel)

class Shallowgram:
    def __init__(self, whisperfile_path=None, vault_path=None):
        self.whisperfile_path = whisperfile_path or os.path.expanduser("~/.whisperfiles")
        self.vault_path = vault_path or os.path.expanduser("~/Documents/ObsidianVault")
        self.ai_service = AIService()

    def transcribe(self, audio_file, model=DEFAULT_WHISPER_MODEL, full_analysis=False):
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        # Convert to wav if needed
        file_ext = os.path.splitext(audio_file)[1].lower()
        if file_ext != ".wav":
            wav_file = "temp_audio.wav"
            convert_to_wav(audio_file, wav_file)
            audio_file = wav_file

        try:
            transcript = transcribe_audio(model, self.whisperfile_path, audio_file, False)

            if full_analysis:
                summary = summarize(transcript)
                sentiment = analyze_sentiment(transcript)
                intent = detect_intent(transcript)
                topics = detect_topics(transcript)
                
                return {
                    'text': transcript,
                    'summary': summary,
                    'sentiment': sentiment,
                    'intent': intent,
                    'topics': topics
                }
            
            return {'text': transcript}

        finally:
            # Cleanup temporary file
            if file_ext != ".wav" and os.path.exists("temp_audio.wav"):
                os.remove("temp_audio.wav")