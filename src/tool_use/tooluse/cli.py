import sys
from .rss import main as rss_main
from .contact import main as contact_main
from rich.console import Console
from rich.panel import Panel

console = Console()

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "contact":
            contact_main()
    else:
        rss_main()

if __name__ == "__main__":
    main()