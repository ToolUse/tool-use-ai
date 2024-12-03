from typing import List, Dict
from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from ..utils.ai_service import AIService
from ..config_manager import config_manager
import random

console = Console()

DEFAULT_GUIDELINES = """Create a system prompt that incorporates these LLM prompting best practices:

1. Role & Context:
   - Define clear role/expertise level
   - Establish relevant context
   - Set output expectations

2. Task Structure:
   - Break into clear steps
   - Use chain-of-thought reasoning
   - Include examples if helpful

3. Output Control:
   - Specify format and boundaries
   - Define success criteria
   - Request explanations when needed

4. Quality & Safety:
   - Include fact-checking requirements
   - Request citations if relevant
   - Define confidence thresholds

5. Style:
   - Set tone and communication style
   - Specify how to handle uncertainty
   - Include error handling

Balance detail with clarity - the prompt should guide effectively while staying focused."""

class Participant:
    def __init__(self, name: str, persona: str):
        self.name = name
        self.persona = persona
        self.reasoning = ""
        self.submission = ""
        self.scores = []

class Judge:
    def __init__(self, name: str, persona: str):
        self.name = name
        self.persona = persona

class Mentor:
    def __init__(self, name: str, persona: str):
        self.name = name
        self.persona = persona

class MentorOutput(BaseModel):
    """Output format for creating a mentor"""
    name: str = Field(description="A creative name for the mentor")
    persona: str = Field(description="2-3 sentence description of their mentoring style, expertise, and background")

class FeedbackOutput(BaseModel):
    """Output format for mentor feedback"""
    feedback: str = Field(description="Constructive feedback on the submission")
    suggestions: str = Field(description="Specific suggestions for improvement")

# Pydantic models for structured outputs
class ParticipantOutput(BaseModel):
    """Output format for creating a participant"""
    name: str = Field(description="A creative name for the participant")
    persona: str = Field(description="2-3 sentence description of their background and personality")

class JudgeOutput(BaseModel):
    """Output format for creating a judge"""
    name: str = Field(description="A creative name for the judge")
    persona: str = Field(description="2-3 sentence description of their judging style and background")

class SubmissionOutput(BaseModel):
    """Output format for a participant's submission"""
    reasoning: str = Field(description="The participant's reasoning behind their submission")
    submission: str = Field(description="The participant's final prompt submission")

class JudgingOutput(BaseModel):
    """Output format for a judge's scoring"""
    score: float = Field(description="Score from 0-10")
    reasoning: str = Field(description="Explanation for the score")

def create_participant(ai: AIService, theme: str) -> Participant:
    system_prompt = "You are a creative AI helping to generate unique personas for a prompt-writing competition."
    persona_prompt = f"""Create a unique persona for a participant in a promptathon (prompt-writing competition).
    Theme: {theme}"""
    
    result = ai.query_structured(persona_prompt, ParticipantOutput, system_prompt)
    return Participant(result.name, result.persona)

def create_judge(ai: AIService) -> Judge:
    system_prompt = "You are a creative AI helping to generate unique personas for competition judges."
    judge_prompt = """Create a unique persona for a judge in a promptathon competition."""
    
    result = ai.query_structured(judge_prompt, JudgeOutput, system_prompt)
    return Judge(result.name, result.persona)

def create_mentor(ai: AIService) -> Mentor:
    system_prompt = "You are a creative AI helping to generate a persona for an experienced prompt engineering mentor."
    mentor_prompt = """Create a unique persona for a mentor in a promptathon competition. This mentor should be experienced in prompt engineering and able to provide constructive feedback."""
    
    result = ai.query_structured(mentor_prompt, MentorOutput, system_prompt)
    return Mentor(result.name, result.persona)

def get_submission(ai: AIService, participant: Participant, guidelines: str, theme: str, host_announcement: str) -> None:
    system_prompt = f"""You are a participant in a promptathon with the following persona:
    {participant.persona}"""
    
    prompt = f"""Guidelines:
    {guidelines}

    Theme: {theme}

    Host Announcement:
    {host_announcement}

    Create a submission for the promptathon. Think carefully about your approach."""

    result = ai.query_structured(prompt, SubmissionOutput, system_prompt)
    participant.reasoning = result.reasoning
    participant.submission = result.submission

def judge_submissions(ai: AIService, judge: Judge, participant: Participant) -> float:
    system_prompt = f"""You are a judge in a promptathon competition with the following persona:
    {judge.persona}"""
    
    prompt = f"""Review this submission for the promptathon:
    
    Participant: {participant.name}
    Participant Background: {participant.persona}
    
    Their Reasoning: {participant.reasoning}
    Their Submission: {participant.submission}
    
    Score this submission from 0-10, explaining your reasoning."""
    
    result = ai.query_structured(prompt, JudgingOutput, system_prompt)
    
    console.print(f"\n[cyan]Judge {judge.name} scores {participant.name}:[/cyan]")
    console.print(f"Score: {result.score}/10")
    console.print(f"Reasoning: {result.reasoning}")
    
    return result.score

def interview_winner(ai: AIService, winner: Participant) -> str:
    prompt = f"""You are interviewing the winner of the promptathon:
    {winner.persona}
    
    Their winning submission: {winner.submission}
    Their reasoning: {winner.reasoning}
    
    Generate a brief interview about how they feel winning and what they might have done differently.
    Format the interview with "Interviewer:" and "{winner.name}:" at the start of each speaker's lines."""
    
    raw_interview = ai.query(prompt)
    
    # Color the dialogue
    colored_interview = raw_interview.replace(
        "Interviewer:", "[bold cyan]Interviewer:[/bold cyan]"
    ).replace(
        f"{winner.name}:", f"[bold yellow]{winner.name}:[/bold yellow]"
    )
    
    return colored_interview

def create_host_announcement(ai: AIService, theme: str, num_participants: int, guidelines: str) -> str:
    prompt = f"""Create an enthusiastic host announcement for a promptathon competition with the following details:
    Theme: {theme}
    Number of Participants: {num_participants}
    Guidelines: {guidelines}
    
    The announcement should be energetic, welcoming, and motivating. Make it feel like a real hackathon opening speech."""
    
    return ai.query(prompt)

def display_participants(participants: List[Participant]) -> None:
    console.print("\n[bold cyan]🎭 Meet Our Contestants![/bold cyan]")
    for participant in participants:
        console.print(Panel.fit(
            f"[bold magenta]{participant.name}[/bold magenta]\n"
            f"{participant.persona}",
            border_style="cyan"
        ))

def display_judges(judges: List[Judge]) -> None:
    console.print("\n[bold blue]👨‍⚖️ Meet Our Distinguished Judges![/bold blue]")
    for judge in judges:
        console.print(Panel.fit(
            f"[bold yellow]{judge.name}[/bold yellow]\n"
            f"{judge.persona}",
            border_style="blue"
        ))

def display_mentors(mentors: List[Mentor]) -> None:
    console.print("\n[bold cyan]🎓 Meet Our Experienced Mentors![/bold cyan]")
    for mentor in mentors:
        console.print(Panel.fit(
            f"[bold magenta]{mentor.name}[/bold magenta]\n"
            f"{mentor.persona}",
            border_style="cyan"
        ))

def get_mentor_feedback(ai: AIService, mentor: Mentor, participant: Participant, submission: str, iteration: int) -> str:
    system_prompt = f"""You are a mentor in a promptathon with the following persona:
    {mentor.persona}
    
    You are mentoring a participant with this background:
    {participant.persona}
    
    This is iteration {iteration} of their submission."""
    
    prompt = f"""Review this prompt submission:
    {submission}
    
    Provide constructive feedback and specific suggestions for improvement.
    Be encouraging but thorough in your analysis."""
    
    result = ai.query_structured(prompt, FeedbackOutput, system_prompt)
    return result.feedback, result.suggestions

def iterative_submission_process(ai: AIService, participant: Participant, mentor: Mentor, guidelines: str, theme: str, host_announcement: str, num_iterations: int) -> None:
    console.print(f"\n[bold yellow]✍️ {participant.name} is working with {mentor.name}...[/bold yellow]")
    
    # Initial submission
    get_submission(ai, participant, guidelines, theme, host_announcement)
    initial_submission = participant.submission
    current_submission = initial_submission
    
    # Iterative feedback loop
    for i in range(num_iterations):
        console.print(f"\n[bold blue] Iteration {i+1}/{num_iterations}[/bold blue]")
        
        # Get mentor feedback
        feedback, suggestions = get_mentor_feedback(ai, mentor, participant, current_submission, i+1)
        
        # Display feedback in a panel
        console.print(Panel.fit(
            f"[bold blue]Submission:[/bold blue]\n"
            f'{current_submission}\n\n'
            f"[bold cyan]{mentor.name}'s Feedback:[/bold cyan]\n"
            f"{feedback}\n\n"
            f"[bold green]Suggestions:[/bold green]\n"
            f"{suggestions}",
            title=f"Mentoring Session {i+1}",
            border_style="blue"
        ))
        
        # Get revised submission
        system_prompt = f"""You are {participant.name} with this background:
        {participant.persona}
        
        You've received feedback from your mentor:
        Feedback: {feedback}
        Suggestions: {suggestions}"""
        
        prompt = f"""Based on your mentor's feedback, revise your submission:
        Original submission: {current_submission}
        
        Create an improved version that addresses the feedback while maintaining your unique style."""
        
        result = ai.query_structured(prompt, SubmissionOutput, system_prompt)
        current_submission = result.submission
        
        # Show the revision
        console.print(Panel(current_submission, title="Revised Submission", border_style="yellow"))
    
    # Store final submission and reasoning
    participant.submission = current_submission
    participant.reasoning = f"After {num_iterations} iterations of mentor feedback, I refined my submission to better achieve the competition goals while maintaining my unique perspective."

def main(args):
    config = config_manager.get_tool_config("promptathon")
    ai = AIService(service_type="openai", model="gpt-4o")
    
    console.print(fr"""\n[bold cyan]
 ____  ____   __   _  _  ____  ____  __  ____  _  _   __   __ _ 
(  _ \(  _ \ /  \ ( \/ )(  _ \(_  _)/ _\(_  _)/ )( \ /  \ (  ( \
 ) __/ )   /(  O )/ \/ \ ) __/  )( /    \ )(  ) __ ((  O )/    /
(__)  (__\_) \__/ \_)(_/(__)   (__)\_/\_/(__) \_)(_/ \__/ \_)__)
    [/bold cyan]""")
    # Interactive setup
    console.print("\n[bold cyan]🎪 Welcome to the Promptathon![/bold cyan]")
    
    # Get number of participants
    while True:
        try:
            num_participants = int(input("\nHow many participants would you like? (2-1000): "))
            if 2 <= num_participants <= 1000:
                break
            console.print("[red]Please enter a number between 2 and 1000[/red]")
        except ValueError:
            console.print("[red]Please enter a valid number[/red]")
    
    # Get theme
    console.print("\n[bold]What's the theme for this promptathon?[/bold]")
    console.print("Examples: 'Summarizing long documents', 'Generating creative stories', 'Teaching complex topics'")
    theme = input("> ").strip()
    while not theme:
        console.print("[red]Theme cannot be empty[/red]")
        theme = input("> ").strip()
    
    # Get guidelines
    default_guidelines = DEFAULT_GUIDELINES
    
    
    console.print("\n[bold]What are the guidelines for the competition?[/bold]")
    console.print("Examples: 'Create a system prompt that results in the most helpful AI assistant', 'Design a prompt that generates engaging stories'")
    console.print("[dim]Press Enter to use default guidelines, which are a set of prompting best practices[/dim]")
    guidelines = input("> ").strip()
    if not guidelines:
        guidelines = default_guidelines
        console.print(f"[dim]Using default guidelines: {default_guidelines}[/dim]")
    
    # Generate host announcement
    console.print("\n[bold yellow]🎙️ Generating host announcement...[/bold yellow]")
    host_announcement = create_host_announcement(ai, theme, num_participants, guidelines)
    
    console.print("\n[bold green]🎭 Creating Participants...[/bold green]")
    participants = [create_participant(ai, theme) for _ in range(num_participants)]
    display_participants(participants)
    
    console.print("\n[bold blue]👨‍⚖️ Assembling Judges...[/bold blue]")
    judges = [create_judge(ai) for _ in range(3)]
    display_judges(judges)
    
    # Get number of mentor feedback iterations
    while True:
        try:
            num_iterations = int(input("\nHow many mentor feedback iterations? (0-∞, default 1): ") or "1")
            if 0 <= num_iterations <= 5:
                break
            console.print("[red]Please enter a number between 0 and 5[/red]")
        except ValueError:
            console.print("[red]Please enter a valid number[/red]")
    
    # Create mentors (one per participant)
    console.print("\n[bold cyan]🎓 Assembling Mentors...[/bold cyan]")
    mentors = [create_mentor(ai) for _ in range(num_participants)]
    display_mentors(mentors)  # Similar to display_participants
    
    # Display competition details with more color
    console.print("\n[bold magenta]🎯 Competition Details[/bold magenta]")
    console.print(Panel.fit(
        f"[bold cyan]Theme:[/bold cyan] [yellow]{theme}[/yellow]\n\n"
        f"[bold green]Guidelines:[/bold green] [white]{guidelines}[/white]\n\n"
        f"[bold magenta]Host Announcement:[/bold magenta]\n[italic]{host_announcement}[/italic]",
        title="[bold]Promptathon Setup[/bold]",
        border_style="magenta"
    ))
    
    # Get confirmation to proceed
    if not input("\nPress Enter to begin the competition (or Ctrl+C to cancel)"):
        # Get submissions with mentor feedback
        console.print("\n[bold yellow]✍️ Participants are working with their mentors...[/bold yellow]")
        for participant, mentor in zip(participants, mentors):
            iterative_submission_process(ai, participant, mentor, guidelines, theme, host_announcement, num_iterations)
        
        # Judge submissions
        console.print("\n[bold magenta]🏆 Judging Phase Beginning...[/bold magenta]")
        for participant in participants:
            for judge in judges:
                score = judge_submissions(ai, judge, participant)
                participant.scores.append(score)
        
        # Calculate winner
        for participant in participants:
            participant.final_score = sum(participant.scores) / len(participant.scores)
        
        winner = max(participants, key=lambda p: p.final_score)
        
        # Display results
        console.print("\n[bold green]🎉 Final Results![/bold green]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Participant")
        table.add_column("Average Score")
        
        for participant in sorted(participants, key=lambda p: p.final_score, reverse=True):
            table.add_row(
                participant.name,
                f"{participant.final_score:.2f}"
            )
        
        console.print(table)
        
        # Display winning submission
        console.print("\n[bold green]🏆 Winning Submission[/bold green]")
        console.print(Panel.fit(
            f"[bold yellow]Reasoning:[/bold yellow]\n{winner.reasoning}\n\n"
            f"[bold green]Submission:[/bold green]\n{winner.submission}",
            title=f"[bold]{winner.name}'s Winning Entry[/bold]",
            border_style="green"
        ))
        
        # Interview winner
        console.print(f"\n[bold green]🎤 Interview with the winner: {winner.name}[/bold green]")
        interview = interview_winner(ai, winner)
        console.print(Panel(interview, title="Winner's Interview"))

if __name__ == "__main__":
    try:
        main(None)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]An unexpected error occurred: {e}[/red]")
        sys.exit(1) 