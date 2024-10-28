import sys
from .rss_cli import main as rss_main
from .contact_cli import main as contact_main
from rich.console import Console
from rich.panel import Panel

console = Console()

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "contact":
            contact_main()
        else:
            console.print(Panel("Invalid command. Use 'tooluse' for RSS feed or 'tooluse contact' for the contact form.", style="red"))
    else:
        rss_main()

if __name__ == "__main__":
    main()
