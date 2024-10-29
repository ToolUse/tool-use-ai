import inquirer
from rich.console import Console
from rich.panel import Panel
import requests

console = Console()

def submit_feedback():
    questions = [
        inquirer.List('type',
                      message="What type of contact would you like to make?",
                      choices=[
                          ('Request a guest', 'Guest Request'),
                          ('Request a topic', 'Topic Request'),
                          ('Provide feedback', 'Feedback'),
                          ('Say hi', 'Saying Hi')
                      ]),
        inquirer.Text('text',
                      message="Please enter your message"),
        inquirer.Text('user_email',
                      message="Please enter your email")
    ]

    answers = inquirer.prompt(questions)

    if answers:
        subject = answers['type']
        text = answers['text']
        user_email = answers['user_email']

        data = {
            "subject": subject,
            "text": text,
            "email": user_email 
        }

        try:
            url = "https://tyfiero-tool_use_feedback.web.val.run" 
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'ToolUse-CLI/1.0'
            }
            response = requests.post(url, json=data, headers=headers, verify=False)
            response.raise_for_status()
            console.print(Panel(f"Thank you for your submission!", style="green"))
        except requests.RequestException as e:
            console.print(Panel(f"An error occurred: {str(e)}\nResponse: {e.response.text if e.response else 'No response'}", style="red"))

def main():
    console.print(Panel("Welcome to the Tool Use Contact Form", style="cyan"))
    submit_feedback()

if __name__ == "__main__":
    main()
