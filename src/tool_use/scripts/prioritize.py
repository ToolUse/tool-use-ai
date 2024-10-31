#!/usr/bin/env python
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from ..utils.shallowgram import Shallowgram, check_ffmpeg
from ..utils.ai_service import AIService
from ..config_manager import config_manager
from pydantic import BaseModel, Field
from typing import List

console = Console()

ASCII_ART = """
 ____       _            _ _   _          
|  _ \ _ __(_) ___  _ __(_) |_(_)_______ 
| |_) | '__| |/ _ \| '__| | __| |_  / _ \\
|  __/| |  | | (_) | |  | | |_| |/ /  __/
|_|   |_|  |_|\___/|_|  |_|\__|_/___\___|
"""

class PriorityTask(BaseModel):
    """A single task with its priority level and details"""
    title: str = Field(description="The main task description")
    priority: str = Field(description="Priority level: 'high', 'medium', or 'low'")
    details: str = Field(description="Be very gentle with the user. They might be stressed. Meet them where they are!")

class TaskAnalysis(BaseModel):
    """Complete analysis of tasks from a brain dump"""
    opening_message: str = Field(description="A brief, empathetic opening message acknowledging their situation")
    priority_tasks: List[PriorityTask] = Field(description="List of tasks extracted and prioritized")
    explanation: str = Field(description="Explanation for why these tasks are important, and why others might be less important, if necessary.")
    next_steps: List[str] = Field(description="Easy to digest, concise, and actionable next steps for the user to take next.")

def extract_tasks(transcript: str) -> TaskAnalysis:
    """Use OpenAI to extract and prioritize tasks from the transcript."""
    ai_service = AIService(service_type="openai")
    
    system_prompt = """You are in conversation with a user, who will ramble about everything they need to do in their life. You are a helpful, friendly, empathetic AI assistant who is tasked with extracting and prioritizing tasks from the user's ramblings. Your job is to:
    1. Start with a brief, empathetic opening message acknowledging their situation
    2. Extract actionable tasks from the transcript
    3. Prioritize them appropriately
    4. Provide strategic insights about the tasks in a friendly, conversational tone
    5. Suggest concrete next steps that the user can take next to get back on track
    
    Keep task descriptions clear and actionable. Dont say things like user, don't be in third person, you are in direct conversation with the user!
    
    For the opening_message, provide a brief, friendly acknowledgment of their situation. Examples:
    - "Wow, you've got quite a bit on your plate! Let's sort this out together."
    - "I can hear how overwhelming this feels. Let's break it down into manageable pieces."
    - "It sounds like you're juggling a lot right now. Let's get organized!"
    """
    
    prompt = f"transcript: \n{transcript}"
    
    return ai_service.query_structured(prompt, TaskAnalysis, system_prompt)

def display_results(analysis: TaskAnalysis):
    """Display the prioritized tasks in a rich format."""
    
    # Display opening message
    console.print(Panel(
        Text(analysis.opening_message, style="bold cyan"),
        border_style="cyan",
        padding=(1, 2)
    ))
    
    # Create the tasks table
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Priority", style="bold", width=12)
    table.add_column("Task", style="", width=40)
    table.add_column("Details", style="dim", width=30)
    
    # Add tasks to table with appropriate styling
    for task in analysis.priority_tasks:
        style = {
            "high": "red bold",
            "medium": "yellow",
            "low": "green"
        }.get(task.priority.lower(), "white")
        
        table.add_row(
            task.priority.upper(),
            Text(task.title, style=style),
            Text(task.details + "\n") if task.details else ""
        )
    
    # Display the table
    console.print(Panel(table, title="[bold]Prioritized Tasks[/bold]", 
                       border_style="blue"))
    
    # Display explanation
    if analysis.explanation:
        explanation_panel = Panel(
            analysis.explanation,
            title="[bold]Analysis[/bold]",
            border_style="cyan",
            padding=(1, 2)
        )
        console.print(explanation_panel)
    
    # Display next steps
    if analysis.next_steps:
        next_steps_text = "\n".join(f"[bold cyan]→[/bold cyan] {step}" for step in analysis.next_steps)
        next_steps_panel = Panel(
            next_steps_text,
            title="[bold]Next Steps[/bold]",
            border_style="green",
            padding=(1, 2)
        )
        console.print(next_steps_panel)

def main(args=None):
    if not check_ffmpeg():
        sys.exit(1)
    
    console.print(Text(ASCII_ART, style="bold blue"))
    console.print("\n[bold cyan]Welcome to Prioritize - Your AI Task Organizer[/bold cyan]")
    console.print("\n[yellow]Start your brain dump - speak freely about all your tasks and thoughts.[/yellow]")
    console.print("[yellow]Press Enter when you're done recording.[/yellow]\n")
    
    # Get tool config
    tool_config = config_manager.get_tool_config("transcribe")
    whisperfile_path = tool_config.get("whisperfile_path")
    
    # Record and transcribe
    try:
        # Create temporary recording file
        input_path = Path("braindump_recording.wav")
        
        # Initialize Shallowgram
        client = Shallowgram(whisperfile_path=whisperfile_path)
        
        # Record audio
        from ..utils.shallowgram import record_audio
        record_audio(str(input_path), verbose=False)
        
        console.print("\n[cyan]Processing your brain dump...[/cyan]")
        
        # Transcribe
        result = client.transcribe(str(input_path))
        transcript = result['text']
        
        # Extract and prioritize tasks
        console.print("[cyan]Analyzing and prioritizing tasks...[/cyan]")
        analysis = extract_tasks(transcript)
        
        # Display results
        display_results(analysis)
        
    except Exception as e:
        console.print(f"[red]Error during processing: {str(e)}[/red]")
        sys.exit(1)
    finally:
        # Cleanup recording
        if input_path.exists():
            input_path.unlink()

if __name__ == "__main__":
    main()
