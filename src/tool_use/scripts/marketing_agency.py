from swarm import Swarm, Agent
import sys
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box
from ..utils.ai_service import AIService
from ..config_manager import config_manager
from typing import List
import subprocess

console = Console()

ASCII_ART = """
╔═══════════════════════════════════╗
║ ██   ██  ██████  ██    ██  ████   ║
║ ██   ██    ██    ██    ██  ██     ║
║ ███████    ██    ██    ██  ████   ║
║ ██   ██    ██     ██  ██   ██     ║
║ ██   ██  ██████    ████    ████   ║
╚═══════════════════════════════════╝
"""


def consult_ceo_agent():
    """Setup the agent CEO"""
    ceo_agent = Agent(
        name="Marketing Agency CEO",
        instructions="""You are the CEO of a marketing agency, responsible for orchestrating your team to create 
        comprehensive marketing solutions for clients.

        DISCOVERY PHASE:
        First, conduct a thorough discovery call with the client. Ask 3-4 strategic questions, one at a time, such as:
        - Understanding their target audience and current market position
        - Their key business objectives and success metrics
        - Current marketing challenges and past efforts
        - Budget considerations and timeline expectations
        
        After gathering requirements, summarize the scope then proceeed to the next phase.

        TEAM COLLABORATION PHASE:
        Your team consists of:
        - Strategy Director: For market analysis and strategic planning
        - Creative Director: For creative concepts and campaign ideas
        - Digital Marketing Specialist: For digital marketing expertise
        
        Explicitly state that you're consulting with the Strategy Director for market analysis and strategic planning. They will pass this information to the Creative Director for creative concepts and the Digital Marketing Specialist for digital marketing recommendations. You will get the final recommendations back and synthesize everything into a cohesive plan. Always acknowledge insights from your team members before adding your own perspective in the final presentation.

        PRESENTATION PHASE:
        Present the final marketing plan in a structured format:
        1. Executive Summary
        2. Strategic Recommendations
        3. Creative Direction
        4. Digital Marketing Approach
        5. Implementation Timeline
        6. Expected Outcomes
        7. Anything else you think is relevant to the task

        Always maintain a professional, strategic approach and ensure all recommendations align with business objectives.""",
        functions=[consult_strategy_director],
        model="gpt-4o"
    )
    return ceo_agent

# Define handoff functions for CEO
def consult_strategy_director():
    """Consult with Strategy Director for strategic marketing insights"""
    strategy_director = Agent(
        name="Strategy Director",
        instructions="""You are an experienced Marketing Strategy Director. Your role is to analyze market opportunities and create high-level strategic recommendations like:
        - Target audience analysis
        - Market positioning
        - Core value propositions
        - Competitive landscape
        - Anything else you think is relevant
        
        After providing your strategic recommendations,  hand off your findings to the Creative Director 
        for campaign ideation based on your strategy.""",
        functions=[consult_creative_director],
        model="gpt-4o"
    )
    return strategy_director

def consult_creative_director():
    """Consult with Creative Director for creative and campaign ideas"""
    creative_director = Agent(
        name="Creative Director",
        instructions="""Review the Strategy Director's analysis and build upon it with creative concepts:
        - Brand storytelling approach
        - Campaign themes and concepts
        - Content style and tone
        - Visual direction
        - Anything else you think is relevant
        
        Reference specific points from the Strategy Director's analysis and explain how your creative 
        direction aligns with them. Then hand off to the Digital Marketing Specialist.""",
        functions=[consult_digital_specialist],
        model="gpt-4o"
    )
    return creative_director

def consult_digital_specialist():
    """Consult with Digital Marketing Specialist for digital marketing recommendations"""
    digital_specialist = Agent(
        name="Digital Marketing Specialist",
        instructions="""Building on both the strategic and creative recommendations, provide specific digital tactics:
        - Channel selection and rationale
        - Content distribution strategy
        - Technical implementation details
        - Budget allocation
        - Performance metrics
        - Anything else you think is relevant
        
        Reference how your recommendations support both the strategic goals and creative direction.
        Then hand off back to the CEO for final review and synthesis.""",
        functions=[consult_ceo_agent],
        model="gpt-4o"
    )
    return digital_specialist

def process_stream_response(response):
    """Helper function to process streamed responses"""
    full_message = ""
    current_sender = None
    
    # Define color mapping for different agents
    agent_colors = {
        "Marketing Agency CEO": "green",
        "Strategy Director": "blue",
        "Creative Director": "magenta",
        "Digital Marketing Specialist": "yellow"
    }
    
    for chunk in response:
        if isinstance(chunk, dict):
            # Handle different response formats
            content = chunk.get('content', '')
            sender = chunk.get('sender', current_sender)
            
            if sender and sender != current_sender:
                if full_message:  # Print accumulated message if exists
                    console.print()
                current_sender = sender
                # Get color for agent, default to green if not found
                color = agent_colors.get(sender, "green")
                console.print(f"\n[bold {color}]{current_sender}:[/bold {color}]", end=" ")
            
            if content:
                console.print(content, end="")
                full_message += content
                
    console.print()  # End line after message
    return full_message

def conduct_discovery(client, ceo_agent, messages):
    """Conduct the initial discovery session with the CEO"""
    console.print("\n[bold cyan]Starting Discovery Session[/bold cyan]")
    console.print("[dim]Our CEO will ask a few questions to better understand your needs...[/dim]\n")

    discovery_messages = messages.copy()
    discovery_messages.append({
        "role": "system",
        "content": """You are now in the discovery phase. Ask one strategic question at a time.
        After receiving an answer, acknowledge it briefly and ask your next question.
        After 1 questions, provide a clear summary of all gathered information and indicate we're moving to planning."""
    })

    discovery_complete = False
    question_count = 0

    while not discovery_complete and question_count < 5:  # Maximum 5 interactions
        try:
            response = client.run(
                agent=ceo_agent,
                messages=discovery_messages,
                context_variables={"phase": "discovery"},
                stream=True
            )

            # Process CEO's response
            current_message = process_stream_response(response)
            if current_message:
                discovery_messages.append({"role": "assistant", "content": current_message})
            
            # Get user's response
            console.print("\n[bold blue]You:[/bold blue]", end=" ")
            user_input = input()
            discovery_messages.append({"role": "user", "content": user_input})
            
            question_count += 1

            # Check if discovery is complete
            if current_message and any(phrase in current_message.lower() for phrase in 
                ["let me summarize", "to summarize", "moving forward", "let's proceed"]):
                discovery_complete = True

        except Exception as e:
            console.print(f"[red]Error during discovery: {str(e)}[/red]")
            console.print("[yellow]Attempting to continue with gathered information...[/yellow]")
            break

    return discovery_messages

def create_marketing_plan(client, ceo_agent, messages):
    """Create and present the marketing plan with the team"""
    console.print("\n[bold cyan]Creating Marketing Plan[/bold cyan]")
    console.print("[dim]Our team is collaborating to create your marketing plan...[/dim]\n")

    plan_messages = messages.copy()
    plan_messages.append({
        "role": "system",
        "content": """Create a comprehensive marketing plan by consulting with each team member. 
        Present the final plan in a structured format. Each team member should provide their specific recommendations."""
    })

    try:
        response = client.run(
            agent=ceo_agent,
            messages=plan_messages,
            context_variables={"phase": "planning"},
            stream=True
        )

        # Process and display the marketing plan
        final_message = process_stream_response(response)
        if final_message:
            plan_messages.append({"role": "assistant", "content": final_message})
        
        return plan_messages
    except Exception as e:
        console.print(f"[red]Error creating marketing plan: {str(e)}[/red]")
        return messages

def handle_feedback(client, ceo_agent, messages):
    """Handle user feedback on the marketing plan"""
    try:
        response = client.run(
            agent=ceo_agent,
            messages=messages,
            context_variables={"phase": "feedback"},
            stream=True
        )

        feedback_response = process_stream_response(response)
        if feedback_response:
            messages.append({"role": "assistant", "content": feedback_response})
        
        return messages
    except Exception as e:
        console.print(f"[red]Error processing feedback: {str(e)}[/red]")
        return messages

def main(args=None):
    # Display welcome message
    console.print(Text(ASCII_ART, style="bold yellow"))
    console.print("\n[bold yellow]Welcome to Hive Collective - Where Creative Minds Swarm 🐝  [/bold yellow]")
    
    time.sleep(1.4)
    console.print("\n[bold orange]Let's get started, what is the product you want to market? The more information you provide, the better we can help.[/bold orange]")
    
    try:
        # Import swarm after dependencies are installed
        try:
            from swarm import Swarm, Agent
        except ImportError as e:
            console.print(f"[red]Error: Could not import Swarm: {str(e)}[/red]")
            console.print("[yellow]Attempting to install swarm directly...[/yellow]")
            try:
                subprocess.check_call([
                    sys.executable, 
                    "-m", 
                    "pip", 
                    "install", 
                    "--force-reinstall",
                    "git+https://github.com/openai/swarm.git@main"
                ])
                console.print("[green]Successfully installed swarm, retrying import...[/green]")
                from swarm import Swarm, Agent
            except Exception as install_error:
                console.print(f"[red]Failed to install swarm: {str(install_error)}[/red]")
                sys.exit(1)

        # Initialize Swarm client
        try:
            client = Swarm()
        except Exception as client_error:
            console.print(f"[red]Error initializing Swarm client: {str(client_error)}[/red]")
            sys.exit(1)
        
        # Setup agents
        try:
            ceo_agent = consult_ceo_agent()
        except Exception as setup_error:
            console.print(f"[red]Error setting up agents: {str(setup_error)}[/red]")
            sys.exit(1)

        # Initialize messages
        messages = [{
            "role": "system", 
            "content": "Welcome to our marketing agency. You are speaking with the CEO who will help understand your needs."
        }]
        
        # Get initial user input
        console.print("\n[bold blue]You:[/bold blue]", end=" ")
        initial_input = input()
        if initial_input.strip():
            messages.append({"role": "user", "content": initial_input})
            
            # Conduct discovery session
            messages = conduct_discovery(client, ceo_agent, messages)

            # Create and present marketing plan
            messages = create_marketing_plan(client, ceo_agent, messages)

            # Enter feedback loop
            console.print("\n[yellow]Would you like to request any changes to the plan? (Type 'exit' to end session)[/yellow]")
            
            while True:
                console.print("\n[bold blue]You:[/bold blue]", end=" ")
                user_input = input()
                if user_input.lower() in ['exit', 'quit', 'bye', '']:
                    console.print("\n[cyan]Thank you for consulting with our agency. Goodbye![/cyan]")
                    break

                messages.append({"role": "user", "content": user_input})
                messages = handle_feedback(client, ceo_agent, messages)

    except Exception as e:
        console.print(f"[red]Fatal error: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main() 